"""Authenticated loopback bridge. Only drain() invokes application code (stdlib only)."""

import collections
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import socket
import stat
import threading
import time
import traceback

PROTOCOL_VERSION = 2
MAX_CONNECTIONS = 4
MAX_QUEUE = 16
MAX_FRAME = 1024 * 1024  # excluding the terminating newline, in either direction
MAX_DEPTH = 32
MAX_NODES = 16384
FRAME_TIMEOUT = 5.0  # absolute frame deadline: trickling bytes does not reset it
EXCHANGE_TIMEOUT = 15.0  # includes authentication, queueing, execution and sending
REQUEST_TIMEOUT = 10.0  # additionally bounds the wait for drain()
AUTH_TIMEOUT = 2.0  # accept -> verified client_auth; a keyless peer cannot hold a slot longer
CAPABILITIES = {
    "authenticated_envelopes": True,
    "bounded_io": True,
    "atomic_cancellation": True,
}
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_METHOD = re.compile(r"[A-Za-z][A-Za-z0-9_.]{0,127}\Z")


_BUILD_FILE = re.compile(r"(?!probe_p\d\d\.py\Z)\w+\.py\Z")  # dev probes are optional


def build_id(files):
    """Content hash of a Remote Script: ``files`` maps file name -> bytes. Dev probes are left
    out (release archives omit them). The host computes the same over its packaged copy."""
    digest = hashlib.sha256()
    for name in sorted(n for n in files if _BUILD_FILE.match(n)):
        digest.update(name.encode() + b"\0" + files[name] + b"\0")
    return "sha256:" + digest.hexdigest()[:16]


def script_identity(directory=None):
    """(version, build) of the Remote Script in ``directory`` (default: this one): VERSION from
    version.py, the single source shared with the host package, and build_id of its files."""
    directory = directory or os.path.dirname(os.path.abspath(__file__))
    try:
        files = {}
        for name in os.listdir(directory):
            if _BUILD_FILE.match(name):
                with open(os.path.join(directory, name), "rb") as handle:
                    files[name] = handle.read()
        found = re.search(rb'^VERSION = "([^"]+)"', files.get("version.py", b""), re.M)
        return (found.group(1).decode() if found else "unknown"), build_id(files)
    except (OSError, UnicodeError):
        return "unknown", "unknown"


SCRIPT_IDENTITY = script_identity()  # at load: the code Live runs, not a later copy on disk


_MODULES = ("ctypes", "msvcrt", "subprocess", "hmac", "hashlib", "secrets")


def module_diagnostic():
    """One log line: which optional stdlib modules this embedded Python has. No secrets."""
    found = []
    for name in _MODULES:
        try:
            __import__(name)
            found.append(name + "=yes")
        except ImportError:
            found.append(name + "=no")
    return "AbletonLiveMCP: python modules " + " ".join(found)


# ---- sanitized failure diagnostics -----------------------------------------------------------
# Exception messages from Live (and locals) can hold file paths, object names or other user data,
# so they are never echoed to a client or written to the log. A client sees ``public_error``: a
# deliberate refusal's own text, otherwise the exception type and a stable code. Live's log gets
# ``log_failure``: a label, the exception type and code locations only. One helper for the
# request loop, batch writes (dom_common.run_writes) and deferred operations.

_failure_sink = None  # Live's log_message, installed by BridgeServer


def failure_location(exc, depth=4):
    """``file:line <- file:line ...`` of the innermost frames: code locations, no values."""
    frames = traceback.extract_tb(exc.__traceback__)[-depth:]
    return " <- ".join(f"{os.path.basename(f.filename)}:{f.lineno}" for f in reversed(frames))


def log_failure(label, exc, log=None):
    """Log where ``label`` failed. Never raises: diagnostics must not change any reply."""
    log = log if log is not None else _failure_sink
    if log is None:
        return
    try:
        log(f"AbletonLiveMCP: {label} failed: {type(exc).__name__} at {failure_location(exc)}")
    except Exception:  # noqa: BLE001
        pass


def readable(exc):
    """True for deliberate refusals, whose text this code wrote: a plain ValueError with one
    string argument (the request loop's rule) or a coded Refused."""
    if type(exc) is ValueError and len(exc.args) == 1 and isinstance(exc.args[0], str):
        return True
    code, message = getattr(exc, "code", None), getattr(exc, "message", None)
    return isinstance(code, str) and isinstance(message, str)


def public_error(exc, code):
    """What a receipt may say about ``exc``: a deliberate refusal's text, else ``Type: code``."""
    if readable(exc):
        text = exc.args[0] if type(exc) is ValueError else f"refused:{exc.code}: {exc.message}"
        return text[:300]
    return f"{type(exc).__name__}: {code}"


def strict_acl_available():
    """True when the full Windows DACL check can run (ctypes importable, or not Windows)."""
    if os.name != "nt":
        return True
    try:
        import ctypes  # noqa: F401
        import msvcrt  # noqa: F401
        from ctypes import wintypes  # noqa: F401
    except ImportError:
        return False
    return True


