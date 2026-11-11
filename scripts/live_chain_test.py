"""[WRITING] Exact-device chain test through the plan/receipt tools (needs --allow-writes).

Creates ONE new audio track, plans an EQ Eight -> Compressor -> Saturator -> Reverb chain from
the EXPLICIT full browser path arrays you pass (--paths-json; no role resolution, no assumption
that a path is [device_name]) with live_plan_chain, builds it once with live_build_chain, and
checks the receipt against the track read back from Live. It only touches the track it creates
(printed, left in the Set; disposable Set only), never deletes or saves, and never touches a
pre-existing track. User preferences are ignored (exact devices only).

Today appending after the first device is refused (append_unverified), so a correct run ends in
a PARTIAL receipt: that exits 1 unless --expect-partial is given, in which case the script checks
the partial receipt is truthful (stage that stopped, why, readback matches). A complete chain
passes only without --expect-partial. The real bridge is read-only unless bridge.json has
"read_only": false; a read_only refusal ends the run with exit code 2.

Exit codes: 0 every required check passed; 1 a required check failed; 2 did not run (writes not
allowed, bridge unreachable/read-only, bad arguments). Lines marked 'info' never change the code.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from abletonlivemcp.bridge import DEFAULT_PORT, BridgeClient, BridgeError

DEVICES = ("EQ Eight", "Compressor", "Saturator", "Reverb")  # build order


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


def load_json_arg(text, what):
    """Inline JSON, or @file to read it from a file."""
    try:
        if text.startswith("@"):
            text = Path(text[1:]).read_text(encoding="utf-8")
        return json.loads(text)
    except (OSError, ValueError) as exc:
        raise Abort(f"{what} is not readable JSON: {exc}") from None


def check_paths(paths):
    if not isinstance(paths, dict) or set(paths) != set(DEVICES):
        raise Abort(f"--paths-json must be an object with exactly the keys {list(DEVICES)}")
    for name, path in paths.items():
        if not (isinstance(path, list) and path and all(isinstance(x, str) and x for x in path)):
            raise Abort(f"--paths-json[{name!r}] must be a non-empty array of browser names")
    return paths


def call_tool(chk, tool, label, **kwargs):
    """Run a server tool; a refusal (ToolError text) is a required-step failure, not a crash."""
    from mcp.server.mcpserver.exceptions import ToolError

    try:
        return tool(**kwargs)
    except ToolError as exc:
        text = str(exc)
        if text.startswith("read_only"):
            raise Abort(f"{text}") from None
        chk.require(False, f"{label} succeeded", text, fatal=True)


def scenario(live, a, chk):
    # Exact stages only: never read the owner's preferences file; point it at a missing file.
    os.environ["ABLETONLIVEMCP_PREFS"] = str(Path(__file__).with_name(".no-preferences.json"))
    from abletonlivemcp import server

    server._bridge = BridgeClient(port=a.port, timeout=a.timeout)
    paths = check_paths(load_json_arg(a.paths_json, "--paths-json"))
    params = load_json_arg(a.params_json, "--params-json") if a.params_json else {}
    if not isinstance(params, dict) or not set(params) <= set(DEVICES):
        raise Abort(f"--params-json must be an object keyed by a subset of {list(DEVICES)}")

    before = live.call("session_info")
    n, generation = before["track_count"], before["generation"]
    baseline = shape(live.call("tracks"))
    chk.info("session", f"tracks={n} generation={generation}")

    live.call("create_track", {"kind": "audio", "index": -1, "generation": generation})
    chk.require(live.call("session_info")["track_count"] == n + 1, "track count +1", fatal=True)
    row = live.call("tracks")[n]
    chk.require(
        not row["has_midi_input"] and not row["devices"], "new track is empty audio", fatal=True
    )
    name = f"{a.track_name_prefix} {time.strftime('%H%M%S')}"
    out = live.call("set_track_name", {"track": row["ref"], "name": name})
    chk.require(out.get("name") == name, "rename result", repr(out.get("name")))
    chk.info("created", f"audio track index={n} name={name!r} (left in the Set)")

    stages = []
    for device in DEVICES:
        stage = {"device": device, "root": a.root, "path": paths[device]}
        if device in params:
            stage["params"] = params[device]
        stages.append(stage)
    plan = call_tool(chk, server.live_plan_chain, "live_plan_chain", track=n, stages=stages)
    got = [(s["device"], s["root"], list(s["path"]), s["role"]) for s in plan["stages"]]
    want = [(d, a.root, paths[d], None) for d in DEVICES]
    chk.require(got == want, "plan holds exactly the supplied paths, no role resolution", str(got))
    chk.require(plan["target"]["index"] == n and plan["intent_complete"], "plan target and intent")
    chk.info("plan", f"plan_id={plan['plan_id']} generation={plan['target']['generation']}")

    receipt = call_tool(chk, server.live_build_chain, "live_build_chain", plan_id=plan["plan_id"])
    report(chk, receipt)
    verify_receipt(live, chk, receipt, n)
    rows = live.call("tracks")
    chk.require(len(rows) == n + 1 and shape(rows)[:n] == baseline, "pre-existing tracks unchanged")
    verdict(chk, receipt, a)
    chk.info(
        "identity", f"audio track index={n} name={rows[n]['name']!r} plan_id={plan['plan_id']}"
    )


def report(chk, receipt):
    chk.info(
        "receipt",
        f"status={receipt['status']} intent_fulfilled={receipt['intent_fulfilled']} "
        f"completed={receipt['completed']} stopped_at={receipt['stopped_at']} "
        f"stop_reason={receipt['stop_reason']}",
    )
    for s in receipt["stages"]:
        chk.info(
            f"stage {s['index']} {s['device']}",
            f"outcome={s['outcome']} reason={s['reason']} operation={s['operation']} "
            f"device_index={s['device_index']}",
        )
        for p in s["params"]:
            chk.info(
                f"  {p['name']}",
                f"requested={p['requested']!r} actual={p['actual']!r} exact={p['exact']}",
            )
        for problem in s["problems"]:
            chk.info("  problem", problem[:200])


def verify_receipt(live, chk, receipt, n):
    stages = receipt["stages"]
    applied = [s for s in stages if s["outcome"] == "applied"]
    unknown = [s for s in stages if s["outcome"] == "unknown"]
    devices = live.call("tracks")[n]["devices"]
    chk.info("devices on the track", str([d["name"] for d in devices]))
    chk.require(
        len(applied) <= len(devices) <= len(applied) + len(unknown),
        "device count on the track matches the receipt",
        f"{len(devices)} devices; applied={len(applied)} unknown={len(unknown)}",
    )
    chk.require(
        all(s["device_index"] == s["index"] for s in applied), "applied stages loaded in order"
    )
    stop = receipt["stopped_at"]
    later = [s for s in stages if stop is not None and s["index"] > stop]
    chk.require(
        all(s["outcome"] == "not_applied" and s["reason"] == "not_attempted" for s in later),
        "no stage after the stopped stage was attempted",
    )


def verdict(chk, receipt, a):
    stop, reason = receipt["stopped_at"], receipt["stop_reason"]
    if a.expect_partial:
        chk.require(
            receipt["status"] == "partial", "receipt is partial as expected", receipt["status"]
        )
        chk.require(stop is not None and bool(reason), "partial receipt names the stage and reason")
        chk.require(
            receipt["completed"] == list(range(stop or 0)),
            "completed stages are exactly those before the stop",
            str(receipt["completed"]),
        )
        if a.expect_stop_reason:
            chk.require(reason == a.expect_stop_reason, "stop reason", f"{reason!r}")
        return
    if stop is not None:
        stage = receipt["stages"][stop]
        chk.require(False, f"chain complete (stage {stop} {stage['device']} stopped)", reason)
    else:
        chk.require(
            receipt["status"] == "complete" and receipt["intent_fulfilled"], "chain complete"
        )


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
        "--track-name-prefix", default="ALMCP chain", help="name prefix for the new track"
    )
    p.add_argument(
        "--paths-json",
        required=True,
        help='required: JSON object (or @file) mapping each of "EQ Eight", "Compressor",\n'
        '"Saturator", "Reverb" to its full browser path array under --root, e.g.\n'
        '\'{"EQ Eight": ["EQ Eight"], ...}\'. Use paths you observed in the browser.',
    )
    p.add_argument("--root", default="audio_effects", help="browser root of every path")
    p.add_argument(
        "--params-json", help="optional JSON object (or @file): device -> {parameter: target}"
    )
    p.add_argument(
        "--expect-partial",
        action="store_true",
        help="pass only if the receipt is a truthful PARTIAL (append is refused today)",
    )
    p.add_argument(
        "--expect-stop-reason",
        help="with --expect-partial: required stop_reason, e.g. append_unverified",
    )
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    print(f"mode: WRITING - creates one audio track and loads 4 devices on 127.0.0.1:{a.port}")
    if not a.allow_writes:
        print("RESULT: REFUSED (exit 2): this script writes to Live; pass --allow-writes to run")
        return 2
    try:
        check_paths(load_json_arg(a.paths_json, "--paths-json"))
    except Abort as exc:
        print(f"RESULT: ABORT (exit 2): {exc}")
        return 2
    return finish(scenario, a)


if __name__ == "__main__":
    sys.exit(main())
