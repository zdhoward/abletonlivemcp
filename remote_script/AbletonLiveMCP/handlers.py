"""Bridge handlers. ``song`` is Live's ``Song`` (or a test double), ``app`` is Live's Application.

Rules: reads are bounded (browser walks have a node budget); every write reads the value back
and returns it, so callers can see what actually happened; nothing here retries.
"""

import math
from itertools import islice

from .core import PROTOCOL_VERSION

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
WALK_BUDGET = 4000  # max browser nodes visited per call (main-thread safety)
LIST_LIMIT = 200
NOTE_LIMIT = 2000
SAMPLE_LIMIT = 129


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
        if (
            isinstance(velocity, bool)
            or not isinstance(velocity, int)
            or not 1 <= velocity <= 127
        ):
            raise ValueError("'velocity' must be an integer 1..127")
        mute = note.get("mute", False)
        if not isinstance(mute, bool):
            raise ValueError("'mute' must be a bool")
        result.append((pitch, start, duration, velocity, mute))
    return result


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


def _item_info(item):
    return {
        "name": item.name,
        "uri": getattr(item, "uri", None),
        "is_folder": bool(getattr(item, "is_folder", False)),
        "is_loadable": bool(getattr(item, "is_loadable", False)),
    }


def _root(app, params):
    name = params.get("root")
    if name not in BROWSER_ROOTS or not hasattr(app.browser, name):
        present = [r for r in BROWSER_ROOTS if hasattr(app.browser, r)]
        raise ValueError(f"'root' must be one of {present}")
    return getattr(app.browser, name)


def _children(item):
    return list(getattr(item, "children", []) or [])


