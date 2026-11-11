"""Labels domain: free tags and a category stored in the Set, on the Song and on each Track.

Live's ``Song.get_data`` / ``Track.get_data`` store survives Save and reopen (P-02: values
round-trip in session up to 1 MB; the final proof checks the reopen). One key holds one JSON string
``{"v": 1, "labels": [...], "category": "..."}``; an empty string means no labels. Corrupt text is
reported, never overwritten silently by a read.

Global labels (plugins, devices, samples) are not here: they live in the host's sidecar file.
"""

import json

from .dom_common import READ, WRITE, require, two_pass

KEY = "almcp_labels"
MAX_LABELS = 16
MAX_LABEL_CHARS = 40
MAX_JSON_CHARS = 4096
TRACK_KINDS = ("track", "return_track")
CAPABILITY = "labels.data"

CAPABILITIES = {
    CAPABILITY: (
        "unverified",
        "P-02: Song/Track get_data/set_data round-trip in session; save and reopen is checked by "
        "the final proof",
    ),
}


def _clean(text, what, limit):
    if not isinstance(text, str):
        raise ValueError(f"{what} must be text")
    text = text.strip()
    if any(ord(c) < 32 or ord(c) == 127 for c in text) or len(text) > limit:
        raise ValueError(f"{what} must be at most {limit} characters without control characters")
    return text


def _stored(obj):
    """(entry or None, corrupt) from the object's data store."""
    raw = obj.get_data(KEY, "")
    if raw in (None, ""):
        return None, False
    try:
        value = json.loads(raw)
        if not isinstance(value, dict) or not isinstance(value.get("labels"), list):
            raise ValueError("shape")
    except (TypeError, ValueError):
        return None, True
    entry = {"labels": [str(x) for x in value["labels"]]}
    if isinstance(value.get("category"), str) and value["category"]:
        entry["category"] = value["category"]
    return entry, False


def _merge(existing, labels, category, mode):
    """Same rules as the host's labelstore.merge; None means no labels remain."""
    old = list((existing or {}).get("labels", []))
    old_category = (existing or {}).get("category")
    if mode == "replace":
        new, new_category = list(dict.fromkeys(labels)), category
    elif mode == "add":
        new = list(dict.fromkeys(old + labels))
        new_category = category if category is not None else old_category
    elif mode == "remove":
        new = [x for x in old if x not in set(labels)]
        new_category = None if category == "" else old_category
    else:
        raise ValueError("'mode' must be 'replace', 'add' or 'remove'")
    if not new and not new_category:
        return None
    entry = {"labels": new}
    if new_category:
        entry["category"] = new_category
    return entry


def _prepare(obj, item, mode):
    """Pass 1 for one object: validate the item and compute the text to store."""
    if not isinstance(item, dict):
        raise ValueError("every item must be an object")
    labels = item.get("labels", [])
    if not isinstance(labels, list) or len(labels) > MAX_LABELS:
        raise ValueError(f"'labels' must be a list of at most {MAX_LABELS} texts")
    labels = [_clean(x, "a label", MAX_LABEL_CHARS) for x in labels]
    if "" in labels:
        raise ValueError("a label must not be empty")
    category = item.get("category")
    if category is not None:
        category = _clean(category, "'category'", MAX_LABEL_CHARS)
    existing, corrupt = _stored(obj)
    if corrupt and mode != "replace":
        raise ValueError("the stored labels are unreadable; use mode 'replace' to rewrite them")
    entry = _merge(existing, labels, category, mode)
    text = "" if entry is None else json.dumps({"v": 1, **entry}, ensure_ascii=False)
    if len(text) > MAX_JSON_CHARS:
        raise ValueError(f"the labels would exceed {MAX_JSON_CHARS} characters")
    return obj, entry, text


def _write(prepared):
    obj, entry, text = prepared
    obj.set_data(KEY, text)
    if obj.get_data(KEY, "") != text:
        raise RuntimeError("readback differs from what was written")
    name = getattr(obj, "name", None)
    return {"name": name if isinstance(name, str) else None, "labels": entry}


def _mode(p):
    mode = p.get("mode", "replace")
    if mode not in ("replace", "add", "remove"):
        raise ValueError("'mode' must be 'replace', 'add' or 'remove'")
    return mode


def _state_note(state):
    return [CAPABILITY] if state == "unverified" else []


def get_labels(ctx, _p):
    """Every labelled object: the Song, tracks and return tracks."""
    song = ctx.song
    state = require(ctx, CAPABILITY, ((song, "get_data"),))
    rows, corrupt = [], []
    song_entry, song_bad = _stored(song)
    for kind, seq in (("track", song.tracks), ("return_track", song.return_tracks)):
        for index, track in enumerate(seq):
            entry, bad = _stored(track)
            if entry is not None or bad:
                row = {"kind": kind, "index": index, "name": track.name, "labels": entry}
                rows.append(row)
                if bad:
                    corrupt.append(f"{kind}/{index}")
    if song_bad:
        corrupt.append("song")
    return {
        "generation": ctx.safety.generation,
        "song": song_entry,
        "tracks": rows,
        "corrupt": corrupt,
        "unverified": _state_note(state),
    }


def set_song_labels(ctx, p, _t):
    """Labels on the Song itself (a global write: the request carries the generation)."""
    state = require(ctx, CAPABILITY, ((ctx.song, "set_data"), (ctx.song, "get_data")))
    mode = _mode(p)
    receipt = two_pass([p.get("item")], lambda _i, item: _prepare(ctx.song, item, mode), _write)
    return {**receipt, "unverified": _state_note(state)}


def set_track_labels(ctx, p, t):
    """Labels on tracks or return tracks named by reference, one two-pass batch."""
    state = require(ctx, CAPABILITY)
    mode = _mode(p)
    items = p.get("items")
    pairs = list(zip(t["items"], items, strict=True))

    def validate(_i, pair):
        resolved, item = pair
        if item.get("kind") not in TRACK_KINDS:
            raise ValueError("track labels need kind 'track' or 'return_track'")
        require(ctx, CAPABILITY, ((resolved.obj, "get_data"), (resolved.obj, "set_data")))
        return _prepare(resolved.obj, item, mode)

    return {**two_pass(pairs, validate, _write), "unverified": _state_note(state)}


# "any" is safety.ANY_KIND: importing it here would be circular (safety imports every domain
# module before it defines the constant), so the literal is used.
METHODS = {
    "get_labels": (get_labels, READ, None),
    "set_song_labels": (set_song_labels, WRITE, ()),
    "set_track_labels": (set_track_labels, WRITE, (("items", "ref", "any"),)),
}
