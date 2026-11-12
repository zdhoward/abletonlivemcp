"""View domain (batch 2): ``view`` (show/hide/focus/zoom/scroll a named view, audition a browser
item, stop audition) and ``select`` (selected track/scene/detail clip/highlighted slot/device),
both behind the single ``live_view`` tool.

Evidence: P-23 (view names, ``is_view_visible`` reads, diagnostics); P-24 (track, scene,
detail-clip and device selection read back; ``select_device`` does not change the selected
track; chain and pad selection untested). View mutations and audition are ``unverified``.
"""

from .core import Invalid
from .dom_common import BROWSER_ROOTS, PATH_LIMIT, WALK_BUDGET, WRITE, Refused, require

# safety.ANY_KIND; importing it from .safety is circular (safety imports every dom_* first).
ANY_KIND = "any"

CAPABILITIES = {
    "view.show_hide": ("unverified", "P-23: names known; show/hide/focus unproven"),
    "view.zoom_scroll": ("unverified", "Application.View.zoom_view/scroll_view unproven"),
    "view.select": ("supported", "P-24: track/scene/detail clip/device selection read back"),
    "view.select_slot": ("unverified", "highlighted_clip_slot unproven"),
    "view.audition": ("unverified", "Browser.preview_item/stop_preview unproven"),
}

VIEWS = ("Browser", "Arranger", "Session", "Detail", "Detail/Clip", "Detail/DeviceChain")
DIRECTIONS = {"up": 0, "down": 1, "left": 2, "right": 3}


def _visible(app):
    view = app.view
    out = {}
    for name in VIEWS:
        try:
            out[name] = bool(view.is_view_visible(name))
        except Exception:  # noqa: BLE001 - a read never fails the reply
            out[name] = None
    return out


def _browser_item(app, root, path):
    """A bounded walk (``WALK_BUDGET`` nodes) to the exact item ``root``/``path``."""
    if root not in BROWSER_ROOTS or not hasattr(app.browser, root):
        raise Invalid(f"'root' must be one of {list(BROWSER_ROOTS)}")
    if not isinstance(path, list) or not 1 <= len(path) <= PATH_LIMIT:
        raise Invalid(f"'path' must be a list of 1..{PATH_LIMIT} names")
    item, visited = getattr(app.browser, root), 0
    for name in path:
        if not isinstance(name, str):
            raise Invalid("'path' must contain only strings")
        found = None
        for child in getattr(item, "children", None) or ():
            visited += 1
            if visited > WALK_BUDGET:
                raise Refused("browser_budget", f"path walk exceeded {WALK_BUDGET} nodes")
            if child.name == name:
                found = child
                break
        if found is None:
            raise Refused("item_not_found", f"no browser child named {name!r}")
        item = found
    return item


def view(ctx, p, _t):
    app = ctx.app
    action = p.get("action")
    name = p.get("view")
    if action in ("show", "hide", "focus", "zoom", "scroll"):
        if name not in VIEWS:
            raise Invalid(f"'view' must be one of {list(VIEWS)}")
    if action in ("show", "hide", "focus"):
        state = require(ctx, "view.show_hide", ((app.view, f"{action}_view"),))
        getattr(app.view, f"{action}_view")(name)
    elif action in ("zoom", "scroll"):
        direction = DIRECTIONS.get(p.get("direction"))
        if direction is None:
            raise Invalid(f"'direction' must be one of {list(DIRECTIONS)}")
        state = require(ctx, "view.zoom_scroll", ((app.view, f"{action}_view"),))
        getattr(app.view, f"{action}_view")(direction, name, False)
    elif action == "audition":
        state = require(ctx, "view.audition", ((app.browser, "preview_item"),))
        item = _browser_item(app, p.get("root"), p.get("path"))
        if not getattr(item, "is_loadable", False) or getattr(item, "is_folder", False):
            raise Invalid("audition needs a loadable browser item, not a folder")
        app.browser.preview_item(item)
    elif action == "stop_audition":
        state = require(ctx, "view.audition", ((app.browser, "stop_preview"),))
        app.browser.stop_preview()
    else:
        actions = ["show", "hide", "focus", "zoom", "scroll", "audition", "stop_audition"]
        raise Invalid(f"'action' must be one of {actions} (or use select)")
    return {
        "action": action,
        "unverified": [action] if state == "unverified" else [],
        "focused": getattr(app.view, "focused_document_view", None),
        "visible": _visible(app),
    }


SELECT = {
    "track": ("selected_track", "view.select"),
    "return_track": ("selected_track", "view.select"),
    "master": ("selected_track", "view.select"),
    "scene": ("selected_scene", "view.select"),
    "clip": ("detail_clip", "view.select"),
    "slot": ("highlighted_clip_slot", "view.select_slot"),
}


def select(ctx, _p, t):
    """Select one object (the list target holds exactly one item)."""
    targets = t["targets"]
    if len(targets) != 1:
        raise Invalid("select takes exactly one target")
    resolved = targets[0]
    kind, obj = resolved.path[-1][0], resolved.obj
    song_view = ctx.song.view
    if kind == "device":
        state = require(ctx, "view.select", ((song_view, "select_device"),))
        song_view.select_device(obj)
        try:  # the device's own parent view (P-24: the selected track does not follow)
            actual = resolved.path[-2][1].view.selected_device
        except Exception:  # noqa: BLE001 - readback is best effort
            actual = None
    elif kind in SELECT:
        attribute, capability = SELECT[kind]
        state = require(ctx, capability, ((song_view, attribute),))
        setattr(song_view, attribute, obj)
        actual = getattr(song_view, attribute)
    else:
        raise Invalid("select takes a track, scene, clip, slot or device")
    return {
        "action": "select",
        "kind": kind,
        "unverified": ["select"] if state == "unverified" else [],
        "selected": actual == obj,
        "name": getattr(obj, "name", None),
    }


METHODS = {
    "view": (view, WRITE, ()),
    "select": (select, WRITE, (("targets", "ref", ANY_KIND),)),
}