def _is_link(path):
    info = os.lstat(path)
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _under(path, root):
    path = os.path.normcase(os.path.realpath(path))
    root = os.path.normcase(os.path.realpath(root))
    return path == root or path.startswith(root.rstrip("/\\") + os.sep)


def _windows_fallback(fd, path):
    """Weaker check when ctypes is missing: the ACL cannot be verified, but fail closed on
    reparse points, a location outside the user's profile, or a linked parent directory."""
    if not path:
        raise ValueError("cannot verify config location without its path")
    if getattr(os.fstat(fd), "st_file_attributes", 0) & 0x400:
        raise ValueError("config must not be a reparse point")
    if _under(path, os.path.expanduser("~")):
        return
    if os.environ.get("ABLETONLIVEMCP_CONFIG") is None or _is_link(os.path.dirname(path)):
        raise ValueError("config must live under the user profile or an unlinked explicit folder")


def _windows_private(fd, path=None):
    """Check the opened file's owner/DACL, without shelling out or trusting mode bits."""
    try:
        import ctypes
        import msvcrt
        from ctypes import wintypes
    except ImportError:  # Live's embedded Python on Windows has no ctypes
        return _windows_fallback(fd, path)

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
            _windows_private(stream.fileno(), path)
        elif info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError("config permissions must be owner-only")
        raw = stream.read(8193)
    if len(raw) > 8192:
        raise ValueError("config exceeds limit")
    # Windows PowerShell 5.1 writes a UTF-8 BOM; tolerate it like config.py does.
    config = _decode(raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw)
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


def _err(rid, kind, may_have_applied=False, message=None):
    return {
        "type": "response",
        "protocol": 2,
        "id": rid,
        "ok": False,
        "error": {
            "type": kind,
            "message": kind if message is None else message,
            "may_have_applied": may_have_applied,
        },
    }


class _Pending:
    def __init__(self, request, deadline):
        self.request, self.deadline = request, deadline
        self.event = threading.Event()
        self.state = "queued"
        self.response = None
        self.abandoned = False


