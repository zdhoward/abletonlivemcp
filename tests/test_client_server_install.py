import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

import abletonlivemcp  # noqa: E402
from abletonlivemcp import install  # noqa: E402
from abletonlivemcp.bridge import BridgeClient, BridgeError  # noqa: E402

# The authenticated client/server roundtrip lives in tests/test_bridge.py (inert dispatch).


def test_client_unreachable_message_is_actionable(tmp_path, monkeypatch):
    from abletonlivemcp import config

    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(tmp_path / "private" / "bridge.json"))
    config.ensure_config()
    with pytest.raises(BridgeError) as e:
        BridgeClient(port=1, timeout=1).call("hello")
    assert e.value.kind == "Unreachable" and "Live" in str(e.value)


def test_server_registers_tools():
    from abletonlivemcp.server import mcp

    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert {"live_hello", "live_get_session", "live_get_tracks", "live_plan_chain"} <= names
    assert "als_summary" not in names  # deferred tools are not registered in v1


def test_schema_edits_reach_tools_list_and_explicit_null_still_works(monkeypatch):
    """Guards server.registered_tool (private SDK access) and _drop_optional_null: the listing
    advertises `include` without null, yet a real MCP call with include=null is accepted."""
    from mcp import Client

    from abletonlivemcp import server
    from abletonlivemcp.tools import session

    async def run():
        async with Client(server.mcp) as client:
            listed = {t.name: t for t in (await client.list_tools()).tools}
            prop = listed["live_get_session"].input_schema["properties"]["include"]
            assert "anyOf" not in prop and prop["type"] == "array", prop
            return await client.call_tool("live_get_session", {"include": None})

    seen, reply = [], {"generation": 1, "tempo": 120.0, "signature": [4, 4], "is_playing": False}
    reply.update(track_count=0, return_count=0, scene_count=0)
    monkeypatch.setattr(session, "_call", lambda m, p=None: seen.append(p) or dict(reply))
    result = asyncio.run(run())
    assert not result.is_error and seen == [{}], result


def test_install_copies_script_and_rejects_non_library(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(home / "bridge.json"))
    with pytest.raises(install.InstallError):
        install.install(tmp_path)
    (tmp_path / "Presets").mkdir()
    dest = install.install(tmp_path)
    assert (dest / "__init__.py").is_file() and (dest / "core.py").is_file()
    assert not list(dest.rglob("__pycache__"))
    install.install(tmp_path)  # reinstall over an existing copy works
    # the installed script reports exactly the identity the host ships; an edit changes it
    from AbletonLiveMCP import core

    shipped = install.packaged_identity()
    assert core.script_identity(str(dest)) == shipped
    assert shipped[0] == abletonlivemcp.__version__
    (dest / "dom_view.py").write_bytes((dest / "dom_view.py").read_bytes() + b"\n# stale")
    assert core.script_identity(str(dest)) == (shipped[0], core.script_identity(str(dest))[1])
    assert core.script_identity(str(dest))[1] != shipped[1]


def test_hello_warns_when_the_running_script_is_not_the_hosts():
    from abletonlivemcp.tools import session

    version, build = install.packaged_identity()
    assert session.compare_script({"version": version, "build": build})["match"] is True
    stale = session.compare_script({"version": version, "build": "sha256:0000000000000000"})
    assert stale["match"] is False and stale["host_build"] == build
    assert session.compare_script(None)["version"] == "unknown"  # an old script reports none
