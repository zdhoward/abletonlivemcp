"""[READ-ONLY] Over real MCP stdio, check that an error tells the client WHY (needs no write flag).

Starts the MCP server over stdio and makes two calls that can never change Live:
  1. live_plan_chain with an empty stage list: rejected by our own code before any bridge call
     (expects 'invalid_plan' and '(not applied)').
  2. live_get_operation with an unknown id: a bridge READ. With a live bridge it is refused
     ('refused:unknown_operation'); with no bridge it is a bridge failure ('Unreachable').
     Either way the client must see that readable text, never a bare 'Error executing tool'.
Use --expect-bridge-text to demand a specific substring (e.g. 'Unreachable' against a dead
port, 'refused:unknown_operation' against a live bridge); absent text exits 1.

Exit codes: 0 every required check passed; 1 expected error text absent; 2 could not run.
Lines marked 'info' never change the code.
"""

import argparse
import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from abletonlivemcp.bridge import DEFAULT_PORT

# The child is the real server; only its bridge port is set so --port can be honoured.
CHILD = (
    "import sys; from abletonlivemcp import server; "
    "from abletonlivemcp.bridge import BridgeClient; "
    "server._bridge = BridgeClient(port=int(sys.argv[1])); server.main()"
)
BRIDGE_KINDS = ("Unreachable", "refused:unknown_operation")


async def run(port, expect):
    failures = []

    def require(ok, label, detail=""):
        text = f"{label}: {detail}" if detail else label
        print(f"{'PASS' if ok else 'FAIL'} {text}")
        if not ok:
            failures.append(text)

    forward = {k: os.environ[k] for k in ("PYTHONPATH", "ABLETONLIVEMCP_CONFIG") if k in os.environ}
    params = StdioServerParameters(
        command=sys.executable, args=["-c", CHILD, str(port)], env=forward
    )
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        names = {t.name for t in (await s.list_tools()).tools}
        have = {"live_plan_chain", "live_get_operation"} <= names
        require(have, "server lists the tools under test", f"{len(names)} tools")

        res = await s.call_tool("live_plan_chain", {"track": 0, "stages": []})
        text = res.content[0].text if res.content else ""
        print(f"info live_plan_chain: is_error={res.is_error} text={text[:200]!r}")
        require(
            res.is_error and "invalid_plan" in text and "(not applied)" in text,
            "invalid request surfaces readable text",
        )

        res = await s.call_tool("live_get_operation", {"operation": "0000000000000000"})
        text = res.content[0].text if res.content else ""
        print(f"info live_get_operation: is_error={res.is_error} text={text[:240]!r}")
        require(
            res.is_error and any(k in text for k in BRIDGE_KINDS) and "(not applied)" in text,
            "bridge refusal/failure surfaces readable text",
        )
        if expect:
            require(expect in text, "expected bridge error text present", repr(expect))
    return failures


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="bridge port (default %(default)s)"
    )
    p.add_argument("--expect-bridge-text", help="substring the bridge error text must contain")
    a = p.parse_args(argv)
    print(f"mode: READ-ONLY - sends no write requests; bridge port 127.0.0.1:{a.port}")
    try:
        failures = asyncio.run(run(a.port, a.expect_bridge_text))
    except Exception as exc:  # noqa: BLE001 - one-line reason, nonzero exit
        print(
            f"RESULT: ABORT (exit 2): cannot run the MCP stdio session: {type(exc).__name__}: {exc}"
        )
        return 2
    if failures:
        print(f"RESULT: FAIL (exit 1): {failures[0]}")
        return 1
    print("RESULT: PASS (exit 0): error text reached the client")
    return 0


if __name__ == "__main__":
    sys.exit(main())
