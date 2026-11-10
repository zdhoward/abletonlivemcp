import asyncio
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from abletonlivemcp import install  # noqa: E402
from abletonlivemcp.bridge import BridgeClient, BridgeError  # noqa: E402
from AbletonLiveMCP.core import BridgeServer  # noqa: E402
from AbletonLiveMCP.handlers import make_dispatch  # noqa: E402
from test_bridge import FakeApp, FakeSong  # noqa: E402


def _running_server():
    server = BridgeServer(make_dispatch(FakeSong(), FakeApp()), port=0)
    server.start()
    stop = threading.Event()

    def loop():
        while not stop.is_set():
            server.drain()
            time.sleep(0.01)

    threading.Thread(target=loop, daemon=True).start()
    return server, stop


def test_client_roundtrip_and_error():
    server, stop = _running_server()
    try:
        c = BridgeClient(port=server.port)
        assert c.call("session_info")["tempo"] == 120.0
        with pytest.raises(BridgeError) as e:
            c.call("nope")
        assert e.value.kind == "ValueError"
    finally:
        stop.set()
        server.stop()


def test_client_unreachable_message_is_actionable():
    with pytest.raises(BridgeError) as e:
        BridgeClient(port=1, timeout=1).call("hello")
    assert e.value.kind == "Unreachable" and "Live" in str(e.value)


def test_server_registers_tools():
    from abletonlivemcp.server import mcp

    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert {"live_hello", "live_session_info", "live_tracks", "als_summary"} <= names


def test_install_copies_script_and_rejects_non_library(tmp_path):
    with pytest.raises(SystemExit):
        install.install(tmp_path)
    (tmp_path / "Presets").mkdir()
    dest = install.install(tmp_path)
    assert (dest / "__init__.py").is_file() and (dest / "core.py").is_file()
    assert not list(dest.rglob("__pycache__"))
    install.install(tmp_path)  # reinstall over an existing copy works
