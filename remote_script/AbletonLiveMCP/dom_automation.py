"""Automation domain: session-clip envelopes (P-10 shapes).

Live 12.2 (P-10): ``create_automation_envelope``, ``insert_step(time, length, value)``,
``value_at_time``, ``events_in_range``, ``delete_events_in_range`` and ``clear_envelope`` work on
session clips. ``automation_envelope`` on an arrangement clip returns None, so arrangement
automation refuses with ``unsupported`` before any call. Ramps are emulated with steps.
"""

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
        raise ValueError("'parameter' must be {kind: param|mixer_param, ...selectors}")
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
        raise ValueError("'sample_times' must be a list of at most 64 beat times")
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
            raise ValueError(f"{w} must be an object")
        t = float(_number(s.get("time"), f"{w}.time", 0, length))
        if t >= length:
            raise ValueError(f"{w}.time must be before the clip end")
        d = float(_number(s.get("length"), f"{w}.length", 0, length, True))
        out.append((t, min(d, length - t), float(_number(s.get("value"), f"{w}.value", lo, hi))))
    for i, r in enumerate(item.get("ramps") or []):
        w = f"{where}.ramps[{i}]"
        if not isinstance(r, dict):
            raise ValueError(f"{w} must be an object")
        a = float(_number(r.get("start"), f"{w}.start", 0, length))
        b = float(_number(r.get("end"), f"{w}.end", 0, length))
        if not a < b:
            raise ValueError(f"{w}: 'start' must be before 'end'")
        v0 = float(_number(r.get("from"), f"{w}.from", lo, hi))
        v1 = float(_number(r.get("to"), f"{w}.to", lo, hi))
        n = r.get("steps", 32)
        if isinstance(n, bool) or not isinstance(n, int) or not 2 <= n <= 256:
            raise ValueError(f"{w}.steps must be an integer 2..256")
        width = (b - a) / n
        out += [(a + k * width, width, v0 + (v1 - v0) * k / (n - 1)) for k in range(n)]
    if len(out) > STEP_LIMIT:
        raise ValueError(f"{where}: at most {STEP_LIMIT} steps per clip (ramps included)")
    return out


def set_automation(ctx, p, t):
    """Per item: optional ``clear`` (the parameter's envelope), optional ``delete_range``
    ([start, end]), then ``steps``/``ramps`` written with insert_step. Readback per item."""
    items, resolved = p.get("targets"), t["targets"]

    def validate(i, item):
        where = f"targets[{i}]"
        kind = resolved[i].path[-1][0]
        if kind not in ("clip", "arr_clip"):
            raise ValueError(f"{where}: must be a clip reference")
        _clip_check(ctx, kind)
        clip = resolved[i].obj
        pk = item.get("param_kind", "param")
        if pk not in PARAM_KINDS:
            raise ValueError(f"{where}.param_kind must be one of {list(PARAM_KINDS)}")
        param_r = ctx.safety.resolve(pk, item.get("param"), ctx.song)
        clip_track = resolved[i].path[0][1]
        if not _same(param_r.path[0][1], clip_track):
            raise ValueError(f"{where}: the parameter must be on the clip's own track")
        param = param_r.obj
        length = float(clip.length)
        steps = _steps(item, param, length, where)
        clear = item.get("clear", False)
        if not isinstance(clear, bool):
            raise ValueError(f"{where}.clear must be a bool")
        span = item.get("delete_range")
        if span is not None:
            if not isinstance(span, list) or len(span) != 2:
                raise ValueError(f"{where}.delete_range must be [start, end]")
            span = (
                float(_number(span[0], f"{where}.delete_range[0]", 0, length)),
                float(_number(span[1], f"{where}.delete_range[1]", 0, length)),
            )
        if not (clear or span or steps):
            raise ValueError(f"{where}: nothing to do (steps, ramps, delete_range or clear)")
        return clip, param, clear, span, steps

    def write(e):
        clip, param, clear, span, steps = e
        if clear:
            clip.clear_envelope(param)
        env = clip.automation_envelope(param)
        if span is not None and env is not None:
            env.delete_events_in_range(span[0], span[1])
        if steps:
            if env is None:
                env = clip.create_automation_envelope(param)
            if env is None:
                raise RuntimeError("Live returned no envelope for this parameter")
            for t_, d, v in steps:
                env.insert_step(t_, d, v)
        row = {"parameter": param.name, "has_envelopes": bool(clip.has_envelopes)}
        if env is not None and steps:
            row["events"] = len(_events(env, 0.0, float(clip.length)))
            row["checks"] = [
                {"time": t_, "wrote": v, "read": env.value_at_time(t_ + d / 2)}
                for t_, d, v in steps[:: max(1, len(steps) // 8)]
            ]
        return row

    return two_pass(items, validate, write)


METHODS = {
    "get_automation": (get_automation, READ, None),
    "set_automation": (set_automation, WRITE, (("targets", "ref", ANY_KIND),)),
}
