import asyncio
from types import SimpleNamespace

import pytest

from abletonlivemcp import judge
from abletonlivemcp.judge import JudgeError, get_judge, verdict
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


def test_auto_falls_back_to_rules_without_a_key(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("ABLETONLIVEMCP_JUDGE", raising=False)
    assert get_judge().name == "rules"


def test_env_can_force_rules_even_with_a_key(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "not-a-real-key")
    monkeypatch.setenv("ABLETONLIVEMCP_JUDGE", "rules")
    assert get_judge().name == "rules"


def test_bad_judge_name_is_rejected():
    with pytest.raises(ValueError):
        get_judge("gpt")


# ---- Jev adapter, with an injected fake client (no network) ---------------------------


class FakeClient:
    def __init__(self, nouls, choices):
        self._r = SimpleNamespace(
            nouls={k: SimpleNamespace(noul=v) for k, v in nouls.items()},
            choices={k: SimpleNamespace(choice=v) for k, v in choices.items()},
        )
        self.calls = []

    def system_one(self, state, questions):
        self.calls.append((state, questions))
        return self._r


def test_jev_sample_sends_only_name_and_two_folders_and_applies_truth_table():
    pytest.importorskip("typesafe_sdk")
    from abletonlivemcp.judge.jev import JevJudge

    fake = FakeClient({"one_shot": 0.95, "is_drum": 0.9}, {"drum_type": "kick"})
    j = JevJudge(client=fake).classify_sample("k1.wav", ["a", "b", "Drums", "Kicks"])
    assert (j.one_shot, j.drum_type, j.source) == ("yes", "kick", "jev")
    state, questions = fake.calls[0]
    assert state == {"sample": {"file_name": "k1.wav", "folders": ["Drums", "Kicks"]}}
    assert set(questions) == {"one_shot", "is_drum", "drum_type"}


def test_jev_ignores_choice_when_not_a_drum_and_reports_unsure():
    pytest.importorskip("typesafe_sdk")
    from abletonlivemcp.judge.jev import JevJudge

    fake = FakeClient({"one_shot": 0.5, "is_drum": 0.1}, {"drum_type": "kick"})
    j = JevJudge(client=fake).classify_sample("pad.wav", [])
    assert j.drum_type is None and j.one_shot == "unsure"


def test_jev_plugin_category_only_when_it_fits():
    pytest.importorskip("typesafe_sdk")
    from abletonlivemcp.judge.jev import JevJudge

    fits = JevJudge(client=FakeClient({"fits": 0.9}, {"category": "reverb"}))
    assert fits.classify_plugin("Hall X", "vst3").category == "reverb"
    nofit = JevJudge(client=FakeClient({"fits": 0.2}, {"category": "reverb"}))
    assert nofit.classify_plugin("???", None).category is None


def test_jev_failure_is_an_error_not_a_no():
    sdk = pytest.importorskip("typesafe_sdk")
    from abletonlivemcp.judge.jev import JevJudge

    class Boom:
        def system_one(self, state, questions):
            raise sdk.TypeSafeError("down")

    with pytest.raises(JudgeError):
        JevJudge(client=Boom()).classify_plugin("x", None)


def test_judge_tools_registered_and_status_reports_backend(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("ABLETONLIVEMCP_JUDGE", raising=False)
    from abletonlivemcp import server

    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"judge_status", "classify_samples", "classify_plugins"} <= names
    assert server.judge_status()["backend"] == "rules"
    out = server.classify_samples(["S:/x/Drums/Kicks/Kick_01.wav"])
    assert out[0]["drum_type"] == "kick"
    with pytest.raises(ValueError):
        server.classify_samples(["a.wav"] * 201)
    assert judge.PLUGIN_CATEGORIES
