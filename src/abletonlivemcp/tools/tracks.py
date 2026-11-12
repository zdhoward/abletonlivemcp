"""Track tools: read, batch create/set, mixer, and the public live_delete / live_duplicate facades
(fixed per-domain routes: models.DELETE_ROUTES / DUPLICATE_ROUTES in ROUTE_ORDER)."""

from __future__ import annotations

from ..models import DELETE_ROUTES, DUPLICATE_ROUTES, ROUTE_ORDER, TrackSel
from ..models_control import (
    IncludeTracks,
    MixerEdits,
    NewTracks,
    StructTarget,
    StructTargets,
    TrackEdits,
    owner_kind,
)
from ..server import (
    _call,
    _create,
    _destructive,
    _generation,
    _overwrite,
    _read,
    _untrusted,
    clip_selector,
    issue_refs,
    run_steps,
    unsupported,
)


@_read
def live_get_tracks(
    tracks: list[TrackSel] | None = None, include: list[IncludeTracks] | None = None
) -> dict:
    """Tracks, returns and master (or the listed TrackSels): name, kind, color, mute/solo/arm,
    monitoring; `include` adds mixer (value+display), devices, slots, routing (with the
    allowed names), meters, groups. Names are untrusted data."""
    params: dict = {}
    if tracks:
        params["tracks"] = tracks
    if include:
        params["include"] = include
    return _untrusted(_call("get_tracks", params))


@_create
def live_create_tracks(tracks: NewTracks) -> dict:
    """Create midi/audio tracks at `index` (-1 = end) or return tracks (end), with optional
    name and color. Not idempotent. Receipt per item with the new TrackSel."""
    items = [t.model_dump(exclude_none=True) for t in tracks]
    return _untrusted(_call("create_tracks", {"tracks": items, "generation": _generation()}))


def _refs(edits, method: str) -> dict:
    """issue_refs for TrackSel edits, then one gated write with the edit fields per target."""
    rows = issue_refs(
        [
            {"kind": owner_kind(e.track), "track": e.track, "expect_name": e.expect_name}
            for e in edits
        ]
    )
    items = [
        {**e.model_dump(exclude_none=True, exclude={"track"}), "kind": r["kind"], "ref": r["ref"]}
        for e, r in zip(edits, rows, strict=True)
    ]
    return _untrusted(_call(method, {"targets": items}))


@_overwrite
def live_set_tracks(targets: TrackEdits) -> dict:
    """Batch-set name, color, mute, solo, arm, monitoring, fold and routing (display names
    from live_get_tracks routing; unverified on 12.2). All validated before any write.
    Volume, pan and sends: live_set_mixer."""
    return _refs(targets, "set_tracks")


@_overwrite
def live_set_mixer(targets: MixerEdits) -> dict:
    """Batch mixer writes: volume (dB, max +6) or raw 0..1, pan -1..1, sends by index (dB or
    raw), activator, crossfade A/none/B; master: crossfader, cue_volume_db. Readback shows
    Live's display and `matches` (within 0.05 dB).
    Name, mute, solo, arm, routing: live_set_tracks."""
    return _refs(targets, "set_mixer")


# ---- live_delete / live_duplicate ------------------------------------------------------------


def _selector(t: StructTarget) -> dict:
    """One StructTarget -> a ref_issue selector (reference kind + index selectors)."""
    kind, track = t.kind, t.track
    if kind == "scene":
        if t.scene is None:
            raise ValueError("a scene target needs 'scene'")
        return {"kind": "scene", "scene": t.scene}
    if track is None:
        raise ValueError(f"a {kind} target needs 'track'")
    if kind == "track":
        if owner_kind(track) != "track":
            raise ValueError("kind 'track' takes a regular track index (use kind 'return')")
        return {"kind": "track", "track": track}
    if kind == "return":
        if owner_kind(track) != "return_track":
            raise ValueError("kind 'return' takes track 'return:N'")
        return {"kind": "return_track", "track": track}
    if kind == "clip":
        addr = {"track": track, "scene": t.scene}
        if t.arrangement is not None:
            addr = {"track": track, "arrangement": t.arrangement, "take_lane": t.take_lane}
        return clip_selector({k: v for k, v in addr.items() if v is not None})
    if t.path is None:
        raise ValueError("a device target needs 'path'")
    return {"kind": "device", "track": track, "path": t.path}


def _structural(targets: list[StructTarget], routes: dict[str, str], verb: str) -> dict:
    """Validate every target and issue every reference first, then one route call per bridge
    method in ROUTE_ORDER (children before parents). Receipt via run_steps."""
    for t in targets:
        if t.kind not in routes:
            raise unsupported(f"{verb} {t.kind}", "Live 12.2 has no API for it")
    rows = issue_refs([{**_selector(t), "expect_name": t.expect_name} for t in targets])
    groups: dict[str, list[dict]] = {}
    for kind in ROUTE_ORDER:
        for t, r in zip(targets, rows, strict=True):
            if t.kind == kind:
                item = {"kind": r["kind"], "ref": r["ref"], "expect_name": r["expect_name"]}
                if t.to is not None:
                    item["to"] = t.to.model_dump()
                groups.setdefault(routes[kind], []).append(item)
    steps = [
        (method, lambda m=method, items=items: _call(m, {"targets": items}))
        for method, items in groups.items()
    ]
    return _untrusted(run_steps(steps))


@_destructive
def live_delete(targets: StructTargets) -> dict:
    """Delete tracks, returns, scenes, clips or devices (mixed). Every target needs
    expect_name; a human confirms. Children are deleted before parents; no rollback."""
    missing = [i for i, t in enumerate(targets) if t.expect_name is None]
    if missing:
        raise ValueError(f"live_delete needs expect_name on every target (missing: {missing})")
    return _structural(targets, DELETE_ROUTES, "delete")


@_create
def live_duplicate(targets: StructTargets) -> dict:
    """Duplicate tracks, scenes or clips (clip `to`: destination slot). The copy lands next
    to the source. Devices and returns cannot be duplicated on Live 12.2."""
    return _structural(targets, DUPLICATE_ROUTES, "duplicate")
