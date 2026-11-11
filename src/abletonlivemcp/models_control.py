"""Domain request models for batch 2 (session, tracks, scenes, recording, view; v2 fast track,
docs/plans/v2-contracts.md). Shared selectors and receipts come from ``abletonlivemcp.models``.

Kept compact on purpose: every field here is part of the core tool listing budget (40,000 bytes).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from .models import (
    MAX_TARGETS,
    BatchTarget,
    ClipAddr,
    DevicePath,
    ExpectName,
    Index,
    StructKind,
    TrackSel,
    _Model,
)

_NULL = {"type": "null"}


def _lean(schema: dict, _cls=None) -> None:
    """Budget: drop the model title, property titles, ``default: null`` and the ``null`` branch
    of optional fields from the advertised schema (validation still uses the real types)."""
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)
        if "default" in prop and prop["default"] is None:
            del prop["default"]
        branches = prop.get("anyOf")
        if branches and _NULL in branches:
            rest = [b for b in branches if b != _NULL]
            del prop["anyOf"]
            prop.update(rest[0] if len(rest) == 1 else {"anyOf": rest})


_LEAN = ConfigDict(frozen=True, extra="forbid", json_schema_extra=_lean)


class _Lean(_Model):
    model_config = _LEAN


class _LeanTarget(BatchTarget):
    model_config = _LEAN


Name = Annotated[str, Field(max_length=256)]
Color = Annotated[int, Field(ge=0, le=69)]
Bpm = Annotated[float, Field(ge=20, le=999)]
Signature = Annotated[list[Annotated[int, Field(ge=1, le=99)]], Field(min_length=2, max_length=2)]
Unit = Annotated[float, Field(ge=0, le=1)]
Pan = Annotated[float, Field(ge=-1, le=1)]
Db = Annotated[float, Field(le=6)]


def _batch(model):
    return Annotated[list[model], Field(min_length=1, max_length=MAX_TARGETS)]


def owner_kind(track) -> str:
    """A TrackSel -> its reference kind: ``track``, ``return_track`` or ``master``."""
    if track == "master":
        return "master"
    return "return_track" if isinstance(track, str) else "track"


# ---- session ----------------------------------------------------------------------------------

SessionSection = Literal[
    "transport", "loop", "scale", "groove", "quantization", "link", "extras", "selection",
    "undo", "cues",
]  # fmt: skip


class Loop(_Lean):
    """Arrangement loop (beats) and punch switches."""

    on: bool | None = None
    start: Annotated[float, Field(ge=0)] | None = None
    length: Annotated[float, Field(gt=0)] | None = None
    punch_in: bool | None = None
    punch_out: bool | None = None


class Scale(_Lean):
    root_note: Annotated[int, Field(ge=0, le=11)] | None = None
    scale_name: Annotated[str, Field(min_length=1, max_length=64)] | None = None
    scale_mode: bool | None = None


Amount = Annotated[float, Field(ge=0, le=100)]


class GrooveEdit(_Lean):
    """A groove-pool entry by index; amounts in percent (velocity -100..100)."""

    index: Index
    expect_name: ExpectName | None = None
    timing_amount: Amount | None = None
    quantization_amount: Amount | None = None
    random_amount: Amount | None = None
    velocity_amount: Annotated[float, Field(ge=-100, le=100)] | None = None


class Groove(_Lean):
    """Song groove amount 0..1.3125, swing 0..1, groove-pool entries."""

    amount: Annotated[float, Field(ge=0, le=1.3125)] | None = None
    swing: Unit | None = None
    pool: Annotated[list[GrooveEdit], Field(min_length=1, max_length=64)] | None = None


class Quantization(_Lean):
    """Live's enum indices (clip trigger 0..13, MIDI recording 0..8)."""

    clip_trigger: Annotated[int, Field(ge=0, le=13)] | None = None
    midi_recording: Annotated[int, Field(ge=0, le=8)] | None = None


class Link(_Lean):
    enabled: bool | None = None
    start_stop_sync: bool | None = None


