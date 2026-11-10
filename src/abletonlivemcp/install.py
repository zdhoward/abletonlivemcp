"""Copy the Remote Script into a Live User Library. Usage: python -m abletonlivemcp.install <lib>"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

SCRIPT = "AbletonLiveMCP"


def source_dir() -> Path:
    # repo layout: <root>/remote_script/AbletonLiveMCP ; this file is <root>/src/abletonlivemcp/
    return Path(__file__).resolve().parents[2] / "remote_script" / SCRIPT


def install(user_library: Path) -> Path:
    if not (user_library / "Presets").is_dir():
        raise SystemExit(f"{user_library} does not look like an Ableton User Library")
    dest = user_library / "Remote Scripts" / SCRIPT
    if dest.exists():
        shutil.rmtree(dest)  # only ever our own folder, by fixed name
    shutil.copytree(source_dir(), dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dest


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("usage: python -m abletonlivemcp.install <path to User Library>")
    print(f"installed to {install(Path(args[0]))}")


if __name__ == "__main__":
    main()
