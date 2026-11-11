"""MCP tool modules, one per domain or toolset. Importing this package registers every tool.

The import list is fixed: later tickets add tools inside their own module, never here. Each module
imports its helpers from ``abletonlivemcp.server``; the server imports the tool modules only after
its helpers are defined, and this package loads the server before any tool module.
"""

from .. import server  # noqa: F401 - must load first: it defines the helpers the tools use
from . import (  # noqa: F401 - imported for their registrations
    als,
    arrangement,
    automation,
    browser,
    chain,
    clips,
    devices,
    devices_advanced,
    drums,
    editing,
    experimental,
    files,
    library,
    notes,
    organize,
    racks,
    recording,
    scenes,
    session,
    song,
    tracks,
    view,
)
