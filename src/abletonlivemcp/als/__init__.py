"""Offline Ableton project reading and usage analysis (no running Live needed)."""

from .paths import PathEscape, configured_roots, confine
from .reader import AlsError, SetSummary, read_set
from .usage import Collection, UsageIndex, collect, scan, scan_projects

__all__ = [
    "AlsError",
    "Collection",
    "PathEscape",
    "SetSummary",
    "UsageIndex",
    "collect",
    "configured_roots",
    "confine",
    "read_set",
    "scan",
    "scan_projects",
]
