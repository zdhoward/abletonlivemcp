"""Editing domain: one audio (or MIDI, for crop/duplicate_loop) clip edit per call (P-09 shapes).

Live 12.2 (P-09): ``add_warp_marker`` takes only a WarpMarker struct built as
``type(existing_marker)(beat_time=..., sample_time=...)`` (dict and float are rejected), so an
add with no existing marker refuses. ``move_warp_marker(beat_time, distance)`` and
``remove_warp_marker(beat_time)`` take beat-time floats. Field writes (gain, pitch, warping,
warp_mode, loop/markers widen-then-narrow) share the clip validation of ``dom_clips``.
"""

from .core import log_failure, public_error
from .dom_clips import apply_fields, clip_row, is_audio, validate_fields, warp_rows
from .dom_common import (
    READ,
    SUPPORTED,
    WRITE,
    _number,
    clip_address_nodes,
    require,
    run_writes,
)

ANY_KIND = "any"  # safety.ANY_KIND; importing it here is circular (safety imports dom_*)

CAPABILITIES = {
    "clip.warp_markers": (SUPPORTED, "P-09: struct add, beat-time move/remove"),
    "clip.crop": (SUPPORTED, "P-09: Clip.crop, Clip.duplicate_loop"),
}

MARKER_OPS = 32
EPS = 1e-6


def get_audio_clip(ctx, p):
    addr = {k: p.get(k) for k in ("track", "scene", "arrangement", "take_lane") if k in p}
    clip = clip_address_nodes(ctx.song, addr)[-1][1]
    return clip_row(clip, detail=True)


def _find(beats, beat):
    for k, b in enumerate(beats):
        if abs(b - beat) <= EPS:
            return k
    return None


def plan_markers(clip, ops, where="warp_markers"):
    """Checked marker ops ``[(label, fn)]``; nothing is written."""
    if not isinstance(ops, list) or len(ops) > MARKER_OPS:
        raise ValueError(f"{where!r} must be a list of at most {MARKER_OPS} operations")
    if not is_audio(clip):
        raise ValueError(f"{where}: warp markers need an audio clip")
    planned = []
    existing = list(clip.warp_markers)
    beats = [m.beat_time for m in existing]  # marker positions as the ops will leave them
    for i, op in enumerate(ops):
        w = f"{where}[{i}]"
        if not isinstance(op, dict):
            raise ValueError(f"{w} must be an object")
        action = op.get("action")
        beat = float(_number(op.get("beat_time"), f"{w}.beat_time", -16384, 16384))
        if action == "add":
            if not existing:
                raise ValueError(f"{w}: the clip has no warp marker to build a new one from")
            if op.get("sample_time") is None:
                raise ValueError(f"{w}: 'sample_time' (seconds) is required")
            sample = float(_number(op.get("sample_time"), f"{w}.sample_time", 0, 86400))
            if _find(beats, beat) is not None:
                raise ValueError(f"{w}: a warp marker already sits at beat {beat}")
            beats.append(beat)
            cls = type(existing[0])
            planned.append(
                (f"add@{beat}", lambda c=cls, b=beat, s=sample: clip.add_warp_marker(
                    c(beat_time=b, sample_time=s)))
            )  # fmt: skip
        elif action == "move":
            k = _find(beats, beat)
            if k is None:
                raise ValueError(f"{w}: no warp marker at beat {beat}")
            dist = float(_number(op.get("distance"), f"{w}.distance", -16384, 16384))
            beats[k] = beat + dist
            planned.append((f"move@{beat}", lambda b=beat, d=dist: clip.move_warp_marker(b, d)))
        elif action == "remove":
            k = _find(beats, beat)
            if k is None:
                raise ValueError(f"{w}: no warp marker at beat {beat}")
            beats.pop(k)
            planned.append((f"remove@{beat}", lambda b=beat: clip.remove_warp_marker(b)))
        else:
            raise ValueError(f"{w}.action must be add, move or remove")
    return planned


def edit_audio_clip(ctx, p, t):
    """Fields, then warp-marker ops in order, then ``crop``, then ``duplicate_loop``."""
    resolved = t["targets"]
    if len(resolved) != 1 or resolved[0].path[-1][0] not in ("clip", "arr_clip"):
        raise ValueError("'targets' must name exactly one clip")
    clip = resolved[0].obj
    ops = []
    writes = validate_fields(clip, p, "edit")
    if writes:
        ops.append(("fields", lambda: apply_fields(clip, writes)))
    if p.get("warp_markers"):
        require(ctx, "clip.warp_markers", ((clip, "add_warp_marker"),))
        ops += plan_markers(clip, p.get("warp_markers"))
    for flag in ("crop", "duplicate_loop"):
        value = p.get(flag)
        if value is None or value is False:
            continue
        if value is not True:
            raise ValueError(f"{flag!r} must be a bool")
        require(ctx, "clip.crop", ((clip, flag),))
        ops.append((flag, getattr(clip, flag)))
    if not ops:
        raise ValueError("nothing to edit")
    receipt = run_writes(ops, lambda op: {"op": op[0], "returned": _plain(op[1]())})
    try:
        receipt["clip"] = clip_row(clip, detail=True)
        if is_audio(clip):
            receipt["clip"]["warp_markers"] = warp_rows(clip)
    except Exception as exc:  # noqa: BLE001 - the receipt stands without the readback
        receipt["clip"] = {"error": public_error(exc, "readback_failed")}
        log_failure("edit readback", exc)
    return receipt


def _plain(value):
    return value if isinstance(value, (int, float, str, bool)) or value is None else None


METHODS = {
    "get_audio_clip": (get_audio_clip, READ, None),
    "edit_audio_clip": (edit_audio_clip, WRITE, (("targets", "ref", ANY_KIND),)),
}
