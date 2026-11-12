"""Shared pieces for the ``dom_*`` handler modules (stdlib only; main thread only).

Holds the method kinds and the refusal type the gate uses (``safety`` re-exports them, so the
domain modules never import ``safety`` and the gate can import every domain module), the limits,
the index selectors that reads use to find objects, and value validation.

Domain module contract: each ``dom_<d>.py`` exports ``METHODS = {name: (handler, kind, targets)}``.
A read handler is ``handler(ctx, params)`` with ``targets`` ``None``; a write handler is
``handler(ctx, params, targets)`` with ``targets`` a tuple of target specs (see
``safety.TARGETS``). ``ctx`` carries ``song``, ``app``, ``safety``, ``operations`` and ``probe``
(a zero-argument capabilities report). ``safety`` merges every module's ``METHODS`` at import;
a duplicate or unclassified name fails the import.

Reference issuing (T-005). ``reference_nodes(song, selector)`` turns index selectors (``track``
as int, ``"return:N"`` or ``"master"``; ``path`` as a DevicePath; ``scene``, ``parameter``,
``role``/``send``, ``take_lane``, ``arrangement``, ``cue``) into the root-to-leaf node path that
``safety.Safety.issue`` stores, with a snapshot per level; ``safety._alive`` re-checks each level.
Every domain module issues through it. Bridge methods here:

- ``ref_issue`` (read): references for up to ``BATCH_LIMIT`` selectors in one call;
- ``ref_check`` (read): whether references still validate (the refusal code when not); it
  runs exactly the gate's ``resolve``, so a proof can show refusals without writing;
- ``ref_lab`` (write, global, dev only): fixed structural edits for ``scripts/live_refs_test.py``.
  Refused unless the config says ``"dev_probes": true`` and the request carries the lease; it
  creates scratch tracks, returns, scenes, take lanes, arrangement clips and cues, loads a drum
  kit onto its own track, and deletes or moves only objects under a root it created itself.
"""

import math

from .core import (  # noqa: F401 - Invalid and Refused are re-exported to the domains
    Invalid,
    Refused,
    log_failure,
    public_error,
    readable,
)

READ, WRITE, CONTROL = "read", "write", "control"

BROWSER_ROOTS = (
    "instruments",
    "sounds",
    "drums",
    "audio_effects",
    "midi_effects",
    "samples",
    "user_library",
    "plugins",
    "packs",
    "current_project",
)
WALK_BUDGET = 4000  # max browser nodes visited per call/slice (main-thread safety)
LIST_LIMIT = 200  # max items per listing page
SEARCH_LIMIT = 100  # max results per search slice
PATH_LIMIT = 8  # max browser path depth
NOTE_LIMIT = 1000  # a defensive bound; the 16384-node frame cap binds first (host: models_clips)
SAMPLE_LIMIT = 129  # max display conversions per bridge request (all requests together)
BATCH_LIMIT = 64
LOAD_ROOTS = ("audio_effects", "plugins")
# Documentation only: a browser load inserts after the selected device of the selected track, so an
# append first selects the track's last device (refused if that cannot be done and observed) and
# the operation tick verifies per load that the single new device landed last.
APPEND_PLACEMENT_VERIFIED = True
MAX_DEVICE_DEPTH = 6  # device levels in a DevicePath (matches models.MAX_DEVICE_DEPTH)
# ``mixer_device`` members a ``mixer_param`` reference may name (plus ``send`` by index). Fixed:
# a role is never an attribute name taken from a request. Present in Live 12.2 per P-01; members
# a given owner lacks (``crossfader`` on a regular track, for instance) fail to issue.
MIXER_ROLES = (
    "volume",
    "panning",
    "track_activator",
    "crossfader",
    "cue_volume",
    "song_tempo",
    "left_split_stereo",
    "right_split_stereo",
)


def _same(a, b):
    if a is b:
        return True
    try:
        return bool(a == b)
    except Exception:  # noqa: BLE001
        return False


def same_items(a, b):
    """Equal length and pairwise identical-or-equal (no ``zip(strict=)``: Python 3.8 safe)."""
    return len(a) == len(b) and all(_same(a[i], b[i]) for i in range(len(a)))


