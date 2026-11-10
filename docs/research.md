# Research notes

> Superseded in depth by [`research-deep-review.md`](research-deep-review.md) (45 sources, confidence labels). This file is the first-pass summary.

Status key: **supported** = sources agree, **unverified** = needs a test against a real Live install.
Written 2026-11-10. Update as questions get resolved; do not delete superseded findings, mark them.

## Upstream (ahujasid/ableton-mcp), MIT

- Two parts: a MIDI Remote Script running inside Live (opens a socket server) and an MCP server (`server.py`) relaying to it.
- Protocol: JSON over TCP, `{type, params}` in, `{status, result|message}` out. Version handshake via `get_remote_script_info`.
- Capabilities: session/track info, create/modify MIDI and audio tracks, clips, notes, transport, load instruments/effects from the browser, tempo.
- Telemetry on by default upstream. **We will not ship telemetry.**
- Source: <https://github.com/ahujasid/ableton-mcp>

## Q1 Macro mapping / grouping (UC4)

- No source documents a LOM method to create macro->parameter mappings. TDAbleton and community practice map macros by hand.
- Newer Live 12.3 `insert_device()` / `insert_chain()` exist but add devices/chains, not mappings.
- `.adg`/`.adv` are gzip-compressed XML containing devices, parameter values, macro knobs and mappings. Existing tooling edits mappings at file level: <https://github.com/ben-juodvalkis/Ableton-Device-Creator>
- Caveat: Live is strict about the XML. Safe approach: start from a real preset as template and mutate it.
- **Plan**: generate/modify `.adg` files and load via browser. **Unverified**: exact XML element names and whether Live 12 loads our output. First task: gunzip a real Audio Effect Rack `.adg` and map the structure.

## Q2 Reading projects (UC1/UC6)

- `.als` is the same family (gzipped XML), so offline parsing should work. **Unverified** per Live version; confirm on the owner's projects.

## Q3 Drum rack (UC1/UC5)

- Same file-level approach as Q1 (Device-Creator already builds drum racks and Simplers from sample folders; good reference for the template approach). Standard pad layout still to be defined with the owner.

## Q4 Color tags (UC2), Q5 VST params (UC3)

- Not researched yet. Q5 working assumption: VST params appear only after Configure in Live.

## Other prior art to study before duplicating work

- <https://github.com/Ziforge/ableton-liveapi-tools> (220 LiveAPI tools; notes some advertised actions don't exist in Live 12.4).
- Unofficial LOM map: <https://midiremotescripts.structure-void.com/guides/lom-map/>
