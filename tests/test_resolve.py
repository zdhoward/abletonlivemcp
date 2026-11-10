import json

import pytest

from abletonlivemcp.adapters import ADAPTERS, known_roles
from abletonlivemcp.chain import ChainError
from abletonlivemcp.chain_presets import PRESETS
from abletonlivemcp.preferences import load_preferences
from abletonlivemcp.resolve import plan_chain

STOCK = ("Compressor", "EQ Eight", "Saturator", "Reverb", "Limiter")
PRO_C = ["VST3", "FabFilter", "Pro-C 2"]
PRO_C_VST2 = ["VST", "Custom", "Pro-C 2"]
PRO_Q = ["VST3", "FabFilter", "Pro-Q 3"]
VERB = ["VST", "Valhalla", "ValhallaDSP x64", "ValhallaVintageVerb_x64"]
VERB_ROOT = ["VST", "Valhalla", "ValhallaDSP x64", "ValhallaVintageVerb"]


class FakeBrowser:
    def __init__(self, plugins=()):
        self.plugins = list(plugins)
        self.calls = []

    def call(self, method, params=None):
        self.calls.append(method)
        if method == "browser_list":
            return {"items": [{"name": n} for n in STOCK]}
        assert method == "browser_search" and params["root"] == "plugins"
        query = params["query"].lower()
        hits = [
            {"name": p[-1], "path": p, "is_loadable": True}
            for p in self.plugins
            if query in p[-1].lower()
        ]
        return {"results": hits}


def one(role, intent, prefs=None, plugins=()):
    b = FakeBrowser(plugins)
    plan = plan_chain(b.call, [{"role": role, "intent": intent}], prefs)
    return plan["stages"][0], plan["report"][0], b


def test_no_preferences_means_stock_everywhere():
    for preset in PRESETS.values():
        plan = plan_chain(FakeBrowser([PRO_C, PRO_Q]).call, preset["stages"], {})
        assert all("path" not in s for s in plan["stages"])
        assert [r["device"] for r in plan["report"]] == [
            "EQ Eight",
            "Compressor",
            "Saturator",
            "Reverb",
        ]


def test_preferred_installed_plugin_is_chosen_and_vst3_wins():
    stage, report, _ = one(
        "compressor",
        {"threshold": "-18 dB", "style": "Vocal"},
        {"compressor": ["Pro-C 2"]},
        plugins=[PRO_C_VST2, PRO_C],
    )
    assert stage["device"] == "Pro-C 2" and stage["root"] == "plugins" and stage["path"] == PRO_C
    assert stage["params"] == {"Threshold": "-18 dB", "Style": "Vocal"}
    assert report["notes"] == [] and report["skipped"] == []


def test_preferred_but_not_installed_falls_back_and_says_why():
    stage, report, _ = one("compressor", {"ratio": 4}, {"compressor": ["Pro-C 2"]})
    assert stage["device"] == "Compressor" and "path" not in stage
    assert report["skipped"] == ["Pro-C 2: not installed"]


def test_opaque_plugin_is_skipped_with_an_explanation():
    stage, report, _ = one("eq", {"high_pass": "80 Hz"}, {"eq": ["Pro-Q 3"]}, plugins=[PRO_Q])
    assert stage["device"] == "EQ Eight"
    assert "not controllable" in report["skipped"][0] and "Pro-Q 3" in report["skipped"][0]


def test_preferred_device_without_an_adapter_is_reported_not_ignored():
    _, report, _ = one("compressor", {"ratio": 4}, {"compressor": ["Some Unknown Comp"]})
    assert report["skipped"] == ["no adapter yet for preferred 'Some Unknown Comp'"]


def test_preference_order_is_respected_and_role_names_are_case_insensitive():
    stage, _, _ = one(
        "reverb",
        {"mix": "10 %"},
        {"Reverb": ["Pro-R", "ValhallaVintageVerb"]},
        plugins=[VERB_ROOT, PRO_Q],
    )
    # Pro-R is not installed, so the second preference wins
    assert stage["device"] == "ValhallaVintageVerb"


def test_plugin_names_match_the_way_live_actually_lists_them():
    # real browser names seen in Live 12.2: 'ValhallaVintageVerb_x64', and v1 next to v2
    stage, _, _ = one(
        "reverb", {"mix": "10 %"}, {"reverb": ["ValhallaVintageVerb"]}, plugins=[VERB]
    )
    assert stage["path"] == VERB
    old = ["VST3", "FabFilter", "FabFilter Pro-C"]
    stage, _, _ = one("compressor", {}, {"compressor": ["Pro-C 2"]}, plugins=[old, PRO_C])
    assert stage["path"] == PRO_C  # not the older Pro-C
    _, report, _ = one("compressor", {}, {"compressor": ["Pro-C 2"]}, plugins=[old])
    assert report["skipped"] == ["Pro-C 2: not installed"]


