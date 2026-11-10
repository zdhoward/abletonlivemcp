"""Call the knowledge tools through a real MCP stdio client (the way Claude reaches them)."""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CALLS = [
    ("knowledge_list", {}),
    ("knowledge_search", {"query": "kick bass ducking", "limit": 2}),
    ("knowledge_read", {"page": "drums", "section": "Conflicts"}),
    ("knowledge_read", {"page": "../x"}),
]


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "abletonlivemcp.server"])
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        names = [t.name for t in (await s.list_tools()).tools]
        print("knowledge tools listed:", [n for n in names if n.startswith("knowledge")])
        for name, args in CALLS:
            res = await s.call_tool(name, args)
            text = res.content[0].text if res.content else ""
            print(name, "is_error=", res.is_error, "|", text[:150].replace("\n", " "))


asyncio.run(main())
