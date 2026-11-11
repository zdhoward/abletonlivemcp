"""Client for the mutually authenticated, bounded protocol-2 loopback bridge."""

from __future__ import annotations

import ctypes
import hashlib
import hmac
import itertools
import json
import math
import os
import re
import secrets
import socket
import stat
import time
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
PROTOCOL_VERSION = 2
MAX_FRAME = 1024 * 1024
MAX_DEPTH = 32
MAX_NODES = 16384
FRAME_TIMEOUT = 5.0
EXCHANGE_TIMEOUT = 15.0
CAPABILITIES = {
    "authenticated_envelopes": True,
    "bounded_io": True,
    "atomic_cancellation": True,
}
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_METHOD = re.compile(r"[A-Za-z][A-Za-z0-9_.]{0,127}\Z")


def _windows_private(fd):
    """Check the opened file's owner/DACL, without shelling out or trusting mode bits."""
    import msvcrt
    from ctypes import wintypes

    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    ptr = ctypes.c_void_p
    adv.GetSecurityInfo.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.DWORD] + [
        ctypes.POINTER(ptr)
    ] * 5
    adv.GetSecurityInfo.restype = wintypes.DWORD
    adv.ConvertSidToStringSidW.argtypes = [ptr, ctypes.POINTER(ptr)]
    adv.ConvertSidToStringSidW.restype = wintypes.BOOL
    adv.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    adv.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ptr,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    adv.GetAce.argtypes = [ptr, wintypes.DWORD, ctypes.POINTER(ptr)]
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.LocalFree.argtypes = [ptr]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]

    def sid_text(sid):
        text = ptr()
        if not adv.ConvertSidToStringSidW(sid, ctypes.byref(text)):
            raise ValueError("cannot inspect config ACL")
        try:
            return ctypes.wstring_at(text)
        finally:
            kernel.LocalFree(text)

    token = wintypes.HANDLE()
    if not adv.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise ValueError("cannot inspect config owner")
    try:
        size = wintypes.DWORD()
        adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        data = ctypes.create_string_buffer(size.value)
        if not adv.GetTokenInformation(token, 1, data, size, ctypes.byref(size)):
            raise ValueError("cannot inspect config owner")
        current = sid_text(ctypes.cast(data, ctypes.POINTER(ptr))[0])
    finally:
        kernel.CloseHandle(token)
    owner, dacl, sd = ptr(), ptr(), ptr()
    code = adv.GetSecurityInfo(
        msvcrt.get_osfhandle(fd),
        1,
        5,
        ctypes.byref(owner),
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(sd),
    )
    if code:
        raise ValueError("cannot inspect config ACL")
    try:
        if not dacl.value or sid_text(owner) != current:
            raise ValueError("config must be owned by the current user with a private ACL")
        # ACL header: BYTE revision/reserved; WORD size/ace_count/reserved.
        count = ctypes.c_ushort.from_address(dacl.value + 4).value
        for index in range(count):
            ace = ptr()
            if not adv.GetAce(dacl, index, ctypes.byref(ace)):
                raise ValueError("cannot inspect config ACL")
            kind = ctypes.c_ubyte.from_address(ace.value).value
            if kind == 1:  # ACCESS_DENIED_ACE grants no access
                continue
            if kind != 0 or sid_text(ace.value + 8) not in {
                current,
                "S-1-3-4",  # OWNER RIGHTS resolves to the checked current-user owner
                "S-1-5-18",
                "S-1-5-32-544",  # owner, SYSTEM, Administrators
            }:
                raise ValueError("config ACL grants access to another principal")
    finally:
        kernel.LocalFree(sd)


