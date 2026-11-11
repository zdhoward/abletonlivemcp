"""[WRITING] Reference-based clip/scene/note test against a running Live (needs --allow-writes).

Creates ONE new MIDI track and ONE new scene and touches only those: names, one clip, notes,
and (only with --include-playback) launching/stopping that clip. It never deletes or saves and
never touches a pre-existing track, scene or clip; the created objects are printed and left in
the Set (disposable Set only). Occupied-slot and bad-note batches must be rejected and leave the
clip unchanged. The real bridge is read-only unless bridge.json has "read_only": false; a
read_only refusal ends the run with exit code 2.

Exit codes: 0 every required check passed; 1 a required check failed; 2 did not run (writes not
allowed, bridge unreachable/read-only, bad arguments). Lines marked 'info' never change the code.
"""

import argparse
import sys
import time

from abletonlivemcp.bridge import DEFAULT_PORT, BridgeClient, BridgeError

NOTES = [
    {"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100},
    {"pitch": 64, "start_time": 1.0, "duration": 1.0, "velocity": 90},
    {"pitch": 67, "start_time": 2.0, "duration": 2.0, "velocity": 80, "mute": False},
]


class Abort(Exception):
    """Cannot run (unreachable, read-only, bad input): exit code 2."""


class Stop(Exception):
    """A required step failed and later steps would be unsafe: finish with exit code 1."""


class Refused(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code


class Checks:
    def __init__(self):
        self.failures = []

    def require(self, ok, label, detail="", fatal=False):
        text = f"{label}: {detail}" if detail else label
        print(f"{'PASS' if ok else 'FAIL'} {text}")
        if not ok:
            self.failures.append(text)
            if fatal:
                raise Stop
        return ok

    def info(self, label, detail=""):
        print(f"info {label}" + (f": {detail}" if detail else ""))


class Live:
    def __init__(self, port, timeout):
        self.client = BridgeClient(port=port, timeout=timeout)

    def call(self, method, params=None):
        """Result of one bridge call; a refusal reply raises Refused (read_only raises Abort)."""
        result = self.client.call(method, params)
        if isinstance(result, dict) and result.get("refused") is True:
            if result.get("code") == "read_only":
                raise Abort(
                    "bridge is read-only; set read_only to false in bridge.json and restart "
                    "Live (nothing was changed)"
                )
            raise Refused(str(result.get("code")), str(result.get("message")))
        return result

    def rejected(self, method, params, code=None):
        """(ok, detail): the bridge refused the call (with `code`, if given) or the handler
        rejected it (only accepted when no code is required)."""
        try:
            self.call(method, params)
        except Refused as exc:
            return code is None or exc.code == code, f"refused {exc.code}"
        except BridgeError as exc:
            return code is None, f"bridge error {exc.kind}"
        return False, "the call was accepted"


def finish(scenario, args):
    chk = Checks()
    try:
        scenario(Live(args.port, args.timeout), args, chk)
    except Stop:
        pass
    except Abort as exc:
        print(f"RESULT: ABORT (exit 2): {exc}")
        return 2
    except Refused as exc:
        chk.failures.append(f"unexpected refusal {exc}")
        print(f"FAIL unexpected refusal {exc}")
    except BridgeError as exc:
        if exc.kind in ("Unreachable", "ConfigError"):
            print(f"RESULT: ABORT (exit 2): bridge unusable: {exc}")
            return 2
        chk.failures.append(f"unexpected bridge error {exc}")
        print(f"FAIL unexpected bridge error {exc}")
    if chk.failures:
        print(f"RESULT: FAIL (exit 1): {chk.failures[0]}")
        return 1
    print("RESULT: PASS (exit 0): every required check passed")
    return 0


def shape(rows):
    return [(r["name"], [d["class_name"] for d in r["devices"]]) for r in rows]


def note_key(notes):
    return sorted(
        (n["pitch"], round(n["start_time"], 6), round(n["duration"], 6), n["velocity"])
        for n in notes
    )


def poll(read, done, timeout):
    """Re-read until done(value) or timeout; returns the last value."""
    end = time.monotonic() + timeout
    value = read()
    while not done(value) and time.monotonic() < end:
        time.sleep(0.25)
        value = read()
    return value


def scenario(live, a, chk):
    before = live.call("session_info")
    n, s, generation = before["track_count"], before["scene_count"], before["generation"]
    chk.info("session", f"tracks={n} scenes={s} generation={generation}")
    tracks0, scenes0 = shape(live.call("tracks")), [x["name"] for x in live.call("scenes")]

    live.call("create_track", {"kind": "midi", "index": -1, "generation": generation})
    chk.require(live.call("session_info")["track_count"] == n + 1, "track count +1", fatal=True)
    made = live.call("create_scene", {"index": -1, "generation": generation})
    chk.require(made.get("scene_count") == s + 1, "scene count +1", str(made), fatal=True)
    scene = made["index"]
    chk.require(scene == s, "new scene is the last row", f"index={scene}", fatal=True)
    row = live.call("tracks")[n]
    chk.require(
        row["has_midi_input"] and not row["devices"], "new track is an empty MIDI track", fatal=True
    )
    stamp = time.strftime("%H%M%S")
    track_name, scene_name = f"{a.track_name_prefix} {stamp}", f"{a.scene_name_prefix} {stamp}"
    chk.info("created", f"MIDI track index={n}, scene index={scene} (left in the Set)")

    out = live.call("set_track_name", {"track": row["ref"], "name": track_name})
    chk.require(out.get("name") == track_name, "track rename result", repr(out.get("name")))
    chk.require(live.call("tracks")[n]["name"] == track_name, "track rename readback")
    ref = live.call("scenes")[scene]["ref"]
    out = live.call("set_scene_name", {"scene": ref, "name": scene_name})
    chk.require(out.get("name") == scene_name, "scene rename result", repr(out.get("name")))
    chk.require(live.call("scenes")[scene]["name"] == scene_name, "scene rename readback")

    slot = live.call("clip_slot", {"track": n, "scene": scene})
    chk.require(slot["has_clip"] is False, "new slot starts empty", fatal=True)
    clip = live.call("create_clip", {"slot": slot["slot"], "length_beats": a.length_beats})
    chk.require(
        clip.get("length") == a.length_beats, "clip created with requested length", str(clip)
    )
    chk.require(
        live.call("get_clip", {"track": n, "scene": scene})["length"] == a.length_beats,
        "clip length readback",
    )
    chk.require(
        note_key(live.call("get_notes", {"track": n, "scene": scene})["notes"]) == [],
        "new clip has no notes",
    )

    again = live.call("clip_slot", {"track": n, "scene": scene})
    chk.require(
        again["has_clip"] is True and "clip" in again, "slot now holds the clip", fatal=True
    )
    ok, why = live.rejected("create_clip", {"slot": again["slot"], "length_beats": a.length_beats})
    chk.require(ok, "create_clip on the occupied slot is rejected", why)
    chk.require(
        live.call("get_clip", {"track": n, "scene": scene})["length"] == a.length_beats,
        "occupied-slot rejection left the clip unchanged",
    )

    added = live.call("add_notes", {"clip": again["clip"], "notes": NOTES})
    chk.require(
        note_key(added["notes"]) == note_key(NOTES), "add_notes result has exactly the notes"
    )
    got = live.call("get_notes", {"track": n, "scene": scene})
    chk.require(
        note_key(got["notes"]) == note_key(NOTES) and not got["truncated"], "get_notes readback"
    )
    bad = NOTES[:1] + [{"pitch": 200, "start_time": 0, "duration": 1, "velocity": 90}]
    ok, why = live.rejected("add_notes", {"clip": again["clip"], "notes": bad})
    chk.require(ok, "batch with a bad pitch is rejected", why)
    after = live.call("get_notes", {"track": n, "scene": scene})
    chk.require(note_key(after["notes"]) == note_key(NOTES), "bad batch left the notes unchanged")

    if a.include_playback:
        playback(live, a, chk, n, scene)
    else:
        chk.info("playback skipped", "pass --include-playback to launch/stop the new clip")

    rows = live.call("tracks")
    chk.require(len(rows) == n + 1 and shape(rows)[:n] == tracks0, "pre-existing tracks unchanged")
    names = [x["name"] for x in live.call("scenes")]
    chk.require(names[:s] == scenes0 and len(names) == s + 1, "pre-existing scenes unchanged")
    chk.info("identity", f"MIDI track index={n} {track_name!r}; scene index={scene} {scene_name!r}")


def playback(live, a, chk, n, scene):
    was_playing = live.call("get_transport")["is_playing"]
    ref = live.call("clip_slot", {"track": n, "scene": scene})["clip"]
    live.call("fire_clip", {"clip": ref})
    read = lambda: live.call("get_clip", {"track": n, "scene": scene})  # noqa: E731
    playing = poll(read, lambda c: c["is_playing"], a.fire_timeout)["is_playing"]
    chk.require(playing, "fired clip reports is_playing", f"within {a.fire_timeout:g}s")
    live.call("stop_clip", {"clip": ref})
    stopped = not poll(read, lambda c: not c["is_playing"], a.fire_timeout)["is_playing"]
    chk.require(stopped, "stopped clip reports not playing", f"within {a.fire_timeout:g}s")
    if not was_playing and live.call("get_transport")["is_playing"]:
        generation = live.call("session_info")["generation"]
        live.call("stop", {"generation": generation})
        ok = not live.call("get_transport")["is_playing"]
        chk.require(ok, "transport restored to stopped (it was stopped before)")


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument(
        "--allow-writes", action="store_true", help="required: this script WRITES to Live"
    )
    p.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="bridge port (default %(default)s)"
    )
    p.add_argument("--timeout", type=float, default=15.0, help="seconds per bridge call")
    p.add_argument("--track-name-prefix", default="ALMCP clip", help="name prefix, new MIDI track")
    p.add_argument("--scene-name-prefix", default="ALMCP scene", help="name prefix, new scene")
    p.add_argument(
        "--length-beats", type=float, default=4.0, help="clip length (0 < beats <= 1024)"
    )
    p.add_argument(
        "--include-playback",
        action="store_true",
        help="also fire and stop the NEW clip (starts playback; stops the transport again\n"
        "if it was stopped before)",
    )
    p.add_argument(
        "--fire-timeout", type=float, default=8.0, help="seconds to wait for launch/stop"
    )
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    print(
        f"mode: WRITING - creates one MIDI track + one scene on 127.0.0.1:{a.port}; "
        "never deletes/saves"
    )
    if not a.allow_writes:
        print("RESULT: REFUSED (exit 2): this script writes to Live; pass --allow-writes to run")
        return 2
    return finish(scenario, a)


if __name__ == "__main__":
    sys.exit(main())
