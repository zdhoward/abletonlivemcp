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
from .models import ParamResult, PlanStage, StageReceipt
from .models_devices import (
    REF_KIND,
    BuildPlan,
    BuildReceipt,
    BuildTarget,
    MacroGroup,
    container_kind,
)

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


# ---- plans: what would be built, checked before anything loads -----------------------------

ROOTS = ("audio_effects", "plugins")  # the proven route (empty regular audio track, load_item)
FX_ROOTS = ROOTS + ("max_for_live", "user_library", "packs", "current_project", "user_folders")
SOURCE_ROOTS = ("instruments", "sounds", "drums", "samples")  # first stage, empty MIDI container
MIDI_ROOTS = ("midi_effects",)
LOAD_ROOTS = FX_ROOTS + SOURCE_ROOTS + MIDI_ROOTS
PAD_ROOTS = ("samples", "sounds", "instruments", "user_library", "packs", "current_project")
MIDI_KINDS = ("midi_track", "chain", "drum_pad")
BUILD_DEADLINE = 55.0  # seconds for a whole build; the bridge lease is at most 60 s
LOAD_WAIT = 25.0  # seconds to wait for one load to be observed (Live's own timeout is 20 s)
POLL = 0.25
PLAN_TTL = 900.0
MAX_PLANS = 8
MAX_PADS = 16  # drum builder cap (the final proof uses three roles)
RACK_DEVICE = "Audio Effect Rack"
DRUM_RACK = "Drum Rack"


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


def _loc(track, path) -> dict:
    return {"track": track, "path": list(path)} if path else {"track": track}


def read_target(call, track, path=()) -> tuple[str, str | None, tuple[str, ...], list[dict]]:
    """(kind, name, device class names, device rows) of a container, read fresh."""
    info = call("device_list", _loc(track, path))
    owner = info["owner"]
    if owner.get("is_group"):
        raise ChainError("a group track holds no devices")
    if path:
        kind = "drum_pad" if isinstance(path[-1], str) else "chain"
        name = info.get("container_name")
    elif owner["kind"] == "track":
        kind = "midi_track" if owner["has_midi_input"] else "audio_track"
        name = owner["name"]
    else:
        kind = "return" if owner["kind"] == "return_track" else "master"
        name = owner["name"]
    rows = info["devices"]
    return kind, name, tuple(d["class_name"] for d in rows), rows


def _target(call, track, path) -> tuple[BuildTarget, list[dict]]:
    if isinstance(track, bool) or not isinstance(track, (int, str)):
        raise ChainError("'track' must be a track index, 'return:N' or 'master'")
    generation = call("session_info")["generation"]
    kind, name, devices, rows = read_target(call, track, tuple(path or ()))
    target = BuildTarget(
        track=track, path=tuple(path or ()), kind=kind, name=name, generation=generation,
        devices=devices,
    )  # fmt: skip
    return target, rows


def _issue(call, kind: str, track, path, expect_name=None) -> str:
    sel = {"kind": kind, **_loc(track, path)}
    if expect_name is not None:
        sel["expect_name"] = expect_name
    row = call("ref_issue", {"targets": [sel]})["refs"][0]
    if expect_name is not None and row.get("name") != expect_name:
        raise Refusal("name_mismatch", f"expected {expect_name!r}, found {row.get('name')!r}")
    return row["ref"]


def gate(call, names) -> tuple[str, ...]:
    """Plan-time capability gate: refuse an unsupported/quarantined ability before anything
    loads; return the capabilities that are still unverified (reported, not hidden)."""
    names = sorted(set(names))
    if not names:
        return ()
    rows = call("device_capabilities", {"names": names})
    for n in names:
        row = rows.get(n) or {}
        if row.get("state") not in ("supported", "unverified"):
            raise Refusal("unsupported", f"{n} is {row.get('state')}: {row.get('reason')}")
    return tuple(n for n in names if rows[n].get("state") == "unverified")


