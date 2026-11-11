"""P-29 offline helper: summarize the Macro -> parameter mapping inside an ``.adg`` rack preset.

An ``.adg`` is a gzipped XML document. This script never writes anything and never loads a file
into Live; it reads one ``.adg`` (read-only) and prints a JSON summary of

- the rack device(s) and their macro controls (index, display name, default, value);
- every parameter that carries a ``KeyMidi`` mapping with ``Channel`` 16 (the macro pseudo
  channel; ``NoteOrController`` is the zero-based macro index) plus its ``MidiControllerRange``;
- counts of the other ``KeyMidi`` channels (real MIDI mappings) so they are not mistaken for macros.

Usage (main checkout venv)::

    PYTHONPATH=src .venv/Scripts/python scripts/adg_schema_probe.py PATH.adg
    ... adg_schema_probe.py --diff A.adg B.adg        # mapping set difference
    ... adg_schema_probe.py --corpus DIR [--limit N]  # channel/field statistics over a folder

The input is untrusted: files over ``MAX_XML_BYTES`` once unzipped are refused, and a document
with a DOCTYPE/ENTITY declaration is refused (no external entity or billion-laughs expansion).
"""

from __future__ import annotations

import argparse
import collections
import gzip
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_XML_BYTES = 64 * 1024 * 1024
MACRO_CHANNEL = 16  # KeyMidi/Channel value used for macro mappings (observed in Core Library)
RACK_TAGS = (
    "InstrumentGroupDevice",
    "AudioEffectGroupDevice",
    "MidiEffectGroupDevice",
    "DrumGroupDevice",
)
KEYMIDI_FIELDS = (
    "PersistentKeyString",
    "IsNote",
    "Channel",
    "NoteOrController",
    "LowerRangeNote",
    "UpperRangeNote",
    "ControllerMapMode",
)


def load_xml(path: Path) -> ET.Element:
    """Gunzip (plain XML is tolerated) and parse, refusing oversized or DTD-bearing input."""
    with path.open("rb") as handle:
        head = handle.read(2)
        handle.seek(0)
        if head == b"\x1f\x8b":
            with gzip.GzipFile(fileobj=handle) as gz:
                data = gz.read(MAX_XML_BYTES + 1)
        else:
            data = handle.read(MAX_XML_BYTES + 1)
    if len(data) > MAX_XML_BYTES:
        raise ValueError(f"{path.name}: more than {MAX_XML_BYTES} bytes of XML")
    if b"<!DOCTYPE" in data[:4096] or b"<!ENTITY" in data[:65536]:
        raise ValueError(f"{path.name}: DOCTYPE/ENTITY declarations are refused")
    return ET.fromstring(data)


def _value(el: ET.Element | None, child: str, default=None):
    node = None if el is None else el.find(child)
    return default if node is None else node.get("Value", default)


def _owner(parent: dict, el: ET.Element) -> str:
    """Tag of the nearest enclosing device element (a child of ``Devices``/``Device``)."""
    cur = el
    while cur in parent:
        up = parent[cur]
        if up.tag in ("Devices", "Device"):
            return f"{cur.tag}#{cur.get('Id', '?')}"
        cur = up
    return "?"


def _path(parent: dict, el: ET.Element, depth: int = 12) -> str:
    tags = []
    cur = el
    while cur in parent and len(tags) < depth:
        tags.append(cur.tag)
        cur = parent[cur]
    return "/".join(reversed(tags))