# ---- selectors (reads only: indices find objects, they never authorize a write) ----------


def _track(song, params, key="track"):
    idx = params.get(key)
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(song.tracks):
        raise Invalid(f"'{key}' must be an integer track index 0..{len(song.tracks) - 1}")
    return song.tracks[idx]


def _device(track, params):
    idx = params.get("device")
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(track.devices):
        raise Invalid(f"'device' must be an integer device index 0..{len(track.devices) - 1}")
    return track.devices[idx]


def _scene(song, params):
    idx = params.get("scene")
    if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(song.scenes):
        raise Invalid(f"'scene' must be an integer scene index 0..{len(song.scenes) - 1}")
    return song.scenes[idx]


def _slot(song, params):
    track = _track(song, params)
    _scene(song, params)
    idx = params["scene"]
    if idx >= len(track.clip_slots):
        raise Invalid("'scene' has no clip slot on this track")
    return track, track.clip_slots[idx]


def _clip(song, params):
    _t, slot = _slot(song, params)
    if not slot.has_clip:
        raise Invalid("clip slot is empty")
    return slot.clip


# ---- validation ---------------------------------------------------------------------------


def _number(value, name, minimum, maximum=None, exclusive=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or (isinstance(value, float) and not math.isfinite(value))
        or (value <= minimum if exclusive else value < minimum)
        or (maximum is not None and value > maximum)
    ):
        bound = f"> {minimum}" if exclusive else f">= {minimum}"
        if maximum is not None:
            bound += f" and <= {maximum}"
        raise Invalid(f"'{name}' must be a finite number {bound}")
    return value


def _validated_notes(notes):
    if not isinstance(notes, list) or len(notes) > NOTE_LIMIT:
        raise Invalid(f"'notes' must be a list of at most {NOTE_LIMIT} notes")
    result = []
    for note in notes:
        if not isinstance(note, dict):
            raise Invalid("each note must be an object")
        pitch = note.get("pitch")
        if isinstance(pitch, bool) or not isinstance(pitch, int) or not 0 <= pitch <= 127:
            raise Invalid("'pitch' must be an integer 0..127")
        start = _number(note.get("start_time"), "start_time", 0)
        duration = _number(note.get("duration"), "duration", 0, exclusive=True)
        velocity = note.get("velocity")
        if isinstance(velocity, bool) or not isinstance(velocity, int) or not 1 <= velocity <= 127:
            raise Invalid("'velocity' must be an integer 1..127")
        mute = note.get("mute", False)
        if not isinstance(mute, bool):
            raise Invalid("'mute' must be a bool")
        result.append((pitch, start, duration, velocity, mute))
    return result


# ---- runtime facts ------------------------------------------------------------------------


def _note_specification():
    try:
        import Live
    except ImportError:
        return None
    clip_module = getattr(Live, "Clip", None)
    if clip_module is not None and hasattr(clip_module, "MidiNoteSpecification"):
        return clip_module.MidiNoteSpecification
    return None


def _live_version(app):
    try:
        return [app.get_major_version(), app.get_minor_version(), app.get_bugfix_version()]
    except Exception:  # noqa: BLE001
        return None


# ---- reference issuing (T-005) ------------------------------------------------------------


def _index(value, name, size):
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < size:
        raise Invalid(f"{name!r} must be an integer index 0..{size - 1}")
    return value


def _numbered(text, prefix):
    """``"<prefix>N"`` -> N (ASCII digits only), else None."""
    if isinstance(text, str) and text.startswith(prefix):
        digits = text[len(prefix) :]
        if digits.isascii() and digits.isdigit() and len(digits) <= 3:
            return int(digits)
    return None


def owner_node(song, sel):
    """A TrackSel (int, ``"return:N"`` or ``"master"``) -> its pinned reference node."""
    if sel == "master":
        return ("master", song.master_track, {})
    n = _numbered(sel, "return:")
    if n is not None:
        returns = song.return_tracks
        i = _index(n, "track", len(returns))
        return ("return_track", returns[i], {"index": i})
    tracks = song.tracks
    i = _index(sel, "track", len(tracks))
    return ("track", tracks[i], {"index": i})


