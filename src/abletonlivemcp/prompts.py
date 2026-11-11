"""MCP prompts (batch 6 fills this; docs/plans/v2-contracts.md).

``register(server)`` is called once by ``server.py`` after every tool is registered. Prompts
are static guidance (vocal chains, organization, drums, manual macro mapping, ...) that name the
registered tools; they never call Live themselves.
"""

from __future__ import annotations


def register(server) -> None:
    """Add prompts to ``server.mcp`` (the module ``abletonlivemcp.server``). Empty for now."""
