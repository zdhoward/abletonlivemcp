"""Over real MCP stdio: knowledge tools are listed only when a knowledge folder exists.

Usage: knowledge_optional_smoke.py [folder]
The folder sets ABLETONLIVEMCP_KNOWLEDGE; omit it to use the default.
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    env = dict(os.environ)
    if len(sys.argv) > 1:
        env["ABLETONLIVEMCP_KNOWLEDGE"] = sys.argv[1]
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "abletonlivemcp.server"], env=env
    )
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        names = [t.name for t in (await s.list_tools()).tools]
        print(f"{len(names)} tools; knowledge tools:", [n for n in names if "knowledge" in n])


asyncio.run(main())
