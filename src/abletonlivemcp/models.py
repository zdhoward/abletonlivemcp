"""Typed plan and receipt models for chain building (host side only).

A plan is immutable review content, not approval: it records what would be built and the target
preconditions. A receipt records what actually happened, stage by stage, including originals,
omissions and unknown outcomes. ``status`` is how far execution got; ``intent_fulfilled`` is a
separate whole-intent flag that omitted or off-target settings keep false.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["complete", "partial", "failed", "pending"]


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


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
