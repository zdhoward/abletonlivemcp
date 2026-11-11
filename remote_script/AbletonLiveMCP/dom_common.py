"""Shared pieces for the ``dom_*`` handler modules (stdlib only; main thread only).

Holds the method kinds and the refusal type the gate uses (``safety`` re-exports them, so the
domain modules never import ``safety`` and the gate can import every domain module), the limits,
the index selectors that reads use to find objects, and value validation.

Domain module contract: each ``dom_<d>.py`` exports ``METHODS = {name: (handler, kind, targets)}``.
A read handler is ``handler(ctx, params)`` with ``targets`` ``None``; a write handler is
``handler(ctx, params, targets)`` with ``targets`` a tuple of target specs (see
``safety.TARGETS``). ``ctx`` carries ``song``, ``app``, ``safety``, ``operations`` and ``probe``
(a zero-argument capabilities report). ``safety`` merges every module's ``METHODS`` at import;
a duplicate or unclassified name fails the import.
"""

import math

READ, WRITE, CONTROL = "read", "write", "control"

BROWSER_ROOTS = (
    "instruments",
    "sounds",
    "drums",
    "audio_effects",
    "midi_effects",
    "samples",
    "user_library",
    "plugins",
    "packs",
    "current_project",
)
WALK_BUDGET = 4000  # max browser nodes visited per call/slice (main-thread safety)
LIST_LIMIT = 200  # max items per listing page
SEARCH_LIMIT = 100  # max results per search slice
PATH_LIMIT = 8  # max browser path depth
NOTE_LIMIT = 2000
SAMPLE_LIMIT = 129  # max display conversions per bridge request (all requests together)
BATCH_LIMIT = 64
LOAD_ROOTS = ("audio_effects", "plugins")
# Documentation only: a browser load inserts after the selected device of the selected track, so an
# append first selects the track's last device (refused if that cannot be done and observed) and
# the operation tick verifies per load that the single new device landed last.
APPEND_PLACEMENT_VERIFIED = True

METHODS = {}  # shared helpers only; no bridge methods live here


class Refused(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message

    def result(self):
        return {"refused": True, "applied": False, "code": self.code, "message": self.message}


def _same(a, b):
    if a is b:
        return True
    try:
        return bool(a == b)
    except Exception:  # noqa: BLE001
        return False


def same_items(a, b):
    """Equal length and pairwise identical-or-equal (no ``zip(strict=)``: Python 3.8 safe)."""
    return len(a) == len(b) and all(_same(a[i], b[i]) for i in range(len(a)))


# ---- selectors (reads only: indices find objects, they never authorize a write) ----------


def _track(song, params, key="track"):
    idx = params.get(key)
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(song.tracks):
        raise ValueError(f"'{key}' must be an integer track index 0..{len(song.tracks) - 1}")
    return song.tracks[idx]


def _device(track, params):
    idx = params.get("device")
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(track.devices):
        raise ValueError(f"'device' must be an integer device index 0..{len(track.devices) - 1}")
    return track.devices[idx]


def _scene(song, params):
    idx = params.get("scene")
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(song.scenes):
        raise ValueError(f"'scene' must be an integer scene index 0..{len(song.scenes) - 1}")
    return song.scenes[idx]


def _slot(song, params):
    track = _track(song, params)
    _scene(song, params)
    idx = params["scene"]
    if idx >= len(track.clip_slots):
        raise ValueError("'scene' has no clip slot on this track")
    return track, track.clip_slots[idx]


def _clip(song, params):
    _t, slot = _slot(song, params)
    if not slot.has_clip:
        raise ValueError("clip slot is empty")
    return slot.clip


# ---- validation ---------------------------------------------------------------------------


def _number(value, name, minimum, maximum=None, exclusive=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or (isinstance(value, float) and not math.isfinite(value))
        or (value <= minimum if exclusive else value < minimum)
        or (maximum is not None and value > maximum)
    ):
        bound = f"> {minimum}" if exclusive else f">= {minimum}"
        if maximum is not None:
            bound += f" and <= {maximum}"
        raise ValueError(f"'{name}' must be a finite number {bound}")
    return value


def _validated_notes(notes):
    if not isinstance(notes, list) or len(notes) > NOTE_LIMIT:
        raise ValueError(f"'notes' must be a list of at most {NOTE_LIMIT} notes")
    result = []
    for note in notes:
        if not isinstance(note, dict):
            raise ValueError("each note must be an object")
        pitch = note.get("pitch")
        if isinstance(pitch, bool) or not isinstance(pitch, int) or not 0 <= pitch <= 127:
            raise ValueError("'pitch' must be an integer 0..127")
        start = _number(note.get("start_time"), "start_time", 0)
        duration = _number(note.get("duration"), "duration", 0, exclusive=True)
        velocity = note.get("velocity")
        if isinstance(velocity, bool) or not isinstance(velocity, int) or not 1 <= velocity <= 127:
            raise ValueError("'velocity' must be an integer 1..127")
        mute = note.get("mute", False)
        if not isinstance(mute, bool):
            raise ValueError("'mute' must be a bool")
        result.append((pitch, start, duration, velocity, mute))
    return result


# ---- runtime facts ------------------------------------------------------------------------


def _note_specification():
    try:
        import Live
    except ImportError:
        return None
    clip_module = getattr(Live, "Clip", None)
    if clip_module is not None and hasattr(clip_module, "MidiNoteSpecification"):
        return clip_module.MidiNoteSpecification
    return None


def _live_version(app):
    try:
        return [app.get_major_version(), app.get_minor_version(), app.get_bugfix_version()]
    except Exception:  # noqa: BLE001
        return None
