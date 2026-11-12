"""Write-boundary safety for the Remote Script (stdlib only; main thread only).

Dispatch contract (M1b-01). Every bridge method is classified in ``CLASSIFICATION``, which is
merged at import from the ``METHODS`` table of each ``dom_*`` module (a duplicate or malformed
declaration fails the import); a method missing from it is refused (fail closed). Order of
checks for a method classed ``write``:

1. policy: ``read_only`` from the shared bridge config (below) must be exactly ``false``;
2. lease: while a mutation lease is held, the request must carry that lease token;
3. Set: the *current* Song is fetched from a supplier on every dispatch; a different Song
   object bumps the generation, which drops every reference and any lease;
4. targets (then ``expect_name`` on each target, all before the handler): every target named in
   ``TARGETS`` must be an opaque reference string issued by a read in the current generation and
   still a current member of the live object tree, checked level by level from the root (see
   "Reference kinds" below); a list spec ``(param, item, ANY_KIND)`` takes mixed kinds, each item
   naming its own ``kind``. A request with no target
   (global operation) must carry the expected ``generation``;
5. only then does the handler run its own value validation and the Live write.

A bare number or name never authorizes a write: numeric indices are accepted by reads only,
to find objects and receive references. A refusal is returned as a successful bridge result
``{"refused": true, "applied": false, "code": ..., "message": ...}`` because the bridge hides
handler exceptions behind ``HandlerError``/``may_have_applied=true``; the host must treat a
``refused`` result as an error (nothing was written). A refusal is never raised after any
write began.

References: ``token_hex(8)`` ids mapped to strong references (so a recycled Python id can never
validate) in a bounded LRU registry of ``MAX_REFS`` entries; evicted/unknown ids are refused.
Generation starts at a random positive number (a reloaded script never reuses one) and
increases on Song change or ``invalidate()`` (disconnect); the
registry and lease are cleared at the same moment. Liveness of Live objects is checked by
identity-or-equality membership inside try/except; any exception means "not valid".

Reference kinds (T-005). A reference is a root-to-leaf path of ``(kind, obj, snapshot)`` nodes;
``PARENTS`` fixes which kind may sit under which, and ``issue`` refuses any other shape. Every
level is re-checked on every use, so a reference refuses once its object (or any ancestor) is
deleted, moved or reordered:

- ``track``: at the issued index of ``song.tracks`` (pinned); a legacy snapshot without
  ``index`` only requires membership (regular or return track);
- ``return_track``: at the issued index of ``song.return_tracks``; ``master``: is
  ``song.master_track`` (pinned identity);
- ``scene``: at the issued index (legacy: membership); ``cue``: in ``song.cue_points`` at the
  issued ``time``;
- ``slot``/``clip``: the slot at its scene row with the issued scene there; the slot's clip;
- ``device`` (under a track, return, master or chain): at the issued index (legacy:
  membership) with the sibling layout (class names) unchanged; ``chain`` (under a rack device
  or a drum pad): at the issued index with the same chain count; ``drum_pad``: the pad at the
  issued ``drum_pads`` position with the same note and the same chains (a cleared or
  copied-over pad refuses);
- ``param``: at the issued index with the same name and parameter count; ``mixer_param``: the
  owner's ``mixer_device`` member named by a fixed role, or the send at the issued index with
  the same send count;
- ``take_lane``: at the issued index of ``track.take_lanes``; ``arr_clip``: in the parent's
  (track or take lane) ``arrangement_clips`` at the issued ``start_time``.

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
insecure config means read-only. It is re-read on every write dispatch. The same config's
``dev_probes`` (the JSON literal ``true`` only) enables the fixed dev probe table in ``dom_probe``.
"""

import collections
import hmac
import os
import secrets
import stat
import time
from types import SimpleNamespace

