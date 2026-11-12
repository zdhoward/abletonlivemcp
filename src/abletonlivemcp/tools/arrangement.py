"""Toolset `arrangement`: arrangement reads, clips and cue points (Live 12.2 limits: P-08/P-19)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..models import ResponseFormat, TrackSel
from ..models_clips import (
    ArrangementEdit,
    CueAdd,
    CueEdit,
    NewArrangementClip,
    Span,
    check_note_total,
)
from ..server import (
    Plan,
    _call,
    _create,
    _generation,
    _overwrite,
    _read,
    _untrusted,
    clip_selector,
    confirmed_plan,
    issue_refs,
    planned,
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
    order by time), song length and loop. 256 clip rows and 256 take lane rows per reply; a
    page also ends after about 4,096 clips and lanes scanned. With `tracks`, a longer read is
    cut (truncated). Without, it reads the whole Set in pages: when a reply has `cursor`, call
    again with it (same other arguments) to continue exactly there, even inside a track (that
    row says partial). A cursor is single use (10 min); one from a Set whose tracks changed, or
    with other arguments, is refused. Group tracks: rows say group: true. A track or take lane
    over 256 clips, or a track over 16 take lanes (with take_lanes), refuses (beyond_scope)."""
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


@planned("live_create_arrangement_clips")
def _plan_replace(args: dict) -> Plan:
    """replace=True: track references plus references to the clips each target deletes."""
    clips = args["clips"]
    tracks = issue_refs([{"kind": "track", "track": c.track} for c in clips])
    expect: list[list[str] | None] = []
    lines: list[str] = []
    for c in clips:
        if not (c.replace and c.kind == "from_session" and c.scene is not None):
            expect.append(None)  # nothing replaced here (the bridge refuses a bad replace)
            continue
        (source,) = _call("get_clips", {"clips": [{"track": c.track, "scene": c.scene}]})["clips"]
        if source.get("empty") or not isinstance(source.get("length"), int | float):
            expect.append(None)
            continue
        end = c.start + float(source["length"])
        (row,) = _call("get_arrangement", {"tracks": [c.track], "include": ["clips"]})["tracks"]
        hits = [k for k in row.get("clips", ()) if k["start"] < end and k["end"] > c.start]
        sels = [
            {"kind": "arr_clip", "track": c.track, "arrangement": k["arrangement"]} for k in hits
        ]
        found = issue_refs(sels) if sels else []  # nothing in the way: replace deletes nothing
        expect.append([r["ref"] for r in found])
        lines += [
            f"arrangement clip {r['name']!r} at beats {r.get('start_time')}-{r.get('end_time')}"
            f" on track {c.track}"
            for r in found
        ]
    return Plan(lines, {"tracks": tracks, "expect": expect})


@_create
def live_create_arrangement_clips(clips: list[NewArrangementClip]) -> dict:
    """New arrangement clips at `start` beats: MIDI (length, notes) or audio (absolute file;
    placed after the track's last clip), or from_session (scene index on the same track;
    copies notes and Session automation to the timeline). Overlaps refuse. Copies are kept;
    direct arrangement envelope reads are unavailable. replace=True deletes only clips wholly
    inside the destination span (needs the local delete permission and your confirmation).
    Take lanes refuse on 12.2."""
    check_note_total(clips)
    plan = None
    if any(c.replace for c in clips):  # the confirmed clips (or, unconfirmed, read now)
        plan = confirmed_plan() or _plan_replace({"clips": clips}).data
        refs = plan["tracks"]
    else:
        refs = issue_refs([{"kind": "track", "track": c.track} for c in clips])
    targets = [{"ref": r["ref"], **fields(c, ("track",))} for r, c in zip(refs, clips, strict=True)]
    if plan is not None:
        for target, expect in zip(targets, plan["expect"], strict=True):
            if expect is not None:
                target["expect_replace"] = expect
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


@planned("live_set_cue_points")
def _plan_cues(args: dict) -> Plan:
    """Cue references, issued now, bound to each cue's object and time."""
    cues = args.get("cues") or []
    refs = issue_refs([{"kind": "cue", "cue": c.cue} for c in cues]) if cues else []
    lines = [
        f"cue {r['name']!r} at beat {r.get('time')} (index {c.cue})"
        for r, c in zip(refs, cues, strict=True)
        if c.action == "delete"
    ]
    return Plan(lines, {"refs": refs})


@_overwrite
def live_set_cue_points(cues: list[CueEdit] | None = None, add: list[CueAdd] | None = None) -> dict:
    """Rename/jump/delete cues (index from live_get_arrangement) and add cues (transport
    stopped). Live 12.2 puts a new cue on the nearest bar: the result gives its `time` and the
    `requested` one. A cue at that time, or alone on that bar, is reused; another cue within
    half a bar refuses the add. Deleting needs the local delete permission and your
    confirmation. Adds and deletes run as an operation: poll live_get_operation only while it is
    pending; ready, failed and unknown are final. Then read its result `status` (complete,
    partial, not_applied) and any `cleanup_issue` (the playhead was not put back). After
    unknown, read the cues and playhead back before any further write. Not one undo step."""
    plan = confirmed_plan()  # deletes: the cues the human confirmed
    if plan is not None:
        refs = plan["refs"]
    else:
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
