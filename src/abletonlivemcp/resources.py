"""MCP resources (batch 6 fills this; docs/plans/v2-contracts.md).

``register(server)`` is called once by ``server.py`` after every tool is registered. Resources
call the existing read implementations (``server.SPECS[name].fn`` or the bridge via
``server._call``); they never add a second read path.
"""

from __future__ import annotations


def register(server) -> None:
    """Add resources to ``server.mcp`` (the module ``abletonlivemcp.server``). Empty for now."""
