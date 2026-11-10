"""Optional language judgments (sample type, plugin category) behind one small interface.

Two backends: `RuleJudge` (always available, filename/name keywords) and `JevJudge` (TypeSafe's
Jev model; needs the `jev` extra and TYPESAFE_API_KEY). Code decides from the judgments; a failed
Jev call raises JudgeError and is never turned into an answer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal, Protocol

Status = Literal["yes", "no", "unsure"]

DRUM_TYPES = (
    "kick",
    "snare",
    "clap",
    "hat_closed",
    "hat_open",
    "tom",
    "cymbal",
    "percussion",
)
PLUGIN_CATEGORIES = (
    "eq",
    "compressor",
    "limiter",
    "reverb",
    "delay",
    "saturation",
    "modulation",
    "filter",
    "synth",
    "sampler",
    "utility",
)

YES_AT = 0.7  # Noul thresholds from TypeSafe guidance; the band between is "unsure"
NO_AT = 0.3


def verdict(p: float) -> Status:
    return "yes" if p >= YES_AT else "no" if p <= NO_AT else "unsure"


class JudgeError(Exception):
    """The judging backend failed. Never treat this as a 'no'."""


@dataclass
class SampleJudgment:
    name: str
    one_shot: Status  # a single hit rather than a loop or phrase
    drum_type: str | None  # only set when the sample is judged a drum/percussion sound
    source: str
    detail: dict = field(default_factory=dict)


@dataclass
class PluginJudgment:
    name: str
    category: str | None  # only set when some category fits
    source: str
    detail: dict = field(default_factory=dict)


class Judge(Protocol):
    name: str

    def classify_sample(self, file_name: str, folders: list[str]) -> SampleJudgment: ...

    def classify_plugin(self, plugin_name: str, plugin_format: str | None) -> PluginJudgment: ...


def get_judge(prefer: str | None = None) -> Judge:
    """`prefer`/ABLETONLIVEMCP_JUDGE: 'rules', 'jev' (error if unavailable) or 'auto' (default)."""
    choice = (prefer or os.environ.get("ABLETONLIVEMCP_JUDGE") or "auto").lower()
    if choice not in ("auto", "rules", "jev"):
        raise ValueError("judge must be 'auto', 'rules' or 'jev'")
    from .rules import RuleJudge

    if choice == "rules":
        return RuleJudge()
    have_key = bool(os.environ.get("TYPESAFE_API_KEY"))
    try:
        from .jev import JevJudge

        if have_key or choice == "jev":
            return JevJudge()
    except ImportError as exc:
        if choice == "jev":
            raise JudgeError("jev backend needs: pip install 'abletonlivemcp[jev]'") from exc
    return RuleJudge()
