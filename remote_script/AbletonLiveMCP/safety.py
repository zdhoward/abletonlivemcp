"""Write-boundary safety for the Remote Script (stdlib only; main thread only).

Dispatch contract (M1b-01). Every bridge method is classified in ``CLASSIFICATION``; a method
missing from it is refused (fail closed). Order of checks for a method classed ``write``:

1. policy: ``read_only`` from the shared bridge config (below) must be exactly ``false``;
2. lease: while a mutation lease is held, the request must carry that lease token;
3. Set: the *current* Song is fetched from a supplier on every dispatch; a different Song
   object bumps the generation, which drops every reference and any lease;
4. targets: every target named in ``TARGETS`` must be an opaque reference string issued by a
   read in the current generation and still a current member of the live object tree
   (track in the Set, device in its track, parameter in its device at the issued position,
   slot in its track at the issued scene row, clip still in its slot, scene in the Set);
   device parameters additionally require an unchanged parameter layout. A request with no
   target (global operation) must carry the expected ``generation``;
5. only then does the handler run its own value validation and the Live write.

A bare number or name never authorizes a write: numeric indices are accepted by reads only,
to find objects and receive references. A refusal is returned as a successful bridge result
``{"refused": true, "applied": false, "code": ..., "message": ...}`` because the bridge hides
handler exceptions behind ``HandlerError``/``may_have_applied=true``; the host must treat a
``refused`` result as an error (nothing was written). A refusal is never raised after any
write began.

References: ``token_hex(8)`` ids mapped to strong references (so a recycled Python id can never
validate) in a bounded LRU registry of ``MAX_REFS`` entries; evicted/unknown ids are refused.
Generation starts at 1 and increases on Song change or ``invalidate()`` (disconnect); the
registry and lease are cleared at the same moment. Liveness of Live objects is checked by
identity-or-equality membership inside try/except; any exception means "not valid".

Lease: ``lease_acquire`` (ttl <= ``MAX_LEASE_TTL``, default ``DEFAULT_LEASE_TTL``) returns a
random token; ``lease_release`` frees it. It is non-renewable, expires on a monotonic clock,
and a competing acquire is refused while one is live. A lease only serializes workflows; it is
not user approval, and policy is always checked first.

Policy source: the same config file ``core._load_secret`` reads (``ABLETONLIVEMCP_CONFIG``
absolute override, else ``~/.abletonlivemcp/bridge.json``; lstat/link/reparse check, opened-file
identity, owner-only ACL/mode via ``core._windows_private``, 8192-byte limit, strict
``core._decode``, 32-byte hex secret required). ``core`` returns only the secret, so
``config_read_only`` repeats that sequence (calling core's own helpers) and reads ``read_only``.
Writes are allowed only when it is the JSON literal ``false``; missing, non-bool, unreadable or
insecure config means read-only. It is re-read on every write dispatch.
"""

import collections
import hmac
import os
import secrets
import stat
import time
from types import SimpleNamespace

from .core import _HEX, _decode, _windows_private

MAX_REFS = 1024
MAX_REF_LEN = 64
DEFAULT_LEASE_TTL = 30.0
MAX_LEASE_TTL = 60.0

READ, WRITE, CONTROL = "read", "write", "control"

CLASSIFICATION = {
    "hello": READ,
    "session_info": READ,
    "tracks": READ,
    "scenes": READ,
    "clip_slot": READ,
    "browser_roots": READ,
    "browser_list": READ,
    "browser_search": READ,
    "device_parameters": READ,
    "sample_parameter": READ,
    "sample_parameters": READ,
    "get_transport": READ,
    "get_clip": READ,
    "get_notes": READ,
    "lease_acquire": CONTROL,
    "lease_release": CONTROL,
    "load_item": WRITE,
    "set_device_parameter": WRITE,
    "set_device_parameters": WRITE,
    "create_track": WRITE,
    "set_track_name": WRITE,
    "set_track_color": WRITE,
    "set_tempo": WRITE,
    "play": WRITE,
    "stop": WRITE,
    "create_scene": WRITE,
    "set_scene_name": WRITE,
    "fire_scene": WRITE,
    "create_clip": WRITE,
    "add_notes": WRITE,
    "fire_clip": WRITE,
    "stop_clip": WRITE,
}

