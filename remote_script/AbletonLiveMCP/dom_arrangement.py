"""Arrangement domain: reads, direct clip creation (P-08), clip field edits, cue points.

Live 12.2 facts: ``Track.create_midi_clip(start, length)`` and ``Track.create_audio_clip(path,
start)`` work (P-08). Session-to-Arrangement copying was measured on Basic in 12.2 on
2026-11-11: no crash, PAD's track automation survived deleting the copied clip. This does not
qualify Arrangement-to-Arrangement duplication, split, move or take-lane writes; those stay
disabled. Cue adds and deletes run as a bounded operation (seek,
observe the playhead, toggle on a later tick, observe the cue where Live puts it) because
``current_song_time`` applies late and ``set_or_delete_cue`` acts at the playhead.
"""

import math

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
    confirmed_clips,
    flag,
    has_arrangement_clips,
    owner_node,
    position_of,
    require,
    run_writes,
    same_items,
    two_pass,
)

CAPABILITIES = {
    "arrangement.create_clip": (SUPPORTED, "P-08: Track.create_midi_clip/create_audio_clip"),
    "arrangement.split": (DISABLED, "crash-prone on Live 12.2 (P-19)"),
    "arrangement.move": (DISABLED, "duplicate + delete is crash-prone on Live 12.2 (P-19)"),
    "cue.edit": (UNVERIFIED, "asynchronous seek/observe/toggle; P-16 unrun"),
}

CLIP_ROWS = 256
# Supported scope: arrangement clips per track and per take lane. Live returns a whole collection
# on every access, so this bounds the native work of each read page; past it a read refuses.
CLIP_SCOPE = 256
SCAN_TRACKS = 256  # track rows per whole-Set read page (continue with cursor)
CUE_ACTIONS = 8  # adds + deletes per call (one bounded operation)
EPS = 1e-6
MAX_TIME = 16384.0
_CUE = {"op": None}  # the pending cue operation id (one at a time)


def _sorted_clips(parent):
    return sorted(parent.arrangement_clips, key=lambda c: c.start_time)


def _in_range(clip, span):
    return span is None or (clip.end_time > span[0] and clip.start_time < span[1])


def _scoped_clips(parent, where):
    """``_sorted_clips`` for a read, refused past ``CLIP_SCOPE`` (the supported scope)."""
    clips = _sorted_clips(parent)
    if len(clips) > CLIP_SCOPE:
        raise Refused(
            "beyond_scope",
            f"{where} holds {len(clips)} arrangement clips; reads support up to {CLIP_SCOPE}",
        )
    return clips


def _track_rows(track, include, span, sel=None):
    """A track's in-range clip rows in reading order: its own clips, then each take lane's.
    Returns ``(rows, lane_names)``; a row is ``(lane index or None, clip index, clip)``."""
    rows, lanes, where = [], [], f"track {sel}"
    if "clips" in include:
        clips = _scoped_clips(track, where)
        rows += [(None, i, c) for i, c in enumerate(clips) if _in_range(c, span)]
    if "take_lanes" in include:
        for k, lane in enumerate(list(getattr(track, "take_lanes", None) or ())):
            lanes.append(lane.name)
            clips = _scoped_clips(lane, f"{where} take lane {k}")
            rows += [(k, i, c) for i, c in enumerate(clips) if _in_range(c, span)]
    return rows, lanes


def _row_ids(rows):
    """A track's rows by lane and clip identity: what a continuation inside it must still see."""
    return tuple((k, c) for k, _i, c in rows)


def _cursor(ctx, tracks, args, track, skip, rows):
    """Keep the continuation here, bound to the Set, its tracks in order (by identity), the
    read's own arguments and, inside a track, that track's rows; the client gets a token."""
    state = {
        "generation": ctx.safety.generation,
        "tracks": tuple(tracks),
        "args": args,
        "track": track,
        "skip": skip,
        "rows": _row_ids(rows) if skip else (),
    }
    return ctx.operations.page_cursors.put("arrangement", state)