from . import (
    dom_arrangement,
    dom_automation,
    dom_browser,
    dom_clips,
    dom_common,
    dom_devices,
    dom_devx,
    dom_drums,
    dom_editing,
    dom_labels,
    dom_notes,
    dom_probe,
    dom_racks,
    dom_recording,
    dom_scenes,
    dom_session,
    dom_song,
    dom_tracks,
    dom_view,
)
from .core import _HEX, _decode, _windows_private
from .dom_common import (  # noqa: F401 - re-exported
    CAPABILITY_STATES,
    CONTROL,
    MIXER_ROLES,
    READ,
    WRITE,
    Refused,
    _same,
    same_items,
)

MAX_REFS = 1024
MAX_REF_LEN = 64
DEFAULT_LEASE_TTL = 30.0
MAX_LEASE_TTL = 60.0

# The fixed list of domain modules. Every bridge method is declared next to its handler in one of
# them; later tickets add methods to their own module, never to this list.
DOMAINS = (
    dom_common,
    dom_session,
    dom_tracks,
    dom_scenes,
    dom_clips,
    dom_notes,
    dom_devices,
    dom_browser,
    dom_drums,
    dom_racks,
    dom_arrangement,
    dom_automation,
    dom_recording,
    dom_editing,
    dom_song,
    dom_view,
    dom_devx,
    dom_labels,
    dom_probe,
)
# Executed by the gate itself (handlers.make_dispatch), never by a domain handler.
GATE_METHODS = {"lease_acquire": CONTROL, "lease_release": CONTROL}
# Reference kinds and the kinds each may sit under (None: a root, found from the Song).
PARENTS = {
    "track": (None,),
    "return_track": (None,),
    "master": (None,),
    "scene": (None,),
    "cue": (None,),
    "slot": ("track",),
    "clip": ("slot",),
    "device": ("track", "return_track", "master", "chain"),
    "chain": ("device", "drum_pad"),
    "drum_pad": ("device",),
    "param": ("device",),
    "mixer_param": ("track", "return_track", "master", "chain"),
    "take_lane": ("track",),
    "arr_clip": ("track", "take_lane"),
}
REFERENCE_KINDS = tuple(PARENTS)
# A list target spec ``(list_param, item_param, ANY_KIND)`` takes mixed kinds: each item names its
# own ``kind`` (one of REFERENCE_KINDS) and ``resolve`` still refuses a reference of another kind.
ANY_KIND = "any"
MAX_PATH_NODES = 24  # owner + 6 device levels (device, pad, chain) + leaf, with margin


class DeclarationError(RuntimeError):
    """A domain's METHODS table is malformed. Raised at import, so the gate never runs open."""


def _valid_spec(spec):
    """(param, kind) is a single reference; (list_param, item_param, kind) is a list of objects
    each carrying a reference."""
    return (
        isinstance(spec, tuple)
        and len(spec) in (2, 3)
        and all(isinstance(s, str) and s for s in spec)
        and (spec[-1] in REFERENCE_KINDS or (len(spec) == 3 and spec[-1] == ANY_KIND))
    )


def _merge(domains):
    """Build ``(CLASSIFICATION, TARGETS, HANDLERS)`` from the domains' ``METHODS``. Fails closed:
    a duplicate name, an unknown kind, a missing handler or a malformed target spec raises."""
    classification, targets, handlers = dict(GATE_METHODS), {}, {}
    for module in domains:
        methods = getattr(module, "METHODS", None)
        if not isinstance(methods, dict):
            raise DeclarationError(f"{module.__name__} must export a METHODS dict")
        for name, entry in methods.items():
            where = f"bridge method {name!r} in {module.__name__}"
            if not isinstance(name, str) or not name:
                raise DeclarationError(f"{where}: name must be a non-empty string")
            if name in classification:
                raise DeclarationError(f"duplicate {where}")
            if not isinstance(entry, tuple) or len(entry) != 3:
                raise DeclarationError(f"{where}: entry must be (handler, kind, targets)")
            handler, kind, spec = entry
            if not callable(handler):
                raise DeclarationError(f"{where}: handler is not callable")
            if kind == READ:
                if spec is not None:
                    raise DeclarationError(f"{where}: a read takes no targets (use None)")
            elif kind == WRITE:
                if not isinstance(spec, tuple) or not all(_valid_spec(s) for s in spec):
                    raise DeclarationError(f"{where}: malformed target spec {spec!r}")
                targets[name] = spec
            else:  # CONTROL is reserved for the gate's own lease methods
                raise DeclarationError(f"unclassified {where}: kind {kind!r}")
            classification[name] = kind
            handlers[name] = handler
    return classification, targets, handlers


