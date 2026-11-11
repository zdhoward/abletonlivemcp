"""Tracks domain: list tracks (issuing references), create, rename, recolor."""

from .dom_common import READ, WRITE


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


METHODS = {
    "tracks": (tracks, READ, None),
    "create_track": (create_track, WRITE, ()),
    "set_track_name": (set_track_name, WRITE, (("track", "track"),)),
    "set_track_color": (set_track_color, WRITE, (("track", "track"),)),
}
