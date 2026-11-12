"""Scenes domain (batch 2): read scenes, batch create/set, launch (fire/stop clips, slots, scenes
and whole tracks) with a read for the settled state, and the ``delete_scenes`` /
``duplicate_scenes`` routes behind ``live_delete``/``live_duplicate``.

``scenes``, ``create_scene``, ``set_scene_name`` and ``fire_scene`` stay as internal bridge
methods (older tests and ``scripts/live_refs_test.py`` use them).

Evidence: P-05 (``delete_scene`` and ``duplicate_scene`` worked; the copy lands at index + 1).
"""

from .core import Invalid
from .dom_common import (
    BATCH_LIMIT,
    LIST_LIMIT,
    READ,
    WRITE,
    _number,
    for_deletion,
    position_of,
    reference_nodes,
    require,
    run_writes,
)

# safety.ANY_KIND; importing it from .safety is circular (safety imports every dom_* first).
ANY_KIND = "any"

CAPABILITIES = {
    "scene.tempo": ("unverified", "Scene.tempo/tempo_enabled; final proof decides"),
    "scene.signature": ("unverified", "Scene.time_signature_*; final proof decides"),
    "scene.delete": ("supported", "P-05: delete_scene removed the scene"),
    "scene.duplicate": ("supported", "P-05: duplicate_scene copied to index + 1"),
}

SLOT_TRACKS = 64
DENOMINATORS = (1, 2, 4, 8, 16)


def _get(obj, attribute, default=None):
    try:
        return getattr(obj, attribute)
    except Exception:  # noqa: BLE001 - a read never fails the whole reply
        return default


# ---- legacy internal methods ----------------------------------------------------------------


def scenes(ctx, _p):
    return [
        {"index": i, "ref": ctx.safety.issue(("scene", s, {})), "name": s.name}
        for i, s in enumerate(ctx.song.scenes)
    ]


def create_scene(ctx, p, _t):
    song = ctx.song
    index = p.get("index", -1)
    if isinstance(index, bool) or not isinstance(index, int) or not -1 <= index <= len(song.scenes):
        raise Invalid(f"'index' must be an integer -1..{len(song.scenes)} (-1 = end)")
    song.create_scene(index)
    actual = len(song.scenes) - 1 if index == -1 else index
    return {
        "scene_count": len(song.scenes),
        "index": actual,
        "name": song.scenes[actual].name,
    }


def set_scene_name(_ctx, p, t):
    scene = t["scene"].obj
    name = p.get("name")
    if not isinstance(name, str):
        raise Invalid("'name' must be a string")
    scene.name = name
    return {"name": scene.name}


def fire_scene(_ctx, _p, t):
    scene = t["scene"].obj
    scene.fire()
    return {"name": scene.name, "is_triggered": scene.is_triggered}


# ---- get_scenes -----------------------------------------------------------------------------


def scene_row(song, i, scene, include_slots=False):
    row = {
        "scene": i,
        "name": scene.name,
        "color_index": _get(scene, "color_index"),
        "tempo": _get(scene, "tempo") if _get(scene, "tempo_enabled") else None,
        "signature": [
            _get(scene, "time_signature_numerator"),
            _get(scene, "time_signature_denominator"),
        ]
        if _get(scene, "time_signature_enabled")
        else None,
        "is_triggered": _get(scene, "is_triggered"),
    }
    if include_slots:
        row["slots"] = [
            {
                "track": n,
                "has_clip": t.clip_slots[i].has_clip,
                "is_playing": _get(t.clip_slots[i], "is_playing"),
                "is_triggered": _get(t.clip_slots[i], "is_triggered"),
            }
            for n, t in enumerate(list(song.tracks)[:SLOT_TRACKS])
        ]
    return row


def get_scenes(ctx, p):
    song = ctx.song
    include_slots = bool(p.get("include_slots", False))
    all_scenes = list(song.scenes)
    picked = p.get("scenes")
    if picked is None:
        picked = list(range(min(len(all_scenes), LIST_LIMIT)))
    elif not isinstance(picked, list) or not 1 <= len(picked) <= LIST_LIMIT:
        raise Invalid(f"'scenes' must be a list of 1..{LIST_LIMIT} scene indices")
    rows = []
    for i in picked:
        if isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < len(all_scenes):
            raise Invalid(f"scene index {i!r} must be 0..{len(all_scenes) - 1}")
        rows.append(scene_row(song, i, all_scenes[i], include_slots))
    return {"generation": ctx.safety.generation, "scene_count": len(all_scenes), "scenes": rows}


