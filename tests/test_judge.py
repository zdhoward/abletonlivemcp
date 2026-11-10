import asyncio

import pytest

from abletonlivemcp import judge
from abletonlivemcp.judge import get_judge, verdict
from abletonlivemcp.judge.rules import RuleJudge


def test_verdict_thresholds_have_an_unsure_band():
    assert verdict(0.95) == "yes" and verdict(0.7) == "yes"
    assert verdict(0.05) == "no" and verdict(0.3) == "no"
    assert verdict(0.5) == "unsure"


@pytest.mark.parametrize(
    "name,one_shot,drum",
    [
        ("Kick_Heavy_01.wav", "yes", "kick"),
        ("SNR 03.wav", "yes", "snare"),
        ("OpenHat_12.wav", "yes", "hat_open"),
        ("808 Closed Hat.wav", "yes", "hat_closed"),
        ("Break 90bpm.wav", "no", None),
        ("Drum Loop 120 BPM.wav", "no", None),
        ("random_texture.wav", "unsure", None),
    ],
)
def test_rule_sample_judgments(name, one_shot, drum):
    j = RuleJudge().classify_sample(name, [])
    assert (j.one_shot, j.drum_type, j.source) == (one_shot, drum, "rules")


@pytest.mark.parametrize(
    "name,category",
    [
        ("FabFilter Pro-Q 3", "eq"),
        ("Compressor", "compressor"),
        ("ValhallaVintageVerb", "reverb"),
        ("Nexus", "synth"),
        ("Sequencer Thing", None),
        ("Mystery Box", None),
    ],
)
def test_rule_plugin_judgments(name, category):
    assert RuleJudge().classify_plugin(name, "vst3").category == category


@pytest.fixture
def no_keys(monkeypatch):
    for var in ("TYPESAFE_API_KEY", "OPENROUTER_API_KEY", "ABLETONLIVEMCP_JUDGE"):
        monkeypatch.delenv(var, raising=False)


def test_auto_falls_back_to_rules_without_a_key(no_keys):
    assert get_judge().name == "rules"


def test_env_can_force_rules_even_with_a_key(no_keys, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "not-a-real-key")
    monkeypatch.setenv("ABLETONLIVEMCP_JUDGE", "rules")
    assert get_judge().name == "rules"


def test_bad_judge_name_is_rejected():
    with pytest.raises(ValueError):
        get_judge("gpt")


def test_judge_tools_registered_and_status_reports_backend(no_keys):
    from abletonlivemcp import server

    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"judge_status", "classify_samples", "classify_plugins"} <= names
    assert server.judge_status()["backend"] == "rules"
    out = server.classify_samples(["S:/x/Drums/Kicks/Kick_01.wav"])
    assert out[0]["drum_type"] == "kick"
    with pytest.raises(ValueError):
        server.classify_samples(["a.wav"] * 201)
    assert judge.PLUGIN_CATEGORIES
