"""Notes domain: bounded MIDI note readback and note adds."""

from itertools import islice

from .dom_common import NOTE_LIMIT, READ, WRITE, _clip, _note_specification, _validated_notes


def _notes(clip):
    if not clip.is_midi_clip:
        raise ValueError("get_notes requires a MIDI clip")
    if hasattr(clip, "get_notes_extended"):
        raw = clip.get_notes_extended(0, 128, 0.0, clip.length)
        notes = [
            {
                "pitch": n.pitch,
                "start_time": n.start_time,
                "duration": n.duration,
                "velocity": n.velocity,
                "mute": n.mute,
            }
            for n in islice(raw, NOTE_LIMIT + 1)
        ]
    elif hasattr(clip, "get_notes"):
        raw = clip.get_notes(0.0, 0, clip.length, 128)
        notes = [
            {
                "pitch": pitch,
                "start_time": start,
                "duration": duration,
                "velocity": velocity,
                "mute": mute,
            }
            for pitch, start, duration, velocity, mute in islice(raw, NOTE_LIMIT + 1)
        ]
    else:
        raise ValueError("clip has neither get_notes_extended nor get_notes")
    return {"notes": notes[:NOTE_LIMIT], "truncated": len(notes) > NOTE_LIMIT}


def get_notes(ctx, p):
    return _notes(_clip(ctx.song, p))


def add_notes(_ctx, p, t):
    clip = t["clip"].obj
    if not clip.is_midi_clip:
        raise ValueError("add_notes requires a MIDI clip")
    notes = _validated_notes(p.get("notes"))
    # Require a read API before changing anything: all writes must return a readback.
    if not (hasattr(clip, "get_notes_extended") or hasattr(clip, "get_notes")):
        raise ValueError("clip has neither get_notes_extended nor get_notes")
    if hasattr(clip, "add_new_notes"):
        specification = _note_specification()
        if specification is None:
            raise ValueError("Live.Clip.MidiNoteSpecification is unavailable for add_new_notes")
        clip.add_new_notes(
            tuple(
                specification(
                    pitch=pitch,
                    start_time=start,
                    duration=duration,
                    velocity=velocity,
                    mute=mute,
                )
                for pitch, start, duration, velocity, mute in notes
            )
        )
    elif hasattr(clip, "set_notes"):
        clip.set_notes(tuple(notes))
    else:
        raise ValueError("clip has neither add_new_notes nor set_notes")
    return _notes(clip)


METHODS = {
    "get_notes": (get_notes, READ, None),
    "add_notes": (add_notes, WRITE, (("clip", "clip"),)),
}
