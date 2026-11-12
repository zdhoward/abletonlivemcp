"""Recording domain (batch 2): one bridge method ``record`` behind ``live_record``.

P-18 is unrun, so every action is ``unverified`` and member-gated. Turning a record switch ON is
always bounded: it needs ``length`` (beats, at most ``MAX_SECONDS`` at the current tempo), starts
playback if needed, and a step task (``operations.start_task``) restores the previous record
switches and play state once the song time has advanced ``length`` beats (or the wall-clock bound
passes). Turning a switch OFF is a plain write.

Cleanup is verified, not assumed: each restore step is reported, then the switch and play state
are read back. A step that raised or a readback that does not show the prior state makes the
task ``unknown`` (``cleanup_failed``), never ready, and the recording exclusion stays until a
fresh readback shows the prior state (or the Set changes).

``Song.trigger_session_record`` is deliberately not exposed: a second trigger stops a running
recording, its start waits for launch quantization (so a beat count cannot bound it) and it
creates clips in whichever slot is selected. The bounded ``session_record`` switch covers the
same Session recording with a guard, an operation and a cleanup finalizer.
"""

import time

from .core import Invalid
from .dom_common import WRITE, Refused, _number, require

CAPABILITIES = {
    "record.session": ("unverified", "P-18 unrun: Song.session_record"),
    "record.arrangement": ("unverified", "P-18 unrun: Song.record_mode"),
    "record.overdub": ("unverified", "P-18 unrun: Song.arrangement_overdub"),
    "record.capture_midi": ("unverified", "P-18 unrun: Song.capture_midi/can_capture_midi"),
    "record.capture_scene": ("unverified", "P-18 unrun: Song.capture_and_insert_scene"),
}

SWITCHES = {
    "session_record": ("record.session", "session_record"),
    "arrangement_record": ("record.arrangement", "record_mode"),
    "overdub": ("record.overdub", "arrangement_overdub"),
}
MAX_SECONDS = 8.0
TASK_SLACK = 1.5


def _state(song):
    return {
        "is_playing": song.is_playing,
        "current_song_time": song.current_song_time,
        **{key: getattr(song, attr, None) for key, (_cap, attr) in SWITCHES.items()},
    }


def _attempt(name, fn):
    """One cleanup step: ``{"step", "ok"}`` plus the exception type when it failed."""
    try:
        fn()
        return {"step": name, "ok": True}
    except Exception as exc:  # noqa: BLE001 - the next step still runs
        return {"step": name, "ok": False, "error": type(exc).__name__}


def _bounded(ctx, key, attribute, length):
    """Switch ``attribute`` on for ``length`` beats, then restore; returns the task snapshot."""
    song = ctx.song
    seconds = float(length) * 60.0 / float(song.tempo)
    if seconds > MAX_SECONDS:
        raise Invalid(
            f"'length' {length} beats is {seconds:.1f} s at this tempo; at most {MAX_SECONDS} s"
        )
    # One bounded recording at a time: a second one would snapshot the first one's switches as
    # "before" and restore them to on after the first had turned them off.
    active = ctx.operations.blocking_task("record:")
    if active is not None:
        raise Refused(
            "recording_active",
            f"a bounded recording is still running or its cleanup is unconfirmed (operation "
            f"{active}); poll it, and turn the switch off / stop the transport if it stays on",
        )
    before = {"was_playing": song.is_playing, attribute: getattr(song, attribute)}
    start = song.current_song_time
    started = time.monotonic()

    def unrestored():
        """Readback: the switch and play state are not back where this call found them."""
        if getattr(song, attribute) != before[attribute]:
            return True
        return not before["was_playing"] and bool(song.is_playing)

    def restore():
        # Independent steps: a failing switch restore must never skip stopping the transport.
        steps = [(attribute, lambda: setattr(song, attribute, before[attribute]))]
        if not before["was_playing"]:
            steps.append(("stop_playing", song.stop_playing))
        cleanup = [_attempt(name, fn) for name, fn in steps]
        readback = {}
        for key, read in (
            (attribute, lambda: getattr(song, attribute)),
            ("is_playing", lambda: song.is_playing),
            ("recorded_beats", lambda: max(0.0, song.current_song_time - start)),
        ):
            try:
                readback[key] = read()
            except Exception as exc:  # noqa: BLE001 - reported, never raised from cleanup
                readback[key] = f"unreadable: {type(exc).__name__}"
        # Per step: what it should have left and what the readback shows.
        reads = {attribute: (attribute, before[attribute]), "stop_playing": ("is_playing", False)}
        for row in cleanup:
            key, expected = reads[row["step"]]
            row["observed"] = readback[key]
            row["restored"] = row["ok"] and readback[key] == expected
        restored = all(row["restored"] for row in cleanup)
        out = {
            "recorded_beats": readback.pop("recorded_beats"),
            "cleanup": cleanup,
            "restored": readback,
        }
        if not restored:
            out["status"] = "cleanup_failed"  # unknown, and the exclusion stays (hold)
        return out

    def step():
        done = song.current_song_time - start >= length
        if done or time.monotonic() - started >= seconds + 0.5:
            return restore()
        return None

    # The task exists before the first write: a full ring refuses with nothing applied, and a
    # failing write below still leaves the restore step scheduled.
    # restore is also the finalizer: a late tick (timeout), a step error or a script disconnect
    # still turns recording off and stops a transport this call started.
    task = ctx.operations.start_task(
        f"record:{key}", step, timeout=seconds + TASK_SLACK, finalize=restore, hold=unrestored
    )
    setattr(song, attribute, True)
    if not song.is_playing:
        song.start_playing()
    return {"operation": task}


def record(ctx, p, _t):
    song = ctx.song
    action = p.get("action")
    value = p.get("value")
    if action in SWITCHES:
        capability, attribute = SWITCHES[action]
        if not isinstance(value, bool):
            raise Invalid(f"'{action}' needs 'value': true or false")
        state = require(ctx, capability, ((song, attribute),))
        if value:
            length = _number(p.get("length"), "length", 0.0, exclusive=True)
            out = _bounded(ctx, action, attribute, length)
        else:
            setattr(song, attribute, False)
            out = {}
    elif action == "capture_midi":
        state = require(ctx, "record.capture_midi", ((song, "capture_midi"),))
        destination = p.get("destination", 0)
        if destination not in (0, 1, 2) or isinstance(destination, bool):
            raise Invalid("'destination' must be 0 (auto), 1 (session) or 2 (arrangement)")
        if not getattr(song, "can_capture_midi", False):
            raise Refused("nothing_to_capture", "Live has no recent MIDI input to capture")
        song.capture_midi(destination)
        out = {}
    elif action == "capture_and_insert_scene":
        state = require(ctx, "record.capture_scene", ((song, "capture_and_insert_scene"),))
        before = len(song.scenes)
        song.capture_and_insert_scene()
        out = {"scenes_added": len(song.scenes) - before}
    else:
        actions = [*SWITCHES, "capture_midi", "capture_and_insert_scene"]
        raise Invalid(f"'action' must be one of {actions}")
    return {
        "action": action,
        "unverified": [action] if state == "unverified" else [],
        **out,
        "state": _state(song),
    }


METHODS = {"record": (record, WRITE, ())}
