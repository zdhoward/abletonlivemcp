"""Session tools: handshake, Set summary and transport."""

from __future__ import annotations

import time

from .. import server
from ..server import _call, _generation, _overwrite, _read


@_read
def live_hello() -> dict:
    """Handshake with Live: protocol version, Live version, generation, capabilities and the
    enabled and available toolsets."""
    return {**_call("hello"), "toolsets": server.toolsets()}


@_read
def live_session_info() -> dict:
    """Tempo, play state, time signature, counts and the Set generation of the open Set."""
    return _call("session_info")


@_read
def live_get_transport() -> dict:
    """Read play state, tempo, time signature and current song time in beats."""
    return _call("get_transport")


@_overwrite
def live_set_transport(tempo: float | None = None, playing: bool | None = None) -> dict:
    """Set the tempo (20..999 BPM) and/or start (true) or stop (false) playback. Returns the
    transport as read back after Live applied it."""
    if tempo is None and playing is None:
        raise ValueError("give a tempo and/or playing")
    generation = _generation()
    if tempo is not None:
        _call("set_tempo", {"bpm": tempo, "generation": generation})
    if playing is not None:
        _call("play" if playing else "stop", {"generation": generation})
    time.sleep(server.SETTLE_SECONDS)
    return _call("get_transport")