def make_dispatch(song, app):  # noqa: C901 - flat table of small handlers
    def hello(_p):
        return {
            "protocol": PROTOCOL_VERSION,
            "live_version": _live_version(app),
            "capabilities": probe(song, app),
        }

    def session_info(_p):
        return {
            "tempo": song.tempo,
            "is_playing": song.is_playing,
            "signature": [song.signature_numerator, song.signature_denominator],
            "track_count": len(song.tracks),
            "return_count": len(song.return_tracks),
            "scene_count": len(song.scenes),
        }

    def tracks(_p):
        return [
            {
                "index": i,
                "name": t.name,
                "color_index": getattr(t, "color_index", None),
                "has_midi_input": t.has_midi_input,
                "devices": [{"name": d.name, "class_name": d.class_name} for d in t.devices],
            }
            for i, t in enumerate(song.tracks)
        ]

    # ---- browser (read) --------------------------------------------------------------
    def browser_roots(_p):
        return [r for r in BROWSER_ROOTS if hasattr(app.browser, r)]

    def browser_list(p):
        item = _root(app, p)
        for name in p.get("path") or []:
            match = [c for c in _children(item) if c.name == name]
            if not match:
                raise ValueError(f"no child named {name!r}")
            item = match[0]
        kids = _children(item)
        return {
            "truncated": len(kids) > LIST_LIMIT,
            "items": [_item_info(c) for c in kids[:LIST_LIMIT]],
        }

    def browser_search(p):
        query = str(p.get("query", "")).strip().lower()
        if not query:
            raise ValueError("'query' is required")
        limit = min(int(p.get("limit", 25)), 100)
        found, visited = [], 0
        stack = [([], _root(app, p))]
        while stack and len(found) < limit and visited < WALK_BUDGET:
            path, node = stack.pop()
            for child in _children(node):
                visited += 1
                if query in child.name.lower():
                    found.append({**_item_info(child), "path": path + [child.name]})
                if getattr(child, "is_folder", False) or _children(child):
                    stack.append((path + [child.name], child))
        return {
            "results": found[:limit],
            "visited": visited,
            "budget_exhausted": visited >= WALK_BUDGET,
        }

    # ---- writes (each returns a readback) ------------------------------------------
    def load_item(p):
        """Load a browser item (by root+path) onto a track. Live loads onto the selected track."""
        track = _track(song, p)
        item = _root(app, p)
        for name in p.get("path") or []:
            match = [c for c in _children(item) if c.name == name]
            if len(match) != 1:
                raise ValueError(f"{len(match)} children named {name!r}; expected exactly 1")
            item = match[0]
        if not getattr(item, "is_loadable", False):
            raise ValueError(f"{item.name!r} is not loadable")
        before = len(track.devices)
        song.view.selected_track = track
        app.browser.load_item(item)
        return {"loaded": item.name, "devices_before": before, "devices_after": len(track.devices)}

    def device_parameters(p):
        dev = _device(_track(song, p), p)
        return [
            {
                "index": i,
                "name": q.name,
                "value": q.value,
                "min": q.min,
                "max": q.max,
                "is_quantized": q.is_quantized,
                "is_enabled": getattr(q, "is_enabled", True),
                "display": q.str_for_value(q.value),
            }
            for i, q in enumerate(dev.parameters)
        ]

    def set_device_parameter(p):
        dev = _device(_track(song, p), p)
        idx = p.get("parameter")
        if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(dev.parameters):
            raise ValueError("'parameter' must be a valid parameter index")
        q = dev.parameters[idx]
        value = float(p["value"])
        if not q.min <= value <= q.max:
            raise ValueError(f"value {value} outside {q.min}..{q.max} for {q.name!r}")
        if not getattr(q, "is_enabled", True):
            raise ValueError(f"parameter {q.name!r} is not enabled (macro-controlled?)")
        q.value = value
        return {"name": q.name, "value": q.value, "display": q.str_for_value(q.value)}

    def sample_parameter(p):
        """Display text for candidate values of one parameter. Read-only; writes nothing."""
        dev = _device(_track(song, p), p)
        idx = p.get("parameter")
        if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(dev.parameters):
            raise ValueError("'parameter' must be a valid parameter index")
        q = dev.parameters[idx]
        values = p.get("values")
        if not isinstance(values, list) or not 1 <= len(values) <= SAMPLE_LIMIT:
            raise ValueError(f"'values' must be a list of 1..{SAMPLE_LIMIT} numbers")
        out = []
        for v in values:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not q.min <= v <= q.max:
                raise ValueError(f"every value must be a number within {q.min}..{q.max}")
            out.append(q.str_for_value(float(v)))
        return {"name": q.name, "displays": out}

    def create_track(p):
        kind = p.get("kind")
        index = int(p.get("index", -1))
        if kind == "midi":
            song.create_midi_track(index)
        elif kind == "audio":
            song.create_audio_track(index)
        else:
            raise ValueError("'kind' must be 'midi' or 'audio'")
        return {"track_count": len(song.tracks)}

    def set_track_name(p):
        t = _track(song, p)
        t.name = str(p["name"])
        return {"name": t.name}

    def set_track_color(p):
        t = _track(song, p)
        t.color_index = int(p["color_index"])
        return {"color_index": t.color_index}

    def set_tempo(p):
        bpm = float(p["bpm"])
        if not 20.0 <= bpm <= 999.0:
            raise ValueError("bpm must be 20..999")
        song.tempo = bpm
        return {"tempo": song.tempo}

    # ---- transport, scenes and clips ----------------------------------------------
    def get_transport(_p):
        return {
            "is_playing": song.is_playing,
            "tempo": song.tempo,
            "signature": [song.signature_numerator, song.signature_denominator],
            "current_song_time": song.current_song_time,
        }

    def play(_p):
        song.start_playing()
        return {"is_playing": song.is_playing}

    def stop(_p):
        song.stop_playing()
        return {"is_playing": song.is_playing}

    def create_scene(p):
        index = p.get("index", -1)
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or not -1 <= index <= len(song.scenes)
        ):
            raise ValueError(f"'index' must be an integer -1..{len(song.scenes)} (-1 = end)")
        song.create_scene(index)
        actual = len(song.scenes) - 1 if index == -1 else index
        return {
            "scene_count": len(song.scenes),
            "index": actual,
            "name": song.scenes[actual].name,
        }

    def set_scene_name(p):
        scene = _scene(song, p)
        name = p.get("name")
        if not isinstance(name, str):
            raise ValueError("'name' must be a string")
        scene.name = name
        return {"name": scene.name}

    def fire_scene(p):
        scene = _scene(song, p)
        scene.fire()
        return {"name": scene.name, "is_triggered": scene.is_triggered}

    def get_clip(p):
        clip = _clip(song, p)
        return {
            "name": clip.name,
            "length": clip.length,
            "is_playing": clip.is_playing,
            "looping": clip.looping,
        }

    def create_clip(p):
        track, slot = _slot(song, p)
        length = _number(p.get("length_beats"), "length_beats", 0, 1024, exclusive=True)
        if not track.has_midi_input:
            raise ValueError("create_clip requires a MIDI track")
        if slot.has_clip:
            raise ValueError("clip slot is occupied")
        slot.create_clip(length)
        return get_clip(p)

    def get_notes(p):
        clip = _clip(song, p)
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

    def add_notes(p):
        clip = _clip(song, p)
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
        return get_notes(p)

    def fire_clip(p):
        clip = _clip(song, p)
        clip.fire()
        return get_clip(p)

    def stop_clip(p):
        clip = _clip(song, p)
        clip.stop()
        return get_clip(p)

    methods = {
        "hello": hello,
        "session_info": session_info,
        "tracks": tracks,
        "browser_roots": browser_roots,
        "browser_list": browser_list,
        "browser_search": browser_search,
        "load_item": load_item,
        "device_parameters": device_parameters,
        "set_device_parameter": set_device_parameter,
        "sample_parameter": sample_parameter,
        "create_track": create_track,
        "set_track_name": set_track_name,
        "set_track_color": set_track_color,
        "set_tempo": set_tempo,
        "play": play,
        "stop": stop,
        "get_transport": get_transport,
        "create_scene": create_scene,
        "set_scene_name": set_scene_name,
        "fire_scene": fire_scene,
        "create_clip": create_clip,
        "get_clip": get_clip,
        "add_notes": add_notes,
        "get_notes": get_notes,
        "fire_clip": fire_clip,
        "stop_clip": stop_clip,
    }

    def dispatch(method, params):
        if method not in methods:
            raise ValueError(f"unknown method: {method}")
        return methods[method](params)

    return dispatch


