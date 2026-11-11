"""Verdict rules of probes P-13 .. P-17 (pure logic; no Live needed)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "remote_script"))

from AbletonLiveMCP import probe_p13, probe_p14, probe_p15, probe_p16, probe_p17  # noqa: E402


def test_p13_verdict():
    names = probe_p13.FUNCTIONS
    present = dict.fromkeys(names, True)
    assert probe_p13.verdict_for(True, present, dict.fromkeys(names, True)) == "go"
    assert probe_p13.verdict_for(True, present, {}) == "no-go"
    assert probe_p13.verdict_for(True, {**present, names[0]: False}, {}) == "gated"
    assert probe_p13.verdict_for(False, {}, {}) == "gated"


def test_p14_verdict():
    assert probe_p14.verdict_for(True, True, True) == "go"
    assert probe_p14.verdict_for(True, True, False) == "no-go"
    assert probe_p14.verdict_for(False, True, True) == "gated"


def test_p15_verdict():
    ok = {"counts_ok": True}
    assert probe_p15.verdict_for(True, [ok, ok]) == "go"
    assert probe_p15.verdict_for(True, [ok, {"counts_ok": False}]) == "no-go"
    assert probe_p15.verdict_for(False, [ok, ok]) == "gated"


def test_p16_verdict():
    assert probe_p16.verdict_for(True, True, True, True) == "go"
    assert probe_p16.verdict_for(True, False, True, True) == "no-go"
    assert probe_p16.verdict_for(False, True, True, True) == "gated"


def test_p17_verdict():
    assert probe_p17.verdict_for(True, 6, 0) == "go"
    assert probe_p17.verdict_for(True, 6, 1) == "no-go"
    assert probe_p17.verdict_for(True, 0, 0) == "no-go"
    assert probe_p17.verdict_for(False, 6, 0) == "gated"
