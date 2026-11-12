"""Local capabilities, independent of tool visibility and the master read-only switch."""

from __future__ import annotations

PERMISSIONS = frozenset({"transport", "edit", "files", "delete"})
DEFAULT_PERMISSIONS = ["transport", "edit"]


def allowed_permissions(config: dict) -> frozenset[str]:
    """Legacy configs retain access; an explicit malformed list grants nothing."""
    if "permissions" not in config:
        return PERMISSIONS
    value = config["permissions"]
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        return frozenset()
    if set(value) - PERMISSIONS:
        return frozenset()
    return frozenset(value)


def _field(item, name):
    return item.get(name) if isinstance(item, dict) else getattr(item, name, None)


# Tools that delete only for some arguments: (does this call delete?, what the human confirms).
# Such a call needs the "delete" permission and a human confirmation, like live_delete. The
# Remote Script repeats the same rule per bridge method (safety.DELETING).
DELETING = {
    "live_create_clips": (
        lambda a: a.get("if_exists") == "replace",
        "if_exists='replace' deletes the clip in every occupied target slot",
    ),
    "live_create_arrangement_clips": (
        lambda a: any(_field(c, "replace") for c in a.get("clips") or ()),
        "replace=True deletes the clips wholly inside that target's span",
    ),
    "live_set_cue_points": (
        lambda a: any(_field(c, "action") == "delete" for c in a.get("cues") or ()),
        "every cue with action 'delete' is removed",
    ),
}


def deletes(tool: str, args: dict | None) -> bool:
    """True when this call of ``tool`` with ``args`` deletes something."""
    if tool == "live_delete":
        return True
    entry = DELETING.get(tool)
    return entry is not None and args is not None and bool(entry[0](args))


def required_permissions(tool: str, args: dict | None = None) -> frozenset[str]:
    if tool == "live_delete":
        return frozenset({"delete"})
    if tool in {"live_transport", "live_launch", "live_view"}:
        return frozenset({"transport"})
    if tool == "live_export_midi":
        return frozenset({"files"})
    if tool == "live_import_midi":
        return frozenset({"files", "edit"})
    if deletes(tool, args):
        return frozenset({"edit", "delete"})
    return frozenset({"edit"})
