"""Shared harness for the real-Live proofs (`scripts/live_<domain>_test.py`).

A proof is an async scenario ``async def scenario(h: Harness, args, chk: Checks)``. The harness
launches the real stdio MCP server, hands the scenario an MCP session (``h.tool``) plus a raw
bridge handle (``h.bridge``) for protocol-level checks the tool surface hides (references,
generations), and turns the outcome into an exit code and an evidence file.

Exit codes: 0 every required check passed; 1 a required check failed; 2 the proof could not run
(not allowed, Live/bridge unreachable or read-only, bad arguments). Lines marked 'info' never
change the code.

Evidence: ``docs/release/v2/<ticket>.md`` with the Live version, the AbletonLiveMCP lines of
Live's ``Log.txt`` (module list, listening line) and the full proof output.

Typical use::

    def main(argv=None):
        return run_proof("T-004", scenario, parser, argv)
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import json
import os
import sys
import time
from collections.abc import Awaitable, Callable
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from abletonlivemcp.bridge import DEFAULT_PORT, BridgeClient, BridgeError

REPO = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO / "docs" / "release" / "v2"


class Abort(Exception):
    """Cannot run (unreachable, read-only, bad input): exit code 2."""


class Stop(Exception):
    """A required step failed and later steps would be unsafe: finish with exit code 1."""


class Refused(Exception):
    """A bridge or tool refusal, with its stable code."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class Checks:
    def __init__(self):
        self.failures: list[str] = []
        self.passed = 0

    def require(self, ok, label, detail="", fatal=False):
        text = f"{label}: {detail}" if detail else label
        print(f"{'PASS' if ok else 'FAIL'} {text}")
        if ok:
            self.passed += 1
        else:
            self.failures.append(text)
            if fatal:
                raise Stop
        return bool(ok)

    def info(self, label, detail=""):
        print(f"info {label}" + (f": {detail}" if detail else ""))


@dataclass
class Scratch:
    """A track this proof created; the only object a proof may modify."""

    kind: str
    index: int
    name: str = ""


def _unwrap(data):
    if isinstance(data, dict) and data.get("provenance") == "live_object_text_untrusted":
        return data["data"]
    return data


def _error_code(text: str) -> str | None:
    """`refused:<code>: ...` or `<code>: ...` (the server's stable error text) -> code."""
    head = text.split(":")
    if head[0] == "refused" and len(head) > 1:
        return head[1].strip()
    return head[0].strip() if len(head) > 1 else None


