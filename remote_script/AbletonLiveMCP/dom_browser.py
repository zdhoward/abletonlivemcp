"""Browser domain: bounded listing and search, device loads and their operation records.

Two load routes:

- ``load_item`` (proven): an audio effect onto an empty (or owned-prefix) regular audio track,
  observed by ``operations.begin``/tick.
- ``load_device`` (v2): any supported item onto a regular audio/MIDI track, a return, the master,
  a rack chain or a drum pad. Each target kind has its own capability gate. Placement is observed
  by a bounded identity diff on the target container in an ``operations.start_task`` step: one
  new device, appended, stable across two ticks. Anything else is ``unknown``, quarantines that
  target (and, for chain/pad loads, the capability), and is never retried.
"""

from itertools import islice

from .core import log_failure, public_error
from .dom_common import (
    BROWSER_ROOTS,
    LIST_LIMIT,
    LOAD_ROOTS,
    PATH_LIMIT,
    READ,
    SEARCH_LIMIT,
    SUPPORTED,
    UNSUPPORTED,
    UNVERIFIED,
    WALK_BUDGET,
    WRITE,
    Refused,
    _same,
    quarantine,
    require,
    same_items,
)

ANY_KIND = "any"  # safety.ANY_KIND; importing it here is circular (safety imports dom_*)

_END = object()
EXTRA_ROOTS = ("max_for_live", "clips", "user_folders")  # T-016: listed/searched when present
ALL_ROOTS = BROWSER_ROOTS + EXTRA_ROOTS
LOAD_TASK_TIMEOUT = 10.0  # the contract's task cap; a slower load reads as unknown (quarantined)
LOAD_HISTORY = 16

# root -> item category; a category loads only onto the target kinds in TARGET_CATEGORIES
CATEGORIES = {
    "audio_effects": "audio_effect",
    "plugins": "plugin",
    "instruments": "instrument",
    "drums": "drums",
    "sounds": "sound",
    "midi_effects": "midi_effect",
    "max_for_live": "max_for_live",
    "samples": "sample",
    "user_library": "user",
    "packs": "user",
    "current_project": "user",
    "user_folders": "user",
}
FX = ("audio_effect", "plugin", "max_for_live", "user")
SOURCES = ("instrument", "drums", "sound", "sample")  # need an empty MIDI container
TARGET_CATEGORIES = {
    "audio_track": FX,
    "midi_track": FX + SOURCES + ("midi_effect",),
    "return": FX,
    "master": FX,
    "chain": FX + SOURCES + ("midi_effect",),
    "drum_pad": ("instrument", "sound", "sample", "plugin", "user"),
}

CAPABILITIES = {
    "load.audio_track": (SUPPORTED, "audio effect loads observed since M1 (live_write_test)"),
    "load.midi_track": (UNVERIFIED, "P-14 unrun: instrument/drum loads onto a MIDI track"),
    "load.return": (UNVERIFIED, "P-14 unrun: loads onto a return track"),
    "load.master": (UNVERIFIED, "P-14 unrun: loads onto the master track"),
    "load.chain": (UNVERIFIED, "P-14 unrun: selected_chain then load_item"),
    "load.drum_pad": (
        UNSUPPORTED,
        "final proof 2026-11-11: selected_drum_pad then load_item ended unknown "
        "(ArgumentError) on Live 12.2; load a kit from the drums root instead",
    ),
}


def _item_info(item):
    return {
        "name": item.name,
        "uri": getattr(item, "uri", None),
        "is_folder": bool(getattr(item, "is_folder", False)),
        "is_loadable": bool(getattr(item, "is_loadable", False)),
    }


class _Folder:
    """A root that Live exposes as a list of items (``user_folders``) seen as one folder."""

    is_folder, is_loadable, uri = True, False, None

    def __init__(self, name, children):
        self.name, self.children = name, children


def _roots(app):
    return [r for r in ALL_ROOTS if hasattr(app.browser, r)]


