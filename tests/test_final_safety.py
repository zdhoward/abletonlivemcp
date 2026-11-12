"""Host proof safety boundaries; no Live objects or bridge connections."""

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import live_final_cleanup as cleanup  # noqa: E402
import live_v2_final as proof  # noqa: E402


def test_unknown_tool_outcome_aborts_even_when_a_refusal_was_expected():
    async def tool(*args):
        raise proof.Refused("FrameTimeout", "exchange incomplete; may have been applied")

    run = proof.Run(SimpleNamespace(tool=tool), "test")
    with pytest.raises(proof.Abort, match="outcome unknown"):
        asyncio.run(proof.run_step(run, proof.Checks(), {"id": "boundary"}, 0,
                                   {"tool": "live_delete", "expect": "refused"}))


def test_simpler_rejection_requires_the_specific_error_message():
    async def tool(*args):
        raise proof.Refused("ValueError", "unrelated failure")

    run = proof.Run(SimpleNamespace(tool=tool), "test")
    checks = proof.Checks()
    with pytest.raises(proof.Stop):
        asyncio.run(proof.run_step(run, checks, {"id": "boundary"}, 0,
                                   {"tool": "live_get_simpler", "expect": "refused:ValueError",
                                    "expect_message": "not Simpler"}))
    assert checks.failures


def test_cleanup_discovery_failure_still_restores_safe_policy(monkeypatch, tmp_path):
    config = tmp_path / "bridge.json"
    config.write_text(json.dumps({"read_only": False, "dev_probes": True}), encoding="utf-8")
    monkeypatch.setattr(cleanup, "config_path", lambda: config)
    monkeypatch.setattr(sys, "argv", ["cleanup", "--apply"])

    def unavailable():
        raise RuntimeError("discovery unavailable")

    monkeypatch.setattr(cleanup, "BridgeClient", unavailable)
    with pytest.raises(RuntimeError, match="discovery unavailable"):
        cleanup.main()
    assert json.loads(config.read_text(encoding="utf-8")) == {"read_only": True}


def test_cleanup_success_restores_the_policy_it_found(monkeypatch, tmp_path):
    config = tmp_path / "bridge.json"
    original = b'{"read_only": false}'
    config.write_bytes(original)
    monkeypatch.setattr(cleanup, "config_path", lambda: config)
    monkeypatch.setattr(sys, "argv", ["cleanup", "--apply"])
    monkeypatch.setattr(cleanup, "BridgeClient", lambda: None)
    monkeypatch.setattr(cleanup, "cleanup", lambda client, apply, writable: writable())
    cleanup.main()
    assert config.read_bytes() == original


def test_reruns_merge_only_same_build_rows_and_never_touch_the_full_run(monkeypatch, tmp_path):
    """F7 (round 5): --only merged earlier rows from any build into the full-run evidence."""
    for name in ("EVIDENCE_MD", "EVIDENCE_JSON", "LEDGER_JSON", "RERUN_MD", "RERUN_JSON",
                 "RERUN_LEDGER"):
        monkeypatch.setattr(proof, name, tmp_path / name)
    monkeypatch.setattr(proof, "REPO", tmp_path)
    monkeypatch.setattr(proof, "log_modules", lambda: ("", []))
    case = {"id": "a", "phase": proof.PHASES[0], "steps": []}
    hashes = {"a": proof.case_hash(case), "b": proof.case_hash({**case, "id": "b"})}
    build = proof.build_identity({"script": {"version": "1.0.0", "build": "sha256:1"}}, "12.2")
    build["dirty"] = False

    def row(rid, **mark):
        return {"id": rid, "phase": case["phase"], "status": "pass", "checks": 1, "failures": [],
                "provenance": {**build, "case": hashes[rid], **mark}}

    fresh = [row("a")]
    assert proof._merge([row("b")], fresh, build, hashes) == [row("a"), row("b")]
    for other in ({"git": "0" * 40}, {"script_build": "sha256:2"}, {"case": "sha256:x"},
                  {"dirty": True}, {"env": {}}):
        assert proof._merge([row("b", **other)], fresh, build, hashes) == fresh
    assert proof._merge([row("b")], fresh, {**build, "dirty": True}, hashes) == fresh
    proof.write_evidence(fresh, [], {"build": build}, 0, "", subset=True)
    assert proof.RERUN_JSON.is_file() and not proof.EVIDENCE_JSON.exists()
    assert json.loads(proof.RERUN_JSON.read_text(encoding="utf-8"))["run"] == "subset"


def test_scratch_policy_restores_the_config_byte_for_byte(monkeypatch, tmp_path):
    config = tmp_path / "bridge.json"
    original = b'{"version": 1, "secret": "s", "read_only": false}\r\n'
    config.write_bytes(original)
    monkeypatch.setattr(proof, "config_path", lambda: config)
    with pytest.raises(RuntimeError), proof.scratch_policy(True):
        assert json.loads(config.read_text(encoding="utf-8"))["read_only"] is False
        raise RuntimeError("scenario crashed")
    assert config.read_bytes() == original
