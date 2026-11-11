"""Arrangement domain: reads, direct clip creation (P-08), clip field edits, cue points.

Live 12.2 facts: ``Track.create_midi_clip(start, length)`` and ``Track.create_audio_clip(path,
start)`` work (P-08). Split, move (duplicate + delete), ``duplicate_clip_to_arrangement`` and
take-lane creation/edits are crash-prone on 12.2 (P-19): they refuse with ``unsupported`` before
any native call; take-lane reads stay. Cue adds and deletes run as a bounded operation (seek,
observe the playhead, toggle on a later tick, observe the cue at the exact time) because
``current_song_time`` applies late and ``set_or_delete_cue`` acts at the playhead.
"""

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
    _number,
    _same,
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
CUE_ACTIONS = 8  # adds + deletes per call (one bounded operation)
EPS = 1e-6
MAX_TIME = 16384.0
_CUE = {"op": None}  # the pending cue operation id (one at a time)


def _sorted_clips(parent):
    return sorted(parent.arrangement_clips, key=lambda c: c.start_time)


def _in_range(clip, span):
    return span is None or (clip.end_time > span[0] and clip.start_time < span[1])


def get_arrangement(ctx, p):
    song = ctx.song
    include = p.get("include") or ["clips", "cues", "take_lanes"]
    if not isinstance(include, list) or set(include) - {"clips", "cues", "take_lanes"}:
        raise ValueError("'include' must list 'clips', 'cues' and/or 'take_lanes'")
    span = p.get("range")
    if span is not None:
        if not isinstance(span, list) or len(span) != 2:
            raise ValueError("'range' must be [start, end] in beats")
        span = (float(_number(span[0], "range[0]", 0)), float(_number(span[1], "range[1]", 0)))
    out = {
        "song_length": song.song_length,
        "loop": [song.loop_start, song.loop_length],
        "current_song_time": song.current_song_time,
    }
    if "cues" in include:
        cues = sorted(song.cue_points, key=lambda c: c.time)
        out["cues"] = [{"cue": i, "time": c.time, "name": c.name} for i, c in enumerate(cues)]
    sels = p.get("tracks")
    if sels is None:
        sels = list(range(len(song.tracks)))
    if not isinstance(sels, list) or len(sels) > BATCH_LIMIT:
        raise ValueError(f"'tracks' must be a list of at most {BATCH_LIMIT} track selectors")
    rows, budget, truncated = [], CLIP_ROWS, False

    def clips_of(parent):
        nonlocal budget, truncated
        found = []
        for i, c in enumerate(_sorted_clips(parent)):
            if not _in_range(c, span):
                continue
            if budget <= 0:
                truncated = True
                break
            budget -= 1
            found.append({"arrangement": i, **clip_row(c)})
        return found

    if "clips" in include or "take_lanes" in include:
        for sel in sels:
            kind, track, _snap = owner_node(song, sel)
            if kind != "track":
                continue  # return/master tracks have no arrangement clips
            row = {"track": sel, "name": track.name}
            if "clips" in include:
                row["clips"] = clips_of(track)
            if "take_lanes" in include:
                lanes = list(getattr(track, "take_lanes", None) or ())
                row["take_lanes"] = [
                    {"take_lane": k, "name": lane.name, "clips": clips_of(lane)}
                    for k, lane in enumerate(lanes)
                ]
            rows.append(row)
        out["tracks"] = rows
        out["truncated"] = truncated
    return out


# ---- clips --------------------------------------------------------------------------------------


def _overlaps(parent, start, end):
    return [c for c in parent.arrangement_clips if c.start_time < end and c.end_time > start]


def create_arrangement_clips(ctx, p, t):
    """New arrangement clips on regular tracks, never over an existing clip."""
    items, resolved = p.get("targets"), t["targets"]
    planned = {}  # id(track) -> [(start, end)] reserved by earlier items

    def validate(i, item):
        where = f"targets[{i}]"
        track = resolved[i].obj
        if resolved[i].path[-1][0] != "track":
            raise ValueError(f"{where}: arrangement clips go on regular tracks")
        kind = item.get("kind", "midi")
        if kind == "from_session":
            require(ctx, "arrangement.duplicate")
        if item.get("take_lane") is not None:
            require(ctx, "arrangement.take_lanes")
        start = float(_number(item.get("start"), f"{where}.start", 0, MAX_TIME))
        reserved = planned.setdefault(id(track), [])
        prepared = {"track": track, "kind": kind, "start": start, "notes": ()}
        if kind == "midi":
            require(ctx, "arrangement.create_clip", ((track, "create_midi_clip"),))
            if not track.has_midi_input:
                raise ValueError(f"{where}: a MIDI clip needs a MIDI track")
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
                raise ValueError(f"{where}: an audio clip needs an audio track (P-08)")
            prepared["file"] = audio_file(item.get("file"), where)
            end = float("inf")  # length is known only after creation: place after every clip
        else:
            raise ValueError(f"{where}: 'kind' must be 'midi', 'audio' or 'from_session'")
        if _overlaps(track, start, end) or any(s < end and e > start for s, e in reserved):
            raise ValueError(
                f"{where}: the range overlaps an existing clip (nothing is overwritten"
                + ("; audio clips go after the track's last clip)" if kind == "audio" else ")")
            )
        reserved.append((start, end))
        name = item.get("name")
        prepared["fields"] = validate_fields(_Kind(kind), {"name": name}, where) if name else []
        return prepared

    def write(e):
        track = e["track"]
        before = list(track.arrangement_clips)
        if e["kind"] == "midi":
            track.create_midi_clip(e["start"], e["length"])
        else:
            track.create_audio_clip(e["file"], e["start"])
        new = [c for c in track.arrangement_clips if not any(_same(c, b) for b in before)]
        if len(new) != 1:
            raise RuntimeError(f"expected 1 new arrangement clip, found {len(new)}")
        clip = new[0]
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
            raise ValueError(f"{where}: must be an arrangement clip reference")
        if item.get("move_to") is not None:
            require(ctx, "arrangement.move")
        if item.get("split_at") is not None:
            require(ctx, "arrangement.split")
        if any(n[0] == "take_lane" for n in resolved[i].path):
            require(ctx, "arrangement.take_lanes")
        clip = resolved[i].obj
        writes = validate_fields(clip, item, where)
        if not writes:
            raise ValueError(f"{where}: nothing to set")
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


