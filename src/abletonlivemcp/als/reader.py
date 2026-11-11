"""Offline reader for Ableton Live Set (.als) files.

An .als file is gzip-compressed XML. The structure here is reverse engineered, not an
official schema, so everything is defensive: unknown nodes are ignored, missing fields
become None, and nothing is ever written back.

The XML is parsed incrementally with expat, never with an entity-expanding parser: a DOCTYPE or
ENTITY declaration is refused by the parser itself, and the compressed size, decompressed size,
node count and nesting depth are all capped (a Set that exceeds a cap is reported as unreadable,
not truncated). Text content is dropped; the reader only needs tags and attributes.

Samples found in a Set are *references*, not proof of audible use (see UsageLevel).
"""

from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
import zlib
from collections.abc import Iterator, Sequence
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from xml.parsers import expat

from .paths import PathEscape, open_confined

MAX_GZIP_BYTES = 50 * 1024 * 1024  # compressed file size
MAX_XML_BYTES = 256 * 1024 * 1024  # decompression bomb guard
MAX_NODES = 3_000_000  # elements in one Set (the parsed tree stays in memory)
MAX_DEPTH = 128  # element nesting; the walk below is recursive
_CHUNK = 1024 * 1024

TRACK_TAGS = {"MidiTrack", "AudioTrack", "ReturnTrack", "GroupTrack", "MainTrack", "PreHearTrack"}


class AlsError(Exception):
    """The file could not be read as a Live Set."""


@dataclass(frozen=True)
class DeviceUse:
    device_class: str  # XML tag, e.g. "Reverb", "PluginDevice", "DrumGroupDevice"
    track: str | None
    user_name: str | None = None
    plugin_format: str | None = None  # "vst2" | "vst3" | None
    plugin_name: str | None = None


@dataclass(frozen=True)
class SampleRefUse:
    path: str | None
    relative_path: str | None
    track: str | None
    device_class: str | None
    classification: Literal["referenced", "potentially_triggered"] = "referenced"
    original_file_size: int | None = None


@dataclass
class SetSummary:
    path: Path
    creator: str | None = None
    major_version: str | None = None
    minor_version: str | None = None
    tracks: list[str] = field(default_factory=list)
    devices: list[DeviceUse] = field(default_factory=list)
    samples: list[SampleRefUse] = field(default_factory=list)


def _val(el: ET.Element | None, tag: str) -> str | None:
    if el is None:
        return None
    child = el.find(tag)
    return None if child is None else child.get("Value")


def _track_name(track: ET.Element) -> str | None:
    name = track.find("Name")
    return _val(name, "UserName") or _val(name, "EffectiveName")


def _plugin_info(device: ET.Element) -> tuple[str | None, str | None]:
    desc = device.find("PluginDesc")
    if desc is None:
        return None, None
    vst2 = desc.find("VstPluginInfo")
    if vst2 is not None:
        return "vst2", _val(vst2, "PlugName")
    vst3 = desc.find("Vst3PluginInfo")
    if vst3 is not None:
        return "vst3", _val(vst3, "Name")
    return None, None


def _parse_chunks(chunks: Iterator[bytes]) -> ET.Element:
    """Build the element tree (tags and attributes only) from byte chunks under the caps."""
    parser = expat.ParserCreate()
    stack: list[ET.Element] = []
    seen = {"nodes": 0}
    root: list[ET.Element] = []

    def start(tag: str, attrs: dict) -> None:
        seen["nodes"] += 1
        if seen["nodes"] > MAX_NODES:
            raise AlsError(f"Set has more than {MAX_NODES} XML elements")
        if len(stack) >= MAX_DEPTH:
            raise AlsError(f"Set nests XML elements deeper than {MAX_DEPTH}")
        element = ET.Element(tag, attrs)
        if stack:
            stack[-1].append(element)
        elif not root:
            root.append(element)
        stack.append(element)

    def end(_tag: str) -> None:
        stack.pop()

    def refuse(*_args) -> None:
        raise AlsError("DTD/entity declarations are not allowed in Live Sets")

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.StartDoctypeDeclHandler = refuse
    parser.EntityDeclHandler = refuse
    parser.ExternalEntityRefHandler = refuse
    try:
        for chunk in chunks:
            parser.Parse(chunk, False)
        parser.Parse(b"", True)
    except expat.ExpatError as exc:
        raise AlsError(f"invalid XML: {exc}") from exc
    return root[0]


def _bytes_in(chunks: Iterator[bytes]) -> Iterator[bytes]:
    total = 0
    for chunk in chunks:
        total += len(chunk)
        if total > MAX_XML_BYTES:
            raise AlsError(f"Set decompresses to more than {MAX_XML_BYTES} bytes")
        yield chunk


def parse_xml_bytes(data: bytes, path: Path | None = None) -> SetSummary:
    """Parse already-decompressed Set XML. Rejects DTDs/entities outright."""
    return _summarize(_parse_chunks(_bytes_in(iter([data]))), path)