def _pad_node(device, step):
    note = _numbered(step, "pad:")
    if note is None or note > 127:
        raise Invalid(f"chain step {step!r} must be a chain index or 'pad:0'..'pad:127'")
    if not getattr(device, "can_have_drum_pads", False):
        raise Invalid(f"{step!r}: the device is not a drum rack")
    pads = device.drum_pads
    for slot in range(len(pads)):
        if pads[slot].note == note:
            pad = pads[slot]
            return ("drum_pad", pad, {"slot": slot, "note": note, "chains": tuple(pad.chains)})
    raise Invalid(f"{step!r}: no drum pad with that note")


def device_nodes(container, path):
    """A DevicePath under ``container`` (track, return, master or chain) -> one node per level.
    Even positions are device indices; odd positions a chain index or ``"pad:N"`` (the pad, and
    its first chain when the path continues). Each device node snapshots its sibling layout."""
    if not isinstance(path, list) or not 1 <= len(path) <= 2 * MAX_DEVICE_DEPTH:
        raise Invalid(f"'path' must be a list of 1..{2 * MAX_DEVICE_DEPTH} steps")
    nodes = []
    for pos, step in enumerate(path):
        if pos % 2 == 0:
            devices = container.devices
            i = _index(step, f"path[{pos}]", len(devices))
            container = devices[i]
            layout = tuple(d.class_name for d in devices)
            nodes.append(("device", container, {"index": i, "layout": layout}))
        elif isinstance(step, str):
            pad = _pad_node(container, step)
            nodes.append(pad)
            container = pad[1]
            if pos + 1 < len(path):
                chains = container.chains
                _index(0, f"path[{pos}] chain", len(chains))
                container = chains[0]
                nodes.append(("chain", container, {"index": 0, "count": len(chains)}))
        else:
            if not getattr(container, "can_have_chains", False):
                raise Invalid(f"path[{pos}]: the device is not a rack")
            chains = container.chains
            i = _index(step, f"path[{pos}]", len(chains))
            container = chains[i]
            nodes.append(("chain", container, {"index": i, "count": len(chains)}))
    return nodes


def _mixer_node(mixer, p):
    role = p.get("role")
    if role == "send":
        sends = mixer.sends
        i = _index(p.get("send"), "send", len(sends))
        return ("mixer_param", sends[i], {"role": "send", "index": i, "count": len(sends)})
    if role not in MIXER_ROLES:
        raise Invalid(f"'role' must be 'send' or one of {list(MIXER_ROLES)}")
    try:
        param = getattr(mixer, role)  # role is from the fixed MIXER_ROLES list
    except AttributeError:
        param = None
    if param is None:
        raise Invalid(f"this mixer has no {role!r}")
    return ("mixer_param", param, {"role": role})


def has_arrangement_clips(parent):
    """Group tracks hold no clips; Live raises RuntimeError on their arrangement_clips."""
    return not getattr(parent, "is_foldable", False)


def sorted_arrangement_clips(parent):
    """Arrangement clips by start time (their index); a group track refuses readably."""
    if not has_arrangement_clips(parent):
        raise Invalid("a group track has no arrangement clips; name one of its member tracks")
    return sorted(parent.arrangement_clips, key=lambda c: c.start_time)


