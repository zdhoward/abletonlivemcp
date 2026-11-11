"""The one authoritative settle/readback check: commands re-read state after Live applies them."""

from abletonlivemcp import server


class FakeBridge:
    def __init__(self):
        self.calls = []

    def call(self, method, params=None):
        self.calls.append((method, params))
        if method == "session_info":
            return {"generation": 5}
        if method == "clip_slot":
            return {"slot": "S", "has_clip": True, "clip": "C"}
        return {"method": method}


def test_transport_and_clip_launches_read_back_after_settling(monkeypatch):
    fake, slept = FakeBridge(), []
    monkeypatch.setattr(server, "_bridge", fake)
    monkeypatch.setattr(server, "_writable", lambda: None)
    monkeypatch.setattr(server.time, "sleep", slept.append)

    assert server.live_set_transport(playing=True) == {"method": "get_transport"}
    assert server.live_set_transport(playing=False) == {"method": "get_transport"}
    assert server.live_fire_clip(2, 3) == {"method": "get_clip"}
    assert server.live_stop_clip(2, 3) == {"method": "get_clip"}

    assert [m for m, _ in fake.calls if m not in ("session_info", "clip_slot")] == [
        "play",
        "get_transport",
        "stop",
        "get_transport",
        "fire_clip",
        "get_clip",
        "stop_clip",
        "get_clip",
    ]
    by_method = {m: p for m, p in fake.calls}
    assert by_method["play"] == {"generation": 5}  # global writes carry the generation
    assert by_method["fire_clip"] == {"clip": "C"}  # clip writes carry a reference, not indices
    assert by_method["get_clip"] == {"track": 2, "scene": 3}  # reads still use indices
    assert slept == [server.SETTLE_SECONDS] * 4
