"""The one authoritative settle/readback check: commands re-read state after Live applies them."""

from abletonlivemcp import server
from abletonlivemcp.bridge import BridgeError


class FakeBridge:
    def __init__(self, fail=()):
        self.calls, self.fail = [], set(fail)

    def call(self, method, params=None):
        self.calls.append((method, params))
        if method in self.fail:
            raise BridgeError("timeout", "no reply", may_have_applied=False)
        if method == "session_info":
            return {"generation": 5}
        if method == "clip_slot":
            return {"slot": "S", "has_clip": True, "clip": "C"}
        return {"method": method}


def test_transport_and_clip_launches_read_back_after_settling(monkeypatch):
    fake, slept = FakeBridge(), []
    monkeypatch.setattr(server, "_bridge", fake)
    monkeypatch.setattr(server, "_writable", lambda *_args: None)
    monkeypatch.setattr(server.time, "sleep", slept.append)

    assert server.live_transport("play")["settled"] == {
        "is_playing": None,
        "current_song_time": None,
        "tempo": None,
    }
    assert "settled" in server.live_transport("stop")

    assert [m for m, _ in fake.calls if m not in ("session_info", "clip_slot")] == [
        "transport",
        "get_session",
        "transport",
        "get_session",
    ]
    by_method = {m: p for m, p in fake.calls}
    assert by_method["transport"] == {"action": "stop", "generation": 5}  # global: generation
    assert slept == [server.SETTLE_SECONDS] * 2


def test_a_failed_readback_keeps_the_applied_command_reply(monkeypatch):
    monkeypatch.setattr(server, "_bridge", FakeBridge(fail={"get_session"}))
    monkeypatch.setattr(server, "_writable", lambda *_args: None)
    monkeypatch.setattr(server.time, "sleep", lambda _s: None)
    out = server.live_transport("play")  # no "(not applied)" ToolFailure: play did happen
    assert out["method"] == "transport" and out["settled"] is None
    assert out["verification"].startswith("the command was applied; reading the state back")
