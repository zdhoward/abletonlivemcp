"""The MCP tool surface: per-module snapshots, count and byte budgets, toolsets, selectors.

A surface change is deliberate. Regenerate only your own modules' snapshots with
``ABLETONLIVEMCP_UPDATE_SURFACE=clips,notes pytest tests/test_tool_surface.py`` (other modules'
files are never touched), or every snapshot at once with ``ABLETONLIVEMCP_UPDATE_SURFACE=all``
(the integrator's single global refresh after merges; it also deletes snapshots of modules that
no longer register tools). Review the diff either way.
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

from abletonlivemcp import proof_contract, server
from abletonlivemcp.models import ClipAddr, DevicePath, ParamSel, TrackSel

SNAPSHOTS = Path(__file__).parent / "tool_surface"
PRESETS = [server.READ, server.CREATE, server.OVERWRITE, server.CONTROL, server.DESTRUCTIVE]
UPDATE_ENV = "ABLETONLIVEMCP_UPDATE_SURFACE"


def _listing(enabled) -> list[dict]:
    surface = MCPServer("surface")
    server.install(surface, frozenset(enabled))
    tools = asyncio.run(surface.list_tools())
    return [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools]


def _update_snapshots(by_module: dict[str, list], request: str) -> None:
    """``all``/``1``: rewrite every snapshot and delete stale ones. A comma list: rewrite (or, with
    no tools left, delete) only the named modules' files. Empty: write nothing."""
    names = {n.strip() for n in request.split(",") if n.strip()}
    if not names:
        return
    SNAPSHOTS.mkdir(exist_ok=True)
    if names & {"all", "1"}:
        for old in SNAPSHOTS.glob("*.json"):
            if old.stem not in by_module:
                old.unlink()
        names = set(by_module)
    for module in sorted(names):
        path = SNAPSHOTS / f"{module}.json"
        tools = by_module.get(module)
        if not tools:
            path.unlink(missing_ok=True)
            continue
        text = json.dumps(sorted(tools, key=lambda t: t["name"]), indent=1, sort_keys=True)
        path.write_text(text + "\n", encoding="utf-8")


def test_tool_surface_snapshots_per_module():
    by_module: dict[str, list] = {}
    for tool in _listing(server.TOOLSETS):
        spec = server.SPECS[tool["name"]]
        assert tool["title"] and spec.annotations in PRESETS, tool["name"]
        assert "outputSchema" in tool, tool["name"]
        by_module.setdefault(spec.module.rsplit(".", 1)[-1], []).append(tool)
    _update_snapshots(by_module, os.environ.get(UPDATE_ENV, ""))
    stored = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in SNAPSHOTS.glob("*.json")}
    assert sorted(stored) == sorted(by_module), "a module gained or lost its tools"
    for module, tools in by_module.items():
        assert stored[module] == sorted(tools, key=lambda t: t["name"]), f"{module} surface changed"


def _utf8_size(listing) -> int:
    text = json.dumps(listing, separators=(",", ":"), ensure_ascii=False)
    return len(text.encode("utf-8"))


def test_core_listing_fits_the_utf8_byte_budget():
    size = _utf8_size(_listing({"core"}))
    limit = proof_contract.CORE_LISTING_BYTES
    assert size <= limit, f"core list_tools is {size} UTF-8 bytes (limit {limit})"


def test_tool_counts_stay_within_the_caps():
    core = [s for s in server.SPECS.values() if s.toolset == "core"]
    assert len(core) <= proof_contract.CORE_LIMIT, sorted(s.name for s in core)
    assert len(server.SPECS) <= proof_contract.ALL_LIMIT
    final = proof_contract.final_tools()
    assert sum(1 for m in final.values() if server.toolset_of(m) == "core") == 30
    assert len(final) == 57


def test_registered_tools_use_final_or_legacy_names_in_their_planned_module():
    final, legacy = proof_contract.final_tools(), proof_contract.legacy_tools()
    assert not set(final) & set(legacy)
    for name, spec in server.SPECS.items():
        module = spec.module.rsplit(".", 1)[-1]
        assert final.get(name, legacy.get(name)) == module, f"{name} is not planned in {module}"
    assert set(proof_contract.FINAL_SURFACE) == set(proof_contract.OWNER)
    assert {server.toolset_of(m) for m in proof_contract.FINAL_SURFACE} == set(server.TOOLSETS)


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
