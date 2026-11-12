"""Drums domain: drum rack pads, pad copy, Live.Conversions and Simpler (P-12/13/20 unrun).

Every operation is its own capability (``unverified`` until the final proof): a failure or an
unknown outcome gates only that action. Every refusal comes before the native call.
"""

from .core import Invalid
from .dom_common import (
    BATCH_LIMIT,
    READ,
    UNVERIFIED,
    WRITE,
    Refused,
    _index,
    position_of,
    quarantine,
    require,
    run_writes,
    unsupported,
)
from .dom_devices import _get, locate_device

ANY_KIND = "any"  # safety.ANY_KIND; importing it here is circular (safety imports dom_*)

PAD_DEVICES = 8  # device names listed per pad
SLICE_LIMIT = 128

CAPABILITIES = {
    "drum_pad.mute_solo": (UNVERIFIED, "P-12 unrun: DrumPad.mute/solo"),
    "drum_pad.rename": (UNVERIFIED, "P-12 unrun: DrumPad.name setter"),
    "drum_pad.clear": (UNVERIFIED, "P-12 unrun: DrumPad.delete_all_chains"),
    "drum_pad.choke": (UNVERIFIED, "P-12 unrun: DrumChain.choke_group/out_note"),
    "drum_pad.copy": (UNVERIFIED, "P-12 unrun: RackDevice.copy_pad(source, destination)"),
    "convert.audio_to_midi": (UNVERIFIED, "P-13 unrun: Conversions.audio_to_midi_clip"),
    "convert.drum_rack_from_audio_clip": (UNVERIFIED, "P-13 unrun"),
    "convert.simpler_from_audio_clip": (UNVERIFIED, "P-13 unrun"),
    "convert.midi_track_from_drum_pad": (UNVERIFIED, "P-13 unrun"),
    "convert.sliced_simpler_to_drum_rack": (UNVERIFIED, "P-13 unrun"),
    "convert.devices_to_drum_pad": (UNVERIFIED, "P-13 unrun"),
    "simpler.device": (UNVERIFIED, "P-20 unrun: Simpler mode/voice fields"),
    "simpler.sample": (UNVERIFIED, "P-20 unrun: Sample marker/gain/warp fields"),
    "simpler.slices": (UNVERIFIED, "P-20 unrun: insert/remove/clear/reset slices"),
}


def _plain(value):
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    try:
        return int(value)  # Live enums
    except Exception:  # noqa: BLE001
        return str(value)[:120]


def _drum_rack(ctx, p):
    nodes = locate_device(ctx.song, p)
    dev = nodes[-1][1]
    if not getattr(dev, "can_have_drum_pads", False):
        raise Invalid("that device is not a Drum Rack")
    return nodes, dev


# ---- reads ----------------------------------------------------------------------------------


def _pad_row(pad):
    chains = list(_get(pad, "chains") or ())
    row = {
        "note": pad.note,
        "name": _get(pad, "name"),
        "mute": _get(pad, "mute"),
        "solo": _get(pad, "solo"),
        "chains": len(chains),
    }
    if chains:
        first = chains[0]
        row["devices"] = [d.name for d in list(first.devices)[:PAD_DEVICES]]
        row["choke_group"] = _plain(_get(first, "choke_group"))
        row["out_note"] = _plain(_get(first, "out_note"))
    return row


def drum_rack(ctx, p):
    """Pads of a Drum Rack: filled pads, or all 128 with ``include_empty``."""
    _nodes, dev = _drum_rack(ctx, p)
    pads = [x for x in dev.drum_pads if p.get("include_empty") or len(x.chains)]
    selected = _get(_get(dev, "view"), "selected_drum_pad")
    return {
        "name": dev.name,
        "pads": [_pad_row(x) for x in pads],
        "selected_note": _get(selected, "note"),
        "chains": len(_get(dev, "chains") or ()),
    }