def _cue_task(ctx, queue, previous):
    """The tick-driven cue protocol. ``queue``: ``[("add", time, name) | ("delete", cue, time)]``.
    Returns None while pending, then a result dict."""
    st = {"i": 0, "phase": "seek", "before": None, "waits": 0, "done": []}

    def finish(extra=None):
        ctx.song.current_song_time = previous
        out = {"status": "complete", "results": st["done"]}
        if extra:
            out.update(extra)
        return out

    def advance(row):
        st["done"].append(row)
        st["i"] += 1
        st["phase"], st["waits"] = "seek", 0

    def step():
        song = ctx.song
        if st["i"] >= len(queue):
            return finish()
        if song.is_playing:
            raise RuntimeError("the transport started during a cue edit")
        action, a, b = queue[st["i"]]
        time_ = a if action == "add" else b
        if st["phase"] == "seek":
            if action == "add" and _cue_at(song, time_) is not None:
                cue = _cue_at(song, time_)
                if b:
                    cue.name = b
                return advance({"action": "add", "time": cue.time, "reused": True})
            if action == "delete" and not any(_same(c, a) for c in song.cue_points):
                return advance({"action": "delete", "time": time_, "already_gone": True})
            song.current_song_time = time_
            st["phase"] = "observe_seek"
            return None
        if st["phase"] == "observe_seek":
            if abs(song.current_song_time - time_) > EPS:
                st["waits"] += 1
                if st["waits"] > 20:
                    return finish(
                        {
                            "status": "partial",
                            "stopped_at": st["i"],
                            "error": f"the playhead stayed at {song.current_song_time}, not "
                            f"{time_} (past the song end?); nothing toggled",
                        }
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
        now = list(song.cue_points)
        if action == "add":
            new = [c for c in now if not any(_same(c, o) for o in st["before"])]
            if not new:
                return None
            if len(new) != 1 or abs(new[0].time - time_) > EPS:
                raise RuntimeError(f"unexpected cue change: {[c.time for c in new]}")
            if b:
                new[0].name = b
            return advance({"action": "add", "time": new[0].time, "cue": _cue_index(song, new[0])})
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
        raise ValueError(f"'add' must be a list of at most {CUE_ACTIONS} cue points")
    if not items and not adds:
        raise ValueError("nothing to do: give 'cues' and/or 'add'")
    if adds and p.get("generation") != ctx.safety.generation:
        raise Refused("stale_generation", "expected 'generation' does not match the Set")
    renames, deletes, jump = [], [], None
    for i, item in enumerate(items):
        where = f"cues[{i}]"
        action, cue = item.get("action"), resolved[i].obj
        if action == "rename":
            name = item.get("name")
            if not isinstance(name, str) or len(name) > 256:
                raise ValueError(f"{where}: 'name' must be a string of at most 256 characters")
            renames.append((cue, name))
        elif action == "delete":
            deletes.append(("delete", cue, cue.time))
        elif action == "jump":
            if jump is not None:
                raise ValueError("only one 'jump' per call")
            jump = cue
        else:
            raise ValueError(f"{where}: 'action' must be rename, jump or delete")
    queue = list(deletes)
    seen = {round(d[2], 6) for d in deletes}
    for i, add in enumerate(adds):
        if not isinstance(add, dict):
            raise ValueError(f"add[{i}] must be an object")
        time_ = float(_number(add.get("time"), f"add[{i}].time", 0, MAX_TIME))
        name = add.get("name")
        if name is not None and (not isinstance(name, str) or len(name) > 256):
            raise ValueError(f"add[{i}]: 'name' must be a string of at most 256 characters")
        if round(time_, 6) in seen:
            raise ValueError(f"add[{i}]: time {time_} is already in this call")
        seen.add(round(time_, 6))
        queue.append(("add", time_, name))
    if len(queue) > CUE_ACTIONS:
        raise ValueError(f"at most {CUE_ACTIONS} adds + deletes per call")
    if queue:
        require(ctx, "cue.edit", ((song, "set_or_delete_cue"), (song, "is_cue_point_selected")))
        if jump is not None:
            raise ValueError(
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
        step = _cue_task(ctx, arg, song.current_song_time)
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
