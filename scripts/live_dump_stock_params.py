"""Load candidate stock audio effects onto a NEW audio track and dump their parameters.

Writes docs/data/stock-params-live-12.2.json. Creates one new track; deletes nothing; saves nothing.
"""

import json
from pathlib import Path

from abletonlivemcp.bridge import BridgeClient

WANT = [
    "EQEight",
    "ChannelEQ",
    "Compressor",
    "GlueCompressor",
    "MultibandDynamics",
    "Limiter",
    "Saturator",
    "DynamicTube",
    "Roar",
    "Reverb",
    "HybridReverb",
    "Echo",
    "Delay",
    "AutoFilter",
    "Utility",
    "Chorus-Ensemble",
    "DrumBuss",
    "Pedal",
    "Redux",
    "Vocoder",
    "Spectrum",
]
c = BridgeClient()
names = c.call("browser_list", {"root": "audio_effects", "path": []})
items = names["items"] if isinstance(names, dict) and "items" in names else names
flat = [i["name"] if isinstance(i, dict) else i for i in items]
print("browser has", len(flat), "audio effects")
lower = {n.lower().replace(" ", ""): n for n in flat}

tr = c.call("create_track", {"kind": "audio", "index": -1})
t = tr["track_count"] - 1
c.call("set_track_name", {"track": t, "name": "ALMCP stock dump"})
out, missing = {}, []
for want in WANT:
    real = lower.get(want.lower().replace(" ", ""))
    if not real:
        missing.append(want)
        continue
    try:
        r = c.call("load_item", {"track": t, "root": "audio_effects", "path": [real]})
        d = r["devices_after"] - 1
        out[real] = c.call("device_parameters", {"track": t, "device": d})
        print("OK  ", real, len(out[real]), "params")
    except Exception as exc:
        print("FAIL", real, str(exc)[:200])
print("not in browser:", missing)
dest = Path("docs/data/stock-params-live-12.2.json")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps({"live": [12, 2, 0], "devices": out}, indent=1), encoding="utf8")
print("wrote", dest, "browser names sample:", flat[:60])
