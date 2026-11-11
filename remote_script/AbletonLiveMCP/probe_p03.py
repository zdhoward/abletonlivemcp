"""P-03: begin_undo_step/end_undo_step and Song.undo: is a 3-write batch one undo entry.

Behavioural probe (write): every object it changes is a scratch track it created through
``scratch``. Four scratch tracks are made first (three targets and a marker). Then:

- marker: one rename made *before* any undo step, standing in for a user's own edit. If one
  ``Song.undo`` also reverts it, the batch merged into the previous step.
- phase A: inside one begin/end undo step (``end`` in a ``finally``) rename the three targets;
  call ``Song.undo`` once; read which renames survive.
- phase B: inside one begin/end undo step create three more scratch tracks; call ``Song.undo``
  once; count how many of the three still exist.

Verdict: ``go`` when one undo reverts exactly the three phase-A renames, keeps the marker, and
removes exactly the three phase-B tracks; ``go-with-limits`` when phase A is exact but phase B
is not (renames group, creations do not); otherwise ``no-go``.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-03"
KIND = WRITE

TARGETS = 3
MARKER_NAME = "p03-marker"


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def _name(track):
    try:
        return track.name
    except Exception as exc:  # noqa: BLE001 - a reverted/stale object is evidence, not a crash
        return f"<unreadable: {_err(exc)}>"


def _present(song, track):
    return any(_same(t, track) for t in song.tracks)


def verdict_for(a_reverted, a_untouched_ok, marker_kept, b_removed, b_total):
    """Pure verdict rule (kept separate so it is unit-testable)."""
    a_exact = a_reverted == TARGETS and a_untouched_ok and marker_kept
    b_exact = b_total == TARGETS and b_removed == b_total
    if a_exact and b_exact:
        return "go"
    if a_exact:
        return "go-with-limits"
    return "no-go"


def _step(song, work):
    """Run ``work`` inside one undo step; returns (begin_error, end_error, work_error)."""
    begin_err = end_err = work_err = None
    try:
        song.begin_undo_step()
    except Exception as exc:  # noqa: BLE001
        return _err(exc), None, None
    try:
        work()
    except Exception as exc:  # noqa: BLE001
        work_err = _err(exc)
    finally:
        try:
            song.end_undo_step()
        except Exception as exc:  # noqa: BLE001
            end_err = _err(exc)
    return begin_err, end_err, work_err


def _undo(song):
    info = {}
    try:
        info["can_undo_before"] = bool(song.can_undo)
    except Exception as exc:  # noqa: BLE001
        info["can_undo_before"] = f"<{_err(exc)}>"
    try:
        song.undo()
        info["undo_error"] = None
    except Exception as exc:  # noqa: BLE001
        info["undo_error"] = _err(exc)
    return info


def run(ctx, scratch):
    song = ctx.song
    targets = [scratch.midi_track() for _ in range(TARGETS)]
    marker = scratch.midi_track()
    original = [_name(t) for t in targets]
    new_names = [f"p03-batch-{i}" for i in range(TARGETS)]

    marker.name = MARKER_NAME  # a write outside any undo step, before the batch

    def rename():
        for track, name in zip(targets, new_names, strict=True):
            track.name = name

    a_begin, a_end, a_work = _step(song, rename)
    renamed_before_undo = [_name(t) for t in targets]
    a_undo = _undo(song)
    after = [_name(t) for t in targets]
    a_reverted = sum(1 for got, orig in zip(after, original, strict=True) if got == orig)
    a_still_changed = [n for n, got in zip(new_names, after, strict=True) if got == n]
    marker_after = _name(marker)
    marker_kept = marker_after == MARKER_NAME
    # Nothing but the three targets may differ from the original names (the marker is checked
    # separately); a target left as neither the original nor the batch name is also a failure.
    a_untouched_ok = all(
        got in (orig, nn) for got, orig, nn in zip(after, original, new_names, strict=True)
    )

    created = []

    def create():
        for _ in range(TARGETS):
            created.append(scratch.midi_track())

    count_before = len(list(song.tracks))
    b_begin, b_end, b_work = _step(song, create)
    count_mid = len(list(song.tracks))
    b_undo = _undo(song)
    count_after = len(list(song.tracks))
    b_removed = sum(1 for t in created if not _present(song, t))

    verdict = verdict_for(a_reverted, a_untouched_ok, marker_kept, b_removed, len(created))
    if any((a_begin, a_work, b_begin, b_work, a_undo["undo_error"], b_undo["undo_error"])):
        verdict = "no-go"
    return {
        "verdict": verdict,
        "phase_a_rename": {
            "begin_error": a_begin,
            "end_error": a_end,
            "work_error": a_work,
            "names_original": original,
            "names_after_batch": renamed_before_undo,
            "names_after_one_undo": after,
            "reverted": a_reverted,
            "still_changed": a_still_changed,
            "undo": a_undo,
        },
        "marker": {
            "name_before_undo": MARKER_NAME,
            "name_after_undo": marker_after,
            "kept": marker_kept,
            "merged_into_batch": not marker_kept,
        },
        "phase_b_create": {
            "begin_error": b_begin,
            "end_error": b_end,
            "work_error": b_work,
            "track_count": {
                "before": count_before,
                "after_batch": count_mid,
                "after_one_undo": count_after,
            },
            "created": len(created),
            "removed_by_one_undo": b_removed,
            "undo": b_undo,
        },
    }
