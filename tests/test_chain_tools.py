import asyncio

import pytest

from abletonlivemcp import server
from abletonlivemcp.chain_presets import PRESETS, stock_equivalent


def test_tools_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"live_build_chain", "live_vocal_presets", "stock_equivalent_for_gear"} <= names


def test_presets_are_well_formed_stock_only():
    stock = {"EQ Eight", "Compressor", "Saturator", "Reverb", "Glue Compressor", "Echo"}
    for preset in PRESETS.values():
        assert 1 <= len(preset["stages"]) <= 12
        for stage in preset["stages"]:
            assert stage["device"] in stock and stage["params"]


def test_gear_lookup_known_and_unknown():
    assert stock_equivalent(" 1176 ")["device"] == "Compressor"
    assert stock_equivalent("1176")["approximate"] is True
    miss = stock_equivalent("Fairchild 670")
    assert miss["known"] is False and "1176" in miss["known_gear"]


def test_build_chain_tool_turns_chain_errors_into_value_errors(monkeypatch):
    monkeypatch.setattr(server._bridge, "call", lambda m, p=None: {"items": [{"name": "Reverb"}]})
    with pytest.raises(ValueError, match="not in Live"):
        server.live_build_chain(0, [{"device": "Pultec"}])