def probe(song, app=None):
    """Report which version-gated APIs exist at runtime. Never assume; ask the objects."""
    track_cls = type(song.tracks[0]) if len(song.tracks) else None
    caps = {
        "track.insert_device": bool(track_cls and hasattr(track_cls, "insert_device")),  # 12.3+
        "track.color_index": bool(track_cls and hasattr(track_cls, "color_index")),
    }
    # Sample a bounded number of slots; false means unavailable on the sampled clips.
    clips = []
    remaining = LIST_LIMIT
    for track in islice(song.tracks, LIST_LIMIT):
        slots = list(islice(getattr(track, "clip_slots", ()), remaining))
        clips.extend(slot.clip for slot in slots if slot.has_clip)
        remaining -= len(slots)
        if remaining == 0:
            break
    for member in ("add_new_notes", "set_notes", "get_notes_extended", "get_notes"):
        caps[f"clip.{member}"] = any(hasattr(clip, member) for clip in clips)
    caps["clip.note_api_sample_count"] = len(clips)
    caps["Live.Clip.MidiNoteSpecification"] = _note_specification() is not None
    if app is not None:
        browser = getattr(app, "browser", None)
        caps["browser.load_item"] = bool(browser and hasattr(browser, "load_item"))
        caps["browser.roots"] = [r for r in BROWSER_ROOTS if browser and hasattr(browser, r)]
    return caps
