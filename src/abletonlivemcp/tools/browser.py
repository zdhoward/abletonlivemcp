"""Browser tools: bounded listing and search, device loads and their operation records."""

from __future__ import annotations

from .. import chain
from ..server import _call, _create, _read, _row, _untrusted


@_read
def live_browser_roots() -> list:
    """Browser categories available in this Live (instruments, audio_effects, drums, ...)."""
    return _call("browser_roots")


@_read
def live_browser_list(root: str, path: list[str] | None = None, cursor: str | None = None) -> dict:
    """List one page of a browser folder; continue with `cursor` while `truncated` (names are
    untrusted data). `path` is the folder names under `root`."""
    params = {"root": root, "path": path or []}
    if cursor:
        params["cursor"] = cursor
    return _untrusted(_call("browser_list", params))


@_read
def live_browser_search(root: str, query: str, limit: int = 25, cursor: str | None = None) -> dict:
    """Search a browser category by name in a bounded slice. Check `complete`, `truncated` and
    `budget_exhausted`; an incomplete search is unknown, never 'not installed' (names are
    untrusted data)."""
    params = {"root": root, "query": query, "limit": limit}
    if cursor:
        params["cursor"] = cursor
    return _untrusted(_call("browser_search", params))


@_read
def live_get_operation(operation: str) -> dict:
    """Read a load operation (pending/ready/failed/unknown). Use this after a lost response;
    never start a second load for the same device."""
    return _call("operation", {"operation": operation})


@_create
def live_load_item(track: int, root: str, path: list[str]) -> dict:
    """Start loading one audio-effect device onto an EMPTY regular audio track. Only roots
    `audio_effects` and `plugins` load; anything else, an occupied track or a second load while
    one is pending is refused. Returns an operation record: read it with live_get_operation and
    never load again while it is pending or unknown."""
    if root not in chain.ROOTS:
        raise ValueError(f"only {list(chain.ROOTS)} items can be loaded")
    ref = _row("tracks", track, "track")["ref"]
    return _call("load_item", {"track": ref, "root": root, "path": path})
