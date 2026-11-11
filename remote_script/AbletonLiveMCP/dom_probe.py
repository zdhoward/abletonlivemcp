"""Dev probe domain (T-003): a fixed table of probe functions for settling Live API questions.

Probes are developer instruments, never MCP tools (the server registers no tool for them). Each
probe is one fixed function in its own flat module ``probe_pNN.py`` (flat so the installer copies
it), declaring ``PROBE_ID = "P-NN"``, ``KIND`` (``read`` or ``write``) and ``run(ctx, scratch)``.
A request names a probe by its id; the id is only a key into ``PROBES``, never an attribute name,
and no request argument reaches a probe (there is no argument-driven attribute access).

Bridge methods (every one refused unless the private config says ``"dev_probes": true``):

- ``probe_list`` (read): the probe ids and their kinds.
- ``probe_read(name)`` (read): runs an introspection probe; it must not change the Set.
- ``probe_run(name)`` (write, global): runs a behavioural probe. The gate first requires writes
  enabled and the current ``generation`` and checks any lease token (``safety.authorize``); the
  handler then requires a lease token, which the gate has matched. The probe receives a
  ``Scratch`` that creates tracks/scenes at the end of the Set and records them; a probe touches
  only objects it created through it. Its scratch objects are deleted afterwards, each only if it
  is still the identical object.

The kinds are disjoint: ``probe_read`` refuses a write probe and ``probe_run`` a read probe. The
table is built at import and fails closed: a missing or wrong id, a duplicate id, an unknown kind
or a missing ``run`` raises ``ProbeTableError``, so the Remote Script does not load at all.
Release archives omit the ``probe_pNN`` modules; the table is then empty and every probe id
is refused. A partial set of probe modules also raises ``ProbeTableError``.
A refusal happens before any probe code runs; an exception inside a probe is reported in the
result (``ok: false``) after its scratch cleanup, never as a refusal.
"""

import importlib

from .dom_common import READ, WRITE, Refused, _same

# The fixed probe list (plan section 4). P-21, P-25 and P-26 are not used; P-28 has no row.
PROBE_NUMBERS = (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 27, 29,
)  # fmt: skip
SCRATCH_LIMIT = 8  # max scratch objects one probe run may create


class ProbeTableError(RuntimeError):
    """A probe module is malformed. Raised at import, so no probe can run unclassified."""


def _table(modules):
    table = {}
    for module in modules:
        name = module.__name__.rsplit(".", 1)[-1]
        pid = getattr(module, "PROBE_ID", None)
        kind = getattr(module, "KIND", None)
        run = getattr(module, "run", None)
        if not isinstance(pid, str) or len(pid) != 4 or name != f"probe_p{pid[2:]}":
            raise ProbeTableError(f"{name}: PROBE_ID {pid!r} must be 'P-NN' matching the file")
        if not pid.startswith("P-") or not pid[2:].isdigit():
            raise ProbeTableError(f"{name}: PROBE_ID {pid!r} must be 'P-NN'")
        if pid in table:
            raise ProbeTableError(f"duplicate probe {pid} in {name}")
        if kind not in (READ, WRITE):
            raise ProbeTableError(f"unclassified probe {pid}: kind {kind!r}")
        if not callable(run):
            raise ProbeTableError(f"probe {pid} has no run function")
        table[pid] = (run, kind)
    return table


def _load_probe_modules():
    """The probe modules are a development add-on: release archives omit all of them, the
    source tree has all of them. A partial set is a broken copy and fails closed."""
    found, missing = [], []
    for number in PROBE_NUMBERS:
        name = f"probe_p{number:02d}"
        try:
            found.append(importlib.import_module("." + name, __package__))
        except ModuleNotFoundError as exc:
            if exc.name != f"{__package__}.{name}":
                raise  # the probe exists but one of its own imports is missing
            missing.append(name)
    if found and missing:
        raise ProbeTableError("incomplete probe set; missing " + ", ".join(missing))
    return tuple(found)


PROBE_MODULES = _load_probe_modules()
PROBES = _table(PROBE_MODULES)


