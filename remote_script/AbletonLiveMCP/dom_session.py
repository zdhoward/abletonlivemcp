"""Session domain (batch 2): handshake and diagnostics, session state get/set (song extras from
``dom_song``), transport and undo/redo.

``hello``, ``session_info``, ``get_transport``, ``set_tempo``, ``play`` and ``stop`` are kept as
internal bridge methods (``server._generation`` and older tests call them); the public tools use
``get_session``/``set_session``/``transport``/``undo``. ``undo`` is exempt from the automatic undo
step (``handlers.OWN_UNDO_STEPS``).
"""

from . import dom_song
from .core import PROTOCOL_VERSION, SCRIPT_IDENTITY, Invalid, log_failure, public_error
from .dom_common import (
    READ,
    WRITE,
    Refused,
    _index,
    _live_version,
    _number,
    capability_report,
    require,
    run_writes,
)

CAPABILITIES = {
    "transport.play": ("supported", "start_playing/stop_playing in use since v1"),
    "transport.jump_to": ("supported", "current_song_time write used by ref_lab cues"),
    "transport.continue": ("unverified", "Song.continue_playing; final proof decides"),
    "transport.stop_all_clips": ("unverified", "Song.stop_all_clips; final proof decides"),
    "transport.jump_by": ("unverified", "Song.jump_by; final proof decides"),
    "transport.cue_jump": ("unverified", "jump_to_next_cue/prev_cue; final proof decides"),
    "transport.tap_tempo": ("unverified", "P-01: tap_tempo present; behaviour unproven"),
    "transport.nudge": ("unverified", "P-01: nudge_up/down present; behaviour unproven"),
    "transport.back_to_arranger": ("unverified", "P-01: present on Song; behaviour unproven"),
    "session.scale": ("supported", "P-22: root_note/scale_name/scale_mode round trip"),
    "session.quantization": ("supported", "P-22: midi_recording_quantization round trip"),
}

SECTIONS = (
    "transport",
    "loop",
    "scale",
    "groove",
    "quantization",
    "link",
    "extras",
    "selection",
    "undo",
    "cues",
)
CUE_LIMIT = 64
DENOMINATORS = (1, 2, 4, 8, 16)
TOLERANCE = 1e-3
UNDO_LIMIT = 10


def _get(obj, attribute, default=None):
    return dom_song._get(obj, attribute, default)


def _app_call(app, name):
    member = getattr(app, name, None)
    if not callable(member):
        return None
    try:
        return member()
    except Exception:  # noqa: BLE001 - diagnostics never fail the handshake
        return None


def hello(ctx, _p):
    app = ctx.app
    return {
        "protocol": PROTOCOL_VERSION,
        "script": {"version": SCRIPT_IDENTITY[0], "build": SCRIPT_IDENTITY[1]},
        "live_version": _live_version(app),
        "variant": _app_call(app, "get_variant"),
        "build_id": _app_call(app, "get_build_id"),
        "generation": ctx.safety.generation,
        # the bridge re-reads its config on every call: an edit applies without a restart
        "read_only": ctx.safety.read_only(),
        "dev_probes": ctx.safety.dev_probes_enabled(),
        "diagnostics": {
            f: _get(app, f)
            for f in (
                "open_dialog_count",
                "current_dialog_message",
                "average_process_usage",
                "peak_process_usage",
            )
        },
        "capabilities": ctx.probe(),
        "capability_report": capability_report(ctx),
    }


# ---- legacy internal methods (server._generation, older tests) ----------------------------


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
    bpm = float(_number(p["bpm"], "bpm", 20.0, 999.0))
    ctx.song.tempo = bpm
    return {"tempo": ctx.song.tempo}


def play(ctx, _p, _t):
    ctx.song.start_playing()
    return {"is_playing": ctx.song.is_playing}


def stop(ctx, _p, _t):
    ctx.song.stop_playing()
    return {"is_playing": ctx.song.is_playing}


# ---- get_session ---------------------------------------------------------------------------


