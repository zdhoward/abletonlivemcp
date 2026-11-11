"""P-09: Clip setters, warp markers, crop and duplicate_loop.

Behavioural probe (write): a scratch MIDI track (4-beat session clip) and a scratch audio track
(a Core Library WAV clip) are the only objects touched. Each setter is written and read back
(``rw``); a failed write keeps its exact error text. Write-order constraints are tested by
writing in the "wrong" order (loop_end below loop_start, start_marker past end_marker, ...) and
recording the outcomes. Warp markers (audio clip): shape of ``warp_markers`` entries, then
add/move/remove with readback. ``crop`` and ``duplicate_loop`` run on the MIDI clip.

Verdict: ``gated`` when a member is absent on 12.2; ``no-go`` when no clip can be created;
``go`` when every plain setter reads back and the warp marker calls work; else ``go-with-limits``
(the failures are the recorded constraint list).
"""

from .dom_common import WRITE

PROBE_ID = "P-09"
KIND = WRITE

MEMBERS = (
    "loop_start",
    "loop_end",
    "start_marker",
    "end_marker",
    "launch_mode",
    "launch_quantization",
    "legato",
    "warp_mode",
    "gain",
    "pitch_coarse",
    "pitch_fine",
    "signature_numerator",
    "signature_denominator",
    "warp_markers",
    "add_warp_marker",
    "move_warp_marker",
    "remove_warp_marker",
    "crop",
    "duplicate_loop",
)


