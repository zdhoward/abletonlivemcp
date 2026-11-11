"""Clips domain: slot lookup (issuing references), clip state, create, fire, stop."""

from .dom_common import READ, WRITE, _clip, _number, _slot


def _clip_info(clip):
    return {
        "name": clip.name,
        "length": clip.length,
        "is_playing": clip.is_playing,
        "looping": clip.looping,
    }


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
    return _clip_info(_clip(ctx.song, p))


def create_clip(_ctx, p, t):
    slot, track = t["slot"].obj, t["slot"].nodes["track"]
    length = _number(p.get("length_beats"), "length_beats", 0, 1024, exclusive=True)
    if not track.has_midi_input:
        raise ValueError("create_clip requires a MIDI track")
    if slot.has_clip:
        raise ValueError("clip slot is occupied")
    slot.create_clip(length)
    return _clip_info(slot.clip)


def fire_clip(_ctx, _p, t):
    clip = t["clip"].obj
    clip.fire()
    return _clip_info(clip)


def stop_clip(_ctx, _p, t):
    clip = t["clip"].obj
    clip.stop()
    return _clip_info(clip)


METHODS = {
    "clip_slot": (clip_slot, READ, None),
    "get_clip": (get_clip, READ, None),
    "create_clip": (create_clip, WRITE, (("slot", "slot"),)),
    "fire_clip": (fire_clip, WRITE, (("clip", "clip"),)),
    "stop_clip": (stop_clip, WRITE, (("clip", "clip"),)),
}
