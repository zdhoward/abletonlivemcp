"""Stdlib-only configuration shared with the installed Live Remote Script.

ABLETONLIVEMCP_CONFIG must name an absolute file; otherwise both runtimes use
~/.abletonlivemcp/bridge.json. Only the installer provisions configuration.
"""

from __future__ import annotations

import csv
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
    result = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        check=True, capture_output=True, text=True,
    )
    sid = next(csv.reader(result.stdout.splitlines()))[-1]
    if not re.fullmatch(r"S-1-[0-9-]+", sid):
        raise ConfigError("Cannot establish the current Windows security principal")
    return sid


def _windows_sddl(path: Path) -> str:
    from ctypes import wintypes

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_security = advapi.GetNamedSecurityInfoW
    get_security.argtypes = [
        wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    get_security.restype = wintypes.DWORD
    stringify = advapi.ConvertSecurityDescriptorToStringSecurityDescriptorW
    stringify.argtypes = [
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(wintypes.LPWSTR), ctypes.c_void_p,
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
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
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
        aces = re.findall(r"\(([^()]*)\)", sddl)
        fields = aces[0].split(";") if len(aces) == 1 else []
        if (
            owner is None or owner[1] != sid or "D:P" not in sddl
            or len(fields) != 6 or fields[0] != "A"
            or fields[2] not in {"FA", "0x1f01ff"} or fields[5] != sid
        ):
            raise ConfigError("Bridge configuration ACL must grant only its owner full control")
    elif info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ConfigError("Bridge configuration must be owner-only (chmod 600)")


def load_config() -> dict:
    path = config_path()
    try:
        _check_private(path)
        if path.stat().st_size > 16384:
            raise ConfigError("Bridge configuration is too large")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        if isinstance(exc, ConfigError):
            raise
        raise ConfigError("Cannot read private bridge configuration; run the installer") from None
    if (
        not isinstance(value, dict) or type(value.get("version")) is not int
        or value["version"] != 1 or type(value.get("read_only")) is not bool
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
