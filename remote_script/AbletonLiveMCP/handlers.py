"""Bridge handlers. ``song`` is Live's ``Song`` (or a test double), ``app`` is Live's Application.

Rules: reads are bounded (browser walks have a node budget); every write reads the value back
and returns it, so callers can see what actually happened; nothing here retries.

Every call goes through ``make_dispatch``'s gate (see ``safety.py`` for the dispatch contract):
writes receive already-validated targets and never resolve an index themselves.
"""

import math
from itertools import islice

from .core import PROTOCOL_VERSION
from .operations import Operations
from .safety import CLASSIFICATION, CONTROL, READ, Refused, Safety, _same, same_items

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
_END = object()


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
        if isinstance(velocity, bool) or not isinstance(velocity, int) or not 1 <= velocity <= 127:
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


def _iter_children(item):
    """Lazy iterator over ``item.children``. The single native ``children`` access cannot be
    preempted, but nothing is copied and every caller stops after its own bounded count."""
    kids = getattr(item, "children", None)
    return iter(kids) if kids is not None else iter(())


def _find_child(node, name, unique, budget=WALK_BUDGET):
    """Scan ``node``'s children for ``name`` visiting at most ``budget`` nodes.
    Returns ``(matches, exhausted)``: first match only (or up to two when ``unique``) and whether
    the budget ended the scan before the children did."""
    matches, visited = [], 0
    for child in _iter_children(node):
        if visited >= budget:
            return matches, True
        visited += 1
        if child.name == name:
            matches.append(child)
            if not unique or len(matches) == 2:
                break
    return matches, False


def _walk_path(item, names):
    if not isinstance(names, list) or len(names) > PATH_LIMIT:
        raise ValueError(f"'path' must be a list of at most {PATH_LIMIT} names")
    for name in names:
        if not isinstance(name, str):
            raise ValueError("'path' must contain only strings")
        match, exhausted = _find_child(item, name, False)
        if not match:
            if exhausted:
                raise Refused("browser_budget", f"path walk exceeded {WALK_BUDGET} nodes")
            raise ValueError(f"no child named {name!r}")
        item = match[0]
    return item


