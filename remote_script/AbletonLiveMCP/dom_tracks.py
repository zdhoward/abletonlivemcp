"""Tracks domain (batch 2): read tracks/returns/master, batch create, batch set (state, routing),
mixer (dB by bisection inside one call, P-06) and the structural routes ``delete_tracks`` /
``duplicate_tracks`` behind the public ``live_delete``/``live_duplicate`` facades.

``tracks``, ``create_track``, ``set_track_name`` and ``set_track_color`` stay as internal bridge
methods (``server._row``, the browser tools and older tests use them); no public tool maps 1:1.

Evidence: P-06 go (mixer values, dB bisection, crossfade 0/1/2, activator); P-05 partial
(``delete_track`` removes but its undo did not restore the fixture; ``delete_return_track`` and
duplicates worked). P-17 routing is unrun: routing writes are ``unverified`` and only accept a
``display_name`` listed in the track's own ``available_*`` lists (allowlist).
"""

import math
import re

from .dom_common import (
    BATCH_LIMIT,
    LIST_LIMIT,
    READ,
    SAMPLE_LIMIT,
    WRITE,
    _index,
    _number,
    for_deletion,
    owner_node,
    position_of,
    require,
    run_writes,
)

# safety.ANY_KIND; importing it from .safety is circular (safety imports every dom_* first).
ANY_KIND = "any"

CAPABILITIES = {
    "track.routing": ("unverified", "P-17 unrun: allowlisted display_name writes only"),
    "track.monitoring": ("supported", "current_monitoring_state in P-01 inventory"),
    "track.fold": ("unverified", "fold_state on group tracks; final proof decides"),
    "mixer.db": ("supported", "P-06: bisection over str_for_value, -6 dB -> -5.992 dB"),
    "mixer.crossfade": ("supported", "P-06: crossfade_assign 0/1/2 written and read back"),
    "mixer.master": ("supported", "P-06: master crossfader/cue_volume ranges read"),
    "track.delete": ("unverified", "P-05: delete works; undo did not restore the fixture"),
    "track.duplicate": ("unverified", "P-05: shape known; final proof decides"),
}

INCLUDES = ("mixer", "devices", "slots", "routing", "meters", "groups")
MONITORING = {"in": 0, "auto": 1, "off": 2}
CROSSFADE = {"A": 0, "none": 1, "B": 2}
DB_TOLERANCE = 0.05
BISECT_STEPS = 16
SLOT_LIMIT = 64
ROUTING_LIMIT = 32
_DB = re.compile(r"^\s*(-?inf|-?\d+(?:\.\d+)?)\s*dB\s*$")


def _get(obj, attribute, default=None):
    try:
        return getattr(obj, attribute)
    except Exception:  # noqa: BLE001 - a read never fails the whole reply
        return default


# ---- legacy internal methods ----------------------------------------------------------------


def tracks(ctx, _p):
    return [
        {
            "index": i,
            "ref": ctx.safety.issue(("track", t, {})),
            "name": t.name,
            "color_index": getattr(t, "color_index", None),
            "has_midi_input": t.has_midi_input,
            "devices": [{"name": d.name, "class_name": d.class_name} for d in t.devices],
        }
        for i, t in enumerate(ctx.song.tracks)
    ]


def create_track(ctx, p, _t):
    song = ctx.song
    kind = p.get("kind")
    index = int(p.get("index", -1))
    if kind == "midi":
        song.create_midi_track(index)
    elif kind == "audio":
        song.create_audio_track(index)
    else:
        raise ValueError("'kind' must be 'midi' or 'audio'")
    return {"track_count": len(song.tracks)}


def set_track_name(_ctx, p, t):
    track = t["track"].obj
    track.name = str(p["name"])
    return {"name": track.name}


def set_track_color(_ctx, p, t):
    track = t["track"].obj
    track.color_index = int(p["color_index"])
    return {"color_index": track.color_index}