def _root(app, params):
    name = params.get("root")
    if name not in ALL_ROOTS or not hasattr(app.browser, name):
        raise ValueError(f"'root' must be one of {_roots(app)}")
    node = getattr(app.browser, name)
    if isinstance(node, (list, tuple)) or not hasattr(node, "children"):
        return _Folder(name, tuple(node or ()))
    return node


def _iter_children(item):
    """Lazy iterator over ``item.children``. The single native ``children`` access cannot be
    preempted, but nothing is copied and every caller stops after its own bounded count."""
    kids = getattr(item, "children", None)
    return iter(kids) if kids is not None else iter(())


def _find_child(node, name, unique, budget=WALK_BUDGET):
    """Scan ``node``'s children for ``name`` visiting at most ``budget`` nodes.
    Returns ``(matches, exhausted)``: first match only (or up to two when ``unique``) and whether
    the budget ended the scan before the children did."""
    matches, visited = [], 0
    for child in _iter_children(node):
        if visited >= budget:
            return matches, True
        visited += 1
        if child.name == name:
            matches.append(child)
            if not unique or len(matches) == 2:
                break
    return matches, False


def _walk_path(item, names):
    if not isinstance(names, list) or len(names) > PATH_LIMIT:
        raise ValueError(f"'path' must be a list of at most {PATH_LIMIT} names")
    for name in names:
        if not isinstance(name, str):
            raise ValueError("'path' must contain only strings")
        match, exhausted = _find_child(item, name, False)
        if not match:
            if exhausted:
                raise Refused("browser_budget", f"path walk exceeded {WALK_BUDGET} nodes")
            raise ValueError(f"no child named {name!r}")
        item = match[0]
    return item


def _walk_path_unique(root, names):
    if not isinstance(names, list) or not 1 <= len(names) <= PATH_LIMIT:
        raise ValueError(f"'path' must be a list of 1..{PATH_LIMIT} names")
    item = root
    for name in names:
        if not isinstance(name, str):
            raise ValueError("'path' must contain only strings")
        matches, exhausted = _find_child(item, name, True)
        if exhausted:
            raise Refused("browser_budget", f"path walk exceeded {WALK_BUDGET} nodes")
        if len(matches) != 1:
            code = "item_not_found" if not matches else "ambiguous_item"
            raise Refused(code, f"{len(matches)} children named {name!r}; expected exactly 1")
        item = matches[0]
    return item


def _count(p, key, default, maximum):
    value = p.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ValueError(f"'{key}' must be an integer 1..{maximum}")
    return value


# ---- reads ----------------------------------------------------------------------------------


def browser_roots(ctx, _p):
    return [r for r in BROWSER_ROOTS if hasattr(ctx.app.browser, r)]


def browser_list(ctx, p):
    """One page (<= LIST_LIMIT items). ``cursor`` continues a truncated listing. Without
    ``root`` (and no cursor) it lists the roots this Live has, as folders."""
    if p.get("root") is None and p.get("cursor") is None:
        roots = [
            {"name": r, "uri": None, "is_folder": True, "is_loadable": False}
            for r in _roots(ctx.app)
        ]
        return {"complete": True, "truncated": False, "cursor": None, "items": roots}
    limit = _count(p, "limit", LIST_LIMIT, LIST_LIMIT)
    if p.get("cursor") is None:
        node, offset = _walk_path(_root(ctx.app, p), p.get("path") or []), 0
    else:
        node, offset = ctx.operations.cursors.take(p["cursor"], "list")
    page = list(islice(_iter_children(node), offset, offset + limit + 1))
    more = len(page) > limit
    return {
        "complete": not more,
        "truncated": more,
        "cursor": ctx.operations.cursors.put("list", (node, offset + limit)) if more else None,
        "items": [_item_info(c) for c in page[:limit]],
    }


