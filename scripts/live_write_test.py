"""[WRITING] Reference-based write test against a running Live (needs --allow-writes).

Creates ONE new audio track and touches only that track: rename, colour, optionally load one
device and write one parameter, plus refusal checks (index instead of reference, unknown
reference, stale generation, out-of-range value, occupied load). It never deletes or saves,
never changes the tempo or transport, and never touches a pre-existing track. The created track
is printed and left in the Set (disposable Set only). The real bridge is read-only unless
bridge.json has "read_only": false; a read_only refusal ends the run with exit code 2.

Exit codes: 0 every required check passed; 1 a required check failed; 2 did not run (writes not
allowed, bridge unreachable/read-only, bad arguments). Lines marked 'info' never change the code.
"""

import argparse
import json
import sys
import time

from abletonlivemcp.bridge import DEFAULT_PORT, BridgeClient, BridgeError


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


def wait_operation(live, op, timeout):
    end = time.monotonic() + timeout
    while op["state"] == "pending" and time.monotonic() < end:
        time.sleep(0.25)
        op = live.call("operation", {"operation": op["operation"]})
    return op


def scenario(live, a, chk):
    before = live.call("session_info")
    n, generation = before["track_count"], before["generation"]
    chk.info("session", f"tracks={n} generation={generation} tempo={before['tempo']} (not changed)")
    baseline = shape(live.call("tracks"))
    chk.require(len(baseline) == n, "baseline track list matches session_info", f"{len(baseline)}")

    live.call("create_track", {"kind": "audio", "index": -1, "generation": generation})
    chk.require(live.call("session_info")["track_count"] == n + 1, "track count +1", fatal=True)
    row = live.call("tracks")[n]
    chk.require(
        not row["has_midi_input"] and not row["devices"], "new track is empty audio", fatal=True
    )
    name = f"{a.track_name_prefix} {time.strftime('%H%M%S')}"
    chk.info("created", f"audio track index={n} (renaming to {name!r}; left in the Set)")

    out = live.call("set_track_name", {"track": row["ref"], "name": name})
    chk.require(out.get("name") == name, "rename result", repr(out.get("name")))
    row = live.call("tracks")[n]
    chk.require(row["name"] == name, "rename readback", repr(row["name"]))
    out = live.call("set_track_color", {"track": row["ref"], "color_index": a.color_index})
    chk.require(out.get("color_index") == a.color_index, "colour result", str(out))
    row = live.call("tracks")[n]
    chk.require(row["color_index"] == a.color_index, "colour readback", str(row["color_index"]))

    ok, why = live.rejected("set_track_name", {"track": n, "name": "ALMCP x"}, "reference_required")
    chk.require(ok, "numeric track index is refused as a write target", why)
    ok, why = live.rejected(
        "set_track_name", {"track": "0123456789abcdef", "name": "ALMCP x"}, "unknown_reference"
    )
    chk.require(ok, "unknown reference is refused", why)
    stale = {"kind": "audio", "index": -1, "generation": generation - 1}
    ok, why = live.rejected("create_track", stale, "stale_generation")
    chk.require(ok, "stale generation is refused", why)
    chk.require(
        live.call("session_info")["track_count"] == n + 1, "refusals created no track", fatal=True
    )
    chk.require(live.call("tracks")[n]["name"] == name, "refusals left the name unchanged")

    if a.device_path:
        device_steps(live, a, chk, n)
    else:
        chk.info("device steps skipped", "no --device-path given (load/parameter/occupied checks)")

    rows = live.call("tracks")
    chk.require(len(rows) == n + 1, "final track count", f"{len(rows)} (expected {n + 1})")
    chk.require(shape(rows)[:n] == baseline, "pre-existing tracks unchanged (names and devices)")
    chk.info("identity", f"created audio track index={n} name={rows[n]['name']!r}")


def device_steps(live, a, chk, n):
    row = live.call("tracks")[n]
    started = time.monotonic()
    op = live.call("load_item", {"track": row["ref"], "root": a.root, "path": a.device_path})
    chk.info("load started", f"operation={op.get('operation')} state={op.get('state')}")
    op = wait_operation(live, op, a.load_timeout)
    took = time.monotonic() - started
    chk.require(op["state"] == "ready", "load reached ready", f"{op['state']} ({op.get('reason')})")
    chk.info("load timing", f"{took:.1f}s to {op['state']}")
    devices = live.call("tracks")[n]["devices"]
    chk.require(
        [d["class_name"] for d in devices] == op["devices_after"] and len(devices) == 1,
        "track holds exactly the one loaded device",
        str(devices),
        fatal=True,
    )
    params = live.call("device_parameters", {"track": n, "device": 0})
    usable = [
        p
        for p in params
        if p["is_enabled"]
        and not p["is_quantized"]
        and p["name"] != "Device On"
        and p["max"] > p["min"]
    ]
    chk.require(bool(usable), "device has a writable continuous parameter", fatal=True)
    p = usable[0]
    span = p["max"] - p["min"]
    target = p["min"] + span / 2
    out = live.call("set_device_parameter", {"parameter": p["ref"], "value": target})
    chk.require(abs(out["value"] - target) <= 1e-3 * span, f"set {p['name']!r}", str(out))
    again = {q["name"]: q for q in live.call("device_parameters", {"track": n, "device": 0})}
    chk.require(
        abs(again[p["name"]]["value"] - out["value"]) <= 1e-9 * span,
        "parameter readback matches the write",
        f"display={again[p['name']]['display']!r}",
    )
    write = {"parameter": p["ref"], "value": p["max"] + 100}
    ok, why = live.rejected("set_device_parameter", write)
    chk.require(ok, "out-of-range value is rejected", why)
    now = {q["name"]: q for q in live.call("device_parameters", {"track": n, "device": 0})}
    chk.require(now[p["name"]]["value"] == again[p["name"]]["value"], "rejected write left value")
    row = live.call("tracks")[n]
    load = {"track": row["ref"], "root": a.root, "path": a.device_path}
    ok, why = live.rejected("load_item", load, "target_occupied")
    chk.require(ok, "second load on the occupied track is refused", why)
    chk.require(len(live.call("tracks")[n]["devices"]) == 1, "still exactly one device")


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument(
        "--allow-writes", action="store_true", help="required: this script WRITES to Live"
    )
    p.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="bridge port (default %(default)s)"
    )
    p.add_argument("--timeout", type=float, default=15.0, help="seconds per bridge call")
    p.add_argument(
        "--track-name-prefix", default="ALMCP write", help="name prefix for the new track"
    )
    p.add_argument("--color-index", type=int, default=9, help="Live palette index to set")
    p.add_argument(
        "--device-path",
        type=json.loads,
        help="optional JSON array: full browser path to one device, e.g. '[\"Compressor\"]'.\n"
        "Without it the load/parameter/occupied-load steps are skipped (info).",
    )
    p.add_argument("--root", default="audio_effects", help="browser root for --device-path")
    p.add_argument("--load-timeout", type=float, default=30.0, help="seconds to wait for ready")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.device_path is not None and (
        not isinstance(a.device_path, list)
        or not a.device_path
        or not all(isinstance(x, str) and x for x in a.device_path)
    ):
        print("RESULT: ABORT (exit 2): --device-path must be a non-empty JSON array of names")
        return 2
    print(f"mode: WRITING - creates one new audio track on 127.0.0.1:{a.port}; never deletes/saves")
    if not a.allow_writes:
        print("RESULT: REFUSED (exit 2): this script writes to Live; pass --allow-writes to run")
        return 2
    return finish(scenario, a)


if __name__ == "__main__":
    sys.exit(main())