def summarize(root: ET.Element) -> dict:
    parent = {c: p for p in root.iter() for c in p}
    racks = []
    for el in root.iter():
        if el.tag in RACK_TAGS or el.find("MacroControls.0") is not None:
            macros = []
            for i in range(16):
                ctl = el.find(f"MacroControls.{i}")
                if ctl is None:
                    continue
                macros.append(
                    {
                        "index": i,
                        "name": _value(el, f"MacroDisplayNames.{i}"),
                        "manual": _value(ctl, "Manual"),
                        "default": _value(el, f"MacroDefaults.{i}"),
                        "range": [
                            _value(ctl.find("MidiControllerRange"), "Min"),
                            _value(ctl.find("MidiControllerRange"), "Max"),
                        ],
                    }
                )
            racks.append(
                {
                    "tag": el.tag,
                    "visible_macros": _value(el, "NumVisibleMacroControls"),
                    "macros": macros,
                }
            )
    mappings, other_channels = [], collections.Counter()
    for key in root.iter("KeyMidi"):
        param = parent[key]
        channel = _value(key, "Channel")
        if channel != str(MACRO_CHANNEL) or _value(key, "IsNote") != "false":
            other_channels[f"channel={channel},is_note={_value(key, 'IsNote')}"] += 1
            continue
        rng = param.find("MidiControllerRange")
        mappings.append(
            {
                "parameter": param.tag,
                "device": _owner(parent, param),
                "path": _path(parent, param),
                "macro_index": int(_value(key, "NoteOrController", "-1")),
                "range_min": _value(rng, "Min"),
                "range_max": _value(rng, "Max"),
                "manual": _value(param, "Manual"),
                "keymidi": {f: _value(key, f) for f in KEYMIDI_FIELDS},
                "param_children": [c.tag for c in param],
            }
        )
    by_macro = collections.Counter(m["macro_index"] for m in mappings)
    return {
        "root": {"tag": root.tag, **{k: root.get(k) for k in ("MajorVersion", "MinorVersion")}},
        "creator": root.get("Creator"),
        "racks": racks,
        "macro_mappings": mappings,
        "mappings_per_macro": {str(k): v for k, v in sorted(by_macro.items())},
        "non_macro_keymidi": dict(other_channels),
    }


def _key(m: dict) -> tuple:
    return (m["device"], m["parameter"], m["macro_index"], m["range_min"], m["range_max"])


def diff(a: dict, b: dict) -> dict:
    sa, sb = {_key(m) for m in a["macro_mappings"]}, {_key(m) for m in b["macro_mappings"]}
    return {"only_in_a": sorted(sa - sb), "only_in_b": sorted(sb - sa), "common": len(sa & sb)}


def corpus(folder: Path, limit: int | None) -> dict:
    files = sorted(p for p in folder.rglob("*") if p.suffix.lower() == ".adg")
    if limit:
        files = files[:limit]
    stats = collections.Counter()
    channels, child_sets = collections.Counter(), collections.Counter()
    examples, failed = {}, []
    for path in files:
        try:
            info = summarize(load_xml(path))
        except Exception as exc:  # noqa: BLE001 - a bad file is a finding, keep scanning
            failed.append(f"{path.name}: {type(exc).__name__}: {exc}"[:200])
            continue
        stats["files"] += 1
        if info["macro_mappings"]:
            stats["files_with_macro_mappings"] += 1
            examples.setdefault("first_mapped", str(path))
        for m in info["macro_mappings"]:
            stats["macro_mappings"] += 1
            child_sets[tuple(m["param_children"])] += 1
            channels[m["keymidi"]["ControllerMapMode"]] += 1
        for key, n in info["non_macro_keymidi"].items():
            channels[key] += n
    return {
        "stats": dict(stats),
        "controller_map_mode_or_other_channels": dict(channels),
        "param_child_sets_of_mapped_parameters": [
            {"children": list(k), "count": v} for k, v in child_sets.most_common(5)
        ],
        "examples": examples,
        "failed": failed[:10],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--diff", action="store_true", help="compare two .adg mapping sets")
    ap.add_argument("--corpus", type=Path, help="scan a folder recursively for .adg files")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--brief", action="store_true", help="omit per-mapping detail")
    args = ap.parse_args(argv)
    if args.corpus:
        out = corpus(args.corpus, args.limit)
    elif args.diff:
        if len(args.paths) != 2:
            ap.error("--diff needs exactly two .adg paths")
        out = diff(*(summarize(load_xml(p)) for p in args.paths))
    elif len(args.paths) == 1:
        out = summarize(load_xml(args.paths[0]))
        if args.brief:
            out["macro_mappings"] = out["macro_mappings"][:5]
    else:
        ap.error("give one .adg path (or --diff A B, or --corpus DIR)")
    json.dump(out, sys.stdout, indent=1, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
