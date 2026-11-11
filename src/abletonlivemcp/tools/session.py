"""Session tools: handshake/diagnostics, session state (song extras included), transport, undo."""

from __future__ import annotations

import time
from typing import Annotated, Literal

from pydantic import Field

from .. import server
from ..models_control import (
    Bpm,
    Groove,
    Link,
    Loop,
    Quantization,
    Scale,
    SessionSection,
    Signature,
    TransportAction,
)
from ..server import _call, _control, _generation, _overwrite, _read, _untrusted


@_read
def live_hello() -> dict:
    """Handshake: protocol, Live version, build id, variant, generation, read_only and
    dev_probes (bridge config, re-read per call), dialogs and CPU,
    capability_report (supported/unverified/disabled/unsupported per ability) and toolsets.
    Call first; current tempo/transport state is in live_get_session."""
    return {**_call("hello"), "toolsets": server.toolsets()}


@_read
def live_get_session(include: list[SessionSection] = None) -> dict:
    """Session state: tempo, signature, counts, plus sections (default all): transport, loop
    and punch, scale, groove pool, quantization, Link, extras (count-in, tuning; read-only),
    selection, undo, cues. Names are untrusted data."""
    return _untrusted(_call("get_session", {"include": include} if include else {}))


@_overwrite
def live_set_session(
    tempo: Bpm = None,
    signature: Signature = None,
    metronome: bool = None,
    loop: Loop = None,
    scale: Scale = None,
    groove: Groove = None,
    quantization: Quantization = None,
    link: Link = None,
    count_in: int = None,
) -> dict:
    """Set tempo (BPM), signature [num, den], metronome, loop/punch (beats), scale, groove
    (amount, swing, pool amounts), quantization (Live enum indices), Link. All validated
    before any write; each value is read back. count_in is read-only on Live 12.2."""
    if count_in is not None:
        raise server.unsupported("count_in", "Live 12.2 has no count-in setter (P-22)")
    params: dict = {"tempo": tempo, "signature": signature, "metronome": metronome}
    if loop is not None:
        fields = loop.model_dump(exclude_none=True)
        punch = {k[6:]: fields.pop(k) for k in ("punch_in", "punch_out") if k in fields}
        params.update(loop=fields or None, punch=punch or None)
    if scale is not None:
        params["scale"] = scale.model_dump(exclude_none=True)
    if groove is not None:
        params.update(groove_amount=groove.amount, swing_amount=groove.swing)
        if groove.pool:
            params["grooves"] = [g.model_dump(exclude_none=True) for g in groove.pool]
    if quantization is not None:
        params.update(
            clip_trigger_quantization=quantization.clip_trigger,
            midi_recording_quantization=quantization.midi_recording,
        )
    if link is not None:
        params.update(link_enabled=link.enabled, link_start_stop_sync=link.start_stop_sync)
    params = {k: v for k, v in params.items() if v is not None}
    if not params:
        raise ValueError("give at least one field to set")
    return _untrusted(_call("set_session", {**params, "generation": _generation()}))


@_control
def live_transport(action: TransportAction, beats: float = None) -> dict:
    """Transport: play, stop, continue, stop_all_clips, jump_to/jump_by (`beats`), cue jumps,
    tap_tempo, nudge, back_to_arranger. Returns the state read after Live settles.
    Clips and scenes: live_launch."""
    if action in ("jump_to", "jump_by") and beats is None:
        raise ValueError(f"{action} needs 'beats'")
    params = {"action": action, "generation": _generation()}
    if beats is not None:
        params["beats"] = beats
    reply = _call("transport", params)
    time.sleep(server.SETTLE_SECONDS)
    state = _call("get_session", {"include": ["transport"]})
    keys = ("is_playing", "current_song_time", "tempo")
    return {**reply, "settled": {k: state.get(k) for k in keys}}


@_control
def live_undo(
    action: Literal["undo", "redo"] = "undo", steps: Annotated[int, Field(ge=1, le=10)] = 1
) -> dict:
    """Undo or redo 1..10 steps of Live's history (each tool write is one step). Stops early
    when history runs out; reports done/requested."""
    return _call("undo", {"action": action, "steps": steps, "generation": _generation()})