def _merge_capabilities(domains):
    """Merge the optional ``CAPABILITIES = {name: (state, reason)}`` tables (dom_common's gate
    helpers read them through ``ctx.capabilities``). Fails closed like ``_merge``."""
    merged = {}
    for module in domains:
        table = getattr(module, "CAPABILITIES", {})
        if not isinstance(table, dict):
            raise DeclarationError(f"{module.__name__}.CAPABILITIES must be a dict")
        for name, entry in table.items():
            where = f"capability {name!r} in {module.__name__}"
            if not isinstance(name, str) or not name or name in merged:
                raise DeclarationError(f"duplicate or empty {where}")
            if (
                not isinstance(entry, tuple)
                or len(entry) != 2
                or entry[0] not in CAPABILITY_STATES
                or not isinstance(entry[1], str)
            ):
                raise DeclarationError(f"{where}: entry must be (state, reason)")
            merged[name] = entry
    return merged


# Every bridge method is classified; a method missing from CLASSIFICATION is refused (fail
# closed). TARGETS: a write with an empty tuple is a global operation (needs `generation`).
CLASSIFICATION, TARGETS, HANDLERS = _merge(DOMAINS)
CAPABILITIES = _merge_capabilities(DOMAINS)


def _read_config():
    """The shared config as a dict; None when it is missing, insecure or invalid (fail closed)."""
    try:
        path = os.environ.get("ABLETONLIVEMCP_CONFIG")
        if path is None:
            path = os.path.join(os.path.expanduser("~"), ".abletonlivemcp", "bridge.json")
        if not path or not os.path.isabs(path):
            return None
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode) or getattr(before, "st_file_attributes", 0) & 0x400:
            return None
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or (before.st_dev, before.st_ino) != (
                info.st_dev,
                info.st_ino,
            ):
                return None
            if os.name == "nt":
                _windows_private(stream.fileno(), path)
            elif info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                return None
            raw = stream.read(8193)
        if len(raw) > 8192:
            return None
        config = _decode(raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw)  # tolerate a BOM
        secret = config.get("secret") if isinstance(config, dict) else None
        if not isinstance(secret, str) or not _HEX.fullmatch(secret):
            return None
        return config
    except Exception:  # noqa: BLE001 - every failure must fail closed
        return None


def config_read_only():
    """True unless the shared config is valid, private and says ``"read_only": false``."""
    config = _read_config()
    return config is None or config.get("read_only") is not False


def config_dev_probes():
    """True only when the shared config is valid, private and says ``"dev_probes": true``."""
    config = _read_config()
    return config is not None and config.get("dev_probes") is True


PERMISSIONS = frozenset({"transport", "edit", "files", "delete"})


def config_permissions():
    """Same local capability contract as the host; invalid explicit lists grant nothing."""
    config = _read_config()
    if config is None:
        return frozenset()
    if "permissions" not in config:
        return PERMISSIONS  # backwards compatibility for existing private configurations
    value = config["permissions"]
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        return frozenset()
    return frozenset(value) if not set(value) - PERMISSIONS else frozenset()


def _any_item(params, key, field, value):
    items = params.get(key) if isinstance(params, dict) else None
    return isinstance(items, list) and any(
        isinstance(i, dict) and i.get(field) == value for i in items
    )


