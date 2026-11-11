"""Toolset `automation`: Session-clip envelopes. Arrangement automation refuses on Live 12.2
(``automation_envelope`` returns None there, P-10)."""

from __future__ import annotations

from .. import chain
from ..models import ClipRef, ResponseFormat
from ..models_clips import AutomationEdit, AutoParam, Span
from ..server import _call, _overwrite, _read, clip_selector, issue_refs, unsupported

ARRANGEMENT = "automation_envelope returns None on arrangement clips in Live 12.2 (P-10)"


def param_selector(track, p: AutoParam) -> dict:
    if (p.mixer is None) == (p.device is None or p.parameter is None):
        raise ValueError("parameter: give either {device, parameter} or {mixer[, send]}")
    if p.mixer is not None:
        sel = {"kind": "mixer_param", "track": track, "role": p.mixer}
        if p.mixer == "send":
            if p.send is None:
                raise ValueError("parameter.send is required for mixer 'send'")
            sel["send"] = p.send
        return sel
    index = p.parameter
    if isinstance(index, str):  # a name: resolve it on the device, like live_set_device_parameters
        rows = _call("device_parameters", {"track": track, "path": list(p.device)})
        index = chain._resolve(rows, index)["index"]
    return {"kind": "param", "track": track, "path": p.device, "parameter": index}


def _session_only(clip) -> None:
    if clip_selector(clip)["kind"] != "clip":
        raise unsupported("arrangement automation", ARRANGEMENT)


@_read
def live_get_automation(
    clip: ClipRef,
    parameter: AutoParam,
    sample_times: list[float] | None = None,
    response_format: ResponseFormat = "concise",
) -> dict:
    """One Session clip's envelope for a parameter: events and value_at_time samples (16
    evenly spaced, or sample_times beats). concise omits the event list."""
    _session_only(clip)
    sel = param_selector(clip.track, parameter)
    params = {**clip.model_dump(exclude_none=True), "parameter": sel}
    if sample_times is not None:
        params["sample_times"] = sample_times
    out = _call("get_automation", params)
    if response_format == "concise":
        out.pop("events", None)
    return out


@_overwrite
def live_set_automation(targets: list[AutomationEdit]) -> dict:
    """Write Session-clip automation: optional clear, delete_range [start,end], then steps
    [{time,length,value}] and ramps [{start,end,from,to,steps}] (value in the parameter's
    raw min..max). Alternatively points [{time,value}] (2-3, increasing) creates linear
    segments over the full clip (requires clear=true); a middle point tunes the shape.
    Live retains coincident boundary guard
    events. No native Bezier curvature setter exists. Points cannot mix with steps/ramps.
    Readback samples and actual event counts per item."""
    for t in targets:
        _session_only(t.clip)
    sels = [clip_selector(t.clip) for t in targets]
    sels += [param_selector(t.clip.track, t.parameter) for t in targets]
    refs = issue_refs(sels)
    n = len(targets)
    items = []
    for t, clip_ref, param_ref in zip(targets, refs[:n], refs[n:], strict=True):
        body = t.model_dump(exclude_none=True, by_alias=True, exclude={"clip", "parameter"})
        items.append(
            {
                "kind": clip_ref["kind"],
                "ref": clip_ref["ref"],
                "param": param_ref["ref"],
                "param_kind": param_ref["kind"],
                **body,
            }
        )
    return _call("set_automation", {"targets": items})


__all__ = ["Span", "live_get_automation", "live_set_automation"]