TransportAction = Literal[
    "play", "stop", "continue", "stop_all_clips", "jump_to", "jump_by", "next_cue",
    "prev_cue", "tap_tempo", "nudge_up", "nudge_down", "back_to_arranger",
]  # fmt: skip


# ---- tracks and mixer -------------------------------------------------------------------------


class NewTrack(_Lean):
    kind: Literal["midi", "audio", "return"]
    index: Annotated[int, Field(ge=-1)] = -1
    name: Name | None = None
    color_index: Color | None = None


class Routing(_Lean):
    """Display names exactly as listed by live_get_tracks(include=['routing'])."""

    type: Annotated[str, Field(min_length=1, max_length=256)]
    channel: Name | None = None


class TrackEdit(_LeanTarget):
    track: TrackSel
    name: Name | None = None
    color_index: Color | None = None
    mute: bool | None = None
    solo: bool | None = None
    arm: bool | None = None
    monitoring: Literal["in", "auto", "off"] | None = None
    fold: bool | None = None
    input_routing: Routing | None = None
    output_routing: Routing | None = None


class SendEdit(_Lean):
    send: Index
    db: Db | None = None
    value: Unit | None = None


class MixerEdit(_LeanTarget):
    """dB values are matched within 0.05 dB; `volume`/`value` are raw 0..1."""

    track: TrackSel
    volume_db: Db | None = None
    volume: Unit | None = None
    pan: Pan | None = None
    sends: Annotated[list[SendEdit], Field(max_length=12)] | None = None
    activator: bool | None = None
    crossfade: Literal["A", "none", "B"] | None = None
    crossfader: Pan | None = None
    cue_volume_db: Db | None = None


IncludeTracks = Literal["mixer", "devices", "slots", "routing", "meters", "groups"]


# ---- scenes and launch ------------------------------------------------------------------------


class NewScene(_Lean):
    index: Annotated[int, Field(ge=-1)] = -1
    name: Name | None = None
    color_index: Color | None = None
    tempo: Bpm | None = None
    signature: Signature | None = None


class SceneEdit(_LeanTarget):
    """`tempo`/`signature` "off" disables the scene's own value."""

    scene: Index
    name: Name | None = None
    color_index: Color | None = None
    tempo: Bpm | Literal["off"] | None = None
    signature: Signature | Literal["off"] | None = None


class LaunchTarget(_Lean):
    """clip/slot: track+scene; scene: scene; track: track (stop only)."""

    kind: Literal["clip", "slot", "scene", "track"]
    track: TrackSel | None = None
    scene: Index | None = None


# ---- structural (live_delete / live_duplicate) --------------------------------------------------


class StructTarget(_LeanTarget):
    """track: track=N; return: track="return:N"; scene: scene; clip: track+scene or
    track+arrangement[+take_lane]; device: track+path. `to`: clip duplicate destination."""

    kind: StructKind
    track: TrackSel | None = None
    scene: Index | None = None
    arrangement: Index | None = None
    take_lane: Index | None = None
    path: DevicePath | None = None
    to: ClipAddr | None = None


# ---- recording and view -----------------------------------------------------------------------

RecordAction = Literal[
    "session_record", "arrangement_record", "overdub", "trigger_session_record",
    "capture_midi", "capture_and_insert_scene",
]  # fmt: skip

ViewAction = Literal[
    "show", "hide", "focus", "zoom", "scroll", "select", "audition", "stop_audition"
]
ViewName = Literal["Browser", "Arranger", "Session", "Detail", "Detail/Clip", "Detail/DeviceChain"]


class ViewTarget(_Lean):
    kind: Literal["track", "scene", "clip", "slot", "device"]
    track: TrackSel | None = None
    scene: Index | None = None
    path: DevicePath | None = None


# ---- batch parameter types (1..64 items) ----------------------------------------------------

NewTracks = _batch(NewTrack)
TrackEdits = _batch(TrackEdit)
MixerEdits = _batch(MixerEdit)
NewScenes = _batch(NewScene)
SceneEdits = _batch(SceneEdit)
LaunchTargets = _batch(LaunchTarget)
StructTargets = _batch(StructTarget)