def _read_cursor(ctx, value, tracks, args):
    """``(track, skip, rows)`` of a cursor this reader issued, refused unless the Set, its
    tracks (same objects, same order) and the arguments are unchanged. Single use."""
    if not isinstance(value, str) or len(value) > 64:
        raise Invalid("'cursor' must be the cursor string of a previous reply")
    state = ctx.operations.page_cursors.take(value, "arrangement")  # unknown_cursor otherwise
    if state["generation"] != ctx.safety.generation or not same_items(tracks, state["tracks"]):
        raise Refused(
            "stale_cursor",
            "the Set or its track list changed since that page; read again from the start",
        )
    if state["args"] != args:
        raise Refused(
            "cursor_mismatch",
            "that cursor continues a read with other 'include'/'range'; read again from the start",
        )
    return state["track"], state["skip"], state["rows"]


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
    # is refused when the Set, its tracks (identity and order), the arguments or the cut track's
    # clips changed in between. The cursor is a token; its state never leaves the script.
    sels, cursor = p.get("tracks"), p.get("cursor")
    scan = sels is None
    tracks = list(song.tracks)
    count = len(tracks)
    args = (tuple(sorted(set(include))), span)
    start_at, skip, seen = 0, 0, ()
    if scan:
        if cursor is not None:
            start_at, skip, seen = _read_cursor(ctx, cursor, tracks, args)
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
        items, lanes = _track_rows(track, include, span, sel)
        done = skip if scan and n == 0 else 0
        now = _row_ids(items)
        if done and not (
            len(now) == len(seen)
            and all(k == kk and _same(c, cc) for (k, c), (kk, cc) in zip(now, seen, strict=False))
        ):
            raise Refused(
                "stale_cursor",
                f"track {sel} changed since that page; read again from the start",
            )
        left = items[done:]
        if scan and budget <= 0 and left:
            nxt = _cursor(ctx, tracks, args, sel, done, items)  # this track's rest: next page
            break
        picked = left[:budget]
        budget -= len(picked)
        row = _emit(sel, track, picked, include, lanes)
        if len(picked) < len(left):
            truncated = True
            if scan:
                row["partial"] = True
                rows.append(row)
                nxt = _cursor(ctx, tracks, args, sel, done + len(picked), items)
                break
        rows.append(row)
    else:
        if scan and sels and sels[-1] + 1 < count:
            nxt = _cursor(ctx, tracks, args, sels[-1] + 1, 0, ())
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
            expected = item.get("expect_replace")
            if expected is None and overlaps:
                raise Invalid(f"{where}: replace needs 'expect_replace' (the clips' references)")
            bound = confirmed_clips(ctx, expected or [], where, "expect_replace", "arr_clip")
            if len(bound) != len(overlaps) or not all(
                any(_same(c, b) for b in bound) for c in overlaps
            ):
                raise Refused(
                    "target_changed",
                    f"{where}: the clips in the destination are not the ones confirmed for "
                    "deletion; nothing was applied",
                )
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


def _bar(song):
    """Beats per bar at the Set's time signature (4/4 when unreadable)."""
    try:
        bar = 4.0 * song.signature_numerator / song.signature_denominator
    except (AttributeError, TypeError, ZeroDivisionError):
        return 4.0
    return bar if bar > 0 else 4.0


def _landings(song, time_):
    """Where a cue added at ``time_`` may appear: the time itself, or the bar line Live 12.2 puts
    it on. Measured on Basic 2026-11-12: the nearest bar of the Set's signature, an exact tie
    going to the later bar (4/4: 33 -> 32, 42 -> 44, 61.5 -> 60; 3/4: 127 -> 126, 137.5 ->
    138). Returns ``(nearest, accepted)``; at a tie both adjacent bars are accepted."""
    bar = _bar(song)
    q = time_ / bar
    nearest = math.floor(q + 0.5) * bar
    accepted = [time_, nearest]
    if abs(q - math.floor(q) - 0.5) <= EPS:
        accepted += [math.floor(q) * bar, math.ceil(q) * bar]
    return nearest, accepted


