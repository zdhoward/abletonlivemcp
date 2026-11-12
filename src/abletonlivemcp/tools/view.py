"""Toolset `view`: live_view (views, selection and browser audition in one tool)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..errors import Invalid
from ..models_control import ViewAction, ViewName, ViewTarget, owner_kind
from ..server import _call, _control, _generation, _untrusted, issue_refs


def _target_selector(t: ViewTarget) -> dict:
    if t.kind == "scene":
        if t.scene is None:
            raise Invalid("a scene target needs 'scene'")
        return {"kind": "scene", "scene": t.scene}
    if t.track is None:
        raise Invalid(f"a {t.kind} target needs 'track'")
    if t.kind == "track":
        return {"kind": owner_kind(t.track), "track": t.track}
    if t.kind == "device":
        if t.path is None:
            raise Invalid("a device target needs 'path'")
        return {"kind": "device", "track": t.track, "path": t.path}
    if t.scene is None:
        raise Invalid(f"a {t.kind} target needs 'scene'")
    return {"kind": t.kind, "track": t.track, "scene": t.scene}


@_control
def live_view(
    action: ViewAction,
    view: ViewName | None = None,
    direction: Literal["up", "down", "left", "right"] | None = None,
    target: ViewTarget | None = None,
    root: str | None = None,
    path: Annotated[list[str] | None, Field(min_length=1, max_length=8)] = None,
) -> dict:
    """show/hide/focus a `view`, zoom/scroll it (`direction`), select a `target` (track,
    scene, clip -> detail clip, slot, device), audition a browser item (`root`+`path`) or
    stop_audition. Returns the readback (visible views or selection)."""
    if action == "select":
        if target is None:
            raise Invalid("select needs 'target'")
        row = issue_refs([_target_selector(target)])[0]
        reply = _call("select", {"targets": [{"kind": row["kind"], "ref": row["ref"]}]})
        return _untrusted(reply)
    params: dict = {"action": action, "generation": _generation()}
    for key, val in (("view", view), ("direction", direction), ("root", root), ("path", path)):
        if val is not None:
            params[key] = val
    return _call("view", params)
