"""Aggregate usage across many Sets: how often each device, plugin and sample appears.

Counts describe what is *saved in the Sets*, not listening time or confirmed playback.
Both per-project presence and raw instance totals are kept so callers can rank either way.
Recency comes from each Set file's modification time: ``last_seen`` is the newest Set that holds
the item and ``recent`` is how many holding Sets changed within the recency window.
"""

from __future__ import annotations

import fnmatch
import time
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .paths import plain_entries
from .reader import AlsError, SetSummary, read_set

SKIP_DIRS = {"backup"}  # Live's auto-backups are not independent Sets.
MAX_SETS = 2000  # Sets read per scan
MAX_VISITED = 200_000  # directory entries looked at per scan
RECENT_DAYS = 90


@dataclass
class UsageCount:
    key: str
    projects: int = 0
    instances: int = 0
    last_seen: float | None = None  # newest modification time (epoch seconds) of a holding Set
    recent: int = 0  # holding Sets modified within the recency window


@dataclass
class UsageIndex:
    sets_scanned: int
    errors: list[tuple[Path, str]]
    devices: list[UsageCount]
    plugins: list[UsageCount]
    samples: list[UsageCount]


@dataclass
class Collection:
    """What one scan read: the Set summaries and everything the usage index needs about them."""

    summaries: list[SetSummary] = field(default_factory=list)
    mtimes: dict[Path, float] = field(default_factory=dict)
    errors: list[tuple[Path, str]] = field(default_factory=list)
    found: int = 0  # Sets that matched the filters
    truncated: bool = False  # a cap (Sets, entries visited or time) stopped the scan early


def _iter_sets(root: Path, meta: dict) -> Iterator[tuple[Path, float]]:
    """(.als path, mtime) under root: Backup folders and every link/junction/reparse point are
    skipped, and the walk stops after MAX_VISITED entries."""
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = list(plain_entries(directory))
        except OSError:
            continue
        for entry in entries:
            meta["visited"] += 1
            if meta["visited"] > MAX_VISITED:
                meta["truncated"] = True
                return
            try:
                if entry.is_dir(follow_symlinks=False):
                    if entry.name.lower() not in SKIP_DIRS:
                        stack.append(Path(entry.path))
                elif entry.name.lower().endswith(".als") and entry.is_file(follow_symlinks=False):
                    yield Path(entry.path), entry.stat(follow_symlinks=False).st_mtime
            except OSError:
                continue


def find_sets(root: str | Path) -> list[Path]:
    """All .als files under root, pruning Backup directories (case insensitive)."""
    root = Path(root)
    if any(part.lower() in SKIP_DIRS for part in root.parts):
        return []
    return sorted(path for path, _ in _iter_sets(root, {"visited": 0, "truncated": False}))


def _rank(counts: dict[str, UsageCount]) -> list[UsageCount]:
    return sorted(counts.values(), key=lambda c: (-c.projects, -c.instances, c.key))


def _tally(keys: Iterable[str]) -> dict[str, UsageCount]:
    """Per-Set counts: instances = occurrences, projects = 1 per distinct key."""
    out: dict[str, UsageCount] = {}
    for key in keys:
        out.setdefault(key, UsageCount(key, projects=1)).instances += 1
    return out


def build_index(
    sets: Iterable[SetSummary],
    errors: list[tuple[Path, str]] | None = None,
    *,
    mtimes: dict[Path, float] | None = None,
    recent_days: int = RECENT_DAYS,
    now: float | None = None,
) -> UsageIndex:
    now = time.time() if now is None else now
    cutoff = now - recent_days * 86400
    tables: tuple[dict[str, UsageCount], ...] = ({}, {}, {})
    n = 0
    for s in sets:
        n += 1
        modified = (mtimes or {}).get(s.path)
        per_set = (
            _tally(d.device_class for d in s.devices),
            _tally(f"{d.plugin_format}:{d.plugin_name}" for d in s.devices if d.plugin_name),
            _tally(r.path or r.relative_path for r in s.samples if r.path or r.relative_path),
        )
        for total, local in zip(tables, per_set, strict=True):
            for key, c in local.items():
                t = total.setdefault(key, UsageCount(key))
                t.projects += c.projects
                t.instances += c.instances
                if modified is not None:
                    t.last_seen = modified if t.last_seen is None else max(t.last_seen, modified)
                    t.recent += modified >= cutoff
    dev, plug, samp = tables
    return UsageIndex(n, errors or [], _rank(dev), _rank(plug), _rank(samp))


def collect(
    roots: Sequence[Path],
    *,
    confine: Sequence[str | Path] | None = None,
    since_days: float | None = None,
    folder_glob: str | None = None,
    limit: int = MAX_SETS,
    budget_s: float | None = None,
) -> Collection:
    """Read the most recently saved Sets under ``roots`` (newest first, at most ``limit``).

    ``confine`` is the allowlist every read is validated against (the tools pass the configured
    roots); None trusts the caller. ``folder_glob`` is matched case-insensitively against the
    folder of each Set relative to its root, with ``/`` separators. Unreadable Sets are reported
    in ``errors``, not raised."""
    now = time.time()
    meta = {"visited": 0, "truncated": False}
    out = Collection()
    candidates: list[tuple[float, Path]] = []
    for root in roots:
        if any(part.lower() in SKIP_DIRS for part in root.parts):
            continue
        for path, modified in _iter_sets(root, meta):
            if since_days is not None and modified < now - since_days * 86400:
                continue
            if folder_glob:
                folder = path.parent.relative_to(root).as_posix().lower()
                if not fnmatch.fnmatchcase(folder, folder_glob.lower()):
                    continue
            candidates.append((modified, path))
    out.truncated = meta["truncated"]
    candidates.sort(key=lambda c: (-c[0], str(c[1])))
    out.found = len(candidates)
    started = time.monotonic()
    for modified, path in candidates[: max(0, min(limit, MAX_SETS))]:
        if budget_s is not None and time.monotonic() - started > budget_s:
            out.truncated = True
            break
        try:
            summary = read_set(path, roots=confine)
        except AlsError as exc:
            out.errors.append((path, str(exc)))
            continue
        out.summaries.append(summary)
        out.mtimes[path] = modified
    if len(candidates) > min(limit, MAX_SETS):
        out.truncated = True
    return out


def scan(root: str | Path) -> UsageIndex:
    """Read every Set under root into a usage index. Unreadable Sets are reported, not fatal."""
    return scan_projects(Path(root))


def scan_projects(root: Path, **filters) -> UsageIndex:
    """Aggregate saved references across Sets; collect unreadable/corrupt file errors.
    ``filters`` are ``collect``'s keyword arguments."""
    got = collect([Path(root)], **filters)
    return build_index(got.summaries, got.errors, mtimes=got.mtimes)
