"""Arrangement domain: reads, direct clip creation (P-08), clip field edits, cue points.

Live 12.2 facts: ``Track.create_midi_clip(start, length)`` and ``Track.create_audio_clip(path,
start)`` work (P-08). Session-to-Arrangement copying was measured on Basic in 12.2 on
2026-11-11: no crash, PAD's track automation survived deleting the copied clip. This does not
qualify Arrangement-to-Arrangement duplication, split, move or take-lane writes; those stay
disabled. Cue adds and deletes run as a bounded operation (seek,
observe the playhead, toggle on a later tick, observe the cue at the exact time) because
``current_song_time`` applies late and ``set_or_delete_cue`` acts at the playhead.
"""

import re

from .core import Invalid
from .dom_clips import (
    MAX_NEW_LENGTH,
    apply_fields,
    audio_file,
    clip_row,
    note_specs,
    validate_fields,
)
from .dom_common import (
    BATCH_LIMIT,
    DISABLED,
    READ,
    SUPPORTED,
    UNVERIFIED,
    WRITE,
    Refused,
    _index,
    _number,
    _same,
    flag,
    has_arrangement_clips,
    owner_node,
    position_of,
    require,
    run_writes,
    two_pass,
)

CAPABILITIES = {
    "arrangement.create_clip": (SUPPORTED, "P-08: Track.create_midi_clip/create_audio_clip"),
    "arrangement.split": (DISABLED, "crash-prone on Live 12.2 (P-19)"),
    "arrangement.move": (DISABLED, "duplicate + delete is crash-prone on Live 12.2 (P-19)"),
    "cue.edit": (UNVERIFIED, "asynchronous seek/observe/toggle; P-16 unrun"),
}

CLIP_ROWS = 256
SCAN_TRACKS = 256  # track rows per whole-Set read page (continue with cursor)
# generation . track count . track . rows of that track already read . fingerprint of its rows
_CURSOR = re.compile(r"(\d{1,12})\.(\d{1,5})\.(\d{1,5})\.(\d{1,7})\.([0-9a-f]{12}|-)")
CUE_ACTIONS = 8  # adds + deletes per call (one bounded operation)
EPS = 1e-6
MAX_TIME = 16384.0
_CUE = {"op": None}  # the pending cue operation id (one at a time)


def _sorted_clips(parent):
    return sorted(parent.arrangement_clips, key=lambda c: c.start_time)


def _in_range(clip, span):
    return span is None or (clip.end_time > span[0] and clip.start_time < span[1])


def _track_rows(track, include, span):
    """A track's in-range clip rows in reading order: its own clips, then each take lane's.
    Returns ``(rows, lane_names)``; a row is ``(lane index or None, clip index, clip)``."""
    rows, lanes = [], []
    if "clips" in include:
        rows += [(None, i, c) for i, c in enumerate(_sorted_clips(track)) if _in_range(c, span)]
    if "take_lanes" in include:
        for k, lane in enumerate(list(getattr(track, "take_lanes", None) or ())):
            lanes.append(lane.name)
            rows += [(k, i, c) for i, c in enumerate(_sorted_clips(lane)) if _in_range(c, span)]
    return rows, lanes


def _fingerprint(rows):
    """Identifies a track's rows between pages: a continuation refuses when it changed."""
    # hash() of numbers is not salted, and a cursor only lives as long as this Live process
    key = tuple((k, round(c.start_time, 6), round(c.end_time, 6)) for k, _i, c in rows)
    return format(hash((len(key), key)) & 0xFFFFFFFFFFFF, "012x")


def _cursor(ctx, count, track, skip, rows):
    fp = _fingerprint(rows) if skip else "-"
    return f"{ctx.safety.generation}.{count}.{track}.{skip}.{fp}"