def _load_secret():
    """Never create, repair, print or fall back from an explicitly selected config."""
    path = os.environ.get("ABLETONLIVEMCP_CONFIG")
    if path is None:
        path = os.path.join(os.path.expanduser("~"), ".abletonlivemcp", "bridge.json")
    if not path or not os.path.isabs(path):
        raise ValueError("config path must be absolute")
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or getattr(before, "st_file_attributes", 0) & 0x400:
        raise ValueError("config must be a regular file, not a link")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or (before.st_dev, before.st_ino) != (
            info.st_dev,
            info.st_ino,
        ):
            raise ValueError("config changed while opening")
        if os.name == "nt":
            _windows_private(stream.fileno())
        elif info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError("config permissions must be owner-only")
        raw = stream.read(8193)
    if len(raw) > 8192:
        raise ValueError("config exceeds limit")
    config = _decode(raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw)  # tolerate a BOM
    secret = config.get("secret") if isinstance(config, dict) else None
    if not isinstance(secret, str) or not _HEX.fullmatch(secret):
        raise ValueError("config requires a 32-byte lowercase hex secret")
    return bytes.fromhex(secret)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_number(value):
    raise ValueError("non-finite JSON number")


def _validate(value):
    stack = [(value, 0)]
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("JSON structure exceeds limit")
        if isinstance(item, dict):
            if count + len(stack) + 2 * len(item) > MAX_NODES:
                raise ValueError("JSON structure exceeds limit")
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError("JSON keys must be strings")
                stack.extend(((key, depth + 1), (child, depth + 1)))
        elif isinstance(item, list):
            if count + len(stack) + len(item) > MAX_NODES:
                raise ValueError("JSON structure exceeds limit")
            stack.extend((child, depth + 1) for child in item)
        elif isinstance(item, str):
            if len(item) > MAX_FRAME // 6:
                raise ValueError("JSON string exceeds limit")
        elif isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError("non-finite JSON number")
        elif type(item) is int and abs(item) > 2**53 - 1:
            raise ValueError("JSON integer exceeds limit")
        elif item is not None and not isinstance(item, (bool, int)):
            raise ValueError("unsupported JSON value")


def _decode(raw):
    value = json.loads(
        raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_invalid_number
    )
    _validate(value)
    return value


def _encode(value):
    _validate(value)
    chunks, size = [], 0
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
    for piece in encoder.iterencode(value):
        chunk = piece.encode("ascii")  # ensure_ascii=True is intentional and canonical
        size += len(chunk)
        if size > MAX_FRAME:
            raise ValueError("frame exceeds limit")
        chunks.append(chunk)
    return b"".join(chunks)


def _mac(secret, domain, context, body):
    digest = hmac.new(
        secret, b"AbletonLiveMCP/v2/" + domain.encode("ascii") + b"\0", hashlib.sha256
    )
    digest.update(_encode(context))
    digest.update(b"\0")
    digest.update(_encode(body))
    return digest.hexdigest()


def _signed(secret, domain, context, body):
    return dict(body, mac=_mac(secret, domain, context, body))


def _verify(secret, domain, context, envelope):
    if not isinstance(envelope, dict):
        raise ValueError("expected object envelope")
    body = dict(envelope)
    signature = body.pop("mac", None)
    if not isinstance(signature, str) or not _HEX.fullmatch(signature):
        raise ValueError("missing authentication")
    if not hmac.compare_digest(signature, _mac(secret, domain, context, body)):
        raise ValueError("authentication failed")
    return body


class _FrameError(ValueError):
    def __init__(self, kind):
        self.kind = kind


class _Wire:
    def __init__(self, conn, deadline):
        self.conn, self.deadline, self.buf = conn, deadline, b""

    def read(self):
        end = min(self.deadline, time.monotonic() + FRAME_TIMEOUT)
        while True:
            newline = self.buf.find(b"\n")
            if newline >= 0:
                if newline > MAX_FRAME:
                    raise _FrameError("FrameTooLarge")
                line, self.buf = self.buf[:newline], self.buf[newline + 1 :]
                try:
                    return _decode(line)
                except (ValueError, RecursionError):
                    raise _FrameError("BadFrame") from None
            if len(self.buf) > MAX_FRAME:
                raise _FrameError("FrameTooLarge")
            left = end - time.monotonic()
            if left <= 0:
                raise _FrameError("FrameTimeout")
            self.conn.settimeout(left)
            try:
                chunk = self.conn.recv(min(65536, MAX_FRAME + 1 - len(self.buf)))
            except TimeoutError:
                raise _FrameError("FrameTimeout") from None
            if not chunk:
                raise _FrameError("ConnectionClosed")
            self.buf += chunk

    def send(self, body):
        raw = _encode(body)
        left = min(FRAME_TIMEOUT, self.deadline - time.monotonic())
        if left <= 0:
            raise _FrameError("ExchangeTimeout")
        self.conn.settimeout(left)
        self.conn.sendall(raw + b"\n")


