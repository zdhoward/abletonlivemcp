"""Install packaged Remote Script resources without deleting a working installation."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
import uuid
from importlib import resources
from pathlib import Path

from .config import ConfigError, checked_path, config_path, ensure_config

SCRIPT = "AbletonLiveMCP"
MANIFEST = ".abletonlivemcp-install.json"


class InstallError(ValueError):
    """An installation cannot be safely replaced."""


def source_files() -> dict:
    """Use wheel resources, with the canonical tree for editable development only."""
    root = resources.files("abletonlivemcp").joinpath("_remote_script", SCRIPT)
    if root.is_dir():
        return {
            **{entry.name: entry for entry in root.iterdir() if entry.is_file()},
            "config.py": resources.files("abletonlivemcp").joinpath("config.py"),
        }
    root = checked_path(Path(__file__).absolute().parents[2] / "remote_script" / SCRIPT)
    if not root.is_dir():
        raise InstallError("Remote Script resources are missing; reinstall the host package")
    return {
        **{entry.name: entry for entry in root.glob("*.py")},
        "config.py": Path(__file__).with_name("config.py"),
    }


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _snapshot(directory: Path) -> dict[str, str]:
    checked_path(directory)
    if not directory.is_dir():
        raise InstallError(f"Installation is not a directory: {directory}")
    result = {}
    for entry in directory.iterdir():
        checked_path(entry)
        if entry.name == "__pycache__" and entry.is_dir():
            for cached in entry.iterdir():
                checked_path(cached)
                if not cached.is_file():
                    raise InstallError(f"Unmanaged cache directory; preserved: {cached}")
                result[f"__pycache__/{cached.name}"] = _digest(cached.read_bytes())
            continue
        if not entry.is_file():
            raise InstallError(f"Unmanaged directory in installation; preserved: {entry}")
        if entry.name != MANIFEST:
            result[entry.name] = _digest(entry.read_bytes())
    return result


def _owned_snapshot(directory: Path) -> dict[str, str]:
    actual = _snapshot(directory)
    try:
        manifest = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise InstallError(f"Unknown installation; preserved intact: {directory}") from None
    managed = {name: digest for name, digest in actual.items() if "/" not in name}
    if (
        not isinstance(manifest, dict) or manifest.get("format") != 1
        or manifest.get("script") != SCRIPT or manifest.get("files") != managed
    ):
        raise InstallError(f"Unmanaged or modified installation; preserved intact: {directory}")
    for name in actual.keys() - managed.keys():
        match = re.fullmatch(r"__pycache__/(\w+)\.cpython-\d+(?:\.opt-\d+)?\.pyc", name)
        if match is None or f"{match[1]}.py" not in managed:
            raise InstallError(f"Unmanaged cache file; installation preserved: {directory}")
    return actual


def _overlaps(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def install(user_library: Path) -> Path:
    library = checked_path(user_library)
    presets = checked_path(library / "Presets")
    if not presets.is_dir():
        raise InstallError(f"{library} does not look like an Ableton User Library (missing Presets)")
    parent = checked_path(library / "Remote Scripts")
    dest = checked_path(parent / SCRIPT)
    configuration = config_path()
    if _overlaps(dest, configuration):
        raise InstallError("Bridge configuration and script installation paths must not overlap")
    package_root = checked_path(Path(__file__).absolute().parents[1])
    if _overlaps(library, package_root) or _overlaps(configuration, package_root):
        raise InstallError("Library, configuration and package resources must not overlap")
    files = source_files()
    if not {"__init__.py", "core.py", "handlers.py", "config.py"} <= files.keys():
        raise InstallError("Remote Script resources are incomplete; reinstall the host package")
    expected = {}
    for name, resource in files.items():
        if Path(name).name != name or not name.endswith(".py"):
            raise InstallError("Unexpected Remote Script resource")
        if isinstance(resource, Path):
            source = checked_path(resource)
            if _overlaps(library, source.parent) or _overlaps(configuration, source):
                raise InstallError("Library, configuration and package resources must not overlap")
        expected[name] = _digest(resource.read_bytes())
    previous = _owned_snapshot(dest) if dest.exists() else None
    parent.mkdir(parents=True, exist_ok=True)
    checked_path(parent)
    stage = Path(tempfile.mkdtemp(prefix=f".{SCRIPT}.stage-", dir=parent))
    backup = parent / f".{SCRIPT}.backup-{uuid.uuid4().hex}"
    try:
        for name, resource in files.items():
            with resource.open("rb") as source, (stage / name).open("xb") as target:
                shutil.copyfileobj(source, target)
        (stage / MANIFEST).write_text(
            json.dumps({"format": 1, "script": SCRIPT, "files": expected}, sort_keys=True),
            encoding="utf-8",
        )
        if _owned_snapshot(stage) != expected:
            raise InstallError("Staged script validation failed; previous installation preserved")
        ensure_config()
        checked_path(dest)
        if previous is not None:
            if _owned_snapshot(dest) != previous:
                raise InstallError("Installation changed during staging; preserved intact")
            dest.rename(backup)
        elif dest.exists():
            raise InstallError("Installation appeared during staging; preserved intact")
        try:
            stage.rename(dest)
        except OSError as exc:
            if previous is not None:
                try:
                    backup.rename(dest)
                except OSError:
                    raise InstallError(
                        f"Replacement and rollback failed. Previous installation remains at {backup}; "
                        "close Live before restoring that folder"
                    ) from exc
            raise InstallError(
                "Replacement failed; previous installation restored. Close Live and retry"
            ) from exc
        return dest
    finally:
        if stage.exists():
            checked_path(stage)
            if stage.resolve().parent != parent.resolve() or not stage.name.startswith(
                f".{SCRIPT}.stage-"
            ):
                raise InstallError("Refusing cleanup outside the private staging directory")
            for entry in stage.iterdir():
                checked_path(entry)
            shutil.rmtree(stage)


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("usage: python -m abletonlivemcp.install <path to User Library>")
    try:
        destination = install(Path(args[0]))
    except (InstallError, ConfigError, OSError) as exc:
        raise SystemExit(
            f"Installation failed: {exc}. Close Live and check path/access before retrying"
        ) from None
    print(f"installed to {destination}")


if __name__ == "__main__":
    main()