def _read_cursor(ctx, value, count):
    """``(track, skip, fingerprint)`` from a cursor this reader issued for the current Set."""
    if not isinstance(value, str) or len(value) > 64:
        raise Invalid("'cursor' must be the cursor string of a previous reply")
    match = _CURSOR.fullmatch(value)
    if match is None:
        raise Invalid("'cursor' must be the cursor string of a previous reply")
    gen, was, track, skip, fp = match.groups()
    if int(gen) != ctx.safety.generation or int(was) != count or int(track) >= count:
        raise Refused("stale_cursor", "the Set changed since that page; read again from the start")
    return int(track), int(skip), fp


def _emit(sel, track, picked, include, lanes):
    row = {"track": sel, "name": track.name}
    if "clips" in include:
        row["clips"] = [{"arrangement": i, **clip_row(c)} for k, i, c in picked if k is None]
    if "take_lanes" in include:
        row["take_lanes"] = [
            {
                "take_lane": k,
                "name": name,
                "clips": [{"arrangement": i, **clip_row(c)} for kk, i, c in picked if kk == k],
            }
            for k, name in enumerate(lanes)
        ]
    return row


def get_arrangement(ctx, p):
    song = ctx.song
    include = p.get("include") or ["clips", "cues"]
    if not isinstance(include, list) or set(include) - {"clips", "cues", "take_lanes"}:
        raise Invalid("'include' must list 'clips', 'cues' and/or 'take_lanes'")
    span = p.get("range")
    if span is not None:
        if not isinstance(span, list) or len(span) != 2:
            raise Invalid("'range' must be [start, end] in beats")
        span = (float(_number(span[0], "range[0]", 0)), float(_number(span[1], "range[1]", 0)))
    out = {
        "song_length": song.song_length,
        "loop": [song.loop_start, song.loop_length],
        "current_song_time": song.current_song_time,
    }
    if "cues" in include:
        cues = sorted(song.cue_points, key=lambda c: c.time)
        out["cues"] = [{"cue": i, "time": c.time, "name": c.name} for i, c in enumerate(cues)]
    # Explicit `tracks`: at most BATCH_LIMIT selectors, CLIP_ROWS rows (``truncated`` when cut).
    # Omitted: a whole-Set read in pages of CLIP_ROWS rows and SCAN_TRACKS track rows; a page
    # that stops early returns `cursor`, and calling again with it continues exactly there, even
    # inside one track (that row then says ``partial``). Never a row lost or repeated: a cursor
    # is refused when the Set, its track count or the cut track's clips changed in between.
    sels, cursor = p.get("tracks"), p.get("cursor")
    scan = sels is None
    count = len(song.tracks)
    start_at, skip, fp = 0, 0, "-"
    if scan:
        if cursor is not None:
            start_at, skip, fp = _read_cursor(ctx, cursor, count)
        sels = list(range(start_at, min(count, start_at + SCAN_TRACKS)))
    elif cursor is not None:
        raise Invalid("'cursor' continues a whole-Set read; do not combine it with 'tracks'")
    if not isinstance(sels, list) or (not scan and len(sels) > BATCH_LIMIT):
        raise Invalid(f"'tracks' must be a list of at most {BATCH_LIMIT} track selectors")
    if not ("clips" in include or "take_lanes" in include):
        return out
    rows, budget, truncated, nxt = [], CLIP_ROWS, False, None
    for n, sel in enumerate(sels):
        kind, track, _snap = owner_node(song, sel)
        if kind != "track":
            continue  # return/master tracks have no arrangement clips
        if not has_arrangement_clips(track):
            rows.append({"track": sel, "name": track.name, "group": True})  # clips on members
            continue
        items, lanes = _track_rows(track, include, span)
        done = skip if scan and n == 0 else 0
        if done and _fingerprint(items) != fp:
            raise Refused(
                "stale_cursor",
                f"track {sel} changed since that page; read again from the start",
            )
        left = items[done:]
        if scan and budget <= 0 and left:
            nxt = _cursor(ctx, count, sel, done, items)  # this track's rest: next page
            break
        picked = left[:budget]
        budget -= len(picked)
        row = _emit(sel, track, picked, include, lanes)
        if len(picked) < len(left):
            truncated = True
            if scan:
                row["partial"] = True
                rows.append(row)
                nxt = _cursor(ctx, count, sel, done + len(picked), items)
                break
        rows.append(row)
    else:
        if scan and sels and sels[-1] + 1 < count:
            nxt = _cursor(ctx, count, sels[-1] + 1, 0, ())
    out["tracks"] = rows
    out["truncated"] = truncated
    if nxt is not None:
        out["cursor"] = nxt
    return out