def err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def attempt(fn):
    """Run ``fn``; the outcome is evidence either way."""
    try:
        return {"ok": True, "value": fn()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": err(exc)}


def _close(a, b, tol=1e-6):
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


def rw(obj, attr, value, tol=1e-6):
    """Write ``obj.attr = value`` and read it back: {wrote, readback, match | error}."""
    out = {"attr": attr, "wrote": value}
    try:
        setattr(obj, attr, value)
    except Exception as exc:  # noqa: BLE001
        out.update(match=False, error=err(exc))
        return out
    try:
        got = getattr(obj, attr)
    except Exception as exc:  # noqa: BLE001
        out.update(match=False, error=f"readback {err(exc)}")
        return out
    out.update(readback=got, match=_close(got, value, tol))
    return out


# Domain modules may not import os/glob (Live's embedded Python rule, tests/test_domains.py), so
# the WAV is a candidate list tried in order: a missing file is just a recorded create error.
CORE = "C:/ProgramData/Ableton/Live 12 Suite/Resources/Core Library"
WAV_CANDIDATES = (
    CORE + "/Samples/Loops/Drums/Full/80s Beat 90 bpm.wav",
    CORE + "/Samples/Loops/Drums/Full/80s Drum Machine Wingman 120 bpm.wav",
    CORE + "/Samples/Loops/Drums/Full/Break Ahmir's Voodoo 119 bpm.wav",
)


def make_audio_clip(slot):
    """Create a clip from the first candidate WAV that works: (path | None, attempts)."""
    tried = []
    for path in WAV_CANDIDATES:
        res = attempt(lambda p=path: slot.create_audio_clip(p))
        tried.append({"path": path, "ok": res["ok"], "error": res.get("error")})
        if res["ok"] and slot.has_clip:
            return path, tried
    return None, tried


def verdict_for(have_clip, setters_ok, warp_ok):
    """Pure verdict rule (unit-testable)."""
    if not have_clip:
        return "no-go"
    return "go" if setters_ok and warp_ok else "go-with-limits"


def _marker_shape(marker):
    shape = {}
    for attr in ("beat_time", "sample_time", "time", "position"):
        if hasattr(marker, attr):
            shape[attr] = attempt(lambda a=attr: getattr(marker, a)).get("value")
    shape["type"] = type(marker).__name__
    return shape


def _markers(clip):
    res = attempt(lambda: [_marker_shape(m) for m in clip.warp_markers])
    return res.get("value", res.get("error"))


def _order_tests(clip):
    """Writes in the order a naive caller would use; records which are refused."""
    out = {}
    out["loop_end_below_loop_start"] = rw(clip, "loop_end", 0.0)  # loop_start is 0.0
    out["loop_start_above_loop_end"] = rw(clip, "loop_start", float(clip.loop_end) + 1.0)
    clip.loop_start, clip.loop_end = 0.0, 4.0
    out["end_marker_below_start_marker"] = rw(clip, "end_marker", -1.0)
    out["start_marker_past_end_marker"] = rw(clip, "start_marker", float(clip.end_marker) + 1.0)
    out["loop_end_beyond_end_marker"] = rw(clip, "loop_end", float(clip.end_marker) + 4.0)
    out["loop_end_then_end_marker_order"] = {
        "end_marker_first": rw(clip, "end_marker", 8.0),
        "loop_end_after": rw(clip, "loop_end", 8.0),
    }
    return out


def _midi_clip_probe(clip):
    plain = [
        rw(clip, "loop_start", 0.0),
        rw(clip, "loop_end", 2.0),
        rw(clip, "start_marker", 0.0),
        rw(clip, "end_marker", 2.0),
        rw(clip, "legato", True),
        rw(clip, "signature_numerator", 3),
        rw(clip, "signature_denominator", 8),
    ]
    for attr in ("launch_mode", "launch_quantization"):
        cur = attempt(lambda a=attr: getattr(clip, a))
        plain.append(rw(clip, attr, cur["value"]) if cur["ok"] else {"attr": attr, **cur})
    # a value different from the current one proves the write, not just a no-op
    plain.append(rw(clip, "launch_mode", 1))
    plain.append(rw(clip, "launch_quantization", 4))
    order = attempt(lambda: _order_tests(clip))
    clip.loop_start, clip.loop_end, clip.start_marker, clip.end_marker = 0.0, 4.0, 0.0, 4.0
    crop = attempt(clip.crop)
    dup = attempt(lambda: (clip.duplicate_loop(), float(clip.length))[1])
    return {
        "setters": plain,
        "order_constraints": order.get("value", order.get("error")),
        "crop": {"ok": crop["ok"], "error": crop.get("error")},
        "duplicate_loop": {
            "ok": dup["ok"],
            "length_after": dup.get("value"),
            "error": dup.get("error"),
        },
    }


def _audio_clip_probe(clip):
    plain = [
        rw(clip, "gain", 0.5, 0.05),
        rw(clip, "pitch_coarse", 2),
        rw(clip, "pitch_fine", 10.0, 0.5),
    ]
    warp_modes = attempt(lambda: list(clip.available_warp_modes))
    mode_tests = []
    for mode in (warp_modes.get("value") or [])[:3]:
        mode_tests.append(rw(clip, "warp_mode", mode))
    warping = rw(clip, "warping", True)
    before = _markers(clip)
    count_before = len(before) if isinstance(before, list) else None
    length = attempt(lambda: float(clip.length)).get("value") or 4.0
    # Live wants a WarpMarker struct: a float is refused (probe run 1), so try a dict form.
    beat, ratio = length / 2.0, 2.0 / 3.0  # sample_time/beat_time ratio seen on the 2nd marker
    forms = {
        "dict": {"beat_time": beat, "sample_time": beat * ratio},
        "beat_only_dict": {"beat_time": beat},
        "float": beat,
    }
    marker_cls = type(clip.warp_markers[0]) if len(clip.warp_markers) else None
    if marker_cls is not None:
        forms["struct_kwargs"] = attempt(
            lambda: marker_cls(beat_time=beat, sample_time=beat * ratio)
        ).get("value")
        forms["struct_positional"] = attempt(lambda: marker_cls(beat, beat * ratio)).get("value")
        forms["struct_default_then_set"] = attempt(
            lambda: setattr(m := marker_cls(), "beat_time", beat) or m
        ).get("value")
    forms = {k: v for k, v in forms.items() if v is not None}
    add_attempts = {}
    added = {"ok": False}
    for name, arg in forms.items():
        add_attempts[name] = attempt(lambda a=arg: clip.add_warp_marker(a))
        if add_attempts[name]["ok"]:
            added = add_attempts[name]
            break
    after_add = _markers(clip)
    added = dict(added, attempts=add_attempts)
    move_forms = {"beat_time float": (beat, 0.25), "marker dict": (forms["dict"], 0.25)}
    move_attempts = {}
    moved = {"ok": False}
    for name, args in move_forms.items():
        move_attempts[name] = attempt(lambda a=args: clip.move_warp_marker(*a))
        if move_attempts[name]["ok"]:
            moved = move_attempts[name]
            break
    moved = dict(moved, attempts=move_attempts)
    after_move = _markers(clip)
    rem_attempts = {}
    removed = {"ok": False}
    for name, arg in (("float", beat + 0.25), ("float unmoved", beat), ("dict", forms["dict"])):
        rem_attempts[name] = attempt(lambda a=arg: clip.remove_warp_marker(a))
        if rem_attempts[name]["ok"]:
            removed = rem_attempts[name]
            break
    removed = dict(removed, attempts=rem_attempts)
    after_remove = _markers(clip)
    return {
        "setters": plain,
        "available_warp_modes": warp_modes.get("value", warp_modes.get("error")),
        "warp_mode_writes": mode_tests,
        "warping": warping,
        "warp_markers": {
            "before": before,
            "add": {"ok": added["ok"], "attempts": add_attempts},
            "after_add": after_add,
            "move": {"ok": moved["ok"], "attempts": move_attempts},
            "after_move": after_move,
            "remove": {"ok": removed["ok"], "attempts": rem_attempts},
            "after_remove": after_remove,
            "count_before": count_before,
        },
    }


def _all_match(items):
    return all(i.get("match") for i in items)


def run(ctx, scratch):
    midi = scratch.midi_track()
    audio = scratch.audio_track()
    probe_clip = midi.clip_slots[0]
    try:
        probe_clip.create_clip(4.0)
        clip = probe_clip.clip
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "no-go", "reason": f"MIDI clip not created: {err(exc)}"}
    # class-level check: hasattr on an instance evaluates the property (warp_* raise on MIDI clips)
    members = {n: hasattr(type(clip), n) for n in MEMBERS}
    missing = sorted(n for n, ok in members.items() if not ok)
    if missing:
        return {"verdict": "gated", "missing_members": missing}

    midi_part = _midi_clip_probe(clip)
    wav, candidates = make_audio_clip(audio.clip_slots[0])
    if wav is None:
        audio_part = {"skipped": "no candidate WAV could be created", "candidates": candidates}
    else:
        audio_part = attempt(lambda: _audio_clip_probe(audio.clip_slots[0].clip))
        audio_part = audio_part.get("value", {"error": audio_part.get("error")})

    setters = midi_part["setters"] + audio_part.get("setters", [])
    wm = audio_part.get("warp_markers", {})
    warp_ok = bool(wm) and wm["add"]["ok"] and wm["move"]["ok"] and wm["remove"]["ok"]
    return {
        "verdict": verdict_for(True, _all_match(setters) and "setters" in audio_part, warp_ok),
        "midi_clip": midi_part,
        "audio_clip": audio_part,
        "constraints_note": "failed rw entries (match false, error text) are the constraint list",
    }