# ---- dB conversion (P-06) -------------------------------------------------------------------


def parse_db(text):
    """``"-5.992 dB"`` -> -5.992, ``"-inf dB"`` -> -inf; None when it is not a dB display."""
    match = _DB.match(str(text))
    if not match:
        return None
    return float(match.group(1).replace("inf", "Infinity"))


class _Budget:
    """Display conversions per request (``SAMPLE_LIMIT``): bounded main-thread work."""

    def __init__(self):
        self.left = SAMPLE_LIMIT

    def display(self, param, value):
        if self.left <= 0:
            raise ValueError("too many dB conversions in one call; split the batch")
        self.left -= 1
        return param.str_for_value(value)


def db_to_value(param, db, budget, label):
    """The parameter value whose display is ``db`` (bisection; the display rises with value)."""
    lo, hi = float(param.min), float(param.max)
    top = parse_db(budget.display(param, hi))
    if top is None:
        raise ValueError(f"{label}: this parameter has no dB display")
    if db > top + DB_TOLERANCE:
        raise ValueError(f"{label}: {db} dB is above the maximum {top} dB")
    if db >= top:
        return hi
    for _ in range(BISECT_STEPS):
        mid = (lo + hi) / 2
        shown = parse_db(budget.display(param, mid))
        if shown is None:
            raise ValueError(f"{label}: unexpected display while converting dB")
        if abs(shown - db) <= DB_TOLERANCE / 5:
            return mid
        if shown < db:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _param_row(param):
    value = _get(param, "value")
    row = {"value": value}
    try:
        row["display"] = param.str_for_value(value)
    except Exception:  # noqa: BLE001
        row["display"] = None
    return row


# ---- get_tracks -----------------------------------------------------------------------------


def _kind(song, track):
    if track == song.master_track:
        return "master"
    if any(track == r for r in song.return_tracks):
        return "return"
    if _get(track, "is_foldable"):
        return "group"
    return "midi" if _get(track, "has_midi_input") else "audio"


def _mixer(song, track):
    mixer = track.mixer_device
    out = {
        "volume": _param_row(mixer.volume),
        "pan": _get(mixer.panning, "value"),
        "sends": [
            {"send": i, **_param_row(s)} for i, s in enumerate(list(_get(mixer, "sends", ())))
        ],
    }
    activator = _get(mixer, "track_activator")
    if activator is not None:
        out["activator"] = bool(activator.value)
    assign = _get(mixer, "crossfade_assign")
    if assign is not None:
        out["crossfade"] = {v: k for k, v in CROSSFADE.items()}.get(int(assign))
    if track == song.master_track:
        out["crossfader"] = _get(mixer.crossfader, "value")
        out["cue_volume"] = _param_row(mixer.cue_volume)
    return out


def _routing(track):
    out = {}
    for side in ("input", "output"):
        kind = _get(track, f"{side}_routing_type")
        channel = _get(track, f"{side}_routing_channel")
        if kind is None:
            continue
        out[f"{side}_routing"] = {
            "type": _get(kind, "display_name"),
            "channel": _get(channel, "display_name"),
            "available": [
                _get(t, "display_name")
                for t in list(_get(track, f"available_{side}_routing_types", ()) or ())[
                    :ROUTING_LIMIT
                ]
            ],
        }
    return out


