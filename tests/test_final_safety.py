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
