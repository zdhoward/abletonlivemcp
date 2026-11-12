"""Devices domain: device lists, parameter reads (issuing references), display sampling,
parameter writes, device on/name/collapse, gated moves and the ``delete_devices`` route.

Location: ``track`` is a TrackSel (index, ``"return:N"`` or ``"master"``) and ``path`` a DevicePath
(``[device]`` or ``[device, chain, device, ...]``, a chain step may be ``"pad:N"``). The legacy
``{track, device}`` shape still works (``path = [device]``).
"""

from .core import Invalid
from .dom_common import (
    BATCH_LIMIT,
    READ,
    SAMPLE_LIMIT,
    SUPPORTED,
    UNSUPPORTED,
    UNVERIFIED,
    WRITE,
    _index,
    _same,
    capability_report,
    device_nodes,
    for_deletion,
    owner_node,
    position_of,
    quarantine,
    require,
    run_writes,
    unsupported,
)

ANY_KIND = "any"  # safety.ANY_KIND; importing it here is circular (safety imports dom_*)

PARAM_PAGE = 128  # max parameter rows per read
ITEMS_LIMIT = 64  # max value_items listed for a quantized parameter
DEVICE_TYPES = {0: "undefined", 1: "instrument", 2: "audio_effect", 4: "midi_effect"}

CAPABILITIES = {
    "device.on": (SUPPORTED, "Device On is parameter 0; parameter writes proven (P-27)"),
    "device.rename": (UNVERIFIED, "Device.name setter not probed on 12.2"),
    "device.collapse": (UNVERIFIED, "Device.View.is_collapsed setter not probed on 12.2"),
    "device.move_cross_track": (SUPPORTED, "P-04: cross-track Song.move_device observed"),
    "device.move_reorder": (UNSUPPORTED, "P-04: same-container reorder raised 'Couldn't move'"),
    "device.move_into_chain": (UNVERIFIED, "P-04 had no rack fixture"),
    "device.move_out_of_chain": (UNVERIFIED, "P-04 had no rack fixture"),
    "device.delete": (UNVERIFIED, "P-24: Track/Chain.delete_device not observed yet"),
    "param.reset": (SUPPORTED, "P-27: default_value read for unquantized parameters"),
    "param.re_enable_automation": (UNVERIFIED, "DeviceParameter.re_enable_automation not probed"),
}


def _get(obj, name, default=None):
    try:
        return getattr(obj, name, default)
    except Exception:  # noqa: BLE001 - a Live property may raise; a read reports it as absent
        return default


# ---- location ------------------------------------------------------------------------------


def locate(song, p):
    """``{track, path}`` (or legacy ``{track, device}``) -> owner node + device/chain nodes."""
    owner = owner_node(song, p.get("track"))
    path = p.get("path")
    if path is None:
        path = [p.get("device")]
    return [owner] + device_nodes(owner[1], path)


def locate_device(song, p):
    nodes = locate(song, p)
    if nodes[-1][0] != "device":
        raise Invalid("'path' must end at a device (an even number of steps)")
    return nodes


def container_nodes(song, p):
    """A device container: the owner track, or the chain/drum pad a ``path`` ends at (a pad's
    devices are those of its first chain; an empty pad has none)."""
    owner = owner_node(song, p.get("track"))
    path = p.get("path")
    if not path:
        return [owner]
    nodes = [owner] + device_nodes(owner[1], path)
    if nodes[-1][0] not in ("chain", "drum_pad"):
        raise Invalid("a container 'path' must end at a chain or a drum pad")
    return nodes


def container_devices(node):
    kind, obj = node[0], node[1]
    if kind == "drum_pad":
        chains = obj.chains
        return tuple(chains[0].devices) if len(chains) else ()
    return tuple(obj.devices)


def device_row(i, d):
    params = _get(d, "parameters") or ()
    first = params[0] if len(params) else None
    on = None
    if first is not None and _get(first, "name") == "Device On":
        on = bool(_get(first, "value"))
    row = {
        "index": i,
        "name": _get(d, "name"),
        "class_name": _get(d, "class_name"),
        "type": DEVICE_TYPES.get(_get(d, "type"), "undefined"),
        "on": on,
        "is_active": _get(d, "is_active"),
        "collapsed": _get(_get(d, "view"), "is_collapsed"),
        "parameters": len(params),
        "rack": bool(_get(d, "can_have_chains", False)),
        "drum_rack": bool(_get(d, "can_have_drum_pads", False)),
    }
    if row["rack"]:
        row["chains"] = len(_get(d, "chains") or ())
    return row