# (param, kind) is a single reference; (list_param, item_param, kind) is a list of objects each
# carrying a reference. A write with an empty tuple is a global operation (needs `generation`).
TARGETS = {
    "load_item": (("track", "track"),),
    "set_device_parameter": (("parameter", "param"),),
    "set_device_parameters": (("writes", "parameter", "param"),),
    "create_track": (),
    "set_track_name": (("track", "track"),),
    "set_track_color": (("track", "track"),),
    "set_tempo": (),
    "play": (),
    "stop": (),
    "create_scene": (),
    "set_scene_name": (("scene", "scene"),),
    "fire_scene": (("scene", "scene"),),
    "create_clip": (("slot", "slot"),),
    "add_notes": (("clip", "clip"),),
    "fire_clip": (("clip", "clip"),),
    "stop_clip": (("clip", "clip"),),
}


class Refused(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message

    def result(self):
        return {"refused": True, "applied": False, "code": self.code, "message": self.message}


def config_read_only():
    """True unless the shared config is valid, private and says ``"read_only": false``."""
    try:
        path = os.environ.get("ABLETONLIVEMCP_CONFIG")
        if path is None:
            path = os.path.join(os.path.expanduser("~"), ".abletonlivemcp", "bridge.json")
        if not path or not os.path.isabs(path):
            return True
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode) or getattr(before, "st_file_attributes", 0) & 0x400:
            return True
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or (before.st_dev, before.st_ino) != (
                info.st_dev,
                info.st_ino,
            ):
                return True
            if os.name == "nt":
                _windows_private(stream.fileno())
            elif info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                return True
            raw = stream.read(8193)
        if len(raw) > 8192:
            return True
        config = _decode(raw)
        secret = config.get("secret") if isinstance(config, dict) else None
        if not isinstance(secret, str) or not _HEX.fullmatch(secret):
            return True
        return config.get("read_only") is not False
    except Exception:  # noqa: BLE001 - every failure must fail closed
        return True


def _same(a, b):
    if a is b:
        return True
    try:
        return bool(a == b)
    except Exception:  # noqa: BLE001
        return False


def _at(seq, index, obj):
    try:
        return 0 <= index < len(seq) and _same(seq[index], obj)
    except Exception:  # noqa: BLE001
        return False


def _member(seq, obj):
    try:
        return any(_same(x, obj) for x in seq)
    except Exception:  # noqa: BLE001
        return False


