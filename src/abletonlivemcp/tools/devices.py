"""Device tools: device lists and parameters (nested, return, master), device state, moves."""

from __future__ import annotations

from .. import chain
from ..models import DevicePath, RawValue, ResponseFormat, TrackSel
from ..models_devices import DeviceEdit, ParamWrite, container_kind
from ..server import (
    _call,
    _explain,
    _overwrite,
    _read,
    _untrusted,
    issue_refs,
    shape,
    unsupported,
)

PARAMS_CONCISE = ("index", "name", "value", "display", "min", "max", "is_quantized", "items")
DEVICES_CONCISE = ("index", "name", "class_name", "type", "on", "rack", "drum_rack", "chains")
PAGE = 128
UNTRUSTED = "live_object_text_untrusted"


def loc(track, path) -> dict:
    return {"track": track, "path": list(path)} if path else {"track": track}


def at_device(path) -> bool:
    return bool(path) and len(path) % 2 == 1


def device_ref(track, path, expect_name: str | None = None) -> str:
    """A fresh device reference (name-checked when ``expect_name`` is given)."""
    if not at_device(path):
        raise ValueError("'path' must end at a device: [device] or [device, chain, device, ...]")
    sel = {"kind": "device", **loc(track, path)}
    if expect_name is not None:
        sel["expect_name"] = expect_name
    return issue_refs([sel])[0]["ref"]


@_read
def live_get_device_parameters(
    track: TrackSel,
    path: DevicePath | None = None,
    offset: int = 0,
    limit: int = PAGE,
    response_format: ResponseFormat = "concise",
) -> dict:
    """No path, or a path ending at a chain index or "pad:N": list the devices there. A path
    ending at a device ([d] or [d, chain, d, ...]): its parameters (value, range, display,
    items, default), paged (limit <= 128). track: index, "return:N" or "master".
    Rack macros and chains: live_get_rack; drum pads: live_get_drum_rack (opt-in toolsets)."""
    if not at_device(path):
        info = _call("device_list", loc(track, path))
        info["devices"] = shape(info["devices"], response_format, DEVICES_CONCISE)
        return _untrusted(info)
    if not 1 <= limit <= PAGE or offset < 0:
        raise ValueError(f"'offset' must be >= 0 and 'limit' 1..{PAGE}")
    rows = _call("device_parameters", {**loc(track, path), "offset": offset, "limit": limit})
    rows = [{k: v for k, v in r.items() if k != "ref"} for r in rows]
    more = len(rows) == limit
    concise = PARAMS_CONCISE + ("default",)
    return _untrusted(
        {
            "parameters": shape(rows, response_format, concise),
            "next_offset": offset + len(rows) if more else None,
        }
    )


def _target(value):
    return {"raw": value.raw} if isinstance(value, RawValue) else value


def _special_rows(rows: list[dict], kinds: list[str]) -> list[dict]:
    return [
        {"name": r["name"], "requested": k, "actual": r["display"], "actual_raw": r["value"],
         "exact": True, "off_target": False, "raw": False}
        for r, k in zip(rows, kinds, strict=True)
    ]  # fmt: skip