class Harness:
    def __init__(self, session: ClientSession, port: int, timeout: float):
        self.session = session
        self.bridge = BridgeClient(port=port, timeout=timeout)
        self.tool_names: list[str] = []
        self.created: list[Scratch] = []

    # ---- MCP tool calls -------------------------------------------------------------------

    async def raw_tool(self, name: str, args: dict | None = None):
        """(is_error, text, structured) of one tool call, without interpretation."""
        res = await self.session.call_tool(name, args or {})
        text = res.content[0].text if res.content else ""
        return bool(res.is_error), text, getattr(res, "structuredContent", None)

    async def tool(self, name: str, args: dict | None = None):
        """Result of one tool call (untrusted wrapper removed). An error result raises Refused;
        a read_only refusal raises Abort."""
        is_error, text, structured = await self.raw_tool(name, args)
        if is_error:
            code = _error_code(text) or "tool_error"
            if code == "read_only":
                raise Abort(
                    "writes are disabled; set read_only to false in bridge.json and restart "
                    "Live (nothing was changed)"
                )
            raise Refused(code, text)
        if isinstance(structured, dict):
            data = structured.get("result", structured)
        else:
            try:
                data = json.loads(text)
            except ValueError:
                data = text
        return _unwrap(data)

    async def expect_refusal(self, code: str | None, name: str, args: dict | None = None):
        """(ok, detail): the tool call failed (with `code`, if given) and changed nothing."""
        try:
            await self.tool(name, args)
        except Refused as exc:
            return code is None or exc.code == code, f"refused {exc.code}"
        return False, "the call was accepted"

    # ---- raw bridge calls (protocol-level checks) -----------------------------------------

    def call(self, method: str, params: dict | None = None):
        """Result of one raw bridge call; a refusal reply raises Refused (read_only: Abort)."""
        result = self.bridge.call(method, params)
        if isinstance(result, dict) and result.get("refused") is True:
            if result.get("code") == "read_only":
                raise Abort(
                    "bridge is read-only; set read_only to false in bridge.json and restart "
                    "Live (nothing was changed)"
                )
            raise Refused(str(result.get("code")), str(result.get("message")))
        return result

    def expect_bridge_refusal(
        self, method: str, params: dict | None = None, code: str | None = None
    ):
        """(ok, detail): the bridge refused the call (with `code`, if given) or the handler
        rejected it (only accepted when no code is required)."""
        try:
            self.call(method, params)
        except Refused as exc:
            return code is None or exc.code == code, f"refused {exc.code}"
        except BridgeError as exc:
            return code is None, f"bridge error {exc.kind}"
        return False, "the call was accepted"

    # ---- scratch objects ------------------------------------------------------------------

    async def scratch_track(self, kind: str = "audio", prefix: str = "ALMCP") -> Scratch:
        """Create one new track at the end through the MCP tool; it is the only track the proof
        may modify. Raises Stop if the track did not appear."""
        before = (await self.tool("live_get_session"))["track_count"]
        await self.tool("live_create_tracks", {"tracks": [{"kind": kind, "index": -1}]})
        after = (await self.tool("live_get_session"))["track_count"]
        if after != before + 1:
            print(f"FAIL scratch {kind} track created: count {before} -> {after}")
            raise Stop
        track = Scratch(kind=kind, index=before, name=f"{prefix} {time.strftime('%H%M%S')}")
        self.created.append(track)
        return track


Scenario = Callable[[Harness, argparse.Namespace, Checks], Awaitable[None]]


# ---- evidence ---------------------------------------------------------------------------


def find_log() -> Path | None:
    """Newest Live Log.txt under %APPDATA%/Ableton (Windows) or ~/Library/Preferences/Ableton."""
    roots = [
        os.path.join(os.environ.get("APPDATA", ""), "Ableton", "Live *", "Preferences", "Log.txt"),
        os.path.expanduser("~/Library/Preferences/Ableton/Live */Log.txt"),
    ]
    found = [p for pattern in roots if pattern for p in glob.glob(pattern)]
    return Path(max(found, key=os.path.getmtime)) if found else None


def log_modules(limit: int = 40) -> tuple[str, list[str]]:
    """(log path or reason, the last `limit` AbletonLiveMCP lines of Log.txt)."""
    path = find_log()
    if path is None:
        return "Log.txt not found", []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"{path} unreadable: {exc}", []
    return str(path), [x for x in lines if "AbletonLiveMCP" in x][-limit:]


def write_evidence(ticket: str, title: str, live_version, code: int, output: str) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    log_path, modules = log_modules()
    body = [
        f"# {ticket} evidence ({time.strftime('%Y-%m-%d')}): {title}",
        "",
        f"- Live version: {live_version or 'unknown (hello not answered)'}",
        f"- Result: exit {code}",
        f"- Log.txt: {log_path}",
        "",
        "## Log.txt (AbletonLiveMCP lines, module list)",
        "",
        "```",
        *(modules or ["(none obtained)"]),
        "```",
        "",
        "## Output",
        "",
        "```",
        output.rstrip(),
        "```",
        "",
    ]
    path = EVIDENCE_DIR / f"{ticket}.md"
    path.write_text("\n".join(body), encoding="utf-8")
    return path


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for s in self.streams:
            s.write(text)
        return len(text)

    def flush(self):
        for s in self.streams:
            s.flush()


