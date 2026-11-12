"""Clips domain: session and arrangement clip reads, batch create/set, delete/duplicate routes.

One clip address everywhere: ``{track, scene}`` (session) or ``{track, arrangement[,
take_lane]}`` (arrangement, sorted by start). Reads take index addresses; every write takes
references issued by ``ref_issue`` and runs two-pass (validate all, then write with a receipt).
``fire_clip``/``stop_clip``/``clip_slot`` stay for the launch route (batch 2).
"""

import os

from .core import Invalid
from .dom_common import (
    BATCH_LIMIT,
    DISABLED,
    READ,
    SUPPORTED,
    UNVERIFIED,
    WRITE,
    _index,
    _note_specification,
    _number,
    _same,
    _slot,
    clip_address_nodes,
    for_deletion,
    owner_node,
    position_of,
    require,
    run_writes,
    two_pass,
)

ANY_KIND = "any"  # safety.ANY_KIND; importing it here is circular (safety imports dom_*)

CAPABILITIES = {
    "clip.create_audio": (SUPPORTED, "P-08: ClipSlot.create_audio_clip, absolute path"),
    "clip.duplicate": (UNVERIFIED, "ClipSlot.duplicate_clip_to; no 12.2 probe yet"),
    "arrangement.delete_clip": (
        SUPPORTED, "P-19 Basic 12.2, 2026-11-11: delete read back"
    ),
    "arrangement.duplicate": (DISABLED, "Arrangement-to-Arrangement copy remains unqualified"),
    "arrangement.from_session": (
        SUPPORTED, "P-19 Basic 12.2, 2026-11-11: Session copy only; no crash"
    ),
    "arrangement.take_lanes": (DISABLED, "take-lane create/edit crash risk on 12.2 (P-19)"),
}

ROW_LIMIT = 128  # clips per scan read
MARKER_LIMIT = 64  # warp markers per detailed row
MAX_BEATS = 16384.0
MAX_NEW_LENGTH = 1024.0
AUDIO_EXT = (".wav", ".aif", ".aiff", ".flac", ".mp3", ".ogg", ".m4a")
LAUNCH_MODES = ("trigger", "gate", "toggle", "repeat")
QUANTIZATIONS = (
    "global", "none", "8 bars", "4 bars", "2 bars", "1 bar", "1/2", "1/2t", "1/4", "1/4t",
    "1/8", "1/8t", "1/16", "1/16t", "1/32",
)  # fmt: skip
WARP_MODES = ("beats", "tones", "texture", "re_pitch", "complex", "rex", "complex_pro")
CLIP_KINDS = ("clip", "arr_clip")
EPS = 1e-6


def _get(obj, name, default=None):
    try:
        return getattr(obj, name)
    except Exception:  # noqa: BLE001 - a read never fails on one odd member
        return default


def _named(table, value):
    return table[value] if isinstance(value, int) and 0 <= value < len(table) else value


def is_audio(clip):
    return bool(_get(clip, "is_audio_clip", False))


def warp_rows(clip):
    markers = list(_get(clip, "warp_markers", None) or ())[:MARKER_LIMIT]
    return [{"beat_time": m.beat_time, "sample_time": m.sample_time} for m in markers]


def clip_row(clip, detail=False):
    """A compact readback row (``detail`` adds launch, audio and warp fields)."""
    audio = is_audio(clip)
    row = {
        "name": _get(clip, "name"),
        "kind": "audio" if audio else "midi",
        "length": _get(clip, "length"),
        "looping": _get(clip, "looping"),
        "loop": [_get(clip, "loop_start"), _get(clip, "loop_end")],
        "markers": [_get(clip, "start_marker"), _get(clip, "end_marker")],
        "muted": _get(clip, "muted"),
        "color_index": _get(clip, "color_index"),
    }
    if _get(clip, "is_arrangement_clip", False):
        # `length` is the loop/source length; the clip's span on the timeline is start..end.
        row["start"], row["end"] = _get(clip, "start_time"), _get(clip, "end_time")
        if row["start"] is not None and row["end"] is not None:
            row["arrangement_length"] = row["end"] - row["start"]
    else:
        row["is_playing"] = _get(clip, "is_playing")
    if detail:
        row.update(
            launch_mode=_named(LAUNCH_MODES, _get(clip, "launch_mode")),
            launch_quantization=_named(QUANTIZATIONS, _get(clip, "launch_quantization")),
            legato=_get(clip, "legato"),
            velocity_amount=_get(clip, "velocity_amount"),
            signature=[_get(clip, "signature_numerator"), _get(clip, "signature_denominator")],
        )
        if audio:
            row.update(
                gain=_get(clip, "gain"),
                gain_display=_get(clip, "gain_display_string"),
                pitch_coarse=_get(clip, "pitch_coarse"),
                pitch_fine=_get(clip, "pitch_fine"),
                warping=_get(clip, "warping"),
                warp_mode=_named(WARP_MODES, _get(clip, "warp_mode")),
                file_path=_get(clip, "file_path"),
                warp_markers=warp_rows(clip),
            )
    return row


