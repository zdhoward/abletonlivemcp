"""Bridge handlers. ``song`` is Live's ``Song`` (or a test double), ``app`` is Live's Application.

Rules: reads are bounded (browser walks have a node budget); every write reads the value back
and returns it, so callers can see what actually happened; nothing here retries.
"""

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
        "create_track": create_track,
        "set_track_name": set_track_name,
        "set_track_color": set_track_color,
        "set_tempo": set_tempo,
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
    if app is not None:
        browser = getattr(app, "browser", None)
        caps["browser.load_item"] = bool(browser and hasattr(browser, "load_item"))
        caps["browser.roots"] = [r for r in BROWSER_ROOTS if browser and hasattr(browser, r)]
    return caps