# ---- runner -----------------------------------------------------------------------------


def server_params(toolsets: str | None = None, extra_env: dict | None = None):
    """Parameters for launching the real stdio server (``toolsets``: the
    ``ABLETONLIVEMCP_TOOLSETS`` value, e.g. ``"all"``; None keeps the caller's environment)."""
    env = {**os.environ, **(extra_env or {})}
    if toolsets is not None:
        env["ABLETONLIVEMCP_TOOLSETS"] = toolsets
    return StdioServerParameters(
        command=sys.executable, args=["-m", "abletonlivemcp.server"], env=env
    )


async def _run(scenario: Scenario, args, chk: Checks, state: dict) -> None:
    params = server_params()
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        h = Harness(session, args.port, args.timeout)
        h.tool_names = [t.name for t in (await session.list_tools()).tools]
        chk.info("tools", f"{len(h.tool_names)} listed by the stdio server")
        hello = await h.tool("live_hello")
        version = hello.get("live_version")
        state["live_version"] = (
            ".".join(map(str, version)) if isinstance(version, list | tuple) else version
        )
        chk.info("live", f"version {state['live_version']} protocol {hello.get('protocol')}")
        await scenario(h, args, chk)


def _flatten(exc: BaseException) -> BaseException:
    """The MCP client's task group wraps exceptions raised in the scenario in an exception
    group; unwrap a group with a single leaf so Abort/Stop/Refused keep their meaning."""
    while isinstance(getattr(exc, "exceptions", None), tuple) and len(exc.exceptions) == 1:
        exc = exc.exceptions[0]
    return exc


def finish(scenario: Scenario, args, state: dict | None = None) -> int:
    """Run the scenario against the real stdio server; print RESULT and return the exit code."""
    chk = Checks()
    state = state if state is not None else {}
    try:
        try:
            asyncio.run(_run(scenario, args, chk, state))
        except BaseException as exc:
            raise _flatten(exc) from None
    except Stop:
        pass
    except Abort as exc:
        print(f"RESULT: ABORT (exit 2): {exc}")
        return 2
    except Refused as exc:
        chk.failures.append(f"unexpected refusal {exc}")
        print(f"FAIL unexpected refusal {exc}")
    except BridgeError as exc:
        if exc.kind in ("Unreachable", "ConfigError"):
            print(f"RESULT: ABORT (exit 2): bridge unusable: {exc}")
            return 2
        chk.failures.append(f"unexpected bridge error {exc}")
        print(f"FAIL unexpected bridge error {exc}")
    except (OSError, RuntimeError) as exc:  # server would not start / pipe died
        print(f"RESULT: ABORT (exit 2): could not run the stdio server: {exc!r}")
        return 2
    if chk.failures:
        print(f"RESULT: FAIL (exit 1): {chk.failures[0]}")
        return 1
    print(f"RESULT: PASS (exit 0): every required check passed ({chk.passed})")
    return 0


def base_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawTextHelpFormatter
    )
    p.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="raw bridge port (default %(default)s)"
    )
    p.add_argument("--timeout", type=float, default=15.0, help="seconds per bridge call")
    p.add_argument("--no-evidence", action="store_true", help="do not write the evidence file")
    return p


def run_proof(
    ticket: str,
    title: str,
    scenario: Scenario,
    args: argparse.Namespace,
    banner: str = "",
) -> int:
    """Print the banner, run the scenario, write docs/release/v2/<ticket>.md (when it ran)."""
    import io

    buf = io.StringIO()
    state: dict = {}
    with redirect_stdout(_Tee(sys.stdout, buf)):
        if banner:
            print(banner)
        code = finish(scenario, args, state)
    if code != 2 and not args.no_evidence:
        path = write_evidence(ticket, title, state.get("live_version"), code, buf.getvalue())
        print(f"evidence: {path}")
    return code


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
