"""Plan and build chains of audio effects and set parameters from human values.

Live stores most parameters as 0..1 with a nonlinear display ("-18.0 dB", "4.00 : 1", "1.00 kHz").
`set_to_display` finds the stored value whose display matches a target such as "-18 dB". It asks
Live for the display text of 65 candidate values at once (`sample_parameter`, which writes
nothing), narrows the bracket a round at a time, then writes once and reports what Live shows.
`make_plan` checks every device and the target BEFORE anything loads; `execute` then runs the
plan once, stops at the first stage that is not fully applied and exact, and returns a receipt.
"""

from __future__ import annotations

import collections
import difflib
import hashlib
import json
import re
import time

from .adapters import adapters_for, known_roles
from .bridge import BridgeError
from .models import ChainPlan, ChainReceipt, ParamResult, PlanStage, StageReceipt, Target

MAX_STAGES = 12
GRID = 65
MAX_ROUNDS = 3

_NUM = re.compile(r"^\s*([-+]?(?:\d+(?:[.,]\d+)?|inf\b))\s*([A-Za-z%]+)?", re.IGNORECASE)
# unit -> (kind, scale to the kind's base unit)
_UNITS = {
    "hz": ("hz", 1.0),
    "khz": ("hz", 1000.0),
    "ms": ("ms", 1.0),
    "s": ("ms", 1000.0),
    "db": ("db", 1.0),
    "%": ("%", 1.0),
    "st": ("st", 1.0),
}


def parse_display(text: str) -> tuple[float, str | None] | None:
    """'1.00 kHz' -> (1000.0, 'hz'); '4.00 : 1' -> (4.0, None); 'inf : 1' -> (inf, None)."""
    m = _NUM.match(str(text))
    if not m:
        return None
    number = m.group(1).lower().replace(",", ".")
    value = float(number.replace("inf", "inf"))  # float() accepts 'inf', '-inf', '+inf'
    unit = (m.group(2) or "").lower()
    if unit in _UNITS:
        kind, scale = _UNITS[unit]
        return value * scale, kind
    return value, None


def _same_text(a, b) -> bool:
    return str(a).strip().lower() == str(b).strip().lower()


def _on_off(value):
    return "on" if value is True else "off" if value is False else value


class ChainError(ValueError):
    pass


CHUNK = 32  # requests or writes per bridge call (the Remote Script accepts up to 64)


def _linspace(lo, hi, n):
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def _chunks(items, size=CHUNK):
    for i in range(0, len(items), size):
        yield items[i : i + size]


