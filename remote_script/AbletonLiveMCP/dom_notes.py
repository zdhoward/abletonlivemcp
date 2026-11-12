"""Notes domain: extended MIDI note reads and one-call note edits (P-07 shapes).

Binding Live 12.2 facts (P-07): ``apply_note_modifications`` accepts only the raw object that
``get_notes_extended`` returned (never a list()/tuple() copy), so modifications mutate those note
objects in place and pass that same object back. Notes past the clip end are kept by Live but sit
outside a clip-length read window, so every read here uses a wide window and note IDs.
"""

from .core import Invalid
from .dom_common import (
    NOTE_LIMIT,
    READ,
    WRITE,
    _number,
    clip_address_nodes,
    require,
    run_writes,
)

ANY_KIND = "any"  # safety.ANY_KIND; importing it here is circular (safety imports dom_*)

CAPABILITIES = {
    "notes.extended": ("supported", "P-07: get_notes_extended/apply_note_modifications/ids"),
}

WIDE_FROM, WIDE_SPAN = -16384.0, 65536.0  # every note Live keeps, past the clip end included
READ_LIMIT = 1000
MAX_TIME = 16384.0
FIELDS = (
    "note_id", "pitch", "start_time", "duration", "velocity", "mute", "probability",
    "velocity_deviation", "release_velocity",
)  # fmt: skip
EDITABLE = FIELDS[1:]
DEFAULTS = {"velocity": 100.0, "mute": False, "probability": 1.0, "velocity_deviation": 0.0,
            "release_velocity": 64.0}  # fmt: skip


def note_row(n):
    return {f: getattr(n, f) for f in FIELDS}


def _int(value, name, lo, hi):
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise Invalid(f"{name!r} must be an integer {lo}..{hi}")
    return value


def checked_field(name, value, where):
    """One extended note field, range-checked."""
    label = f"{where}.{name}"
    if name == "pitch":
        return _int(value, label, 0, 127)
    if name == "start_time":
        return float(_number(value, label, 0, MAX_TIME))
    if name == "duration":
        return float(_number(value, label, 0, 16384, exclusive=True))
    if name == "velocity":
        return float(_number(value, label, 1, 127))
    if name == "mute":
        if not isinstance(value, bool):
            raise Invalid(f"{label!r} must be a bool")
        return value
    if name == "probability":
        return float(_number(value, label, 0, 1))
    if name == "velocity_deviation":
        return float(_number(value, label, -127, 127))
    if name == "release_velocity":
        return float(_number(value, label, 0, 127))
    raise Invalid(f"{where}: unknown note field {name!r}")


def validated_notes(notes, where="notes"):
    """New notes -> MidiNoteSpecification keyword dicts (defaults filled)."""
    if not isinstance(notes, list) or len(notes) > NOTE_LIMIT:
        raise Invalid(f"{where!r} must be a list of at most {NOTE_LIMIT} notes")
    rows = []
    for i, note in enumerate(notes):
        here = f"{where}[{i}]"
        if not isinstance(note, dict):
            raise Invalid(f"{here}: each note must be an object")
        unknown = set(note) - set(EDITABLE)
        if unknown:
            raise Invalid(f"{here}: unknown note field(s) {sorted(unknown)}")
        for required in ("pitch", "start_time", "duration"):
            if note.get(required) is None:
                raise Invalid(f"{here}: {required!r} is required")
        row = dict(DEFAULTS)
        row.update({k: checked_field(k, v, here) for k, v in note.items() if v is not None})
        rows.append(row)
    return rows


def midi_clip(song, p, members=("get_notes_extended",)):
    addr = {k: p.get(k) for k in ("track", "scene", "arrangement", "take_lane") if k in p}
    clip = clip_address_nodes(song, addr)[-1][1]
    return checked_midi(clip, members)


def checked_midi(clip, members=("get_notes_extended",)):
    if not getattr(clip, "is_midi_clip", False):
        raise Invalid("notes need a MIDI clip")
    for m in members:
        if not hasattr(clip, m):
            raise Invalid(f"this clip has no {m!r}")
    return clip


def wide(clip):
    """The raw note object of the wide window (pass it back untouched to apply)."""
    return clip.get_notes_extended(0, 128, WIDE_FROM, WIDE_SPAN)


def _clip_end(clip):
    return float(getattr(clip, "end_marker", clip.length))