def _selection(song):
    view = _get(song, "view")
    track, scene = _get(view, "selected_track"), _get(view, "selected_scene")
    out = {"track": None, "track_name": None, "scene": None, "detail_clip": None}
    if track is not None:
        out["track_name"] = _get(track, "name")
        for prefix, seq in (("", song.tracks), ("return:", song.return_tracks)):
            for i, t in enumerate(seq):
                if t == track:
                    out["track"] = f"{prefix}{i}" if prefix else i
        if out["track"] is None and track == song.master_track:
            out["track"] = "master"
    if scene is not None:
        for i, s in enumerate(song.scenes):
            if s == scene:
                out["scene"] = i
    clip = _get(view, "detail_clip")
    if clip is not None:
        out["detail_clip"] = _get(clip, "name")
    return out


def session_state(ctx, include=SECTIONS):
    song = ctx.song
    out = {
        "generation": ctx.safety.generation,
        "tempo": song.tempo,
        "signature": [song.signature_numerator, song.signature_denominator],
        "is_playing": song.is_playing,
        "track_count": len(song.tracks),
        "return_count": len(song.return_tracks),
        "scene_count": len(song.scenes),
    }
    if "transport" in include:
        out["current_song_time"] = song.current_song_time
        out["metronome"] = _get(song, "metronome")
        out["record_mode"] = _get(song, "record_mode")
        out["session_record"] = _get(song, "session_record")
    if "loop" in include:
        out["loop"] = {
            "on": _get(song, "loop"),
            "start": _get(song, "loop_start"),
            "length": _get(song, "loop_length"),
        }
        out["punch"] = {"in": _get(song, "punch_in"), "out": _get(song, "punch_out")}
    if "scale" in include:
        out["scale"] = {f: _get(song, f) for f in ("root_note", "scale_name", "scale_mode")}
    if "groove" in include:
        out["groove_amount"] = _get(song, "groove_amount")
        out["swing_amount"] = _get(song, "swing_amount")
        out["grooves"] = dom_song.read_grooves(song)
    if "quantization" in include:
        out["clip_trigger_quantization"] = _get(song, "clip_trigger_quantization")
        out["midi_recording_quantization"] = _get(song, "midi_recording_quantization")
    if "link" in include:
        out["link"] = dom_song.read_link(song)
    if "extras" in include:
        out.update(dom_song.read_extras(song))
    if "selection" in include:
        out["selection"] = _selection(song)
    if "undo" in include:
        out["can_undo"] = _get(song, "can_undo")
        out["can_redo"] = _get(song, "can_redo")
    if "cues" in include:
        cues = sorted(_get(song, "cue_points", ()) or (), key=lambda c: c.time)
        out["cues"] = [{"index": i, "name": c.name, "time": c.time} for i, c in enumerate(cues)]
        out["cues"] = out["cues"][:CUE_LIMIT]
    return out


def get_session(ctx, p):
    include = p.get("include") or list(SECTIONS)
    if not isinstance(include, list) or any(s not in SECTIONS for s in include):
        raise Invalid(f"'include' must be a list of {list(SECTIONS)}")
    return session_state(ctx, include)


# ---- set_session ---------------------------------------------------------------------------


def _bool(p, key):
    if not isinstance(p[key], bool):
        raise Invalid(f"{key!r} must be a bool")
    return p[key]


def _int(value, name, lo, hi):
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise Invalid(f"{name!r} must be an integer {lo}..{hi}")
    return value


