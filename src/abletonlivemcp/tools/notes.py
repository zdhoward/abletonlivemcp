"""Note tools: read and edit MIDI notes with IDs and every extended field."""

from __future__ import annotations

from collections import Counter
from typing import Annotated, Literal

from pydantic import Field

from ..models import ClipRef, ExpectName
from ..models_clips import (
    READ_PAGE,
    Ids,
    NoteMods,
    NoteRange,
    Notes,
    Quantize,
    Region,
    Transpose,
)
from ..server import _call, _overwrite, _read, clip_selector, issue_refs, shape

NotesFormat = Literal["concise", "detailed", "summary"]  # summary: live_get_notes only


@_read
def live_get_notes(
    clip: ClipRef,
    pitch_from: Annotated[int, Field(ge=0, le=127)] = 0,
    pitch_span: Annotated[int, Field(ge=1, le=128)] = 128,
    time_from: Annotated[float, Field(ge=-16384, allow_inf_nan=False)] | None = None,
    time_span: Annotated[float, Field(gt=0, le=65536, allow_inf_nan=False)] | None = None,
    limit: Annotated[int, Field(ge=1, le=READ_PAGE)] = READ_PAGE,
    cursor: Annotated[str, Field(max_length=64)] | None = None,
    response_format: NotesFormat = "detailed",
) -> dict:
    """Notes by time with note_id (detailed adds probability, velocity_deviation,
    release_velocity; summary gives this page's counts and ranges instead of rows).
    The default window includes notes past the clip end (past_clip_end
    counts them). More pages: call again with the same clip/window and the reply's `cursor`;
    all pages are one snapshot (single-use cursor, 10 min), refused if the clip is replaced or
    its notes change before the last page. A window over 12,000 notes refuses (beyond_scope)."""
    params = {**clip.model_dump(exclude_none=True), "pitch_from": pitch_from}
    params.update(pitch_span=pitch_span, limit=limit)
    if cursor is not None:
        params["cursor"] = cursor
    if time_from is not None:
        params["time_from"] = time_from
    if time_span is not None:
        params["time_span"] = time_span
    out = _call("get_notes", params)
    if response_format == "summary":
        return {**{k: v for k, v in out.items() if k != "notes"}, **summarize(out["notes"])}
    out["notes"] = shape(out["notes"], response_format, CONCISE)
    return out


CONCISE = ("note_id", "pitch", "start_time", "duration", "velocity", "mute")


def summarize(notes: list[dict]) -> dict:
    """Counts and ranges of one page of note rows."""
    counts = Counter(n["pitch"] for n in notes)
    starts = [n["start_time"] for n in notes]
    ends = [n["start_time"] + n["duration"] for n in notes]
    velocities = [n["velocity"] for n in notes]
    return {
        "note_count": len(notes),
        "distinct_pitches": sorted(counts),
        "pitch_counts": {str(p): counts[p] for p in sorted(counts)},
        "time_range": [min(starts), max(ends)] if notes else None,
        "velocity_range": [min(velocities), max(velocities)] if notes else None,
    }


@_overwrite
def live_edit_notes(
    clip: ClipRef,
    expect_name: ExpectName | None = None,
    add: Notes | None = None,
    modify: NoteMods | None = None,
    remove_ids: Ids | None = None,
    remove_range: NoteRange | None = None,
    transpose: Transpose | None = None,
    quantize: Quantize | None = None,
    duplicate_region: Region | None = None,
) -> dict:
    """Edit one MIDI clip's notes in one call: removes, then modify/transpose/quantize (by
    note_id from live_get_notes), then duplicate_region, then add. Validated first; receipt
    with exact counts and note_ids (at most 4000 ids in all, new notes first; past that
    note_ids_truncated is true and live_get_notes lists them)."""
    ref = issue_refs([{**clip_selector(clip), "expect_name": expect_name}])[0]
    params = {"targets": [{"kind": ref["kind"], "ref": ref["ref"], "expect_name": expect_name}]}
    parts = {
        "add": add,
        "modify": modify,
        "remove_ids": remove_ids,
        "remove_range": remove_range,
        "transpose": transpose,
        "quantize": quantize,
        "duplicate_region": duplicate_region,
    }
    params.update({k: _plain(v) for k, v in parts.items() if v is not None})
    return _call("edit_notes", params)


def _plain(value):
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value.model_dump(exclude_none=True) if hasattr(value, "model_dump") else value