def test_unitless_plugin_gets_raw_values_and_every_guess_is_flagged():
    stage, report, _ = one(
        "reverb",
        {"predelay": "20 ms", "decay": {"value": "1.2 s", "level": "short"}, "mix": "12 %"},
        {"reverb": ["ValhallaVintageVerb"]},
        plugins=[VERB_ROOT],
    )
    assert stage["params"] == {"Mix": {"raw": 0.12}, "Decay": {"raw": 0.3}}
    text = " ".join(report["notes"])
    assert "predelay" in text and "no mapping" in text  # not silently dropped
    assert "guess, not calibrated" in text


def test_a_value_the_device_cannot_use_is_skipped_with_a_reason():
    # VintageVerb's decay needs a level; a bare physical value has nothing to map to
    stage, report, _ = one(
        "reverb",
        {"decay": "1.2 s", "mix": "10 %"},
        {"reverb": ["ValhallaVintageVerb"]},
        plugins=[VERB_ROOT],
    )
    assert "Decay" not in stage["params"]
    assert any("needs a level" in n for n in report["notes"])
    _, report2, _ = one(
        "reverb", {"mix": 0.1}, {"reverb": ["ValhallaVintageVerb"]}, plugins=[VERB_ROOT]
    )
    assert any("needs a percentage" in n for n in report2["notes"])


def test_eq_setup_parameters_come_along_with_the_intent_that_needs_them():
    stage, _, _ = one("eq", {"high_pass": "80 Hz", "cut_gain": "-2 dB"})
    assert stage["params"]["1 Filter Type A"] == "High Pass 12dB"
    assert stage["params"]["1 Frequency A"] == "80 Hz" and stage["params"]["2 Gain A"] == "-2 dB"
    only_cut, _, _ = one("eq", {"cut_gain": "-2 dB"})
    assert "1 Filter Type A" not in only_cut["params"]


def test_unsupported_intent_key_is_noted_for_stock_too():
    _, report, _ = one("compressor", {"style": "Vocal", "ratio": 4})
    assert any("no mapping for 'style'" in n for n in report["notes"])


def test_each_plugin_is_searched_once_per_plan():
    b = FakeBrowser([PRO_C])
    stages = [{"role": "compressor", "intent": {"ratio": 4}}] * 3
    plan_chain(b.call, stages, {"compressor": ["Pro-C 2"]})
    assert b.calls.count("browser_search") == 1


@pytest.mark.parametrize(
    "stages",
    [
        [],
        "x",
        [{"role": "nonsense", "intent": {}}],
        [{"role": "eq", "intent": 3}],
        [3],
    ],
)
def test_bad_stages_are_refused(stages):
    with pytest.raises(ChainError):
        plan_chain(FakeBrowser().call, stages, {})


def test_adapter_data_is_consistent():
    names = [(a.role, a.device) for a in ADAPTERS]
    assert len(names) == len(set(names))
    for a in ADAPTERS:
        assert a.access in {"full", "partial", "opaque"}
        assert (a.access == "opaque") == (not a.params)  # opaque devices map nothing
        for key in a.setup:
            assert key in a.params
        for spec in a.params.values():
            assert spec.get("mode", "display") in {"display", "percent_raw", "levels"}
            assert ("levels" in spec) == (spec.get("mode") == "levels")
    # every role has a stock device to fall back on
    assert all(
        any(a.root == "audio_effects" for a in ADAPTERS if a.role == r) for r in known_roles()
    )


def test_presets_only_use_known_roles():
    for preset in PRESETS.values():
        assert {s["role"] for s in preset["stages"]} <= set(known_roles())


def test_preferences_file_roundtrip_and_errors(tmp_path):
    f = tmp_path / "p.json"
    assert load_preferences(f) == {}  # missing file: no preferences
    f.write_text(json.dumps({"Compressor": ["Pro-C 2"]}), encoding="utf8")
    assert load_preferences(f) == {"compressor": ["Pro-C 2"]}
    for bad in ["{", "[]", '{"compressor": "Pro-C 2"}', '{"compressor": [3]}']:
        f.write_text(bad, encoding="utf8")
        with pytest.raises(ValueError, match="preferences|look like"):
            load_preferences(f)