# ---- reads -----------------------------------------------------------------------------------


def _addr(p):
    return {k: p.get(k) for k in ("track", "scene", "arrangement", "take_lane") if k in p}


def get_clips(ctx, p):
    """Rows for explicit ``clips`` addresses, or a scan of session clips (``track``/``scene``
    filters, ``ROW_LIMIT`` rows, ``truncated``)."""
    detail = p.get("detail") is True
    song = ctx.song
    addrs = p.get("clips")
    if addrs is not None:
        if not isinstance(addrs, list) or not 1 <= len(addrs) <= BATCH_LIMIT:
            raise Invalid(f"'clips' must be a list of 1..{BATCH_LIMIT} addresses")
        rows = []
        for addr in addrs:
            if not isinstance(addr, dict):
                raise Invalid("a clip address must be an object")
            if addr.get("arrangement") is None:
                _t, slot = _slot(song, addr)
                if not slot.has_clip:
                    rows.append({**_addr(addr), "empty": True})
                    continue
            clip = clip_address_nodes(song, _addr(addr))[-1][1]
            rows.append({**_addr(addr), **clip_row(clip, detail)})
        return {"clips": rows, "truncated": False}
    tracks = range(len(song.tracks))
    if p.get("track") is not None:
        kind, _track, snap = owner_node(song, p.get("track"))
        tracks = [snap["index"]] if kind == "track" else []  # returns/master have no slots
    scenes = range(len(song.scenes))
    if p.get("scene") is not None:
        scenes = [_index(p.get("scene"), "scene", len(song.scenes))]
    rows, truncated = [], False
    for t in tracks:
        slots = song.tracks[t].clip_slots
        for s in scenes:
            if s >= len(slots) or not slots[s].has_clip:
                continue
            if len(rows) >= ROW_LIMIT:
                truncated = True
                break
            rows.append({"track": t, "scene": s, **clip_row(slots[s].clip, detail)})
    return {"clips": rows, "truncated": truncated}


# ---- shared field validation and writes (live_set_clips, arrangement edits, audio edits) -----


def _bool(value, name):
    if not isinstance(value, bool):
        raise Invalid(f"{name!r} must be a bool")
    return value


def _choice(value, table, name, allowed=None):
    if value not in table:
        raise Invalid(f"{name!r} must be one of {list(table)}")
    index = table.index(value)
    if allowed is not None and index not in allowed:
        raise Invalid(f"{name!r} {value!r} is not available on this clip")
    return index


def _range(value, name):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise Invalid(f"{name!r} must be [start, end]")
    s = _number(value[0], f"{name}[0]", -MAX_BEATS, MAX_BEATS)
    e = _number(value[1], f"{name}[1]", -MAX_BEATS, MAX_BEATS)
    if not s < e:
        raise Invalid(f"{name!r} must have start < end (got {s}, {e})")
    return float(s), float(e)


AUDIO_FIELDS = ("gain", "pitch_coarse", "pitch_fine", "warping", "warp_mode")
PAIRS = (("loop", "loop_start", "loop_end"), ("markers", "start_marker", "end_marker"))
FIELDS = (
    "name", "color_index", "muted", "looping", "loop", "markers", "launch_mode",
    "launch_quantization", "legato", "velocity_amount", "signature",
) + AUDIO_FIELDS  # fmt: skip