DEVICE_FIELDS = ("playback_mode", "voices", "retrigger", "multi_sample_mode", "pad_slicing")
SAMPLE_FIELDS = (
    "file_path",
    "length",
    "sample_rate",
    "start_marker",
    "end_marker",
    "gain",
    "warping",
    "warp_mode",
    "slicing_style",
    "slicing_sensitivity",
    "slicing_beat_division",
    "slicing_region_count",
)


def _simpler(ctx, p):
    nodes = locate_device(ctx.song, p)
    dev = nodes[-1][1]
    if dev.class_name != "OriginalSimpler":
        raise Invalid(f"that device is a {dev.class_name}, not Simpler")
    return dev


def simpler(ctx, p):
    dev = _simpler(ctx, p)
    sample = _get(dev, "sample")
    out = {"name": dev.name, "device": {f: _plain(_get(dev, f)) for f in DEVICE_FIELDS}}
    if sample is None:
        out["sample"] = None
        return out
    out["sample"] = {f: _plain(_get(sample, f)) for f in SAMPLE_FIELDS}
    slices = list(_get(sample, "slices") or ())
    out["sample"]["slices"] = [_plain(s) for s in slices[:SLICE_LIMIT]]
    out["sample"]["slices_truncated"] = len(slices) > SLICE_LIMIT
    return out


# ---- pad writes -----------------------------------------------------------------------------


def set_drum_pads(ctx, p, t):
    """``targets: [{kind: "drum_pad", ref, mute?, solo?, name?, clear?, choke_group?}]``."""
    items = p.get("targets") or []
    unverified, prepared = set(), []
    for i, item in enumerate(items):
        pad = t["targets"][i].obj
        edit = {}
        for key in ("mute", "solo"):
            if key in item:
                if not isinstance(item[key], bool):
                    raise Invalid(f"targets[{i}].{key} must be true or false")
                require(ctx, "drum_pad.mute_solo", ((pad, key),))
                unverified.add("drum_pad.mute_solo")
                edit[key] = item[key]
        if "name" in item:
            if not isinstance(item["name"], str) or not 1 <= len(item["name"]) <= 256:
                raise Invalid(f"targets[{i}].name must be a string of 1..256 characters")
            require(ctx, "drum_pad.rename", ((pad, "name"),))
            unverified.add("drum_pad.rename")
            edit["name"] = item["name"]
        if "choke_group" in item:
            g = item["choke_group"]
            if isinstance(g, bool) or not isinstance(g, int) or not 0 <= g <= 16:
                raise Invalid(f"targets[{i}].choke_group must be 0..16")
            if not len(pad.chains):
                raise Invalid(f"targets[{i}]: the pad is empty")
            require(ctx, "drum_pad.choke", ((pad.chains[0], "choke_group"),))
            unverified.add("drum_pad.choke")
            edit["choke_group"] = g
        if item.get("clear") is True:
            require(ctx, "drum_pad.clear", ((pad, "delete_all_chains"),))
            unverified.add("drum_pad.clear")
            edit["clear"] = True
        if not edit:
            raise Invalid(f"targets[{i}] sets nothing")
        prepared.append((pad, edit))

    def write(entry):
        pad, edit = entry
        for key in ("mute", "solo", "name"):
            if key in edit:
                setattr(pad, key, edit[key])
        if "choke_group" in edit:
            pad.chains[0].choke_group = edit["choke_group"]
        if edit.get("clear"):
            pad.delete_all_chains()
        return _pad_row(pad)

    receipt = run_writes(prepared, write)
    receipt["unverified"] = sorted(unverified)
    return receipt


