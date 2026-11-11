"""P-18: session_record, record_mode, arrangement_overdub, capture_midi and friends.

Behavioural probe (write). It must never start a real recording and must leave the three modes as
it found them. Each mode is read, set to the opposite value, read back and restored in a
``finally`` (restoration is itself read back). ``session_record`` is only toggled when the
transport is stopped and no track is armed, so no clip can start recording; otherwise it is
skipped with the reason recorded. ``trigger_session_record``, ``capture_midi`` and
``capture_and_insert_scene`` change the Set when they succeed, so they are checked for presence
only, except that ``capture_and_insert_scene`` is called when ``can_capture_midi`` is False (there
is nothing to capture) to record the exact refusal text.

Verdict: ``gated`` when none of the Song members exist; ``go`` when every mode tried reads
back and restores and ``record_mode`` and ``arrangement_overdub`` were both tried;
``go-with-limits`` when the safe subset works but a mode was skipped; else ``no-go``.
"""

from .dom_common import WRITE

PROBE_ID = "P-18"
KIND = WRITE

MODES = ("record_mode", "arrangement_overdub", "session_record")
ACTIONS = ("trigger_session_record", "capture_midi", "can_capture_midi", "capture_and_insert_scene")


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def _plain(value):
    return (
        value if value is None or isinstance(value, (bool, int, float, str)) else repr(value)[:80]
    )


def verdict_for(modes, present):
    """Pure verdict rule. ``modes`` maps name -> {"tried": bool, "ok": bool}."""
    if not present:
        return "gated"
    tried = [m for m in modes.values() if m.get("tried")]
    if any(not m["ok"] for m in tried):
        return "no-go"
    core = all(modes.get(n, {}).get("tried") for n in ("record_mode", "arrangement_overdub"))
    if not core:
        return "no-go"
    return "go" if len(tried) == len(MODES) else "go-with-limits"


def _skip_reason(song):
    """Why session_record must not be toggled, or None."""
    try:
        if song.is_playing:
            return "transport is playing"
        armed = [t for t in song.tracks if getattr(t, "can_be_armed", False) and t.arm]
        if armed:
            return f"{len(armed)} armed track(s): setting session_record could start recording"
    except Exception as exc:  # noqa: BLE001
        return f"could not check the transport/arm state: {_err(exc)}"
    return None


def _mode(song, name):
    rec = {"mode": name, "tried": False, "ok": False}
    try:
        old = getattr(song, name)
    except Exception as exc:  # noqa: BLE001
        rec["reason"] = f"read failed: {_err(exc)}"
        return rec
    rec["before"] = _plain(old)
    if name == "session_record":
        reason = _skip_reason(song)
        if reason:
            rec["skipped"] = reason
            return rec
    rec["tried"] = True
    new = not old
    try:
        setattr(song, name, new)
        rec["after_set"] = _plain(getattr(song, name))
        rec["set_error"] = None
    except Exception as exc:  # noqa: BLE001
        rec["set_error"] = _err(exc)
    finally:
        try:
            setattr(song, name, old)
            rec["restored"] = _plain(getattr(song, name))
        except Exception as exc:  # noqa: BLE001
            rec["restore_error"] = _err(exc)
    rec["ok"] = (
        rec.get("set_error") is None
        and rec.get("after_set") == new
        and rec.get("restored") == old
        and "restore_error" not in rec
    )
    return rec


def _actions(song):
    out = {name: {"present": hasattr(song, name)} for name in ACTIONS}
    try:
        can = song.can_capture_midi
        out["can_capture_midi"]["value"] = _plain(can)
    except Exception as exc:  # noqa: BLE001
        can = None
        out["can_capture_midi"]["error"] = _err(exc)
    if can is False and out["capture_and_insert_scene"]["present"]:
        before = len(list(song.scenes))
        try:
            song.capture_and_insert_scene()
            out["capture_and_insert_scene"]["refused"] = False
        except Exception as exc:  # noqa: BLE001
            out["capture_and_insert_scene"]["refused"] = True
            out["capture_and_insert_scene"]["error"] = _err(exc)
        out["capture_and_insert_scene"]["scenes_added"] = len(list(song.scenes)) - before
    else:
        out["capture_and_insert_scene"]["called"] = False
    out["trigger_session_record"]["called"] = False
    out["capture_midi"]["called"] = False
    return out


def run(ctx, scratch):
    song = ctx.song
    present = [n for n in MODES if hasattr(song, n)]
    modes = {}
    for name in MODES:
        modes[name] = _mode(song, name) if name in present else {"mode": name, "tried": False}
        modes[name].setdefault("ok", False)
    actions = _actions(song)
    return {
        "verdict": verdict_for(modes, present),
        "modes": modes,
        "actions": actions,
        "unverified": "recording itself is never started; trigger_session_record/capture_midi "
        "outcomes are not exercised",
    }