def _handlers(song, app, safety, operations=None):  # noqa: C901 - flat table of small handlers
    """Handler table bound to one Song. Reads take ``(p)``; writes take ``(p, t)`` where ``t``
    holds the targets the gate already resolved and validated."""
    operations = operations or Operations(safety)

    def hello(_p):
        return {
            "protocol": PROTOCOL_VERSION,
            "live_version": _live_version(app),
            "generation": safety.generation,
            "capabilities": probe(song, app),
        }

    def session_info(_p):
        return {
            "generation": safety.generation,
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
                "ref": safety.issue(("track", t, {})),
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

    def _count(p, key, default, maximum):
        value = p.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            raise ValueError(f"'{key}' must be an integer 1..{maximum}")
        return value

    def browser_list(p):
        """One page (<= LIST_LIMIT items). ``cursor`` continues a truncated listing."""
        limit = _count(p, "limit", LIST_LIMIT, LIST_LIMIT)
        if p.get("cursor") is None:
            node, offset = _walk_path(_root(app, p), p.get("path") or []), 0
        else:
            node, offset = operations.cursors.take(p["cursor"], "list")
        page = list(islice(_iter_children(node), offset, offset + limit + 1))
        more = len(page) > limit
        return {
            "complete": not more,
            "truncated": more,
            "cursor": operations.cursors.put("list", (node, offset + limit)) if more else None,
            "items": [_item_info(c) for c in page[:limit]],
        }

    def browser_search(p):
        """Depth-first slice of at most WALK_BUDGET visited nodes / ``limit`` results. When it
        stops early it returns ``cursor``; ``complete`` is true only when the walk finished."""
        limit = _count(p, "limit", 25, SEARCH_LIMIT)
        if p.get("cursor") is None:
            query = str(p.get("query", "")).strip().lower()
            if not query:
                raise ValueError("'query' is required")
            stack = [([], _iter_children(_root(app, p)))]
        else:
            query, stack = operations.cursors.take(p["cursor"], "search")
        found, visited = [], 0
        while stack and len(found) < limit and visited < WALK_BUDGET:
            path, kids = stack[-1]
            child = next(kids, _END)
            if child is _END:
                stack.pop()
                continue
            visited += 1
            if query in child.name.lower():
                found.append({**_item_info(child), "path": path + [child.name]})
            if getattr(child, "is_folder", False):  # only folders are descended into
                stack.append((path + [child.name], _iter_children(child)))
        done = not stack
        return {
            "results": found,
            "visited": visited,
            "complete": done,
            "truncated": not done and len(found) >= limit,
            "budget_exhausted": not done and visited >= WALK_BUDGET,
            "cursor": None if done else operations.cursors.put("search", (query, stack)),
        }

    def operation(p):
        return operations.get(p.get("operation"))

    # ---- writes (each returns a readback) ------------------------------------------
    def _load_target(track, p):
        """Preconditions that must hold before any browser call. Raises Refused."""
        if p.get("root") not in LOAD_ROOTS:
            raise Refused("unsupported_root", f"only {list(LOAD_ROOTS)} items can be loaded")
        if not any(_same(x, track) for x in song.tracks):
            raise Refused("unsupported_target", "target must be a regular track of the Set")
        if track.has_midi_input or getattr(track, "is_foldable", False):
            raise Refused("unsupported_target", "target must be a regular audio track")
        operations.check_can_load(track)
        after = p.get("after")
        if after is None:
            if len(track.devices):
                raise Refused("target_occupied", "track already has devices; only empty tracks")
            return
        prior = operations.prior(after)
        if (
            prior is None
            or prior.state != "ready"
            or prior.generation != safety.generation
            or not _same(prior.track, track)
            or not same_items(prior.after, track.devices)
        ):
            raise Refused("prefix_mismatch", "track is not exactly the ready prefix of 'after'")

    def _select_last_device(track):
        """Make the track's last device Live's insertion point; refuse unless observed."""
        last = track.devices[-1]
        select = getattr(getattr(song, "view", None), "select_device", None)
        if not callable(select):
            raise Refused("append_unverified", "song.view.select_device is not available")
        try:
            select(last)
            selected = track.view.selected_device
        except Exception as exc:  # noqa: BLE001
            raise Refused("append_unverified", f"cannot select last device: {exc!r}") from exc
        if not _same(selected, last):
            raise Refused("append_unverified", "last device selection was not observed")

    def load_item(p, t):
        """Start a native load of one supported audio-effect device onto an empty (or owned
        prefix) audio track and return an operation record. Completion is observed on later
        display ticks (``operation`` reads it); this never retries and never waits."""
        track = t["track"].obj
        _load_target(track, p)
        item = _walk_path_unique(_root(app, p), p.get("path"))
        if not getattr(item, "is_loadable", False) or getattr(item, "is_device", False) is not True:
            raise Refused("unsupported_item", f"{item.name!r} is not a loadable device")
        song.view.selected_track = track
        append = p.get("after") is not None
        if append:
            _select_last_device(track)
        op = operations.begin(track, item.name, p["root"], append=append)
        try:
            app.browser.load_item(item)
        except Exception as exc:  # noqa: BLE001 - outcome is established by observation
            operations.native_error(op, exc)
        return operations.snapshot(op)

    def _walk_path_unique(root, names):
        if not isinstance(names, list) or not 1 <= len(names) <= PATH_LIMIT:
            raise ValueError(f"'path' must be a list of 1..{PATH_LIMIT} names")
        item = root
        for name in names:
            if not isinstance(name, str):
                raise ValueError("'path' must contain only strings")
            matches, exhausted = _find_child(item, name, True)
            if exhausted:
                raise Refused("browser_budget", f"path walk exceeded {WALK_BUDGET} nodes")
            if len(matches) != 1:
                code = "item_not_found" if not matches else "ambiguous_item"
                raise Refused(code, f"{len(matches)} children named {name!r}; expected exactly 1")
            item = matches[0]
        return item

    def device_parameters(p):
        track = _track(song, p)
        dev = _device(track, p)
        chain = (
            ("track", track, {}),
            ("device", dev, {"layout": tuple(d.class_name for d in track.devices)}),
        )
        count = len(dev.parameters)
        return [
            {
                "index": i,
                "ref": safety.issue(
                    *chain, ("param", q, {"index": i, "count": count, "name": q.name})
                ),
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

    def _param(dev, idx):
        if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(dev.parameters):
            raise ValueError("'parameter' must be a valid parameter index")
        return dev.parameters[idx]

    def _checked_write(q, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"value for {q.name!r} must be a number")
        if not q.min <= value <= q.max:
            raise ValueError(f"value {value} outside {q.min}..{q.max} for {q.name!r}")
        if not getattr(q, "is_enabled", True):
            raise ValueError(f"parameter {q.name!r} is not enabled (macro-controlled?)")
        return float(value)

    def _write(q, value):
        q.value = value
        return {"name": q.name, "value": q.value, "display": q.str_for_value(q.value)}

    def _sampled(q, values):
        if not isinstance(values, list) or not 1 <= len(values) <= SAMPLE_LIMIT:
            raise ValueError(f"'values' must be a list of 1..{SAMPLE_LIMIT} numbers")
        out = []
        for v in values:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not q.min <= v <= q.max:
                raise ValueError(f"every value must be a number within {q.min}..{q.max}")
            out.append(q.str_for_value(float(v)))
        return {"name": q.name, "displays": out}

    def _batch(p, key):
        items = p.get(key)
        if not isinstance(items, list) or not 1 <= len(items) <= BATCH_LIMIT:
            raise ValueError(f"{key!r} must be a list of 1..{BATCH_LIMIT} items")
        if not all(isinstance(i, dict) for i in items):
            raise ValueError(f"every item in {key!r} must be an object")
        return items

    def set_device_parameter(p, t):
        q = t["parameter"].obj
        return _write(q, _checked_write(q, p.get("value")))

    def set_device_parameters(p, t):
        """Write several parameters (by reference). Everything is validated before any write."""
        plan = []
        items = _batch(p, "writes")
        for i, w in enumerate(items):  # t["writes"] was built from the same list by the gate
            q = t["writes"][i].obj
            plan.append((q, _checked_write(q, w.get("value"))))
        return {"results": [_write(q, v) for q, v in plan]}

    def sample_parameter(p):
        """Display text for candidate values of one parameter. Read-only; writes nothing."""
        q = _param(_device(_track(song, p), p), p.get("parameter"))
        return _sampled(q, p.get("values"))

    def sample_parameters(p):
        """Like sample_parameter for many parameters of one device in a single round trip."""
        dev = _device(_track(song, p), p)
        requests = _batch(p, "requests")
        total = sum(len(r["values"]) for r in requests if isinstance(r.get("values"), list))
        if total > SAMPLE_LIMIT:  # one cap for the whole request, not per entry
            raise ValueError(f"at most {SAMPLE_LIMIT} display values in total per request")
        return {
            "results": [
                _sampled(_param(dev, r.get("parameter")), r.get("values")) for r in requests
            ]
        }

    def create_track(p, _t):
        kind = p.get("kind")
        index = int(p.get("index", -1))
        if kind == "midi":
            song.create_midi_track(index)
        elif kind == "audio":
            song.create_audio_track(index)
        else:
            raise ValueError("'kind' must be 'midi' or 'audio'")
        return {"track_count": len(song.tracks)}

    def set_track_name(p, t):
        track = t["track"].obj
        track.name = str(p["name"])
        return {"name": track.name}

    def set_track_color(p, t):
        track = t["track"].obj
        track.color_index = int(p["color_index"])
        return {"color_index": track.color_index}

    def set_tempo(p, _t):
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

    def play(_p, _t):
        song.start_playing()
        return {"is_playing": song.is_playing}

    def stop(_p, _t):
        song.stop_playing()
        return {"is_playing": song.is_playing}

    def scenes(_p):
        return [
            {"index": i, "ref": safety.issue(("scene", s, {})), "name": s.name}
            for i, s in enumerate(song.scenes)
        ]

    def clip_slot(p):
        """Read a slot by indices; returns references for the slot and its clip (if any)."""
        track, slot = _slot(song, p)
        scene_obj = song.scenes[p["scene"]]
        chain = (("track", track, {}), ("slot", slot, {"index": p["scene"], "scene": scene_obj}))
        out = {"slot": safety.issue(*chain), "has_clip": bool(slot.has_clip)}
        if slot.has_clip:
            out["clip"] = safety.issue(*chain, ("clip", slot.clip, {}))
        return out

    def create_scene(p, _t):
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

    def set_scene_name(p, t):
        scene = t["scene"].obj
        name = p.get("name")
        if not isinstance(name, str):
            raise ValueError("'name' must be a string")
        scene.name = name
        return {"name": scene.name}

    def fire_scene(_p, t):
        scene = t["scene"].obj
        scene.fire()
        return {"name": scene.name, "is_triggered": scene.is_triggered}

    def _clip_info(clip):
        return {
            "name": clip.name,
            "length": clip.length,
            "is_playing": clip.is_playing,
            "looping": clip.looping,
        }

    def get_clip(p):
        return _clip_info(_clip(song, p))

    def create_clip(p, t):
        slot, track = t["slot"].obj, t["slot"].nodes["track"]
        length = _number(p.get("length_beats"), "length_beats", 0, 1024, exclusive=True)
        if not track.has_midi_input:
            raise ValueError("create_clip requires a MIDI track")
        if slot.has_clip:
            raise ValueError("clip slot is occupied")
        slot.create_clip(length)
        return _clip_info(slot.clip)

    def get_notes(p):
        return _notes(_clip(song, p))

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

    def add_notes(p, t):
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

    def fire_clip(_p, t):
        clip = t["clip"].obj
        clip.fire()
        return _clip_info(clip)

    def stop_clip(_p, t):
        clip = t["clip"].obj
        clip.stop()
        return _clip_info(clip)

    return {
        "hello": hello,
        "session_info": session_info,
        "tracks": tracks,
        "browser_roots": browser_roots,
        "browser_list": browser_list,
        "browser_search": browser_search,
        "load_item": load_item,
        "operation": operation,
        "device_parameters": device_parameters,
        "set_device_parameter": set_device_parameter,
        "set_device_parameters": set_device_parameters,
        "sample_parameter": sample_parameter,
        "sample_parameters": sample_parameters,
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
        "scenes": scenes,
        "clip_slot": clip_slot,
    }


class _Params(dict):
    """Request params; a missing required key is a readable refusal, not a handler crash."""

    def __missing__(self, key):
        raise ValueError(f"missing required parameter {key!r}")


def make_dispatch(song_supplier, app, safety=None):
    """Build the bridge dispatcher. ``song_supplier`` is a callable returning the *current* Song
    (a bare Song is accepted for tests and wrapped). Returns ``dispatch(method, params)``; the
    Safety object is exposed as ``dispatch.safety`` for the entry point's session hooks."""
    if not callable(song_supplier):
        fixed = song_supplier
        song_supplier = lambda: fixed  # noqa: E731
    safety = safety or Safety(song_supplier)
    operations = Operations(safety)
    bound = {"song": None, "table": None}

    def table():
        song = safety.song()  # bumps generation / clears refs and lease on Set change
        if bound["song"] is not song:
            bound["song"], bound["table"] = song, _handlers(song, app, safety, operations)
        return bound["table"]

    def dispatch(method, params):
        kind = CLASSIFICATION.get(method)
        if kind is None:
            raise ValueError(f"unknown or unclassified method: {method}")
        if not isinstance(params, dict):
            raise ValueError("params must be an object")
        params = _Params(params)
        try:
            if kind == CONTROL:
                if safety.read_only():
                    raise Refused("read_only", "bridge is read-only; leases are unavailable")
                safety.song()
                if method == "lease_acquire":
                    return safety.lease_acquire(params.get("ttl", 30.0))
                return safety.lease_release(params.get("lease"))
            if kind == READ:
                return table()[method](params)
            targets = safety.authorize(method, params)  # policy, lease, Set, targets
            return table()[method](params, targets)
        except Refused as refusal:
            return refusal.result()

    dispatch.safety = safety
    dispatch.operations = operations
    dispatch.methods = sorted(CLASSIFICATION)
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