def _track_row(ctx, sel, track, include):
    song = ctx.song
    kind = _kind(song, track)
    row = {
        "track": sel,
        "name": track.name,
        "kind": kind,
        "color_index": _get(track, "color_index"),
        "mute": _get(track, "mute"),
        "solo": _get(track, "solo"),
    }
    if kind not in ("return", "master"):
        row["arm"] = _get(track, "arm") if _get(track, "can_be_armed") else None
        monitoring = _get(track, "current_monitoring_state")
        row["monitoring"] = {v: k for k, v in MONITORING.items()}.get(monitoring)
    if "groups" in include:
        row["is_foldable"] = _get(track, "is_foldable")
        row["fold_state"] = _get(track, "fold_state") if row["is_foldable"] else None
        group = _get(track, "group_track")
        row["group"] = None
        if group is not None:
            for i, t in enumerate(song.tracks):
                if t == group:
                    row["group"] = i
    if "mixer" in include:
        row["mixer"] = _mixer(song, track)
    if "devices" in include:
        row["devices"] = [
            {"index": i, "name": d.name, "class_name": d.class_name}
            for i, d in enumerate(list(track.devices)[:LIST_LIMIT])
        ]
    if "slots" in include and kind not in ("return", "master"):
        slots = list(track.clip_slots)[:SLOT_LIMIT]
        row["slots"] = [
            {
                "scene": i,
                "has_clip": s.has_clip,
                "clip": s.clip.name if s.has_clip else None,
                "is_playing": _get(s, "is_playing"),
                "is_triggered": _get(s, "is_triggered"),
            }
            for i, s in enumerate(slots)
        ]
    if "routing" in include:
        row.update(_routing(track))
    if "meters" in include:
        row["meters"] = {f: _get(track, f"output_meter_{f}") for f in ("left", "right", "level")}
    return row


def _all_selectors(song):
    sels = list(range(min(len(song.tracks), LIST_LIMIT)))
    sels += [f"return:{i}" for i in range(len(song.return_tracks))]
    return sels + ["master"]


def get_tracks(ctx, p):
    song = ctx.song
    include = p.get("include") or []
    if not isinstance(include, list) or any(s not in INCLUDES for s in include):
        raise ValueError(f"'include' must be a list of {list(INCLUDES)}")
    sels = p.get("tracks")
    if sels is None:
        sels = _all_selectors(song)
    elif not isinstance(sels, list) or not 1 <= len(sels) <= LIST_LIMIT:
        raise ValueError(f"'tracks' must be a list of 1..{LIST_LIMIT} track selectors")
    rows = []
    for sel in sels:
        _kind_name, track, _snap = owner_node(song, sel)
        rows.append(_track_row(ctx, sel, track, include))
    return {
        "generation": ctx.safety.generation,
        "track_count": len(song.tracks),
        "return_count": len(song.return_tracks),
        "tracks": rows,
    }


# ---- create_tracks --------------------------------------------------------------------------


def _name(value, label):
    if not isinstance(value, str) or len(value) > 256:
        raise ValueError(f"{label}: 'name' must be a string of at most 256 characters")
    return value