def _legacy(target: BuildTarget, stages) -> bool:
    """The proven route: audio effects onto an empty regular audio track."""
    return (
        target.kind == "audio_track" and not target.devices and all(s.root in ROOTS for s in stages)
    )


class _Stock:
    """Top-level names of browser roots, read once per plan."""

    def __init__(self, call):
        self.call, self.seen = call, {}

    def find(self, root: str, name: str) -> str:
        if root not in self.seen:
            items = self.call("browser_list", {"root": root, "path": []})["items"]
            self.seen[root] = {x["name"].lower(): x["name"] for x in items}
        real = self.seen[root].get(name.lower())
        if real is None:
            close = difflib.get_close_matches(name, list(self.seen[root].values()), 3, 0.5)
            raise ChainError(f"not in Live's {root} browser: {name!r}; similar: {close}")
        return real


def _check_roots(stages, target: BuildTarget) -> None:
    for i, st in enumerate(stages):
        if st.root not in LOAD_ROOTS:
            raise ChainError(f"only {list(LOAD_ROOTS)} items can be built, not {st.root!r}")
        if st.root in SOURCE_ROOTS and (i or target.devices or target.kind not in MIDI_KINDS):
            raise ChainError(
                f"{st.root} items load only as the first stage on an empty MIDI track, chain or pad"
            )
        if st.root in MIDI_ROOTS and target.kind not in ("midi_track", "chain"):
            raise ChainError("MIDI effects load only onto a MIDI track or a chain")


def _finish_plan(mode, target, stages, report, unverified, extra=(), **kw) -> BuildPlan:
    fingerprint = _digest(
        mode,
        [o.model_dump() for o in stages],
        target.model_dump(),
        [repr(a) for r in known_roles() for a in adapters_for(r)],
        *extra,
    )
    return BuildPlan(
        plan_id=fingerprint[:24],
        fingerprint=fingerprint,
        mode=mode,
        target=target,
        stages=tuple(stages),
        report=tuple(report),
        intent_complete=not any(o.omitted for o in stages),
        unverified=tuple(unverified),
        expires_in=PLAN_TTL,
        **kw,
    )


def make_plan(
    call, stages: list[dict], track, preferences: dict, resolver, path=(), append=False
) -> BuildPlan:
    """Read-only: resolve stages to concrete devices for a device container (a track, return,
    master, rack chain or drum pad). `resolver` is resolve.plan_chain (injected: resolve
    imports this module). Nothing is loaded: plugin controls stay `unverified_until_loaded`."""
    call = checked(call)
    _validate(stages)
    target, _rows = _target(call, track, path)
    if target.devices and not append:
        raise ChainError("the target must be empty (pass append=true to add after its devices)")
    role_at = [i for i, s in enumerate(stages) if "role" in s]
    resolved = resolver(call, [stages[i] for i in role_at], preferences) if role_at else None
    out: list[PlanStage] = []
    report: list[dict] = []
    stock = _Stock(call)
    for i, s in enumerate(stages):
        if i in role_at:
            k = role_at.index(i)
            c, rep = resolved["stages"][k], resolved["report"][k]
            out.append(
                PlanStage(
                    role=rep["role"],
                    device=c["device"],
                    root=c.get("root", ROOTS[0]),
                    path=tuple(c.get("path") or [c["device"]]),
                    params=c["params"],
                    omitted=tuple(n for n in rep["notes"] if "skipped" in n),
                    notes=tuple(n for n in rep["notes"] if "skipped" not in n),
                )
            )
            report.append(rep)
            continue
        root = s.get("root", ROOTS[0] if "path" not in s else "plugins")
        if root not in LOAD_ROOTS:
            raise ChainError(f"only {list(LOAD_ROOTS)} items can be built, not {root!r}")
        path_ = tuple(s["path"]) if "path" in s else (stock.find(root, s["device"]),)
        out.append(
            PlanStage(device=s["device"], root=root, path=path_, params=s.get("params") or {})
        )
        report.append({"device": s["device"], "exact": True})
    _check_roots(out, target)
    unverified = () if _legacy(target, out) else gate(call, ["load." + target.kind])
    return _finish_plan("chain", target, out, report, unverified, (preferences,))


