"""Bounded pending-load state and browser cursors (stdlib only; main thread only).

Not a job engine: one load may be in flight, and a small ring keeps recent records so a client
can read an outcome back after losing a response. Nothing here calls Live except reading
``track.devices`` / ``len(device.parameters)`` during ``tick``.

Load operation states (``pending`` is the only non-terminal state besides watched ``unknown``):

* ``pending``  native load started; waiting to observe exactly one new device.
* ``ready``    exactly one new device (by object identity, existing prefix unchanged) was seen on
               two consecutive ticks with the same, non-zero parameter count. Parameter writes
               must wait for this state; ``device`` is a reference to that device.
* ``failed``   ``browser.load_item`` raised and the device list was observed unchanged.
* ``unknown``  outcome not established: ``timeout`` (``LOAD_TIMEOUT`` s without a new device),
               ``set_changed``, ``track_gone``, ``layout_changed`` (existing devices changed),
               ``ambiguous_change`` (more than one new device), ``no_song``, ``session_ended``.
               A timeout is never "absent": only ``timeout`` stays watched for ``WATCH_TTL`` s
               and becomes ``ready`` if a single new device later appears.

Quarantine: while any load is ``pending``, every new load is refused (``load_pending``); an
``unknown`` load keeps its target track refused (``quarantined``) for the life of the bridge
session (generation). Only ``Safety.invalidate`` (Set change, disconnect) resets it. There is no
retry, no rollback and no replay. Ring: ``RING`` records; only ``ready``/``failed`` ones are
evicted, so a full ring of pending/unknown records refuses new loads (``operations_full``).

``tick`` is called from the entry point's ``update_display``; a soft monotonic budget of
``TICK_BUDGET`` s per call stops it between operations (a single native call cannot be preempted).
"""

import collections
import secrets
import time

from .safety import Refused, _same, same_items

RING = 16
LOAD_TIMEOUT = 20.0
WATCH_TTL = 120.0
TICK_BUDGET = 0.010
MAX_CURSORS = 4
CURSOR_TTL = 30.0

PENDING, READY, FAILED, UNKNOWN = "pending", "ready", "failed", "unknown"


class Cursors:
    """At most ``MAX_CURSORS`` single-use continuations that expire after ``CURSOR_TTL`` s."""

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._items = collections.OrderedDict()

    def expire(self):
        now = self._clock()
        for token in [t for t, (_k, _s, exp) in self._items.items() if exp <= now]:
            del self._items[token]

    def put(self, kind, state):
        self.expire()
        token = secrets.token_hex(8)
        self._items[token] = (kind, state, self._clock() + CURSOR_TTL)
        while len(self._items) > MAX_CURSORS:
            self._items.popitem(last=False)  # oldest continuation is dropped
        return token

    def take(self, token, kind):
        self.expire()
        entry = self._items.pop(token, None) if isinstance(token, str) else None
        if entry is None or entry[0] != kind:
            raise Refused("unknown_cursor", "unknown, used or expired cursor; start again")
        return entry[1]

    def clear(self):
        self._items.clear()

    def __len__(self):
        return len(self._items)


class Op:
    def __init__(self, op_id, track, before, item, root, generation, now):
        self.id, self.track, self.before = op_id, track, tuple(before)
        self.item, self.root, self.generation = item, root, generation
        self.state, self.reason = PENDING, None
        self.started, self.watch_until = now, None
        self.seen = None  # (device, parameter count) from the previous tick
        self.device = self.after = self.devices_after = None  # set when ready