def reference_nodes(song, p):
    """Index selectors -> the node path for one reference of kind ``p["kind"]``. Raises
    ValueError when the selectors do not name exactly an object of that kind."""
    kind = p.get("kind")
    if kind == "scene":
        scenes = song.scenes
        i = _index(p.get("scene"), "scene", len(scenes))
        return [("scene", scenes[i], {"index": i})]
    if kind == "cue":
        cues = sorted(song.cue_points, key=lambda c: c.time)
        c = cues[_index(p.get("cue"), "cue", len(cues))]
        return [("cue", c, {"time": c.time})]
    owner = owner_node(song, p.get("track"))
    nodes = [owner]
    if kind in ("slot", "clip"):
        slots = owner[1].clip_slots
        i = _index(p.get("scene"), "scene", min(len(slots), len(song.scenes)))
        nodes.append(("slot", slots[i], {"index": i, "scene": song.scenes[i]}))
        if kind == "clip":
            if not slots[i].has_clip:
                raise Invalid("clip slot is empty")
            nodes.append(("clip", slots[i].clip, {}))
    elif kind in ("device", "chain", "drum_pad", "param"):
        nodes += device_nodes(owner[1], p.get("path"))
        if kind == "param" and nodes[-1][0] == "device":
            params = nodes[-1][1].parameters
            i = _index(p.get("parameter"), "parameter", len(params))
            q = params[i]
            nodes.append(("param", q, {"index": i, "count": len(params), "name": q.name}))
    elif kind == "mixer_param":
        if p.get("path") is not None:
            nodes += device_nodes(owner[1], p.get("path"))
            if nodes[-1][0] != "chain":
                raise Invalid("a mixer 'path' must end at a chain")
        nodes.append(_mixer_node(nodes[-1][1].mixer_device, p))
    elif kind in ("take_lane", "arr_clip"):
        parent = owner[1]
        if kind == "take_lane" or p.get("take_lane") is not None:
            lanes = parent.take_lanes
            i = _index(p.get("take_lane"), "take_lane", len(lanes))
            parent = lanes[i]
            nodes.append(("take_lane", parent, {"index": i}))
        if kind == "arr_clip":
            clips = sorted_arrangement_clips(parent)
            c = clips[_index(p.get("arrangement"), "arrangement", len(clips))]
            nodes.append(("arr_clip", c, {"start": c.start_time}))
    if nodes[-1][0] != kind:
        raise Invalid(f"the selectors name a {nodes[-1][0]}, not a {kind!r}")
    return nodes


def _items(p, key):
    items = p.get(key)
    if not isinstance(items, list) or not 1 <= len(items) <= BATCH_LIMIT:
        raise Invalid(f"{key!r} must be a list of 1..{BATCH_LIMIT} objects")
    if not all(isinstance(i, dict) for i in items):
        raise Invalid(f"every item in {key!r} must be an object")
    return items


_DESCRIBE = ("time", "start_time", "end_time", "length")  # what a confirmation can show


def ref_issue(ctx, p):
    """References for a batch of index selectors (all or nothing). Each row also describes
    the object it binds (a cue's time, a clip's span and length) so a confirmation can show
    exactly what that reference will act on."""
    out = []
    for item in _items(p, "targets"):
        nodes = reference_nodes(ctx.song, item)
        obj = nodes[-1][1]
        name = getattr(obj, "name", None)
        row = {
            "kind": nodes[-1][0],
            "ref": ctx.safety.issue(*nodes),
            "name": name if isinstance(name, str) else None,
        }
        if nodes[-1][0] in ("cue", "clip", "arr_clip"):
            for attr in _DESCRIBE:
                try:
                    value = getattr(obj, attr, None)
                except Exception:  # noqa: BLE001 - a description is optional
                    value = None
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    row[attr] = value
        out.append(row)
    return {"generation": ctx.safety.generation, "refs": out}


def confirmed_clips(ctx, refs, where, key, kind="clip"):
    """``refs`` (clip references a confirmation showed) -> the clips they bind; a missing,
    stale or changed one refuses as ``target_changed`` before anything is written."""
    if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
        raise Invalid(f"{where}: {key!r} must be a list of clip references")
    try:
        return [ctx.safety.resolve(kind, r, ctx.song).obj for r in refs]
    except Refused as exc:
        raise Refused(
            "target_changed",
            f"{where}: a clip confirmed for deletion changed or is gone ({exc.code}); "
            "nothing was applied, read again and confirm anew",
        ) from None


def ref_check(ctx, p):
    """Whether each ``{kind, ref}`` still passes the gate's own ``resolve`` (read-only)."""
    results = []
    for item in _items(p, "refs"):
        try:
            ctx.safety.resolve(item.get("kind"), item.get("ref"), ctx.song)
            results.append({"valid": True})
        except Refused as refusal:
            results.append({"valid": False, "code": refusal.code})
    return {"generation": ctx.safety.generation, "results": results}


