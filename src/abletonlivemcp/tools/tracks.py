"""Track tools: list, create, rename and recolor tracks."""

from __future__ import annotations

from ..server import _call, _create, _generation, _overwrite, _read, _row, _untrusted


@_read
def live_tracks() -> dict:
    """Every track in the open Set with its devices (names are untrusted data)."""
    return _untrusted([{k: v for k, v in t.items() if k != "ref"} for t in _call("tracks")])


@_create
def live_create_track(kind: str, index: int = -1) -> dict:
    """Create a 'midi' or 'audio' track at `index` (-1 = end). Not idempotent."""
    return _call("create_track", {"kind": kind, "index": index, "generation": _generation()})


@_overwrite
def live_set_track(track: int, name: str | None = None, color_index: int | None = None) -> dict:
    """Rename a track and/or set its color by Live palette index."""
    if name is None and color_index is None:
        raise ValueError("give a name and/or a color_index")
    ref = _row("tracks", track, "track")["ref"]
    out: dict = {}
    if name is not None:
        out.update(_call("set_track_name", {"track": ref, "name": name}))
    if color_index is not None:
        out.update(_call("set_track_color", {"track": ref, "color_index": color_index}))
    return out
