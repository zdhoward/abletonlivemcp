"""P-08: ClipSlot/Track create_audio_clip(path) and Track.create_midi_clip.

Behavioural probe (write): every object it touches is a scratch track it created through
``scratch`` (one audio, one MIDI). A Core Library WAV is chosen from ``WAV_CANDIDATES`` (the
first that loads). Then:

- session: ``ClipSlot.create_audio_clip`` with forward-slash and backslash path forms; each
  result is read back (has_clip, file_path, warping, warp_mode, length) and the clip deleted;
- errors (exact texts kept): missing file, relative path, a non-audio file, an empty string, and
  an audio file on a MIDI track's slot;
- arrangement: ``Track.create_audio_clip(path, 0.0)`` and ``Track.create_midi_clip(0.0, 4.0)``.

Verdict: ``gated`` when an API member is absent on 12.2; ``no-go`` when no WAV loads or the
session clip is not created; ``go`` when session and both arrangement creations work;
otherwise ``go-with-limits``.

Helpers are inlined per probe: cross-probe imports are not allowed (tests/test_domains.py).
"""

from .dom_common import WRITE

PROBE_ID = "P-08"
KIND = WRITE

# Domain modules may not import os/glob (Live's embedded Python rule, tests/test_domains.py), so
# the WAV is a candidate list tried in order: a missing file is just a recorded create error.
CORE = "C:/ProgramData/Ableton/Live 12 Suite/Resources/Core Library"
WAV_CANDIDATES = (
    CORE + "/Samples/Loops/Drums/Full/80s Beat 90 bpm.wav",
    CORE + "/Samples/Loops/Drums/Full/80s Drum Machine Wingman 120 bpm.wav",
    CORE + "/Samples/Loops/Drums/Full/Break Ahmir's Voodoo 119 bpm.wav",
)
NON_AUDIO = "C:/Windows/System32/drivers/etc/hosts"


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


def make_audio_clip(slot):
    """Create a clip from the first candidate WAV that works: (path | None, attempts)."""
    tried = []
    for path in WAV_CANDIDATES:
        res = attempt(lambda p=path: slot.create_audio_clip(p))
        tried.append({"path": path, "ok": res["ok"], "error": res.get("error")})
        if res["ok"] and slot.has_clip:
            return path, tried
    return None, tried


def verdict_for(session_ok, arrangement_audio_ok, arrangement_midi_ok):
    """Pure verdict rule (unit-testable)."""
    if not session_ok:
        return "no-go"
    if arrangement_audio_ok and arrangement_midi_ok:
        return "go"
    return "go-with-limits"


def _norm(path):
    return str(path).replace("\\", "/").lower()


def _clip_info(clip, wav):
    info = {}
    for attr in ("name", "length", "warping", "warp_mode", "is_audio_clip", "looping"):
        res = attempt(lambda a=attr: getattr(clip, a))
        info[attr] = res.get("value", res.get("error"))
    res = attempt(lambda: clip.file_path)
    info["file_path_matches"] = res["ok"] and _norm(res["value"]) == _norm(wav)
    if not res["ok"]:
        info["file_path_error"] = res["error"]
    return info


def _session_create(slot, path, wav):
    """create_audio_clip on ``slot``; reads back and deletes any clip it made."""
    res = attempt(lambda: slot.create_audio_clip(path))
    out = {"ok": res["ok"]}
    if not res["ok"]:
        out["error"] = res["error"]
    try:
        out["has_clip_after"] = bool(slot.has_clip)
        if slot.has_clip:
            out["clip"] = _clip_info(slot.clip, wav)
            slot.delete_clip()
            out["deleted"] = not slot.has_clip
    except Exception as exc:  # noqa: BLE001
        out["readback_error"] = err(exc)
    return out


def run(ctx, scratch):
    audio = scratch.audio_track()
    midi = scratch.midi_track()
    slot = audio.clip_slots[0]
    midi_slot = midi.clip_slots[0]
    members = {
        "ClipSlot.create_audio_clip": hasattr(slot, "create_audio_clip"),
        "Track.create_audio_clip": hasattr(audio, "create_audio_clip"),
        "Track.create_midi_clip": hasattr(midi, "create_midi_clip"),
    }
    if not all(members.values()):
        return {"verdict": "gated", "members": members}
    wav, candidates = make_audio_clip(slot)
    if wav is None:
        return {
            "verdict": "no-go",
            "reason": "no candidate Core Library WAV could be created",
            "candidates": candidates,
            "members": members,
        }
    slot.delete_clip()

    forms = {
        "forward_slash": _session_create(slot, wav, wav),
        "backslash": _session_create(slot, wav.replace("/", "\\"), wav),
    }
    errors = {
        "missing_file": _session_create(slot, wav + ".missing.wav", wav),
        "relative": _session_create(slot, wav.rsplit("/", 1)[-1], wav),
        "non_audio_file": _session_create(slot, NON_AUDIO, wav),
        "empty_string": _session_create(slot, "", wav),
        "on_midi_track": _session_create(midi_slot, wav, wav),
    }

    before = len(list(audio.arrangement_clips))
    arr_audio = attempt(lambda: audio.create_audio_clip(wav, 0.0))
    after = attempt(lambda: len(list(audio.arrangement_clips)))
    arr_audio_out = {
        "ok": arr_audio["ok"],
        "error": arr_audio.get("error"),
        "arrangement_clips": {"before": before, "after": after.get("value")},
    }
    if arr_audio["ok"] and arr_audio.get("value") is not None:
        arr_audio_out["clip"] = _clip_info(arr_audio["value"], wav)

    mbefore = len(list(midi.arrangement_clips))
    arr_midi = attempt(lambda: midi.create_midi_clip(0.0, 4.0))
    mafter = attempt(lambda: len(list(midi.arrangement_clips)))
    arr_midi_out = {
        "ok": arr_midi["ok"],
        "error": arr_midi.get("error"),
        "arrangement_clips": {"before": mbefore, "after": mafter.get("value")},
    }
    if arr_midi["ok"] and arr_midi.get("value") is not None:
        arr_midi_out["length"] = attempt(lambda: arr_midi["value"].length).get("value")

    session_ok = any(f.get("ok") and f.get("has_clip_after") for f in forms.values())
    audio_ok = arr_audio["ok"] and (after.get("value") or 0) == before + 1
    midi_ok = arr_midi["ok"] and (mafter.get("value") or 0) == mbefore + 1
    return {
        "verdict": verdict_for(session_ok, audio_ok, midi_ok),
        "members": members,
        "wav": wav,
        "candidates": candidates,
        "session_forms": forms,
        "session_errors": errors,
        "arrangement_audio": arr_audio_out,
        "arrangement_midi": arr_midi_out,
    }
