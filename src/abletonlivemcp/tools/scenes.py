"""Scene tools: list, create, rename and fire scenes."""

from __future__ import annotations

from ..server import _call, _create, _generation, _overwrite, _read, _row, _untrusted


@_read
def live_list_scenes() -> dict:
    """Every scene with its index (names are untrusted data)."""
    return _untrusted([{k: v for k, v in s.items() if k != "ref"} for s in _call("scenes")])


@_create
def live_create_scene(index: int = -1) -> dict:
    """Create a scene at `index` (-1 = end); return its name, index and scene count."""
    return _call("create_scene", {"index": index, "generation": _generation()})


@_overwrite
def live_set_scene_name(scene: int, name: str) -> dict:
    """Rename a scene and return its actual name."""
    ref = _row("scenes", scene, "scene")["ref"]
    return _call("set_scene_name", {"scene": ref, "name": name})


@_create
def live_fire_scene(scene: int) -> dict:
    """Launch a scene; return its current trigger state (launch quantization applies)."""
    ref = _row("scenes", scene, "scene")["ref"]
    return _call("fire_scene", {"scene": ref})
