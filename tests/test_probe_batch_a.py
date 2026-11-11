"""Verdict rules of probes P-02, P-04, P-05, P-06 and P-07 (pure logic, no Live needed)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "remote_script"))

from AbletonLiveMCP import probe_p02, probe_p04, probe_p05, probe_p06, probe_p07  # noqa: E402


def test_p02_verdict_and_payload():
    assert len(probe_p02.reopen_payload()) == 4096
    assert probe_p02.verdict_for(False, True, True) == "gated"
    assert probe_p02.verdict_for(True, True, True) == "go"
    assert probe_p02.verdict_for(True, True, False) == "no-go"


def test_p04_verdict():
    v = probe_p04.verdict_for
    assert v(False, True, True, True, "x") == "gated"
    assert v(True, True, True, True, "RuntimeError: bad type") == "go"
    assert v(True, True, True, False, "RuntimeError: bad type") == "no-go"
    assert v(True, True, True, True, None) == "no-go"


def test_p05_verdict():
    v = probe_p05.verdict_for
    assert v(["Song.x"], [], []) == "gated"
    assert v([], [], []) == "go"
    assert v([], ["Track.delete_device"], []) == "no-go"
    assert v([], [], ["delete_track"]) == "no-go"


def test_p06_verdict_and_parse():
    p = probe_p06
    assert p.parse_db("-6.0 dB") == -6.0
    assert p.parse_db("-inf dB") == float("-inf")
    assert p.parse_db(None) is None
    assert p.verdict_for(False, None, None, None) == "gated"
    assert p.verdict_for(True, -6.01, 6.0, float("-inf")) == "go"
    assert p.verdict_for(True, -5.0, 6.0, float("-inf")) == "no-go"
    assert p.verdict_for(True, -6.0, 6.0, -70.0) == "no-go"


def test_p07_verdict():
    v = probe_p07.verdict_for
    assert v(["MidiNoteSpecification"], {}, True) == "gated"
    assert v([], {}, True) == "go"
    assert v([], {"quantize": "RuntimeError: x"}, True) == "no-go"
    assert v([], {}, False) == "no-go"
