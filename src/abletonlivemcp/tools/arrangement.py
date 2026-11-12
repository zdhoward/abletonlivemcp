"""Toolset `arrangement`: arrangement reads, clips and cue points (Live 12.2 limits: P-08/P-19)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..models import ResponseFormat, TrackSel
from ..models_clips import ArrangementEdit, CueAdd, CueEdit, NewArrangementClip, Span
from ..server import (
    _call,
    _create,
    _generation,
    _overwrite,
    _read,
    _untrusted,
    clip_selector,
    issue_refs,
    shape,
)
from .clips import fields

Part = Literal["clips", "cues", "take_lanes"]
CONCISE = ("arrangement", "name", "kind", "start", "end", "muted")


@_read
def live_get_arrangement(
    tracks: list[TrackSel] | None = None,
    range: Span | None = None,  # noqa: A002 - the planned parameter name
    include: list[Part] | None = None,
    response_format: ResponseFormat = "concise",
    cursor: Annotated[str, Field(max_length=64)] | None = None,
) -> dict:
    """Arrangement clips per track (index = order by start), take lanes, cue points (index =
    order by time), song length and loop. 256 clip rows per reply. With `tracks`, a longer read
    is cut (truncated). Without, it reads the whole Set in pages: when a reply has `cursor`,
    call again with it (same other arguments) to continue exactly there, even inside a track
    (that row says partial). A stale cursor is refused. Group tracks: rows say group: true."""
    params = {"include": include or ["clips", "cues"]}
    if tracks is not None:
        params["tracks"] = tracks
    if cursor is not None:
        params["cursor"] = cursor
    if range is not None:
        params["range"] = range
    out = _call("get_arrangement", params)
    for row in out.get("tracks", []):
        for holder in [row, *row.get("take_lanes", [])]:
            if "clips" in holder:
                holder["clips"] = shape(holder["clips"], response_format, CONCISE)
    return _untrusted(out)


@_create
def live_create_arrangement_clips(clips: list[NewArrangementClip]) -> dict:
    """New arrangement clips at `start` beats: MIDI (length, notes) or audio (absolute file;
    placed after the track's last clip), or from_session (scene index on the same track;
    copies notes and Session automation to the timeline). Overlaps refuse. Copies are kept;
    direct arrangement envelope reads are unavailable. replace=True deletes only clips wholly
    inside the destination span (needs the local delete permission and your confirmation).
    Take lanes refuse on 12.2."""
    refs = issue_refs([{"kind": "track", "track": c.track} for c in clips])
    targets = [{"ref": r["ref"], **fields(c, ("track",))} for r, c in zip(refs, clips, strict=True)]
    return _call("create_arrangement_clips", {"targets": targets})


@_overwrite
def live_edit_arrangement_clips(targets: list[ArrangementEdit]) -> dict:
    """Set arrangement clip fields (as live_set_clips). move_to, split_at and take-lane clips
    refuse on Live 12.2; delete with live_delete."""
    refs = issue_refs([{**clip_selector(t.clip), "expect_name": t.expect_name} for t in targets])
    items = [
        {"ref": r["ref"], "expect_name": r["expect_name"], **fields(t, ("clip",))}
        for r, t in zip(refs, targets, strict=True)
    ]
    return _call("edit_arrangement_clips", {"targets": items})


@_overwrite
def live_set_cue_points(cues: list[CueEdit] | None = None, add: list[CueAdd] | None = None) -> dict:
    """Rename/jump/delete cues (index from live_get_arrangement) and add cues at exact times
    (transport stopped; an existing cue there is reused). Deleting needs the local delete
    permission and your confirmation. Adds and deletes run as an operation: poll
    live_get_operation until ready."""
    refs = issue_refs([{"kind": "cue", "cue": c.cue} for c in cues]) if cues else []
    params: dict = {
        "cues": [
            {"cue": r["ref"], **fields(c, ("cue",))} for r, c in zip(refs, cues or [], strict=True)
        ]
    }
    if add:
        params["add"] = [a.model_dump(exclude_none=True) for a in add]
        params["generation"] = _generation()
    return _call("set_cue_points", params)
