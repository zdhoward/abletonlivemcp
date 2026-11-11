"""Verdict logic of the P-18/19/20/22/23 probes (pure rules; no Live needed)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "remote_script"))

from AbletonLiveMCP import probe_p18, probe_p19, probe_p20, probe_p22, probe_p23  # noqa: E402


def test_p18_verdict():
    ok = {"tried": True, "ok": True}
    full = {"record_mode": ok, "arrangement_overdub": ok, "session_record": ok}
    assert probe_p18.verdict_for(full, ["a"]) == "go"
    skipped = dict(full, session_record={"tried": False, "ok": False})
    assert probe_p18.verdict_for(skipped, ["a"]) == "go-with-limits"
    assert probe_p18.verdict_for(dict(full, record_mode={"tried": True, "ok": False}), ["a"]) == (
        "no-go"
    )
    assert probe_p18.verdict_for({}, []) == "gated"


def test_p19_verdict():
    good = {n: {"ok": True} for n in ("create_midi_clip", "trim_markers", "delete_clip")}
    good["duplicate_to_arrangement"] = {"ok": True}
    assert probe_p19.verdict_for(good) == "go"
    assert probe_p19.verdict_for(dict(good, delete_clip={"ok": False})) == "go-with-limits"
    assert probe_p19.verdict_for({"create_midi_clip": {"ok": False}}) == "no-go"
    assert probe_p19.verdict_for({}, create_present=False) == "gated"


def test_p20_verdict_and_field_probe():
    ok, bad, absent = {"ok": True}, {"ok": False, "reason": "x"}, {"ok": False, "reason": "absent"}
    assert probe_p20.verdict_for([ok, ok, absent]) == "go"
    assert probe_p20.verdict_for([ok, bad]) == "go-with-limits"
    assert probe_p20.verdict_for([bad]) == "no-go"
    assert probe_p20.verdict_for([ok], usable=False) == "gated"

    class Sample:
        gain = 0.5

    rec = probe_p20.probe_field(Sample(), "gain")
    assert rec["ok"] and rec["restored"] is True


def test_p22_verdict():
    ok = {"ok": True, "before": 1}
    why = {"ok": False, "before": 1, "reason": "read-only"}
    assert probe_p22.verdict_for([ok, why]) == "go"
    assert probe_p22.verdict_for([{"ok": False, "before": 1}]) == "no-go"
    assert probe_p22.verdict_for([{"ok": False, "reason": "absent"}]) == "gated"


def test_p23_verdict():
    assert probe_p23.verdict_for(True, ["Browser", "Arranger"]) == "go"
    assert probe_p23.verdict_for(True, []) == "no-go"
    assert probe_p23.verdict_for(False, []) == "gated"
