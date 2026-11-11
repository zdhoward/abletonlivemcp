"""Domain request/result models for batch devices (v2 fast track; see docs/plans/v2-contracts.md).

Owned by its batch; import shared selectors and receipts from ``abletonlivemcp.models``.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .models import (
    BatchTarget,
    DevicePath,
    ParamResult,
    PlanStage,
    RawValue,
    StageReceipt,
    Status,
    TrackSel,
    _Model,
)

Macro = Annotated[int, Field(ge=1, le=16)]
Note = Annotated[int, Field(ge=0, le=127)]
Value = RawValue | str | float | bool

TargetKind = Literal["audio_track", "midi_track", "return", "master", "chain", "drum_pad"]
REF_KIND = {  # a load/build target kind -> its bridge reference kind
    "audio_track": "track",
    "midi_track": "track",
    "return": "return_track",
    "master": "master",
    "chain": "chain",
    "drum_pad": "drum_pad",
}


def track_kind(track) -> str:
    """The reference kind of a TrackSel."""
    if track == "master":
        return "master"
    return "return_track" if isinstance(track, str) else "track"


def container_kind(track, path) -> str:
    """Reference kind of a container: the track itself, or the chain/pad a path ends at."""
    if not path:
        return track_kind(track)
    return "drum_pad" if isinstance(path[-1], str) else "chain"


# ---- devices -------------------------------------------------------------------------------


# One parameter write: a display target ("-18 dB", 4, "Vocal", true) or {"raw": x} in
# ``value``; or ``reset`` (its default); or ``re_enable_automation``.
class ParamWrite(_Model):
    parameter: str | Annotated[int, Field(ge=0)]
    value: Value | None = None
    reset: bool = False
    re_enable_automation: bool = False


class DeviceEdit(BatchTarget):
    track: TrackSel
    path: DevicePath
    on: bool | None = None
    name: str | None = Field(default=None, min_length=1, max_length=256)
    collapsed: bool | None = None


# ---- drums / racks / simpler ---------------------------------------------------------------


class PadEdit(_Model):
    note: Note
    mute: bool | None = None
    solo: bool | None = None
    name: str | None = Field(default=None, min_length=1, max_length=256)
    choke_group: Annotated[int, Field(ge=0, le=16)] | None = None
    clear: bool = False
    expect_name: str | None = Field(
        default=None, max_length=256, description="required with clear: the pad's current name"
    )


class PadCopy(_Model):
    source: Note
    destination: Note


# One pad of a planned Drum Rack: a browser item loaded onto pad ``note``.
class DrumRole(_Model):
    note: Note
    root: str = "samples"
    path: list[str] = Field(min_length=1, max_length=8)


class MacroSet(_Model):
    macro: Macro
    value: Value


# A rack chain (index): state and raw mixer values (volume/pan as stored 0..1 / -1..1).
class ChainEdit(_Model):
    index: Annotated[int, Field(ge=0)]
    name: str | None = Field(default=None, min_length=1, max_length=256)
    mute: bool | None = None
    solo: bool | None = None
    volume: float | None = None
    pan: float | None = None


class Variation(_Model):
    action: Literal["store", "recall", "delete", "randomize"]
    index: Annotated[int, Field(ge=0)] | None = None


class SliceEdit(_Model):
    insert: list[Annotated[int, Field(ge=0)]] = Field(default_factory=list, max_length=64)
    remove: list[Annotated[int, Field(ge=0)]] = Field(default_factory=list, max_length=64)
    clear: bool = False
    reset: bool = False


# What a conversion acts on: a clip (``scene`` or ``arrangement``), a device or drum pad
# (``path``), or the track's devices (track only).
class ConvertTarget(_Model):
    track: TrackSel
    scene: Annotated[int, Field(ge=0)] | None = None
    arrangement: Annotated[int, Field(ge=0)] | None = None
    path: DevicePath | None = None


# ---- plans and receipts (chain, FX rack, drum rack) ----------------------------------------


class MacroTarget(_Model):
    device: Annotated[int, Field(ge=0)] = Field(description="index among the wrapped devices")
    parameter: str = Field(max_length=120)
    min: str | float | None = None
    max: str | float | None = None


class MacroGroup(_Model):
    macro: Macro
    label: str | None = Field(default=None, max_length=60)
    value: Value | None = None
    targets: list[MacroTarget] = Field(default_factory=list, max_length=8)


# Wrap the target's existing audio effects (in order) into a new Audio Effect Rack.
class FxRack(_Model):
    groups: list[MacroGroup] = Field(default_factory=list, max_length=16)


# The device container a plan builds on, as read at plan time.
class BuildTarget(_Model):
    track: int | str
    path: tuple[int | str, ...] = ()
    kind: TargetKind
    name: str | None
    generation: int
    devices: tuple[str, ...] = ()  # class names: must be unchanged at build time


class BuildPlan(_Model):
    plan_id: str
    fingerprint: str
    mode: Literal["chain", "fx_rack", "drum_rack"] = "chain"
    target: BuildTarget
    stages: tuple[PlanStage, ...]
    containers: tuple[tuple[int | str, ...], ...] = ()  # per-stage path under the target
    groups: tuple[MacroGroup, ...] = ()
    report: tuple[dict, ...] = ()
    intent_complete: bool
    unverified: tuple[str, ...] = ()  # capabilities the build relies on, not yet Live-proven
    manual_steps: tuple[str, ...] = ()
    expires_in: float


class BuildReceipt(_Model):
    plan_id: str
    mode: str = "chain"
    status: Status
    intent_fulfilled: bool
    target: BuildTarget
    completed: tuple[int, ...] = ()
    stopped_at: int | None = None
    stop_reason: str | None = None
    omitted: tuple[str, ...] = ()
    unknown: tuple[str, ...] = ()
    stages: tuple[StageReceipt, ...] = ()
    unverified: tuple[str, ...] = ()
    manual_steps: tuple[str, ...] = ()


__all__ = [
    "REF_KIND",
    "BuildPlan",
    "BuildReceipt",
    "BuildTarget",
    "ChainEdit",
    "ConvertTarget",
    "DeviceEdit",
    "DrumRole",
    "FxRack",
    "MacroGroup",
    "MacroSet",
    "MacroTarget",
    "PadCopy",
    "PadEdit",
    "ParamResult",
    "ParamWrite",
    "SliceEdit",
    "Variation",
    "container_kind",
    "track_kind",
]
