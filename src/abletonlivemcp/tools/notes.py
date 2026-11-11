"""Note tools: read and add MIDI notes."""

from __future__ import annotations

from ..server import _call, _clip_ref, _create, _read


@_read
def live_get_notes(track: int, scene: int) -> dict:
    """Read up to 2000 MIDI notes starting within the clip length; check `truncated`."""
    return _call("get_notes", {"track": track, "scene": scene})


@_create
def live_add_notes(track: int, scene: int, notes: list[dict]) -> dict:
    """Add up to 2000 MIDI notes: pitch 0..127, start_time >= 0, duration > 0,
    velocity 1..127 and optional boolean mute. Not idempotent: notes are added, not replaced.
    Returns bounded note readback."""
    return _call("add_notes", {"clip": _clip_ref(track, scene), "notes": notes})
