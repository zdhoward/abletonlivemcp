"""Session domain: handshake, Set summary, transport and tempo."""

from .core import PROTOCOL_VERSION
from .dom_common import READ, WRITE, _live_version


def hello(ctx, _p):
    return {
        "protocol": PROTOCOL_VERSION,
        "live_version": _live_version(ctx.app),
        "generation": ctx.safety.generation,
        "capabilities": ctx.probe(),
    }


def session_info(ctx, _p):
    song = ctx.song
    return {
        "generation": ctx.safety.generation,
        "tempo": song.tempo,
        "is_playing": song.is_playing,
        "signature": [song.signature_numerator, song.signature_denominator],
        "track_count": len(song.tracks),
        "return_count": len(song.return_tracks),
        "scene_count": len(song.scenes),
    }


def get_transport(ctx, _p):
    song = ctx.song
    return {
        "is_playing": song.is_playing,
        "tempo": song.tempo,
        "signature": [song.signature_numerator, song.signature_denominator],
        "current_song_time": song.current_song_time,
    }


def set_tempo(ctx, p, _t):
    bpm = float(p["bpm"])
    if not 20.0 <= bpm <= 999.0:
        raise ValueError("bpm must be 20..999")
    ctx.song.tempo = bpm
    return {"tempo": ctx.song.tempo}


def play(ctx, _p, _t):
    ctx.song.start_playing()
    return {"is_playing": ctx.song.is_playing}


def stop(ctx, _p, _t):
    ctx.song.stop_playing()
    return {"is_playing": ctx.song.is_playing}


METHODS = {
    "hello": (hello, READ, None),
    "session_info": (session_info, READ, None),
    "get_transport": (get_transport, READ, None),
    "set_tempo": (set_tempo, WRITE, ()),
    "play": (play, WRITE, ()),
    "stop": (stop, WRITE, ()),
}