def browser_search(ctx, p):
    """Depth-first slice of at most WALK_BUDGET visited nodes / ``limit`` results. When it
    stops early it returns ``cursor``; ``complete`` is true only when the walk finished."""
    limit = _count(p, "limit", 25, SEARCH_LIMIT)
    if p.get("cursor") is None:
        query = str(p.get("query", "")).strip().lower()
        if not query:
            raise ValueError("'query' is required")
        stack = [([], _iter_children(_root(ctx.app, p)))]
    else:
        query, stack = ctx.operations.cursors.take(p["cursor"], "search")
    found, visited = [], 0
    while stack and len(found) < limit and visited < WALK_BUDGET:
        path, kids = stack[-1]
        child = next(kids, _END)
        if child is _END:
            stack.pop()
            continue
        visited += 1
        if query in child.name.lower():
            found.append({**_item_info(child), "path": path + [child.name]})
        if getattr(child, "is_folder", False):  # only folders are descended into
            stack.append((path + [child.name], _iter_children(child)))
    done = not stack
    return {
        "results": found,
        "visited": visited,
        "complete": done,
        "truncated": not done and len(found) >= limit,
        "budget_exhausted": not done and visited >= WALK_BUDGET,
        "cursor": None if done else ctx.operations.cursors.put("search", (query, stack)),
    }


def operation(ctx, p):
    """One record by ``operation`` id, or up to 16 by ``operations`` (a list) in one read."""
    if p.get("operations") is not None:
        return ctx.operations.get_many(p.get("operations"))
    return ctx.operations.get(p.get("operation"))


# ---- loads ----------------------------------------------------------------------------------


def _load_target(ctx, track, p):
    """Preconditions that must hold before any browser call. Raises Refused."""
    if p.get("root") not in LOAD_ROOTS:
        raise Refused("unsupported_root", f"only {list(LOAD_ROOTS)} items can be loaded")
    if not any(_same(x, track) for x in ctx.song.tracks):
        raise Refused("unsupported_target", "target must be a regular track of the Set")
    if track.has_midi_input or getattr(track, "is_foldable", False):
        raise Refused("unsupported_target", "target must be a regular audio track")
    ctx.operations.check_can_load(track)
    after = p.get("after")
    if after is None:
        if len(track.devices):
            raise Refused("target_occupied", "track already has devices; only empty tracks")
        return
    prior = ctx.operations.prior(after)
    if (
        prior is None
        or prior.state != "ready"
        or prior.generation != ctx.safety.generation
        or not _same(prior.track, track)
        or not same_items(prior.after, track.devices)
    ):
        raise Refused("prefix_mismatch", "track is not exactly the ready prefix of 'after'")


def _select_last_device(ctx, track):
    """Make the track's last device Live's insertion point; refuse unless observed."""
    last = track.devices[-1]
    select = getattr(getattr(ctx.song, "view", None), "select_device", None)
    if not callable(select):
        raise Refused("append_unverified", "song.view.select_device is not available")
    try:
        select(last)
        selected = track.view.selected_device
    except Exception as exc:  # noqa: BLE001
        raise Refused("append_unverified", f"cannot select last device: {exc!r}") from exc
    if not _same(selected, last):
        raise Refused("append_unverified", "last device selection was not observed")


def load_item(ctx, p, t):
    """Start a native load of one supported audio-effect device onto an empty (or owned
    prefix) audio track and return an operation record. Completion is observed on later
    display ticks (``operation`` reads it); this never retries and never waits."""
    track = t["track"].obj
    _task_guard(ctx, track)
    _load_target(ctx, track, p)
    item = _walk_path_unique(_root(ctx.app, p), p.get("path"))
    if not getattr(item, "is_loadable", False) or getattr(item, "is_device", False) is not True:
        raise Refused("unsupported_item", f"{item.name!r} is not a loadable device")
    ctx.song.view.selected_track = track
    append = p.get("after") is not None
    if append:
        _select_last_device(ctx, track)
    op = ctx.operations.begin(track, item.name, p["root"], append=append)
    try:
        ctx.app.browser.load_item(item)
    except Exception as exc:  # noqa: BLE001 - outcome is established by observation
        ctx.operations.native_error(op, exc)
    return ctx.operations.snapshot(op)


