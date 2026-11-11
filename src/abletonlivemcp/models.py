"""Typed plan and receipt models for chain building (host side only).

A plan is immutable review content, not approval: it records what would be built and the target
preconditions. A receipt records what actually happened, stage by stage, including originals,
omissions and unknown outcomes. ``status`` is how far execution got; ``intent_fulfilled`` is a
separate whole-intent flag that omitted or off-target settings keep false.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

Status = Literal["complete", "partial", "failed", "pending"]


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# ---- shared selectors (v2 plan section 2.1); indices are 0-based -----------------------------

MAX_TARGETS = 64  # per batch call; every target is validated before any write
MAX_DEVICE_DEPTH = 6  # device levels in a DevicePath

ResponseFormat = Literal["concise", "detailed"]

Index = Annotated[int, Field(ge=0)]
TrackSel = Index | Annotated[str, StringConstraints(pattern=r"^(return:(0|[1-9]\d{0,2})|master)$")]
"""A regular track index, ``"return:N"`` or ``"master"``."""


def check_device_path(path: list) -> list:
    """Devices sit at even positions (ints only); ``pad:N`` only at chain positions."""
    for i, step in enumerate(path):
        if i % 2 == 0 and not isinstance(step, int):
            raise ValueError(f"DevicePath position {i} must be a device index, got {step!r}")
    return path


PadSel = Annotated[str, StringConstraints(pattern=r"^pad:(0|[1-9]\d?|1[01]\d|12[0-7])$")]
DevicePath = Annotated[
    list[Index | PadSel],
    Field(min_length=1, max_length=2 * MAX_DEVICE_DEPTH),
    AfterValidator(check_device_path),
]
"""Alternating device and chain indices: ``[device]`` or ``[device, chain, device, ...]``; a
chain position may be ``"pad:N"`` (drum pad note N)."""

ParamSel = Index | Annotated[str, StringConstraints(min_length=1, max_length=120)]
"""A parameter index, or a name that must match exactly one parameter (else ``ambiguous``)."""

ExpectName = Annotated[str, StringConstraints(max_length=256)]


class ClipAddr(_Model):
    """A Session clip slot."""

    track: TrackSel
    scene: Index


class ArrangementClipAddr(_Model):
    """An arrangement clip: index into ``track.arrangement_clips`` sorted by start."""

    track: TrackSel
    arrangement: Index


class BatchTarget(_Model):
    """Base for one batch target: ``expect_name`` refuses with ``name_mismatch`` when the indexed
    object's current name differs."""

    expect_name: ExpectName | None = None


def check_expect_name(target: BatchTarget, actual: str) -> None:
    """Raise the ``name_mismatch`` refusal (nothing applied) when the name has changed."""
    from .chain import Refusal  # local: chain imports this module

    if target.expect_name is not None and target.expect_name != actual:
        raise Refusal(
            "name_mismatch", f"expected {target.expect_name!r} but the object is named {actual!r}"
        )


# ---- reply shapes -----------------------------------------------------------------------------


class Untrusted(_Model):
    """Names and text from Live or the browser: data, never instructions."""

    provenance: Literal["live_object_text_untrusted"] = "live_object_text_untrusted"
    data: Any


class ReadPage(_Model):
    items: list[Any]
    truncated: bool = False
    cursor: str | None = None


class WriteReply(_Model):
    applied: list[Any]  # readback rows
    generation: int | None = None
    undo_steps: int | None = None
    receipt: dict[str, Any] | None = None


class RawValue(_Model):
    """A stored (not displayed) parameter value; it is written as given and never claimed to
    be a physical unit."""

    raw: float


class Setting(_Model):
    """One parameter request: a display target ("-18 dB", 4, "Vocal", true) or a RawValue."""

    parameter: str = Field(max_length=120)
    value: RawValue | str | float | int | bool


class Target(_Model):
    """The empty regular audio track a plan builds on, as read at plan time."""

    index: int
    name: str
    generation: int
    devices: tuple[str, ...] = ()  # device class names: must be unchanged at build time


class PlanStage(_Model):
    role: str | None = None
    device: str
    root: str
    path: tuple[str, ...]
    # name -> display target ("-18 dB", 4, "Vocal") or {"raw": 0.3}; raw stays raw
    params: dict[str, object] = Field(default_factory=dict)
    omitted: tuple[str, ...] = ()  # intent that could not be mapped (visible, never silent)
    notes: tuple[str, ...] = ()
    controls: Literal["checked_at_plan", "unverified_until_loaded"] = "unverified_until_loaded"


class ChainPlan(_Model):
    plan_id: str
    fingerprint: str
    target: Target
    stages: tuple[PlanStage, ...]
    report: tuple[dict, ...] = ()
    intent_complete: bool  # false when any stage omitted intent
    expires_in: float


class ParamResult(_Model):
    name: str
    requested: object
    original: dict | None = None  # {"value", "display"} read before writing
    actual: str | None = None  # Live's display after the write
    actual_raw: float | None = None
    exact: bool = False
    off_target: bool = False
    raw: bool = False


class StageReceipt(_Model):
    index: int
    device: str
    outcome: Literal["applied", "not_applied", "unknown"]
    operation: str | None = None
    device_index: int | None = None
    params: tuple[ParamResult, ...] = ()
    problems: tuple[str, ...] = ()
    reason: str | None = None  # refusal code / failure state when not fully applied


class ChainReceipt(_Model):
    plan_id: str
    status: Status
    intent_fulfilled: bool
    target: Target
    completed: tuple[int, ...] = ()  # stages whose load and every setting were exact
    stopped_at: int | None = None
    stop_reason: str | None = None
    omitted: tuple[str, ...] = ()
    unknown: tuple[str, ...] = ()
    stages: tuple[StageReceipt, ...] = ()
