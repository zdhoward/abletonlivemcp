"""Real-Live check of transport, scene, clip and note handlers.

Touches only a NEW midi track and a NEW scene it creates. Nothing is saved; nothing is deleted.
"""

import json
import time

from abletonlivemcp.bridge import BridgeClient

c = BridgeClient()
state = {}


def step(label, fn):
    try:
        out = fn()
        print("OK  ", label, json.dumps(out)[:300])
        return out
    except Exception as exc:  # report every failure, keep going
        print("FAIL", label, type(exc).__name__, str(exc)[:300])
        return None


hello = step("hello", lambda: c.call("hello"))
before = step("get_transport", lambda: c.call("get_transport"))
tr = step("create midi track", lambda: c.call("create_track", {"kind": "midi", "index": -1}))
sc = step("create scene", lambda: c.call("create_scene", {"index": -1}))
if tr and sc:
    t = (tr.get("track_count") or 0) - 1
    s = (sc.get("scene_count") or 0) - 1 if "scene_count" in sc else sc.get("index")
    step("rename track", lambda: c.call("set_track_name", {"track": t, "name": "ALMCP clip test"}))
    step("rename scene", lambda: c.call("set_scene_name", {"scene": s, "name": "ALMCP test"}))
    step("create clip", lambda: c.call("create_clip", {"track": t, "scene": s, "length_beats": 4}))
    step(
        "create clip again (must fail: occupied)",
        lambda: c.call("create_clip", {"track": t, "scene": s, "length_beats": 4}),
    )
    step("get_clip", lambda: c.call("get_clip", {"track": t, "scene": s}))
    notes = [
        {"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100},
        {"pitch": 64, "start_time": 1.0, "duration": 1.0, "velocity": 90},
        {"pitch": 67, "start_time": 2.0, "duration": 2.0, "velocity": 80, "mute": False},
    ]
    step("add_notes", lambda: c.call("add_notes", {"track": t, "scene": s, "notes": notes}))
    got = step("get_notes", lambda: c.call("get_notes", {"track": t, "scene": s}))
    step("fire_clip", lambda: c.call("fire_clip", {"track": t, "scene": s}))
    time.sleep(1.5)
    step("get_clip after fire", lambda: c.call("get_clip", {"track": t, "scene": s}))
    step("get_transport while playing", lambda: c.call("get_transport"))
    step("stop_clip", lambda: c.call("stop_clip", {"track": t, "scene": s}))
    step("fire_scene", lambda: c.call("fire_scene", {"scene": s}))
    time.sleep(1.0)
step("stop", lambda: c.call("stop"))
step("play", lambda: c.call("play"))
step("stop", lambda: c.call("stop"))
step("bad scene index (must fail)", lambda: c.call("fire_scene", {"scene": 9999}))
step(
    "bad note pitch (must fail)",
    lambda: c.call(
        "add_notes",
        {
            "track": 0,
            "scene": 0,
            "notes": [{"pitch": 200, "start_time": 0, "duration": 1, "velocity": 90}],
        },
    ),
)
