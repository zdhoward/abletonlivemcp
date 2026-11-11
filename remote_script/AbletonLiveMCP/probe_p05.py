"""P-05: delete/duplicate calls: return values, index effects, undo.

Behavioural (write) probe. Every call is observed by readback and each observation is a small
entry in ``observations``. Objects: scratch tracks and scenes made through ``scratch``, one
temporary return track the probe creates and deletes itself (``finally``), and, for
``Track.delete_device`` / ``Chain.delete_device``, a duplicate of an existing track that has a
device (the original is only read; the duplicate is adopted into ``scratch``). Without such a
track those two calls are listed under ``not_observed`` and the verdict is ``no-go``.

Objects the probe deletes are forgotten from ``scratch.created``; objects a call creates
(duplicates, an undo restoring a track) are adopted into it so they are cleaned up.

Verdict: ``gated`` when any of the calls is absent on its class; ``go`` when every call was observed
and behaved as its readback expects; otherwise ``no-go``.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-05"
KIND = WRITE

REQUIRED = {
    "song": (
        "delete_track",
        "delete_return_track",
        "delete_scene",
        "duplicate_track",
        "duplicate_scene",
        "undo",
    ),
    "track": ("delete_device", "duplicate_clip_slot"),
    "slot": ("delete_clip", "duplicate_clip_to"),
}


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(missing_api, not_observed, failed):
    """Pure verdict rule (kept separate so it is unit-testable)."""
    if missing_api:
        return "gated"
    return "go" if not not_observed and not failed else "no-go"


def _find(seq, obj):
    for i, o in enumerate(seq):
        if _same(o, obj):
            return i
    return -1


def _forget(scratch, obj):
    scratch.created = [(k, o) for k, o in scratch.created if not _same(o, obj)]


def _adopt_new(scratch, kind, before, after):
    new = [o for o in after if not any(_same(o, b) for b in before)]
    for o in new:
        scratch.created.append((kind, o))
    return new


def _call(fn, *args):
    """(return value, error text) of one call."""
    try:
        return fn(*args), None
    except Exception as exc:  # noqa: BLE001 - the exact error text is the evidence
        return None, _err(exc)


def run(ctx, scratch):
    try:
        return _run(ctx, scratch)
    except Exception as exc:  # noqa: BLE001 - report where an unexpected error came from
        tb, lines = exc.__traceback__, []
        while tb is not None:
            lines.append(tb.tb_lineno)
            tb = tb.tb_next
        return {"verdict": "no-go", "unexpected_error": _err(exc), "lines": lines}


def _run(ctx, scratch):
    song = ctx.song
    probe_track = scratch.midi_track()  # also the clip-slot test track below
    owners = {"song": song, "track": probe_track, "slot": probe_track.clip_slots[0]}
    missing = [
        f"{k}.{n}" for k, names in REQUIRED.items() for n in names if not hasattr(owners[k], n)
    ]
    if missing:
        return {"verdict": "gated", "missing_api": missing}

    obs, not_observed, failed = {}, [], []

    def record(name, ok, **info):
        obs[name] = dict(info, ok=bool(ok))
        if not ok:
            failed.append(name)

    # delete_track: index effect on the tracks after it, and one undo.
    victim = scratch.midi_track()
    tail = scratch.midi_track()
    idx = _find(song.tracks, victim)
    n = len(song.tracks)
    ret, err = _call(song.delete_track, idx)
    gone = _find(song.tracks, victim) == -1
    shifted = _find(song.tracks, tail) == idx
    _forget(scratch, victim)
    undo = {"can_undo": None, "error": None, "restored": None}
    try:
        undo["can_undo"] = bool(song.can_undo)
    except Exception as exc:  # noqa: BLE001
        undo["can_undo"] = _err(exc)
    before = list(song.tracks)
    _, uerr = _call(song.undo)
    undo["error"] = uerr
    adopted = _adopt_new(scratch, "track", before, song.tracks)
    undo["restored"] = len(adopted) == 1
    undo["count_after_undo"] = len(song.tracks)
    record(
        "delete_track",
        err is None and gone and shifted and len(song.tracks) in (n - 1, n),
        index=idx,
        return_value=ret,
        error=err,
        count_before=n,
        removed=gone,
        later_track_shifted_down=shifted,
        undo=undo,
    )

    # duplicate_track: where the copy lands and what is selected.
    src = scratch.midi_track()
    src_i = _find(song.tracks, src)
    before = list(song.tracks)
    ret, err = _call(song.duplicate_track, src_i)
    new = _adopt_new(scratch, "track", before, song.tracks)
    landed = _find(song.tracks, new[0]) if len(new) == 1 else None
    record(
        "duplicate_track",
        err is None and len(new) == 1 and landed == src_i + 1,
        source_index=src_i,
        return_value=ret,
        error=err,
        new_index=landed,
        new_is_selected=bool(new and _same(song.view.selected_track, new[0])),
    )

    # delete_scene / duplicate_scene.
    sc = scratch.scene()
    sc_i = _find(song.scenes, sc)
    before = list(song.scenes)
    ret, err = _call(song.duplicate_scene, sc_i)
    new = _adopt_new(scratch, "scene", before, song.scenes)
    record(
        "duplicate_scene",
        err is None and len(new) == 1 and _find(song.scenes, new[0]) == sc_i + 1,
        source_index=sc_i,
        return_value=ret,
        error=err,
        new_index=_find(song.scenes, new[0]) if len(new) == 1 else None,
    )
    count = len(song.scenes)
    ret, err = _call(song.delete_scene, _find(song.scenes, sc))
    gone = _find(song.scenes, sc) == -1
    _forget(scratch, sc)
    record(
        "delete_scene",
        err is None and gone and len(song.scenes) == count - 1,
        return_value=ret,
        error=err,
        removed=gone,
    )

    # Clip slots on the scratch track made first (slot 0 and 1 belong to existing scenes).
    track = scratch.midi_track()  # probe_track may be stale after the undo test above
    slots = track.clip_slots
    if len(slots) >= 2:
        slot0, slot1 = slots[0], slots[1]
        clip_ok = _call(slot0.create_clip, 4.0)[1] is None and slot0.has_clip
        scenes_before = list(song.scenes)
        idx_ret, err = _call(track.duplicate_clip_slot, 0)
        _adopt_new(scratch, "scene", scenes_before, song.scenes)
        record(
            "duplicate_clip_slot",
            clip_ok
            and err is None
            and isinstance(idx_ret, int)
            and track.clip_slots[idx_ret].has_clip,
            return_value=idx_ret,
            error=err,
            expected_next_free_slot=1,
            scene_created=len(song.scenes) != len(scenes_before),
        )
        ret, err = _call(
            slot0.duplicate_clip_to, track.clip_slots[2] if len(track.clip_slots) > 2 else slot1
        )
        target = track.clip_slots[2] if len(track.clip_slots) > 2 else slot1
        record("duplicate_clip_to", err is None and target.has_clip, return_value=ret, error=err)
        ret, err = _call(slot0.delete_clip)
        record("delete_clip", err is None and not slot0.has_clip, return_value=ret, error=err)
        _, empty_err = _call(slot0.delete_clip)
        obs["delete_clip"]["error_on_empty_slot"] = empty_err
    else:
        not_observed += ["duplicate_clip_slot", "duplicate_clip_to", "delete_clip"]

    # delete_return_track on a return the probe made (sends on every track change and revert).
    ret_before = list(song.return_tracks)
    created_return = None
    try:
        _, err = _call(song.create_return_track)
        new = [r for r in song.return_tracks if not any(_same(r, b) for b in ret_before)]
        if err is None and len(new) == 1:
            created_return = new[0]
            ri = _find(song.return_tracks, created_return)
            ret, derr = _call(song.delete_return_track, ri)
            created_return = None if _find(song.return_tracks, new[0]) == -1 else new[0]
            record(
                "delete_return_track",
                derr is None
                and created_return is None
                and len(song.return_tracks) == len(ret_before),
                index=ri,
                return_value=ret,
                error=derr,
            )
        else:
            not_observed.append("delete_return_track")
            obs["delete_return_track"] = {"create_error": err, "ok": False}
    finally:
        if created_return is not None:
            _call(song.delete_return_track, _find(song.return_tracks, created_return))

    # Track.delete_device and Chain.delete_device on a duplicate of an existing track with devices.
    tracks = list(song.tracks)
    src_dev = next(
        (i for i, t in enumerate(tracks) if len(list(t.devices)) > 0 and not _same(t, probe_track)),
        None,
    )
    if src_dev is None:
        not_observed += ["Track.delete_device", "Chain.delete_device"]
    else:
        before = list(song.tracks)
        song.duplicate_track(src_dev)
        copies = _adopt_new(scratch, "track", before, song.tracks)
        dup = copies[0] if len(copies) == 1 else None
        if dup is None:
            not_observed += ["Track.delete_device", "Chain.delete_device"]
        else:
            rack = next((d for d in dup.devices if getattr(d, "can_have_chains", False)), None)
            chain = next(
                (c for c in (rack.chains if rack else []) if len(list(c.devices)) > 0), None
            )
            if chain is not None:
                n = len(list(chain.devices))
                ret, err = _call(chain.delete_device, 0)
                record(
                    "Chain.delete_device",
                    err is None and len(list(chain.devices)) == n - 1,
                    return_value=ret,
                    error=err,
                )
            else:
                not_observed.append("Chain.delete_device")
            n = len(list(dup.devices))
            ret, err = _call(dup.delete_device, 0)
            record(
                "Track.delete_device",
                err is None and len(list(dup.devices)) == n - 1,
                return_value=ret,
                error=err,
            )

    return {
        "verdict": verdict_for([], not_observed, failed),
        "observations": obs,
        "not_observed": not_observed,
        "failed": failed,
        "needs_fixture": bool(not_observed),
    }
