"""Read-only probe of a running Live via the bridge. Prints capabilities and browser layout."""

import json

from abletonlivemcp.bridge import BridgeClient, BridgeError

c = BridgeClient()


def show(label, fn):
    try:
        print(f"## {label}\n{json.dumps(fn(), indent=1)[:1500]}")
    except BridgeError as e:
        print(f"## {label} ERROR {e}")


show("hello", lambda: c.call("hello"))
roots = c.call("browser_roots")
for r in roots:
    show(f"list {r}", lambda r=r: [i["name"] for i in c.call("browser_list", {"root": r})["items"]][:25])
show("search Reverb", lambda: c.call("browser_search", {"root": "audio_effects", "query": "reverb"}))
show("params track4 dev0", lambda: [p["name"] for p in c.call("device_parameters", {"track": 4, "device": 0})][:15])