class Scratch:
    """Creates scratch tracks and scenes at the end of the Set and remembers exactly those."""

    def __init__(self, song):
        self._song = song
        self.created = []  # (kind, obj) in creation order

    def _create(self, kind, seq_name, make):
        if len(self.created) >= SCRATCH_LIMIT:
            raise RuntimeError(f"a probe may create at most {SCRATCH_LIMIT} scratch objects")
        before = list(getattr(self._song, seq_name))
        make()
        new = [o for o in getattr(self._song, seq_name) if not any(_same(o, b) for b in before)]
        if len(new) != 1:
            raise RuntimeError(f"could not identify the new scratch {kind}")
        self.created.append((kind, new[0]))
        return new[0]

    def midi_track(self):
        return self._create("track", "tracks", lambda: self._song.create_midi_track(-1))

    def audio_track(self):
        return self._create("track", "tracks", lambda: self._song.create_audio_track(-1))

    def scene(self):
        return self._create("scene", "scenes", lambda: self._song.create_scene(-1))

    def owns(self, obj):
        return any(_same(obj, o) for _k, o in self.created)

    def cleanup(self):
        """Delete each scratch object (newest first) only if it is still in the Set."""
        report = []
        for kind, obj in reversed(self.created):
            seq_name, delete = (
                ("tracks", self._song.delete_track)
                if kind == "track"
                else ("scenes", self._song.delete_scene)
            )
            try:
                seq = list(getattr(self._song, seq_name))
                index = next((i for i, o in enumerate(seq) if _same(o, obj)), None)
                if index is None:
                    report.append({"kind": kind, "deleted": False, "reason": "gone"})
                    continue
                delete(index)
                report.append({"kind": kind, "deleted": True})
            except Exception as exc:  # noqa: BLE001 - report, keep cleaning the rest
                report.append({"kind": kind, "deleted": False, "reason": _error(exc)})
        self.created = []
        return report


def _error(exc):
    return f"{type(exc).__name__}: {exc}"[:500]


def _lookup(ctx, p, kind):
    """Refusals only (nothing runs yet): dev_probes off, unknown id, wrong method for the kind."""
    if not ctx.safety.dev_probes_enabled():
        raise Refused(
            "dev_probes_disabled", 'dev probes are off; set "dev_probes": true in the config'
        )
    name = p["name"]
    entry = PROBES.get(name) if isinstance(name, str) else None
    if entry is None:
        raise Refused("unknown_probe", "unknown probe id; see probe_list")
    run, probe_kind = entry
    if probe_kind != kind:
        method = "probe_run" if probe_kind == WRITE else "probe_read"
        raise Refused("wrong_probe_kind", f"probe {name} is a {probe_kind} probe; use {method}")
    return name, run


def probe_list(ctx, _p):
    if not ctx.safety.dev_probes_enabled():
        raise Refused(
            "dev_probes_disabled", 'dev probes are off; set "dev_probes": true in the config'
        )
    return {"probes": {pid: kind for pid, (_run, kind) in sorted(PROBES.items())}}


def probe_read(ctx, p):
    name, run = _lookup(ctx, p, READ)
    try:
        return {"probe": name, "kind": READ, "ok": True, "result": run(ctx, None)}
    except Exception as exc:  # noqa: BLE001 - a probe failure is a finding, not a crash
        return {"probe": name, "kind": READ, "ok": False, "error": _error(exc)}


def probe_run(ctx, p, _t):
    name, run = _lookup(ctx, p, WRITE)
    # The gate refuses a token that does not match the live lease, but lets a request with no
    # token through while no lease is held; a behavioural probe always requires one.
    if p.get("lease") is None:
        raise Refused("lease_required", "a behavioural probe runs only under the lease")
    scratch = Scratch(ctx.song)
    out = {"probe": name, "kind": WRITE}
    try:
        out.update(ok=True, result=run(ctx, scratch))
    except Exception as exc:  # noqa: BLE001 - a probe failure is a finding, not a crash
        out.update(ok=False, error=_error(exc))
    finally:
        out["scratch"] = scratch.cleanup()
    return out


METHODS = {
    "probe_list": (probe_list, READ, None),
    "probe_read": (probe_read, READ, None),
    "probe_run": (probe_run, WRITE, ()),
}
