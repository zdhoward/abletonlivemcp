"""Load named third-party plugins on a NEW audio track and dump what Live exposes of each.

Usage: python scripts/live_probe_plugins.py "Pro-C 2" "Pro-Q 3" ...
Writes docs/data/plugin-params-probe.json. Creates one track; deletes nothing; saves nothing.
"""

import json
import sys
from pathlib import Path

from abletonlivemcp.bridge import BridgeClient

c = BridgeClient()
wanted = sys.argv[1:] or ["Pro-C 2", "Pro-Q 3", "Pro-L 2", "Pro-R", "ValhallaVintageVerb"]
track = c.call("create_track", {"kind": "audio", "index": -1})["track_count"] - 1
c.call("set_track_name", {"track": track, "name": "ALMCP plugin probe"})
report = {}
for query in wanted:
    hits = [
        h
        for h in c.call("browser_search", {"root": "plugins", "query": query, "limit": 10})[
            "results"
        ]
        if h["is_loadable"]
    ]
    if not hits:
        report[query] = {"error": "no loadable match in the plugins browser"}
        print("NO MATCH", query)
        continue
    hit = next((h for h in hits if h["name"].lower() == query.lower()), hits[0])
    try:
        loaded = c.call("load_item", {"track": track, "root": "plugins", "path": hit["path"]})
        idx = loaded["devices_after"] - 1
        params = c.call("device_parameters", {"track": track, "device": idx})
        report[query] = {"path": hit["path"], "count": len(params), "parameters": params}
        named = [p["name"] for p in params]
        print(f"{query}: loaded as {hit['path']}, {len(params)} parameters")
        print("   first 25:", named[:25])
    except Exception as exc:  # noqa: BLE001 - report and continue with the next plugin
        report[query] = {"path": hit["path"], "error": str(exc)[:300]}
        print("FAIL", query, str(exc)[:200])
dest = Path("docs/data/plugin-params-probe.json")
dest.write_text(json.dumps(report, indent=1), encoding="utf8")
print("wrote", dest)