# Methods that delete only for some params also need "delete" then (host: permissions.DELETING).
DELETING = {
    "create_clips": lambda p: _any_item(p, "targets", "replace", True),
    "create_arrangement_clips": lambda p: _any_item(p, "targets", "replace", True),
    "set_cue_points": lambda p: _any_item(p, "cues", "action", "delete"),
}


def method_permissions(method, params=None):
    """Every local permission a write of ``method`` with ``params`` needs."""
    if method.startswith("delete_"):
        return frozenset({"delete"})
    if method in {
        "transport", "play", "stop", "launch", "fire_scene", "fire_clip", "view", "select"
    }:
        return frozenset({"transport"})
    test = DELETING.get(method)
    if test is not None and test(params or {}):
        return frozenset({"edit", "delete"})
    return frozenset({"edit"})


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


def _shape_ok(nodes):
    """Root first, each node under an allowed parent kind, dict snapshots, bounded depth."""
    if not isinstance(nodes, tuple) or not 0 < len(nodes) <= MAX_PATH_NODES:
        return False
    previous = None
    for node in nodes:
        if not isinstance(node, tuple) or len(node) != 3 or not isinstance(node[2], dict):
            return False
        if previous not in PARENTS.get(node[0], ()):
            return False
        previous = node[0]
    return True


def _alive(kind, song, parent, obj, snap):
    """One level of a reference: ``obj`` (of ``kind``) is still where it was issued under
    ``parent`` (the previous level's object; the Song for a root). Raising means invalid."""
    if kind == "track":
        if "index" in snap:
            return _at(song.tracks, snap["index"], obj)
        return _member(song.tracks, obj) or _member(getattr(song, "return_tracks", ()), obj)
    if kind == "return_track":
        return _at(song.return_tracks, snap["index"], obj)
    if kind == "master":
        return _same(song.master_track, obj)
    if kind == "scene":
        if "index" in snap:
            return _at(song.scenes, snap["index"], obj)
        return _member(song.scenes, obj)
    if kind == "cue":
        return _member(song.cue_points, obj) and obj.time == snap["time"]
    if kind == "slot":
        return _at(parent.clip_slots, snap["index"], obj) and _at(
            song.scenes, snap["index"], snap["scene"]
        )
    if kind == "clip":
        return bool(parent.has_clip) and _same(parent.clip, obj)
    if kind == "device":
        devices = parent.devices
        placed = _at(devices, snap["index"], obj) if "index" in snap else _member(devices, obj)
        return placed and snap["layout"] == tuple(d.class_name for d in devices)
    if kind == "chain":
        chains = parent.chains
        return len(chains) == snap["count"] and _at(chains, snap["index"], obj)
    if kind == "drum_pad":
        return (
            _at(parent.drum_pads, snap["slot"], obj)
            and obj.note == snap["note"]
            and same_items(tuple(obj.chains), snap["chains"])
        )
    if kind == "param":
        return (
            len(parent.parameters) == snap["count"]
            and _at(parent.parameters, snap["index"], obj)
            and obj.name == snap["name"]
        )
    if kind == "mixer_param":
        mixer, role = parent.mixer_device, snap["role"]
        if role == "send":
            sends = mixer.sends
            return len(sends) == snap["count"] and _at(sends, snap["index"], obj)
        return role in MIXER_ROLES and _same(getattr(mixer, role), obj)
    if kind == "take_lane":
        return _at(parent.take_lanes, snap["index"], obj)
    if kind == "arr_clip":
        return _member(parent.arrangement_clips, obj) and obj.start_time == snap["start"]
    return False