# ---- load_device (v2 targets) ----------------------------------------------------------------


class _PadSlot:
    """A drum pad watched as a device container: its first chain's devices (none before)."""

    def __init__(self, pad):
        self.pad = pad

    @property
    def devices(self):
        chains = self.pad.chains
        return tuple(chains[0].devices) if len(chains) else ()

    def __eq__(self, other):
        return isinstance(other, _PadSlot) and _same(self.pad, other.pad)

    __hash__ = object.__hash__


def _loads(ctx):
    """Per-session load_device history kept on the operations store (a fresh store, a fresh
    history): ``(operation id, watched container, capability)`` newest last, and the ids whose
    native call raised with nothing changed (failed, not unknown)."""
    ops = ctx.operations
    if not hasattr(ops, "_device_loads"):
        ops._device_loads, ops._device_failed = [], set()
    return ops._device_loads, ops._device_failed


def _task_guard(ctx, container):
    """One load at a time across both routes; a load_device with an unknown outcome
    quarantines its container (and, for chain/pad targets, the whole capability)."""
    loads, failed = _loads(ctx)
    for op_id, watched, cap in list(loads):
        rec = ctx.operations.prior(op_id)
        if rec is None or op_id in failed:
            continue
        if rec.generation != ctx.safety.generation:
            continue
        if rec.state == "pending":
            raise Refused("load_pending", f"load {op_id} is still pending; read it, do not retry")
        if rec.state == "unknown":
            if cap in ("load.chain", "load.drum_pad"):
                quarantine(ctx, cap, f"load {op_id} had an unknown outcome")
            if _same(watched, container):
                raise Refused("quarantined", f"load {op_id} on this target has an unknown outcome")


def _classify(ref):
    """Resolved target -> (target kind, watched container, owner track, rack or None)."""
    kind, obj = ref.path[-1][0], ref.obj
    if kind == "track":
        if getattr(obj, "is_foldable", False):
            raise Refused("unsupported_target", "a group track holds no devices")
        return ("midi_track" if obj.has_midi_input else "audio_track"), obj, obj, None
    if kind in ("return_track", "master"):
        return ("return" if kind == "return_track" else "master"), obj, obj, None
    if kind == "chain":
        return "chain", obj, ref.path[0][1], ref.path[-2][1]
    if kind == "drum_pad":
        return "drum_pad", _PadSlot(obj), ref.path[0][1], ref.path[-2][1]
    raise ValueError("the load target must be a track, return, master, chain or drum pad")


def _prior_layout(ctx, after):
    rec = ctx.operations.prior(after)
    if rec is None or rec.state != "ready" or rec.generation != ctx.safety.generation:
        return None
    result = getattr(rec, "result", None)
    if isinstance(result, dict):
        return list(result.get("devices_after") or ())
    return list(getattr(rec, "devices_after", None) or ())


def _select(ctx, owner, rack, tkind, ref, last):
    """Make Live's insertion point the target; refuse (before loading) unless observed."""
    view = ctx.song.view
    try:
        view.selected_track = owner
        if tkind == "chain":
            rack.view.selected_chain = ref.obj
            if not _same(rack.view.selected_chain, ref.obj):
                raise RuntimeError("selected_chain not observed")
        elif tkind == "drum_pad":
            rack.view.selected_drum_pad = ref.obj
            if not _same(rack.view.selected_drum_pad, ref.obj):
                raise RuntimeError("selected_drum_pad not observed")
        if last is not None:
            view.select_device(last)
            if not _same(owner.view.selected_device, last):
                raise RuntimeError("last device selection not observed")
    except Exception as exc:  # noqa: BLE001 - selection is view state; nothing loaded yet
        log_failure("load target selection", exc)
        why = public_error(exc, "select_failed")
        raise Refused("append_unverified", f"cannot select the load target ({why})") from exc


