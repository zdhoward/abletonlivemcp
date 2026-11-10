from abletonlivemcp import server


class FakeBridge:
    def __init__(self):
        self.calls = []

    def call(self, method, params=None):
        self.calls.append((method, params))
        return {"method": method}


def test_transport_and_clip_launches_read_back_after_settling(monkeypatch):
    fake, slept = FakeBridge(), []
    monkeypatch.setattr(server, "_bridge", fake)
    monkeypatch.setattr(server.time, "sleep", slept.append)

    assert server.live_play() == {"method": "get_transport"}
    assert server.live_stop() == {"method": "get_transport"}
    assert server.live_fire_clip(2, 3) == {"method": "get_clip"}
    assert server.live_stop_clip(2, 3) == {"method": "get_clip"}

    assert [m for m, _ in fake.calls] == [
        "play",
        "get_transport",
        "stop",
        "get_transport",
        "fire_clip",
        "get_clip",
        "stop_clip",
        "get_clip",
    ]
    assert fake.calls[5][1] == {"track": 2, "scene": 3}
    assert slept == [server.SETTLE_SECONDS] * 4
