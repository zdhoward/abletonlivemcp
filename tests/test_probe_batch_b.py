"""Verdict logic of probes P-08..P-12 (pure functions and gated paths; no Live needed)."""

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "remote_script"))

from AbletonLiveMCP import (  # noqa: E402
    dom_probe,
    probe_p08,
    probe_p09,
    probe_p10,
    probe_p11,
    probe_p12,
)


def test_p08_verdict_rule():
    v = probe_p08.verdict_for
    assert v(True, True, True) == "go"
    assert v(True, False, True) == "go-with-limits"
    assert v(False, True, True) == "no-go"


def test_p09_verdict_rule():
    v = probe_p09.verdict_for
    assert v(True, True, True) == "go"
    assert v(True, True, False) == "go-with-limits"
    assert v(False, True, True) == "no-go"


def test_p10_verdict_rule():
    v = probe_p10.verdict_for
    assert v(True, 0.02) == "go"
    assert v(True, 0.05) == "go-with-limits"
    assert v(True, None) == "go-with-limits"
    assert v(False, 0.0) == "no-go"


def test_p11_pending_without_rack_and_rule():
    assert probe_p11.verdict_for(False, []) == "pending"
    assert probe_p11.verdict_for(True, [True, True]) == "go"
    assert probe_p11.verdict_for(True, [True, False]) == "go-with-limits"


def test_p12_gated_when_kit_cannot_load():
    class Song:
        tracks = []

        def create_midi_track(self, _i):
            self.tracks.append(object())

    song = Song()
    ctx = types.SimpleNamespace(
        song=song,
        app=types.SimpleNamespace(
            browser=types.SimpleNamespace(drums=types.SimpleNamespace(children=[]))
        ),
    )
    result = probe_p12.run(ctx, dom_probe.Scratch(song))
    assert result["verdict"] == "gated"
    assert probe_p12.verdict_for(False, []) == "pending"
    assert probe_p12.verdict_for(True, [True]) == "go"