def _color(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 69:
        raise ValueError(f"{label}: 'color_index' must be an integer 0..69")
    return value


def _items(p, key):
    items = p.get(key)
    if not isinstance(items, list) or not 1 <= len(items) <= BATCH_LIMIT:
        raise ValueError(f"{key!r} must be a list of 1..{BATCH_LIMIT} objects")
    if not all(isinstance(i, dict) for i in items):
        raise ValueError(f"every item in {key!r} must be an object")
    return items


def create_tracks(ctx, p, _t):
    song = ctx.song
    items = _items(p, "tracks")
    prepared = []
    for n, item in enumerate(items):
        label = f"tracks[{n}]"
        kind = item.get("kind")
        if kind not in ("midi", "audio", "return"):
            raise ValueError(f"{label}: 'kind' must be 'midi', 'audio' or 'return'")
        index = item.get("index", -1)
        if isinstance(index, bool) or not isinstance(index, int) or index < -1:
            raise ValueError(f"{label}: 'index' must be -1 (end) or a track index")
        if kind == "return" and index != -1:
            raise ValueError(f"{label}: a return track is always added at the end (index -1)")
        name = _name(item["name"], label) if item.get("name") is not None else None
        color = _color(item["color_index"], label) if item.get("color_index") is not None else None
        prepared.append((kind, index, name, color))

    def write(entry):
        kind, index, name, color = entry
        if kind == "return":
            song.create_return_track()
            seq, prefix = song.return_tracks, "return:"
            at = len(seq) - 1
        else:
            count = len(song.tracks)
            at = count if index == -1 or index > count else index
            (song.create_midi_track if kind == "midi" else song.create_audio_track)(
                -1 if index == -1 else at
            )
            seq, prefix = song.tracks, ""
            at = len(seq) - 1 if index == -1 else at
        track = seq[at]
        if name is not None:
            track.name = name
        if color is not None:
            track.color_index = color
        return {
            "kind": kind,
            "track": f"{prefix}{at}" if prefix else at,
            "name": track.name,
            "color_index": _get(track, "color_index"),
        }

    return run_writes(prepared, write)


# ---- set_tracks -----------------------------------------------------------------------------


def _bool_field(item, key, label):
    if not isinstance(item[key], bool):
        raise ValueError(f"{label}: {key!r} must be a bool")
    return item[key]


def _routing_entry(ctx, track, item, side, label):
    """Allowlist: ``type`` must be a display_name in ``available_<side>_routing_types``; the
    channel (optional) is matched after the type is set, against the then-available channels."""
    spec = item[f"{side}_routing"]
    if not isinstance(spec, dict) or not isinstance(spec.get("type"), str):
        raise ValueError(f"{label}: '{side}_routing' must be {{type, channel?}}")
    attr = f"available_{side}_routing_types"
    require(ctx, "track.routing", ((track, attr), (track, f"{side}_routing_type")))
    types = [t for t in getattr(track, attr) if t.display_name == spec["type"]]
    if len(types) != 1:
        names = [t.display_name for t in list(getattr(track, attr))[:ROUTING_LIMIT]]
        raise ValueError(f"{label}: {side} routing type must be one of {names}")
    channel = spec.get("channel")
    if channel is not None and not isinstance(channel, str):
        raise ValueError(f"{label}: routing 'channel' must be a display name string")

    def apply():
        setattr(track, f"{side}_routing_type", types[0])
        if channel is not None:
            found = [
                c
                for c in getattr(track, f"available_{side}_routing_channels")
                if c.display_name == channel
            ]
            if len(found) != 1:
                raise RuntimeError(f"no unique {side} routing channel {channel!r}")
            setattr(track, f"{side}_routing_channel", found[0])
        return {
            "type": getattr(track, f"{side}_routing_type").display_name,
            "channel": _get(_get(track, f"{side}_routing_channel"), "display_name"),
        }

    return apply


def _set_attr(obj, attribute, value):
    def apply():
        setattr(obj, attribute, value)
        return getattr(obj, attribute)

    return apply


def _track_fields(ctx, resolved, item, label):
    track, kind = resolved.obj, resolved.path[-1][0]
    fields = []
    if item.get("name") is not None:
        fields.append(("name", _set_attr(track, "name", _name(item["name"], label))))
    if item.get("color_index") is not None:
        color = _color(item["color_index"], label)
        fields.append(("color_index", _set_attr(track, "color_index", color)))
    for key in ("mute", "solo"):
        if item.get(key) is not None:
            if kind == "master":
                raise ValueError(f"{label}: the master track has no {key!r}")
            fields.append((key, _set_attr(track, key, _bool_field(item, key, label))))
    if item.get("arm") is not None:
        if kind != "track" or not _get(track, "can_be_armed"):
            raise ValueError(f"{label}: this track cannot be armed")
        fields.append(("arm", _set_attr(track, "arm", _bool_field(item, "arm", label))))
    if item.get("monitoring") is not None:
        state = MONITORING.get(item["monitoring"])
        if state is None or kind != "track":
            raise ValueError(f"{label}: 'monitoring' is in|auto|off on a regular track")
        require(ctx, "track.monitoring", ((track, "current_monitoring_state"),))
        fields.append(("monitoring", _set_attr(track, "current_monitoring_state", state)))
    if item.get("fold") is not None:
        require(ctx, "track.fold", ((track, "fold_state"),))
        if not _get(track, "is_foldable"):
            raise ValueError(f"{label}: only a group track can be folded")
        fold = int(_bool_field(item, "fold", label))
        fields.append(("fold", _set_attr(track, "fold_state", fold)))
    for side in ("input", "output"):
        if item.get(f"{side}_routing") is not None:
            if kind == "master" and side == "input":
                raise ValueError(f"{label}: the master track has no input routing")
            fields.append((f"{side}_routing", _routing_entry(ctx, track, item, side, label)))
    if not fields:
        raise ValueError(f"{label}: give at least one field to set")
    return fields


def _flatten(ctx, p, t, build):
    """Pass 1 over gate-resolved list targets -> ``(target, field, apply, requested)`` entries."""
    prepared = []
    for n, (item, resolved) in enumerate(zip(p["targets"], t["targets"], strict=True)):
        for field, apply, *rest in build(ctx, resolved, item, f"targets[{n}]"):
            prepared.append((n, field, apply, rest[0] if rest else None))
    return prepared


def _write(entry):
    target, field, apply, requested = entry
    row = {"target": target, "field": field, "actual": apply()}
    if requested is not None:
        row["requested"] = requested
    return row


def _owner_kinds(t, allowed):
    for n, resolved in enumerate(t["targets"]):
        if resolved.path[-1][0] not in allowed:
            raise ValueError(f"targets[{n}] must be one of {list(allowed)}")


def set_tracks(ctx, p, t):
    _owner_kinds(t, ("track", "return_track", "master"))
    return run_writes(_flatten(ctx, p, t, _track_fields), _write)


# ---- set_mixer ------------------------------------------------------------------------------


def _mixer_value(param, item, key_db, key_value, budget, label, lo=None, hi=None):
    """A ``*_db`` (bisection) or a raw value -> ``(value, requested_db)``."""
    if item.get(key_db) is not None and item.get(key_value) is not None:
        raise ValueError(f"{label}: give {key_db!r} or {key_value!r}, not both")
    if item.get(key_db) is not None:
        db = _number(item[key_db], key_db, -math.inf)
        return db_to_value(param, float(db), budget, label), float(db)
    lo = param.min if lo is None else lo
    hi = param.max if hi is None else hi
    return float(_number(item[key_value], key_value, lo, hi)), None


def _write_param(param, value, requested_db):
    def apply():
        param.value = value
        row = _param_row(param)
        if requested_db is not None:
            shown = parse_db(row["display"])
            row["matches"] = shown is not None and abs(shown - requested_db) <= DB_TOLERANCE
        return row

    return apply


def _mixer_fields(budget):
    def build(ctx, resolved, item, label):
        track, kind = resolved.obj, resolved.path[-1][0]
        mixer = track.mixer_device
        fields = []
        if item.get("volume_db") is not None or item.get("volume") is not None:
            require(ctx, "mixer.db")
            value, db = _mixer_value(mixer.volume, item, "volume_db", "volume", budget, label)
            fields.append(("volume", _write_param(mixer.volume, value, db), db))
        if item.get("pan") is not None:
            pan = float(_number(item["pan"], "pan", -1.0, 1.0))
            fields.append(("pan", _write_param(mixer.panning, pan, None), pan))
        for n, send in enumerate(item.get("sends") or []):
            if not isinstance(send, dict):
                raise ValueError(f"{label}: each send must be an object {{send, db|value}}")
            sends = list(mixer.sends)
            i = _index(send.get("send"), f"{label}.sends[{n}].send", len(sends))
            value, db = _mixer_value(sends[i], send, "db", "value", budget, label)
            fields.append((f"send[{i}]", _write_param(sends[i], value, db), db))
        if item.get("activator") is not None:
            if kind == "master":
                raise ValueError(f"{label}: the master track has no activator")
            on = 1.0 if _bool_field(item, "activator", label) else 0.0
            fields.append(("activator", _write_param(mixer.track_activator, on, None), None))
        if item.get("crossfade") is not None:
            assign = CROSSFADE.get(item["crossfade"])
            if assign is None or kind == "master":
                raise ValueError(f"{label}: 'crossfade' is A|none|B on a non-master track")
            require(ctx, "mixer.crossfade", ((mixer, "crossfade_assign"),))
            fields.append(("crossfade", _set_attr(mixer, "crossfade_assign", assign), None))
        for key in ("crossfader", "cue_volume_db", "cue_volume"):
            if item.get(key) is not None and kind != "master":
                raise ValueError(f"{label}: {key!r} is a master-track field")
        if kind == "master":
            if item.get("crossfader") is not None:
                require(ctx, "mixer.master", ((mixer, "crossfader"),))
                x = float(_number(item["crossfader"], "crossfader", -1.0, 1.0))
                fields.append(("crossfader", _write_param(mixer.crossfader, x, None), x))
            if item.get("cue_volume_db") is not None or item.get("cue_volume") is not None:
                require(ctx, "mixer.master", ((mixer, "cue_volume"),))
                cue = mixer.cue_volume
                value, db = _mixer_value(cue, item, "cue_volume_db", "cue_volume", budget, label)
                fields.append(("cue_volume", _write_param(cue, value, db), db))
        if not fields:
            raise ValueError(f"{label}: give at least one mixer field")
        return fields

    return build


def set_mixer(ctx, p, t):
    _owner_kinds(t, ("track", "return_track", "master"))
    receipt = run_writes(_flatten(ctx, p, t, _mixer_fields(_Budget())), _write)
    receipt["mismatched"] = [
        f"targets[{r['target']}].{r['field']}"
        for r in receipt["applied"]
        if isinstance(r["actual"], dict) and r["actual"].get("matches") is False
    ]
    return receipt


# ---- structural routes (live_delete / live_duplicate) -----------------------------------------


def delete_tracks(ctx, p, t):
    song = ctx.song
    _owner_kinds(t, ("track", "return_track"))
    resolved = t["targets"]
    require(ctx, "track.delete")
    regular = sum(1 for r in resolved if r.path[-1][0] == "track")
    if regular and regular >= len(song.tracks):
        raise ValueError("a Set must keep at least one regular track")

    def write(r):
        kind, name = r.path[-1][0], r.obj.name
        if kind == "track":
            at = position_of(song.tracks, r.obj)
            song.delete_track(at)
        else:
            at = position_of(song.return_tracks, r.obj)
            song.delete_return_track(at)
        return {"kind": kind, "index": at, "name": name}

    return run_writes(for_deletion(resolved), write)


def duplicate_tracks(ctx, p, t):
    song = ctx.song
    _owner_kinds(t, ("track",))
    require(ctx, "track.duplicate", ((song, "duplicate_track"),))
    ordered = sorted(t["targets"], key=lambda r: -r.path[-1][2].get("index", 0))

    def write(r):
        at = position_of(song.tracks, r.obj)
        song.duplicate_track(at)
        copy = song.tracks[at + 1]
        return {"kind": "track", "source": at, "track": at + 1, "name": copy.name}

    return run_writes(ordered, write)


TARGETS = (("targets", "ref", ANY_KIND),)

METHODS = {
    "tracks": (tracks, READ, None),
    "get_tracks": (get_tracks, READ, None),
    "create_track": (create_track, WRITE, ()),
    "create_tracks": (create_tracks, WRITE, ()),
    "set_track_name": (set_track_name, WRITE, (("track", "track"),)),
    "set_track_color": (set_track_color, WRITE, (("track", "track"),)),
    "set_tracks": (set_tracks, WRITE, TARGETS),
    "set_mixer": (set_mixer, WRITE, TARGETS),
    "delete_tracks": (delete_tracks, WRITE, TARGETS),
    "duplicate_tracks": (duplicate_tracks, WRITE, TARGETS),
}