def make_rack_plan(call, track, path, groups: list[dict]) -> BuildPlan:
    """FX-rack mode: wrap the container's audio effects (in order) into a new Audio Effect Rack,
    set macro values, and list the macro mappings the user makes by hand (12.2 has no mapping
    API). Refused unless chain placement (load, insert_chain, move into a chain) is allowed."""
    call = checked(call)
    target, rows = _target(call, track, path)
    if target.kind not in ("audio_track", "midi_track", "return", "master"):
        raise ChainError("FX-rack mode wraps the devices of a track, return or master")
    if not rows or any(d.get("type") != "audio_effect" for d in rows):
        raise ChainError("FX-rack mode needs one or more audio effects (and nothing else)")
    names = [d["name"] for d in rows]
    steps: list[str] = []
    for g in groups:
        label = g.get("label") or f"Macro {g['macro']}"
        if g.get("label"):
            steps.append(f"Rename Macro {g['macro']} to {label!r} (no rename API on 12.2).")
        for m in g.get("targets") or []:
            if m["device"] >= len(rows):
                raise ChainError(f"macro {g['macro']}: device {m['device']} is not wrapped")
            span = f" from {m.get('min')} to {m.get('max')}" if m.get("min") is not None else ""
            where = f"{names[m['device']]} > {m['parameter']}"
            steps.append(
                f"Map {where} to Macro {g['macro']} ({label}){span}: right-click the parameter"
                " > Map to Macro, then set Min/Max in Map mode."
            )
    rack = PlanStage(
        device=RACK_DEVICE,
        root="audio_effects",
        path=(_Stock(call).find("audio_effects", RACK_DEVICE),),
    )
    unverified = gate(call, ["load." + target.kind, "rack.insert_chain", "device.move_into_chain"])
    report = [{"wrap": names, "groups": len(groups)}]
    return _finish_plan(
        "fx_rack", target, [rack], report, unverified, (groups,),
        groups=tuple(MacroGroup(**g) for g in groups), manual_steps=tuple(steps),
    )  # fmt: skip


def make_drum_plan(call, track, pads: list[dict]) -> BuildPlan:
    """Drum builder: an empty Drum Rack on an empty MIDI track, then one browser item per pad.
    Capped at MAX_PADS; every pad item is checked in its browser folder at plan time."""
    call = checked(call)
    if not 1 <= len(pads) <= MAX_PADS:
        raise ChainError(f"'pads' must hold 1..{MAX_PADS} pads")
    notes = [p["note"] for p in pads]
    if len(set(notes)) != len(notes):
        raise ChainError("each pad note may appear once")
    target, _rows = _target(call, track, ())
    if target.kind != "midi_track" or target.devices:
        raise ChainError("the drum builder needs an empty regular MIDI track")
    stages = [
        PlanStage(
            device=DRUM_RACK,
            root="instruments",
            path=(_Stock(call).find("instruments", DRUM_RACK),),
        )
    ]
    containers: list[tuple] = [()]
    report: list[dict] = [{"device": DRUM_RACK}]
    folders: dict[tuple, dict] = {}
    for p in pads:
        if p["root"] not in PAD_ROOTS:
            raise ChainError(f"pad items load from {list(PAD_ROOTS)}, not {p['root']!r}")
        key = (p["root"], tuple(p["path"][:-1]))
        if key not in folders:
            listing = call("browser_list", {"root": key[0], "path": list(key[1])})
            folders[key] = {
                "names": {x["name"] for x in listing["items"] if x.get("is_loadable", True)},
                "truncated": bool(listing.get("truncated")),
            }
        seen = folders[key]
        found = p["path"][-1] in seen["names"]
        if not found and not seen["truncated"]:
            raise ChainError(f"pad {p['note']}: {p['path'][-1]!r} is not in that browser folder")
        stages.append(PlanStage(device=p["path"][-1], root=p["root"], path=tuple(p["path"])))
        containers.append((0, f"pad:{p['note']}"))
        report.append({"note": p["note"], "item_checked": found})
    unverified = gate(call, ["load.midi_track", "load.drum_pad"])
    return _finish_plan(
        "drum_rack", target, stages, report, unverified, (containers,), containers=tuple(containers)
    )