def get_notes(ctx, p):
    """Notes with IDs and every extended field, sorted by time then pitch; paged by offset.
    The default window is wide (notes past the clip end are listed and counted)."""
    clip = midi_clip(ctx.song, p)
    pitch_from = _int(p.get("pitch_from", 0), "pitch_from", 0, 127)
    pitch_span = _int(p.get("pitch_span", 128), "pitch_span", 1, 128)
    time_from = p.get("time_from")
    time_from = WIDE_FROM if time_from is None else float(_number(time_from, "time_from", -16384))
    span = p.get("time_span")
    span = WIDE_SPAN if span is None else float(_number(span, "time_span", 0, WIDE_SPAN, True))
    limit = _int(p.get("limit", 500), "limit", 1, READ_LIMIT)
    offset = _int(p.get("offset", 0), "offset", 0, 10**6)
    raw = clip.get_notes_extended(pitch_from, pitch_span, time_from, span)
    notes = sorted(raw, key=lambda n: (n.start_time, n.pitch, n.note_id))
    end = _clip_end(clip)
    page = notes[offset : offset + limit]
    nxt = offset + limit if offset + limit < len(notes) else None
    return {
        "notes": [note_row(n) for n in page],
        "total": len(notes),
        "next_offset": nxt,
        "clip_end": end,
        "past_clip_end": sum(1 for n in notes if n.start_time >= end),
    }


# ---- edits --------------------------------------------------------------------------------------


def _ids(value, name):
    if not isinstance(value, list) or len(value) > NOTE_LIMIT:
        raise Invalid(f"{name!r} must be a list of at most {NOTE_LIMIT} note ids")
    for i in value:
        _int(i, f"{name}[]", 0, 2**31)
    return set(value)


def _region(value, name, keys):
    if not isinstance(value, dict) or set(value) - set(keys):
        raise Invalid(f"{name!r} must be an object with keys {list(keys)}")
    return value


def plan_edits(clip, p):
    """Pass 1: validate every requested edit against the clip's current notes. Nothing is
    written. Returns the ordered op list ``[(label, fn)]``."""
    spec = None
    current = {n.note_id: n for n in wide(clip)}
    ops = []
    removed = set()
    if p.get("remove_ids") is not None:
        removed = _ids(p.get("remove_ids"), "remove_ids")
        missing = sorted(removed - set(current))
        if missing:
            raise Invalid(f"remove_ids: unknown note ids {missing[:20]}")
        if not hasattr(clip, "remove_notes_by_id"):
            raise Invalid("this clip has no 'remove_notes_by_id'")
        ids = tuple(sorted(removed))
        ops.append(("remove_ids", lambda: _removed(clip.remove_notes_by_id(ids), len(ids))))
    if p.get("remove_range") is not None:
        r = _region(
            p.get("remove_range"),
            "remove_range",
            ("pitch_from", "pitch_span", "time_from", "time_span"),
        )  # noqa: E501
        pf = _int(r.get("pitch_from", 0), "remove_range.pitch_from", 0, 127)
        ps = _int(r.get("pitch_span", 128), "remove_range.pitch_span", 1, 128)
        tf = float(_number(r.get("time_from"), "remove_range.time_from", WIDE_FROM))
        ts = float(_number(r.get("time_span"), "remove_range.time_span", 0, WIDE_SPAN, True))
        removed |= {
            i
            for i, n in current.items()
            if pf <= n.pitch < pf + ps and tf <= n.start_time < tf + ts
        }
        ops.append(("remove_range", lambda: _range_removed(clip, pf, ps, tf, ts)))
    changes = _planned_changes(current, removed, p)
    if changes:
        ops.append(("modify", lambda: _apply(clip, changes)))
    if p.get("duplicate_region") is not None:
        d = _region(
            p.get("duplicate_region"), "duplicate_region", ("start", "length", "dest", "transpose")
        )  # noqa: E501
        start = float(_number(d.get("start"), "duplicate_region.start", WIDE_FROM))
        length = float(_number(d.get("length"), "duplicate_region.length", 0, 16384, True))
        dest = float(_number(d.get("dest"), "duplicate_region.dest", 0, MAX_TIME))
        shift = _int(d.get("transpose", 0), "duplicate_region.transpose", -127, 127)
        src = [
            n
            for i, n in current.items()
            if i not in removed and start <= n.start_time < start + length
        ]  # noqa: E501
        if not 1 <= len(src) <= NOTE_LIMIT:
            raise Invalid(
                f"duplicate_region: the region holds {len(src)} notes (1..{NOTE_LIMIT})"
            )
        for n in src:
            _int(n.pitch + shift, "duplicate_region pitch", 0, 127)
        spec = spec or _spec()
        ops.append(("duplicate_region", lambda: _dup(clip, spec, start, length, dest, shift)))
    if p.get("add"):
        rows = validated_notes(p.get("add"), "add")
        spec = spec or _spec()
        new = tuple(spec(**row) for row in rows)
        end = _clip_end(clip)
        past = [i for i, row in enumerate(rows) if row["start_time"] >= end]
        ops.append(("add", lambda: _added(clip.add_new_notes(new), len(new), past)))
    if not ops:
        raise Invalid(
            "nothing to edit: give add, modify, remove_ids, remove_range, "
            "transpose, quantize or duplicate_region"
        )
    return ops


def _spec():
    from .dom_common import _note_specification

    spec = _note_specification()
    if spec is None:
        raise Invalid("Live.Clip.MidiNoteSpecification is unavailable for add_new_notes")
    return spec