# ---- create_scenes / set_scenes -------------------------------------------------------------


def _items(p, key):
    items = p.get(key)
    if not isinstance(items, list) or not 1 <= len(items) <= BATCH_LIMIT:
        raise Invalid(f"{key!r} must be a list of 1..{BATCH_LIMIT} objects")
    if not all(isinstance(i, dict) for i in items):
        raise Invalid(f"every item in {key!r} must be an object")
    return items


def _scene_fields(ctx, scene, item, label):
    """Pass 1 for one scene's fields -> ``[(field, apply)]`` (``scene`` may be None: created
    later; the appliers then take the scene as an argument)."""
    fields = []
    name = item.get("name")
    if name is not None:
        if not isinstance(name, str) or len(name) > 256:
            raise Invalid(f"{label}: 'name' must be a string of at most 256 characters")
        fields.append(("name", lambda s: _assign(s, "name", name)))
    color = item.get("color_index")
    if color is not None:
        if isinstance(color, bool) or not isinstance(color, int) or not 0 <= color <= 69:
            raise Invalid(f"{label}: 'color_index' must be an integer 0..69")
        fields.append(("color_index", lambda s: _assign(s, "color_index", color)))
    tempo = item.get("tempo")
    if tempo is not None:
        require(ctx, "scene.tempo")
        if tempo == "off":
            fields.append(("tempo", lambda s: _assign(s, "tempo_enabled", False)))
        else:
            bpm = float(_number(tempo, "tempo", 20.0, 999.0))
            fields.append(("tempo", lambda s: _tempo(s, bpm)))
    sig = item.get("signature")
    if sig is not None:
        require(ctx, "scene.signature")
        if sig == "off":
            fields.append(("signature", lambda s: _assign(s, "time_signature_enabled", False)))
        else:
            if (
                not isinstance(sig, list)
                or len(sig) != 2
                or any(isinstance(v, bool) or not isinstance(v, int) for v in sig)
                or not 1 <= sig[0] <= 99
                or sig[1] not in DENOMINATORS
            ):
                raise Invalid(f"{label}: 'signature' must be [1..99, 1|2|4|8|16] or 'off'")
            fields.append(("signature", lambda s: _signature(s, sig)))
    return fields


def _assign(scene, attribute, value):
    setattr(scene, attribute, value)
    return getattr(scene, attribute)


def _tempo(scene, bpm):
    scene.tempo = bpm
    scene.tempo_enabled = True
    return scene.tempo


def _signature(scene, sig):
    scene.time_signature_numerator, scene.time_signature_denominator = sig
    scene.time_signature_enabled = True
    return [scene.time_signature_numerator, scene.time_signature_denominator]


def create_scenes(ctx, p, _t):
    song = ctx.song
    prepared = []
    for n, item in enumerate(_items(p, "scenes")):
        index = item.get("index", -1)
        if isinstance(index, bool) or not isinstance(index, int) or index < -1:
            raise Invalid(f"scenes[{n}]: 'index' must be -1 (end) or a scene index")
        prepared.append((index, _scene_fields(ctx, None, item, f"scenes[{n}]")))

    def write(entry):
        index, fields = entry
        count = len(song.scenes)
        at = count if index == -1 or index > count else index
        song.create_scene(-1 if index == -1 else at)
        at = len(song.scenes) - 1 if index == -1 else at
        scene = song.scenes[at]
        for _field, apply in fields:
            apply(scene)
        return scene_row(song, at, scene)

    return run_writes(prepared, write)


def set_scenes(ctx, p, t):
    prepared = []
    for n, (item, resolved) in enumerate(zip(p["targets"], t["targets"], strict=True)):
        fields = _scene_fields(ctx, resolved.obj, item, f"targets[{n}]")
        if not fields:
            raise Invalid(f"targets[{n}]: give at least one field to set")
        prepared += [(n, resolved.obj, field, apply) for field, apply in fields]

    def write(entry):
        target, scene, field, apply = entry
        return {"target": target, "field": field, "actual": apply(scene)}

    return run_writes(prepared, write)


# ---- launch ---------------------------------------------------------------------------------

