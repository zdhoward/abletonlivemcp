"""Automation domain: session-clip envelopes (P-10 shapes).

Live 12.2 (P-10): ``create_automation_envelope``, ``insert_step(time, length, value)``,
``value_at_time``, ``events_in_range``, ``delete_events_in_range`` and ``clear_envelope`` work on
session clips. ``automation_envelope`` on an arrangement clip returns None, so arrangement
automation refuses with ``unsupported`` before any call. Legacy ramps use steps; sparse
points retain linear interpolation by deleting interior step boundaries.
"""

from .core import Invalid
from .dom_common import (
    DISABLED,
    READ,
    SUPPORTED,
    WRITE,
    _number,
    _same,
    clip_address_nodes,
    reference_nodes,
    require,
    two_pass,
)

ANY_KIND = "any"  # safety.ANY_KIND; importing it here is circular (safety imports dom_*)

CAPABILITIES = {
    "automation.session": (SUPPORTED, "P-10: session clip envelopes"),
    "automation.arrangement": (
        DISABLED,
        "automation_envelope returns None on arrangement clips in Live 12.2 (P-10)",
    ),  # fmt: skip
}

EVENT_LIMIT = 512
STEP_LIMIT = 512
SAMPLE_POINTS = 16
PARAM_KINDS = ("param", "mixer_param")


def _events(env, start, end):
    rows = []
    for e in env.events_in_range(start, end):
        if len(rows) >= EVENT_LIMIT:
            break
        rows.append({"time": e.time, "value": e.value})
    return rows


def _clip_check(ctx, kind):
    if kind == "arr_clip":
        require(ctx, "automation.arrangement")
    require(ctx, "automation.session")


def get_automation(ctx, p):
    """Envelope state for one clip and one parameter (index selectors)."""
    song = ctx.song
    addr = {k: p.get(k) for k in ("track", "scene", "arrangement", "take_lane") if k in p}
    nodes = clip_address_nodes(song, addr)
    _clip_check(ctx, nodes[-1][0])
    clip = nodes[-1][1]
    sel = p.get("parameter")
    if not isinstance(sel, dict) or sel.get("kind") not in PARAM_KINDS:
        raise Invalid("'parameter' must be {kind: param|mixer_param, ...selectors}")
    param = reference_nodes(song, {**sel, "track": p.get("track")})[-1][1]
    env = clip.automation_envelope(param)
    out = {
        "parameter": param.name,
        "range": [param.min, param.max],
        "has_envelopes": bool(getattr(clip, "has_envelopes", False)),
        "has_envelope": env is not None,
        "clip_length": clip.length,
    }
    if env is None:
        return out
    end = float(clip.length)
    out["events"] = _events(env, 0.0, end)
    times = p.get("sample_times")
    if times is None:
        n = SAMPLE_POINTS
        times = [end * k / (n - 1) if k < n - 1 else end * 0.999 for k in range(n)]
    if not isinstance(times, list) or len(times) > 64:
        raise Invalid("'sample_times' must be a list of at most 64 beat times")
    out["samples"] = [
        {"time": t, "value": env.value_at_time(float(_number(t, "sample_times[]", 0, end)))}
        for t in times
    ]
    return out


def _steps(item, param, length, where):
    """``steps`` ([{time, length, value}]) plus ``ramps`` ([{start, end, from, to, steps?}])
    -> one checked ``[(time, length, value)]`` list."""
    lo, hi = float(param.min), float(param.max)
    out = []
    for i, s in enumerate(item.get("steps") or []):
        w = f"{where}.steps[{i}]"
        if not isinstance(s, dict):
            raise Invalid(f"{w} must be an object")
        t = float(_number(s.get("time"), f"{w}.time", 0, length))
        if t >= length:
            raise Invalid(f"{w}.time must be before the clip end")
        d = float(_number(s.get("length"), f"{w}.length", 0, length, True))
        out.append((t, min(d, length - t), float(_number(s.get("value"), f"{w}.value", lo, hi))))
    for i, r in enumerate(item.get("ramps") or []):
        w = f"{where}.ramps[{i}]"
        if not isinstance(r, dict):
            raise Invalid(f"{w} must be an object")
        a = float(_number(r.get("start"), f"{w}.start", 0, length))
        b = float(_number(r.get("end"), f"{w}.end", 0, length))
        if not a < b:
            raise Invalid(f"{w}: 'start' must be before 'end'")
        v0 = float(_number(r.get("from"), f"{w}.from", lo, hi))
        v1 = float(_number(r.get("to"), f"{w}.to", lo, hi))
        n = r.get("steps", 32)
        if isinstance(n, bool) or not isinstance(n, int) or not 2 <= n <= 256:
            raise Invalid(f"{w}.steps must be an integer 2..256")
        width = (b - a) / n
        out += [(a + k * width, width, v0 + (v1 - v0) * k / (n - 1)) for k in range(n)]
    if len(out) > STEP_LIMIT:
        raise Invalid(f"{where}: at most {STEP_LIMIT} steps per clip (ramps included)")
    return out


