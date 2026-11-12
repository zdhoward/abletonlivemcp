"""Path confinement for offline file reads (Sets, knowledge pages).

A path is accepted only when it is absolute, free of ``..`` and device/stream syntax, lies under a
configured root, and no component below that root is a symlink, junction or other reparse point
(``FILE_ATTRIBUTE_REPARSE_POINT``, which ``os.walk`` and ``Path.is_symlink`` miss for junctions).
The fully resolved path must also stay under the root's resolved path. Files are opened once and
checked against the identity seen before opening, so a swap between check and open is refused.

Roots: the environment variable ``ABLETONLIVEMCP_ALS_ROOTS`` (``os.pathsep`` separated) and the
optional ``als_roots`` list in the private bridge config. Nothing is allowed when none is set.
"""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Iterable, Sequence
from pathlib import Path

from ..errors import Invalid

ROOTS_ENV = "ABLETONLIVEMCP_ALS_ROOTS"
REPARSE = 0x400  # FILE_ATTRIBUTE_REPARSE_POINT
_PARTS = re.compile(r"[\\/]+")


class PathEscape(Invalid):
    """A path that leaves the configured roots or crosses a link."""


def is_reparse(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & REPARSE)


def configured_roots() -> list[Path]:
    """Existing absolute directories named by the environment and the private config."""
    raw = [r for r in os.environ.get(ROOTS_ENV, "").split(os.pathsep) if r.strip()]
    try:
        from ..config import load_config

        extra = load_config().get("als_roots")
        if isinstance(extra, list):
            raw += [r for r in extra if isinstance(r, str)]
    except ValueError:  # ConfigError: no private config, or an invalid one
        pass
    roots: list[Path] = []
    for item in raw:
        if os.path.isabs(item) and os.path.isdir(item):
            path = Path(os.path.abspath(item))
            if path not in roots:
                roots.append(path)
    return roots


def _syntax(text: str) -> None:
    if "\x00" in text:
        raise PathEscape("path contains a NUL byte")
    if text.startswith(("\\\\?\\", "\\\\.\\", "//?/", "//./")):
        raise PathEscape("device paths are not allowed")
    if ":" in os.path.splitdrive(text)[1]:
        raise PathEscape("a colon is only allowed as the drive separator (no streams)")
    if ".." in _PARTS.split(text):
        raise PathEscape("'..' is not allowed in a path")
    if not os.path.isabs(text):
        raise PathEscape("path must be absolute")


def _under(key: str, base: str) -> bool:
    base = base.rstrip("\\/")
    return key == base or key.startswith(base + os.sep)


def _no_reparse_below(base: str, full: str) -> None:
    """Every existing component from ``base`` (excluded) down to ``full`` must be a plain entry."""
    current = base
    for part in [p for p in _PARTS.split(os.path.relpath(full, base)) if p and p != "."]:
        current = os.path.join(current, part)
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return
        if is_reparse(info):
            raise PathEscape(f"symlink/junction/reparse point in the path: {part}")


def confine(path: str | os.PathLike, roots: Sequence[str | os.PathLike]) -> Path:
    """The validated absolute path, or PathEscape. ``roots`` must already be absolute."""
    text = os.fspath(path)
    _syntax(text)
    full = os.path.abspath(text)
    key = os.path.normcase(full)
    for root in roots:
        given = os.path.abspath(os.fspath(root))
        real = os.path.realpath(given)
        for base in dict.fromkeys((given, real)):
            if not _under(key, os.path.normcase(base)):
                continue
            _no_reparse_below(base, full)
            if _under(os.path.normcase(os.path.realpath(full)), os.path.normcase(real)):
                return Path(full)
    raise PathEscape("path is outside the configured roots")


def open_confined(path: str | os.PathLike, roots: Sequence[str | os.PathLike]):
    """``(binary file object, os.stat_result)`` of a confined regular file, opened once."""
    full = confine(path, roots)
    before = os.lstat(full)
    if is_reparse(before) or not stat.S_ISREG(before.st_mode):
        raise PathEscape("not a plain regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(full, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or (before.st_dev, before.st_ino) != (
            info.st_dev,
            info.st_ino,
        ):
            raise PathEscape("the file changed while it was being opened")
        return os.fdopen(fd, "rb"), info
    except BaseException:
        os.close(fd)
        raise


def plain_entries(directory: str | os.PathLike) -> Iterable[os.DirEntry]:
    """Directory entries that are not links, sorted by name; reparse entries are skipped."""
    with os.scandir(directory) as it:
        entries = sorted(it, key=lambda e: e.name.lower())
    for entry in entries:
        try:
            if not is_reparse(entry.stat(follow_symlinks=False)):
                yield entry
        except OSError:
            continue
