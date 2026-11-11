"""Run one fixed dev probe (T-003) against a running Live and write its evidence.

Usage: ``python scripts/live_probe_run.py P-01``

The Remote Script refuses every probe method unless the private bridge config says
``"dev_probes": true``; a write (behavioural) probe also needs ``"read_only": false`` and runs
under a lease, on scratch objects it creates and deletes itself. Introspection probes are reads.

Writes ``docs/release/probes/P-NN.md`` and, for probes that produce a data file (P-01: the Live
API dump ``docs/data/live-<major>.<minor>-api.json``), that file. Owner paths (home directory,
user profile paths) are replaced with ``~`` before anything is written.

Exit codes: 0 the probe ran and recorded a verdict (go, no-go or gated); 1 the probe raised or
returned no verdict; 2 it could not run (unreachable, refused, dev_probes off, stub probe).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

from abletonlivemcp.bridge import DEFAULT_PORT, BridgeClient, BridgeError

ROOT = Path(__file__).resolve().parents[1]
VERDICTS = ("go", "no-go", "gated")
LEASE_TTL = 60
# Probes whose result carries a data file; the summary keys stay in the markdown.
DATA_FILES = {"P-01": "live-{major}.{minor}-api.json"}
_OWNER_PATH = re.compile(
    r"(?i)(?:[a-z]:[\\/]+(?:users|documents and settings)|/users|/home)[\\/]+[^\\/\s\"'<>|]+"
)


class Abort(Exception):
    """The probe could not run: exit code 2."""


def strip_owner_paths(value, home=None):
    """Recursively replace the home directory and any user-profile path prefix with ``~``."""
    home = home if home is not None else os.path.expanduser("~")
    homes = {h for h in (home, home.replace("\\", "/"), home.replace("/", "\\")) if len(h) > 3}

    def text(s):
        for h in sorted(homes, key=len, reverse=True):
            s = re.sub(re.escape(h), "~", s, flags=re.IGNORECASE)
        return _OWNER_PATH.sub("~", s)

    if isinstance(value, str):
        return text(value)
    if isinstance(value, list):
        return [strip_owner_paths(v, home) for v in value]
    if isinstance(value, dict):
        return {text(k): strip_owner_paths(v, home) for k, v in value.items()}
    return value


def _call(client, method, params=None):
    result = client.call(method, params)
    if isinstance(result, dict) and result.get("refused") is True:
        raise Abort(f"{method} refused: {result.get('code')}: {result.get('message')}")
    return result


def run_probe(client, name):
    """Return ``(hello, reply)`` for one probe; raises Abort when it cannot run."""
    hello = _call(client, "hello")
    kinds = _call(client, "probe_list")["probes"]
    kind = kinds.get(name)
    if kind == "read":
        return hello, _call(client, "probe_read", {"name": name})
    if kind != "write":
        raise Abort(f"unknown probe {name}; known: {', '.join(sorted(kinds))}")
    lease = _call(client, "lease_acquire", {"ttl": LEASE_TTL})
    try:
        params = {"name": name, "generation": lease["generation"], "lease": lease["lease"]}
        return hello, _call(client, "probe_run", params)
    finally:
        try:
            client.call("lease_release", {"lease": lease["lease"]})
        except BridgeError as exc:
            print(f"info lease release failed: {exc}")


def _version(hello):
    version = hello.get("live_version") or []
    return ".".join(str(v) for v in version) or "unknown"


def render(name, hello, reply, data_path=None):
    result = reply.get("result") if isinstance(reply.get("result"), dict) else {}
    verdict = result.get("verdict", "error" if not reply.get("ok") else "missing")
    lines = [
        f"# {name} probe evidence",
        "",
        f"- Verdict: **{verdict}**",
        f"- Live version: {_version(hello)}",
        f"- Protocol: {hello.get('protocol')}",
        f"- Kind: {reply.get('kind')}",
        f"- Run: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "- Runner: `scripts/live_probe_run.py` (T-003 fixed probe table)",
    ]
    if data_path:
        lines.append(f"- Data: `{data_path}`")
    if not reply.get("ok"):
        lines += ["", "## Error", "", "```", str(reply.get("error")), "```"]
    if "scratch" in reply:
        lines += ["", "## Scratch cleanup", "", "```json", json.dumps(reply["scratch"]), "```"]
    if name == "P-01" and result:
        lines += ["", "## hasattr answers", "", "| Member | Owners |", "|---|---|"]
        for member, owners in result.get("hasattr", {}).items():
            lines.append(f"| `{member}` | {', '.join(owners) or '**absent**'} |")
        for sub, per_class in result.get("matching", {}).items():
            lines += ["", f"Members containing `{sub}`:", ""]
            for label, members in per_class.items():
                lines.append(f"- {label}: {', '.join(f'`{m}`' for m in members)}")
            if not per_class:
                lines.append("- none")
        found = ", ".join(result.get("classes", {})) or "none"
        lines += ["", "## Classes", "", f"Dumped: {found}", ""]
        lines.append(f"Missing: {', '.join(result.get('missing', [])) or 'none'}")
        lines.append(f"Docstring limit: {result.get('doc_limit')}")
    elif result:
        lines += ["", "## Result", "", "```json", json.dumps(result, indent=1), "```"]
    return "\n".join(lines) + "\n"


def write_evidence(name, hello, reply, root=ROOT, home=None):
    """Write the evidence (owner paths stripped); returns the paths written."""
    hello, reply = strip_owner_paths(hello, home), strip_owner_paths(reply, home)
    written, data_rel = [], None
    result = reply.get("result")
    if name in DATA_FILES and reply.get("ok") and isinstance(result, dict):
        version = hello.get("live_version") or ["x", "x"]
        data_rel = Path("docs/data") / DATA_FILES[name].format(major=version[0], minor=version[1])
        target = root / data_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        body = {"probe": name, "live_version": hello.get("live_version"), **result}
        target.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        written.append(target)
    doc = root / "docs/release/probes" / f"{name}.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(render(name, hello, reply, data_rel and data_rel.as_posix()), encoding="utf-8")
    written.append(doc)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("probe", help="probe id, e.g. P-01")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"P-\d\d", args.probe):
        print("probe id must look like P-01")
        return 2
    client = BridgeClient(port=args.port, timeout=args.timeout)
    try:
        hello, reply = run_probe(client, args.probe)
    except (Abort, BridgeError) as exc:
        print(f"did not run: {exc}")
        return 2
    result = reply.get("result") if isinstance(reply.get("result"), dict) else {}
    if reply.get("ok") and result.get("verdict") == "not_implemented":
        print(f"{args.probe} is still a stub; nothing written")
        return 2
    for path in write_evidence(args.probe, hello, reply):
        print(f"wrote {path.relative_to(ROOT).as_posix()}")
    if not reply.get("ok"):
        print(f"FAIL {args.probe} raised: {reply.get('error')}")
        return 1
    if result.get("verdict") not in VERDICTS:
        print(f"FAIL {args.probe} returned no verdict")
        return 1
    print(f"{args.probe} verdict: {result['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