class PlanStore:
    """Bounded in-memory plans. A plan builds once: later use returns its receipt or refuses."""

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._plans: collections.OrderedDict[str, dict] = collections.OrderedDict()

    def add(self, plan: BuildPlan) -> None:
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

    def peek(self, plan_id: str):
        entry = self._plans.get(plan_id) if isinstance(plan_id, str) else None
        return entry["plan"] if entry else None

    def release(self, plan_id: str) -> None:
        """Nothing was started (a precondition failed): the plan may be tried again."""
        entry = self._plans.get(plan_id)
        if entry is not None and entry["state"] == "building":
            entry["state"] = "planned"

    def finish(self, plan_id: str, receipt: BuildReceipt) -> None:
        entry = self._plans[plan_id]
        entry["state"], entry["receipt"] = "built", receipt


def verify_target(call, plan: BuildPlan) -> str:
    """Fresh preconditions: same Set, and the planned container still reads exactly as planned.
    Returns its reference for the loads. Raises ChainError before anything is written."""
    call = checked(call)
    t = plan.target
    if call("session_info")["generation"] != t.generation:
        raise ChainError("the Set or bridge session changed since planning; plan again")
    try:
        kind, name, devices, _rows = read_target(call, t.track, t.path)
    except BridgeError:
        raise
    except (ChainError, Exception) as exc:  # a vanished container reads as changed
        raise ChainError(f"the target changed since planning; plan again ({exc})") from exc
    if (kind, name, devices) != (t.kind, t.name, t.devices):
        raise ChainError("the target changed since planning; plan again (nothing built)")
    return _issue(call, REF_KIND[t.kind], t.track, t.path)


# ---- build -----------------------------------------------------------------------------------


def _wait_ready(call, op: dict, sleep, clock) -> dict:
    """Poll the load operation; a pending/unknown state is never absence and never reloads."""
    limit = clock() + LOAD_WAIT
    while op["state"] == "pending" and clock() < limit:
        sleep(POLL)
        op = call("operation", {"operation": op["operation"]})
    return op


def _layout(op: dict) -> list | None:
    if op.get("devices_after") is not None:
        return list(op["devices_after"])
    return list((op.get("result") or {}).get("devices_after") or []) or None


def _run_stage(call, plan, i, ref, previous, sleep, clock, legacy):
    """Load one stage and set its parameters. Returns (StageReceipt, stop_reason or None)."""
    st, t = plan.stages[i], plan.target
    sub = plan.containers[i] if plan.containers else ()
    path = tuple(t.path) + tuple(sub)

    def receipt(outcome, reason=None, **kw):
        return StageReceipt(index=i, device=st.device, outcome=outcome, reason=reason, **kw)

    op = None
    try:
        if sub:  # a container that exists only after an earlier stage (a drum pad)
            ref = _issue(call, container_kind(t.track, path), t.track, path)
        load = {"root": st.root, "path": list(st.path)}
        if legacy:
            method, load["track"] = "load_item", ref
        else:
            method = "load_device"
            load["targets"] = [{"kind": container_kind(t.track, path), "ref": ref}]
            if previous is None and t.devices and not sub:
                load["append"] = True  # planned with append: add after the planned devices
        if previous:
            load["after"] = previous  # must be exactly the prefix this build produced
        op = call(method, load)
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
    layout = _layout(op) or []
    index = len(layout) - 1
    loc = _loc(t.track, path + (index,))
    try:
        _kind, cname, devices, _rows = read_target(call, t.track, path)
        if (not sub and cname != t.name) or list(devices) != layout:
            raise ChainError("the target no longer matches the loaded device")
        params = call("device_parameters", loc)
    except (ChainError, BridgeError, IndexError, KeyError) as exc:
        rec = receipt(
            "applied", "target_changed", operation=name, device_index=index, problems=(str(exc),)
        )
        return rec, "target_changed"
    return _apply_params(call, receipt, loc, params, st.params.items(), name, index)


