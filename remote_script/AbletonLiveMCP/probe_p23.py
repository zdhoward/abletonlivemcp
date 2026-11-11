"""P-23: Application.View names, dialog state and process usage (introspection, read-only).

Reads only: ``Application.View.available_main_views``, ``browse_mode``, ``focused_document_view``,
``is_view_visible`` for every available main view, ``open_dialog_count``,
``current_dialog_message``, ``current_dialog_button_count``, ``average_process_usage`` and
``peak_process_usage``. Nothing is shown, hidden, focused or pressed. Each read is in its own
``try`` and a failure is recorded as ``{"error": ...}`` rather than failing the probe.

Verdict: ``gated`` when ``Application.View`` is absent; ``go`` when the view-name list was read and
is non-empty; otherwise ``no-go``.
"""

from .dom_common import READ

PROBE_ID = "P-23"
KIND = READ

APP_VALUES = (
    "open_dialog_count",
    "current_dialog_message",
    "current_dialog_button_count",
    "average_process_usage",
    "peak_process_usage",
    "number_of_push_apps_running",
)
VIEW_VALUES = ("browse_mode", "focused_document_view")
MAX_VIEWS = 40


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def _plain(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return repr(value)[:80]


def _read(obj, name):
    try:
        return _plain(getattr(obj, name))
    except AttributeError:
        return {"absent": True}
    except Exception as exc:  # noqa: BLE001
        return {"error": _err(exc)}


def verdict_for(view_present, views):
    """Pure verdict rule."""
    if not view_present:
        return "gated"
    return "go" if isinstance(views, list) and views else "no-go"


def run(ctx, scratch):
    app = ctx.app
    view = getattr(app, "view", None)
    result = {"app": {n: _read(app, n) for n in APP_VALUES}}
    if view is None:
        result.update(verdict="gated", reason="Application.view is absent")
        return result
    names = []
    try:
        raw = view.available_main_views  # a method in the Live docs; tolerate a property too
        names = [str(n) for n in list(raw() if callable(raw) else raw)][:MAX_VIEWS]
        result["available_main_views"] = names
    except Exception as exc:  # noqa: BLE001
        result["available_main_views"] = {"error": _err(exc)}
    result["view"] = {n: _read(view, n) for n in VIEW_VALUES}
    visible = {}
    for name in names:
        try:
            visible[name] = _plain(view.is_view_visible(name))
        except Exception as exc:  # noqa: BLE001
            visible[name] = {"error": _err(exc)}
    result["is_view_visible"] = visible
    result["verdict"] = verdict_for(True, names)
    return result
