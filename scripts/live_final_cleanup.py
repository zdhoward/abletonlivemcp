"""List or delete only ALMCP-FINAL scratch tracks/returns/scenes; never save the Set.

Dry-run is the default. --apply is authorized only for disposable proof material.
Apply mode restores safety defaults after discovery/deletion failures when the config is readable
and writable. Credentials are never printed.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import time
from pathlib import Path

from abletonlivemcp.bridge import BridgeClient
from abletonlivemcp.config import config_path

SCRATCH = re.compile(r"^(?:[A-Z]{1,2}-)?ALMCP-FINAL (?:\d{4}-\d{6} .+|clips audio)$")


def call(bridge, method, params=None):
    result = bridge.call(method, params)
    if isinstance(result, dict) and result.get("refused"):
        raise RuntimeError(f"{method}: {result.get('code')}")
    return result


def cleanup(bridge, apply, enable=None):
    tracks = call(bridge, "get_tracks")["tracks"]
    scenes = call(bridge, "get_scenes")["scenes"]
    cues = [c for c in call(bridge, "get_arrangement", {"include": ["cues"]})["cues"]
            if c["name"] == "ALMCP-FINAL cue" and c["time"] == 4.0]
    targets = [
        {"kind": "return_track" if t["kind"] == "return" else "track",
         "track": t["track"], "expect_name": t["name"]}
        for t in tracks if SCRATCH.fullmatch(t["name"]) and t["kind"] != "master"
    ]
    targets += [
        {"kind": "scene", "scene": s["scene"], "expect_name": s["name"]}
        for s in scenes if SCRATCH.fullmatch(s["name"])
    ]
    print(json.dumps(targets, indent=2))
    print(f"Scratch cues: {len(cues)}")
    if not apply:
        return
    enable()
    if cues:
        if call(bridge, "session_info").get("is_playing"):
            raise RuntimeError("stop transport before scratch cue cleanup")
        cue_refs = call(bridge, "ref_issue", {"targets": [
            {"kind": "cue", "cue": c["cue"], "expect_name": c["name"]} for c in cues
        ]})["refs"]
        result = call(bridge, "set_cue_points", {"cues": [
            {"cue": r["ref"], "expect_name": c["name"], "action": "delete"}
            for c, r in zip(cues, cue_refs, strict=True)
        ]})
        operation = result["applied"][0]["operation"]
        deadline = time.monotonic() + 15
        while True:
            result = call(bridge, "operation", {"operation": operation})
            if result["state"] == "ready":
                break
            if result["state"] != "pending" or time.monotonic() >= deadline:
                raise RuntimeError(f"cue cleanup unresolved: {result['state']}; do not retry")
            time.sleep(0.25)
        print(f"Deleted {len(cues)} scratch cues")
    # Retain references and names before structural deletions shift indices.
    refs = call(bridge, "ref_issue", {"targets": targets})["refs"] if targets else []
    for kind, method in (("scene", "delete_scenes"), ("track", "delete_tracks"),
                         ("return_track", "delete_tracks")):
        rows = [{"kind": t["kind"], "ref": r["ref"], "expect_name": t["expect_name"]}
                for t, r in zip(targets, refs, strict=True) if t["kind"] == kind]
        if rows:
            result = call(bridge, method, {"targets": rows})
            if result.get("status") != "complete":
                raise RuntimeError(f"{method}: incomplete cleanup: {result}")
            print(f"Deleted {len(rows)} scratch {kind} objects")
    files = 0
    for path in Path(tempfile.gettempdir()).glob("ALMCP-FINAL ????-?????? clips-midi.mid"):
        if re.fullmatch(r"ALMCP-FINAL \d{4}-\d{6} clips-midi\.mid", path.name):
            path.unlink()
            files += 1
    print(f"Deleted {files} scratch MIDI exports")


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.apply or args.dry_run:
        cleanup(BridgeClient(), False)
        return
    path = config_path()
    config = json.loads(path.read_text(encoding="utf-8"))

    def policy(writable):
        config["read_only"] = not writable
        config.pop("dev_probes", None)
        path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    try:
        policy(False)
        cleanup(BridgeClient(), True, lambda: policy(True))
    finally:
        policy(False)


if __name__ == "__main__":
    main()
