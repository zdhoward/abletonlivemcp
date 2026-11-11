"""Scenes domain: list scenes (issuing references), create, rename, fire."""

from .dom_common import READ, WRITE


def scenes(ctx, _p):
    return [
        {"index": i, "ref": ctx.safety.issue(("scene", s, {})), "name": s.name}
        for i, s in enumerate(ctx.song.scenes)
    ]


def create_scene(ctx, p, _t):
    song = ctx.song
    index = p.get("index", -1)
    if isinstance(index, bool) or not isinstance(index, int) or not -1 <= index <= len(song.scenes):
        raise ValueError(f"'index' must be an integer -1..{len(song.scenes)} (-1 = end)")
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
        raise ValueError("'name' must be a string")
    scene.name = name
    return {"name": scene.name}


def fire_scene(_ctx, _p, t):
    scene = t["scene"].obj
    scene.fire()
    return {"name": scene.name, "is_triggered": scene.is_triggered}


METHODS = {
    "scenes": (scenes, READ, None),
    "create_scene": (create_scene, WRITE, ()),
    "set_scene_name": (set_scene_name, WRITE, (("scene", "scene"),)),
    "fire_scene": (fire_scene, WRITE, (("scene", "scene"),)),
}
