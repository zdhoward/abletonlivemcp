"""The user's preferred devices per role, read from a small JSON file.

~/.abletonlivemcp/preferences.json (override the location with ABLETONLIVEMCP_PREFS):

    {"compressor": ["Pro-C 2"], "reverb": ["ValhallaVintageVerb"], "eq": ["Pro-Q 3"]}

Names are tried in order; a device the user does not have, or that Live cannot configure, is
skipped and the next one (finally the stock device) is used.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .errors import Invalid


def preferences_path() -> Path:
    override = os.environ.get("ABLETONLIVEMCP_PREFS")
    return Path(override) if override else Path.home() / ".abletonlivemcp" / "preferences.json"


def load_preferences(path: Path | None = None) -> dict[str, list[str]]:
    """Role -> ordered device names. A missing file means no preferences; a bad one is an error."""
    path = path or preferences_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf8"))
    except (OSError, ValueError) as exc:  # the reason (type only) goes to stderr, not the reply
        logging.getLogger("abletonlivemcp").warning(
            "preferences file unreadable: %s", type(exc).__name__
        )
        raise Invalid(
            f"cannot read preferences file {path}: not a readable UTF-8 JSON file"
        ) from exc
    ok = isinstance(data, dict) and all(
        isinstance(v, list) and all(isinstance(n, str) for n in v) for v in data.values()
    )
    if not ok:
        raise Invalid(f'{path} must look like {{"compressor": ["Pro-C 2"]}}')
    return {str(k).lower(): v for k, v in data.items()}
