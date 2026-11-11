"""Toolset `organize`: your own labels (free tags + one category) on Set and library items.

Track, return-track and Set labels live inside the Set (Live's data store; they travel with the
file once it is saved). Plugin, device and sample labels live in a global sidecar file in the
private data directory and apply across Sets. Native Live tags and colours of plugins are not
reachable through the API.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .. import labelstore
from ..models_library import (
    SET_KINDS,
    TRACK_KINDS,
    LabelFilter,
    LabelItem,
    LabelKind,
    LabelMode,
)
from ..server import _call, _generation, _overwrite, _read, _untrusted, issue_refs, run_steps


def _selector(item: LabelItem) -> dict:
    track = item.key if item.kind == "track" else f"return:{item.key}"
    return {"kind": item.kind, "track": track, "expect_name": item.expect_name}


def _wanted(filters: LabelFilter, entry: dict | None) -> bool:
    if entry is None:
        return False
    return filters.label is None or filters.label in entry.get("labels", [])


@_read
def live_get_labels(
    scope: Literal["set", "global", "both"] = "both",
    kind: LabelKind | None = None,
    label: Annotated[str | None, Field(max_length=40)] = None,
) -> dict:
    """Your labels. `scope` set (Song, tracks, returns, from the open Set), global (plugins,
    devices, samples, from the sidecar) or both; `kind` and `label` filter. Text is untrusted."""
    filters = LabelFilter(scope=scope, kind=kind, label=label)
    out: dict = {"scope": filters.scope}
    if filters.scope in ("set", "both"):
        data = _call("get_labels")
        rows = []
        if data["song"] is not None:
            rows.append({"kind": "song", "key": None, "name": None, **data["song"]})
        rows += [
            {"kind": r["kind"], "key": r["index"], "name": r["name"], **(r["labels"] or {})}
            for r in data["tracks"]
            if r["labels"] is not None
        ]
        out["set"] = [
            r
            for r in rows
            if (filters.kind is None or r["kind"] == filters.kind) and _wanted(filters, r)
        ]
        out["corrupt"] = data["corrupt"]
        out["unverified"] = data.get("unverified", [])
    if filters.scope in ("global", "both"):
        store = labelstore.load()["entries"]
        out["global"] = [
            {"kind": k, "key": key, **entry}
            for k, table in sorted(store.items())
            if filters.kind is None or filters.kind == k
            for key, entry in sorted(table.items())
            if _wanted(filters, entry)
        ]
    return _untrusted(out)


@_overwrite
def live_set_labels(
    items: Annotated[list[LabelItem], Field(min_length=1, max_length=64)],
    mode: LabelMode = "replace",
) -> dict:
    """Set labels in one call. Items: `song` (no key), `track`/`return_track` (key = index,
    optional expect_name), `plugin`/`device`/`sample` (key = usage key). `mode` replace (empty
    labels and no category clear it), add or remove. Set labels are written first, the sidecar
    last; later failures return a receipt, with no rollback."""
    seen = set()
    for n, item in enumerate(items):
        ident = (item.kind, item.key)
        if ident in seen:
            raise ValueError(f"items[{n}] repeats {item.kind} {item.key!r}")
        seen.add(ident)
    tracks = [i for i in items if i.kind in TRACK_KINDS]
    song = [i for i in items if i.kind == "song"]
    globals_ = [i for i in items if i.kind not in SET_KINDS]
    steps: list = []
    if tracks:
        rows = issue_refs([_selector(i) for i in tracks])  # reads only: raises before any write
        payload = [
            {
                "kind": i.kind,
                "ref": row["ref"],
                "expect_name": row["expect_name"],
                "labels": i.labels,
                "category": i.category,
            }
            for i, row in zip(tracks, rows, strict=True)
        ]
        steps.append(
            (
                f"track labels ({len(payload)})",
                lambda: _call("set_track_labels", {"items": payload, "mode": mode}),
            )
        )
    if song:
        body = {"labels": song[0].labels, "category": song[0].category}
        steps.append(
            (
                "song labels",
                lambda: _call(
                    "set_song_labels", {"item": body, "mode": mode, "generation": _generation()}
                ),
            )
        )
    if globals_:
        entries = [
            {"kind": i.kind, "key": i.key, "labels": i.labels, "category": i.category}
            for i in globals_
        ]
        steps.append((f"global labels ({len(entries)})", lambda: labelstore.apply(entries, mode)))
    return run_steps(steps)