def _points(item, param, length, where):
    points = item.get("points")
    if points is None:
        return []
    if item.get("steps") or item.get("ramps"):
        raise Invalid(f"{where}: points cannot be combined with steps or ramps")
    if item.get("clear") is not True:
        raise Invalid(f"{where}.points replaces the envelope; set clear=true")
    if not isinstance(points, list) or not 2 <= len(points) <= 3:
        raise Invalid(f"{where}.points: give 2 or 3 breakpoints")
    if param.is_quantized:
        raise Invalid(f"{where}.points: interpolation needs a continuous parameter")
    out = []
    for p in points:
        if not isinstance(p, dict):
            raise Invalid(f"{where}.points entries must be objects")
        time = float(_number(p.get("time"), f"{where}.points.time", 0, length))
        value = float(_number(p.get("value"), f"{where}.points.value", param.min, param.max))
        if out and time - out[-1][0] < 0.001:
            raise Invalid(f"{where}.points must increase by at least 0.001 beats")
        out.append((time, value))
    if out[0][0] != 0 or out[-1][0] != length:
        raise Invalid(f"{where}.points must span beat 0 through clip.length ({length})")
    return out


def set_automation(ctx, p, t):
    """Per item: optional ``clear`` (the parameter's envelope), optional ``delete_range``
    ([start, end]), then ``steps``/``ramps`` written with insert_step. Readback per item."""
    items, resolved = p.get("targets"), t["targets"]

    def validate(i, item):
        where = f"targets[{i}]"
        kind = resolved[i].path[-1][0]
        if kind not in ("clip", "arr_clip"):
            raise Invalid(f"{where}: must be a clip reference")
        _clip_check(ctx, kind)
        clip = resolved[i].obj
        pk = item.get("param_kind", "param")
        if pk not in PARAM_KINDS:
            raise Invalid(f"{where}.param_kind must be one of {list(PARAM_KINDS)}")
        param_r = ctx.safety.resolve(pk, item.get("param"), ctx.song)
        clip_track = resolved[i].path[0][1]
        if not _same(param_r.path[0][1], clip_track):
            raise Invalid(f"{where}: the parameter must be on the clip's own track")
        param = param_r.obj
        length = float(clip.length)
        steps = _steps(item, param, length, where)
        points = _points(item, param, length, where)
        clear = item.get("clear", False)
        if not isinstance(clear, bool):
            raise Invalid(f"{where}.clear must be a bool")
        span = item.get("delete_range")
        if span is not None:
            if not isinstance(span, list) or len(span) != 2:
                raise Invalid(f"{where}.delete_range must be [start, end]")
            span = (
                float(_number(span[0], f"{where}.delete_range[0]", 0, length)),
                float(_number(span[1], f"{where}.delete_range[1]", 0, length)),
            )
        if not (clear or span or steps or points):
            raise Invalid(f"{where}: nothing to do (steps, ramps, delete_range or clear)")
        return clip, param, clear, span, steps, points

    def write(e):
        clip, param, clear, span, steps, points = e
        if clear:
            clip.clear_envelope(param)
        env = clip.automation_envelope(param)
        if span is not None and env is not None:
            env.delete_events_in_range(span[0], span[1])
        if steps or points:
            if env is None:
                env = clip.create_automation_envelope(param)
            if env is None:
                raise RuntimeError("Live returned no envelope for this parameter")
            for t_, d, v in steps:
                env.insert_step(t_, d, v)
            # Live has no insert-point/curve setter. Remove the interior step boundaries
            # to retain interpolation between endpoints. Coincident outer guards remain.
            if points:
                # Force a terminal boundary even when the last value equals Live's
                # original/default value (notably Pump A/B = 1). The seed ends beyond
                # the clip, so its restoring event is outside the copied timeline span.
                baseline = param.min if points[-1][1] != param.min else param.max
                env.insert_step(0.0, float(clip.length) + 1.0, baseline)
            for (a, va), (b, vb) in zip(points, points[1:], strict=False):
                mid = (a + b) / 2
                env.insert_step(a, mid - a, va)
                env.insert_step(mid, b - mid, vb)
                epsilon = min(0.0001, (b - a) / 4)
                env.delete_events_in_range(a + epsilon, b - epsilon)
        row = {"parameter": param.name, "has_envelopes": bool(clip.has_envelopes)}
        if env is not None and steps:
            row["events"] = len(_events(env, 0.0, float(clip.length)))
            row["checks"] = [
                {"time": t_, "wrote": v, "read": env.value_at_time(t_ + d / 2)}
                for t_, d, v in steps[:: max(1, len(steps) // 8)]
            ]
        if env is not None and points:
            events = _events(env, 0.0, float(clip.length))
            row["events"] = len(events)
            row["breakpoint_times"] = sorted({e["time"] for e in events})
            row["interpolation"] = "linear; coincident boundary guards retained by Live"
            row["checks"] = [
                {"time": (a + b) / 2, "read": env.value_at_time((a + b) / 2)}
                for (a, _), (b, _) in zip(points, points[1:], strict=False)
            ]
        return row

    return two_pass(items, validate, write)


METHODS = {
    "get_automation": (get_automation, READ, None),
    "set_automation": (set_automation, WRITE, (("targets", "ref", ANY_KIND),)),
}
