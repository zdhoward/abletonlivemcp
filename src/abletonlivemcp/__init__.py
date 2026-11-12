"""AbletonLiveMCP: LLM-assisted workflows for Ableton Live."""

import re as _re
from pathlib import Path as _Path


def _read_version() -> str:
    """VERSION from the Remote Script's version.py, the single version source (pyproject reads
    it too): packaged in a wheel, or the source tree in an editable install."""
    here = _Path(__file__).absolute().parent
    for path in (
        here / "_remote_script" / "AbletonLiveMCP" / "version.py",
        here.parents[1] / "remote_script" / "AbletonLiveMCP" / "version.py",
    ):
        if path.is_file():
            found = _re.search(r'^VERSION = "([^"]+)"', path.read_text(encoding="utf-8"), _re.M)
            if found:
                return found[1]
    return "0+unknown"


__version__ = _read_version()