@_overwrite
def live_set_device_parameters(
    track: TrackSel, path: DevicePath, settings: list[ParamWrite]
) -> dict:
    """Set 1..32 parameters of one device, by name or index. value: a display target ("-18 dB",
    4, "Vocal", true) solved against Live's display, or {"raw": x}; or reset (default) or
    re_enable_automation. Results show actual vs requested and `exact`. Disabled or
    macro-controlled parameters are refused.
    On/off or rename: live_set_devices; rack macros: live_set_rack (racks toolset)."""
    if not 1 <= len(settings) <= 32:
        raise ValueError("'settings' must hold 1..32 items")
    where = loc(track, path)
    if not at_device(path):
        raise ValueError("'path' must end at a device")
    params = _call("device_parameters", where)
    items, special, kinds = [], [], []
    for s in settings:
        if isinstance(s.parameter, int):
            if s.parameter >= len(params):
                raise ValueError(f"parameter {s.parameter} does not exist ({len(params)})")
            q = params[s.parameter]
        else:
            q = chain._resolve(params, s.parameter)
        if not q.get("is_enabled", True):
            raise ValueError(f"{q['name']!r} is disabled or controlled elsewhere")
        modes = [s.value is not None, s.reset, s.re_enable_automation]
        if sum(modes) != 1:
            raise ValueError(
                f"{q['name']!r}: give exactly one of value, reset, re_enable_automation"
            )
        if s.value is not None:
            items.append((q, _target(s.value)))
            continue
        kind = "reset" if s.reset else "re_enable_automation"
        special.append({"parameter": q["ref"], kind: True})
        kinds.append(kind)
    results, unverified = [], []
    if special:  # first: a refusal here is still "not applied"
        reply = _call("set_device_parameters", {"writes": special})
        results += _special_rows(reply["results"], kinds)
        unverified += reply.get("unverified", [])
    problems: list[str] = []
    try:
        if items:
            done, problems = chain.set_parameters(_call, where, items)
            results += done
    except chain.WriteInterrupted as exc:
        if not results and not exc.results:
            raise exc.cause from exc
        return {
            "status": "partial",
            "results": results + exc.results,
            "problems": exc.problems + [_explain(exc.cause)],
            "unverified": unverified,
        }
    ok = not problems and all(r["exact"] for r in results)
    return {
        "status": "complete" if ok else "partial",
        "results": results,
        "problems": problems,
        "unverified": unverified,
    }


@_overwrite
def live_set_devices(targets: list[DeviceEdit]) -> dict:
    """Turn devices on/off, rename or collapse them (1..64 targets, each its track + path to a
    device; optional expect_name). All are validated before any write; the receipt has
    per-item outcomes and `unverified` abilities.
    Parameter values: live_set_device_parameters."""
    if not 1 <= len(targets) <= 64:
        raise ValueError("'targets' must hold 1..64 devices")
    selectors = []
    for t in targets:
        if not at_device(t.path):
            raise ValueError("every 'path' must end at a device")
        if t.on is None and t.name is None and t.collapsed is None:
            raise ValueError("each target sets on, name or collapsed")
        sel = {"kind": "device", **loc(t.track, t.path)}
        if t.expect_name is not None:
            sel["expect_name"] = t.expect_name
        selectors.append(sel)
    refs = issue_refs(selectors)
    items = []
    for t, r in zip(targets, refs, strict=True):
        item = {"ref": r["ref"]}
        if t.expect_name is not None:
            item["expect_name"] = t.expect_name
        item.update(
            {k: getattr(t, k) for k in ("on", "name", "collapsed") if getattr(t, k) is not None}
        )
        items.append(item)
    return {**_call("set_devices", {"targets": items}), "provenance": UNTRUSTED}


@_overwrite
def live_move_device(
    track: TrackSel,
    path: DevicePath,
    to_track: TrackSel,
    to_path: DevicePath | None = None,
    position: int | None = None,
    expect_name: str | None = None,
) -> dict:
    """Move one device to another track/return/master, or into a rack chain or drum pad
    (to_path ending at a chain index or "pad:N"); position defaults to the end. Reordering
    within the same container is refused (Live 12.2). Verified at the destination."""
    if not at_device(path):
        raise ValueError("'path' must end at a device")
    if to_path and at_device(to_path):
        raise ValueError("'to_path' must end at a chain index or 'pad:N'")
    if to_track == track and list(to_path or []) == list(path[:-1]):
        raise unsupported("device reorder", "Live 12.2 refuses moves within one container (P-04)")
    if position is not None and position < 0:
        raise ValueError("'position' must be >= 0")
    dest_kind = container_kind(to_track, to_path)
    sel = {"kind": "device", **loc(track, path)}
    if expect_name is not None:
        sel["expect_name"] = expect_name
    dev, dest = issue_refs([sel, {"kind": dest_kind, **loc(to_track, to_path)}])
    first = {"kind": "device", "ref": dev["ref"]}
    if expect_name is not None:
        first["expect_name"] = expect_name
    params = {"targets": [first, {"kind": dest_kind, "ref": dest["ref"]}]}
    if position is not None:
        params["position"] = position
    return {**_call("move_device", params), "provenance": UNTRUSTED}
