"""P-19: arrangement clip feasibility (create, move, trim, split, take lanes) and 12.2 crash check.

Behavioural probe (write) on one scratch MIDI track (deleted by the runner afterwards). Live 12.2
has known crash bugs in arrangement create/duplicate, so the work is a fixed, bounded list of
operations (``MAX_OPS``), each in its own ``try`` with the exact error text recorded, ordered
from safest to riskiest: reads and creation first, marker edits, ``delete_clip``, take lanes, and
``duplicate_clip_to_arrangement`` last. The result lists every operation attempted, so if Live
dies the evidence file shows how far a re-run got (the last operation before the crash is the
suspect). No Live reply carries clip data, only counts and times.

Split: Live 12.2 has no native split member (checked by name on Clip and Track), so a split is
emulated as duplicate-then-trim; the verdict reports ``split`` as ``native``, ``emulated`` or
``unavailable``.

Verdict: ``gated`` when ``Track.create_midi_clip`` is absent; ``no-go`` when creation fails;
``go`` when create, trim, delete and duplicate all work; otherwise ``go-with-limits``.
"""

from .dom_common import WRITE

PROBE_ID = "P-19"
KIND = WRITE

MAX_OPS = 20
SPLIT_NAMES = ("split", "split_at", "split_clip")


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def _plain(value):
    return (
        value if value is None or isinstance(value, (bool, int, float, str)) else repr(value)[:80]
    )


def verdict_for(ops, create_present=True):
    """Pure verdict rule. ``ops`` maps an operation name to ``{"ok": bool}``."""
    if not create_present:
        return "gated"
    if not ops.get("create_midi_clip", {}).get("ok"):
        return "no-go"
    core = ("create_midi_clip", "trim_markers", "delete_clip", "duplicate_to_arrangement")
    return "go" if all(ops.get(n, {}).get("ok") for n in core) else "go-with-limits"


def _arr(parent):
    return sorted(parent.arrangement_clips, key=lambda c: c.start_time)


class _Runner:
    def __init__(self):
        self.ops, self.order = {}, []

    def __call__(self, name, fn):
        if len(self.order) >= MAX_OPS:
            raise RuntimeError("operation budget exceeded")
        self.order.append(name)
        rec = {"ok": False}
        try:
            detail = fn()
            rec["ok"] = True
            if detail is not None:
                rec["detail"] = detail
        except Exception as exc:  # noqa: BLE001 - the exact text is the evidence
            rec["error"] = _err(exc)
        self.ops[name] = rec
        return rec


def _split_support(track, clip):
    return {
        # class-level lookups: no property is read, so a stale Live object cannot raise here
        "Clip": [n for n in SPLIT_NAMES if hasattr(type(clip), n)] if clip is not None else None,
        "Track": [n for n in SPLIT_NAMES if hasattr(type(track), n)],
    }


def run(ctx, scratch):
    track = scratch.midi_track()
    do = _Runner()
    state = {}
    create_present = hasattr(track, "create_midi_clip")

    def create():
        track.create_midi_clip(0.0, 4.0)
        clips = _arr(track)
        if len(clips) != 1:
            raise RuntimeError(f"expected 1 arrangement clip, found {len(clips)}")
        state["clip"] = clips[0]
        return {"start": clips[0].start_time, "end": clips[0].end_time}

    def create_second():
        track.create_midi_clip(8.0, 2.0)
        return {"count": len(_arr(track))}

    def read_fields():
        clip = state["clip"]
        return {
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "length": clip.length,
            "loop_start": _plain(getattr(clip, "loop_start", None)),
            "loop_end": _plain(getattr(clip, "loop_end", None)),
            "start_marker": _plain(getattr(clip, "start_marker", None)),
            "end_marker": _plain(getattr(clip, "end_marker", None)),
        }

    def trim():
        clip = state["clip"]
        before = clip.end_time
        clip.end_marker = 3.0
        return {"end_time_before": before, "end_time_after": clip.end_time, "end_marker": 3.0}

    def delete_second():
        before = len(_arr(track))
        victim = _arr(track)[-1]
        track.delete_clip(victim)
        return {"before": before, "after": len(_arr(track))}

    def take_lane():
        before = len(list(track.take_lanes))
        track.create_take_lane()
        lanes = list(track.take_lanes)
        state["lane"] = lanes[-1]
        return {"before": before, "after": len(lanes)}

    def lane_clip():
        lane = state["lane"]
        lane.create_midi_clip(0.0, 2.0)
        return {"lane_clips": len(list(lane.arrangement_clips))}

    def dup():
        before = len(_arr(track))
        track.duplicate_clip_to_arrangement(state["clip"], 16.0)
        return {"before": before, "after": len(_arr(track))}

    def split_emulated():
        clips = _arr(track)
        copy = next((c for c in clips if abs(c.start_time - 16.0) < 1e-6), None)
        if copy is None:
            raise RuntimeError("no duplicate at 16.0 to trim")
        copy.end_marker = 1.0
        return {"copy_end_time": copy.end_time}

    if create_present:
        do("create_midi_clip", create)
    if do.ops.get("create_midi_clip", {}).get("ok"):
        do("create_second_clip", create_second)
        do("read_fields", read_fields)
        do("trim_markers", trim)
        do("delete_clip", delete_second)
        do("create_take_lane", take_lane)
        if do.ops["create_take_lane"]["ok"]:
            do("take_lane_create_midi_clip", lane_clip)
        do("duplicate_to_arrangement", dup)  # riskiest on 12.2: last
        if do.ops["duplicate_to_arrangement"]["ok"]:
            do("split_emulated_trim_copy", split_emulated)

    clip = state.get("clip")
    native = _split_support(track, clip)
    if native["Clip"] or native["Track"]:
        split = "native"
    elif do.ops.get("duplicate_to_arrangement", {}).get("ok") and do.ops.get(
        "split_emulated_trim_copy", {}
    ).get("ok"):
        split = "emulated"
    else:
        split = "unavailable"
    return {
        "verdict": verdict_for(do.ops, create_present),
        "operations_attempted": list(do.order),
        "operations": do.ops,
        "split": split,
        "split_members": native,
    }
