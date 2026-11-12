"""Clip tools: read, create and set Session and arrangement clips (one ClipRef address).

Delete and duplicate go through live_delete / live_duplicate (bridge routes delete_clips /
duplicate_clips); launch goes through live_launch.
"""

from __future__ import annotations

from typing import Literal

from ..models import ClipRef, ResponseFormat, TrackSel
from ..models_clips import ClipEdit, NewClip
from ..server import (
    Plan,
    _call,
    _create,
    _overwrite,
    _read,
    _untrusted,
    clip_selector,
    confirmed_plan,
    issue_refs,
    planned,
    shape,
)

CONCISE = ("track", "scene", "arrangement", "name", "kind", "length", "start", "is_playing")
CONCISE += ("empty",)


def fields(model, skip: tuple[str, ...]) -> dict:
    return model.model_dump(exclude_none=True, by_alias=True, exclude=set(skip))


@_read
def live_get_clips(
    clips: list[ClipRef] | None = None,
    track: TrackSel | None = None,
    scene: int | None = None,
    detail: bool = False,
    response_format: ResponseFormat = "concise",
) -> dict:
    """Clips by address, or scan Session clips (filter by track/scene; 128 rows max).
    detail=True adds launch, audio and warp-marker fields.
    Note contents: live_get_notes."""
    params = {"detail": detail or response_format == "detailed"}
    if clips is not None:
        params["clips"] = [c.model_dump(exclude_none=True) for c in clips]
    if track is not None:
        params["track"] = track
    if scene is not None:
        params["scene"] = scene
    out = _call("get_clips", params)
    if response_format == "concise" and not detail:
        out["clips"] = shape(out["clips"], response_format, CONCISE)
    return _untrusted(out)


def _occupied(clips: list[NewClip]) -> set[tuple[int, int]]:
    """Which requested slots already hold a clip (one read per 64 slots)."""
    found: set[tuple[int, int]] = set()
    for i in range(0, len(clips), 64):
        addrs = [{"track": c.track, "scene": c.scene} for c in clips[i : i + 64]]
        for row in _call("get_clips", {"clips": addrs})["clips"]:
            if not row.get("empty"):
                found.add((row["track"], row["scene"]))
    return found


@planned("live_create_clips")
def _plan_replace(args: dict) -> Plan:
    """if_exists='replace': slot references plus a reference to each occupant to delete."""
    clips = args["clips"]
    slots = issue_refs([{"kind": "slot", "track": c.track, "scene": c.scene} for c in clips])
    occupied = sorted(_occupied(clips))
    # every destination empty: nothing to delete (issue_refs refuses an empty list)
    occupants_sel = [{"kind": "clip", "track": t, "scene": s} for t, s in occupied]
    rows = issue_refs(occupants_sel) if occupants_sel else []
    lines = [
        f"Session clip {r['name']!r} (length {r.get('length')} beats) at track {t}, scene {s}"
        for (t, s), r in zip(occupied, rows, strict=True)
    ]
    occupants = {key: r["ref"] for key, r in zip(occupied, rows, strict=True)}
    return Plan(lines, {"slots": slots, "occupants": occupants})


@_create
def live_create_clips(
    clips: list[NewClip], if_exists: Literal["error", "skip", "replace"] = "error"
) -> dict:
    """Create clips in empty Session slots: MIDI (length beats, optional notes) or audio (file:
    absolute path, audio track). Returns readback with new note_ids. if_exists for an occupied
    slot: "error" (default; the whole batch is refused, nothing written), "skip" (leave that
    clip alone, create the rest; skipped slots are listed) or "replace" (validate everything,
    then delete the old clip and create; rows say replaced; needs the local "delete"
    permission and your confirmation). Re-running with skip or replace is idempotent.
    Arrangement: live_create_arrangement_clips; from a .mid: live_import_midi."""
    skipped: list[dict] = []
    if if_exists == "skip":
        busy = _occupied(clips)
        skipped = [{"track": t, "scene": s} for t, s in sorted(busy)]
        clips = [c for c in clips if (c.track, c.scene) not in busy]
    if not clips:
        return {
            "status": "complete", "items": [], "stopped_at": None, "error": None,
            "applied": [], "skipped": skipped,
        }  # fmt: skip
    plan = None
    if if_exists == "replace":  # the confirmed occupants (or, unconfirmed, read now)
        plan = confirmed_plan() or _plan_replace({"clips": clips}).data
        refs = plan["slots"]
    else:
        refs = issue_refs([{"kind": "slot", "track": c.track, "scene": c.scene} for c in clips])
    targets = []
    for r, c in zip(refs, clips, strict=True):
        target = {"ref": r["ref"], **fields(c, ("track", "scene"))}
        if plan is not None:
            target["replace"] = True
            occupant = plan["occupants"].get((c.track, c.scene))
            if occupant is not None:
                target["expect_clip"] = occupant
        targets.append(target)
    receipt = _call("create_clips", {"targets": targets})
    return {**receipt, "skipped": skipped} if skipped else receipt


@_overwrite
def live_set_clips(targets: list[ClipEdit]) -> dict:
    """Set clip fields (Session or arrangement). loop/markers are [start, end] beats; gain,
    pitch_*, warping, warp_mode need audio clips. Validates all, then writes; receipt.
    Notes: live_edit_notes; warp markers or crop: live_edit_audio_clip (editing toolset)."""
    refs = issue_refs([{**clip_selector(t.clip), "expect_name": t.expect_name} for t in targets])
    items = [
        {
            "kind": r["kind"],
            "ref": r["ref"],
            "expect_name": r["expect_name"],
            **fields(t, ("clip",)),
        }
        for r, t in zip(refs, targets, strict=True)
    ]
    return _call("set_clips", {"targets": items})
