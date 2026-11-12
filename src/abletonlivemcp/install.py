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
from .errors import Invalid

SCRIPT = "AbletonLiveMCP"
MANIFEST = ".abletonlivemcp-install.json"
# Every module the Remote Script imports (flat files only: a subpackage would not be copied).
DOMAINS = (
    "common", "session", "tracks", "scenes", "clips", "notes", "devices", "browser", "drums",
    "racks", "arrangement", "automation", "recording", "editing", "song", "view", "devx", "labels",
    "probe",
)  # fmt: skip
# The fixed dev probe table (dom_probe.PROBE_NUMBERS). Development add-on: release archives
# omit every probe, a source checkout has every probe, and a partial set is refused.
PROBES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 27, 29)
REQUIRED = frozenset(
    {"__init__.py", "core.py", "handlers.py", "operations.py", "safety.py", "version.py"}
    | {f"dom_{name}.py" for name in DOMAINS}
)
OPTIONAL_PROBES = frozenset(f"probe_p{n:02d}.py" for n in PROBES)


class InstallError(Invalid):
    """An installation cannot be safely replaced."""


def source_files() -> dict:
    """Use wheel resources, with the canonical tree for editable development only."""
    root = resources.files("abletonlivemcp").joinpath("_remote_script", SCRIPT)
    if root.is_dir():
        return {entry.name: entry for entry in root.iterdir() if entry.is_file()}
    root = checked_path(Path(__file__).absolute().parents[2] / "remote_script" / SCRIPT)
    if not root.is_dir():
        raise InstallError("Remote Script resources are missing; reinstall the host package")
    return {entry.name: entry for entry in root.glob("*.py")}


_BUILD_FILE = re.compile(r"(?!probe_p\d\d\.py\Z)\w+\.py\Z")


def packaged_identity() -> tuple[str, str]:
    """(version, build) of the Remote Script this host ships; the same values a freshly
    installed script reports (core.script_identity / core.build_id, kept in step by a test)."""
    files = {n: e.read_bytes() for n, e in source_files().items() if _BUILD_FILE.match(n)}
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode() + b"\0" + files[name] + b"\0")
    found = re.search(rb'^VERSION = "([^"]+)"', files.get("version.py", b""), re.M)
    return (found[1].decode() if found else "unknown"), "sha256:" + digest.hexdigest()[:16]


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
        not isinstance(manifest, dict)
        or manifest.get("format") != 1
        or manifest.get("script") != SCRIPT
        or manifest.get("files") != managed
    ):
        raise InstallError(f"Unmanaged or modified installation; preserved intact: {directory}")
    for name in actual.keys() - managed.keys():
        match = re.fullmatch(r"__pycache__/(\w+)\.cpython-\d+(?:\.opt-\d+)?\.pyc", name)
        if match is None or f"{match[1]}.py" not in managed:
            raise InstallError(f"Unmanaged cache file; installation preserved: {directory}")
    return actual


def _overlaps(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def _prune_backups(parent: Path, keep: Path | None) -> None:
    """Keep only the newest installer-owned backup; never raise, never touch foreign folders."""
    try:
        candidates = [
            entry
            for entry in parent.iterdir()
            if re.fullmatch(rf"\.{SCRIPT}\.backup-[0-9a-f]{{32}}", entry.name)
        ]
        if keep is None and candidates:
            keep = max(candidates, key=lambda entry: entry.stat().st_mtime_ns)
    except OSError:
        return
    for entry in candidates:
        if entry == keep:
            continue
        try:
            checked_path(entry)
            if entry.resolve().parent != parent.resolve():
                continue
            _owned_snapshot(entry)  # requires our manifest and unmodified managed files
            shutil.rmtree(entry)
        except Exception:  # noqa: BLE001 - unowned, modified or busy backups are preserved
            continue


def install(user_library: Path) -> Path:
    library = checked_path(user_library)
    presets = checked_path(library / "Presets")
    if not presets.is_dir():
        raise InstallError(
            f"{library} does not look like an Ableton User Library (missing Presets)"
        )
    parent = checked_path(library / "Remote Scripts")
    dest = checked_path(parent / SCRIPT)
    configuration = config_path()
    if _overlaps(dest, configuration):
        raise InstallError("Bridge configuration and script installation paths must not overlap")
    package_root = checked_path(Path(__file__).absolute().parents[1])
    if _overlaps(library, package_root) or _overlaps(configuration, package_root):
        raise InstallError("Library, configuration and package resources must not overlap")
    files = source_files()
    probes = OPTIONAL_PROBES & files.keys()
    if not REQUIRED <= files.keys() or probes not in (frozenset(), OPTIONAL_PROBES):
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
                        "Replacement and rollback failed. Previous installation remains "
                        f"at {backup}; close Live before restoring that folder"
                    ) from exc
            raise InstallError(
                "Replacement failed; previous installation restored. Close Live and retry"
            ) from exc
        _prune_backups(parent, keep=backup if previous is not None else None)
        return dest
    finally:
        # Cleanup must never raise: that would hide the original error and backup location.
        try:
            if stage.exists():
                checked_path(stage)
                if stage.resolve().parent != parent.resolve() or not stage.name.startswith(
                    f".{SCRIPT}.stage-"
                ):
                    raise InstallError("Refusing cleanup outside the private staging directory")
                for entry in stage.iterdir():
                    checked_path(entry)
                shutil.rmtree(stage)
        except Exception:  # noqa: BLE001, S110 - best effort; leftovers are harmless
            pass


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
