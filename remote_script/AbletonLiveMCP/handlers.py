"""Bridge dispatch. ``song`` is Live's ``Song`` (or a test double), ``app`` is Live's Application.

The handlers live in the ``dom_*`` modules, one per domain, each declaring its methods in
``METHODS``; ``safety`` merges those tables (``CLASSIFICATION``, ``TARGETS``, ``HANDLERS``).

Rules: reads are bounded (browser walks have a node budget); every write reads the value back
and returns it, so callers can see what actually happened; nothing here retries.

Every call goes through ``make_dispatch``'s gate (see ``safety.py`` for the dispatch contract):
writes receive already-validated targets and never resolve an index themselves.
"""

import functools
from itertools import islice
from types import SimpleNamespace

from .dom_common import (  # noqa: F401 - limits re-exported for callers and tests
    APPEND_PLACEMENT_VERIFIED,
    BATCH_LIMIT,
    BROWSER_ROOTS,
    LIST_LIMIT,
    LOAD_ROOTS,
    NOTE_LIMIT,
    PATH_LIMIT,
    SAMPLE_LIMIT,
    SEARCH_LIMIT,
    WALK_BUDGET,
    _note_specification,
)
from .operations import Operations
from .safety import CLASSIFICATION, CONTROL, HANDLERS, READ, Refused, Safety


def _handlers(song, app, safety, operations=None):
    """Handler table bound to one Song. Reads take ``(p)``; writes take ``(p, t)`` where ``t``
    holds the targets the gate already resolved and validated."""
    ctx = SimpleNamespace(
        song=song,
        app=app,
        safety=safety,
        operations=operations or Operations(safety),
        probe=lambda: probe(song, app),
    )
    return {name: functools.partial(handler, ctx) for name, handler in HANDLERS.items()}


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
