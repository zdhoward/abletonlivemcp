"""Racks domain: macros, variations, chains and chain mixers (P-11 unrun).

Macro values are ordinary device parameters (1..16): the host writes them through
``set_device_parameters`` (display targets solved). This module reads the rack and writes the
rack-only state. Native macro mapping is not offered (manual mapping guidance only); no .adg
writing. Each operation has its own capability; every refusal comes before the native call.
"""

from .core import Invalid
from .dom_common import (
    BATCH_LIMIT,
    READ,
    UNVERIFIED,
    WRITE,
    _index,
    quarantine,
    require,
    run_writes,
)
from .dom_devices import _get, locate_device

CHAIN_LIMIT = 64
MACRO_LIMIT = 16

CAPABILITIES = {
    "rack.visible_macros": (UNVERIFIED, "P-11 unrun: add_macro/remove_macro"),
    "rack.variations": (UNVERIFIED, "P-11 unrun: store/recall/delete variation"),
    "rack.randomize": (UNVERIFIED, "P-11 unrun: randomize_macros"),
    "rack.chain_state": (UNVERIFIED, "P-11 unrun: Chain.name/mute/solo"),
    "rack.chain_mixer": (UNVERIFIED, "P-11 unrun: Chain.mixer_device volume/panning"),
    "rack.insert_chain": (UNVERIFIED, "not probed: RackDevice.insert_chain (absent before 12.x?)"),
}


def _rack(ctx, p):
    dev = locate_device(ctx.song, p)[-1][1]
    if not getattr(dev, "can_have_chains", False):
        raise Invalid("that device is not a rack")
    return dev


def _mixer_value(chain, role):
    q = _get(_get(chain, "mixer_device"), role)
    if q is None:
        return None
    return {"value": q.value, "display": q.str_for_value(q.value), "min": q.min, "max": q.max}


def _chain_row(i, chain):
    return {
        "index": i,
        "name": _get(chain, "name"),
        "mute": _get(chain, "mute"),
        "solo": _get(chain, "solo"),
        "devices": [d.name for d in list(_get(chain, "devices") or ())[:8]],
        "volume": _mixer_value(chain, "volume"),
        "pan": _mixer_value(chain, "panning"),
    }


def rack(ctx, p):
    """Macros (parameters 1..16), variations and chains (capped) of one rack."""
    dev = _rack(ctx, p)
    params = list(dev.parameters)
    visible = _get(dev, "visible_macro_count")
    count = visible if isinstance(visible, int) else min(8, len(params) - 1)
    macros = [
        {
            "index": i,
            "parameter": i + 1,
            "name": q.name,
            "value": q.value,
            "display": q.str_for_value(q.value),
        }
        for i, q in enumerate(params[1 : 1 + min(count, MACRO_LIMIT)])
    ]
    chains = list(_get(dev, "chains") or ())
    return {
        "name": dev.name,
        "class_name": dev.class_name,
        "drum_rack": bool(_get(dev, "can_have_drum_pads", False)),
        "visible_macro_count": visible,
        "has_macro_mappings": _get(dev, "has_macro_mappings"),
        "macros": macros,
        "variation_count": _get(dev, "variation_count"),
        "selected_variation_index": _get(dev, "selected_variation_index"),
        "chains": [_chain_row(i, c) for i, c in enumerate(chains[:CHAIN_LIMIT])],
        "chains_truncated": len(chains) > CHAIN_LIMIT,
        "mapping": "macro mapping is manual in Live: right-click a control > Map to Macro",
    }


VARIATIONS = ("store", "recall", "delete", "randomize")


def _number_in(q, value, name):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not q.min <= value <= q.max
    ):
        raise Invalid(f"{name} must be a number within {q.min}..{q.max}")
    return float(value)


