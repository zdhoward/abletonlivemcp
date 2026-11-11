"""P-07: extended MIDI note API: ids, per-note fields, by-id edits, quantize, duplicate_region.

Behavioural (write) probe on one 4-beat MIDI clip in slot 0 of a scratch MIDI track (deleted
with the track). Steps, each with its exact error text on failure:

1. ``add_new_notes`` with ``MidiNoteSpecification`` (extra fields tried one at a time), then
   ``get_notes_extended`` to list the fields a note exposes;
2. ``apply_note_modifications``: velocity and the extra per-note fields; ids must stay the same;
3. ``get_notes_by_id``, ``duplicate_notes_by_id``, ``remove_notes_by_id``;
4. ``quantize`` and ``duplicate_region``, ``remove_notes_extended``;
5. a note starting past the clip end: kept or dropped (documented, not a pass condition).

Verdict: ``gated`` when ``MidiNoteSpecification`` or any of the note calls is absent; ``go`` when
every call worked and ids were stable; otherwise ``no-go``.
"""

from .dom_common import WRITE, _note_specification

PROBE_ID = "P-07"
KIND = WRITE

CALLS = (
    "add_new_notes",
    "get_notes_extended",
    "apply_note_modifications",
    "get_notes_by_id",
    "remove_notes_by_id",
    "duplicate_notes_by_id",
    "remove_notes_extended",
    "quantize",
    "duplicate_region",
)
EXTRA_FIELDS = ("probability", "velocity_deviation", "release_velocity")
NOTE_FIELDS = ("note_id", "pitch", "start_time", "duration", "velocity", "mute") + EXTRA_FIELDS
CLIP_LENGTH = 4.0


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(missing_api, errors, ids_stable):
    """Pure verdict rule (kept separate so it is unit-testable)."""
    if missing_api:
        return "gated"
    return "go" if not errors and ids_stable else "no-go"


def _notes(clip, span=64.0):
    # raw return value: apply_note_modifications refuses a list()/tuple() copy of it (P-07 run 3)
    return clip.get_notes_extended(0, 128, 0.0, span)


def _brief(note):
    return {f: getattr(note, f, "<absent>") for f in NOTE_FIELDS}


