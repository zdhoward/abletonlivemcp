"""P-16: cue points: race-free add at a time, rename, delete, jump.

Behavioural probe (write), stateful across re-runs. ``CuePoint.time`` is read-only (the 12.2 API
docs say Get/Listen) and ``Song.set_or_delete_cue`` acts at the playhead, whose
``current_song_time`` setter applies late in Live. So the probe compares:

- E1 (immediate): set the time and call ``set_or_delete_cue`` in the same call; read the cue time.
- E3 (two-stage): set the time in one run and call ``set_or_delete_cue`` in a *later* run (a later
  tick). This is the candidate race-free add.
- rename: ``CuePoint.name`` write and readback.
- delete: set the time to an owned cue's time, then (a later run) confirm the playhead is on it
  (``is_cue_point_selected``) and toggle.

Only cues the probe created are ever written or deleted; it refuses if the playhead starts on a
cue or the Song is playing. State lives in ``_STATE`` (the Remote Script process), so a re-run
continues the stages and reaps the cues; ``complete: false`` in the result means "re-run". The
original playhead is restored at the end. Scratch is unused (a cue is not a scratch track).

Verdict (final stage only): ``gated`` when the cue API is absent; ``go`` when the two-stage add
lands on the target, rename reads back and a delete is confirmed; otherwise ``no-go``.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-16"
KIND = WRITE

E1_TARGET = 8.0
E3_TARGET = 24.0
MAX_STAGES = 8
_STATE = {}


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(api_present, two_stage_exact, rename_ok, delete_ok):
    """Pure verdict rule."""
    if not api_present:
        return "gated"
    return "go" if (two_stage_exact and rename_ok and delete_ok) else "no-go"


def _api_present(song):
    return all(
        hasattr(song, n)
        for n in ("set_or_delete_cue", "cue_points", "is_cue_point_selected", "current_song_time")
    )


def _new_cues(song, before):
    return [c for c in song.cue_points if not any(_same(c, b) for b in before)]


def _still_present(song, cues):
    return [c for c in cues if any(_same(c, x) for x in song.cue_points)]


def _reap(song, st):
    """One step of deleting the cues this probe made. Returns True when none remain."""
    st["owned"] = _still_present(song, st["owned"])
    if not st["owned"]:
        return True
    cue = st["owned"][0]
    on_owned = song.is_cue_point_selected and abs(float(song.current_song_time) - cue.time) < 1e-6
    if on_owned:
        count = len(list(song.cue_points))
        song.set_or_delete_cue()
        removed = count - len(list(song.cue_points))
        st["delete_log"].append({"selected": True, "cues_removed": removed})
        st["owned"] = _still_present(song, st["owned"])
    else:
        st["delete_log"].append(
            {
                "selected": bool(song.is_cue_point_selected),
                "playhead": float(song.current_song_time),
            }
        )
        song.current_song_time = float(cue.time)
    return not st["owned"]


def _fresh(song):
    if song.is_cue_point_selected:
        return None, {"verdict": "no-go", "complete": True, "refused": "playhead is on a cue"}
    if song.is_playing:
        return None, {"verdict": "no-go", "complete": True, "refused": "Song is playing"}
    before = list(song.cue_points)
    st = {
        "stage": 1,
        "orig_time": float(song.current_song_time),
        "owned": [],
        "delete_log": [],
        "cues_before": [float(c.time) for c in before],
    }
    song.current_song_time = E1_TARGET  # E1: immediate add
    time_after_set = float(song.current_song_time)
    song.set_or_delete_cue()
    new = _new_cues(song, before)
    st["owned"].extend(new)
    st["e1"] = {
        "requested": E1_TARGET,
        "time_property_after_set": time_after_set,
        "cue_times": [float(c.time) for c in new],
        "lands_at_target": [float(c.time) for c in new] == [E1_TARGET],
    }
    rename = {"ok": False}
    st["time_writable"] = None
    if new:
        try:
            new[0].name = "p16-cue"
            rename.update(name_after=new[0].name, ok=new[0].name == "p16-cue")
        except Exception as exc:  # noqa: BLE001
            rename["error"] = _err(exc)
        try:
            new[0].time = new[0].time + 1.0  # an owned cue only
            st["time_writable"] = True
        except Exception as exc:  # noqa: BLE001 - expected: read-only
            st["time_writable"] = False
            st["time_write_error"] = _err(exc)
    st["rename"] = rename
    st["before_e3"] = list(song.cue_points)
    song.current_song_time = E3_TARGET  # E3: the toggle happens on a later run
    return st, None


def _finish(song, st):
    song.current_song_time = st["orig_time"]
    _STATE.clear()
    e3 = st.get("e3", {})
    delete_ok = any(e.get("cues_removed") == 1 for e in st["delete_log"]) and not st["owned"]
    verdict = verdict_for(True, e3.get("lands_at_target", False), st["rename"]["ok"], delete_ok)
    return {
        "verdict": verdict,
        "complete": True,
        "e1_immediate": st["e1"],
        "e3_two_stage": e3,
        "rename": st["rename"],
        "time_writable": st["time_writable"],
        "time_write_error": st.get("time_write_error"),
        "delete_log": st["delete_log"],
        "delete_ok": delete_ok,
        "cues_left_behind": len(st["owned"]),
        "cues_before": st["cues_before"],
        "finding": (
            "immediate add lands at the old playhead; set the time in one call and toggle in a "
            "later call"
            if not st["e1"]["lands_at_target"] and e3.get("lands_at_target")
            else "see e1_immediate / e3_two_stage"
        ),
    }


def _pending(st):
    return {"verdict": "no-go", "complete": False, "stage": st["stage"], "next": "re-run P-16"}


def run(ctx, scratch):
    song = ctx.song
    if not _api_present(song):
        return {"verdict": verdict_for(False, False, False, False), "complete": True}
    st = _STATE.get("st")
    if st is None:
        st, refusal = _fresh(song)
        if refusal:
            return refusal
        _STATE["st"] = st
        return _pending(st)
    st["stage"] += 1
    try:
        if "e3" not in st:
            seen = float(song.current_song_time)
            on_cue = bool(song.is_cue_point_selected)
            song.set_or_delete_cue()
            new = _new_cues(song, st["before_e3"])
            st["owned"].extend(new)
            st["e3"] = {
                "requested": E3_TARGET,
                "time_property_at_toggle": seen,
                "was_on_a_cue": on_cue,
                "cue_times": [float(c.time) for c in new],
                "lands_at_target": [float(c.time) for c in new] == [E3_TARGET],
            }
            if st["owned"]:
                song.current_song_time = float(st["owned"][0].time)
            return _pending(st)
        done = _reap(song, st)
        if done or st["stage"] >= MAX_STAGES:
            return _finish(song, st)
        return _pending(st)
    except Exception:
        _STATE.clear()
        raise
