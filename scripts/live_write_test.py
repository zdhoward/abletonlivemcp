"""Write test against a running Live. Touches only a NEW track and restores tempo. Never saves."""

import json

from abletonlivemcp.bridge import BridgeClient, BridgeError

c = BridgeClient()


def step(label, method, params=None):
    try:
        r = c.call(method, params)
        print(f"OK   {label}: {json.dumps(r)[:300]}")
        return r
    except BridgeError as e:
        print(f"FAIL {label}: {e}")
        return None


before = c.call("session_info")
n = before["track_count"]
step("create audio track", "create_track", {"kind": "audio"})
idx = c.call("session_info")["track_count"] - 1
step("rename", "set_track_name", {"track": idx, "name": "ALMCP test"})
step("color", "set_track_color", {"track": idx, "color_index": 9})
step("load Compressor", "load_item", {"track": idx, "root": "audio_effects", "path": ["Compressor"]})
tr = [t for t in c.call("tracks") if t["index"] == idx][0]
print("devices on new track:", tr["devices"])
if tr["devices"]:
    params = c.call("device_parameters", {"track": idx, "device": 0})
    print("params:", [(p["index"], p["name"], p["value"], p["min"], p["max"]) for p in params][:12])
    p = next(p for p in params if p["is_enabled"] and not p["is_quantized"] and p["name"] != "Device On")
    mid = (p["min"] + p["max"]) / 2
    step(f"set {p['name']}", "set_device_parameter",
         {"track": idx, "device": 0, "parameter": p["index"], "value": mid})
    step("out-of-range rejected", "set_device_parameter",
         {"track": idx, "device": 0, "parameter": p["index"], "value": p["max"] + 100})
step("tempo +1", "set_tempo", {"bpm": before["tempo"] + 1})
step("tempo restore", "set_tempo", {"bpm": before["tempo"]})
step("bad track index rejected", "set_track_name", {"track": 999, "name": "x"})
print("tracks before/after:", n, c.call("session_info")["track_count"])