def validate_fields(clip, item, where):
    """Checked ``[(attribute, value)]`` writes in a valid order (nothing is written)."""
    if not any(item.get(f) is not None for f in FIELDS):
        return []
    audio = is_audio(clip)
    for f in AUDIO_FIELDS:
        if item.get(f) is not None and not audio:
            raise Invalid(f"{where}: {f!r} needs an audio clip")
    out = []

    def put(attr, value):
        out.append((attr, value))

    v = item.get
    if v("name") is not None:
        if not isinstance(v("name"), str) or len(v("name")) > 256:
            raise Invalid(f"{where}: 'name' must be a string of at most 256 characters")
        put("name", v("name"))
    if v("color_index") is not None:
        c = v("color_index")
        if isinstance(c, bool) or not isinstance(c, int) or not 0 <= c <= 69:
            raise Invalid(f"{where}: 'color_index' must be an integer 0..69")
        put("color_index", c)
    if v("muted") is not None:
        put("muted", _bool(v("muted"), "muted"))
    if v("warping") is not None:
        put("warping", _bool(v("warping"), "warping"))
    if v("warp_mode") is not None:
        allowed = _get(clip, "available_warp_modes", None)
        allowed = set(allowed) if allowed is not None else None
        put("warp_mode", _choice(v("warp_mode"), WARP_MODES, "warp_mode", allowed))
    if v("looping") is not None:
        put("looping", _bool(v("looping"), "looping"))
    for key, start, end in PAIRS:
        if v(key) is not None:
            s, e = _range(v(key), key)
            cs, ce = float(getattr(clip, start)), float(getattr(clip, end))
            # widen first, then narrow: every intermediate pair keeps start < end (P-09)
            put(end, max(ce, e))
            put(start, min(cs, s))
            put(start, s)
            put(end, e)
    if v("launch_mode") is not None:
        put("launch_mode", _choice(v("launch_mode"), LAUNCH_MODES, "launch_mode"))
    if v("launch_quantization") is not None:
        q = _choice(v("launch_quantization"), QUANTIZATIONS, "launch_quantization")
        put("launch_quantization", q)
    if v("legato") is not None:
        put("legato", _bool(v("legato"), "legato"))
    if v("velocity_amount") is not None:
        put("velocity_amount", float(_number(v("velocity_amount"), "velocity_amount", 0, 1)))
    if v("signature") is not None:
        sig = v("signature")
        if (
            not isinstance(sig, (list, tuple))
            or len(sig) != 2
            or not all(isinstance(x, int) and not isinstance(x, bool) for x in sig)
            or not 1 <= sig[0] <= 99
            or sig[1] not in (1, 2, 4, 8, 16)
        ):
            raise Invalid(f"{where}: 'signature' must be [1..99, 1|2|4|8|16]")
        put("signature_numerator", sig[0])
        put("signature_denominator", sig[1])
    if v("gain") is not None:
        put("gain", float(_number(v("gain"), "gain", 0, 1)))
    if v("pitch_coarse") is not None:
        pc = v("pitch_coarse")
        if isinstance(pc, bool) or not isinstance(pc, int) or not -48 <= pc <= 48:
            raise Invalid(f"{where}: 'pitch_coarse' must be an integer -48..48")
        put("pitch_coarse", pc)
    if v("pitch_fine") is not None:
        put("pitch_fine", float(_number(v("pitch_fine"), "pitch_fine", -50, 50)))
    return out


def apply_fields(clip, writes):
    for attr, value in writes:
        setattr(clip, attr, value)


def clip_kind(resolved, where, allowed=CLIP_KINDS):
    kind = resolved.path[-1][0]
    if kind not in allowed:
        raise Invalid(f"{where}: a {kind} is not a clip this method edits ({list(allowed)})")
    return kind


def set_clips(_ctx, p, t):
    """Field writes on session/arrangement clips (two-pass; receipt with detailed readback)."""
    items, resolved = p.get("targets"), t["targets"]

    def validate(i, item):
        clip_kind(resolved[i], f"targets[{i}]")
        clip = resolved[i].obj
        writes = validate_fields(clip, item, f"targets[{i}]")
        if not writes:
            raise Invalid(f"targets[{i}]: nothing to set")
        return clip, writes

    def write(entry):
        clip, writes = entry
        apply_fields(clip, writes)
        return clip_row(clip, detail=True)

    return two_pass(items, validate, write)


# ---- create -------------------------------------------------------------------------------------


