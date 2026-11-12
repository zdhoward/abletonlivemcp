"""Device extras domain: plugin presets, parameter names, A/B compare, latency (P-15 unrun).

Two opt-in tools only. Every write is its own capability and refuses before the native call.
"""

from .core import Invalid
from .dom_common import READ, UNVERIFIED, WRITE, _index, require
from .dom_devices import _get, locate_device

PRESET_LIMIT = 128
NAME_LIMIT = 256

CAPABILITIES = {
    "devx.preset_select": (UNVERIFIED, "P-15 unrun: PluginDevice.selected_preset_index"),
    "devx.ab_compare": (UNVERIFIED, "not probed: Device A/B compare (12.x)"),
}


def _texts(values, cap):
    out = [str(v) for v in list(values or ())[:cap]]
    return out, len(list(values or ())) > cap


def device_extras(ctx, p):
    dev = locate_device(ctx.song, p)[-1][1]
    out = {
        "name": dev.name,
        "class_name": dev.class_name,
        "class_display_name": _get(dev, "class_display_name"),
        "latency_samples": _get(dev, "latency_in_samples"),
        "latency_ms": _get(dev, "latency_in_ms"),
        "can_compare_ab": _get(dev, "can_compare_ab"),
        "using_preset_b": _get(dev, "is_using_compare_preset_b"),
    }
    presets = _get(dev, "presets")
    if presets is not None:
        out["presets"], out["presets_truncated"] = _texts(presets, PRESET_LIMIT)
        out["selected_preset_index"] = _get(dev, "selected_preset_index")
    names = _get(dev, "get_parameter_names")
    if callable(names):
        try:
            out["plugin_parameter_names"], out["names_truncated"] = _texts(names(), NAME_LIMIT)
        except Exception as exc:  # noqa: BLE001 - a read reports it, never fails the device read
            out["plugin_parameter_names_error"] = f"{type(exc).__name__}"
    return out


AB_ACTIONS = ("save", "a", "b")


def set_device_extras(ctx, p, t):
    """``device`` + ``preset_index`` (plugin preset) and/or ``compare`` (save|a|b)."""
    dev = t["device"].obj
    steps, caps = [], []
    if p.get("preset_index") is not None:
        require(ctx, "devx.preset_select", ((dev, "selected_preset_index"), (dev, "presets")))
        steps.append(("preset", _index(p["preset_index"], "preset_index", len(dev.presets))))
        caps.append("devx.preset_select")
    if p.get("compare") is not None:
        if p["compare"] not in AB_ACTIONS:
            raise Invalid(f"compare must be one of {list(AB_ACTIONS)}")
        member = (
            "save_preset_to_compare_ab_slot"
            if p["compare"] == "save"
            else "is_using_compare_preset_b"
        )
        require(ctx, "devx.ab_compare", ((dev, member),))
        if not _get(dev, "can_compare_ab", False):
            raise Invalid("this device cannot compare A/B")
        steps.append(("compare", p["compare"]))
        caps.append("devx.ab_compare")
    if not steps:
        raise Invalid("set_device_extras sets nothing")
    out = {}
    for kind, value in steps:  # at most two writes: pass 1 has validated both
        if kind == "preset":
            dev.selected_preset_index = value
            out["selected_preset_index"] = dev.selected_preset_index
        elif value == "save":
            dev.save_preset_to_compare_ab_slot()
            out["saved"] = True
        else:
            dev.is_using_compare_preset_b = value == "b"
            out["using_preset_b"] = dev.is_using_compare_preset_b
    out["unverified"] = caps
    return out


METHODS = {
    "device_extras": (device_extras, READ, None),
    "set_device_extras": (set_device_extras, WRITE, (("device", "device"),)),
}