def _validate_device_load(ctx, p, tkind, container):
    root = p.get("root")
    category = CATEGORIES.get(root)
    if category is None or root not in _roots(ctx.app):
        raise Refused("unsupported_root", f"{root!r} items cannot be loaded here")
    if category not in TARGET_CATEGORIES[tkind]:
        raise Refused("unsupported_target", f"{root} items do not load onto a {tkind}")
    before = tuple(container.devices)
    if not before:
        return before
    if category in SOURCES:
        raise Refused(
            "target_occupied", "instruments, drums, sounds and samples load only when empty"
        )
    if category == "midi_effect" and any(getattr(d, "type", 0) != 4 for d in before):
        raise Refused("unsupported_target", "a MIDI effect cannot be appended after an instrument")
    after = p.get("after")
    if after is not None:
        if _prior_layout(ctx, after) != [d.class_name for d in before]:
            raise Refused("prefix_mismatch", "target is not exactly the ready prefix of 'after'")
    elif p.get("append") is not True:
        raise Refused("target_occupied", "the target has devices: pass append to add at the end")
    return before


def load_device(ctx, p, t):
    """Start loading one browser item onto a target (``targets: [{kind, ref}]``) and return a
    task record; ``operation`` reads it. Never retries, never waits."""
    if len(t["targets"]) != 1:
        raise ValueError("'targets' must hold exactly one load target")
    ref = t["targets"][0]
    tkind, container, owner, rack = _classify(ref)
    cap = "load." + tkind
    state = require(ctx, cap)
    before = _validate_device_load(ctx, p, tkind, container)
    ctx.operations.check_can_load(container)  # legacy route: pending anywhere / unknown here
    _task_guard(ctx, container)
    item = _walk_path_unique(_root(ctx.app, p), p.get("path"))
    if not getattr(item, "is_loadable", False):
        raise Refused("unsupported_item", f"{item.name!r} is not loadable")
    _select(ctx, owner, rack, tkind, ref, before[-1] if before else None)
    owner_before = tuple(owner.devices)
    seen = {}

    def step():
        cur = tuple(container.devices)
        n = len(before)
        if len(cur) < n or not same_items(cur[:n], before):
            raise RuntimeError("layout_changed")
        if tkind in ("chain", "drum_pad") and not same_items(tuple(owner.devices), owner_before):
            quarantine(ctx, cap, "a chain/pad load changed the owner track")
            raise RuntimeError("landed_outside_target")
        extra = cur[n:]
        if not extra:
            return None
        if len(extra) > 1:
            raise RuntimeError("ambiguous_change")
        dev, count = extra[0], len(extra[0].parameters)
        prev = seen.get("dev")
        seen["dev"] = (dev, count)
        if not (count and prev is not None and _same(prev[0], dev) and prev[1] == count):
            return None
        return {
            "target": tkind,
            "item": item.name,
            "root": p["root"],
            "device_index": n,
            "devices_after": [d.class_name for d in cur],
            "names_after": [d.name for d in cur],
        }

    snap = ctx.operations.start_task("load", step, LOAD_TASK_TIMEOUT)
    loads, failed = _loads(ctx)
    loads.append((snap["operation"], container, cap))
    del loads[:-LOAD_HISTORY]
    failed.intersection_update(e[0] for e in loads)
    try:
        ctx.app.browser.load_item(item)
    except Exception as exc:  # noqa: BLE001 - outcome is established by observation
        if same_items(tuple(container.devices), before):
            failed.add(snap["operation"])
            log_failure("load_item", exc)
            why = public_error(exc, "load_failed")
            raise Refused("load_failed", f"Live refused the load ({why})") from exc
    snap.update({"target": tkind, "item": item.name, "root": p["root"]})
    snap["unverified"] = [cap] if state == UNVERIFIED else []
    return snap


METHODS = {
    "browser_roots": (browser_roots, READ, None),
    "browser_list": (browser_list, READ, None),
    "browser_search": (browser_search, READ, None),
    "operation": (operation, READ, None),
    "load_item": (load_item, WRITE, (("track", "track"),)),
    "load_device": (load_device, WRITE, (("targets", "ref", ANY_KIND),)),
}
