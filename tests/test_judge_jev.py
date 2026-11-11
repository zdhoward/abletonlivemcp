import io
import json
import urllib.error

import pytest

from abletonlivemcp.judge import JudgeError, get_judge
from abletonlivemcp.judge import jev as jev_mod
from abletonlivemcp.judge.jev import JevJudge, OpenRouterTransport


class FakeTransport:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def ask(self, state, questions):
        self.calls.append((state, questions))
        return self.answers


def test_sample_payload_is_minimal_and_truth_table_applies():
    t = FakeTransport(
        {"one_shot": {"noul": 0.95}, "is_drum": {"noul": 0.9}, "drum_type": {"choice": "kick"}}
    )
    j = JevJudge(t).classify_sample("k1.wav", ["a", "b", "Drums", "Kicks"])
    assert (j.one_shot, j.drum_type, j.source) == ("yes", "kick", "jev")
    state, questions = t.calls[0]
    assert state == {"sample": {"file_name": "k1.wav", "folders": ["Drums", "Kicks"]}}
    assert set(questions) == {"one_shot", "is_drum", "drum_type"}
    assert questions["drum_type"]["criteria"]["kick"] is None


def test_choice_ignored_when_not_a_drum_and_unsure_band():
    t = FakeTransport(
        {"one_shot": {"noul": 0.5}, "is_drum": {"noul": 0.1}, "drum_type": {"choice": "kick"}}
    )
    j = JevJudge(t).classify_sample("pad.wav", [])
    assert j.drum_type is None and j.one_shot == "unsure"


def test_plugin_category_only_when_it_fits():
    yes = JevJudge(FakeTransport({"fits": {"noul": 0.9}, "category": {"choice": "reverb"}}))
    assert yes.classify_plugin("Hall X", "vst3").category == "reverb"
    no = JevJudge(FakeTransport({"fits": {"noul": 0.2}, "category": {"choice": "reverb"}}))
    assert no.classify_plugin("???", None).category is None


def test_unexpected_answer_shape_is_an_error():
    with pytest.raises(JudgeError):
        JevJudge(FakeTransport({"fits": {"noul": 0.9}})).classify_plugin("x", None)


def _patch_urlopen(monkeypatch, result):
    def fake(req, timeout=None):
        if isinstance(result, Exception):
            raise result
        return io.BytesIO(json.dumps(result).encode())

    monkeypatch.setattr(jev_mod.urllib.request, "urlopen", fake)


def test_openrouter_transport_returns_answers_and_sends_bearer(monkeypatch):
    seen = {}

    def fake(req, timeout=None):
        seen["auth"] = req.get_header("Authorization")
        seen["body"] = json.loads(req.data)
        return io.BytesIO(json.dumps({"answers": {"q": {"noul": 0.8}}}).encode())

    monkeypatch.setattr(jev_mod.urllib.request, "urlopen", fake)
    out = OpenRouterTransport(api_key="k").ask({"s": 1}, {"q": {"type": "noul"}})
    assert out == {"q": {"noul": 0.8}}
    assert seen["auth"] == "Bearer k"
    assert seen["body"]["model"] == "typesafe/jev-1.14" and seen["body"]["state"] == {"s": 1}


@pytest.mark.parametrize(
    "failure",
    [
        urllib.error.HTTPError("u", 429, "rate", {}, None),
        urllib.error.URLError("offline"),
        TimeoutError(),
    ],
)
def test_transport_failures_are_judge_errors_without_leaking_the_key(monkeypatch, failure):
    _patch_urlopen(monkeypatch, failure)
    with pytest.raises(JudgeError) as exc:
        OpenRouterTransport(api_key="sk-secret").ask({}, {})
    assert "sk-secret" not in str(exc.value)


def test_malformed_response_is_a_judge_error(monkeypatch):
    _patch_urlopen(monkeypatch, {"no_answers": 1})
    with pytest.raises(JudgeError):
        OpenRouterTransport(api_key="k").ask({}, {})


def test_missing_openrouter_key_is_a_judge_error(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(JudgeError):
        OpenRouterTransport()


def test_selection_by_environment(monkeypatch):
    monkeypatch.delenv("ABLETONLIVEMCP_JUDGE", raising=False)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert get_judge().name == "rules"
    with pytest.raises(JudgeError):
        get_judge("jev")
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    assert get_judge().name == "rules"  # a key never silently selects a network judge
    assert get_judge("rules").name == "rules"
