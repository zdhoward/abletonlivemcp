"""Toolset `files`: MIDI file import/export through the host SMF codec (``midi_file``).

Paths are confined to file roots: ``ABLETONLIVEMCP_FILE_ROOTS`` (os.pathsep-separated) or, by
default, the user's home and the temp directory. Export writes new files only.
"""

from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path
from typing import Annotated

from pydantic import Field

from .. import midi_file
from ..models import ClipRef, Index
from ..server import _call, _create, clip_selector, issue_refs

NOTE_PAGE = 1000


def file_roots() -> list[Path]:
    raw = os.environ.get("ABLETONLIVEMCP_FILE_ROOTS")
    roots = raw.split(os.pathsep) if raw else [str(Path.home()), tempfile.gettempdir()]
    return [Path(r).resolve() for r in roots if r.strip()]


def confined(path: str, suffixes=(".mid", ".midi")) -> Path:
    """An absolute, resolved path inside a file root with a MIDI suffix (ValueError otherwise)."""
    p = Path(path)
    if not p.is_absolute():
        raise ValueError("'file' must be an absolute path")
    p = p.resolve()
    if p.suffix.lower() not in suffixes:
        raise ValueError(f"'file' must end with one of {list(suffixes)}")
    if not any(p == r or r in p.parents for r in file_roots()):
        raise ValueError(
            f"'file' is outside the allowed roots ({os.pathsep.join(map(str, file_roots()))})"
        )  # noqa: E501
    return p


def _row(n: midi_file.MidiNote) -> dict:
    return {
        "pitch": n.pitch,
        "start_time": round(n.start_time, 6),
        "duration": round(n.duration, 6),
        "velocity": float(n.velocity),
    }


@_create
def live_import_midi(
    file: str,
    track: Index,
    scene: Index | None = None,
    start: Annotated[float, Field(ge=0, le=16384)] | None = None,
    length: Annotated[float, Field(gt=0, le=1024)] | None = None,
    name: Annotated[str, Field(max_length=256)] | None = None,
) -> dict:
    """Import a .mid (SMF 0/1, all tracks merged, 2000 notes max) as a new MIDI clip: in the
    empty Session slot `scene`, or in the arrangement at `start` beats. Length defaults to the
    notes rounded up to a bar."""
    if (scene is None) == (start is None):
        raise ValueError("give exactly one of 'scene' (Session) or 'start' (arrangement)")
    path = confined(file)
    if not path.is_file():
        raise ValueError(f"no such file: {path}")
    if path.stat().st_size > midi_file.MAX_BYTES:
        raise ValueError(f"file larger than {midi_file.MAX_BYTES} bytes")
    content = midi_file.parse(path.read_bytes())
    if not content.notes:
        raise ValueError("the file holds no notes")
    end = max(n.start_time + n.duration for n in content.notes)
    size = length or min(1024.0, max(4.0, math.ceil(end / 4.0) * 4.0))
    item = {"kind": "midi", "length": size, "notes": [_row(n) for n in content.notes]}
    if name is not None:
        item["name"] = name
    if scene is not None:
        ref = issue_refs([{"kind": "slot", "track": track, "scene": scene}])[0]
        out = _call("create_clips", {"targets": [{"ref": ref["ref"], **item}]})
    else:
        ref = issue_refs([{"kind": "track", "track": track}])[0]
        out = _call(
            "create_arrangement_clips", {"targets": [{"ref": ref["ref"], "start": start, **item}]}
        )  # noqa: E501
    out["file"] = {
        "notes": len(content.notes),
        "truncated": content.truncated,
        "format": content.format,
        "tracks": content.tracks,
        "tempo_bpm": content.tempo_bpm,
        "time_signature": content.time_signature,
    }
    return out


@_create
def live_export_midi(clip: ClipRef, file: str) -> dict:
    """Export a MIDI clip's notes (from beat 0 of the clip, Set tempo and signature) to a NEW
    .mid file (SMF 0; an existing file refuses)."""
    path = confined(file)
    clip_selector(clip)
    if path.exists():
        raise ValueError(f"{path} exists; export writes new files only")
    if not path.parent.is_dir():
        raise ValueError(f"no such directory: {path.parent}")
    notes, offset = [], 0
    while offset is not None and len(notes) < midi_file.MAX_NOTES:
        page = _call(
            "get_notes",
            {**clip.model_dump(exclude_none=True), "time_from": 0.0, "time_span": 16384.0,
             "limit": NOTE_PAGE, "offset": offset},
        )  # fmt: skip
        notes += page["notes"]
        offset = page["next_offset"]
    if offset is not None:
        raise ValueError(f"the clip holds more than {midi_file.MAX_NOTES} notes")
    session = _call("session_info")
    sig = session.get("signature")
    audible = [n for n in notes if not n.get("mute")]
    data = midi_file.encode(
        audible, tempo_bpm=session.get("tempo"), time_signature=tuple(sig) if sig else None
    )
    with open(path, "xb") as fh:  # x: never overwrite
        fh.write(data)
    skipped = len(notes) - len(audible)
    return {"file": str(path), "notes": len(audible), "muted_skipped": skipped, "bytes": len(data)}