class BridgeServer:
    def __init__(self, dispatch, host="127.0.0.1", port=9877, log=None):
        if host != "127.0.0.1":
            raise ValueError("bridge requires IPv4 loopback")
        self._dispatch, self._host, self._port = dispatch, host, port
        self._log = log
        if log is not None:
            global _failure_sink
            _failure_sink = log  # handler-level failures (batch writes, tasks) log here too
        self._lock = threading.Lock()
        self._queue = collections.deque()
        self._pending, self._connections, self._workers = set(), set(), set()
        self._sock = None
        self._stop = threading.Event()
        self._slots = threading.BoundedSemaphore(MAX_CONNECTIONS)
        self._accept_thread = None

    @property
    def port(self):
        return self._port

    def start(self):
        if self._sock is not None or self._stop.is_set():
            raise RuntimeError("bridge instance cannot be restarted")
        try:
            self._secret = _load_secret()
        except (OSError, ValueError, RecursionError):
            raise ValueError(
                "private bridge config unavailable; reinstall or repair config"
            ) from None
        version, build = SCRIPT_IDENTITY
        self._status = {
            "protocol": 2,
            "component_version": version,
            "build": build,
            "session": secrets.token_hex(32),
            "methods": [
                m for m in getattr(self._dispatch, "methods", ()) if _METHOD.fullmatch(m)
            ],
            "capabilities": dict(CAPABILITIES),
        }
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((self._host, self._port))
            s.listen(MAX_CONNECTIONS)
            s.settimeout(0.1)
        except OSError:
            s.close()
            raise
        self._port, self._sock = s.getsockname()[1], s
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

    def stop(self):
        self._stop.set()
        with self._lock:
            for pending in self._pending:
                was_started = pending.state == "started"
                if pending.state == "queued":
                    pending.state = "cancelled"
                pending.response = _err(pending.request["id"], "Shutdown", was_started)
                pending.abandoned = True
                pending.event.set()
            self._queue.clear()
            self._pending.clear()
            connections, workers = list(self._connections), list(self._workers)
        if self._sock is not None:
            self._sock.close()
        for conn in connections:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conn.close()
        end = time.monotonic() + 1.0
        for thread in workers + ([self._accept_thread] if self._accept_thread else []):
            if thread is not threading.current_thread():
                thread.join(max(0, end - time.monotonic()))

    def drain(self, budget=8):
        """Only the Live main thread calls this; never waits on a socket or client."""
        for _ in range(budget):
            with self._lock:
                if self._stop.is_set() or not self._queue:
                    return
                pending = self._queue.popleft()
                if pending.state != "queued":
                    continue
                if time.monotonic() >= pending.deadline:
                    pending.state = "cancelled"
                    pending.response = _err(pending.request["id"], "Timeout")
                    pending.event.set()
                    self._pending.discard(pending)
                    continue
                pending.state = "started"  # atomic with the timeout/cancel decision
            response = self._run(pending.request)
            with self._lock:
                pending.state = "completed"
                if not pending.abandoned:
                    pending.response = response
                pending.event.set()
                self._pending.discard(pending)

    def _run(self, req):
        try:
            result = self._dispatch(req["method"], req["params"])
            return {
                "type": "response",
                "protocol": 2,
                "id": req["id"],
                "ok": True,
                "result": result,
            }
        except Exception as exc:
            # Only deliberate argument refusals (plain ValueError, raised before any change)
            # are readable. Every other exception can hold credentials or user input: not echoed.
            if type(exc) is ValueError and len(exc.args) == 1 and isinstance(exc.args[0], str):
                return _err(req["id"], "ValueError", False, exc.args[0])
            self._log_failure(req["method"], exc)
            return _err(req["id"], "HandlerError", True)

    def _log_failure(self, method, exc):
        """Log where a handler failed: method, exception type and code locations only. The
        message and locals can hold user data or secrets, so they are never written."""
        if self._log is not None:
            log_failure(method, exc, self._log)

    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with self._lock:
                if self._stop.is_set():
                    conn.close()
                    return
                admitted = self._slots.acquire(blocking=False)
                if admitted:
                    self._connections.add(conn)
                    worker = threading.Thread(target=self._client_loop, args=(conn,), daemon=True)
                    self._workers.add(worker)
                    worker.start()
            if not admitted:
                # Never hold the drain/state lock across socket I/O.
                try:
                    _Wire(conn, time.monotonic() + 0.05).send(
                        {"type": "error", "protocol": 2, "error": "Busy"}
                    )
                    # Consume the peer's hello so close() sends FIN, not an RST that
                    # could discard the Busy frame before the client reads it.
                    conn.shutdown(socket.SHUT_WR)
                    conn.settimeout(0.05)
                    conn.recv(4096)
                except (OSError, ValueError):
                    pass
                conn.close()

    def _client_loop(self, conn):
        started = time.monotonic()
        wire = _Wire(conn, started + min(AUTH_TIMEOUT, EXCHANGE_TIMEOUT))
        full_deadline = started + EXCHANGE_TIMEOUT
        context = None
        try:
            hello = wire.read()
            if (
                not isinstance(hello, dict)
                or set(hello) != {"type", "protocol", "nonce"}
                or hello["type"] != "client_hello"
                or type(hello["protocol"]) is not int
                or hello["protocol"] != 2
                or not isinstance(hello["nonce"], str)
                or not _HEX.fullmatch(hello["nonce"])
            ):
                return
            context = {
                "client_nonce": hello["nonce"],
                "server_nonce": secrets.token_hex(32),
                "status": self._status,
            }
            wire.send(
                _signed(
                    self._secret,
                    "server_hello",
                    {},
                    {"type": "server_hello", "protocol": 2, "context": context},
                )
            )
            auth = _verify(self._secret, "client_auth", context, wire.read())
            if auth != {"type": "client_auth", "protocol": 2} or type(auth["protocol"]) is not int:
                return
            wire.deadline = full_deadline  # authenticated: normal exchange deadlines apply
            wire.send(
                _signed(
                    self._secret, "authenticated", context, {"type": "authenticated", "protocol": 2}
                )
            )
            req = _verify(self._secret, "request", context, wire.read())
            if (
                set(req) != {"type", "protocol", "id", "method", "params"}
                or req["type"] != "request"
                or type(req["protocol"]) is not int
                or req["protocol"] != 2
                or type(req["id"]) is not int
                or not 1 <= req["id"] <= 2**53 - 1
                or not isinstance(req["method"], str)
                or not _METHOD.fullmatch(req["method"])
                or not isinstance(req["params"], dict)
                or wire.buf
            ):
                return
            response = self._submit(req, wire.deadline)
            try:
                envelope = _signed(self._secret, "response", context, response)
                _encode(envelope)
            except (ValueError, RecursionError):
                envelope = _signed(
                    self._secret, "response", context, _err(req["id"], "ReplyTooLarge", True)
                )
            wire.send(envelope)
        except _FrameError as exc:
            # Unauthenticated errors are diagnostic only; never trusted as command outcomes.
            try:
                if not self._stop.is_set():
                    wire.send({"type": "error", "protocol": 2, "error": exc.kind})
            except (OSError, ValueError):
                pass
        except (OSError, ValueError, RecursionError):
            pass  # first invalid/authentication failure closes; no dispatch or error echo
        finally:
            conn.close()
            with self._lock:
                self._connections.discard(conn)
                self._workers.discard(threading.current_thread())
                self._slots.release()

    def _submit(self, req, deadline):
        pending = _Pending(req, min(deadline, time.monotonic() + REQUEST_TIMEOUT))
        with self._lock:
            if self._stop.is_set():
                return _err(req["id"], "Shutdown")
            if len(self._queue) >= MAX_QUEUE:
                return _err(req["id"], "Busy")
            self._queue.append(pending)
            self._pending.add(pending)
        pending.event.wait(max(0, pending.deadline - time.monotonic()))
        with self._lock:
            if pending.response is not None:
                return pending.response
            if pending.state == "queued":
                pending.state = "cancelled"
                self._queue.remove(pending)
                self._pending.discard(pending)
                return _err(req["id"], "Timeout")
            pending.abandoned = True
            return _err(req["id"], "TimeoutAfterStart", True)
