"""Smoke test: launch the MCP server over stdio with a real MCP client and call its read tools.

Exit 0 = every call succeeded, 1 = a call failed, 2 = could not run. Needs Live running with the
Remote Script (read-only is fine; this makes no writes).
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

READS = ["live_hello", "live_get_session", "live_get_tracks"]


async def main() -> int:
    params = StdioServerParameters(command=sys.executable, args=["-m", "abletonlivemcp.server"])
    failed = 0
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        tools = (await s.list_tools()).tools
        names = [t.name for t in tools]
        print("tools:", len(names), names)
        for t in tools:
            d = t.model_dump(by_alias=True)
            a = d.get("annotations") or {}
            keys = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")
            flags = {k: a.get(k) for k in keys} if a else None
            title = d.get("title") or a.get("title")
            ok = bool(title) and flags is not None and d.get("outputSchema") is not None
            has_out = d.get("outputSchema") is not None
            verdict = "PASS" if ok else "FAIL"
            print(verdict, "surface", t.name, "|", title, "|", flags, "| out:", has_out)
            failed += not ok
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