def copy_drum_pad(ctx, p, t):
    """``device`` (a Drum Rack) + ``source``/``destination`` notes; the destination must be
    empty (nothing is overwritten)."""
    rack = t["device"].obj
    if not getattr(rack, "can_have_drum_pads", False):
        raise Invalid("'device' must be a Drum Rack")
    require(ctx, "drum_pad.copy", ((rack, "copy_pad"),))
    src = _index(p.get("source"), "source", 128)
    dst = _index(p.get("destination"), "destination", 128)
    pads = {x.note: x for x in rack.drum_pads}
    if src == dst or src not in pads or dst not in pads:
        raise Invalid("'source' and 'destination' must be two different pad notes")
    if not len(pads[src].chains):
        raise Invalid("the source pad is empty")
    if len(pads[dst].chains):
        raise Refused("target_occupied", "the destination pad is not empty; clear it first")
    rack.copy_pad(src, dst)
    if not len(pads[dst].chains):
        quarantine(ctx, "drum_pad.copy", "copy not observed on the destination pad")
        raise RuntimeError("the copy was not observed (outcome unknown)")
    return {
        "copied": [src, dst],
        "destination": _pad_row(pads[dst]),
        "unverified": ["drum_pad.copy"],
    }


# ---- conversions ----------------------------------------------------------------------------


def _conversions():
    try:
        import Live  # noqa: PLC0415 - only inside Live
    except ImportError:
        return None
    return getattr(Live, "Conversions", None)


CONVERSIONS = {  # action -> (Conversions function, target kinds)
    "audio_to_midi": ("audio_to_midi_clip", ("clip", "arr_clip")),
    "drum_rack_from_audio_clip": ("create_drum_rack_from_audio_clip", ("clip", "arr_clip")),
    "simpler_from_audio_clip": ("create_midi_track_with_simpler", ("clip", "arr_clip")),
    "midi_track_from_drum_pad": ("create_midi_track_from_drum_pad", ("drum_pad",)),
    "sliced_simpler_to_drum_rack": ("sliced_simpler_to_drum_rack", ("device",)),
    "devices_to_drum_pad": ("move_devices_on_track_to_new_drum_rack_pad", ("track",)),
}
MIDI_TYPES = ("drums", "harmony", "melody")


def convert(ctx, p, t):
    """One Live.Conversions action on one target (``targets: [{kind, ref}]``)."""
    action = p.get("action")
    if action not in CONVERSIONS:
        raise Invalid(f"'action' must be one of {sorted(CONVERSIONS)}")
    if len(t["targets"]) != 1:
        raise Invalid("'targets' must hold exactly one target")
    ref = t["targets"][0]
    fname, kinds = CONVERSIONS[action]
    kind = ref.path[-1][0]
    if kind not in kinds:
        raise Invalid(f"{action} takes a {' or '.join(kinds)}, not a {kind}")
    cap = "convert." + action
    conv = _conversions()
    if conv is None:
        raise unsupported(cap, "Live.Conversions is not available")
    require(ctx, cap, ((conv, fname),))
    song, obj = ctx.song, ref.obj
    args = (song, obj)
    if kind in ("clip", "arr_clip") and not getattr(obj, "is_audio_clip", False):
        raise Invalid(f"{action} needs an audio clip")
    if action == "audio_to_midi":
        mode = p.get("midi_type", "melody")
        enum = getattr(conv, "AudioToMidiType", None)
        if mode not in MIDI_TYPES or enum is None or not hasattr(enum, mode):
            raise unsupported(cap, f"midi_type must be one of {list(MIDI_TYPES)} on this Live")
        args = (song, obj, getattr(enum, mode))
    elif action == "sliced_simpler_to_drum_rack":
        if obj.class_name != "OriginalSimpler":
            raise Invalid("sliced_simpler_to_drum_rack needs a Simpler device")
    elif action == "devices_to_drum_pad":
        if not len(obj.devices):
            raise Invalid("the track has no devices to move")
        args = (song, position_of(song.tracks, obj))
    tracks_before = len(song.tracks)
    try:
        returned = getattr(conv, fname)(*args)
    except Exception as exc:
        quarantine(ctx, cap, f"native call raised {type(exc).__name__}")
        raise
    return {
        "action": action,
        "tracks_before": tracks_before,
        "tracks_after": len(song.tracks),
        "returned": _plain(returned),
        "unverified": [cap],
        "note": "re-read the affected tracks: a conversion may finish on a later tick",
    }


