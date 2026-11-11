"""Browser domain: bounded listing and search, device loads and their operation records."""

from itertools import islice

from .dom_common import (
    BROWSER_ROOTS,
    LIST_LIMIT,
    LOAD_ROOTS,
    PATH_LIMIT,
    READ,
    SEARCH_LIMIT,
    WALK_BUDGET,
    WRITE,
    Refused,
    _same,
    same_items,
)

_END = object()


def _item_info(item):
    return {
        "name": item.name,
        "uri": getattr(item, "uri", None),
        "is_folder": bool(getattr(item, "is_folder", False)),
        "is_loadable": bool(getattr(item, "is_loadable", False)),
    }


def _root(app, params):
    name = params.get("root")
    if name not in BROWSER_ROOTS or not hasattr(app.browser, name):
        present = [r for r in BROWSER_ROOTS if hasattr(app.browser, r)]
        raise ValueError(f"'root' must be one of {present}")
    return getattr(app.browser, name)


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
    """One page (<= LIST_LIMIT items). ``cursor`` continues a truncated listing."""
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


METHODS = {
    "browser_roots": (browser_roots, READ, None),
    "browser_list": (browser_list, READ, None),
    "browser_search": (browser_search, READ, None),
    "operation": (operation, READ, None),
    "load_item": (load_item, WRITE, (("track", "track"),)),
}
