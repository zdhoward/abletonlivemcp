import json
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP.core import BridgeServer  # noqa: E402
from AbletonLiveMCP.handlers import make_dispatch  # noqa: E402

from AbletonLiveMCP import core  # noqa: E402


class FakeDevice:
    name = "Reverb"
    class_name = "Reverb"


class FakeTrack:
    name = "Bass"
    color_index = 3
    has_midi_input = True
    devices = [FakeDevice()]

    def insert_device(self, *a):
        pass


class FakeSong:
    tempo = 120.0
    is_playing = False
    signature_numerator = 4
    signature_denominator = 4
    tracks = [FakeTrack()]
    return_tracks = []
    scenes = [object(), object()]


class FakeApp:
    def get_major_version(self):
        return 12

    def get_minor_version(self):
        return 4

    def get_bugfix_version(self):
        return 0


def start(dispatch=None, pump=True):
    server = BridgeServer(dispatch or make_dispatch(FakeSong(), FakeApp()), port=0)
    server.start()
    stop = threading.Event()
    if pump:

        def loop():
            while not stop.is_set():
                server.drain()
                time.sleep(0.01)

        threading.Thread(target=loop, daemon=True).start()
    return server, stop


def call(server, payload: bytes):
    with socket.create_connection(("127.0.0.1", server.port), timeout=5) as c:
        c.sendall(payload)
        buf = b""
        while b"\n" not in buf:
            buf += c.recv(4096)
    return json.loads(buf.split(b"\n")[0])


def test_hello_reports_version_and_capabilities():
    server, stop = start()
    try:
        r = call(server, b'{"id":1,"method":"hello"}\n')
        assert r["ok"] and r["id"] == 1
        assert r["result"]["protocol"] == core.PROTOCOL_VERSION
        assert r["result"]["live_version"] == [12, 4, 0]
        assert r["result"]["capabilities"]["track.insert_device"] is True
    finally:
        stop.set()
        server.stop()


def test_session_info_and_tracks():
    server, stop = start()
    try:
        info = call(server, b'{"id":2,"method":"session_info"}\n')["result"]
        assert info["tempo"] == 120.0 and info["scene_count"] == 2
        tracks = call(server, b'{"id":3,"method":"tracks"}\n')["result"]
        assert tracks[0]["devices"][0]["class_name"] == "Reverb"
    finally:
        stop.set()
        server.stop()


def test_bad_json_and_unknown_method_are_errors_not_crashes():
    server, stop = start()
    try:
        assert call(server, b"not json\n")["error"]["type"] == "BadRequest"
        r = call(server, b'{"id":9,"method":"nope"}\n')
        assert not r["ok"] and r["id"] == 9 and "unknown method" in r["error"]["message"]
    finally:
        stop.set()
        server.stop()


def test_timeout_request_is_cancelled_and_never_run_late(monkeypatch):
    monkeypatch.setattr(core, "REQUEST_TIMEOUT", 0.2)
    ran = []
    server, stop = start(dispatch=lambda m, p: ran.append(m), pump=False)
    try:
        r = call(server, b'{"id":5,"method":"mutate"}\n')
        assert r["error"]["type"] == "Timeout"
        server.drain()  # main thread finally gets to it: must skip the cancelled request
        assert ran == []
    finally:
        stop.set()
        server.stop()


def test_binds_loopback_only():
    server, stop = start()
    try:
        assert server._sock.getsockname()[0] == "127.0.0.1"
    finally:
        stop.set()
        server.stop()