# ---- shared write helpers (v2 tool contract) -------------------------------------------
#
# Capabilities. A domain module may export ``CAPABILITIES = {name: (state, reason)}`` next to
# ``METHODS``; ``safety`` merges them fail-closed into ``safety.CAPABILITIES`` (duplicate names or
# an unknown state fail the import) and ``ctx.capabilities`` carries the merged table. States:
#
# - ``supported``: proven in Live (evidence named in ``reason``); runs.
# - ``unverified``: implemented defensively, not yet proven; runs, and the reply should say so
#   (``unverified`` list). The final proof promotes it to ``supported`` or ``disabled``.
# - ``disabled``: known unsafe on this Live (native crash risk, P-19); refused before any native
#   call, whatever ``hasattr`` says.
# - ``unsupported``: the API is absent or read-only (count-in setter, follow actions, ...);
#   refused before any native call.
#
# A runtime quarantine (``quarantine``) closes a capability for the life of the Remote Script
# after an unknown outcome; it is never reopened by a retry.

SUPPORTED, UNVERIFIED, DISABLED, UNSUPPORTED = "supported", "unverified", "disabled", "unsupported"
CAPABILITY_STATES = (SUPPORTED, UNVERIFIED, DISABLED, UNSUPPORTED)


def read_after(read, label):
    """Read Live state back after this call already wrote: any failure becomes a
    ``readback_error`` field (logged by type and location), never a raise, because a raise
    here would report an applied write as not applied."""
    try:
        return read()
    except Exception as exc:  # noqa: BLE001 - the write happened; keep its receipt
        log_failure(label, exc)
        return {"readback_error": public_error(exc, "readback_failed")}


def flag(item, key, where):
    """A request boolean, read the same way by the write gate and by every handler: absent is
    False, anything but a JSON true/false is refused (never truthiness: "true" or 1 is not a
    flag). Delete-controlling flags must go through this helper on both sides."""
    value = item.get(key, False)
    if not isinstance(value, bool):
        raise Invalid(f"{where}: '{key}' must be a bool")
    return value


def flagged(params, key, field):
    """True when an item of the list ``params[key]`` sets the boolean ``field``. Every item's
    value is type-checked first, so the gate never decides a permission from a malformed flag."""
    items = params.get(key) if isinstance(params, dict) else None
    if not isinstance(items, list):
        return False
    hits = [flag(it, field, f"{key}[{i}]") for i, it in enumerate(items) if isinstance(it, dict)]
    return any(hits)


def unsupported(what, reason):
    """The bounded refusal for an ability this Live cannot do: ``refused:unsupported``. Raise it
    only before any write began."""
    return Refused("unsupported", f"{what}: {reason}")


def require(ctx, name, members=()):
    """Gate one capability before any native call. Returns its state (``supported`` or
    ``unverified``); raises ``refused:unsupported`` when it is disabled, unsupported, quarantined,
    undeclared, or when an object in ``members`` (``(obj, attribute)`` pairs) lacks the member.
    Presence never unlocks a disabled or unsupported capability."""
    table = getattr(ctx, "capabilities", None) or {}
    entry = table.get(name)
    if entry is None:
        raise unsupported(name, "not a declared capability")
    state, reason = entry
    held = getattr(ctx.safety, "quarantined", {}).get(name)
    if held is not None:
        raise unsupported(name, f"quarantined after an unknown outcome ({held})")
    if state not in (SUPPORTED, UNVERIFIED):
        raise unsupported(name, f"{state} on this Live ({reason})")
    for obj, attribute in members:
        if not hasattr(obj, attribute):
            raise unsupported(name, f"this object has no {attribute!r}")
    return state


def quarantine(ctx, name, why):
    """Close a capability after an unknown outcome (never retried in this script session)."""
    held = getattr(ctx.safety, "quarantined", None)
    if isinstance(held, dict):
        held.setdefault(name, str(why)[:200])


def capability_report(ctx):
    """``{name: {state, reason}}`` for ``live_hello`` (quarantine overrides the declared state)."""
    held = getattr(ctx.safety, "quarantined", {})
    out = {}
    for name, (state, reason) in sorted((getattr(ctx, "capabilities", None) or {}).items()):
        if name in held:
            state, reason = "quarantined", held[name]
        out[name] = {"state": state, "reason": reason}
    return out