# ---- Simpler writes -------------------------------------------------------------------------

DEVICE_WRITABLE = ("playback_mode", "voices", "retrigger", "multi_sample_mode", "pad_slicing")
SAMPLE_WRITABLE = (
    "start_marker",
    "end_marker",
    "gain",
    "warping",
    "warp_mode",
    "slicing_style",
    "slicing_sensitivity",
    "slicing_beat_division",
)


def _scalar(value, name):
    if not isinstance(value, (bool, int, float)):
        raise Invalid(f"{name!r} must be a number or boolean")
    return value


def set_simpler(ctx, p, t):
    """``device`` (Simpler) + ``device_fields``, ``sample_fields`` (objects) and ``slices``
    (``{insert: [t], remove: [t], clear: bool, reset: bool}``). Validated, then written in order;
    the receipt says how far it got."""
    dev = t["device"].obj
    if dev.class_name != "OriginalSimpler":
        raise Invalid("'device' must be a Simpler")
    steps = []
    for key, value in sorted((p.get("device_fields") or {}).items()):
        if key not in DEVICE_WRITABLE:
            raise Invalid(f"device field {key!r} is not one of {list(DEVICE_WRITABLE)}")
        require(ctx, "simpler.device", ((dev, key),))
        steps.append(("device", key, _scalar(value, key)))
    sample = _get(dev, "sample")
    fields = p.get("sample_fields") or {}
    slices = p.get("slices") or {}
    if (fields or slices) and sample is None:
        raise Invalid("this Simpler has no sample")
    for key, value in sorted(fields.items()):
        if key not in SAMPLE_WRITABLE:
            raise Invalid(f"sample field {key!r} is not one of {list(SAMPLE_WRITABLE)}")
        require(ctx, "simpler.sample", ((sample, key),))
        steps.append(("sample", key, _scalar(value, key)))
    for op in ("clear", "reset"):
        if slices.get(op) is True:
            member = "clear_slices" if op == "clear" else "reset_slices"
            require(ctx, "simpler.slices", ((sample, member),))
            steps.append(("slices", member, None))
    for op, member in (("insert", "insert_slice"), ("remove", "remove_slice")):
        times = slices.get(op) or []
        if not isinstance(times, list) or len(times) > BATCH_LIMIT:
            raise Invalid(f"slices.{op} must be a list of at most {BATCH_LIMIT} sample times")
        for x in times:
            if isinstance(x, bool) or not isinstance(x, int) or x < 0:
                raise Invalid(f"slices.{op} times are sample positions (integers >= 0)")
            require(ctx, "simpler.slices", ((sample, member),))
            steps.append(("slices", member, x))
    if not steps:
        raise Invalid("set_simpler sets nothing")

    def write(step):
        where, key, value = step
        if where == "device":
            setattr(dev, key, value)
            return {key: _plain(_get(dev, key))}
        if where == "sample":
            setattr(sample, key, value)
            return {key: _plain(_get(sample, key))}
        getattr(sample, key)(*(() if value is None else (value,)))
        return {key: value, "slices": len(list(_get(sample, "slices") or ()))}

    receipt = run_writes(steps, write)
    receipt["unverified"] = sorted({"simpler." + s[0] for s in steps})
    return receipt


METHODS = {
    "drum_rack": (drum_rack, READ, None),
    "simpler": (simpler, READ, None),
    "set_drum_pads": (set_drum_pads, WRITE, (("targets", "ref", "drum_pad"),)),
    "copy_drum_pad": (copy_drum_pad, WRITE, (("device", "device"),)),
    "convert": (convert, WRITE, (("targets", "ref", ANY_KIND),)),
    "set_simpler": (set_simpler, WRITE, (("device", "device"),)),
}