class Safety:
    def __init__(self, song_supplier, policy=config_read_only, clock=time.monotonic):
        self._supplier, self._policy, self._clock = song_supplier, policy, clock
        self._song = None
        self.generation = 1
        self._refs = collections.OrderedDict()
        self._lease = None  # (token, expires)

    # ---- Set / generation -------------------------------------------------------------
    def song(self):
        try:
            current = self._supplier()
        except Exception:  # noqa: BLE001
            current = None
        if current is None:
            raise Refused("no_song", "the current Live Set is unavailable")
        if self._song is None:
            self._song = current
        elif not _same(current, self._song):
            self.invalidate()
            self._song = current
        return current

    def invalidate(self):
        """Set change or bridge disconnect: drop every reference and the lease."""
        self.generation += 1
        self._refs.clear()
        self._lease = None

    # ---- references -------------------------------------------------------------------
    def issue(self, *nodes):
        """nodes: root-to-leaf tuples (kind, obj, snapshot dict). Returns the leaf's reference."""
        ref = secrets.token_hex(8)
        self._refs[ref] = (self.generation, tuple(nodes))
        while len(self._refs) > MAX_REFS:
            self._refs.popitem(last=False)
        return ref

    def _valid(self, song, nodes):
        parent = song
        for kind, obj, snap in nodes:
            try:
                if kind == "track":
                    ok = _member(song.tracks, obj) or _member(
                        getattr(song, "return_tracks", ()), obj
                    )
                elif kind == "scene":
                    ok = _member(song.scenes, obj)
                elif kind == "slot":
                    ok = _at(parent.clip_slots, snap["index"], obj) and _at(
                        song.scenes, snap["index"], snap["scene"]
                    )
                elif kind == "clip":
                    ok = bool(parent.has_clip) and _same(parent.clip, obj)
                elif kind == "device":
                    ok = _member(parent.devices, obj) and snap["layout"] == tuple(
                        d.class_name for d in parent.devices
                    )
                elif kind == "param":
                    ok = (
                        len(parent.parameters) == snap["count"]
                        and _at(parent.parameters, snap["index"], obj)
                        and obj.name == snap["name"]
                    )
                else:
                    ok = False
            except Exception:  # noqa: BLE001
                ok = False
            if not ok:
                return False
            parent = obj
        return True

    def resolve(self, kind, ref, song):
        if not isinstance(ref, str):
            raise Refused(
                "reference_required",
                f"{kind} must be a reference string from a read; an index is not accepted",
            )
        entry = self._refs.get(ref) if len(ref) <= MAX_REF_LEN else None
        if entry is None:
            raise Refused("unknown_reference", f"unknown or expired {kind} reference; re-read")
        generation, nodes = entry
        if generation != self.generation or nodes[-1][0] != kind:
            raise Refused("stale_reference", f"stale or wrong-kind {kind} reference; re-read")
        if not self._valid(song, nodes):
            raise Refused("stale_target", f"{kind} reference no longer matches Live; re-read")
        self._refs.move_to_end(ref)
        return SimpleNamespace(obj=nodes[-1][1], nodes={n[0]: n[1] for n in nodes})

    # ---- policy and lease ---------------------------------------------------------------
    def read_only(self):
        try:
            return self._policy() is not False
        except Exception:  # noqa: BLE001
            return True

    def _live_lease(self):
        if self._lease is not None and self._clock() >= self._lease[1]:
            self._lease = None
        return self._lease

    def lease_acquire(self, ttl):
        if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or not 0 < ttl:
            raise Refused("bad_lease", "'ttl' must be a positive number of seconds")
        if self._live_lease() is not None:
            raise Refused("lease_held", "another workflow holds the mutation lease")
        ttl = min(float(ttl), MAX_LEASE_TTL)
        token = secrets.token_hex(16)
        self._lease = (token, self._clock() + ttl)
        return {"lease": token, "ttl": ttl, "generation": self.generation}

    def lease_release(self, token):
        held = self._live_lease()
        if held is None or not isinstance(token, str) or not hmac.compare_digest(held[0], token):
            raise Refused("lease_mismatch", "no matching live lease to release")
        self._lease = None
        return {"released": True}

    def check_lease(self, token):
        held = self._live_lease()
        if held is None:
            if token is not None:
                raise Refused("lease_expired", "the lease expired or was invalidated; stop")
            return
        if not isinstance(token, str) or not hmac.compare_digest(held[0], token):
            raise Refused("lease_held", "another workflow holds the mutation lease")

    # ---- the single write gate ------------------------------------------------------------
    def authorize(self, method, params):
        """Run checks 1-4 for a write; return resolved targets by param name. Raises Refused."""
        if self.read_only():
            raise Refused("read_only", "bridge is read-only; enable writes in the local config")
        self.check_lease(params.get("lease"))
        song = self.song()
        specs = TARGETS[method]
        if not specs:
            if params.get("generation") != self.generation:
                raise Refused("stale_generation", "expected 'generation' does not match the Set")
            return {}
        targets = {}
        for spec in specs:
            if len(spec) == 2:
                targets[spec[0]] = self.resolve(spec[1], params.get(spec[0]), song)
            else:
                items = params.get(spec[0])
                if (
                    not isinstance(items, list)
                    or len(items) > 64
                    or not all(isinstance(i, dict) for i in items)
                ):
                    raise ValueError(f"{spec[0]!r} must be a list of objects")
                targets[spec[0]] = [self.resolve(spec[2], i.get(spec[1]), song) for i in items]
        return targets
