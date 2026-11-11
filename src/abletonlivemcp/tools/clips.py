"""Clip tools: read, create, fire and stop session clips."""

from __future__ import annotations

from ..server import _call, _clip_ref, _create, _overwrite, _read, _settled, _slot, _untrusted


@_read
def live_get_clip(track: int, scene: int) -> dict:
    """Read a clip's name, length, play state and looping state; empty slots raise an error."""
    return _untrusted(_call("get_clip", {"track": track, "scene": scene}))


@_create
def live_create_clip(track: int, scene: int, length_beats: float) -> dict:
    """Create a clip in an empty MIDI slot, length > 0 and <= 1024 beats; read it back."""
    slot = _slot(track, scene)
    return _call("create_clip", {"slot": slot["slot"], "length_beats": length_beats})


@_create
def live_fire_clip(track: int, scene: int) -> dict:
    """Launch a clip and return its current state (launch quantization applies)."""
    ref = _clip_ref(track, scene)
    return _settled("fire_clip", {"clip": ref}, "get_clip", {"track": track, "scene": scene})


@_overwrite
def live_stop_clip(track: int, scene: int) -> dict:
    """Stop a clip and return its current state."""
    ref = _clip_ref(track, scene)
    return _settled("stop_clip", {"clip": ref}, "get_clip", {"track": track, "scene": scene})
