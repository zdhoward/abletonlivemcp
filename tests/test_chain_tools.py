import asyncio

import pytest

from abletonlivemcp import server
from abletonlivemcp.chain_presets import PRESETS, stock_equivalent


def test_tools_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {
        "live_build_chain",
        "live_plan_chain",
        "live_build_role_chain",
        "live_vocal_presets",
        "stock_equivalent_for_gear",
    } <= names


def test_presets_are_well_formed_role_stages():
    for preset in PRESETS.values():
        assert 1 <= len(preset["stages"]) <= 12
        for stage in preset["stages"]:
            assert stage["role"] and stage["intent"] and "device" not in stage


def test_plan_tool_merges_file_and_call_preferences_and_reports_errors(monkeypatch, tmp_path):
    prefs = tmp_path / "prefs.json"
    prefs.write_text('{"compressor": ["Pro-C 2"]}', encoding="utf8")
    monkeypatch.setenv("ABLETONLIVEMCP_PREFS", str(prefs))
    seen = {}

    def fake_plan(call, stages, preferences):
        seen["prefs"] = preferences
        return {"stages": [], "report": []}

    monkeypatch.setattr(server, "plan_chain", fake_plan)
    server.live_plan_chain([{"role": "eq", "intent": {}}], {"Reverb": ["Pro-R"]})
    assert seen["prefs"] == {"compressor": ["Pro-C 2"], "reverb": ["Pro-R"]}
    monkeypatch.undo()
    monkeypatch.setenv("ABLETONLIVEMCP_PREFS", str(tmp_path / "none.json"))
    monkeypatch.setattr(server._bridge, "call", lambda m, p=None: {"items": []})
    with pytest.raises(ValueError, match="role"):
        server.live_plan_chain([{"role": "nonsense", "intent": {}}])


def test_gear_lookup_known_and_unknown():
    assert stock_equivalent(" 1176 ")["device"] == "Compressor"
    assert stock_equivalent("1176")["approximate"] is True
    miss = stock_equivalent("Fairchild 670")
    assert miss["known"] is False and "1176" in miss["known_gear"]


def test_build_chain_tool_turns_chain_errors_into_value_errors(monkeypatch):
    monkeypatch.setattr(server._bridge, "call", lambda m, p=None: {"items": [{"name": "Reverb"}]})
    with pytest.raises(ValueError, match="not in Live"):
        server.live_build_chain(0, [{"device": "Pultec"}])
