"""P-01: dir() and docstrings of the Live object model classes (introspection, read-only).

Walks a fixed table of class paths under the ``Live`` module (no request argument is used), dumps
each class's public members with a truncated docstring, lists the names in each ``Live``
submodule, and answers the plan's ``hasattr`` questions by listing which dumped classes own each
member. It reads class objects only: no Live object is created, changed or called.
"""

import json

from .core import _validate
from .dom_common import READ, _live_version

PROBE_ID = "P-01"
KIND = READ

# label -> candidate attribute paths under ``Live``; the first that resolves wins.
CLASSES = (
    ("Song", ("Song", "Song")),
    ("Song.View", ("Song", "Song", "View")),
    ("Track", ("Track", "Track")),
    ("ClipSlot", ("ClipSlot", "ClipSlot")),
    ("Clip", ("Clip", "Clip")),
    ("Clip.View", ("Clip", "Clip", "View")),
    ("Scene", ("Scene", "Scene")),
    ("Device", ("Device", "Device")),
    ("DeviceParameter", ("DeviceParameter", "DeviceParameter")),
    ("RackDevice", ("RackDevice", "RackDevice")),
    ("DrumPad", ("DrumPad", "DrumPad")),
    ("Chain", ("Chain", "Chain")),
    ("DrumChain", ("DrumChain", "DrumChain")),
    ("SimplerDevice", ("SimplerDevice", "SimplerDevice")),
    ("Sample", ("Sample", "Sample")),
    ("PluginDevice", ("PluginDevice", "PluginDevice")),
    ("MaxDevice", ("MaxDevice", "MaxDevice")),
    ("MixerDevice", ("MixerDevice", "MixerDevice")),
    ("CuePoint", ("Song", "CuePoint"), ("CuePoint", "CuePoint")),
    ("Envelope", ("Clip", "AutomationEnvelope"), ("Envelope", "Envelope")),
    ("TakeLane", ("TakeLane", "TakeLane"), ("Track", "TakeLane")),
    ("GroovePool", ("GroovePool", "GroovePool")),
    ("Groove", ("Groove", "Groove")),
    ("TuningSystem", ("TuningSystem", "TuningSystem")),
    ("Browser", ("Browser", "Browser")),
    ("BrowserItem", ("Browser", "BrowserItem")),
    ("Application", ("Application", "Application")),
    ("Application.View", ("Application", "Application", "View")),
    ("Conversions", ("Conversions",)),
)

# Members whose owners settle the plan's hasattr questions (P-01 row of section 4).
QUESTIONS = (
    "tap_tempo",
    "nudge_up",
    "nudge_down",
    "exclusive_arm",
    "exclusive_solo",
    "back_to_arranger",
    "is_frozen",
    "can_be_frozen",
    "duplicate_device",
    "note_number_to_name",
    "delete_clip",
    "begin_undo_step",
    "end_undo_step",
    "get_data",
    "set_data",
    "insert_device",
    "move_device",
)
SUBSTRINGS = ("follow_action", "freeze")  # members containing these are listed per class

BUDGET = 700_000  # encoded bytes; the bridge frame limit is 1 MiB
DOC_LIMITS = (400, 160, 60, 0)  # docstring truncation steps until the dump fits the budget
MODULE_NAME_LIMIT = 200  # names listed per Live submodule


def _resolve(live, paths):
    for path in paths:
        obj = live
        try:
            for part in path:
                obj = getattr(obj, part)
        except Exception:  # noqa: BLE001 - absent on this version
            continue
        return ".".join(("Live",) + path), obj
    return None, None


def _doc(obj):
    try:
        doc = obj.__doc__
    except Exception:  # noqa: BLE001
        return ""
    return " ".join(doc.split()) if isinstance(doc, str) else ""


def _members(obj):
    out = {}
    try:
        names = sorted(n for n in dir(obj) if not n.startswith("__"))
    except Exception:  # noqa: BLE001
        return out
    for name in names:
        try:
            out[name] = _doc(getattr(obj, name))
        except Exception as exc:  # noqa: BLE001 - record, never fail the dump
            out[name] = f"<getattr failed: {type(exc).__name__}>"
    return out


def _modules(live):
    out = {}
    for name in sorted(n for n in dir(live) if not n.startswith("_")):
        try:
            module = getattr(live, name)
        except Exception:  # noqa: BLE001
            continue
        if type(module) is type(live):
            out[name] = sorted(n for n in dir(module) if not n.startswith("_"))[:MODULE_NAME_LIMIT]
    return out


def _fit(classes, extra):
    """Truncate docstrings until the encoded dump fits the budget; returns (classes, limit)."""
    for limit in DOC_LIMITS:
        trimmed = {
            label: dict(entry, members={m: d[:limit] for m, d in entry["members"].items()})
            for label, entry in classes.items()
        }
        size = len(json.dumps({"classes": trimmed, **extra}, separators=(",", ":")))
        if size <= BUDGET:
            return trimmed, limit
    raise RuntimeError("the member dump exceeds the bridge budget even without docstrings")


def run(ctx, scratch):
    import Live

    classes, missing = {}, []
    for label, *paths in CLASSES:
        where, obj = _resolve(Live, paths)
        if obj is None:
            missing.append(label)
            continue
        classes[label] = {"path": where, "doc": _doc(obj), "members": _members(obj)}
    owners = {
        q: sorted(label for label, entry in classes.items() if q in entry["members"])
        for q in QUESTIONS
    }
    matches = {
        s: {
            label: [m for m in entry["members"] if s in m]
            for label, entry in classes.items()
            if any(s in m for m in entry["members"])
        }
        for s in SUBSTRINGS
    }
    extra = {
        "live_version": _live_version(ctx.app),
        "missing": missing,
        "hasattr": owners,
        "matching": matches,
        "modules": _modules(Live),
    }
    classes, doc_limit = _fit(classes, extra)
    result = {
        "verdict": "go" if classes else "no-go",
        "doc_limit": doc_limit,
        "classes": classes,
        **extra,
    }
    _validate(result)  # fail here, readably, rather than in the bridge encoder (node limit)
    return result
