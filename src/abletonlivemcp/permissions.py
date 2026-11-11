"""Local capabilities, independent of tool visibility and the master read-only switch."""

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


def required_permissions(tool: str) -> frozenset[str]:
    if tool == "live_delete":
        return frozenset({"delete"})
    if tool in {"live_transport", "live_launch", "live_view"}:
        return frozenset({"transport"})
    if tool == "live_export_midi":
        return frozenset({"files"})
    if tool == "live_import_midi":
        return frozenset({"files", "edit"})
    return frozenset({"edit"})