class BridgeError(Exception):
    """An explicit refusal or an uncertain exchange; commands are never auto-retried."""

    def __init__(self, kind: str, message: str, may_have_applied: bool = False):
        super().__init__(f"{kind}: {message}")
        self.kind = kind
        self.message = message
        self.may_have_applied = may_have_applied
        self.retryable = False

    def __str__(self) -> str:
        # MCP clients only see this text, so state the outcome explicitly.
        outcome = (
            "may have been applied; read back state before retrying"
            if self.may_have_applied
            else "not applied"
        )
        return f"{self.kind}: {self.message} ({outcome})"


_UNSIGNED_KINDS = {"BadFrame", "FrameTooLarge", "FrameTimeout"}


def _reject_unsigned_error(frame, transmitted):
    """The server's unsigned {"type":"error"} frames are diagnostics, never outcomes."""
    if isinstance(frame, dict) and frame.get("type") == "error" and "mac" not in frame:
        kind = frame.get("error")
        if kind == "Busy":
            raise BridgeError("BridgeBusy", "bridge busy; try again shortly", transmitted)
        if kind in _UNSIGNED_KINDS:
            raise BridgeError(kind, "bridge exchange incomplete", transmitted)


class BridgeClient:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = 15.0,
        *,
        required_capabilities: tuple[str, ...] = (),
    ):
        if host != DEFAULT_HOST:
            raise ValueError("bridge requires IPv4 loopback")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        self._addr = (host, port)
        self._timeout = min(timeout, EXCHANGE_TIMEOUT)
        self._ids = itertools.count(1)
        self._required = set(CAPABILITIES) | set(required_capabilities)
        self.status = None

    def _authenticate(self, wire, secret):
        nonce = secrets.token_hex(32)
        try:
            wire.send({"type": "client_hello", "protocol": 2, "nonce": nonce})
        except OSError:
            # A busy server may already have answered and closed; surface its explicit reply.
            try:
                _reject_unsigned_error(wire.read(), False)
            except (OSError, ValueError):
                pass
            raise
        frame = wire.read()
        _reject_unsigned_error(frame, False)
        hello = _verify(secret, "server_hello", {}, frame)
        if (
            set(hello) != {"type", "protocol", "context"}
            or hello["type"] != "server_hello"
            or type(hello["protocol"]) is not int
            or hello["protocol"] != 2
        ):
            raise ValueError("incompatible server handshake")
        context = hello["context"]
        if (
            not isinstance(context, dict)
            or set(context) != {"client_nonce", "server_nonce", "status"}
            or context["client_nonce"] != nonce
            or not isinstance(context["server_nonce"], str)
            or not _HEX.fullmatch(context["server_nonce"])
        ):
            raise ValueError("invalid connection binding")
        status = context["status"]
        if (
            not isinstance(status, dict)
            or set(status)
            != {"protocol", "component_version", "build", "session", "methods", "capabilities"}
            or type(status["protocol"]) is not int
            or status["protocol"] != 2
            or not isinstance(status["session"], str)
            or not _HEX.fullmatch(status["session"])
            or not isinstance(status["component_version"], str)
            or not isinstance(status["build"], str)
            or not isinstance(status["methods"], list)
            or any(not isinstance(m, str) or not _METHOD.fullmatch(m) for m in status["methods"])
            or not isinstance(status["capabilities"], dict)
            or any(status["capabilities"].get(cap) is not True for cap in self._required)
        ):
            raise ValueError("incompatible bridge status or capabilities")
        wire.send(_signed(secret, "client_auth", context, {"type": "client_auth", "protocol": 2}))
        frame = wire.read()
        _reject_unsigned_error(frame, False)
        ready = _verify(secret, "authenticated", context, frame)
        if ready != {"type": "authenticated", "protocol": 2} or type(ready["protocol"]) is not int:
            raise ValueError("invalid authentication acknowledgement")
        self.status = status
        return context

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self.status = None  # never reuse an unauthenticated or previous-session status
        if not isinstance(method, str) or not _METHOD.fullmatch(method):
            raise BridgeError("BadRequest", "method exceeds protocol bounds")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise BridgeError("BadRequest", "params must be an object")
        try:
            secret = _load_secret()
        except (OSError, ValueError, RecursionError):
            raise BridgeError(
                "ConfigError", "private bridge config unavailable; reinstall or repair"
            ) from None
        transmitted = False
        try:
            deadline = time.monotonic() + self._timeout
            try:
                conn = socket.create_connection(self._addr, timeout=self._timeout)
            except OSError:  # includes a connect timeout; nothing was sent, so nothing applied
                raise BridgeError(
                    "Unreachable",
                    f"Cannot reach Ableton Live at {self._addr[0]}:{self._addr[1]}. Start Live "
                    "and enable the AbletonLiveMCP control surface in Settings > Link/Tempo/MIDI.",
                    False,
                ) from None
            with conn:
                wire = _Wire(conn, deadline)
                context = self._authenticate(wire, secret)
                rid = next(self._ids)
                if rid > 2**53 - 1:
                    raise BridgeError("IdExhausted", "create a new bridge client")
                request = _signed(
                    secret,
                    "request",
                    context,
                    {
                        "type": "request",
                        "protocol": 2,
                        "id": rid,
                        "method": method,
                        "params": params,
                    },
                )
                _encode(request)  # validate and bound everything before attempting transmission
                transmitted = True  # even a failed sendall may have transmitted the entire request
                wire.send(request)
                frame = wire.read()
                _reject_unsigned_error(frame, True)
                reply = _verify(secret, "response", context, frame)
                if (
                    reply.get("type") != "response"
                    or type(reply.get("protocol")) is not int
                    or reply["protocol"] != 2
                    or type(reply.get("id")) is not int
                    or reply["id"] != rid
                    or type(reply.get("ok")) is not bool
                    or wire.buf
                ):
                    raise ValueError("invalid reply envelope")
                if reply["ok"]:
                    if set(reply) != {"type", "protocol", "id", "ok", "result"}:
                        raise ValueError("invalid success envelope")
                    return reply["result"]
                if set(reply) != {"type", "protocol", "id", "ok", "error"}:
                    raise ValueError("invalid error envelope")
                error = reply["error"]
                if (
                    not isinstance(error, dict)
                    or set(error) != {"type", "message", "may_have_applied"}
                    or not isinstance(error["type"], str)
                    or not isinstance(error["message"], str)
                    or type(error["may_have_applied"]) is not bool
                ):
                    raise ValueError("invalid error outcome")
                raise BridgeError(error["type"], error["message"], error["may_have_applied"])
        except BridgeError:
            raise
        except _FrameError as exc:
            raise BridgeError(exc.kind, "bridge exchange incomplete", transmitted) from None
        except TimeoutError:
            raise BridgeError("ExchangeTimeout", "bridge deadline expired", transmitted) from None
        except OSError:
            raise BridgeError(
                "Unreachable", "loopback bridge unavailable or connection lost", transmitted
            ) from None
        except (ValueError, RecursionError):
            kind = "ProtocolError" if transmitted else "AuthenticationOrProtocolError"
            raise BridgeError(
                kind,
                "protocol 2 verification failed; reinstall script and restart Live",
                transmitted,
            ) from None
