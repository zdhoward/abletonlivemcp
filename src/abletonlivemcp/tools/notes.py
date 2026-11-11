"""Note tools: read and edit MIDI notes with IDs and every extended field."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ..models import ClipRef, ExpectName, ResponseFormat
from ..models_clips import Ids, NoteMod, NoteRange, Notes, Quantize, Region, Transpose
from ..server import _call, _overwrite, _read, clip_selector, issue_refs, shape


@_read
def live_get_notes(
    clip: ClipRef,
    pitch_from: Annotated[int, Field(ge=0, le=127)] = 0,
    pitch_span: Annotated[int, Field(ge=1, le=128)] = 128,
    time_from: Annotated[float, Field(ge=-16384, allow_inf_nan=False)] | None = None,
    time_span: Annotated[float, Field(gt=0, le=65536, allow_inf_nan=False)] | None = None,
    limit: Annotated[int, Field(ge=1, le=1000)] = 500,
    offset: Annotated[int, Field(ge=0, le=1000000)] = 0,
    response_format: ResponseFormat = "detailed",
) -> dict:
    """Notes by time with note_id (detailed adds probability, velocity_deviation,
    release_velocity); page with next_offset. The default window includes notes past the clip
    end (past_clip_end counts them)."""
    params = {**clip.model_dump(exclude_none=True), "pitch_from": pitch_from}
    params.update(pitch_span=pitch_span, limit=limit, offset=offset)
    if time_from is not None:
        params["time_from"] = time_from
    if time_span is not None:
        params["time_span"] = time_span
    out = _call("get_notes", params)
    out["notes"] = shape(out["notes"], response_format, CONCISE)
    return out


CONCISE = ("note_id", "pitch", "start_time", "duration", "velocity", "mute")


@_overwrite
def live_edit_notes(
    clip: ClipRef,
    expect_name: ExpectName | None = None,
    add: Notes | None = None,
    modify: list[NoteMod] | None = None,
    remove_ids: Ids | None = None,
    remove_range: NoteRange | None = None,
    transpose: Transpose | None = None,
    quantize: Quantize | None = None,
    duplicate_region: Region | None = None,
) -> dict:
    """Edit one MIDI clip's notes in one call: removes, then modify/transpose/quantize (by
    note_id from live_get_notes), then duplicate_region, then add. Validated first; receipt
    with new note_ids."""
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
