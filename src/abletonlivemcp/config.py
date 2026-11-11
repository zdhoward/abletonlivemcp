"""Stdlib-only configuration shared with the installed Live Remote Script.

ABLETONLIVEMCP_CONFIG must name an absolute file; otherwise both runtimes use
~/.abletonlivemcp/bridge.json. Only the installer provisions configuration.
"""

from __future__ import annotations

import ctypes
import json
import os
import re
import secrets
import stat
import subprocess
import tempfile
from pathlib import Path


class ConfigError(ValueError):
    """Configuration is missing, invalid, or not private to its owner."""


def checked_path(path: Path) -> Path:
    """Check lexical ancestors before resolving, including Windows junctions."""
    path = Path(os.path.abspath(path))
    for part in (*reversed(path.parents), path):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ConfigError(f"Refusing symlink/junction/reparse path: {part}")
    return path


def config_path() -> Path:
    override = os.environ.get("ABLETONLIVEMCP_CONFIG")
    if override is not None:
        path = Path(override)
        if not override or not path.is_absolute():
            raise ConfigError("ABLETONLIVEMCP_CONFIG must be an absolute file path")
    else:
        path = Path.home() / ".abletonlivemcp" / "bridge.json"
    return checked_path(path)


def _windows_sid() -> str:
    """Current user SID from the process token; no subprocess, no PATH search."""
    from ctypes import wintypes

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    ptr = ctypes.c_void_p
    advapi.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ptr,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi.ConvertSidToStringSidW.argtypes = [ptr, ctypes.POINTER(ptr)]
    advapi.ConvertSidToStringSidW.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.LocalFree.argtypes = [ptr]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    failure = ConfigError("Cannot establish the current Windows security principal")
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise failure
    try:
        size = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))  # TokenUser
        data = ctypes.create_string_buffer(size.value)
        if not advapi.GetTokenInformation(token, 1, data, size, ctypes.byref(size)):
            raise failure
        text = ptr()
        if not advapi.ConvertSidToStringSidW(
            ctypes.cast(data, ctypes.POINTER(ptr))[0], ctypes.byref(text)
        ):
            raise failure
        try:
            sid = ctypes.wstring_at(text)
        finally:
            kernel.LocalFree(text)
    finally:
        kernel.CloseHandle(token)
    if not re.fullmatch(r"S-1-[0-9-]+", sid):
        raise failure
    return sid


def _windows_sddl(path: Path) -> str:
    from ctypes import wintypes

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_security = advapi.GetNamedSecurityInfoW
    get_security.argtypes = [
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    get_security.restype = wintypes.DWORD
    stringify = advapi.ConvertSecurityDescriptorToStringSecurityDescriptorW
    stringify.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.c_void_p,
    ]
    stringify.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    descriptor = ctypes.c_void_p()
    output = wintypes.LPWSTR()
    status = get_security(str(path), 1, 5, None, None, None, None, ctypes.byref(descriptor))
    if status:
        raise ConfigError(f"Cannot inspect configuration ACL (Windows error {status})")
    try:
        if not stringify(descriptor, 1, 5, ctypes.byref(output), None):
            raise ConfigError("Cannot inspect configuration security descriptor")
        try:
            return output.value
        finally:
            kernel.LocalFree(ctypes.cast(output, ctypes.c_void_p))
    finally:
        kernel.LocalFree(descriptor)


def _windows_set_private(path: Path) -> None:
    from ctypes import wintypes

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
    ]
    convert.restype = wintypes.BOOL
    apply = advapi.SetFileSecurityW
    apply.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    apply.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    descriptor = ctypes.c_void_p()
    sid = _windows_sid()
    if not convert(f"O:{sid}D:P(A;;FA;;;{sid})", 1, ctypes.byref(descriptor), None):
        raise ConfigError("Cannot construct an owner-only configuration ACL")
    try:
        if not apply(str(path), 0x80000005, descriptor):  # owner + protected DACL
            raise ConfigError("Cannot apply an owner-only configuration ACL")
    finally:
        kernel.LocalFree(descriptor)


def _check_private(path: Path) -> None:
    checked_path(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ConfigError("Bridge configuration must be a regular file")
    if os.name == "nt":
        sid = _windows_sid()
        sddl = _windows_sddl(path)
        owner = re.search(r"O:(.*?)(?=[GDS]:|$)", sddl)
        dacl = sddl[sddl.find("D:") :] if "D:" in sddl else ""
        allowed = {sid, "OW", "S-1-3-4", "SY", "S-1-5-18", "BA", "S-1-5-32-544"}
        fields = [ace.split(";") for ace in re.findall(r"\(([^()]*)\)", dacl)]
        if (
            owner is None
            or owner[1] != sid
            or not dacl
            or any(len(f) != 6 for f in fields)
            or any(f[0] != "D" and (f[0] != "A" or f[5] not in allowed) for f in fields)
        ):
            raise ConfigError(
                "Bridge configuration ACL must grant access only to its owner, SYSTEM "
                "and Administrators"
            )
    elif info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ConfigError("Bridge configuration must be owner-only (chmod 600)")


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_config() -> dict:
    path = config_path()
    try:
        _check_private(path)
        if path.stat().st_size > 8192:
            raise ConfigError("Bridge configuration is too large")
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)
    except (OSError, ValueError) as exc:
        if isinstance(exc, ConfigError):
            raise
        raise ConfigError("Cannot read private bridge configuration; run the installer") from None
    # Only `secret` is required; version/read_only are tolerated and ignored like the runtimes do.
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("secret"), str)
        or re.fullmatch(r"[0-9a-f]{64}", value["secret"]) is None
    ):
        raise ConfigError("Invalid bridge configuration; preserve it and repair it locally")
    return value


def ensure_config() -> dict:
    """Create privately before writing a secret; publish without overwriting."""
    path = config_path()
    if path.exists():
        return load_config()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    checked_path(path)
    fd, name = tempfile.mkstemp(prefix=".bridge-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            if os.name == "nt":
                _windows_set_private(temporary)
            else:
                os.chmod(temporary, 0o600)
            _check_private(temporary)
            json.dump({"version": 1, "secret": secrets.token_hex(32), "read_only": True}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            pass  # A concurrent installer won; validate and preserve its configuration.
        return load_config()
    except (OSError, subprocess.SubprocessError) as exc:
        raise ConfigError(
            "Cannot provision private configuration; check directory access and ACLs"
        ) from exc
    finally:
        temporary.unlink(missing_ok=True)
