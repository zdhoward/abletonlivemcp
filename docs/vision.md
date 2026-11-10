# Vision & requirements

Source of truth: [`original-prompt.md`](original-prompt.md) (verbatim). This file is a structured
reading of it. If the two disagree, the original prompt wins. Direction changes go in the
decision log at the bottom, dated.

## What this is

A personal, open-source alternative to [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp):
an MCP server that lets Claude (or any MCP-capable LLM) assist in Ableton Live. It doubles as portfolio work
and a tool the owner uses daily.

## Constraints from the prompt

- **Public, open source, contributable**, with process scoped to a small project.
- **Parity first**: everything the upstream ableton-mcp can already do.
- **Main differentiator**: LLM sets up a scene, builds a stack of VSTs, or fills a drum rack.
- **Organization**: help organize and label things by category and, if possible, by usage frequency.
- **Fully featured**, but not a fully automatable control surface. Goal is *as close to native control as possible* so the LLM
  *assists the user* in using Live and applying ideas.

## Target use cases (the owner's examples)

| # | Use case | Summary |
|---|---|---|
| UC1 | Drum rack from real usage | Scan recent dance-genre projects, find the drum one-shots actually used, build a drum rack in a **standard layout** (kicks, snares, etc. in standard pads) so MIDI transfers between racks. |
| UC2 | Color-tag plugins | Apply color tags to regularly used plugins so common ones sort together. |
| UC3 | Replicate a vocal chain | From an article (e.g. how Future does vocals; software and hardware), identify the gear, map to direct emulations the user owns, else closest alternatives owned, then attempt to dial in settings. |
| UC4 | Macro-ize an FX chain | Point at a track's FX chain; group into an Audio Effect Rack; label and map macros (e.g. "Riser FX", "Dub Delay FX", rest as makes sense) with ranges such as mono-to-stereo 0.0–1.0, reverb dry/wet 0.0–1.0, pitch up 0.0–12.0 st. |
| UC5 | Scene / VST stack setup | LLM sets up a scene or a stack of VSTs on request. |
| UC6 | Organize & label | Categorize and label library/devices by category and usage frequency. |

## Non-goals

- Turning Live into a fully autonomous AI-driven surface.
- Replacing the user's decisions; the LLM proposes and applies, the user stays in charge.

## Decision log

- 2026-11-10: Project started. Prompt recorded verbatim.
- 2026-11-10: Owner approved plan. Repo stays private until a v1 the owner is happy with. MIT license, no telemetry.
