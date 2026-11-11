"""Toolset `drums`: Drum Rack pads, conversions, Simpler and the capped drum-rack builder.

Every operation has its own remote capability gate (P-12/13/20 unrun): a failure or unknown
outcome gates only that action, and every receipt lists what is still `unverified`.
"""

from __future__ import annotations

from typing import Literal

from .. import chain, server
from ..models import DevicePath, TrackSel
from ..models_devices import ConvertTarget, DrumRole, PadCopy, PadEdit, SliceEdit
from ..server import _call, _create, _overwrite, _read, _untrusted, issue_refs, unsupported
from .chain import run_plan
from .devices import at_device, device_ref, loc

UNTRUSTED = "live_object_text_untrusted"


def _rack_path(path) -> list:
    if not at_device(path):
        raise ValueError("'path' must end at a Drum Rack device")
    return list(path)


@_read
def live_get_drum_rack(track: TrackSel, path: DevicePath, include_empty: bool = False) -> dict:
    """Pads of a Drum Rack (path to the rack device): note, name, mute/solo, chain devices,
    choke group. include_empty lists all 128 pads."""
    params = {**loc(track, _rack_path(path)), "include_empty": include_empty}
    return _untrusted(_call("drum_rack", params))


@_overwrite
def live_set_drum_pads(
    track: TrackSel,
    path: DevicePath,
    pads: list[PadEdit] | None = None,
    copy: PadCopy | None = None,
) -> dict:
    """Edit pads of a Drum Rack (by note): mute, solo, name, choke_group, clear (needs the pad's
    current expect_name); or copy one pad onto an EMPTY pad. Validated before any write."""
    rack = _rack_path(path)
    if bool(pads) == (copy is not None):
        raise ValueError("give 'pads' (1..64 edits) or 'copy', not both")
    if copy is not None:
        raise unsupported(
            "drum pad copy",
            "the final Live 12.2 proof did not establish copying into an empty pad; "
            "disabled pending real-Live verification",
        )
    if len(pads) > 64:
        raise ValueError("'pads' must hold at most 64 edits")
    selectors = []
    for p in pads:
        if p.clear and p.expect_name is None:
            raise ValueError(f"pad {p.note}: clear needs expect_name (the pad's current name)")
        sel = {"kind": "drum_pad", **loc(track, rack + [f"pad:{p.note}"])}
        if p.expect_name is not None:
            sel["expect_name"] = p.expect_name
        selectors.append(sel)
    refs = issue_refs(selectors)
    items = []
    for p, r in zip(pads, refs, strict=True):
        item = {"ref": r["ref"], **p.model_dump(exclude_none=True, exclude={"note", "clear"})}
        if p.clear:
            item["clear"] = True
        items.append(item)
    return {**_call("set_drum_pads", {"targets": items}), "provenance": UNTRUSTED}


ConvertAction = Literal[
    "audio_to_midi",
    "drum_rack_from_audio_clip",
    "simpler_from_audio_clip",
    "midi_track_from_drum_pad",
    "sliced_simpler_to_drum_rack",
    "devices_to_drum_pad",
]


def _convert_selector(action: str, t: ConvertTarget) -> dict:
    if action.endswith("audio_clip") or action == "audio_to_midi":
        if (t.scene is None) == (t.arrangement is None):
            raise ValueError(f"{action} needs the clip: 'scene' or 'arrangement'")
        if t.scene is not None:
            return {"kind": "clip", "track": t.track, "scene": t.scene}
        return {"kind": "arr_clip", "track": t.track, "arrangement": t.arrangement}
    if action == "midi_track_from_drum_pad":
        if not t.path or not isinstance(t.path[-1], str):
            raise ValueError("midi_track_from_drum_pad needs a path ending at 'pad:N'")
        return {"kind": "drum_pad", **loc(t.track, t.path)}
    if action == "sliced_simpler_to_drum_rack":
        return {"kind": "device", **loc(t.track, _rack_path(t.path))}
    if not isinstance(t.track, int):
        raise ValueError("devices_to_drum_pad takes a regular track")
    return {"kind": "track", "track": t.track}


@_create
def live_convert(
    action: ConvertAction,
    target: ConvertTarget,
    midi_type: Literal["drums", "harmony", "melody"] = "melody",
) -> dict:
    """Run one Live conversion (adds tracks/devices; nothing is deleted): audio_to_midi
    (midi_type), drum_rack_from_audio_clip, simpler_from_audio_clip, midi_track_from_drum_pad,
    sliced_simpler_to_drum_rack, devices_to_drum_pad. Re-read tracks afterwards."""
    sel = _convert_selector(action, target)
    ref = issue_refs([sel])[0]["ref"]
    params = {"action": action, "targets": [{"kind": sel["kind"], "ref": ref}]}
    if action == "audio_to_midi":
        params["midi_type"] = midi_type
    return _call("convert", params)


@_read
def live_get_simpler(track: TrackSel, path: DevicePath) -> dict:
    """A Simpler's mode/voices and its sample: markers, gain, warp, slicing and slices."""
    return _untrusted(_call("simpler", loc(track, _rack_path(path))))


@_overwrite
def live_set_simpler(
    track: TrackSel,
    path: DevicePath,
    device_fields: dict | None = None,
    sample_fields: dict | None = None,
    slices: SliceEdit | None = None,
) -> dict:
    """Set Simpler fields (playback_mode, voices, retrigger, ...), sample fields (start_marker,
    end_marker, gain, warping, warp_mode, slicing_*) and slices (insert/remove sample times,
    clear, reset). Validated first; the receipt says how far it got."""
    params = {"device": device_ref(track, _rack_path(path))}
    if device_fields:
        params["device_fields"] = device_fields
    if sample_fields:
        params["sample_fields"] = sample_fields
    if slices is not None:
        params["slices"] = slices.model_dump()
    return _call("set_simpler", params)


@_read
def live_plan_drum_rack(track: int, pads: list[DrumRole]) -> dict:
    """Dry run: an empty Drum Rack on an EMPTY MIDI track, then one browser item (root + path,
    checked in its folder) per pad note; at most 16 pads. Returns plan_id, unverified."""
    plan = chain.make_drum_plan(_call, track, [p.model_dump() for p in pads])
    server._plans.add(plan)
    return plan.model_dump(mode="json")


@_create
def live_build_drum_rack(plan_id: str) -> dict:
    """Build a live_plan_drum_rack plan exactly once (Set and target re-checked). Stops at the
    first pad not observed; never retries, deletes or substitutes. Reuse returns the receipt."""
    return run_plan(plan_id, False, ("drum_rack",))
