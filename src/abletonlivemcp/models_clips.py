"""Batch-3 tool inputs: clips, notes, arrangement, automation, audio editing, MIDI files.

Every clip is addressed by the shared ``ClipRef`` (``{track, scene}`` or ``{track,
arrangement[, take_lane]}``). Field bounds mirror the remote validation (which re-checks all).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from .models import ArrangementClipAddr, ClipAddr, ClipRef, DevicePath, ExpectName, Index
from .models import _Model as Model

Beats = Annotated[float, Field(ge=0, le=16384)]
Span = Annotated[list[float], Field(min_length=2, max_length=2)]
Name = Annotated[str, StringConstraints(max_length=256)]
Ids = Annotated[list[Index], Field(max_length=2000)]
Quant = Literal[
    "global", "none", "8 bars", "4 bars", "2 bars", "1 bar", "1/2", "1/2t", "1/4", "1/4t",
    "1/8", "1/8t", "1/16", "1/16t", "1/32",
]  # fmt: skip
WarpMode = Literal["beats", "tones", "texture", "re_pitch", "complex", "rex", "complex_pro"]
MixerRole = Literal["volume", "panning", "send", "track_activator", "crossfader"]


class Note(Model):
    pitch: Annotated[int, Field(ge=0, le=127)]
    start_time: Beats
    duration: Annotated[float, Field(gt=0, le=16384)]
    velocity: Annotated[float, Field(ge=1, le=127)] = 100
    mute: bool = False
    probability: Annotated[float, Field(ge=0, le=1)] = 1
    velocity_deviation: Annotated[float, Field(ge=-127, le=127)] = 0
    release_velocity: Annotated[float, Field(ge=0, le=127)] = 64


Notes = Annotated[list[Note], Field(max_length=2000)]


class ClipFields(Model):
    """Settable clip fields; loop/markers are [start, end] (widened before narrowing)."""

    name: Name | None = None
    color_index: Annotated[int, Field(ge=0, le=69)] | None = None
    muted: bool | None = None
    looping: bool | None = None
    loop: Span | None = None
    markers: Span | None = None
    launch_mode: Literal["trigger", "gate", "toggle", "repeat"] | None = None
    launch_quantization: Quant | None = None
    legato: bool | None = None
    velocity_amount: Annotated[float, Field(ge=0, le=1)] | None = None
    signature: Annotated[list[int], Field(min_length=2, max_length=2)] | None = None
    gain: Annotated[float, Field(ge=0, le=1)] | None = None
    pitch_coarse: Annotated[int, Field(ge=-48, le=48)] | None = None
    pitch_fine: Annotated[float, Field(ge=-50, le=50)] | None = None
    warping: bool | None = None
    warp_mode: WarpMode | None = None


class ClipEdit(ClipFields):
    clip: ClipRef
    expect_name: ExpectName | None = None


class NewClip(Model):
    track: Index
    scene: Index
    kind: Literal["midi", "audio"] = "midi"
    length: Annotated[float, Field(gt=0, le=1024)] = 4.0
    file: Annotated[str, StringConstraints(max_length=1024)] | None = None
    name: Name | None = None
    color_index: Annotated[int, Field(ge=0, le=69)] | None = None
    notes: Notes | None = None


class NoteMod(Model):
    note_id: Index
    pitch: Annotated[int, Field(ge=0, le=127)] | None = None
    start_time: Beats | None = None
    duration: Annotated[float, Field(gt=0, le=16384)] | None = None
    velocity: Annotated[float, Field(ge=1, le=127)] | None = None
    mute: bool | None = None
    probability: Annotated[float, Field(ge=0, le=1)] | None = None
    velocity_deviation: Annotated[float, Field(ge=-127, le=127)] | None = None
    release_velocity: Annotated[float, Field(ge=0, le=127)] | None = None


class NoteRange(Model):
    pitch_from: Annotated[int, Field(ge=0, le=127)] = 0
    pitch_span: Annotated[int, Field(ge=1, le=128)] = 128
    time_from: float
    time_span: Annotated[float, Field(gt=0)]


class Transpose(Model):
    semitones: Annotated[int, Field(ge=-127, le=127)]
    ids: Ids | None = None


class Quantize(Model):
    grid: Annotated[float, Field(gt=0, le=16)]
    amount: Annotated[float, Field(ge=0, le=1)] = 1.0
    ids: Ids | None = None


class Region(Model):
    start: float
    length: Annotated[float, Field(gt=0)]
    dest: Beats
    transpose: Annotated[int, Field(ge=-127, le=127)] = 0


# ---- arrangement ------------------------------------------------------------------------------


class NewArrangementClip(Model):
    track: Index
    start: Beats
    kind: Literal["midi", "audio", "from_session"] = "midi"
    scene: Index | None = None
    replace: bool = False
    length: Annotated[float, Field(gt=0, le=1024)] = 4.0
    file: Annotated[str, StringConstraints(max_length=1024)] | None = None
    name: Name | None = None
    notes: Notes | None = None
    take_lane: Index | None = None


class ArrangementEdit(ClipFields):
    clip: ArrangementClipAddr
    expect_name: ExpectName | None = None
    move_to: Beats | None = None
    split_at: Beats | None = None


class CueEdit(Model):
    cue: Index
    action: Literal["rename", "jump", "delete"]
    name: Name | None = None


class CueAdd(Model):
    time: Beats
    name: Name | None = None


# ---- automation -------------------------------------------------------------------------------


class AutoParam(Model):
    """A device parameter (``device`` path + ``parameter`` name or index) or a mixer control."""

    device: DevicePath | None = None
    parameter: Index | Annotated[str, StringConstraints(max_length=120)] | None = None
    mixer: MixerRole | None = None
    send: Index | None = None


class Step(Model):
    time: Beats
    length: Annotated[float, Field(gt=0)]
    value: float


class Ramp(Model):
    start: Beats
    end: Beats
    from_: float = Field(alias="from")
    to: float
    steps: Annotated[int, Field(ge=2, le=256)] = 32


class Breakpoint(Model):
    time: Beats
    value: float


class AutomationEdit(Model):
    clip: ClipRef
    parameter: AutoParam
    steps: Annotated[list[Step], Field(max_length=512)] | None = None
    ramps: Annotated[list[Ramp], Field(max_length=16)] | None = None
    points: Annotated[list[Breakpoint], Field(min_length=2, max_length=3)] | None = None
    delete_range: Span | None = None
    clear: bool = False


# ---- audio editing ----------------------------------------------------------------------------


class WarpOp(Model):
    action: Literal["add", "move", "remove"]
    beat_time: float
    sample_time: Annotated[float, Field(ge=0)] | None = None
    distance: float | None = None


__all__ = [
    "ArrangementClipAddr", "ArrangementEdit", "AutoParam", "AutomationEdit", "ClipAddr",
    "ClipEdit", "ClipFields", "ClipRef", "CueAdd", "CueEdit", "NewArrangementClip", "NewClip",
    "Note", "NoteMod", "NoteRange", "Quantize", "Ramp", "Region", "Step", "Transpose", "WarpOp",
]  # fmt: skip
