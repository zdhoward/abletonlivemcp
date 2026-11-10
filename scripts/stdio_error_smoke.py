"""Over real MCP stdio, check that a refused call tells the client WHY (not just 'Error executing').

Both calls are rejected before anything changes in Live. Needs Live running for the tempo call.
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CALLS = [
    ("live_set_tempo", {"bpm": 5}),  # refused by the Remote Script in Live
    ("live_plan_chain", {"stages": [{"role": "nonsense", "intent": {}}]}),  # refused by our code
    ("knowledge_read", {"page": "../x"}),  # refused by the knowledge reader
]


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "abletonlivemcp.server"])
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        for name, args in CALLS:
            res = await s.call_tool(name, args)
            text = res.content[0].text if res.content else ""
            print(f"{name}: is_error={res.is_error}\n    {text[:240]}")


asyncio.run(main())