class Safety:
    def __init__(
        self,
        song_supplier,
        policy=config_read_only,
        clock=time.monotonic,
        dev_probes=config_dev_probes,
        permissions=None,
    ):
        self._supplier, self._policy, self._clock = song_supplier, policy, clock
        self._dev_probes = dev_probes
        # An injected policy is a complete test/embedding policy. Production uses the
        # private config for both switches; custom embedders can inject capabilities too.
        self._permissions = permissions or (
            config_permissions if policy is config_read_only else lambda: PERMISSIONS
        )
        self._song = None
        # Random start: Live reloads the script on a Set change and a fresh instance must never
        # share a generation with the previous one, or a stale client's number would match.
        self.generation = secrets.randbelow(2**30) + 1
        self._refs = collections.OrderedDict()
        self._lease = None  # (token, expires)
        # capability -> reason, closed after an unknown outcome (dom_common.quarantine); kept
        # for the life of this script instance, never reopened by a retry or a Set change.
        self.quarantined = {}

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
        """nodes: root-to-leaf tuples (kind, obj, snapshot dict). Returns the leaf's reference.
        A path whose shape breaks ``PARENTS`` is never issued (ValueError, fail closed)."""
        if not _shape_ok(nodes):
            raise ValueError("internal: malformed reference path")
        ref = secrets.token_hex(8)
        self._refs[ref] = (self.generation, tuple(nodes))
        while len(self._refs) > MAX_REFS:
            self._refs.popitem(last=False)
        return ref

    def _valid(self, song, nodes):
        if not _shape_ok(nodes):
            return False
        parent = song
        for kind, obj, snap in nodes:
            try:
                ok = _alive(kind, song, parent, obj, snap)
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
        # ``nodes``: kind -> innermost object of that kind; ``path``: every level, root first.
        return SimpleNamespace(obj=nodes[-1][1], nodes={n[0]: n[1] for n in nodes}, path=nodes)

    # ---- policy and lease ---------------------------------------------------------------
    def read_only(self):
        try:
            return self._policy() is not False
        except Exception:  # noqa: BLE001
            return True

    def dev_probes_enabled(self):
        """Dev probes (``dom_probe``) run only when the config says ``"dev_probes": true``."""
        try:
            return self._dev_probes() is True
        except Exception:  # noqa: BLE001
            return False

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
    def check_policy(self, method, params):
        """Checks 1-2 (read_only switch, local permissions), read fresh from the config. The
        write gate runs it per call; deferred operations rerun it before every later step."""
        if self.read_only():
            raise Refused("read_only", "bridge is read-only; enable writes in the local config")
        missing = method_permissions(method, params) - self._permissions()
        if missing:
            needed = ", ".join(sorted(missing))
            raise Refused("permission_denied", f"{method} requires local permission {needed}")

    def authorize(self, method, params):
        """Run checks 1-4 for a write; return resolved targets by param name. Raises Refused."""
        self.check_policy(method, params)
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
                resolved = self.resolve(spec[1], params.get(spec[0]), song)
                if len(specs) == 1:  # the single target may carry the request's expect_name
                    _expect_name(resolved, params.get("expect_name"), spec[0])
                targets[spec[0]] = resolved
            else:
                items = params.get(spec[0])
                if (
                    not isinstance(items, list)
                    or len(items) > 64
                    or not all(isinstance(i, dict) for i in items)
                ):
                    raise ValueError(f"{spec[0]!r} must be a list of objects")
                out = []
                for n, item in enumerate(items):
                    kind = item.get("kind") if spec[2] == ANY_KIND else spec[2]
                    if kind not in REFERENCE_KINDS:
                        raise ValueError(f"{spec[0]}[{n}].kind must be one of {REFERENCE_KINDS}")
                    resolved = self.resolve(kind, item.get(spec[1]), song)
                    _expect_name(resolved, item.get("expect_name"), f"{spec[0]}[{n}]")
                    out.append(resolved)
                targets[spec[0]] = out
        return targets


def _expect_name(resolved, expected, where):
    """Exact-name check at the gate: every target is checked before the handler (any write)."""
    if expected is None:
        return
    if not isinstance(expected, str):
        raise ValueError(f"{where}.expect_name must be a string")
    try:
        actual = resolved.obj.name
    except Exception:  # noqa: BLE001
        actual = None
    if actual != expected:
        raise Refused(
            "name_mismatch", f"{where}: expected {expected!r} but the object is named {actual!r}"
        )