def _overlaps(parent, start, end):
    if not has_arrangement_clips(parent):
        raise Invalid("a group track cannot hold arrangement clips; use a member track")
    return [c for c in parent.arrangement_clips if c.start_time < end and c.end_time > start]


def create_arrangement_clips(ctx, p, t):
    """New arrangement clips on regular tracks, never over an existing clip."""
    items, resolved = p.get("targets"), t["targets"]
    planned = {}  # id(track) -> [(start, end)] reserved by earlier items

    def validate(i, item):
        where = f"targets[{i}]"
        track = resolved[i].obj
        if resolved[i].path[-1][0] != "track":
            raise Invalid(f"{where}: arrangement clips go on regular tracks")
        kind = item.get("kind", "midi")
        if kind == "from_session":
            require(ctx, "arrangement.from_session")
        if item.get("take_lane") is not None:
            require(ctx, "arrangement.take_lanes")
        start = float(_number(item.get("start"), f"{where}.start", 0, MAX_TIME))
        reserved = planned.setdefault(id(track), [])
        prepared = {"track": track, "kind": kind, "start": start, "notes": ()}
        if kind == "midi":
            require(ctx, "arrangement.create_clip", ((track, "create_midi_clip"),))
            if not track.has_midi_input:
                raise Invalid(f"{where}: a MIDI clip needs a MIDI track")
            length = float(
                _number(item.get("length", 4.0), f"{where}.length", 0, MAX_NEW_LENGTH, True)
            )
            end = start + length
            prepared["length"] = length
            if item.get("notes"):
                prepared["notes"] = note_specs(item.get("notes"), f"{where}.notes")
        elif kind == "audio":
            require(ctx, "arrangement.create_clip", ((track, "create_audio_clip"),))
            if track.has_midi_input:
                raise Invalid(f"{where}: an audio clip needs an audio track (P-08)")
            prepared["file"] = audio_file(item.get("file"), where)
            end = float("inf")  # length is known only after creation: place after every clip
        elif kind == "from_session":
            require(ctx, "arrangement.from_session", ((track, "duplicate_clip_to_arrangement"),))
            scene = _index(item.get("scene"), f"{where}.scene", len(track.clip_slots))
            slot = track.clip_slots[scene]
            if not slot.has_clip:
                raise Invalid(f"{where}: source Session slot is empty")
            source = slot.clip
            length = float(source.length)
            if length <= 0 or start + length > MAX_TIME:
                raise Invalid(f"{where}: source length is outside the timeline bounds")
            prepared["source"] = source
            prepared["length"] = length
            end = start + length
        else:
            raise Invalid(f"{where}: 'kind' must be 'midi', 'audio' or 'from_session'")
        overlaps = _overlaps(track, start, end)
        prepared["replace"] = []
        replace = flag(item, "replace", where)  # the gate's DELETING reads it the same way
        if replace:  # the write gate required the delete permission
            if kind != "from_session":
                raise Invalid(f"{where}: replace is only supported for from_session")
            require(ctx, "arrangement.delete_clip", ((track, "delete_clip"),))
            if any(c.start_time < start or c.end_time > end for c in overlaps):
                raise Invalid(f"{where}: replace refuses clips outside the destination")
            prepared["replace"] = overlaps
        collision = any(s < end and e > start for s, e in reserved)
        if (overlaps and not replace) or collision:
            raise Invalid(
                f"{where}: the range overlaps an existing clip (nothing is overwritten"
                + ("; audio clips go after the track's last clip)" if kind == "audio" else ")")
            )
        reserved.append((start, end))
        name = item.get("name")
        prepared["fields"] = validate_fields(_Kind(kind), {"name": name}, where) if name else []
        return prepared

    def write(e):
        track = e["track"]
        for old in e["replace"]:
            track.delete_clip(old)
        before = list(track.arrangement_clips)
        if e["kind"] == "midi":
            track.create_midi_clip(e["start"], e["length"])
        elif e["kind"] == "from_session":
            track.duplicate_clip_to_arrangement(e["source"], e["start"])
        else:
            track.create_audio_clip(e["file"], e["start"])
        new = [c for c in track.arrangement_clips if not any(_same(c, b) for b in before)]
        if len(new) != 1:
            raise RuntimeError(f"expected 1 new arrangement clip, found {len(new)}")
        clip = new[0]
        if e["kind"] == "from_session" and (
            abs(clip.start_time - e["start"]) > EPS
            or abs(clip.end_time - (e["start"] + e["length"])) > EPS
        ):
            raise RuntimeError("copied clip has unexpected bounds; inspect before retrying")
        apply_fields(clip, e["fields"])
        ids = clip.add_new_notes(e["notes"]) if e["notes"] else ()
        row = {
            "track": position_of(ctx.song.tracks, track),
            "arrangement": position_of(_sorted_clips(track), clip),
            **clip_row(clip),
        }
        if e["notes"]:
            row["note_ids"] = list(ids or ())
        return row

    return two_pass(items, validate, write)


