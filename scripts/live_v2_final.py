"""The single end-of-project v2 proof (fast-track plan; contract: docs/plans/v2-contracts.md).

One long-lived stdio MCP client with every toolset enabled runs every scenario in
``scripts/final_cases/*.json`` in the nine fixed phases (``proof_contract.PHASES``). Batches add
scenarios to their own case file and never edit this runner.

Scenario file: a JSON list of objects::

    {
      "id": "clips-create-midi",          # unique across every file
      "phase": "musical_edits",           # one of PHASES
      "tools": ["live_create_clips"],     # tools this scenario covers (steps add theirs)
      "needs": ["fixture-tracks"],        # ids that must have passed first (else: blocked)
      "steps": [
        {"tool": "live_create_clips", "args": {...}, "expect": "ok", "save": "clip",
         "confirm": "accept", "assert": [{"path": "status", "equals": "complete"}]}
      ],
      "hook": "clips.check_loop"          # optional: async def check_loop(run, case, chk) in
    }                                     #   scripts/final_cases/clips.py

``expect``: ``ok`` (default), ``refused`` (any code), ``refused:<code>``, or ``ok_or_unsupported``
(success, or ``refused:unsupported`` recorded as a supported refusal). ``args`` strings of the
form ``${key.path}`` are replaced with values saved earlier (``save``) in this run; a value of
``${ledger:<label>}`` is the scratch name recorded under that label. ``confirm`` answers the next
destructive confirmation: ``accept`` | ``decline`` | ``cancel`` (default ``decline``).

Scratch ownership: every object a scenario creates is named ``ALMCP-FINAL <run> <label>`` and is
recorded in the ledger (``run.own(label, kind)``; a step's ``"own": {"label", "kind"}`` does it
declaratively). The elicitation callback accepts a confirmation only when the step asked for
``accept`` AND every target in the confirmation message carries an ``expect_name`` that is
ledger-owned; anything else (an unnamed target included) is declined, so the proof can never
delete the owner's material. Destructive steps therefore always pass ``expect_name``.

Coverage: every tool the server registers must be named by at least one scenario; a gap fails the
run (``--check`` verifies coverage and the manifest offline, without Live).

Exit codes: 0 every scenario passed and coverage is complete; 1 a scenario failed, was blocked,
or a tool has no scenario; 2 the proof could not run (Live/bridge unreachable, read-only, bad
manifest or arguments). ``--only ID[,ID]`` reruns just those scenarios (plus nothing else) and
merges their results into the previous results file.

Evidence: ``docs/release/v2-fast-track.md`` (table + output) and ``v2-fast-track.json``
(machine-readable results, used by ``--only``).
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import io
import json
import re
import sys
import time
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

import mcp_types as types
from live_harness import (
    REPO,
    Abort,
    Checks,
    Harness,
    Refused,
    Stop,
    _flatten,
    _Tee,
    base_parser,
    log_modules,
    server_params,
)
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from abletonlivemcp.bridge import BridgeError
from abletonlivemcp.proof_contract import PHASES

CASES_DIR = Path(__file__).resolve().parent / "final_cases"
EVIDENCE_MD = REPO / "docs" / "release" / "v2-fast-track.md"
EVIDENCE_JSON = REPO / "docs" / "release" / "v2-fast-track.json"
LEDGER_JSON = REPO / "docs" / "release" / "v2-fast-track-ledger.json"
SCRATCH_PREFIX = "ALMCP-FINAL"
EXPECTS = re.compile(r"^(ok|refused|refused:[a-z_]+|ok_or_unsupported)$")
TEMPLATE = re.compile(r"\$\{([^}]+)\}")


class ManifestError(ValueError):
    """A malformed scenario file: the proof cannot run (exit 2)."""


# ---- manifest -----------------------------------------------------------------------------


def load_cases(directory: Path = CASES_DIR) -> list[dict]:
    """Every scenario, validated and ordered by phase (file order inside a phase)."""
    cases, seen = [], set()
    for path in sorted(directory.glob("*.json")):
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ManifestError(f"{path.name}: not JSON ({exc})") from None
        if not isinstance(items, list):
            raise ManifestError(f"{path.name}: must be a JSON list of scenarios")
        for n, case in enumerate(items):
            where = f"{path.name}[{n}]"
            if not isinstance(case, dict) or not isinstance(case.get("id"), str):
                raise ManifestError(f"{where}: a scenario is an object with a string 'id'")
            if case["id"] in seen:
                raise ManifestError(f"{where}: duplicate id {case['id']!r}")
            if case.get("phase") not in PHASES:
                raise ManifestError(f"{where}: phase must be one of {PHASES}")
            for step in case.get("steps", []):
                if not isinstance(step, dict) or not isinstance(step.get("tool"), str):
                    raise ManifestError(f"{where}: every step names a 'tool'")
                if not EXPECTS.match(step.get("expect", "ok")):
                    raise ManifestError(f"{where}: bad expect {step.get('expect')!r}")
                if step.get("confirm", "decline") not in ("accept", "decline", "cancel"):
                    raise ManifestError(f"{where}: confirm is accept|decline|cancel")
            seen.add(case["id"])
            cases.append({**case, "_file": path.stem})
    for case in cases:
        missing = [d for d in case.get("needs", []) if d not in seen]
        if missing:
            raise ManifestError(f"{case['id']}: needs unknown scenario(s) {missing}")
    return sorted(cases, key=lambda c: PHASES.index(c["phase"]))


def covered_tools(cases: list[dict]) -> set[str]:
    out: set[str] = set()
    for case in cases:
        out.update(case.get("tools", []))
        out.update(step["tool"] for step in case.get("steps", []))
    return out


def registered_tools() -> list[str]:
    """Every tool the server registers in any toolset (offline; no Live)."""
    from abletonlivemcp import server

    return sorted(server.SPECS)


# ---- run state ----------------------------------------------------------------------------


@dataclass
class Run:
    """What a scenario sees: the MCP harness, saved values, and the scratch ledger."""

    h: Harness
    run_id: str
    saved: dict = field(default_factory=dict)
    ledger: dict = field(default_factory=dict)  # label -> {name, kind, scenario}
    confirm: str = "decline"
    confirmations: list = field(default_factory=list)
    case_id: str = ""

    def own(self, label: str, kind: str) -> str:
        """Record a scratch object this proof creates; returns the name to give it."""
        name = f"{SCRATCH_PREFIX} {self.run_id} {label}"
        self.ledger[label] = {"name": name, "kind": kind, "scenario": self.case_id}
        return name

    def owned_names(self) -> set[str]:
        return {entry["name"] for entry in self.ledger.values()}

    def resolve(self, value):
        """Substitute ``${key.path}`` / ``${ledger:label}`` in step arguments."""
        if isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve(v) for v in value]
        if not isinstance(value, str):
            return value
        whole = TEMPLATE.fullmatch(value)
        if whole:
            return self._lookup(whole.group(1))
        return TEMPLATE.sub(lambda m: str(self._lookup(m.group(1))), value)

    def _lookup(self, key: str):
        if key.startswith("ledger:"):
            label = key.removeprefix("ledger:")
            if label not in self.ledger:
                raise Stop(f"no scratch object labelled {label!r}")
            return self.ledger[label]["name"]
        value = self.saved
        for part in key.split("."):
            if isinstance(value, list) and part.isdigit():
                value = value[int(part)]
            elif isinstance(value, dict) and part in value:
                value = value[part]
            else:
                raise Stop(f"saved value {key!r} not found")
        return value

    async def elicit(self, _ctx, params):
        """Deterministic confirmation: accept only what the step asked for, on owned names."""
        message = getattr(params, "message", "") or ""
        # server.confirmation_message prints one "expect_name=<repr>" per target: every target
        # must carry a ledger-owned name, so an unnamed or foreign target is never accepted.
        names = re.findall(r"expect_name=(None|'[^']*'|\"[^\"]*\")", message)
        owned = self.owned_names()
        action = self.confirm
        if action == "accept" and (
            not names or any(n == "None" or n[1:-1] not in owned for n in names)
        ):
            action = "decline"
        self.confirmations.append(
            {"scenario": self.case_id, "asked": message[:400], "answer": action}
        )
        self.confirm = "decline"  # one answer per step
        if action == "accept":
            return types.ElicitResult(action="accept", content={"confirm": True})
        return types.ElicitResult(action=action)


def _path(data, dotted: str):
    for part in dotted.split(".") if dotted else []:
        data = data[int(part)] if isinstance(data, list) else data[part]
    return data


def _check_asserts(chk: Checks, label: str, result, asserts: list[dict]) -> None:
    for a in asserts:
        try:
            got = _path(result, a.get("path", ""))
        except (KeyError, IndexError, TypeError, ValueError):
            chk.require(False, f"{label} {a.get('path')}", "missing in the result")
            continue
        if "equals" in a:
            chk.require(got == a["equals"], f"{label} {a['path']} == {a['equals']!r}", repr(got))
        if "contains" in a:
            chk.require(a["contains"] in got, f"{label} {a['path']} contains {a['contains']!r}")
        if "approx" in a:
            tol = a.get("tol", 1e-6)
            ok = isinstance(got, int | float) and abs(got - a["approx"]) <= tol
            chk.require(ok, f"{label} {a['path']} ~= {a['approx']} (tol {tol})", repr(got))


async def run_step(run: Run, chk: Checks, case: dict, n: int, step: dict) -> str:
    """One step; returns ``ok`` or ``unsupported`` (a supported refusal). Raises Stop on a
    required failure."""
    label = f"{case['id']}#{n} {step['tool']}"
    if "own" in step:
        run.own(step["own"]["label"], step["own"].get("kind", "object"))
    run.confirm = step.get("confirm", "decline")
    args = run.resolve(step.get("args", {}))
    expect = step.get("expect", "ok")
    try:
        result = await run.h.tool(step["tool"], args)
    except Refused as exc:
        if expect == "refused" or expect == f"refused:{exc.code}":
            chk.require(True, label, f"refused {exc.code} as expected")
            return "ok"
        if expect == "ok_or_unsupported" and exc.code == "unsupported":
            chk.info(label, f"supported refusal: {exc}")
            return "unsupported"
        chk.require(False, label, f"unexpected refusal {exc}", fatal=True)
    if expect.startswith("refused"):
        chk.require(False, label, f"expected {expect} but the call succeeded", fatal=True)
    chk.require(True, label)
    if step.get("save"):
        run.saved[step["save"]] = result
    _check_asserts(chk, label, result, step.get("assert", []))
    return "ok"


def _load_hook(spec: str):
    stem, _, func = spec.partition(".")
    path = CASES_DIR / f"{stem}.py"
    module_spec = importlib.util.spec_from_file_location(f"final_cases_{stem}", path)
    if module_spec is None or not path.is_file():
        raise ManifestError(f"hook file {path.name} not found")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return getattr(module, func)


async def run_case(run: Run, case: dict) -> dict:
    """One scenario -> its result row (status pass/fail/unsupported, failures, duration)."""
    chk, start, status = Checks(), time.monotonic(), "pass"
    run.case_id = case["id"]
    print(f"\n== {case['id']} ({case['phase']})")
    try:
        for n, step in enumerate(case.get("steps", [])):
            if await run_step(run, chk, case, n, step) == "unsupported":
                status = "unsupported"
        if case.get("hook"):
            await _load_hook(case["hook"])(run, case, chk)
    except Stop as exc:
        if exc.args:  # a fatal require already recorded its failure; a bare message did not
            chk.require(False, case["id"], str(exc.args[0]))
    except Refused as exc:
        chk.require(False, case["id"], f"unexpected refusal {exc}")
    except BridgeError as exc:
        if exc.kind in ("Unreachable", "ConfigError"):
            raise Abort(f"bridge unusable: {exc}") from None
        chk.require(False, case["id"], f"bridge error {exc}")
    if chk.failures:
        status = "fail"
    return {
        "id": case["id"],
        "phase": case["phase"],
        "status": status,
        "checks": chk.passed,
        "failures": chk.failures,
        "seconds": round(time.monotonic() - start, 2),
    }


async def run_all(cases: list[dict], args, state: dict) -> list[dict]:
    run_id = time.strftime("%m%d-%H%M%S")
    results: list[dict] = []
    done: dict[str, str] = dict(state.get("prior_status", {}))
    holder: dict = {}

    async def elicit(ctx, params):
        return await holder["run"].elicit(ctx, params)

    params = server_params(toolsets="all")
    async with (
        stdio_client(params) as (r, w),
        ClientSession(r, w, elicitation_callback=elicit) as session,
    ):
        await session.initialize()
        h = Harness(session, args.port, args.timeout)
        h.tool_names = [t.name for t in (await session.list_tools()).tools]
        run = holder["run"] = Run(h=h, run_id=run_id)
        state["listed"] = h.tool_names
        hello = await h.tool("live_hello")
        version = hello.get("live_version")
        state["live_version"] = (
            ".".join(map(str, version)) if isinstance(version, list | tuple) else version
        )
        print(f"info live {state['live_version']}; {len(h.tool_names)} tools listed")
        for phase in PHASES:
            phase_cases = [c for c in cases if c["phase"] == phase]
            if phase_cases:
                print(f"\n### phase {PHASES.index(phase) + 1}/9: {phase}")
            for case in phase_cases:
                blocked = [d for d in case.get("needs", []) if done.get(d) not in ("pass",)]
                if blocked:
                    row = {"id": case["id"], "phase": phase, "status": "blocked",
                           "checks": 0, "failures": [f"needs {blocked}"], "seconds": 0}  # fmt: skip
                    print(f"\n== {case['id']}: BLOCKED (needs {blocked})")
                else:
                    row = await run_case(run, case)
                done[case["id"]] = "pass" if row["status"] in ("pass", "unsupported") else "fail"
                results.append(row)
        state["ledger"] = run.ledger
        state["confirmations"] = run.confirmations
    return results


# ---- evidence -----------------------------------------------------------------------------


def _merge(prior: list[dict], fresh: list[dict]) -> list[dict]:
    by_id = {r["id"]: r for r in prior}
    by_id.update({r["id"]: r for r in fresh})
    return sorted(by_id.values(), key=lambda r: (PHASES.index(r["phase"]), r["id"]))


def write_evidence(results, coverage_gaps, state, code, output) -> None:
    EVIDENCE_MD.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "live_version": state.get("live_version"),
        "exit": code,
        "coverage_gaps": coverage_gaps,
        "results": results,
    }
    EVIDENCE_JSON.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    LEDGER_JSON.write_text(
        json.dumps(
            {"ledger": state.get("ledger", {}), "confirmations": state.get("confirmations", [])},
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    log_path, modules = log_modules()
    rows = [
        f"| {r['id']} | {r['phase']} | {r['status']} | {r['checks']} | "
        f"{'; '.join(r['failures'])[:160].replace('|', '/')} |"
        for r in results
    ]
    body = [
        f"# v2 fast-track final proof ({payload['date']})",
        "",
        f"- Live version: {state.get('live_version') or 'unknown'}",
        f"- Result: exit {code}",
        f"- Coverage gaps: {', '.join(coverage_gaps) or 'none'}",
        f"- Log.txt: {log_path}",
        f"- Ledger: {LEDGER_JSON.relative_to(REPO).as_posix()}",
        "",
        "| Scenario | Phase | Status | Checks | Failures |",
        "|---|---|---|---:|---|",
        *rows,
        "",
        "## Log.txt (AbletonLiveMCP lines)",
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
    EVIDENCE_MD.write_text("\n".join(body), encoding="utf-8")


# ---- entry --------------------------------------------------------------------------------


def _select(cases: list[dict], only: str | None) -> list[dict]:
    if not only:
        return cases
    wanted = {x.strip() for x in only.split(",") if x.strip()}
    unknown = wanted - {c["id"] for c in cases}
    if unknown:
        raise ManifestError(f"--only names unknown scenario(s) {sorted(unknown)}")
    return [c for c in cases if c["id"] in wanted]


def _prior() -> list[dict]:
    try:
        return json.loads(EVIDENCE_JSON.read_text(encoding="utf-8")).get("results", [])
    except (OSError, ValueError):
        return []


def execute(args, state: dict) -> int:
    try:
        cases = load_cases()
        selected = _select(cases, args.only)
    except ManifestError as exc:
        print(f"RESULT: ABORT (exit 2): bad scenario manifest: {exc}")
        return 2
    gaps = sorted(set(registered_tools()) - covered_tools(cases))
    print(f"info {len(cases)} scenarios; {len(gaps)} registered tool(s) without a scenario")
    for name in gaps:
        print(f"FAIL coverage: {name} has no scenario")
    if args.check:
        code = 1 if gaps else 0
        print(f"RESULT: {'FAIL' if code else 'PASS'} (exit {code}): offline manifest check")
        return code
    prior = _prior() if args.only else []
    state["prior_status"] = {r["id"]: r["status"] for r in prior}
    try:
        try:
            fresh = asyncio.run(run_all(selected, args, state))
        except BaseException as exc:
            raise _flatten(exc) from None
    except Abort as exc:
        print(f"RESULT: ABORT (exit 2): {exc}")
        return 2
    except BridgeError as exc:
        print(f"RESULT: ABORT (exit 2): bridge unusable: {exc}")
        return 2
    except (OSError, RuntimeError) as exc:
        print(f"RESULT: ABORT (exit 2): could not run the stdio server: {exc!r}")
        return 2
    results = _merge(prior, fresh)
    state["results"], state["gaps"] = results, gaps
    unlisted = sorted(set(registered_tools()) - set(state.get("listed", [])))
    for name in unlisted:
        print(f"FAIL listing: {name} is registered but the 'all' server did not list it")
    bad = [r for r in results if r["status"] in ("fail", "blocked")]
    code = 1 if bad or gaps or unlisted else 0
    summary = f"{len(results)} scenarios, {len(bad)} failed/blocked, {len(gaps)} coverage gaps"
    print(f"RESULT: {'FAIL' if code else 'PASS'} (exit {code}): {summary}")
    return code


def main(argv=None) -> int:
    p: argparse.ArgumentParser = base_parser(__doc__.split("\n\n")[0])
    p.add_argument("--only", help="comma-separated scenario ids to rerun (results are merged)")
    p.add_argument("--check", action="store_true", help="offline: manifest + coverage only")
    args = p.parse_args(argv)
    buf = io.StringIO()
    state: dict = {}
    with redirect_stdout(_Tee(sys.stdout, buf)):
        code = execute(args, state)
    if "results" in state and not args.no_evidence:
        write_evidence(state["results"], state["gaps"], state, code, buf.getvalue())
        print(f"evidence: {EVIDENCE_MD}")
    return code


if __name__ == "__main__":
    sys.exit(main())