def run(ctx, scratch):
    spec_cls = _note_specification()
    track = scratch.midi_track()
    slot = track.clip_slots[0]
    if spec_cls is None:
        return {"verdict": "gated", "missing_api": ["MidiNoteSpecification"]}
    slot.create_clip(CLIP_LENGTH)
    clip = slot.clip
    missing = [n for n in CALLS if not hasattr(clip, n)]
    if missing:
        return {"verdict": "gated", "missing_api": missing}

    errors, out = {}, {}

    def attempt(label, fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - the exact error text is the evidence
            errors[label] = _err(exc)
            return None

    # 1. specifications: plain, then each extra field alone.
    base = dict(pitch=60, start_time=0.0, duration=0.5, velocity=100.0, mute=False)
    accepted = {}
    for field, value in (
        ("plain", None),
        ("probability", 0.5),
        ("velocity_deviation", 10.0),
        ("release_velocity", 64.0),
    ):
        kwargs = dict(base)
        if value is not None:
            kwargs[field] = value
        try:
            spec_cls(**kwargs)
            accepted[field] = True
        except Exception as exc:  # noqa: BLE001
            accepted[field] = _err(exc)
    out["specification_kwargs"] = accepted

    specs = [
        spec_cls(**dict(base, pitch=60 + i, start_time=float(i) * 0.25 + 0.1)) for i in range(4)
    ]
    ids = attempt("add_new_notes", lambda: list(clip.add_new_notes(specs)))
    notes = attempt("get_notes_extended", lambda: _notes(clip)) or []
    out["add_new_notes_returned_ids"] = len(ids) if ids is not None else None
    out["note_count_after_add"] = len(notes)
    out["note_fields"] = _brief(notes[0]) if notes else None
    out["note_fields_present"] = [f for f in NOTE_FIELDS if notes and hasattr(notes[0], f)]
    ids_before = sorted(n.note_id for n in notes)

    # 2. modify in place: ids must be unchanged, field writes must read back.
    writes = {}
    if notes:
        for note in notes:
            note.velocity = 50.0
        for field, value in (
            ("probability", 0.5),
            ("velocity_deviation", 10.0),
            ("release_velocity", 64.0),
        ):
            try:
                setattr(notes[0], field, value)
                writes[field] = "set"
            except Exception as exc:  # noqa: BLE001
                writes[field] = _err(exc)
        attempt("apply_note_modifications", lambda: clip.apply_note_modifications(notes))
        if "apply_note_modifications" in errors:
            # list form refused (error kept above); a tuple is how Live hands the notes out
            errors["apply_note_modifications(list)"] = errors.pop("apply_note_modifications", None)
            errors.pop("apply_note_modifications", None)
            # Variants: fresh unmodified notes, one note, a tuple, then add-modify via by-id calls.
            variants = {}
            fresh = _notes(clip)
            for label, arg in (
                ("fresh_list", fresh),
                ("fresh_tuple", tuple(fresh)),
                ("fresh_first_only", fresh[:1]),
                ("raw_tuple", clip.get_notes_extended(0, 128, 0.0, 64.0)),
            ):
                try:
                    clip.apply_note_modifications(arg)
                    variants[label] = "ok"
                except Exception as exc:  # noqa: BLE001
                    variants[label] = _err(exc)[:90]
            out["apply_variants"] = variants
            out["apply_form"] = next((k for k, v in variants.items() if v == "ok"), "none-worked")
    after = attempt("get_notes_extended", lambda: _notes(clip)) or []
    ids_after = sorted(n.note_id for n in after)
    ids_stable = bool(ids_before) and ids_before == ids_after
    for field in EXTRA_FIELDS:
        if writes.get(field) == "set" and after:
            writes[field] = {
                "read_back": getattr(
                    next(n for n in after if n.note_id == notes[0].note_id), field, None
                )
            }
    out["modify"] = {
        "ids_stable": ids_stable,
        "velocities_after": sorted({n.velocity for n in after}),
        "field_writes": writes,
    }

    # 3. by-id calls.
    if ids_after:
        got = attempt("get_notes_by_id", lambda: list(clip.get_notes_by_id(ids_after[:2])))
        out["get_notes_by_id_count"] = len(got) if got is not None else None
        dup = attempt(
            "duplicate_notes_by_id",
            lambda: list(clip.duplicate_notes_by_id(ids_after[:1], 2.0, 12)),
        )
        now = _notes(clip)
        out["duplicate_notes_by_id"] = {
            "returned_ids": len(dup) if dup is not None else None,
            "count_after": len(now),
            "new_pitches": sorted(n.pitch for n in now if n.note_id in (dup or [])),
            "new_starts": sorted(n.start_time for n in now if n.note_id in (dup or [])),
        }
        victim = ids_after[-1]
        attempt("remove_notes_by_id", lambda: clip.remove_notes_by_id([victim]))
        out["remove_notes_by_id"] = {"victim_gone": all(n.note_id != victim for n in _notes(clip))}

    # 4. quantize, duplicate_region, remove_notes_extended.
    before = sorted(round(n.start_time, 4) for n in _notes(clip))
    attempt(
        "quantize", lambda: clip.quantize(5, 1.0)
    )  # grid 5 = 1/16 (Live's index), full strength
    quantized = sorted(round(n.start_time, 4) for n in _notes(clip))
    out["quantize"] = {
        "starts_before": before,
        "starts_after": quantized,
        "changed": before != quantized,
    }
    count = len(_notes(clip))
    attempt("duplicate_region", lambda: clip.duplicate_region(0.0, 1.0, 2.0))
    out["duplicate_region"] = {"count_before": count, "count_after": len(_notes(clip))}
    count = len(_notes(clip))
    attempt("remove_notes_extended", lambda: clip.remove_notes_extended(0, 128, 0.0, 1.0))
    out["remove_notes_extended"] = {"count_before": count, "count_after": len(_notes(clip))}

    # 5. a note beyond the clip end.
    past = attempt(
        "add_new_notes_past_end",
        lambda: list(
            clip.add_new_notes([spec_cls(**dict(base, pitch=90, start_time=CLIP_LENGTH + 1.0))])
        ),
    )
    wide = attempt("get_notes_extended", lambda: _notes(clip, 64.0)) or []
    inside = (
        attempt(
            "get_notes_extended", lambda: list(clip.get_notes_extended(0, 128, 0.0, CLIP_LENGTH))
        )
        or []
    )
    out["past_clip_end"] = {
        "returned_ids": len(past) if past is not None else None,
        "readable_wide_span": any(n.pitch == 90 for n in wide),
        "readable_inside_clip": any(n.pitch == 90 for n in inside),
        "clip_length": clip.length,
        "behaviour": "kept" if any(n.pitch == 90 for n in wide) else "dropped",
    }

    out["errors"] = errors
    core = {
        k: v for k, v in errors.items() if k != "add_new_notes_past_end"
    }  # documented, not graded
    out["verdict"] = verdict_for([], core, ids_stable)
    return out
