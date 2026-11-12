"""The distribution checker refuses developer payloads in a wheel (R2: probes once shipped)."""

import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_distribution  # noqa: E402


@pytest.mark.parametrize(
    "leak",
    [
        "abletonlivemcp/_remote_script/AbletonLiveMCP/probe_p01.py",
        "abletonlivemcp/_remote_script/AbletonLiveMCP/__pycache__/core.cpython-313.pyc",
        "abletonlivemcp/tests/test_x.py",
        "abletonlivemcp/knowledge/notes.py",
    ],
)
def test_a_developer_payload_in_the_wheel_fails_the_check(tmp_path, leak):
    with zipfile.ZipFile(tmp_path / "abletonlivemcp-0-py3-none-any.whl", "w") as wheel:
        wheel.writestr("abletonlivemcp/NOTICE", "n")
        wheel.writestr(leak, "x")
    with tarfile.open(tmp_path / "abletonlivemcp-0.tar.gz", "w:gz"):
        pass
    with pytest.raises(ValueError, match="Developer probe|Development payload"):
        check_distribution.check_archives(tmp_path)
