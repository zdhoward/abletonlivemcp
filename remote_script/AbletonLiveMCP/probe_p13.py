"""P-13: the Live.Conversions functions (call shape, sync/async result, failure modes).

Behavioural probe (write). Every call runs against objects made through ``scratch`` (one MIDI
track with an empty MIDI clip). No audio clip is available to a probe (no file path is known),
so the success paths of the audio-clip functions are *not* exercised: only their call shape and
their exact refusal text on a MIDI clip are recorded (see ``unverified``). The one function that
needs no clip, ``move_devices_on_track_to_new_drum_rack_pad``, is run on the empty scratch track;
it creates a track, so every track it adds is found by diffing the track list and deleted here.

Verdict: ``gated`` when ``Live.Conversions`` or any of its functions is absent; ``go`` when every
function is present and every call produced an observed outcome (a result or an error text);
otherwise ``no-go``.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-13"
KIND = WRITE

FUNCTIONS = (
    "is_convertible_to_midi",
    "audio_to_midi_clip",
    "create_drum_rack_from_audio_clip",
    "create_midi_track_with_simpler",
    "create_midi_track_from_drum_pad",
    "sliced_simpler_to_drum_rack",
    "move_devices_on_track_to_new_drum_rack_pad",
)


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(module_present, present, observed):
    """Pure verdict rule. ``present``/``observed`` map function name -> bool."""
    if not module_present or not all(present.get(n) for n in FUNCTIONS):
        return "gated"
    return "go" if all(observed.get(n) for n in FUNCTIONS) else "no-go"


def _conversions(ctx):
    live = getattr(ctx, "live", None)
    if live is None:
        try:
            import Live as live  # noqa: N813
        except ImportError:
            return None
    return getattr(live, "Conversions", None)


def _call(fn, *args):
    try:
        result = fn(*args)
        return {"ok": True, "result": type(result).__name__ if result is not None else None}
    except Exception as exc:  # noqa: BLE001 - the error text is the evidence
        return {"ok": False, "error": _err(exc)}


def run(ctx, scratch):
    conv = _conversions(ctx)
    present = {n: conv is not None and hasattr(conv, n) for n in FUNCTIONS}
    if conv is None or not all(present.values()):
        return {
            "verdict": verdict_for(conv is not None, present, {}),
            "present": present,
            "live_conversions": conv is not None,
        }
    song = ctx.song
    track = scratch.midi_track()
    slot = track.clip_slots[0]
    slot.create_clip(4.0)
    clip = slot.clip
    before = list(song.tracks)
    calls = {}
    try:
        calls["is_convertible_to_midi(midi_clip)"] = _call(conv.is_convertible_to_midi, song, clip)
        calls["audio_to_midi_clip(midi_clip, 0)"] = _call(conv.audio_to_midi_clip, song, clip, 0)
        calls["audio_to_midi_clip(midi_clip, 99)"] = _call(conv.audio_to_midi_clip, song, clip, 99)
        calls["create_drum_rack_from_audio_clip(midi_clip)"] = _call(
            conv.create_drum_rack_from_audio_clip, song, clip
        )
        calls["create_midi_track_with_simpler(midi_clip)"] = _call(
            conv.create_midi_track_with_simpler, song, clip
        )
        calls["create_midi_track_from_drum_pad(None)"] = _call(
            conv.create_midi_track_from_drum_pad, song, None
        )
        calls["sliced_simpler_to_drum_rack(track)"] = _call(
            conv.sliced_simpler_to_drum_rack, song, track
        )
        index = next(i for i, t in enumerate(song.tracks) if _same(t, track))
        n_before = len(list(song.tracks))
        move = _call(conv.move_devices_on_track_to_new_drum_rack_pad, song, index)
        move["tracks_added_immediately"] = len(list(song.tracks)) - n_before
        calls["move_devices_on_track_to_new_drum_rack_pad(empty_track)"] = move
    finally:
        added = [t for t in song.tracks if not any(_same(t, b) for b in before)]
        removed = 0
        for t in reversed(added):  # tracks this probe's conversion calls created
            for i, cur in enumerate(song.tracks):
                if _same(cur, t):
                    song.delete_track(i)
                    removed += 1
                    break
    observed = {n: any(k.startswith(n + "(") for k in calls) for n in FUNCTIONS}
    members = getattr(conv, "AudioToMidiType", None)
    return {
        "verdict": verdict_for(True, present, observed),
        "present": present,
        "calls": calls,
        "audio_to_midi_types": (
            sorted(a for a in dir(members) if not a.startswith("_"))
            if members is not None
            else None
        ),
        "tracks_created_by_conversions": len(added),
        "tracks_deleted": removed,
        "unverified": [
            "success paths of audio_to_midi_clip, create_drum_rack_from_audio_clip, "
            "create_midi_track_with_simpler, is_convertible_to_midi(audio) need an audio clip",
            "create_midi_track_from_drum_pad success needs a populated drum pad",
            "sliced_simpler_to_drum_rack success needs a sliced Simpler",
        ],
    }
