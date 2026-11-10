"""Aggregate usage across many Sets: how often each device, plugin and sample appears.

Counts describe what is *saved in the Sets*, not listening time or confirmed playback.
Both per-project presence and raw instance totals are kept so callers can rank either way.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .reader import AlsError, SetSummary, read_set

SKIP_DIRS = {"backup"}  # Live's auto-backups are not independent Sets.


@dataclass
class UsageCount:
    key: str
    projects: int = 0
    instances: int = 0


@dataclass
class UsageIndex:
    sets_scanned: int
    errors: list[tuple[Path, str]]
    devices: list[UsageCount]
    plugins: list[UsageCount]
    samples: list[UsageCount]


def find_sets(root: str | Path) -> list[Path]:
    """All .als files under root, pruning Backup directories (case insensitive)."""
    root = Path(root)
    if any(part.lower() in SKIP_DIRS for part in root.parts):
        return []
    found = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        found.extend(Path(directory) / name for name in files if name.lower().endswith(".als"))
    return sorted(found)


def _rank(counts: dict[str, UsageCount]) -> list[UsageCount]:
    return sorted(counts.values(), key=lambda c: (-c.projects, -c.instances, c.key))


def _tally(keys: Iterable[str]) -> dict[str, UsageCount]:
    """Per-Set counts: instances = occurrences, projects = 1 per distinct key."""
    out: dict[str, UsageCount] = {}
    for key in keys:
        out.setdefault(key, UsageCount(key, projects=1)).instances += 1
    return out


def build_index(
    sets: Iterable[SetSummary], errors: list[tuple[Path, str]] | None = None
) -> UsageIndex:
    tables: tuple[dict[str, UsageCount], ...] = ({}, {}, {})
    n = 0
    for s in sets:
        n += 1
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
    dev, plug, samp = tables
    return UsageIndex(n, errors or [], _rank(dev), _rank(plug), _rank(samp))


def scan(root: str | Path) -> UsageIndex:
    """Read every Set under root into a usage index. Unreadable Sets are reported, not fatal."""
    return scan_projects(Path(root))


def scan_projects(root: Path) -> UsageIndex:
    """Aggregate saved references across Sets; collect unreadable/corrupt file errors."""
    summaries, errors = [], []
    for p in find_sets(root):
        try:
            summaries.append(read_set(p))
        except AlsError as exc:
            errors.append((p, str(exc)))
    return build_index(summaries, errors)
