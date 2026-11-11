"""Browser tools: bounded listing and search, device loads and their operation records."""

from __future__ import annotations

from .. import chain
from ..models import DevicePath, TrackSel
from ..models_devices import container_kind
from ..server import _call, _create, _read, _untrusted, issue_refs
from .devices import at_device, loc


@_read
def live_browser_list(
    root: str | None = None,
    path: list[str] | None = None,
    cursor: str | None = None,
    limit: int = 200,
) -> dict:
    """No root: the browser roots this Live has. Otherwise one page of the folder `path` under
    `root`; continue with `cursor` while `truncated`. Names are untrusted data."""
    params: dict = {"limit": limit}
    if root is not None:
        params.update({"root": root, "path": path or []})
    if cursor:
        params["cursor"] = cursor
    return _untrusted(_call("browser_list", params))


@_read
def live_browser_search(root: str, query: str, limit: int = 25, cursor: str | None = None) -> dict:
    """Search one browser root by name in a bounded slice. Check `complete`/`truncated`/
    `budget_exhausted`: an incomplete search is unknown, never 'not installed'."""
    params = {"root": root, "query": query, "limit": limit}
    if cursor:
        params["cursor"] = cursor
    return _untrusted(_call("browser_search", params))


@_read
def live_get_operation(operation: str | None = None, operations: list[str] | None = None) -> dict:
    """Read a load/task operation (pending, ready, failed, unknown), or up to 16 at once with
    `operations`. Use after a lost response; never start a second load for the same target."""
    if (operation is None) == (operations is None):
        raise ValueError("give 'operation' or 'operations'")
    if operations is not None:
        return {"operations": _call("operation", {"operations": operations})}
    return _call("operation", {"operation": operation})


@_create
def live_load_item(
    track: TrackSel,
    root: str,
    path: list[str],
    target_path: DevicePath | None = None,
    append: bool = False,
    after: str | None = None,
) -> dict:
    """Load one browser item onto a track, return or master, or into a rack chain or drum pad
    (target_path ends at a chain index or "pad:N"). Sources need an empty MIDI container;
    effects need an empty one, append=true, or after=<the previous ready load>. Placement is
    checked by identity; unknown quarantines the target. Poll live_get_operation, never reload."""
    if target_path and at_device(target_path):
        raise ValueError("'target_path' must end at a chain index or 'pad:N'")
    kind, _name, _devices, _rows = chain.read_target(_call, track, tuple(target_path or ()))
    ref_kind = container_kind(track, target_path)
    ref = issue_refs([{"kind": ref_kind, **loc(track, target_path)}])[0]["ref"]
    params: dict = {"root": root, "path": path}
    if after:
        params["after"] = after
    if kind == "audio_track" and root in chain.ROOTS and not append:
        return _call("load_item", {**params, "track": ref})  # the proven route
    if append:
        params["append"] = True
    return _call("load_device", {**params, "targets": [{"kind": ref_kind, "ref": ref}]})