# Two-pass batch writes. Pass 1 validates every item and raises (ValueError or Refused) before any
# write: the gate then reports "not applied", which is true. Pass 2 writes in order and never
# raises: from the first write on, the reply is a receipt (complete or partial) whose per-item
# ``outcome`` is ``applied``, ``unknown`` (the write raised: it may have changed Live) or
# ``not_attempted``. It stops at the first failure and never rolls back. Each readback row is
# sent once, in ``applied``: the applied items are always the leading ones, so ``applied[k]`` is
# item ``k``'s row (items carry only index/outcome/error, never a second copy of the row).

APPLIED, UNKNOWN_OUTCOME, NOT_ATTEMPTED = "applied", "unknown", "not_attempted"


def run_writes(prepared, write):
    """Pass 2 over ``prepared`` (pass-1 output, one entry per item): ``write(entry)`` returns a
    readback row. Returns ``{"status", "applied", "items", "stopped_at", "error"}``."""
    items, applied, stopped, error = [], [], None, None
    for i, entry in enumerate(prepared):
        if stopped is not None:
            items.append({"index": i, "outcome": NOT_ATTEMPTED})
            continue
        try:
            row = write(entry)
        except Exception as exc:  # noqa: BLE001 - after writes began, a receipt, never a raise
            stopped, error = i, public_error(exc, "write_failed")
            if not readable(exc):
                log_failure(f"write {i}", exc)
            items.append({"index": i, "outcome": UNKNOWN_OUTCOME, "error": error})
            continue
        applied.append(row)  # items[i] is applied[i]: never sent twice
        items.append({"index": i, "outcome": APPLIED})
    status = "complete" if stopped is None else "partial"
    return {
        "status": status,
        "applied": applied,
        "items": items,
        "stopped_at": stopped,
        "error": error,
    }


def two_pass(items, validate, write):
    """``validate(index, item)`` for every item first (may raise: nothing written), then
    ``run_writes`` over the validated entries."""
    prepared = [validate(i, item) for i, item in enumerate(items)]
    return run_writes(prepared, write)


def position_of(seq, obj):
    """Current index of ``obj`` in ``seq`` by identity/equality (never a stale issued index)."""
    for i in range(len(seq)):
        if _same(seq[i], obj):
            return i
    raise RuntimeError("object not found in its parent")


def for_deletion(resolved):
    """Order resolved targets for structural deletes: deepest paths first, then the highest issued
    index first, so no deletion shifts a later target. Delete by identity (``position_of``) at
    write time, never by the issued index."""

    def key(r):
        snap = r.path[-1][2]
        return (-len(r.path), -snap.get("index", snap.get("slot", snap.get("start", 0))))

    return sorted(resolved, key=key)


def clip_address_nodes(song, addr):
    """A clip address -> reference nodes: ``{track, scene}`` (session clip) or
    ``{track, arrangement[, take_lane]}`` (arrangement clip, sorted by start)."""
    if not isinstance(addr, dict):
        raise Invalid("a clip address must be an object")
    if addr.get("arrangement") is not None:
        if addr.get("scene") is not None:
            raise Invalid("a clip address names a 'scene' or an 'arrangement' index, not both")
        return reference_nodes(song, {**addr, "kind": "arr_clip"})
    return reference_nodes(song, {**addr, "kind": "clip"})


# ---- ref_lab: dev-only structural edits on scratch objects (scripts/live_refs_test.py) -------

_LAB = {"generation": None, "owned": []}  # roots ref_lab created, in the current generation


def _lab_owned(ctx):
    if _LAB["generation"] != ctx.safety.generation:
        _LAB["generation"], _LAB["owned"] = ctx.safety.generation, []
    return _LAB["owned"]


def _lab_new(before, after, what):
    """The single member of ``after`` not in ``before``; RuntimeError otherwise."""
    new = [x for x in after if not any(_same(x, b) for b in before)]
    if len(new) != 1:
        raise RuntimeError(f"could not identify the new {what} ({len(new)} candidates)")
    return new[0]