def _planned_changes(current, removed, p):
    """``{note_id: {field: value}}`` for modify + transpose + quantize, all range-checked."""
    changes = {}
    if p.get("modify") is not None:
        mods = p.get("modify")
        if not isinstance(mods, list) or len(mods) > NOTE_LIMIT:
            raise Invalid(f"'modify' must be a list of at most {NOTE_LIMIT} objects")
        for k, m in enumerate(mods):
            where = f"modify[{k}]"
            if not isinstance(m, dict):
                raise Invalid(f"{where}: must be an object")
            nid = m.get("note_id")
            if nid not in current or nid in removed:
                raise Invalid(f"{where}: unknown or removed note_id {nid!r}")
            fields = {
                f: checked_field(f, v, where)
                for f, v in m.items()
                if f != "note_id" and v is not None
            }  # noqa: E501
            if not fields:
                raise Invalid(f"{where}: no field to change")
            changes.setdefault(nid, {}).update(fields)
    live = [i for i in current if i not in removed]

    def chosen(spec, name):
        ids = spec.get("ids")
        if ids is None:
            return live
        picked = _ids(ids, f"{name}.ids")
        bad = sorted(picked - set(live))
        if bad:
            raise Invalid(f"{name}.ids: unknown or removed note ids {bad[:20]}")
        return sorted(picked)

    def value(nid, field):
        return changes.get(nid, {}).get(field, getattr(current[nid], field))

    if p.get("transpose") is not None:
        t = _region(p.get("transpose"), "transpose", ("semitones", "ids"))
        semis = _int(t.get("semitones"), "transpose.semitones", -127, 127)
        for nid in chosen(t, "transpose"):
            pitch = value(nid, "pitch") + semis
            if not 0 <= pitch <= 127:
                raise Invalid(f"transpose: note {nid} would leave 0..127 ({pitch})")
            changes.setdefault(nid, {})["pitch"] = pitch
    if p.get("quantize") is not None:
        q = _region(p.get("quantize"), "quantize", ("grid", "amount", "ids"))
        grid = float(_number(q.get("grid"), "quantize.grid", 0, 16, True))
        amount = float(_number(q.get("amount", 1.0), "quantize.amount", 0, 1))
        for nid in chosen(q, "quantize"):
            start = value(nid, "start_time")
            target = round(start / grid) * grid
            changes.setdefault(nid, {})["start_time"] = start + amount * (target - start)
    return changes


def _apply(clip, changes):
    raw = wide(clip)  # the raw object: mutate in place, pass it back (P-07)
    seen = 0
    for n in raw:
        fields = changes.get(n.note_id)
        if fields:
            for f, v in fields.items():
                setattr(n, f, v)
            seen += 1
    if seen != len(changes):
        raise RuntimeError(f"only {seen} of {len(changes)} notes were found at write time")
    clip.apply_note_modifications(raw)
    return {"modified": seen, "note_ids": sorted(changes)}


def _removed(_ret, count):
    return {"removed": count}


def _range_removed(clip, pf, ps, tf, ts):
    before = len(wide(clip))
    clip.remove_notes_extended(pf, ps, tf, ts)
    return {"removed": before - len(wide(clip))}


def _dup(clip, spec, start, length, dest, shift):
    src = [n for n in wide(clip) if start <= n.start_time < start + length]
    new = tuple(
        spec(
            pitch=n.pitch + shift,
            start_time=dest + (n.start_time - start),
            duration=n.duration,
            velocity=n.velocity,
            mute=n.mute,
            probability=n.probability,
            velocity_deviation=n.velocity_deviation,
            release_velocity=n.release_velocity,
        )
        for n in src
    )
    return {"duplicated": len(new), "note_ids": list(clip.add_new_notes(new) or ())}


def _added(ids, count, past):
    out = {"added": count, "note_ids": list(ids or ())}
    if past:
        out["past_clip_end"] = past  # indices of `add` kept by Live beyond the clip end
    return out


def edit_notes(ctx, p, t):
    """All edits on one clip in one undo step, in a fixed order: remove_ids, remove_range,
    modify/transpose/quantize (one apply), duplicate_region, add. Receipt per op."""
    resolved = t["targets"]
    if len(resolved) != 1:
        raise Invalid("'targets' must name exactly one clip")
    if resolved[0].path[-1][0] not in ("clip", "arr_clip"):
        raise Invalid("'targets' must name a clip")
    require(ctx, "notes.extended")
    clip = checked_midi(resolved[0].obj, ("get_notes_extended", "apply_note_modifications"))
    ops = plan_edits(clip, p)
    receipt = run_writes(ops, lambda op: op[1]())
    for item, (label, _fn) in zip(receipt["items"], ops, strict=True):
        item["op"] = label
    try:
        receipt["note_count"] = len(wide(clip))
    except Exception:  # noqa: BLE001 - the receipt stands without the count
        receipt["note_count"] = None
    return receipt


METHODS = {
    "get_notes": (get_notes, READ, None),
    "edit_notes": (edit_notes, WRITE, (("targets", "ref", ANY_KIND),)),
}