class _Solver:
    """Finds the stored value whose display matches one target, a sampling round at a time."""

    def __init__(self, param: dict, target):
        self.param, self.target = param, target
        self.name = param["name"]
        self.rounds = 0
        self.pick: float | None = None
        self.values: list[float] | None = None  # next values to sample; None once decided
        self._goal: tuple[float, str | None] | None = None
        self._text: str | None = None  # set when the target is a word, e.g. a style name
        self._options: list[int] = []
        lo, hi = float(param["min"]), float(param["max"])
        if isinstance(target, dict):  # {"raw": 0.3}: write the stored value as given
            raw = target.get("raw")
            if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not lo <= raw <= hi:
                raise ChainError(f"{self.name!r}: raw value must be a number within {lo:g}..{hi:g}")
            self.pick = float(raw)
        elif param["is_quantized"]:
            self._options = list(range(int(lo), int(hi) + 1))
            self.values = [float(v) for v in self._options]
        else:
            self._goal = parse_display(str(_on_off(target)))
            if self._goal is None:
                self._text = str(_on_off(target))
            self.values = _linspace(lo, hi, GRID)

    def feed(self, shown: list[str]) -> None:
        if self.param["is_quantized"]:
            want = _on_off(self.target)
            for v, text in zip(self._options, shown, strict=True):
                if _same_text(text, want):
                    self.pick, self.values = float(v), None
                    return
            raise ChainError(f"{self.name!r}: no option {self.target!r}; options are {shown}")

        if self._text is not None:  # option names that Live reports as a continuous parameter
            hits = [i for i, t in enumerate(shown) if _same_text(t, self._text)]
            if not hits and all(parse_display(t) is not None for t in shown):
                raise ChainError(f"{self.name!r}: cannot read a number from {self.target!r}")
            if not hits:
                seen = list(dict.fromkeys(shown))
                raise ChainError(f"{self.name!r}: no option {self.target!r}; options are {seen}")
            self.pick, self.values = self.values[hits[len(hits) // 2]], None
            return

        goal_value, goal_kind = self._goal
        parsed = [parse_display(t) for t in shown]
        if any(p is None for p in parsed):
            raise ChainError(f"{self.name!r}: cannot read display {shown[0]!r}")
        nums = [p[0] for p in parsed]
        if self.rounds == 0:
            kind = parsed[0][1]
            if kind is not None and goal_kind is None:
                raise ChainError(f"{self.name!r}: give a unit, e.g. '{self.target} {kind}'")
            if kind is None and goal_kind is not None:
                raise ChainError(f"{self.name!r}: this parameter has no unit; give a plain number")
            if kind != goal_kind:
                raise ChainError(f"{self.name!r}: unit {goal_kind!r} does not match {kind!r}")
            if not min(nums) <= goal_value <= max(nums):
                raise ChainError(
                    f"{self.name!r}: {self.target!r} is outside {min(nums):g}..{max(nums):g}"
                )
        self.rounds += 1
        i = min(range(len(nums)), key=lambda k: abs(nums[k] - goal_value))
        best = self.values[i]
        if abs(nums[i] - goal_value) <= max(abs(goal_value) * 0.005, 0.01) or (
            self.rounds >= MAX_ROUNDS
        ):
            self.pick, self.values = best, None
            return
        # narrow to the neighbours of the best sample and sample that bracket finely
        lo, hi = self.values[max(i - 1, 0)], self.values[min(i + 1, len(self.values) - 1)]
        self.values = _linspace(lo, hi, GRID)


class Refusal(ChainError):
    """The bridge refused a call (a SUCCESSFUL reply shaped {"refused": true, ...}); nothing
    was written by that call."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message} (not applied)")
        self.code, self.message = code, message


class WriteInterrupted(Exception):
    """A settings write stopped partway. `results` are the writes that did complete."""

    def __init__(self, results: list[dict], problems: list[str], cause: Exception):
        super().__init__(str(cause))
        self.results, self.problems, self.cause = results, problems, cause


def _solve_and_write(call, loc, solvers: list[_Solver], out: dict[int, dict]) -> None:
    """Sample, then write, a group of parameters; fills `out` {id(solver): result or error}."""
    active = [s for s in solvers if s.values is not None]  # raw targets need no sampling
    while active:
        nxt = []
        for group in _chunks(active):
            requests = [{"parameter": s.param["index"], "values": s.values} for s in group]
            reply = call("sample_parameters", {**loc, "requests": requests})["results"]
            for s, r in zip(group, reply, strict=True):
                try:
                    s.feed(r["displays"])
                except ChainError as exc:
                    out[id(s)] = {"error": str(exc)}
                    continue
                if s.values is not None:
                    nxt.append(s)
        active = nxt
    ready = [s for s in solvers if id(s) not in out]
    for group in _chunks(ready):
        # writes name parameters by the references the parameter read issued, never by index
        writes = [{"parameter": s.param["ref"], "value": s.pick} for s in group]
        reply = call("set_device_parameters", {"writes": writes})["results"]
        for s, r in zip(group, reply, strict=True):
            out[id(s)] = _result(s, r)


def _result(s: _Solver, written: dict) -> dict:
    """What happened to one setting, from Live's own readback of the write."""
    display, actual_raw = written["display"], written.get("value")
    raw = isinstance(s.target, dict)
    if raw:  # a raw request is exact only if the stored value read back as requested
        span = float(s.param["max"]) - float(s.param["min"])
        exact = isinstance(actual_raw, (int, float)) and (
            abs(actual_raw - s.pick) <= 1e-6 * max(span, 1.0)
        )
    elif s.param["is_quantized"] or s._text is not None:
        exact = _same_text(display, _on_off(s.target))
    else:
        got = parse_display(display)
        goal = s._goal[0]
        exact = got is not None and abs(got[0] - goal) <= max(abs(goal) * 0.02, 0.05)
    return {
        "name": s.name,
        "requested": s.target,
        "original": {"value": s.param.get("value"), "display": s.param.get("display")},
        "actual": display,
        "actual_raw": actual_raw,
        "exact": bool(exact),
        "off_target": not exact,
        "raw": raw,
    }


def set_parameters(
    call, loc: dict, items: list[tuple[dict, object]]
) -> tuple[list[dict], list[str]]:
    """Set several parameters of one device so Live's own display matches each target.

    Options and switches go first and the numeric parameters are sampled after them, because a
    display can depend on a mode (Echo's time units depend on its sync setting). A refusal or
    uncertain failure of a write raises WriteInterrupted carrying the writes already made.
    Returns (results in request order, problems).
    """
    solvers: list[_Solver | None] = []
    problems: list[str] = []
    for param, target in items:
        try:
            solvers.append(_Solver(param, target))
        except ChainError as exc:
            solvers.append(None)
            problems.append(str(exc))
    live = [s for s in solvers if s is not None]
    modes = [s for s in live if s.param["is_quantized"] or s._text is not None]
    done: dict[int, dict] = {}

    def made() -> list[dict]:
        return [
            done[id(s)]
            for s in solvers
            if s is not None and id(s) in done and "error" not in done[id(s)]
        ]

    try:
        _solve_and_write(call, loc, modes, done)
        _solve_and_write(call, loc, [s for s in live if s not in modes], done)
    except (ChainError, BridgeError) as exc:
        raise WriteInterrupted(made(), problems, exc) from exc
    results = []
    for s in solvers:
        if s is None:
            continue
        r = done[id(s)]
        if "error" in r:
            problems.append(r["error"])
        else:
            results.append(r)
    return results, problems


def set_to_display(call, loc: dict, param: dict, target) -> dict:
    """Set one parameter so Live's own display matches `target`."""
    results, problems = set_parameters(call, loc, [(param, target)])
    if problems:
        raise ChainError(problems[0])
    return results[0]


def _resolve(params: list[dict], name: str) -> dict:
    hits = [p for p in params if p["name"].lower() == str(name).lower()]
    if len(hits) == 1:
        return hits[0]
    close = difflib.get_close_matches(str(name), [p["name"] for p in params], n=4, cutoff=0.5)
    raise ChainError(f"no unique parameter {name!r}; similar: {close}")


ROOTS = ("audio_effects", "plugins")  # the only roots a chain may load from
BUILD_DEADLINE = 55.0  # seconds for a whole build; the bridge lease is at most 60 s
LOAD_WAIT = 25.0  # seconds to wait for one load to be observed (Live's own timeout is 20 s)
POLL = 0.25
PLAN_TTL = 900.0
MAX_PLANS = 8


def _validate(stages) -> None:
    if not isinstance(stages, list) or not 1 <= len(stages) <= MAX_STAGES:
        raise ChainError(f"'stages' must be a list of 1..{MAX_STAGES} stages")
    for s in stages:
        if not isinstance(s, dict) or not (
            isinstance(s.get("device"), str) or isinstance(s.get("role"), str)
        ):
            raise ChainError("each stage needs a 'role' (with 'intent') or an exact 'device' name")
        if "device" in s and "path" in s and not (isinstance(s["path"], list) and s["path"]):
            raise ChainError("'path' must be a non-empty list of browser names")
        if not isinstance(s.get("params", {}), dict):
            raise ChainError("'params' must be an object of parameter name -> value")


def checked(call):
    """Wrap a bridge call so a refusal reply (a successful result) raises Refusal."""

    def run(method, params=None):
        result = call(method, params)
        if isinstance(result, dict) and result.get("refused") is True:
            raise Refusal(str(result.get("code")), str(result.get("message")))
        return result

    return run


def _digest(*parts) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf8")).hexdigest()


def make_plan(call, stages: list[dict], track: int, preferences: dict, resolver) -> ChainPlan:
    """Read-only: resolve stages to concrete devices for the empty audio track at index `track`.

    `resolver` is resolve.plan_chain (injected: resolve imports this module). Nothing is loaded:
    plugin controls stay `unverified_until_loaded`. Returns a ChainPlan."""
    call = checked(call)
    _validate(stages)
    if isinstance(track, bool) or not isinstance(track, int) or track < 0:
        raise ChainError("'track' must be a track index >= 0")
    generation = call("session_info")["generation"]
    listing = call("tracks")
    if track >= len(listing):
        raise ChainError(f"track {track} does not exist ({len(listing)} tracks)")
    row = listing[track]
    if row["has_midi_input"] or row["devices"]:
        raise ChainError("the target must be an empty regular audio track (no devices yet)")
    target = Target(index=track, name=row["name"], generation=generation)
    role_at = [i for i, s in enumerate(stages) if "role" in s]
    resolved = resolver(call, [stages[i] for i in role_at], preferences) if role_at else None
    out: list[PlanStage] = []
    report: list[dict] = []
    stock = None
    for i, s in enumerate(stages):
        if i in role_at:
            k = role_at.index(i)
            c, rep = resolved["stages"][k], resolved["report"][k]
            omitted = tuple(n for n in rep["notes"] if "skipped" in n)
            notes = tuple(n for n in rep["notes"] if "skipped" not in n)
            root = c.get("root", ROOTS[0])
            path = tuple(c.get("path") or [c["device"]])
            out.append(
                PlanStage(
                    role=rep["role"],
                    device=c["device"],
                    root=root,
                    path=path,
                    params=c["params"],
                    omitted=omitted,
                    notes=notes,
                )
            )
            report.append(rep)
            continue
        root = s.get("root", ROOTS[0] if "path" not in s else "plugins")
        if root not in ROOTS:
            raise ChainError(f"only {list(ROOTS)} devices can be built, not {root!r}")
        if "path" in s:
            path = tuple(s["path"])
        else:
            if stock is None:
                items = call("browser_list", {"root": ROOTS[0], "path": []})["items"]
                stock = {x["name"].lower(): x["name"] for x in items}
            real = stock.get(s["device"].lower())
            if real is None:
                close = difflib.get_close_matches(s["device"], list(stock.values()), 3, 0.5)
                raise ChainError(f"not in Live's {ROOTS[0]} browser: {s['device']!r}; {close}")
            path = (real,)
        out.append(
            PlanStage(device=s["device"], root=root, path=path, params=s.get("params") or {})
        )
        report.append({"device": s["device"], "exact": True})
    fingerprint = _digest(
        [o.model_dump() for o in out],
        target.model_dump(),
        preferences,
        [repr(a) for r in known_roles() for a in adapters_for(r)],
    )
    return ChainPlan(
        plan_id=fingerprint[:24],
        fingerprint=fingerprint,
        target=target,
        stages=tuple(out),
        report=tuple(report),
        intent_complete=not any(o.omitted for o in out),
        expires_in=PLAN_TTL,
    )


class PlanStore:
    """Bounded in-memory plans. A plan builds once: later use returns its receipt or refuses."""

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._plans: collections.OrderedDict[str, dict] = collections.OrderedDict()

    def add(self, plan: ChainPlan) -> None:
        now = self._clock()
        for key in [k for k, v in self._plans.items() if v["expires"] <= now]:
            del self._plans[key]
        if plan.plan_id in self._plans:  # same reviewed content: keep its state
            return
        self._plans[plan.plan_id] = {
            "plan": plan,
            "state": "planned",
            "receipt": None,
            "expires": now + PLAN_TTL,
        }
        while len(self._plans) > MAX_PLANS:
            self._plans.popitem(last=False)

    def claim(self, plan_id: str):
        """('run', plan) once, then ('receipt', receipt). Unknown/expired/running -> ChainError."""
        entry = self._plans.get(plan_id) if isinstance(plan_id, str) else None
        if entry is not None and entry["expires"] <= self._clock():
            del self._plans[plan_id]
            entry = None
        if entry is None:
            raise ChainError("unknown or expired plan_id; plan again (nothing was built)")
        if entry["state"] == "building":
            raise ChainError("this plan is already being built; read its operation, do not retry")
        if entry["state"] == "built":
            return "receipt", entry["receipt"]
        entry["state"] = "building"
        return "run", entry["plan"]

    def release(self, plan_id: str) -> None:
        """Nothing was started (a precondition failed): the plan may be tried again."""
        entry = self._plans.get(plan_id)
        if entry is not None and entry["state"] == "building":
            entry["state"] = "planned"

    def finish(self, plan_id: str, receipt: ChainReceipt) -> None:
        entry = self._plans[plan_id]
        entry["state"], entry["receipt"] = "built", receipt


def verify_target(call, plan: ChainPlan) -> str:
    """Fresh preconditions: same Set, and the planned track is still the same empty audio track.
    Returns a track reference for the loads. Raises ChainError before anything is written."""
    call = checked(call)
    t = plan.target
    if call("session_info")["generation"] != t.generation:
        raise ChainError("the Set or bridge session changed since planning; plan again")
    listing = call("tracks")
    row = listing[t.index] if t.index < len(listing) else None
    if row is None or row["name"] != t.name or row["has_midi_input"] or row["devices"]:
        raise ChainError("the target track changed since planning; plan again (nothing built)")
    return row["ref"]


def _wait_ready(call, op: dict, sleep, clock) -> dict:
    """Poll the load operation; a pending/unknown state is never absence and never reloads."""
    limit = clock() + LOAD_WAIT
    while op["state"] == "pending" and clock() < limit:
        sleep(POLL)
        op = call("operation", {"operation": op["operation"]})
    return op


def _run_stage(call, plan, i, track_ref, previous, sleep, clock):
    """Load one stage and set its parameters. Returns (StageReceipt, stop_reason or None)."""
    st, t = plan.stages[i], plan.target

    def receipt(outcome, reason=None, **kw):
        return StageReceipt(index=i, device=st.device, outcome=outcome, reason=reason, **kw)

    load = {"track": track_ref, "root": st.root, "path": list(st.path)}
    if previous:
        load["after"] = previous  # must be exactly the prefix this build produced
    op = None
    try:
        op = call("load_item", load)
        op = _wait_ready(call, op, sleep, clock)
    except Refusal as exc:
        return receipt("not_applied", exc.code, problems=(exc.message,)), exc.code
    except BridgeError as exc:
        outcome = "unknown" if exc.may_have_applied else "not_applied"
        name = op["operation"] if op else None
        return receipt(outcome, exc.kind, operation=name, problems=(str(exc),)), f"load_{outcome}"
    name = op["operation"]
    if op["state"] != "ready":
        failed = op["state"] == "failed"
        reason = f"load_{op['state']}:{op.get('reason')}"
        return receipt("not_applied" if failed else "unknown", reason, operation=name), reason
    index = len(op["devices_after"]) - 1
    try:
        row = call("tracks")[t.index]
        if (
            row["name"] != t.name
            or [d["class_name"] for d in row["devices"]] != op["devices_after"]
        ):
            raise ChainError("the track no longer matches the loaded device")
        params = call("device_parameters", {"track": t.index, "device": index})
    except (ChainError, BridgeError, IndexError) as exc:
        rec = receipt(
            "applied", "target_changed", operation=name, device_index=index, problems=(str(exc),)
        )
        return rec, "target_changed"
    wanted, problems = [], []
    for pname, value in st.params.items():
        try:
            q = _resolve(params, pname)
            if not q.get("is_enabled", True):
                raise ChainError(f"{pname!r} is disabled or controlled elsewhere; not overriding")
            wanted.append((q, value))
        except ChainError as exc:
            problems.append(str(exc))
    done: list[dict] = []
    reason = None
    try:
        if wanted and not problems:  # an unresolved setting stops the stage before any write
            done, more = set_parameters(call, {"track": t.index, "device": index}, wanted)
            problems += more
    except WriteInterrupted as exc:
        done, problems = exc.results, problems + exc.problems + [str(exc.cause)]
        uncertain = isinstance(exc.cause, BridgeError) and exc.cause.may_have_applied
        reason = "settings_unknown" if uncertain else "settings_refused"
    results = tuple(ParamResult(**r) for r in done)
    if reason is None and (problems or not all(r.exact for r in results)):
        reason = "settings_unresolved" if problems else "off_target"
    outcome = "unknown" if reason == "settings_unknown" else "applied"
    rec = receipt(
        outcome,
        reason,
        operation=name,
        device_index=index,
        params=results,
        problems=tuple(problems),
    )
    return rec, reason


def execute(call, plan: ChainPlan, track_ref: str, sleep=time.sleep, clock=time.monotonic):
    """Run a plan stage by stage; stop at the first stage that is not fully applied and exact.

    Never retries, deletes, undoes or loads a substitute: a stopped build keeps whatever was
    applied and says so. Returns a ChainReceipt."""
    call = checked(call)
    started = clock()
    stages: list[StageReceipt] = []
    completed: list[int] = []
    stop: tuple[int, str] | None = None
    previous = None
    for i in range(len(plan.stages)):
        if clock() - started > BUILD_DEADLINE:
            stop = (i, "deadline")
            break
        rec, reason = _run_stage(call, plan, i, track_ref, previous, sleep, clock)
        stages.append(rec)
        if reason:
            stop = (i, reason)
            break
        completed.append(i)
        previous = rec.operation
    for i in range(len(stages), len(plan.stages)):
        stages.append(
            StageReceipt(
                index=i, device=plan.stages[i].device, outcome="not_applied", reason="not_attempted"
            )
        )
    applied = any(r.outcome == "applied" for r in stages)
    unknown = tuple(f"stage {r.index}: {r.reason}" for r in stages if r.outcome == "unknown")
    if stop is None:
        status = "complete"
    elif applied:
        status = "partial"
    elif unknown:
        status = "pending"
    else:
        status = "failed"
    return ChainReceipt(
        plan_id=plan.plan_id,
        status=status,
        intent_fulfilled=stop is None and plan.intent_complete,
        target=plan.target,
        completed=tuple(completed),
        stopped_at=stop[0] if stop else None,
        stop_reason=stop[1] if stop else None,
        omitted=tuple(o for s in plan.stages for o in s.omitted),
        unknown=unknown,
        stages=tuple(stages),
    )
