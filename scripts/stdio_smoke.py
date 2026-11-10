"""Smoke test: launch the MCP server over stdio with a real MCP client and call its tools."""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SAMPLE = "S:/AbletonMCP/projects/Basic Project/Basic.als"


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "abletonlivemcp.server"])
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        print("tools:", [t.name for t in (await s.list_tools()).tools])
        for name, args in [
            ("live_hello", {}),
            ("live_session_info", {}),
            ("als_summary", {"path": SAMPLE}),
            ("als_usage_index", {"root": "S:/AbletonMCP/projects"}),
        ]:
            res = await s.call_tool(name, args)
            text = res.content[0].text if res.content else ""
            print(name, "is_error=", res.is_error, text[:160].replace("\n", " "))


asyncio.run(main())