def _apply_params(call, receipt, loc, params, wanted_items, name, index):
    wanted, problems = [], []
    for pname, value in wanted_items:
        try:
            q = params[pname] if isinstance(pname, int) else _resolve(params, pname)
            if not q.get("is_enabled", True):
                raise ChainError(
                    f"{q['name']!r} is disabled or controlled elsewhere; not overriding"
                )
            wanted.append((q, value))
        except (ChainError, IndexError) as exc:
            problems.append(str(exc))
    done: list[dict] = []
    reason = None
    try:
        if wanted and not problems:  # an unresolved setting stops the stage before any write
            done, more = set_parameters(call, loc, wanted)
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
        outcome, reason, operation=name, device_index=index, params=results,
        problems=tuple(problems),
    )  # fmt: skip
    return rec, reason


def _status(stages, stop) -> str:
    if stop is None:
        return "complete"
    if any(r.outcome == "applied" for r in stages):
        return "partial"
    return "pending" if any(r.outcome == "unknown" for r in stages) else "failed"


def _receipt(plan: BuildPlan, stages, completed, stop, names=None) -> BuildReceipt:
    total = names or [s.device for s in plan.stages]
    for i in range(len(stages), len(total)):
        stages.append(
            StageReceipt(index=i, device=total[i], outcome="not_applied", reason="not_attempted")
        )
    return BuildReceipt(
        plan_id=plan.plan_id,
        mode=plan.mode,
        status=_status(stages, stop),
        intent_fulfilled=stop is None and plan.intent_complete,
        target=plan.target,
        completed=tuple(completed),
        stopped_at=stop[0] if stop else None,
        stop_reason=stop[1] if stop else None,
        omitted=tuple(o for s in plan.stages for o in s.omitted),
        unknown=tuple(f"stage {r.index}: {r.reason}" for r in stages if r.outcome == "unknown"),
        stages=tuple(stages),
        unverified=plan.unverified,
        manual_steps=plan.manual_steps,
    )


def execute(call, plan: BuildPlan, ref: str, sleep=time.sleep, clock=time.monotonic):
    """Run a plan stage by stage; stop at the first stage that is not fully applied and exact.

    Never retries, deletes, undoes or loads a substitute: a stopped build keeps whatever was
    applied and says so. Returns a BuildReceipt."""
    call = checked(call)
    if plan.mode == "fx_rack":
        return _execute_rack(call, plan, ref, sleep, clock)
    started = clock()
    stages: list[StageReceipt] = []
    completed: list[int] = []
    stop: tuple[int, str] | None = None
    previous = None
    legacy = _legacy(plan.target, plan.stages)
    for i in range(len(plan.stages)):
        if clock() - started > BUILD_DEADLINE:
            stop = (i, "deadline")
            break
        same = not plan.containers or i == 0 or plan.containers[i] == plan.containers[i - 1]
        rec, reason = _run_stage(
            call, plan, i, ref, previous if same else None, sleep, clock, legacy
        )
        stages.append(rec)
        if reason:
            stop = (i, reason)
            break
        completed.append(i)
        previous = rec.operation
    return _receipt(plan, stages, completed, stop)


def _values(call, track, path) -> list:
    return [r["value"] for r in call("device_parameters", _loc(track, path))]


