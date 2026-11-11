"""Smoke test: launch the MCP server over stdio with a real MCP client and call its read tools.

Exit 0 = every call succeeded, 1 = a call failed, 2 = could not run. Needs Live running with the
Remote Script (read-only is fine; this makes no writes).
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

READS = ["live_hello", "live_session_info", "live_tracks", "live_get_transport"]


async def main() -> int:
    params = StdioServerParameters(command=sys.executable, args=["-m", "abletonlivemcp.server"])
    failed = 0
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        names = [t.name for t in (await s.list_tools()).tools]
        print("tools:", len(names), names)
        for name in READS:
            if name not in names:
                print("FAIL missing tool", name)
                failed += 1
                continue
            res = await s.call_tool(name, {})
            text = res.content[0].text if res.content else ""
            print("FAIL" if res.is_error else "PASS", name, text[:120].replace("\n", " "))
            failed += bool(res.is_error)
    print("RESULT:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


try:
    sys.exit(asyncio.run(main()))
except OSError as exc:
    print("RESULT: ABORT (exit 2):", exc)
    sys.exit(2)
