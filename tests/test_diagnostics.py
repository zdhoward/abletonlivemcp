"""Batch-write failures reach the client as stable text and Live's log as code locations only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))
from AbletonLiveMCP import core  # noqa: E402
from AbletonLiveMCP.dom_common import run_writes  # noqa: E402


def test_unexpected_write_errors_are_sanitized_and_logged_once(monkeypatch):
    logged = []
    monkeypatch.setattr(core, "_failure_sink", logged.append)

    def write(entry):
        if entry == "native":
            raise RuntimeError("D:/Music/someone/Secret Project.als is locked")
        if entry == "native_value":  # a ValueError this code did not write is not a refusal
            raise ValueError("D:/Music/someone/Secret Project.als: bad value")
        raise core.Invalid("targets[1]: 'length' must be positive")

    out = run_writes(["native"], write)
    assert out["error"] == "RuntimeError: write_failed" and out["status"] == "partial"
    (line,) = logged
    assert "RuntimeError at test_diagnostics.py:" in line and "Secret" not in line
    refused = run_writes(["refusal"], write)  # a deliberate refusal stays readable, unlogged
    assert refused["error"] == "targets[1]: 'length' must be positive" and len(logged) == 1
    native = run_writes(["native_value"], write)
    assert native["error"] == "ValueError: write_failed" and len(logged) == 2
    assert "Secret" not in logged[1]
