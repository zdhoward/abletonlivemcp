"""One local authorization boundary scenario, including the independent Live gate."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from abletonlivemcp import permissions, server
from abletonlivemcp.tools import files

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))
from AbletonLiveMCP import safety  # noqa: E402


def test_local_permissions_and_file_roots_fail_closed(monkeypatch, tmp_path, caplog):
    assert permissions.allowed_permissions({}) == safety.PERMISSIONS
    for value in (None, "edit", ["edit", "unknown"], [1], []):
        config = {"read_only": False, "permissions": value}
        monkeypatch.setattr(server, "load_config", lambda config=config: config)
        monkeypatch.setattr(safety, "_read_config", lambda config=config: config)
        assert not permissions.allowed_permissions(config)
        assert not safety.config_permissions()
        with pytest.raises(server.ToolFailure, match="permission_denied"):
            server._writable("live_set_tracks")
    config = {"read_only": False, "permissions": ["transport"]}
    monkeypatch.setattr(server, "load_config", lambda: config)
    server._writable("live_transport")
    gate = safety.Safety(lambda: object(), policy=lambda: False, permissions=lambda: {"transport"})
    with pytest.raises(safety.Refused) as denied:
        gate.authorize("delete_tracks", {})
    assert denied.value.code == "permission_denied"
    with pytest.raises(safety.Refused) as denied:
        gate.authorize("set_session", {})
    assert denied.value.code == "permission_denied"
    assert "permission_denied" in caplog.text
    monkeypatch.delenv("ABLETONLIVEMCP_FILE_ROOTS", raising=False)
    with pytest.raises(ValueError, match="explicit"):
        files.confined(str(tmp_path / "export.mid"))
    monkeypatch.setenv("ABLETONLIVEMCP_FILE_ROOTS", str(tmp_path))
    assert files.confined(str(tmp_path / "export.mid")) == tmp_path / "export.mid"
    with pytest.raises(ValueError, match="outside"):
        files.confined(str(tmp_path.parent / "outside.mid"))


def test_read_only_discovery_filters_writes_without_changing_tool_registry():
    code = (
        "import asyncio; from abletonlivemcp import server; "
        "tools=asyncio.run(server.mcp.list_tools()); "
        "assert tools and all(t.annotations.read_only_hint for t in tools); "
        "assert 'live_delete' in server.SPECS; print(len(tools))"
    )
    env = {**os.environ, "ABLETONLIVEMCP_READ_ONLY_TOOLS": "1", "ABLETONLIVEMCP_TOOLSETS": "all"}
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    assert int(result.stdout.strip()) > 0