def note_specs(notes, where="notes"):
    """Validated ``MidiNoteSpecification`` objects (all extended fields)."""
    from .dom_notes import validated_notes

    rows = validated_notes(notes, where)
    spec = _note_specification()
    if spec is None:
        raise Invalid("Live.Clip.MidiNoteSpecification is unavailable for add_new_notes")
    return tuple(spec(**row) for row in rows)


def audio_file(path, where):
    if not isinstance(path, str) or not path or len(path) > 1024:
        raise Invalid(f"{where}: 'file' must be an absolute path string")
    if not os.path.isabs(path):
        raise Invalid(f"{where}: 'file' must be an absolute path (Live refuses relative paths)")
    if not path.lower().endswith(AUDIO_EXT):
        raise Invalid(f"{where}: 'file' must be an audio file {list(AUDIO_EXT)}")
    if not os.path.isfile(path):
        raise Invalid(f"{where}: no such file: {path}")
    return path


def create_clips(ctx, p, t):
    """New session clips: MIDI (length, optional notes) or audio (file). A slot must be empty
    unless its target says ``replace: true`` (needs the delete permission at the gate); every
    target is validated before the first old clip is deleted, so a refusal deletes nothing.
    A replaced slot's row says ``replaced`` (the old clip's name)."""
    items, resolved = p.get("targets"), t["targets"]
    planned = []  # slots of earlier items in this batch

    def validate(i, item):
        where = f"targets[{i}]"
        slot, track = resolved[i].obj, resolved[i].nodes.get("track")
        if track is None:
            raise Invalid(f"{where}: clips are created on regular tracks only")
        if any(_same(slot, s) for s in planned):
            raise Invalid(f"{where}: this slot is already a target of this call")
        planned.append(slot)
        replace = item.get("replace", False)
        if not isinstance(replace, bool):
            raise Invalid(f"{where}: 'replace' must be a bool")
        if slot.has_clip and not replace:
            raise Invalid(f"{where}: clip slot is occupied")
        kind = item.get("kind", "midi")
        prepared = {"slot": slot, "track": track, "kind": kind, "notes": ()}
        prepared["replace"] = slot.has_clip and replace
        if kind == "midi":
            if not track.has_midi_input:
                raise Invalid(f"{where}: a MIDI clip needs a MIDI track")
            prepared["length"] = float(
                _number(item.get("length", 4.0), "length", 0, MAX_NEW_LENGTH, exclusive=True)
            )
            if item.get("notes"):
                prepared["notes"] = note_specs(item.get("notes"), f"{where}.notes")
        elif kind == "audio":
            require(ctx, "clip.create_audio", ((slot, "create_audio_clip"),))
            if track.has_midi_input:
                raise Invalid(f"{where}: an audio clip needs an audio track (P-08)")
            if item.get("notes"):
                raise Invalid(f"{where}: 'notes' are for MIDI clips")
            prepared["file"] = audio_file(item.get("file"), where)
        else:
            raise Invalid(f"{where}: 'kind' must be 'midi' or 'audio'")
        prepared["fields"] = [
            w
            for w in (
                ("name", item.get("name")),
                ("color_index", item.get("color_index")),
            )
            if w[1] is not None
        ]
        if prepared["fields"]:
            validate_fields(_Blank(kind), dict(prepared["fields"]), where)
        return prepared

    def write(e):
        slot = e["slot"]
        replaced = None
        if e["replace"] and slot.has_clip:
            replaced = slot.clip.name
            slot.delete_clip()
        if e["kind"] == "midi":
            slot.create_clip(e["length"])
        else:
            slot.create_audio_clip(e["file"])
        clip = slot.clip
        apply_fields(clip, e["fields"])
        ids = clip.add_new_notes(e["notes"]) if e["notes"] else ()
        song = ctx.song
        row = {
            "track": position_of(song.tracks, e["track"]),
            "scene": position_of(e["track"].clip_slots, slot),
            **clip_row(clip),
        }
        if e["notes"]:
            row["note_ids"] = list(ids or ())
        if replaced is not None:
            row["replaced"] = replaced
        return row

    return two_pass(items, validate, write)


class _Blank:
    """Stand-in clip for validating create-time fields."""

    def __init__(self, kind):
        self.is_audio_clip = kind == "audio"


# ---- structural routes (live_delete / live_duplicate, contract section 5) -----------------------


def _owner(resolved):
    return resolved.path[0][1]


def _in_take_lane(resolved):
    return any(n[0] == "take_lane" for n in resolved.path)