def _add_plan(song, time_):
    """Before an add's toggle: ``("reuse", cue)``, ``("refuse", text)`` or ``("toggle", None)``.

    Live 12.2 (measured 2026-11-12): ``set_or_delete_cue`` deletes a cue lying within half a
    bar of the playhead (33 deleted the cue at 32; in 3/4, 113 deleted 112 and 45.4 deleted
    44, while 101.6 left 100 and added 102), and only adds when none does. A cue at the time,
    or alone on the bar the add would land on, is reused (the documented reuse); any other cue
    that close would be deleted by the toggle, so the add refuses before it."""
    here = _cue_at(song, time_)
    if here is not None:
        return "reuse", here
    nearest, _accepted = _landings(song, time_)
    near = [c for c in song.cue_points if abs(c.time - time_) <= _bar(song) / 2 + EPS]
    if not near:
        return "toggle", None
    if len(near) == 1 and abs(near[0].time - nearest) <= EPS:
        return "reuse", near[0]
    times = sorted(c.time for c in near)
    return "refuse", (
        f"a cue at {times} lies within half a bar of {time_}; Live's toggle there would delete "
        "it, so nothing toggled"
    )


STRETCH = 32.0  # beats the song end runs past a playhead set at it (Live 12.2, measured)
STEP_LIMIT = 48  # planned playhead steps per cue operation (its seeks and the return)
CUE_TIMEOUT = 10.0  # the operation's deadline (s); the return stops RESERVE s before it
RESERVE = 1.0


def _playhead_steps(song, times):
    """Playhead steps a cue operation plans: a seek to each of ``times`` in order, then the
    return to where the playhead is now. Each move is one step, plus one per ``STRETCH`` beats
    past the song end it starts from (see ``_send_playhead``). Conservative: after a move the
    song is taken to end at the move's time or the last arrangement event, never further."""
    try:
        base = float(song.last_event_time)
    except (AttributeError, TypeError, ValueError):
        base = 0.0
    length, steps = float(song.song_length), 0
    for t in [*times, float(song.current_song_time)]:
        steps += 1 + max(0, math.ceil((t - length) / STRETCH - EPS))
        length = max(base, t)
    return steps


def _send_playhead(song, target):
    """One step of moving the stopped playhead toward ``target``; an error text or None.

    Live 12.2 (measured 2026-11-12): setting ``current_song_time`` past ``song_length`` raises
    RuntimeError, and ``song_length`` stretches to cover the playhead (about 32 beats past it).
    So a playhead parked past the arrangement content is legal where it is, but once a seek
    pulls it back the song shrinks and a direct return raises. The way back is in steps:
    each one goes as far as the song allows now, and the stretch it causes allows the next
    (measured: a playhead set at the song end at 232, 264 and 296 made it 264, 296 and 328)."""
    try:
        song.current_song_time = min(target, song.song_length)
    except RuntimeError as exc:
        return f"Live refused the playhead at {target}: {exc}"
    return None


