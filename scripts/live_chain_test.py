"""Build the stock vocal presets on NEW audio tracks in real Live (no deletes, no save)."""

import json
import time

from abletonlivemcp import chain
from abletonlivemcp.bridge import BridgeClient
from abletonlivemcp.chain_presets import PRESETS

c = BridgeClient()
for name, preset in PRESETS.items():
    t = c.call("create_track", {"kind": "audio", "index": -1})["track_count"] - 1
    c.call("set_track_name", {"track": t, "name": f"ALMCP {name}"})
    start = time.time()
    try:
        out = chain.build_chain(c.call, t, preset["stages"])
    except chain.ChainError as exc:
        print("REFUSED", name, exc)
        continue
    print(f"== {name}: ok={out['ok']} in {time.time() - start:.1f}s")
    for s in out["stages"]:
        print("  ", s["device"], "index", s["index"])
        for p in s["params"]:
            print(
                "     ",
                "ok " if p["exact"] else "OFF",
                p["name"],
                p["requested"],
                "->",
                p["actual"],
            )
        for pr in s["problems"]:
            print("      PROBLEM", pr[:300])
print(json.dumps([d["name"] for d in c.call("tracks")[-1]["devices"]]))
