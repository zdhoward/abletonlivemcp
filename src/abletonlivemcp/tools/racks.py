"""Toolset `racks`: rack macros, variations, chains and chain mixers (P-11 unrun).

Macro values go through the display solver (like any parameter). Native macro mapping is not
offered on 12.2: `live_get_rack` returns the manual mapping guidance instead.
"""

from __future__ import annotations

from .. import chain
from ..errors import Invalid
from ..models import DevicePath, TrackSel
from ..models_devices import ChainEdit, MacroSet, Variation
from ..server import _call, _overwrite, _read, _untrusted
from .devices import at_device, device_ref, loc


def _rack(path) -> list:
    if not at_device(path):
        raise Invalid("'path' must end at a rack device")
    return list(path)


@_read
def live_get_rack(track: TrackSel, path: DevicePath) -> dict:
    """A rack's macros (value, display), variations and chains (devices, mute/solo, volume,
    pan). Macro mapping is manual in Live; the reply says how."""
    return _untrusted(_call("rack", loc(track, _rack(path))))


@_overwrite
def live_set_rack(
    track: TrackSel,
    path: DevicePath,
    macros: list[MacroSet] | None = None,
    visible_macros: int | None = None,
    variation: Variation | None = None,
    chains: list[ChainEdit] | None = None,
) -> dict:
    """Set macro values ("50 %", {"raw": x}), visible macro count, store/recall/delete/randomize a
    variation, and chain name/mute/solo/volume/pan (raw). Rack state is validated before any
    write; macros are written last. Receipt lists `unverified` abilities."""
    where = loc(track, _rack(path))
    out: dict = {"status": "complete"}
    rack_edit = {}
    if visible_macros is not None:
        rack_edit["visible_macros"] = visible_macros
    if variation is not None:
        rack_edit["variation"] = variation.model_dump(exclude_none=True)
    if chains:
        rack_edit["chains"] = [c.model_dump(exclude_none=True) for c in chains]
    if not rack_edit and not macros:
        raise Invalid("live_set_rack sets nothing")
    if rack_edit:
        out["rack"] = _call("set_rack", {"device": device_ref(track, where["path"]), **rack_edit})
        if out["rack"].get("status") != "complete":
            out["status"] = "partial"
            return out
    if macros:
        params = _call("device_parameters", where)
        wanted = [(params[m.macro], chain._target_value(m.value)) for m in macros]
        try:
            results, problems = chain.set_parameters(_call, where, wanted)
        except chain.WriteInterrupted as exc:
            if not rack_edit and not exc.results:
                raise exc.cause from exc
            results, problems = exc.results, exc.problems + [str(exc.cause)]
        out["macros"] = results
        out["problems"] = problems
        if problems or not all(r["exact"] for r in results):
            out["status"] = "partial"
    return out