class _Kind:
    def __init__(self, kind):
        self.is_audio_clip = kind == "audio"


def edit_arrangement_clips(ctx, p, t):
    """Field edits on arrangement clips (markers/loop widen-then-narrow, name, colour, mute and
    the audio fields). move_to/split_at/take-lane edits are disabled on 12.2; delete goes
    through live_delete."""
    items, resolved = p.get("targets"), t["targets"]

    def validate(i, item):
        where = f"targets[{i}]"
        if resolved[i].path[-1][0] != "arr_clip":
            raise Invalid(f"{where}: must be an arrangement clip reference")
        if item.get("move_to") is not None:
            require(ctx, "arrangement.move")
        if item.get("split_at") is not None:
            require(ctx, "arrangement.split")
        if any(n[0] == "take_lane" for n in resolved[i].path):
            require(ctx, "arrangement.take_lanes")
        clip = resolved[i].obj
        writes = validate_fields(clip, item, where)
        if not writes:
            raise Invalid(f"{where}: nothing to set")
        return clip, writes

    def write(e):
        clip, writes = e
        apply_fields(clip, writes)
        return clip_row(clip, detail=True)

    return two_pass(items, validate, write)


# ---- cue points ---------------------------------------------------------------------------------


def cue_selected(song):
    """``Song.is_cue_point_selected`` is a method in the 12.2 API (tolerate a property)."""
    value = song.is_cue_point_selected
    return bool(value() if callable(value) else value)


def _cue_at(song, time_):
    for c in song.cue_points:
        if abs(c.time - time_) <= EPS:
            return c
    return None


def _cue_index(song, cue):
    return position_of(sorted(song.cue_points, key=lambda c: c.time), cue)