def _lab_target(ctx, p, kind_key="kind", ref_key="ref"):
    """Resolve a reference through the gate's own check; its root must be a lab object."""
    resolved = ctx.safety.resolve(p.get(kind_key), p.get(ref_key), ctx.song)
    root = resolved.path[0][1]
    if not any(_same(o, root) for o in _lab_owned(ctx)):
        raise Refused("not_lab_owned", "ref_lab only edits objects under a root it created")
    return resolved


_position = position_of


def _lab_create_track(ctx, p):
    song = ctx.song
    before = list(song.tracks)
    if p.get("track_kind") == "audio":
        song.create_audio_track(-1)
    else:
        song.create_midi_track(-1)
    track = _lab_new(before, song.tracks, "track")
    track.name = "ALMCP refs"
    _lab_owned(ctx).append(track)
    return {"track": _position(song.tracks, track)}


def _lab_create_return(ctx, _p):
    song = ctx.song
    before = list(song.return_tracks)
    song.create_return_track()
    track = _lab_new(before, song.return_tracks, "return track")
    track.name = "ALMCP refs"
    _lab_owned(ctx).append(track)
    return {"return": _position(song.return_tracks, track)}


def _lab_create_scene(ctx, _p):
    song = ctx.song
    before = list(song.scenes)
    song.create_scene(-1)
    scene = _lab_new(before, song.scenes, "scene")
    _lab_owned(ctx).append(scene)
    return {"scene": _position(song.scenes, scene)}


def _lab_create_take_lane(ctx, p):
    track = _lab_target(ctx, p).obj
    before = list(track.take_lanes)
    track.create_take_lane()
    lane = _lab_new(before, track.take_lanes, "take lane")
    return {"take_lane": _position(track.take_lanes, lane)}


def _lab_create_arr_clip(ctx, p):
    parent = _lab_target(ctx, p).obj  # a lab MIDI track or one of its take lanes
    start = _number(p.get("start"), "start", 0)
    length = _number(p.get("length"), "length", 0, 64, exclusive=True)
    before = list(parent.arrangement_clips)
    parent.create_midi_clip(float(start), float(length))
    clip = _lab_new(before, parent.arrangement_clips, "arrangement clip")
    return {"start": clip.start_time}


def _at_playhead(song, time_):
    """Move the stopped playhead to ``time_``; returns the previous position."""
    if song.is_playing:
        raise Refused("transport_playing", "stop the transport before cue edits")
    previous = song.current_song_time
    song.current_song_time = time_
    return previous


def _lab_create_cue(ctx, p):
    song = ctx.song
    time_ = float(_number(p.get("time"), "time", 0))
    before = list(song.cue_points)
    previous = _at_playhead(song, time_)
    try:
        if song.is_cue_point_selected():  # a cue already sits there: toggling would delete it
            raise Refused("cue_occupied", "a cue point already exists at that time")
        song.set_or_delete_cue()
    finally:
        song.current_song_time = previous
    cue = _lab_new(before, song.cue_points, "cue point")
    _lab_owned(ctx).append(cue)
    ordered = sorted(song.cue_points, key=lambda c: c.time)
    out = {"time": cue.time, "cue": _position(ordered, cue)}
    if abs(cue.time - time_) > 1e-6:  # Live clamps the playhead to the song length
        # the cue exists (owned, cleaned up with the lab): a receipt, never "not applied"
        out.update(status="applied_mismatch", requested=time_)
    return out


def _lab_load_kit(ctx, p):
    """Load the first drum kit preset (``.adg``) under ``browser.drums`` (or the one named
    ``kit``) onto an empty lab MIDI track. The device appears on a later tick; poll a read."""
    track = _lab_target(ctx, p).obj
    if not track.has_midi_input or len(track.devices):
        raise Refused("unsupported_target", "load_kit needs an empty lab MIDI track")
    wanted = p.get("kit")
    stack, visited, item = [ctx.app.browser.drums], 0, None
    while stack and item is None and visited < WALK_BUDGET:
        node = stack.pop()
        kids = list(getattr(node, "children", None) or ())
        for child in reversed(kids):
            visited += 1
            name = child.name
            if getattr(child, "is_loadable", False) and name.lower().endswith(".adg"):
                if wanted is None or name == wanted:
                    item = child
            elif getattr(child, "is_folder", False):
                stack.append(child)
    if item is None:
        raise Refused("kit_not_found", "no drum kit preset found within the walk budget")
    ctx.song.view.selected_track = track
    ctx.app.browser.load_item(item)
    return {"kit": item.name}