class Operations:
    def __init__(self, safety, clock=time.monotonic):
        self._safety, self._clock = safety, clock
        self._ring = collections.OrderedDict()
        self._closed = False
        self.cursors = Cursors(clock)

    # ---- preconditions and start ------------------------------------------------------
    def check_can_load(self, track):
        """Refuse before any browser call: one load at a time, never on a quarantined track."""
        generation = self._safety.generation
        for op in self._ring.values():
            if op.generation != generation:
                continue
            if op.state == PENDING:
                raise Refused(
                    "load_pending", f"load {op.id} is still pending; read it, do not retry"
                )
            if op.state == UNKNOWN and _same(op.track, track):
                raise Refused("quarantined", f"load {op.id} on this track has an unknown outcome")
        if len(self._ring) >= RING and not any(
            o.state in (READY, FAILED) for o in self._ring.values()
        ):
            raise Refused("operations_full", "too many unresolved operations; reset the session")

    def prior(self, op_id):
        return self._ring.get(op_id) if isinstance(op_id, str) else None

    def begin(self, track, item, root):
        """Record a load about to start. The caller has already run ``check_can_load``."""
        for old_id in [i for i, o in self._ring.items() if o.state in (READY, FAILED)]:
            if len(self._ring) < RING:
                break
            del self._ring[old_id]
        op = Op(
            secrets.token_hex(8),
            track,
            tuple(track.devices),
            item,
            root,
            self._safety.generation,
            self._clock(),
        )
        self._ring[op.id] = op
        return op

    def native_error(self, op, exc):
        op.reason = f"native_error:{type(exc).__name__}"
        if self._unchanged(op):
            op.state = FAILED  # observed unchanged right after the native call raised
        # otherwise stay pending: the tick decides from what is actually on the track

    def _unchanged(self, op):
        try:
            cur = tuple(op.track.devices)
        except Exception:  # noqa: BLE001
            return False
        return same_items(cur, op.before)

    # ---- read back --------------------------------------------------------------------
    def snapshot(self, op):
        state = op.state
        return {
            "operation": op.id,
            "state": state,
            "reason": op.reason,
            "applied": True if state == READY else False if state == FAILED else None,
            "may_have_applied": state in (PENDING, UNKNOWN),
            "item": op.item,
            "root": op.root,
            "generation": op.generation,
            "devices_before": len(op.before),
            "device": op.device,
            "devices_after": list(op.devices_after) if op.devices_after is not None else None,
        }

    def get(self, op_id):
        op = self.prior(op_id)
        if op is None:
            raise Refused("unknown_operation", "unknown or evicted operation id")
        return self.snapshot(op)

    # ---- lifecycle --------------------------------------------------------------------
    def tick(self, budget=TICK_BUDGET):
        """Advance pending/watched operations and expire cursors; returns how many advanced."""
        if self._closed:
            return 0
        self.cursors.expire()
        active = [o for o in self._ring.values() if o.state == PENDING or o.watch_until]
        if not active:
            return 0
        started, advanced = self._clock(), 0
        try:
            song = self._safety.song()  # also detects a Set change while idle
        except Refused:
            for op in active:
                self._finish(op, UNKNOWN, "no_song")
            return len(active)
        for op in active:
            if advanced and self._clock() - started > budget:
                break  # resume on the next display tick
            self._advance(op, song)
            advanced += 1
        return advanced

    def invalidate(self):
        """Bridge disconnect: no operation survives; later ticks do nothing."""
        for op in self._ring.values():
            if op.state in (PENDING, UNKNOWN):
                self._finish(op, UNKNOWN, "session_ended")
        self.cursors.clear()
        self._closed = True

    # ---- internals --------------------------------------------------------------------
    def _finish(self, op, state, reason, watch=False):
        op.state, op.reason = state, reason
        op.watch_until = (self._clock() + WATCH_TTL) if watch else None

    def _advance(self, op, song):
        now = self._clock()
        if op.generation != self._safety.generation:
            return self._finish(op, UNKNOWN, "set_changed")
        try:
            on_set = any(_same(t, op.track) for t in song.tracks)
        except Exception:  # noqa: BLE001
            on_set = False
        if not on_set:
            return self._finish(op, UNKNOWN, "track_gone")
        if op.watch_until and now >= op.watch_until:
            op.watch_until = None  # stop watching; quarantine stays
            return None
        try:
            cur = tuple(op.track.devices)
        except Exception:  # noqa: BLE001
            return self._finish(op, UNKNOWN, "track_unreadable")
        n = len(op.before)
        if len(cur) < n or not same_items(cur[:n], op.before):
            return self._finish(op, UNKNOWN, "layout_changed")
        extra = cur[n:]
        if not extra:
            if op.state == PENDING and now - op.started >= LOAD_TIMEOUT:
                self._finish(op, UNKNOWN, "timeout", watch=True)
            return None
        if len(extra) > 1:
            return self._finish(op, UNKNOWN, "ambiguous_change")
        device = extra[0]
        try:
            count = len(device.parameters)
        except Exception:  # noqa: BLE001
            count = 0
        previous, op.seen = op.seen, (device, count)
        if count and previous is not None and _same(previous[0], device) and previous[1] == count:
            op.after = cur
            op.devices_after = tuple(d.class_name for d in cur)
            layout = {"layout": op.devices_after}
            op.device = self._safety.issue(("track", op.track, {}), ("device", device, layout))
            self._finish(op, READY, "late" if op.reason == "timeout" else None)
        return None