def _cue_task(ctx, queue, previous, params):
    """The tick-driven cue protocol. ``queue``: ``[("add", time, name) | ("delete", cue, time)]``.
    Returns None while pending, then a result dict. The write policy (read_only, permissions for
    ``params``) is read again right before every step that writes: a seek, a toggle, and the
    rename of a cue just added. When it now refuses, the task stops there, keeping the earlier
    results; a toggle already made is still observed (it cannot be called back) but its new cue
    is not renamed. Every ending sends a moved playhead back to where it was and observes it
    there (cleanup to the prior state, never gated); ``playhead`` says where it ended.
    ``status``: ``complete``; ``partial`` (stopped after a cue change, or the playhead did not
    return); ``not_applied`` (stopped with nothing changed)."""
    st = {"i": 0, "phase": "seek", "before": None, "waits": 0, "done": [], "moved": False}

    def refusal():
        try:
            ctx.safety.check_policy("set_cue_points", params)
        except Refused as exc:
            return f"refused:{exc.code}: {exc.message}"
        return None

    def end(error=None):
        """Begin the ending: a moved playhead is sent back, then ``settle`` observes it."""
        st["end"] = {"status": "complete", "results": st["done"]}
        if error is not None:
            st["end"].update(stopped_at=st["i"], error=error)
        if st["moved"]:
            ctx.song.current_song_time = previous
        st["phase"], st["waits"] = "restore", 0
        return settle()

    def settle():
        out = st["end"]
        restored = True
        if st["moved"]:
            at = ctx.song.current_song_time
            restored = abs(at - previous) <= EPS
            if not restored and st["waits"] < 20:
                st["waits"] += 1
                return None
            out["playhead"] = {"moved": True, "restored": restored, "at": at, "was": previous}
        else:
            out["playhead"] = {"moved": False, "at": previous}
        if "error" in out:
            out["status"] = "partial" if st["done"] or not restored else "not_applied"
        elif not restored:
            out["status"] = "partial"
            out["error"] = f"the playhead stayed at {out['playhead']['at']}, not {previous}"
        return out

    def advance(row):
        st["done"].append(row)
        st["i"] += 1
        st["phase"], st["waits"] = "seek", 0

    def step():
        if st["phase"] == "restore":
            return settle()
        try:
            return advance_one()
        except Exception:
            if st["moved"]:  # best effort before the task turns unknown
                try:
                    ctx.song.current_song_time = previous
                except Exception:  # noqa: BLE001
                    pass
            raise

    def advance_one():
        song = ctx.song
        if st["i"] >= len(queue):
            return end()
        if song.is_playing:
            raise RuntimeError("the transport started during a cue edit")
        action, a, b = queue[st["i"]]
        time_ = a if action == "add" else b
        if st["phase"] in ("seek", "observe_seek"):  # both may write: recheck first
            error = refusal()
            if error is not None:
                return end(error)
        if st["phase"] == "seek":
            if action == "add" and _cue_at(song, time_) is not None:
                cue = _cue_at(song, time_)
                if b:
                    cue.name = b
                return advance({"action": "add", "time": cue.time, "reused": True})
            if action == "delete" and not any(_same(c, a) for c in song.cue_points):
                return advance({"action": "delete", "time": time_, "already_gone": True})
            st["moved"] = True
            song.current_song_time = time_
            st["phase"] = "observe_seek"
            return None
        if st["phase"] == "observe_seek":
            if abs(song.current_song_time - time_) > EPS:
                st["waits"] += 1
                if st["waits"] > 20:
                    return end(
                        f"the playhead stayed at {song.current_song_time}, not {time_} (past "
                        "the song end?); nothing toggled"
                    )
                return None
            selected = cue_selected(song)
            if action == "add" and selected:  # a cue sits here: reuse it, never toggle it away
                cue = _cue_at(song, time_)
                if cue is not None and b:
                    cue.name = b
                return advance({"action": "add", "time": time_, "reused": True})
            if action == "delete" and not selected:
                raise RuntimeError("the cue is not selected at its own time")
            st["before"] = list(song.cue_points)
            song.set_or_delete_cue()
            st["phase"], st["waits"] = "observe_toggle", 0
            return None
        now = list(song.cue_points)  # observe_toggle: the toggle is made; observe it to its end
        if action == "add":
            new = [c for c in now if not any(_same(c, o) for o in st["before"])]
            if not new:
                return None
            if len(new) != 1 or abs(new[0].time - time_) > EPS:
                raise RuntimeError(f"unexpected cue change: {[c.time for c in new]}")
            row = {"action": "add", "time": new[0].time, "cue": _cue_index(song, new[0])}
            if b:
                error = refusal()  # the rename is a write of its own
                if error is not None:
                    advance({**row, "renamed": False})
                    return end(error)
                new[0].name = b
            return advance(row)
        if any(_same(c, a) for c in now):
            return None
        return advance({"action": "delete", "time": time_})

    return step