def _cue_task(ctx, queue, previous, params):
    """The tick-driven cue protocol. ``queue``: ``[("add", time, name) | ("delete", cue, time)]``.
    Returns None while pending, then a result dict. The write policy (read_only, permissions for
    ``params``) is read again right before every step that writes: a seek, a toggle, and the
    rename of a cue just added. When it now refuses, the task stops there, keeping the earlier
    results; a toggle already made is still observed (it cannot be called back) but its new cue
    is not renamed. Every ending sends a moved playhead back to where it was and observes it
    there (cleanup to the prior state, never gated, in steps: see ``_send_playhead``);
    ``playhead`` says where it ended. A playhead that cannot return is a ``cleanup_issue``
    beside the cue results, never a task failure: the cue changes made stay reported. The return
    goes on while it makes progress, until ``RESERVE`` s before the operation's deadline; then
    the playhead's place is a ``cleanup_issue`` (the distance was planned within ``STEP_LIMIT``
    before anything moved, so this needs a stalled Live). ``ticks``: how many ticks it took.
    ``status`` (the cue changes only): ``complete``; ``partial`` (stopped after a cue change);
    ``not_applied`` (stopped with nothing changed); ``ambiguous`` (a toggle's change is not the
    expected one: another cue appeared or went, or the new cue is neither at the requested time
    nor on its bar; nothing is renamed, ``ambiguous`` lists what changed, the operation ends
    ``unknown``)."""
    st = {"i": 0, "phase": "seek", "before": None, "done": [], "moved": False, "ticks": 0}
    st["deadline"] = ctx.operations.now() + CUE_TIMEOUT - RESERVE

    def late():
        return ctx.operations.now() >= st["deadline"]

    def toward(target):
        """One tick of moving the playhead to ``target``: None when there, else ``"moving"`` or
        an error text (Live refused the step, keeps the song short of it, or time ran out)."""
        song = ctx.song
        at = song.current_song_time
        if abs(at - target) <= EPS:
            st["stuck"] = 0
            return None
        if late():
            return f"the operation's time ran out with the playhead at {at}, not {target}"
        # No progress: the furthest place the song allows is where it already is.
        stuck = abs(min(target, song.song_length) - at) <= EPS
        st["stuck"] = st.get("stuck", 0) + 1 if stuck else 0
        if st["stuck"] >= 3:  # a tick of lag is normal; three is Live's answer
            return (
                f"Live keeps the song at {song.song_length} beats, so the playhead cannot "
                f"reach {target}"
            )
        return _send_playhead(song, target) or "moving"

    def refusal():
        try:
            ctx.safety.check_policy("set_cue_points", params)
        except Refused as exc:
            return f"refused:{exc.code}: {exc.message}"
        return None

    def end(error=None):
        """Begin the ending; ``settle`` sends a moved playhead back and observes it."""
        st["end"] = {"status": "complete", "results": st["done"]}
        if "ambiguous" in st:
            st["end"]["ambiguous"] = st["ambiguous"]
        if error is not None:
            st["end"].update(stopped_at=st["i"], error=error)
        st["phase"], st["stuck"] = "restore", 0
        return settle()

    def settle():
        """One tick of the playhead's return: a step back while it is not there yet. Never
        raises: a return Live refuses, stalls or runs out of time ends the waiting."""
        out = st["end"]
        if not st["moved"]:
            out["playhead"] = {"moved": False, "at": previous}
        else:
            moving = toward(previous) if "refused" not in st else st["refused"]
            if moving == "moving":
                return None
            at = ctx.song.current_song_time
            restored = moving is None
            out["playhead"] = {"moved": True, "restored": restored, "at": at, "was": previous}
            if not restored:
                out["cleanup_issue"] = moving
        if "error" in out:
            out["status"] = "partial" if st["done"] else "not_applied"
        if "ambiguous" in out:
            out["status"] = "ambiguous"
        out["ticks"] = st["ticks"]
        return out

    def unclear(action, time_, new, gone):
        """The toggle's change is not the expected one: stop, rename nothing, say what changed."""
        st["ambiguous"] = {
            "action": action,
            "requested": time_,
            "appeared": sorted(c.time for c in new),
            "removed": sorted(t for _c, t in gone),
        }
        return end(f"the {action} at {time_} changed other cues than expected; nothing renamed")

    def reuse(cue, time_, name):
        if name:
            cue.name = name
        row = {"action": "add", "time": cue.time, "reused": True}
        if abs(cue.time - time_) > EPS:
            row["requested"] = time_
        return advance(row)

    def moved_cue(song, cue, time_):
        """The confirmed cue no longer sits alone at its confirmed time: the toggle there would
        delete another cue or add one. An error text, or None when the delete may go ahead."""
        if abs(cue.time - time_) > EPS:
            return f"the cue confirmed at {time_} moved to {cue.time}; nothing toggled"
        here = [c for c in song.cue_points if abs(c.time - time_) <= EPS]
        if len(here) != 1 or not _same(here[0], cue):
            return f"the cue at {time_} is not the confirmed one; nothing toggled"
        return None

    def advance(row):
        st["done"].append(row)
        st["i"] += 1
        st["phase"] = "seek"

    def step():
        st["ticks"] += 1
        if st["phase"] == "restore":
            return settle()
        return advance_one()

    def finalize():
        """Timeout, error or disconnect: one step of the playhead back (ungated cleanup). It
        never raises, so a refused step is reported here, not as a failed cleanup."""
        if not st["moved"]:
            return {"playhead": {"moved": False, "at": previous}}
        row = {"moved": True, "sent_back_to": previous, "observed": False}
        error = _send_playhead(ctx.song, previous)
        if error is not None:
            row["error"] = error
        return {"playhead": row}

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
            if action == "add":
                plan, arg = _add_plan(song, time_)
                if plan == "reuse":
                    return reuse(arg, time_, b)
                if plan == "refuse":
                    return end(arg)
            if action == "delete" and not any(_same(c, a) for c in song.cue_points):
                return advance({"action": "delete", "time": time_, "already_gone": True})
            changed = moved_cue(song, a, time_) if action == "delete" else None
            if changed is not None:
                return end(changed)
            st["moved"], st["stuck"] = True, 0
            error = _send_playhead(song, time_)
            if error is not None:
                return end(f"{error}; nothing toggled")
            st["phase"] = "observe_seek"
            return None
        if st["phase"] == "observe_seek":
            moving = toward(time_)  # the next step, past the content end
            if moving == "moving":
                return None
            if moving is not None:
                return end(f"{moving}; nothing toggled")
            if action == "add":  # just before the toggle: what it would do here now
                plan, arg = _add_plan(song, time_)
                if plan == "reuse":  # a cue sits here: reuse it, never toggle it away
                    return reuse(arg, time_, b)
                if plan == "refuse":
                    return end(arg)
            if action == "delete":  # just before the toggle: still the confirmed cue, here?
                selected = cue_selected(song)
                if not any(_same(c, a) for c in song.cue_points):
                    return advance({"action": "delete", "time": time_, "already_gone": True})
                changed = moved_cue(song, a, time_)
                if changed is not None:
                    return end(changed)
                if not selected:
                    raise RuntimeError("the cue is not selected at its own time")
            # Times read now: a deleted cue's handle raises when read (ArgumentError, Live 12.2).
            st["before"] = [(c, c.time) for c in song.cue_points]
            song.set_or_delete_cue()
            st["phase"] = "observe_toggle"
            return None
        now = list(song.cue_points)  # observe_toggle: the toggle is made; observe it to its end
        new = [c for c in now if not any(_same(c, o) for o, _t in st["before"])]
        gone = [(o, t) for o, t in st["before"] if not any(_same(c, o) for c in now)]
        if not new and not gone:
            return None
        if action == "add":
            _nearest, accepted = _landings(song, time_)
            if gone or len(new) != 1 or not any(abs(new[0].time - t) <= EPS for t in accepted):
                return unclear(action, time_, new, gone)
            row = {"action": "add", "time": new[0].time, "cue": _cue_index(song, new[0])}
            if abs(new[0].time - time_) > EPS:  # on its bar (289 -> 288, 290 -> 292)
                row["requested"] = time_
            if b:
                error = refusal()  # the rename is a write of its own
                if error is not None:
                    advance({**row, "renamed": False})
                    return end(error)
                new[0].name = b
            return advance(row)
        # Only live handles are compared: the one gone must be ours (``a`` is no longer here).
        if new or len(gone) != 1 or any(_same(c, a) for c in now):
            return unclear(action, time_, new, gone)
        return advance({"action": "delete", "time": time_})

    return step, finalize


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
        steps = _playhead_steps(song, [q[1] if q[0] == "add" else q[2] for q in queue])
        if steps > STEP_LIMIT:
            raise Refused(
                "beyond_scope",
                f"these cue edits need {steps} playhead steps (seeks and the return, at most "
                f"{STRETCH:g} beats past the song end each); one call supports {STEP_LIMIT}. "
                "Move the playhead nearer, or split the call",
            )
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
        step, finalize = _cue_task(ctx, arg, song.current_song_time, p)
        snap = ctx.operations.start_task("cue_points", step, timeout=CUE_TIMEOUT, finalize=finalize)
        _CUE["op"] = snap["operation"]
        return snap

    return run_writes(ops, write)


METHODS = {
    "get_arrangement": (get_arrangement, READ, None),
    "create_arrangement_clips": (create_arrangement_clips, WRITE, (("targets", "ref", "track"),)),
    "edit_arrangement_clips": (edit_arrangement_clips, WRITE, (("targets", "ref", "arr_clip"),)),
    "set_cue_points": (set_cue_points, WRITE, (("cues", "cue", "cue"),)),
}
