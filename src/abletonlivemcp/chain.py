"""Build chains of Live's stock audio effects and set parameters from human values.

Live stores most parameters as 0..1 with a nonlinear display ("-18.0 dB", "4.00 : 1", "1.00 kHz").
`set_to_display` finds the stored value whose display matches a target such as "-18 dB". It asks
Live for the display text of 65 candidate values at once (`sample_parameter`, which writes
nothing), narrows the bracket a round at a time, then writes once and reports what Live shows.
`build_chain` checks every device name BEFORE it loads anything.
"""

from __future__ import annotations

import difflib
import math
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


def _sample(call, loc, param, values):
    r = call("sample_parameter", {**loc, "parameter": param["index"], "values": values})
    return r["displays"]


def _linspace(lo, hi, n):
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def set_to_display(call, loc: dict, param: dict, target) -> dict:
    """Set one parameter so Live's own display matches `target`. Returns requested/actual/exact."""
    name = param["name"]

    def put(v):
        return call("set_device_parameter", {**loc, "parameter": param["index"], "value": v})

    if param["is_quantized"]:
        options = list(range(int(param["min"]), int(param["max"]) + 1))
        shown = _sample(call, loc, param, [float(v) for v in options])
        want = _on_off(target)
        for v, text in zip(options, shown, strict=True):
            if _same_text(text, want):
                return {
                    "name": name,
                    "requested": target,
                    "actual": put(float(v))["display"],
                    "exact": True,
                }
        raise ChainError(f"{name!r}: no option {target!r}; options are {shown}")

    goal = parse_display(str(target))
    if goal is None:
        raise ChainError(f"{name!r}: cannot read a number from {target!r}")
    goal_value, goal_kind = goal

    lo, hi = float(param["min"]), float(param["max"])
    values = _linspace(lo, hi, GRID)
    shown = _sample(call, loc, param, values)
    parsed = [parse_display(t) for t in shown]
    if any(p is None for p in parsed):
        raise ChainError(f"{name!r}: cannot read display {shown[0]!r}")
    kind = parsed[0][1]
    if kind is not None and goal_kind is None:
        raise ChainError(f"{name!r}: give a unit, e.g. '{target} {kind}'")
    if kind is None and goal_kind is not None:
        raise ChainError(f"{name!r}: this parameter has no unit; give a plain number")
    if kind != goal_kind:
        raise ChainError(f"{name!r}: unit {goal_kind!r} does not match {kind!r}")
    nums = [p[0] for p in parsed]
    low, high = min(nums), max(nums)
    if not low <= goal_value <= high:
        raise ChainError(f"{name!r}: {target!r} is outside {low:g}..{high:g}")

    tol = max(abs(goal_value) * 0.005, 0.01)
    best_v, best_err = values[0], math.inf
    for _ in range(MAX_ROUNDS):
        i = min(range(len(nums)), key=lambda k: abs(nums[k] - goal_value))
        best_v, best_err = values[i], abs(nums[i] - goal_value)
        if best_err <= tol:
            break
        # narrow to the neighbours of the best sample and sample that bracket finely
        lo, hi = values[max(i - 1, 0)], values[min(i + 1, len(values) - 1)]
        values = _linspace(lo, hi, GRID)
        shown = _sample(call, loc, param, values)
        nums = [parse_display(t)[0] for t in shown]
    reading = put(best_v)
    final = parse_display(reading["display"])[0]
    exact = abs(final - goal_value) <= max(abs(goal_value) * 0.02, 0.05)
    return {"name": name, "requested": target, "actual": reading["display"], "exact": exact}


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
        done, problems = [], []
        for pname, value in (s.get("params") or {}).items():
            try:
                done.append(set_to_display(call, loc, _resolve(params, pname), value))
            except ChainError as exc:
                problems.append(str(exc))
        results.append({"device": real, "index": index, "params": done, "problems": problems})
    return {"track": track, "stages": results, "ok": not any(r["problems"] for r in results)}
