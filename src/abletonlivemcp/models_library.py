"""Models for the label, scan and knowledge tools (batch 5).

Label scopes. A label names a thing and gives it free tags and one category:

- ``song`` / ``track`` / ``return_track`` labels live inside the Set (Live's ``get_data`` store on
  the Song or Track, so they travel with the file; P-02). ``key`` is the track or return index.
- ``plugin`` / ``device`` / ``sample`` labels are global: they live in the sidecar file of
  ``labelstore`` and apply across Sets. ``key`` is the usage key (``vst3:Serum``, ``Reverb``, a
  sample path) as ``live_usage_report`` prints it.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, model_validator

MAX_LABEL_ITEMS = 64
MAX_LABELS = 16
MAX_LABEL_CHARS = 40
MAX_KEY_CHARS = 300

LabelKind = Literal["song", "track", "return_track", "plugin", "device", "sample"]
SET_KINDS = ("song", "track", "return_track")
TRACK_KINDS = ("track", "return_track")
LabelMode = Literal["replace", "add", "remove"]

Label = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=MAX_LABEL_CHARS,
        pattern=r"^[^\x00-\x1f\x7f]+$",
    ),
]


class LabelItem(BaseModel):
    """One thing's labels. With ``mode: replace`` empty ``labels`` and no ``category`` clear the
    entry; ``add`` and ``remove`` change only the listed labels (``remove`` with ``category: ""``
    drops the category too)."""

    model_config = ConfigDict(extra="forbid")

    kind: LabelKind
    key: StrictInt | str | None = Field(
        None, description="Track/return index; usage key for plugin/device/sample; none for song"
    )
    labels: list[Label] = Field(default_factory=list, max_length=MAX_LABELS)
    category: Annotated[str, StringConstraints(strip_whitespace=True, max_length=40)] | None = None
    expect_name: str | None = Field(None, description="Track kinds: refuse unless named exactly so")

    @model_validator(mode="after")
    def _shape(self):
        if self.kind == "song":
            if self.key is not None or self.expect_name is not None:
                raise ValueError("song labels take no key or expect_name")
        elif self.kind in TRACK_KINDS:
            if isinstance(self.key, bool) or not isinstance(self.key, int) or self.key < 0:
                raise ValueError(f"{self.kind} labels need a key: the 0-based index")
        else:
            if not isinstance(self.key, str) or not 1 <= len(self.key) <= MAX_KEY_CHARS:
                raise ValueError(f"{self.kind} labels need a text key (1..{MAX_KEY_CHARS} chars)")
            if any(ord(c) < 32 or ord(c) == 127 for c in self.key):
                raise ValueError("key must not contain control characters")
            if self.expect_name is not None:
                raise ValueError("expect_name applies to track labels only")
        return self


class LabelFilter(BaseModel):
    """Which labels a read returns."""

    model_config = ConfigDict(extra="forbid")

    scope: Literal["set", "global", "both"] = "both"
    kind: LabelKind | None = None
    label: str | None = None