LAUNCH_KINDS = ("clip", "slot", "scene", "track", "return_track")


def _launch_entry(action, resolved, label):
    kind, obj = resolved.path[-1][0], resolved.obj
    if kind not in LAUNCH_KINDS:
        raise Invalid(f"{label}: launch takes a clip, slot, scene or track")
    if kind == "scene":
        if action == "stop":
            raise Invalid(f"{label}: a scene is stopped by stopping its clips or tracks")
        return kind, obj.fire
    if kind in ("track", "return_track"):
        if action == "fire":
            raise Invalid(f"{label}: a track can only 'stop' (stop all its clips)")
        return kind, obj.stop_all_clips
    return kind, obj.fire if action == "fire" else obj.stop


def launch(ctx, p, t):
    action = p.get("action")
    if action not in ("fire", "stop"):
        raise Invalid("'action' must be 'fire' or 'stop'")
    prepared = [_launch_entry(action, r, f"targets[{n}]") for n, r in enumerate(t["targets"])]

    def write(entry):
        kind, run = entry
        run()
        return {"kind": kind, "action": action}

    return run_writes(prepared, write)


def launch_state(ctx, p):
    """The settled play state of launch targets by index selector (read after launch)."""
    out = []
    items = _items(p, "targets")
    for item in items:
        nodes = reference_nodes(ctx.song, item)
        kind, obj = nodes[-1][0], nodes[-1][1]
        row = {"kind": kind, "name": _get(obj, "name")}
        if kind == "scene":
            # Live's Scene has no is_playing; derive it from the scene's own clip slots. An
            # unnamed scene reads "" in the API, so report its number as shown in Live.
            at = item.get("scene")
            tracks = ctx.song.tracks
            slots = [t.clip_slots[at] for t in tracks if at is not None and at < len(t.clip_slots)]
            row["scene"] = at
            row["name"] = row["name"] or None
            row["is_playing"] = any(_get(s, "is_playing") is True for s in slots)
            row["is_triggered"] = bool(_get(obj, "is_triggered")) or any(
                _get(s, "is_triggered") is True for s in slots
            )
        elif kind in ("clip", "slot"):
            row["is_playing"] = _get(obj, "is_playing")
            row["is_triggered"] = _get(obj, "is_triggered")
        if kind in ("track", "return_track"):
            row["playing_slot"] = _get(obj, "playing_slot_index")
        out.append(row)
    return {"targets": out}


# ---- structural routes ------------------------------------------------------------------------


def delete_scenes(ctx, p, t):
    song = ctx.song
    require(ctx, "scene.delete", ((song, "delete_scene"),))
    resolved = t["targets"]
    if len(resolved) >= len(song.scenes):
        raise Invalid("a Set must keep at least one scene")

    def write(r):
        name = r.obj.name
        at = position_of(song.scenes, r.obj)
        song.delete_scene(at)
        return {"kind": "scene", "index": at, "name": name}

    return run_writes(for_deletion(resolved), write)


def duplicate_scenes(ctx, p, t):
    song = ctx.song
    require(ctx, "scene.duplicate", ((song, "duplicate_scene"),))
    ordered = sorted(t["targets"], key=lambda r: -r.path[-1][2].get("index", 0))

    def write(r):
        at = position_of(song.scenes, r.obj)
        song.duplicate_scene(at)
        return {"kind": "scene", "source": at, "scene": at + 1, "name": song.scenes[at + 1].name}

    return run_writes(ordered, write)


SCENE_TARGETS = (("targets", "ref", "scene"),)

METHODS = {
    "scenes": (scenes, READ, None),
    "get_scenes": (get_scenes, READ, None),
    "launch_state": (launch_state, READ, None),
    "create_scene": (create_scene, WRITE, ()),
    "create_scenes": (create_scenes, WRITE, ()),
    "set_scene_name": (set_scene_name, WRITE, (("scene", "scene"),)),
    "set_scenes": (set_scenes, WRITE, SCENE_TARGETS),
    "fire_scene": (fire_scene, WRITE, (("scene", "scene"),)),
    "launch": (launch, WRITE, (("targets", "ref", ANY_KIND),)),
    "delete_scenes": (delete_scenes, WRITE, SCENE_TARGETS),
    "duplicate_scenes": (duplicate_scenes, WRITE, SCENE_TARGETS),
}