def _validate_session(ctx, p):
    """Pass 1: every field checked before any write -> ``(label, obj, attribute, value)``."""
    song, out = ctx.song, []
    dom_song.refuse_read_only_extras(ctx, p)
    sig = p.get("signature")
    if sig is not None:
        if not isinstance(sig, list) or len(sig) != 2:
            raise Invalid("'signature' must be [numerator, denominator]")
        num = _int(sig[0], "signature numerator", 1, 99)
        if sig[1] not in DENOMINATORS or isinstance(sig[1], bool):
            raise Invalid(f"signature denominator must be one of {list(DENOMINATORS)}")
        out += [("signature", song, "signature_numerator", num)]
        out += [("signature", song, "signature_denominator", sig[1])]
    if p.get("tempo") is not None:
        out.append(("tempo", song, "tempo", float(_number(p["tempo"], "tempo", 20.0, 999.0))))
    if p.get("metronome") is not None:
        out.append(("metronome", song, "metronome", _bool(p, "metronome")))
    loop = p.get("loop")
    if loop is not None:
        if not isinstance(loop, dict) or not loop:
            raise Invalid("'loop' must be an object {on?, start?, length?}")
        if loop.get("start") is not None:
            out.append(
                ("loop.start", song, "loop_start", float(_number(loop["start"], "start", 0)))
            )
        if loop.get("length") is not None:
            length = float(_number(loop["length"], "length", 0, exclusive=True))
            out.append(("loop.length", song, "loop_length", length))
        if loop.get("on") is not None:
            out.append(("loop.on", song, "loop", _bool(loop, "on")))
    punch = p.get("punch")
    if punch is not None:
        if not isinstance(punch, dict) or not punch:
            raise Invalid("'punch' must be an object {in?, out?}")
        for key in ("in", "out"):
            if punch.get(key) is not None:
                out.append((f"punch.{key}", song, f"punch_{key}", _bool(punch, key)))
    scale = p.get("scale")
    if scale is not None:
        if not isinstance(scale, dict) or not scale:
            raise Invalid("'scale' must be an object {root_note?, scale_name?, scale_mode?}")
        require(ctx, "session.scale", ((song, "root_note"),))
        if scale.get("root_note") is not None:
            root = _int(scale["root_note"], "root_note", 0, 11)
            out.append(("scale.root_note", song, "root_note", root))
        if scale.get("scale_name") is not None:
            name = scale["scale_name"]
            if not isinstance(name, str) or not 0 < len(name) <= 64:
                raise Invalid("'scale_name' must be a string of 1..64 characters")
            out.append(("scale.scale_name", song, "scale_name", name))
        if scale.get("scale_mode") is not None:
            out.append(("scale.scale_mode", song, "scale_mode", _bool(scale, "scale_mode")))
    for key, hi in (("groove_amount", 1.3125), ("swing_amount", 1.0)):
        if p.get(key) is not None:
            out.append((key, song, key, float(_number(p[key], key, 0.0, hi))))
    for key, hi in (("clip_trigger_quantization", 13), ("midi_recording_quantization", 8)):
        if p.get(key) is not None:
            require(ctx, "session.quantization", ((song, key),))
            out.append((key, song, key, _int(p[key], key, 0, hi)))
    out += dom_song.validate_link(ctx, p)
    if p.get("grooves") is not None:
        out += dom_song.validate_grooves(ctx, p["grooves"])
    if not out:
        raise Invalid("give at least one field to set")
    return out


def _write_field(entry):
    label, obj, attribute, value = entry
    setattr(obj, attribute, value)
    actual = getattr(obj, attribute)
    row = {"field": label, "requested": value, "actual": actual}
    if isinstance(value, float) and isinstance(actual, (int, float)):
        row["matches"] = abs(actual - value) <= max(TOLERANCE, abs(value) * 1e-4)
    else:
        row["matches"] = actual == value
    return row


def set_session(ctx, p, _t):
    receipt = run_writes(_validate_session(ctx, p), _write_field)
    receipt["mismatched"] = [r["field"] for r in receipt["applied"] if not r["matches"]]
    receipt["session"] = session_state(ctx, ("transport", "loop", "scale", "groove", "link"))
    return receipt


# ---- transport -----------------------------------------------------------------------------


def _beats(p):
    return float(_number(p.get("beats"), "beats", -1e6, 1e6))


def _set(obj, attribute, value):
    setattr(obj, attribute, value)


def _pulse(obj, attribute):
    """A momentary button (nudge): press and release in the same call."""
    setattr(obj, attribute, True)
    setattr(obj, attribute, False)