def set_cue_points(ctx, p, t):
    """``cues``: ``[{cue: ref, action: rename|jump|delete, name?}]``; ``add``: ``[{time,
    name?}]`` (needs ``generation``). Renames and the jump run now; adds and deletes start one
    bounded operation (poll it with live_get_operation)."""
    song = ctx.song
    items, resolved = p.get("cues") or [], t.get("cues") or []
    adds = p.get("add") or []
    if not isinstance(adds, list) or len(adds) > CUE_ACTIONS:
        raise Invalid(f"'add' must be a list of at most {CUE_ACTIONS} cue points")
    if not items and not adds:
        raise Invalid("nothing to do: give 'cues' and/or 'add'")
    if adds and p.get("generation") != ctx.safety.generation:
        raise Refused("stale_generation", "expected 'generation' does not match the Set")
    renames, deletes, jump = [], [], None
    for i, item in enumerate(items):
        where = f"cues[{i}]"
        action, cue = item.get("action"), resolved[i].obj
        if action == "rename":
            name = item.get("name")
            if not isinstance(name, str) or len(name) > 256:
                raise Invalid(f"{where}: 'name' must be a string of at most 256 characters")
            renames.append((cue, name))
        elif action == "delete":
            deletes.append(("delete", cue, cue.time))
        elif action == "jump":
            if jump is not None:
                raise Invalid("only one 'jump' per call")
            jump = cue
        else:
            raise Invalid(f"{where}: 'action' must be rename, jump or delete")
    queue = list(deletes)
    seen = {round(d[2], 6) for d in deletes}
    for i, add in enumerate(adds):
        if not isinstance(add, dict):
            raise Invalid(f"add[{i}] must be an object")
        time_ = float(_number(add.get("time"), f"add[{i}].time", 0, MAX_TIME))
        name = add.get("name")
        if name is not None and (not isinstance(name, str) or len(name) > 256):
            raise Invalid(f"add[{i}]: 'name' must be a string of at most 256 characters")
        if round(time_, 6) in seen:
            raise Invalid(f"add[{i}]: time {time_} is already in this call")
        seen.add(round(time_, 6))
        queue.append(("add", time_, name))
    if len(queue) > CUE_ACTIONS:
        raise Invalid(f"at most {CUE_ACTIONS} adds + deletes per call")
    if queue:
        require(ctx, "cue.edit", ((song, "set_or_delete_cue"), (song, "is_cue_point_selected")))
        if jump is not None:
            raise Invalid(
                "'jump' cannot share a call with adds or deletes (both move the playhead)"
            )
        if song.is_playing:
            raise Refused("transport_playing", "stop the transport before cue adds or deletes")
        pending = _CUE["op"]
        if pending is not None:
            try:
                state = ctx.operations.get(pending)["state"]
            except Refused:
                state = None
            if state == "pending":
                raise Refused("operation_pending", f"cue operation {pending} is still pending")

    ops = [("rename", (c, n)) for c, n in renames]
    if jump is not None:
        ops.append(("jump", jump))
    if queue:
        ops.append(("operation", queue))

    def write(op):
        label, arg = op
        if label == "rename":
            arg[0].name = arg[1]
            return {"action": "rename", "time": arg[0].time, "name": arg[0].name}
        if label == "jump":
            arg.jump()
            return {"action": "jump", "time": arg.time}
        step = _cue_task(ctx, arg, song.current_song_time, p)
        snap = ctx.operations.start_task("cue_points", step, timeout=10.0)
        _CUE["op"] = snap["operation"]
        return snap

    return run_writes(ops, write)


METHODS = {
    "get_arrangement": (get_arrangement, READ, None),
    "create_arrangement_clips": (create_arrangement_clips, WRITE, (("targets", "ref", "track"),)),
    "edit_arrangement_clips": (edit_arrangement_clips, WRITE, (("targets", "ref", "arr_clip"),)),
    "set_cue_points": (set_cue_points, WRITE, (("cues", "cue", "cue"),)),
}
