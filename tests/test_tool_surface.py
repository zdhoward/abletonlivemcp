"""The MCP tool surface: per-module snapshots, the core size budget, toolsets, selectors.

A surface change is deliberate: regenerate the snapshots with
``ABLETONLIVEMCP_UPDATE_SURFACE=1 pytest tests/test_tool_surface.py`` and review the diff.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from mcp.server.mcpserver import MCPServer
from pydantic import TypeAdapter, ValidationError

from abletonlivemcp import server
from abletonlivemcp.models import ClipAddr, DevicePath, ParamSel, TrackSel

SNAPSHOTS = Path(__file__).parent / "tool_surface"
PRESETS = [server.READ, server.CREATE, server.OVERWRITE, server.CONTROL, server.DESTRUCTIVE]
CORE_BUDGET = 40 * 1024


def _listing(enabled) -> list[dict]:
    surface = MCPServer("surface")
    server.install(surface, frozenset(enabled))
    tools = asyncio.run(surface.list_tools())
    return [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools]


def test_tool_surface_snapshots_per_module():
    by_module: dict[str, list] = {}
    for tool in _listing(server.TOOLSETS):
        spec = server.SPECS[tool["name"]]
        assert tool["title"] and spec.annotations in PRESETS, tool["name"]
        assert "outputSchema" in tool, tool["name"]
        by_module.setdefault(spec.module.rsplit(".", 1)[-1], []).append(tool)
    if os.environ.get("ABLETONLIVEMCP_UPDATE_SURFACE"):
        for old in SNAPSHOTS.glob("*.json"):
            old.unlink()
        SNAPSHOTS.mkdir(exist_ok=True)
        for module, tools in by_module.items():
            text = json.dumps(sorted(tools, key=lambda t: t["name"]), indent=1, sort_keys=True)
            (SNAPSHOTS / f"{module}.json").write_text(text + "\n", encoding="utf-8")
    stored = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in SNAPSHOTS.glob("*.json")}
    assert sorted(stored) == sorted(by_module), "a module gained or lost its tools"
    for module, tools in by_module.items():
        assert stored[module] == sorted(tools, key=lambda t: t["name"]), f"{module} surface changed"


def test_core_listing_fits_the_size_budget():
    size = len(json.dumps(_listing({"core"}), separators=(",", ":")))
    assert size <= CORE_BUDGET, f"core list_tools is {size} bytes (budget {CORE_BUDGET})"


def test_toolset_switch_and_unknown_name_stops_startup():
    assert server.select_toolsets(None) == {"core"}
    assert server.select_toolsets("drums, Racks") == {"core", "drums", "racks"}
    assert server.select_toolsets(["all"]) == set(server.TOOLSETS) - {"experimental"}
    assert server.toolset_of("abletonlivemcp.tools.devices_advanced") == "devices-advanced"
    env = {**os.environ, server.TOOLSETS_ENV: "core,bogus"}
    run = subprocess.run(
        [sys.executable, "-m", "abletonlivemcp.server"],
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 2 and "bogus" in run.stderr


def test_selectors_and_lease_ride_on_every_call(monkeypatch):
    track, path, param = TypeAdapter(TrackSel), TypeAdapter(DevicePath), TypeAdapter(ParamSel)
    sels = [0, "return:1", "master"]
    assert [track.validate_python(v) for v in sels] == sels
    assert path.validate_python([0, "pad:36", 1]) == [0, "pad:36", 1]
    assert param.validate_python("Gain") == "Gain"
    assert ClipAddr(track="master", scene=2).scene == 2
    for bad, adapter in (("return:x", track), (-1, track), (["pad:36"], path), ([0] * 13, path)):
        with pytest.raises(ValidationError):
            adapter.validate_python(bad)
    assert server.shape([{"a": 1, "b": 2}], "concise", ("a",)) == [{"a": 1}]

    sent = []
    monkeypatch.setattr(server._bridge, "call", lambda m, p=None: sent.append((m, p)) or {})
    monkeypatch.setattr(server, "_lease", "TOKEN")
    server._call("set_track_name", {"track": "R"})
    server._call("tracks")
    assert [p["lease"] for _, p in sent] == ["TOKEN", "TOKEN"]
