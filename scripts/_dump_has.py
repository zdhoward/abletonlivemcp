"""List P-01 dump members matching keywords (dev helper): _dump_has.py kw [kw ...]"""

import json
import sys

d = json.load(open("docs/data/live-12.2-api.json", encoding="utf-8"))["classes"]
for cls, entry in d.items():
    members = entry.get("members", entry) if isinstance(entry, dict) else entry
    names = members if isinstance(members, list) else list(members)
    names = [m if isinstance(m, str) else m.get("name") for m in names]
    hit = [n for n in names if any(k in str(n).lower() for k in sys.argv[1:])]
    if hit and cls in ("Clip", "Track", "Song", "Application", "AudioClip", "Device"):
        print(cls, hit)