def set_rack(ctx, p, t):
    """``device`` (a rack) + ``visible_macros`` (1..16), ``variation`` ``{action, index?}``,
    ``insert_chain`` ``{index?}`` and ``chains: [{index, name?, mute?, solo?, volume?, pan?}]``
    (raw mixer values). Pass 1 validates everything, pass 2 writes in order."""
    dev = t["device"].obj
    if not getattr(dev, "can_have_chains", False):
        raise Invalid("'device' must be a rack")
    steps, caps = [], set()

    def gate(cap, members=()):
        require(ctx, cap, members)
        caps.add(cap)

    if p.get("visible_macros") is not None:
        n = p["visible_macros"]
        if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= MACRO_LIMIT:
            raise Invalid("visible_macros must be 1..16")
        gate("rack.visible_macros", ((dev, "visible_macro_count"), (dev, "add_macro")))
        steps.append(("visible_macros", n))
    var = p.get("variation")
    if var is not None:
        action = var.get("action") if isinstance(var, dict) else None
        if action not in VARIATIONS:
            raise Invalid(f"variation.action must be one of {list(VARIATIONS)}")
        if action == "randomize":
            gate("rack.randomize", ((dev, "randomize_macros"),))
        else:
            member = {"store": "store_variation", "recall": "recall_selected_variation"}.get(
                action, "delete_selected_variation"
            )
            gate("rack.variations", ((dev, member), (dev, "selected_variation_index")))
            if action != "store":
                _index(var.get("index"), "variation.index", max(dev.variation_count, 1))
        steps.append(("variation", var))
    ins = p.get("insert_chain")
    if ins is not None:
        gate("rack.insert_chain", ((dev, "insert_chain"),))
        at = ins.get("index", len(dev.chains)) if isinstance(ins, dict) else len(dev.chains)
        steps.append(("insert_chain", _index(at, "insert_chain.index", len(dev.chains) + 1)))
    chains = p.get("chains") or []
    if not isinstance(chains, list) or len(chains) > BATCH_LIMIT:
        raise Invalid(f"chains must be a list of at most {BATCH_LIMIT} edits")
    for k, edit in enumerate(chains):
        if not isinstance(edit, dict):
            raise Invalid(f"chains[{k}] must be an object")
        chain = dev.chains[_index(edit.get("index"), f"chains[{k}].index", len(dev.chains))]
        for key in ("name", "mute", "solo"):
            if key in edit:
                ok = isinstance(edit[key], str) if key == "name" else isinstance(edit[key], bool)
                if not ok:
                    raise Invalid(f"chains[{k}].{key} has the wrong type")
                gate("rack.chain_state", ((chain, key),))
                steps.append(("chain_attr", (chain, key, edit[key])))
        for key, role in (("volume", "volume"), ("pan", "panning")):
            if key in edit:
                gate("rack.chain_mixer", ((chain, "mixer_device"),))
                q = getattr(chain.mixer_device, role)
                steps.append(("chain_attr", (q, "value", _number_in(q, edit[key], key))))
    if not steps:
        raise Invalid("set_rack sets nothing")

    def write(step):
        kind, arg = step
        if kind == "visible_macros":
            while dev.visible_macro_count < arg:
                dev.add_macro()
            while dev.visible_macro_count > arg:
                dev.remove_macro()
            return {"visible_macro_count": dev.visible_macro_count}
        if kind == "variation":
            action = arg["action"]
            if action == "randomize":
                dev.randomize_macros()
            elif action == "store":
                dev.store_variation()
            else:
                dev.selected_variation_index = arg["index"]
                (
                    dev.recall_selected_variation
                    if action == "recall"
                    else dev.delete_selected_variation
                )()
            return {"variation": action, "variation_count": dev.variation_count}
        if kind == "insert_chain":
            before = len(dev.chains)
            dev.insert_chain(arg)
            if len(dev.chains) != before + 1:
                quarantine(ctx, "rack.insert_chain", "no new chain observed")
                raise RuntimeError("insert_chain was not observed")
            return {"chains": len(dev.chains), "inserted": arg}
        obj, key, value = arg
        setattr(obj, key, value)
        return {key: getattr(obj, key)}

    receipt = run_writes(steps, write)
    receipt["unverified"] = sorted(caps)
    return receipt


METHODS = {
    "rack": (rack, READ, None),
    "set_rack": (set_rack, WRITE, (("device", "device"),)),
}