def device_list(ctx, p):
    """The devices of a track (``track``) or of a rack chain (``track`` + chain ``path``)."""
    nodes = container_nodes(ctx.song, p)
    owner = nodes[0]
    container = nodes[-1][1]
    return {
        "owner": {
            "kind": owner[0],
            "name": _get(owner[1], "name"),
            "has_midi_input": bool(_get(owner[1], "has_midi_input", False)),
            "has_audio_input": bool(_get(owner[1], "has_audio_input", False)),
            "is_group": bool(_get(owner[1], "is_foldable", False)),
        },
        "container": nodes[-1][0],
        "container_name": _get(container, "name"),
        "devices": [device_row(i, d) for i, d in enumerate(container_devices(nodes[-1]))],
    }


# ---- parameters ----------------------------------------------------------------------------


def _param(dev, idx):
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(dev.parameters):
        raise Invalid("'parameter' must be a valid parameter index")
    return dev.parameters[idx]


def _checked_write(q, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Invalid(f"value for {q.name!r} must be a number")
    if not q.min <= value <= q.max:
        raise Invalid(f"value {value} outside {q.min}..{q.max} for {q.name!r}")
    if not getattr(q, "is_enabled", True):
        raise Invalid(f"parameter {q.name!r} is not enabled (macro-controlled?)")
    return float(value)


def _write(q, value):
    q.value = value
    return {"name": q.name, "value": q.value, "display": q.str_for_value(q.value)}


def _sampled(q, values):
    if not isinstance(values, list) or not 1 <= len(values) <= SAMPLE_LIMIT:
        raise Invalid(f"'values' must be a list of 1..{SAMPLE_LIMIT} numbers")
    out = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not q.min <= v <= q.max:
            raise Invalid(f"every value must be a number within {q.min}..{q.max}")
        out.append(q.str_for_value(float(v)))
    return {"name": q.name, "displays": out}


def _batch(p, key):
    items = p.get(key)
    if not isinstance(items, list) or not 1 <= len(items) <= BATCH_LIMIT:
        raise Invalid(f"{key!r} must be a list of 1..{BATCH_LIMIT} items")
    if not all(isinstance(i, dict) for i in items):
        raise Invalid(f"every item in {key!r} must be an object")
    return items


def _param_row(ctx, nodes, i, q, count):
    row = {
        "index": i,
        "ref": ctx.safety.issue(*nodes, ("param", q, {"index": i, "count": count, "name": q.name})),
        "name": q.name,
        "value": q.value,
        "min": q.min,
        "max": q.max,
        "is_quantized": q.is_quantized,
        "is_enabled": getattr(q, "is_enabled", True),
        "display": q.str_for_value(q.value),
    }
    default = _get(q, "default_value")
    if isinstance(default, (int, float)) and not isinstance(default, bool):
        row["default"] = default
    state = _get(q, "automation_state")
    if state is not None:
        row["automation_state"] = int(state)
    if q.is_quantized:
        items = _get(q, "value_items")
        if items is not None:
            row["items"] = [str(x) for x in list(items)[:ITEMS_LIMIT]]
    return row


def device_parameters(ctx, p):
    """Parameter rows with references. Optional ``offset``/``limit`` page (limit <= 128)."""
    nodes = locate_device(ctx.song, p)
    dev = nodes[-1][1]
    params = dev.parameters
    count = len(params)
    offset = p.get("offset", 0)
    limit = p.get("limit", count if p.get("offset") is None else PARAM_PAGE)
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise Invalid("'offset' must be an integer >= 0")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise Invalid("'limit' must be an integer >= 0")
    if p.get("limit") is not None and limit > PARAM_PAGE:
        raise Invalid(f"'limit' must be at most {PARAM_PAGE}")
    end = min(count, offset + limit)
    return [_param_row(ctx, nodes, i, params[i], count) for i in range(offset, end)]


def set_device_parameter(_ctx, p, t):
    q = t["parameter"].obj
    return _write(q, _checked_write(q, p.get("value")))


def set_device_parameters(ctx, p, t):
    """Write several parameters (by reference). Each item is ``{parameter, value}``,
    ``{parameter, reset: true}`` (its default value) or ``{parameter, re_enable_automation: true}``.
    Everything is validated before any write."""
    plan = []
    items = _batch(p, "writes")
    unverified = []
    for i, w in enumerate(items):  # t["writes"] was built from the same list by the gate
        q = t["writes"][i].obj
        if w.get("re_enable_automation") is True:
            if require(ctx, "param.re_enable_automation", ((q, "re_enable_automation"),)) == (
                UNVERIFIED
            ):
                unverified.append("param.re_enable_automation")
            plan.append((q, None))
            continue
        if w.get("reset") is True:
            if q.is_quantized:
                raise Invalid(f"{q.name!r} is quantized: give a value instead of reset")
            require(ctx, "param.reset", ((q, "default_value"),))
            plan.append((q, _checked_write(q, q.default_value)))
            continue
        plan.append((q, _checked_write(q, w.get("value"))))
    results = []
    for q, v in plan:
        if v is None:
            q.re_enable_automation()
            results.append({"name": q.name, "value": q.value, "display": q.str_for_value(q.value)})
        else:
            results.append(_write(q, v))
    out = {"results": results}
    if unverified:
        out["unverified"] = sorted(set(unverified))
    return out


def sample_parameter(ctx, p):
    """Display text for candidate values of one parameter. Read-only; writes nothing."""
    q = _param(locate_device(ctx.song, p)[-1][1], p.get("parameter"))
    return _sampled(q, p.get("values"))


def sample_parameters(ctx, p):
    """Like sample_parameter for many parameters of one device in a single round trip."""
    dev = locate_device(ctx.song, p)[-1][1]
    requests = _batch(p, "requests")
    total = sum(len(r["values"]) for r in requests if isinstance(r.get("values"), list))
    if total > SAMPLE_LIMIT:  # one cap for the whole request, not per entry
        raise Invalid(f"at most {SAMPLE_LIMIT} display values in total per request")
    return {
        "results": [_sampled(_param(dev, r.get("parameter")), r.get("values")) for r in requests]
    }


# ---- device state: on / name / collapse ----------------------------------------------------


def _device_on_param(dev):
    params = dev.parameters
    if not len(params) or params[0].name != "Device On":
        raise unsupported("device.on", f"{dev.name!r} has no 'Device On' parameter")
    return params[0]


def set_devices(ctx, p, t):
    """Several devices: ``on`` (bool), ``name`` (str), ``collapsed`` (bool). Two-pass."""
    items = _batch(p, "targets")
    unverified = set()
    prepared = []
    for i, item in enumerate(items):
        dev = t["targets"][i].obj
        edit = {}
        if "on" in item:
            if not isinstance(item["on"], bool):
                raise Invalid(f"targets[{i}].on must be true or false")
            require(ctx, "device.on")
            q = _device_on_param(dev)
            if not getattr(q, "is_enabled", True):
                raise Invalid(f"targets[{i}]: 'Device On' is controlled elsewhere")
            edit["on"] = (q, 1.0 if item["on"] else 0.0)
        if "name" in item:
            name = item["name"]
            if not isinstance(name, str) or not 1 <= len(name) <= 256:
                raise Invalid(f"targets[{i}].name must be a string of 1..256 characters")
            if require(ctx, "device.rename", ((dev, "name"),)) == UNVERIFIED:
                unverified.add("device.rename")
            edit["name"] = name
        if "collapsed" in item:
            if not isinstance(item["collapsed"], bool):
                raise Invalid(f"targets[{i}].collapsed must be true or false")
            view = _get(dev, "view")
            if require(ctx, "device.collapse", ((view, "is_collapsed"),)) == UNVERIFIED:
                unverified.add("device.collapse")
            edit["collapsed"] = (view, item["collapsed"])
        if not edit:
            raise Invalid(f"targets[{i}] sets nothing (give on, name or collapsed)")
        prepared.append((dev, edit))

    def write(entry):
        dev, edit = entry
        if "on" in edit:
            q, v = edit["on"]
            q.value = v
        if "name" in edit:
            dev.name = edit["name"]
        if "collapsed" in edit:
            view, v = edit["collapsed"]
            view.is_collapsed = v
        row = {"name": _get(dev, "name")}
        if "on" in edit:
            row["on"] = bool(edit["on"][0].value)
        if "collapsed" in edit:
            row["collapsed"] = bool(_get(edit["collapsed"][0], "is_collapsed"))
        return row

    receipt = run_writes(prepared, write)
    receipt["unverified"] = sorted(unverified)
    return receipt


# ---- move ----------------------------------------------------------------------------------


def _destination(dest):
    kind = dest.path[-1][0]
    if kind in ("track", "return_track", "master", "chain"):
        return dest.obj, kind
    if kind == "drum_pad":
        chains = dest.obj.chains
        if not len(chains):
            raise unsupported(
                "device.move_into_chain", "that drum pad has no chain; nothing was moved"
            )
        return chains[0], "chain"
    raise Invalid("the destination must be a track, return, master, chain or drum pad")


def move_device(ctx, p, t):
    """``targets: [device, destination]``; ``position`` (default: the end). Every refusal comes
    before the native call: a same-container reorder is unsupported on 12.2 (P-04)."""
    if len(t["targets"]) != 2:
        raise Invalid("'targets' must be [device, destination]")
    dev, dest = t["targets"]
    if dev.path[-1][0] != "device":
        raise Invalid("targets[0] must be a device")
    container, ckind = _destination(dest)
    source = dev.path[-2][1]
    if _same(source, container):
        require(ctx, "device.move_reorder")  # declared unsupported: always refuses here
    if any(_same(node[1], dev.obj) for node in dest.path):
        raise Invalid("a device cannot move into its own chains")
    if ckind == "chain":
        cap = "device.move_into_chain"
    elif dev.path[-2][0] == "chain":
        cap = "device.move_out_of_chain"
    else:
        cap = "device.move_cross_track"
    state = require(ctx, cap, ((ctx.song, "move_device"),))
    before_dest = len(container.devices)
    before_src = len(source.devices)
    position = p.get("position")
    if position is None:
        position = before_dest
    position = _index(position, "position", before_dest + 1)
    name, cls = dev.obj.name, dev.obj.class_name
    ctx.song.move_device(dev.obj, container, position)
    after = container.devices
    landed = position < len(after) and after[position].class_name == cls
    if len(after) != before_dest + 1 or len(source.devices) != before_src - 1 or not landed:
        quarantine(ctx, cap, "moved device not observed at the destination")
        raise RuntimeError("the move was not observed at the destination (outcome unknown)")
    out = {"moved": name, "position": position, "devices": [d.name for d in after]}
    if state == UNVERIFIED:
        out["unverified"] = [cap]
    return out


# ---- delete route (contract: models.DELETE_ROUTES["device"]) --------------------------------


def delete_devices(ctx, p, t):
    """``targets: [{kind: "device", ref, expect_name}]``; deepest/highest first, by identity."""
    state = require(ctx, "device.delete")
    resolved = list(enumerate(t["targets"]))
    for _i, r in resolved:
        parent = r.path[-2][1]
        if not hasattr(parent, "delete_device"):
            raise unsupported("device.delete", f"{r.path[-2][0]} has no delete_device")
    order = {id(r): i for i, r in resolved}
    prepared = [(order[id(r)], r) for r in for_deletion([r for _i, r in resolved])]

    def write(entry):
        index, r = entry
        parent, name = r.path[-2][1], r.obj.name
        parent.delete_device(position_of(parent.devices, r.obj))
        return {"index": index, "deleted": name}

    receipt = run_writes(prepared, write)
    receipt["unverified"] = ["device.delete"] if state == UNVERIFIED else []
    return receipt


CLASS_MEMBERS = {"rack.insert_chain": ("RackDevice", "RackDevice", "insert_chain")}


def _class_has(module, cls, member):
    """Whether Live's class has ``member`` (None outside Live: decided at call time instead)."""
    try:
        import Live  # noqa: PLC0415 - only inside Live
    except ImportError:
        return None
    return hasattr(getattr(getattr(Live, module, None), cls, None), member)


def device_capabilities(ctx, p):
    """State of the named capabilities (plan-time gates); an absent class member reads as
    ``unsupported``."""
    names = p.get("names")
    if not isinstance(names, list) or not 1 <= len(names) <= BATCH_LIMIT:
        raise Invalid(f"'names' must be a list of 1..{BATCH_LIMIT} capability names")
    report = capability_report(ctx)
    out = {}
    for n in names:
        row = report.get(n, {"state": "unsupported", "reason": "not a declared capability"})
        if n in CLASS_MEMBERS and _class_has(*CLASS_MEMBERS[n]) is False:
            row = {"state": "unsupported", "reason": f"this Live has no {CLASS_MEMBERS[n][2]}"}
        out[n] = row
    return out


METHODS = {
    "device_capabilities": (device_capabilities, READ, None),
    "device_list": (device_list, READ, None),
    "device_parameters": (device_parameters, READ, None),
    "sample_parameter": (sample_parameter, READ, None),
    "sample_parameters": (sample_parameters, READ, None),
    "set_device_parameter": (set_device_parameter, WRITE, (("parameter", "param"),)),
    "set_device_parameters": (set_device_parameters, WRITE, (("writes", "parameter", "param"),)),
    "set_devices": (set_devices, WRITE, (("targets", "ref", "device"),)),
    "move_device": (move_device, WRITE, (("targets", "ref", ANY_KIND),)),
    "delete_devices": (delete_devices, WRITE, (("targets", "ref", "device"),)),
}
