"""Offline reader for Ableton Live Set (.als) files.

An .als file is gzip-compressed XML. The structure here is reverse engineered, not an
official schema (see docs/research-deep-review.md), so everything is defensive: unknown
nodes are ignored, missing fields become None, and nothing is ever written back.

Samples found in a Set are *references*, not proof of audible use (see UsageLevel in
docs/research-deep-review.md section 5).
"""

from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

MAX_XML_BYTES = 512 * 1024 * 1024  # decompression bomb guard

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


def parse_xml_bytes(data: bytes, path: Path | None = None) -> SetSummary:
    """Parse already-decompressed Set XML. Rejects DTDs/entities outright."""
    head = data[:4096].lower()
    if b"<!doctype" in head or b"<!entity" in data[:65536].lower():
        raise AlsError("DTD/entity declarations are not allowed in Live Sets")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise AlsError(f"invalid XML: {exc}") from exc
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


def _walk(node: ET.Element, out: SetSummary, track: str | None, device_class: str | None) -> None:
    for child in node:
        tag = child.tag
        if tag in TRACK_TAGS:
            name = _track_name(child)
            if name:
                out.tracks.append(name)
            _walk(child, out, name, None)
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
            _walk(child, out, track, tag)
            continue
        if tag == "SampleRef":
            ref = child.find("FileRef")
            if ref is not None:
                out.samples.append(
                    SampleRefUse(
                        path=_val(ref, "Path") or None,
                        relative_path=_val(ref, "RelativePath") or None,
                        track=track,
                        device_class=device_class,
                    )
                )
            continue
        _walk(child, out, track, device_class)


def read_set(path: str | Path) -> SetSummary:
    """Read and summarize one .als file."""
    p = Path(path)
    try:
        with gzip.open(p, "rb") as fh:
            data = fh.read(MAX_XML_BYTES + 1)
    except (OSError, EOFError) as exc:
        raise AlsError(f"cannot read {p.name}: {exc}") from exc
    if len(data) > MAX_XML_BYTES:
        raise AlsError(f"{p.name} decompresses to more than {MAX_XML_BYTES} bytes")
    return parse_xml_bytes(data, p)
