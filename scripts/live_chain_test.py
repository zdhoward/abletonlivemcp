"""Build the vocal presets on NEW audio tracks in real Live (no deletes, no save).

Usage: python scripts/live_chain_test.py [preferences.json]
With a preferences file the chains use those devices where they are installed and controllable;
without one they use stock devices. Prints the plan (what was chosen and why) and the build.
"""

import json
import sys
import time
from pathlib import Path

from abletonlivemcp import chain
from abletonlivemcp.bridge import BridgeClient
from abletonlivemcp.chain_presets import PRESETS
from abletonlivemcp.preferences import load_preferences
from abletonlivemcp.resolve import plan_chain

c = BridgeClient()
prefs = load_preferences(Path(sys.argv[1])) if len(sys.argv) > 1 else {}
print("preferences:", json.dumps(prefs))
for name, preset in PRESETS.items():
    start = time.time()
    try:
        plan = plan_chain(c.call, preset["stages"], prefs)
    except chain.ChainError as exc:
        print("REFUSED", name, exc)
        continue
    t = c.call("create_track", {"kind": "audio", "index": -1})["track_count"] - 1
    c.call("set_track_name", {"track": t, "name": f"ALMCP {name}"})
    try:
        out = chain.build_chain(c.call, t, plan["stages"])
    except chain.ChainError as exc:
        print("BUILD REFUSED", name, exc)
        continue
    print(f"== {name}: ok={out['ok']} in {time.time() - start:.1f}s")
    for rep, s in zip(plan["report"], out["stages"], strict=True):
        print(f"  {rep['role']:<11} -> {s['device']} (access {rep['access']})")
        for line in rep["skipped"] + rep["notes"]:
            print("       note:", line)
        for p in s["params"]:
            print(
                "       ",
                "ok " if p["exact"] else "OFF",
                p["name"],
                p["requested"],
                "->",
                p["actual"],
            )
        for pr in s["problems"]:
            print("       PROBLEM", pr[:300])
print(json.dumps([d["name"] for d in c.call("tracks")[-1]["devices"]]))