TRANSPORT = {
    "play": ("transport.play", ("start_playing",), lambda s, p: s.start_playing()),
    "stop": ("transport.play", ("stop_playing",), lambda s, p: s.stop_playing()),
    "continue": ("transport.continue", ("continue_playing",), lambda s, p: s.continue_playing()),
    "stop_all_clips": (
        "transport.stop_all_clips",
        ("stop_all_clips",),
        lambda s, p: s.stop_all_clips(),
    ),
    "jump_to": (
        "transport.jump_to",
        ("current_song_time",),
        lambda s, p: _set(s, "current_song_time", max(0.0, _beats(p))),
    ),
    "jump_by": ("transport.jump_by", ("jump_by",), lambda s, p: s.jump_by(_beats(p))),
    "next_cue": ("transport.cue_jump", ("jump_to_next_cue",), lambda s, p: s.jump_to_next_cue()),
    "prev_cue": ("transport.cue_jump", ("jump_to_prev_cue",), lambda s, p: s.jump_to_prev_cue()),
    "tap_tempo": ("transport.tap_tempo", ("tap_tempo",), lambda s, p: s.tap_tempo()),
    "nudge_up": ("transport.nudge", ("nudge_up",), lambda s, p: _pulse(s, "nudge_up")),
    "nudge_down": ("transport.nudge", ("nudge_down",), lambda s, p: _pulse(s, "nudge_down")),
    "back_to_arranger": (
        "transport.back_to_arranger",
        ("back_to_arranger",),
        lambda s, p: _set(s, "back_to_arranger", False),
    ),
}


def transport(ctx, p, _t):
    action = p.get("action")
    entry = TRANSPORT.get(action) if isinstance(action, str) else None
    if entry is None:
        raise Invalid(f"'action' must be one of {sorted(TRANSPORT)}")
    capability, members, run = entry
    song = ctx.song
    state = require(ctx, capability, tuple((song, m) for m in members))
    if action in ("jump_to", "jump_by"):
        _beats(p)  # validate before the write
    run(song, p)
    return {
        "action": action,
        "unverified": [capability] if state == "unverified" else [],
        "is_playing": song.is_playing,
        "current_song_time": song.current_song_time,
        "tempo": song.tempo,
    }


# ---- undo / redo (own undo handling: never wrapped in an undo step) ------------------------


def undo(ctx, p, _t):
    action = p.get("action", "undo")
    if action not in ("undo", "redo"):
        raise Invalid("'action' must be 'undo' or 'redo'")
    steps = _index(p.get("steps", 1), "steps", UNDO_LIMIT + 1)
    if steps < 1:
        raise Invalid(f"'steps' must be 1..{UNDO_LIMIT}")
    song = ctx.song
    can = "can_undo" if action == "undo" else "can_redo"
    if not getattr(song, can):
        raise Refused("nothing_to_" + action, f"Live has nothing to {action}")
    done, error = 0, None
    while done < steps and getattr(song, can):
        try:
            getattr(song, action)()
        except Exception as exc:  # noqa: BLE001 - after the first step: a receipt, not a raise
            if done == 0:
                raise
            error = public_error(exc, f"{action}_failed")
            log_failure(action, exc)
            break
        done += 1
    return {
        "action": action,
        "requested": steps,
        "done": done,
        "status": "complete" if done == steps else "partial",
        "error": error,
        "can_undo": song.can_undo,
        "can_redo": song.can_redo,
    }


METHODS = {
    "hello": (hello, READ, None),
    "session_info": (session_info, READ, None),
    "get_transport": (get_transport, READ, None),
    "get_session": (get_session, READ, None),
    "set_tempo": (set_tempo, WRITE, ()),
    "play": (play, WRITE, ()),
    "stop": (stop, WRITE, ()),
    "set_session": (set_session, WRITE, ()),
    "transport": (transport, WRITE, ()),
    "undo": (undo, WRITE, ()),
}
