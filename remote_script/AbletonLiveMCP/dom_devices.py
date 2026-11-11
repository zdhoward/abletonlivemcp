"""Devices domain: parameter reads (issuing references), display sampling, parameter writes."""

from .dom_common import BATCH_LIMIT, READ, SAMPLE_LIMIT, WRITE, _device, _track


def _param(dev, idx):
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(dev.parameters):
        raise ValueError("'parameter' must be a valid parameter index")
    return dev.parameters[idx]


def _checked_write(q, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"value for {q.name!r} must be a number")
    if not q.min <= value <= q.max:
        raise ValueError(f"value {value} outside {q.min}..{q.max} for {q.name!r}")
    if not getattr(q, "is_enabled", True):
        raise ValueError(f"parameter {q.name!r} is not enabled (macro-controlled?)")
    return float(value)


def _write(q, value):
    q.value = value
    return {"name": q.name, "value": q.value, "display": q.str_for_value(q.value)}


def _sampled(q, values):
    if not isinstance(values, list) or not 1 <= len(values) <= SAMPLE_LIMIT:
        raise ValueError(f"'values' must be a list of 1..{SAMPLE_LIMIT} numbers")
    out = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not q.min <= v <= q.max:
            raise ValueError(f"every value must be a number within {q.min}..{q.max}")
        out.append(q.str_for_value(float(v)))
    return {"name": q.name, "displays": out}


def _batch(p, key):
    items = p.get(key)
    if not isinstance(items, list) or not 1 <= len(items) <= BATCH_LIMIT:
        raise ValueError(f"{key!r} must be a list of 1..{BATCH_LIMIT} items")
    if not all(isinstance(i, dict) for i in items):
        raise ValueError(f"every item in {key!r} must be an object")
    return items


def device_parameters(ctx, p):
    track = _track(ctx.song, p)
    dev = _device(track, p)
    chain = (
        ("track", track, {}),
        ("device", dev, {"layout": tuple(d.class_name for d in track.devices)}),
    )
    count = len(dev.parameters)
    return [
        {
            "index": i,
            "ref": ctx.safety.issue(
                *chain, ("param", q, {"index": i, "count": count, "name": q.name})
            ),
            "name": q.name,
            "value": q.value,
            "min": q.min,
            "max": q.max,
            "is_quantized": q.is_quantized,
            "is_enabled": getattr(q, "is_enabled", True),
            "display": q.str_for_value(q.value),
        }
        for i, q in enumerate(dev.parameters)
    ]


def set_device_parameter(_ctx, p, t):
    q = t["parameter"].obj
    return _write(q, _checked_write(q, p.get("value")))


def set_device_parameters(_ctx, p, t):
    """Write several parameters (by reference). Everything is validated before any write."""
    plan = []
    items = _batch(p, "writes")
    for i, w in enumerate(items):  # t["writes"] was built from the same list by the gate
        q = t["writes"][i].obj
        plan.append((q, _checked_write(q, w.get("value"))))
    return {"results": [_write(q, v) for q, v in plan]}


def sample_parameter(ctx, p):
    """Display text for candidate values of one parameter. Read-only; writes nothing."""
    q = _param(_device(_track(ctx.song, p), p), p.get("parameter"))
    return _sampled(q, p.get("values"))


def sample_parameters(ctx, p):
    """Like sample_parameter for many parameters of one device in a single round trip."""
    dev = _device(_track(ctx.song, p), p)
    requests = _batch(p, "requests")
    total = sum(len(r["values"]) for r in requests if isinstance(r.get("values"), list))
    if total > SAMPLE_LIMIT:  # one cap for the whole request, not per entry
        raise ValueError(f"at most {SAMPLE_LIMIT} display values in total per request")
    return {
        "results": [_sampled(_param(dev, r.get("parameter")), r.get("values")) for r in requests]
    }


METHODS = {
    "device_parameters": (device_parameters, READ, None),
    "sample_parameter": (sample_parameter, READ, None),
    "sample_parameters": (sample_parameters, READ, None),
    "set_device_parameter": (set_device_parameter, WRITE, (("parameter", "param"),)),
    "set_device_parameters": (set_device_parameters, WRITE, (("writes", "parameter", "param"),)),
}