def _summarize(root: ET.Element, path: Path | None) -> SetSummary:
    if root.tag != "Ableton":
        raise AlsError(f"not a Live Set (root element is {root.tag!r})")
    summary = SetSummary(
        path=path or Path("<memory>"),
        creator=root.get("Creator"),
        major_version=root.get("MajorVersion"),
        minor_version=root.get("MinorVersion"),
    )
    live_set = root.find("LiveSet")
    if live_set is None:
        raise AlsError("Set has no LiveSet element")
    _walk(live_set, summary, track=None, device_class=None)
    return summary


def _integer(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _midi_notes(track: ET.Element) -> frozenset[int]:
    notes = set()
    for clip in track.iter("MidiClip"):
        if _val(clip, "Disabled") == "true":
            continue
        for key in clip.iter("KeyTrack"):
            pitch = _integer(_val(key, "MidiKey"))
            for event in key.iter("MidiNoteEvent"):
                try:
                    audible = float(event.get("Velocity", "100")) > 0
                except ValueError:
                    audible = False
                if pitch is not None and audible and event.get("IsEnabled", "true") != "false":
                    notes.add(pitch)
    return frozenset(notes)


def _sample_use(
    sample: ET.Element, track: str | None, device_class: str | None, evidence: bool
) -> SampleRefUse | None:
    ref = sample.find("FileRef")
    if ref is None:
        return None
    relative = _val(ref, "RelativePath")
    if relative is None:
        parts = [el.get("Dir", "") for el in ref.findall("RelativePath/RelativePathElement")]
        relative = "/".join(parts) or None
    name = _val(ref, "Name")
    if name and (not relative or relative.replace("\\", "/").rsplit("/", 1)[-1] != name):
        directory = relative.rstrip("/\\") if relative else ""
        relative = f"{directory}/{name}" if directory else name
    path = _val(ref, "Path") or relative or None
    if not path:
        return None  # Empty sampler slots have no sample to count.
    size = _integer(_val(sample, "OriginalFileSize") or _val(ref, "OriginalFileSize"))
    sampler = device_class in {
        "OriginalSimpler",
        "Simpler",
        "DrumCell",
        "MultiSampler",
        "DrumGroupDevice",
    }
    return SampleRefUse(
        path=path,
        relative_path=relative or None,
        track=track,
        device_class=device_class,
        classification="potentially_triggered" if sampler and not evidence else "referenced",
        original_file_size=size if size is not None and size >= 0 else None,
    )


def _walk(
    node: ET.Element,
    out: SetSummary,
    track: str | None,
    device_class: str | None,
    midi_notes: frozenset[int] = frozenset(),
    evidence: bool = False,
) -> None:
    for child in node:
        tag = child.tag
        if tag in TRACK_TAGS:
            name = _track_name(child)
            if name:
                out.tracks.append(name)
            notes = _midi_notes(child)
            _walk(child, out, name, None, notes, bool(notes))
            continue
        if tag == "DrumBranch":
            note = _integer(_val(child, ".//ReceivingNote"))
            _walk(child, out, track, device_class, midi_notes, note in midi_notes)
            continue
        if tag == "AudioClip":
            _walk(child, out, track, None, midi_notes, True)
            continue
        if node.tag == "Devices":
            fmt, plug = _plugin_info(child) if tag == "PluginDevice" else (None, None)
            out.devices.append(
                DeviceUse(
                    device_class=tag,
                    track=track,
                    user_name=_val(child, "UserName") or None,
                    plugin_format=fmt,
                    plugin_name=plug,
                )
            )
            _walk(child, out, track, tag, midi_notes, evidence and tag != "DrumGroupDevice")
            continue
        if tag == "SampleRef":
            sample = _sample_use(child, track, device_class, evidence)
            if sample is not None:
                out.samples.append(sample)
            continue
        _walk(child, out, track, device_class, midi_notes, evidence)


def read_set(path: str | Path, roots: Sequence[str | Path] | None = None) -> SetSummary:
    """Read and summarize one .als file.

    With ``roots`` the path must lie under one of them (absolute, no ``..``, no symlink, junction
    or reparse point, opened once and checked); the tools always pass them. Without ``roots``
    the caller vouches for the path (tests, trusted local use)."""
    p = Path(path)
    try:
        with ExitStack() as stack:
            if roots is None:
                if p.stat().st_size > MAX_GZIP_BYTES:
                    raise AlsError(f"{p.name} is larger than {MAX_GZIP_BYTES} bytes")
                fh = stack.enter_context(gzip.open(p, "rb"))
            else:
                raw, info = open_confined(p, roots)
                stack.enter_context(raw)
                if info.st_size > MAX_GZIP_BYTES:
                    raise AlsError(f"{p.name} is larger than {MAX_GZIP_BYTES} bytes")
                fh = stack.enter_context(gzip.GzipFile(fileobj=raw, mode="rb"))
            chunks = iter(lambda: fh.read(_CHUNK), b"")
            return _summarize(_parse_chunks(_bytes_in(chunks)), p)
    except PathEscape as exc:
        raise AlsError(f"refused {p.name}: {exc}") from exc
    except (OSError, EOFError, zlib.error) as exc:
        raise AlsError(f"cannot read {p.name}: {exc}") from exc
