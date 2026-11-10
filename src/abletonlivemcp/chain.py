"""Build chains of Live's stock audio effects and set parameters from human values.

Live stores most parameters as 0..1 with a nonlinear display ("-18.0 dB", "4.00 : 1", "1.00 kHz").
`set_to_display` finds the stored value whose display matches a target such as "-18 dB". It asks
Live for the display text of 65 candidate values at once (`sample_parameter`, which writes
nothing), narrows the bracket a round at a time, then writes once and reports what Live shows.
`build_chain` checks every device name BEFORE it loads anything.
"""

from __future__ import annotations

import difflib
import re

ROOT = "audio_effects"
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
        self._options: list[int] = []
        lo, hi = float(param["min"]), float(param["max"])
        if param["is_quantized"]:
            self._options = list(range(int(lo), int(hi) + 1))
            self.values = [float(v) for v in self._options]
        else:
            self._goal = parse_display(str(target))
            if self._goal is None:
                raise ChainError(f"{self.name!r}: cannot read a number from {target!r}")
            self.values = _linspace(lo, hi, GRID)

    def feed(self, shown: list[str]) -> None:
        if self.param["is_quantized"]:
            want = _on_off(self.target)
            for v, text in zip(self._options, shown, strict=True):
                if _same_text(text, want):
                    self.pick, self.values = float(v), None
                    return
            raise ChainError(f"{self.name!r}: no option {self.target!r}; options are {shown}")

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


def _solve_and_write(call, loc, solvers: list[_Solver]) -> dict[int, dict]:
    """Sample, then write, a group of parameters. Returns {id(solver): result or error}."""
    out: dict[int, dict] = {}
    active = list(solvers)
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
        writes = [{"parameter": s.param["index"], "value": s.pick} for s in group]
        reply = call("set_device_parameters", {**loc, "writes": writes})["results"]
        for s, r in zip(group, reply, strict=True):
            out[id(s)] = _result(s, r["display"])
    return out


def _result(s: _Solver, display: str) -> dict:
    if s.param["is_quantized"]:
        exact = _same_text(display, _on_off(s.target))
    else:
        got = parse_display(display)
        goal = s._goal[0]
        exact = got is not None and abs(got[0] - goal) <= max(abs(goal) * 0.02, 0.05)
    return {"name": s.name, "requested": s.target, "actual": display, "exact": exact}


def set_parameters(
    call, loc: dict, items: list[tuple[dict, object]]
) -> tuple[list[dict], list[str]]:
    """Set several parameters of one device so Live's own display matches each target.

    Options and switches go first and the numeric parameters are sampled after them, because a
    display can depend on a mode (Echo's time units depend on its sync setting).
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
    done: dict[int, dict] = {}
    done.update(_solve_and_write(call, loc, [s for s in live if s.param["is_quantized"]]))
    done.update(_solve_and_write(call, loc, [s for s in live if not s.param["is_quantized"]]))
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


def _validate(stages) -> None:
    if not isinstance(stages, list) or not 1 <= len(stages) <= MAX_STAGES:
        raise ChainError(f"'stages' must be a list of 1..{MAX_STAGES} stages")
    for s in stages:
        if not isinstance(s, dict) or not isinstance(s.get("device"), str):
            raise ChainError("each stage needs a 'device' name")
        if not isinstance(s.get("params", {}), dict):
            raise ChainError("'params' must be an object of parameter name -> value")


def build_chain(call, track: int, stages: list[dict]) -> dict:
    """Load each stage's stock device onto `track` (appended in order) and set its parameters."""
    _validate(stages)
    listing = call("browser_list", {"root": ROOT, "path": []})
    items = listing["items"] if isinstance(listing, dict) else listing
    names = [i["name"] if isinstance(i, dict) else i for i in items]
    by_lower = {n.lower(): n for n in names}
    missing = [s["device"] for s in stages if s["device"].lower() not in by_lower]
    if missing:
        close = {m: difflib.get_close_matches(m, names, n=3, cutoff=0.5) for m in missing}
        raise ChainError(f"not in Live's {ROOT} browser: {close}")

    results = []
    for s in stages:
        real = by_lower[s["device"].lower()]
        loaded = call("load_item", {"track": track, "root": ROOT, "path": [real]})
        if loaded["devices_after"] != loaded["devices_before"] + 1:
            raise ChainError(f"loading {real!r} did not add exactly one device")
        index = loaded["devices_after"] - 1
        loc = {"track": track, "device": index}
        params = call("device_parameters", loc)
        wanted, problems = [], []
        for pname, value in (s.get("params") or {}).items():
            try:
                wanted.append((_resolve(params, pname), value))
            except ChainError as exc:
                problems.append(str(exc))
        done, more = set_parameters(call, loc, wanted) if wanted else ([], [])
        results.append(
            {"device": real, "index": index, "params": done, "problems": problems + more}
        )
    ok = all(not r["problems"] and all(p["exact"] for p in r["params"]) for r in results)
    return {"track": track, "stages": results, "ok": ok}