def delete_clips(ctx, p, t):
    """Delete session clips (slot emptied) and arrangement clips; deepest/highest first."""
    resolved = t["targets"]
    for i, r in enumerate(resolved):
        if clip_kind(r, f"targets[{i}]") == "arr_clip":
            if _in_take_lane(r):
                require(ctx, "arrangement.take_lanes")
            require(ctx, "arrangement.delete_clip", ((_owner(r), "delete_clip"),))
    ordered = for_deletion(resolved)

    def write(r):
        target = next(i for i, x in enumerate(resolved) if x is r)
        if r.path[-1][0] == "clip":
            r.nodes["slot"].delete_clip()
            return {"target": target, "kind": "clip", "deleted": True}
        _owner(r).delete_clip(r.obj)
        return {"target": target, "kind": "arr_clip", "deleted": True}

    out = run_writes(ordered, write)
    if any(r.path[-1][0] == "arr_clip" for r in resolved):
        out["unverified"] = ["arrangement.delete_clip"]
    return out


def duplicate_clips(ctx, p, t):
    """Copy each session clip into the next empty slot below it on its track
    (``ClipSlot.duplicate_clip_to``; nothing is overwritten, no scene is created). Arrangement
    duplication is disabled on 12.2 (P-19)."""
    items, resolved = p.get("targets"), t["targets"]
    taken = []  # slots promised to earlier items of this batch

    def validate(i, _item):
        where = f"targets[{i}]"
        if clip_kind(resolved[i], where) == "arr_clip":
            require(ctx, "arrangement.duplicate")
        slot, track = resolved[i].nodes["slot"], resolved[i].nodes.get("track")
        if track is None:
            raise Invalid(f"{where}: only regular-track clips can be duplicated")
        require(ctx, "clip.duplicate", ((slot, "duplicate_clip_to"),))
        slots = track.clip_slots
        start = position_of(slots, slot) + 1
        for k in range(start, len(slots)):
            dest = slots[k]
            if not dest.has_clip and not any(dest is s for s in taken):
                taken.append(dest)
                return slot, track, dest
        raise Invalid(f"{where}: no empty slot below this clip; add a scene first")

    def write(e):
        slot, track, dest = e
        slot.duplicate_clip_to(dest)
        return {
            "track": position_of(ctx.song.tracks, track),
            "scene": position_of(track.clip_slots, dest),
            **clip_row(dest.clip),
        }

    return two_pass(items, validate, write)


# ---- launch (kept for the batch-2 launch route; settle readback in the host) -------------------


def clip_slot(ctx, p):
    """Read a slot by indices; returns references for the slot and its clip (if any)."""
    track, slot = _slot(ctx.song, p)
    scene_obj = ctx.song.scenes[p["scene"]]
    chain = (("track", track, {}), ("slot", slot, {"index": p["scene"], "scene": scene_obj}))
    out = {"slot": ctx.safety.issue(*chain), "has_clip": bool(slot.has_clip)}
    if slot.has_clip:
        out["clip"] = ctx.safety.issue(*chain, ("clip", slot.clip, {}))
    return out


def get_clip(ctx, p):
    """One session clip's compact row by index (the launch settle readback)."""
    addr = {"track": p.get("track"), "scene": p.get("scene")}
    return clip_row(clip_address_nodes(ctx.song, addr)[-1][1])


def fire_clip(_ctx, _p, t):
    clip = t["clip"].obj
    clip.fire()
    return clip_row(clip)


def stop_clip(_ctx, _p, t):
    clip = t["clip"].obj
    clip.stop()
    return clip_row(clip)


METHODS = {
    "get_clips": (get_clips, READ, None),
    "clip_slot": (clip_slot, READ, None),
    "get_clip": (get_clip, READ, None),
    "create_clips": (create_clips, WRITE, (("targets", "ref", "slot"),)),
    "set_clips": (set_clips, WRITE, (("targets", "ref", ANY_KIND),)),
    "delete_clips": (delete_clips, WRITE, (("targets", "ref", ANY_KIND),)),
    "duplicate_clips": (duplicate_clips, WRITE, (("targets", "ref", ANY_KIND),)),
    "fire_clip": (fire_clip, WRITE, (("clip", "clip"),)),
    "stop_clip": (stop_clip, WRITE, (("clip", "clip"),)),
}