def _execute_rack(call, plan: BuildPlan, ref, sleep, clock) -> BuildReceipt:
    """Load the rack after the devices, give it a chain, move each device into that chain in
    order (refs re-issued per move), check order and values, then set macro values."""
    t = plan.target
    n = len(t.devices)
    base = tuple(t.path)
    names = [plan.stages[0].device] + [f"move {c}" for c in t.devices] + ["macros"]
    stages: list[StageReceipt] = []
    completed: list[int] = []

    def stage(i, outcome, reason=None, problems=(), **kw):
        rec = StageReceipt(
            index=i, device=names[i], outcome=outcome, reason=reason, problems=tuple(problems),
            **kw,
        )  # fmt: skip
        stages.append(rec)
        if outcome != "applied":
            return _receipt(plan, stages, completed, (i, reason), names)
        completed.append(i)
        return None

    rec, reason = _run_stage(call, plan, 0, ref, None, sleep, clock, False)
    stages.append(rec)
    if reason:
        return _receipt(plan, stages, completed, (0, reason), names)
    completed.append(0)
    rack_path = base + (n,)
    try:
        before = [_values(call, t.track, base + (j,)) for j in range(n)]
        dev_names = [r["name"] for r in call("device_list", _loc(t.track, t.path))["devices"]]
        if not call("rack", _loc(t.track, rack_path))["chains"]:
            rack_ref = _issue(call, "device", t.track, rack_path)
            made = call("set_rack", {"device": rack_ref, "insert_chain": {"index": 0}})
            if made.get("status") != "complete":
                raise ChainError(f"insert_chain: {made.get('error')}")
    except (Refusal, BridgeError, ChainError, KeyError) as exc:
        return stage(1, "not_applied", "no_chain", (str(exc),))
    for k in range(n):
        i = k + 1
        targets = []
        try:
            dev = _issue(call, "device", t.track, base + (0,), dev_names[k])
            dest = _issue(call, "chain", t.track, base + (n - k, 0))
            targets = [
                {"kind": "device", "ref": dev, "expect_name": dev_names[k]},
                {"kind": "chain", "ref": dest},
            ]
            call("move_device", {"targets": targets, "position": k})
        except Refusal as exc:
            return stage(i, "not_applied", exc.code, (exc.message,))
        except BridgeError as exc:
            sent = bool(targets) and exc.may_have_applied
            outcome = "unknown" if sent else "not_applied"
            return stage(i, outcome, f"move_{outcome}", (str(exc),))
        stage(i, "applied", device_index=k)
    i = n + 1
    inner = base + (0, 0)
    problems: list[str] = []
    try:
        moved = call("device_list", _loc(t.track, inner))["devices"]
        if [d["class_name"] for d in moved] != list(t.devices):
            problems.append("device order inside the rack chain differs from the original")
        for j in range(n):
            if _values(call, t.track, inner + (j,)) != before[j]:
                problems.append(f"{dev_names[j]}: parameter values changed by the move")
        params = call("device_parameters", _loc(t.track, base + (0,)))
    except (BridgeError, ChainError, KeyError, Refusal) as exc:
        return stage(i, "not_applied", "verify_failed", (str(exc),))
    if problems:
        return stage(i, "not_applied", "wrap_mismatch", problems)
    wanted = [(g.macro, _target_value(g.value)) for g in plan.groups if g.value is not None]

    def receipt(outcome, reason=None, **kw):
        return StageReceipt(index=i, device="macros", outcome=outcome, reason=reason, **kw)

    rack_loc = _loc(t.track, base + (0,))
    rec, reason = _apply_params(call, receipt, rack_loc, params, wanted, None, 0)
    stages.append(rec)
    if reason:
        return _receipt(plan, stages, completed, (i, reason), names)
    completed.append(i)
    return _receipt(plan, stages, completed, None, names)


def _target_value(value):
    return {"raw": value.raw} if hasattr(value, "raw") else value