def _lab_delete(ctx, p):
    resolved = _lab_target(ctx, p)
    song, kind, obj = ctx.song, resolved.path[-1][0], resolved.obj
    if kind == "track":
        song.delete_track(_position(song.tracks, obj))
    elif kind == "return_track":
        song.delete_return_track(_position(song.return_tracks, obj))
    elif kind == "scene":
        song.delete_scene(_position(song.scenes, obj))
    elif kind == "device":
        parent = resolved.path[-2][1]  # track, return, master or chain
        parent.delete_device(_position(parent.devices, obj))
    elif kind == "drum_pad":
        obj.delete_all_chains()
    elif kind == "arr_clip":
        resolved.path[0][1].delete_clip(obj)  # Track.delete_clip (12.2)
    elif kind == "cue":
        previous = _at_playhead(song, obj.time)
        try:
            if not song.is_cue_point_selected():
                raise RuntimeError("cue point not selected at its own time")
            song.set_or_delete_cue()
        finally:
            song.current_song_time = previous
    else:  # chain, take_lane, mixer_param, master: Live 12.2 has no delete for these
        raise Refused("unsupported", f"ref_lab cannot delete a {kind}")
    return {"deleted": kind}


def _lab_move_device(ctx, p):
    device = _lab_target(ctx, p)
    if device.path[-1][0] != "device":
        raise Invalid("'ref' must be a device reference")
    to = _lab_target(ctx, p, "to_kind", "to_ref")
    target = to.obj
    if to.path[-1][0] == "drum_pad":  # into the pad's first chain
        target = target.chains[0]
    elif to.path[-1][0] not in ("track", "chain"):
        raise Invalid("'to_ref' must be a track, chain or drum pad reference")
    position = _index(p.get("position"), "position", len(target.devices) + 1)
    ctx.song.move_device(device.obj, target, position)
    return {"moved": True, "position": position}


def _lab_cue_times(ctx, _p):
    cues = list(ctx.song.cue_points)
    return {
        "times": [c.time for c in cues],
        "eq": [[bool(a == b) for b in cues] for a in cues],
        "is_same": [[a is b for b in cues] for a in cues],
    }


LAB_ACTIONS = {
    "cue_times": _lab_cue_times,
    "create_track": _lab_create_track,
    "create_return": _lab_create_return,
    "create_scene": _lab_create_scene,
    "create_take_lane": _lab_create_take_lane,
    "create_arr_clip": _lab_create_arr_clip,
    "create_cue": _lab_create_cue,
    "load_kit": _lab_load_kit,
    "delete": _lab_delete,
    "move_device": _lab_move_device,
}


def ref_lab(ctx, p, _t):
    if not ctx.safety.dev_probes_enabled():
        raise Refused("dev_probes_disabled", 'ref_lab is off; set "dev_probes": true in the config')
    if p.get("lease") is None:  # the gate matched any token; the lab always requires one
        raise Refused("lease_required", "ref_lab runs only under the lease")
    action = p.get("action")
    run = LAB_ACTIONS.get(action) if isinstance(action, str) else None
    if run is None:
        raise Invalid(f"'action' must be one of {sorted(LAB_ACTIONS)}")
    # Any other exception propagates: the dispatcher logs it (sanitized) and answers
    # HandlerError with may_have_applied, since a lab action can fail after it mutated.
    out = run(ctx, p)
    out["generation"] = ctx.safety.generation
    return out


METHODS = {
    "ref_issue": (ref_issue, READ, None),
    "ref_check": (ref_check, READ, None),
    "ref_lab": (ref_lab, WRITE, ()),
}
