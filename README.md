<img src="assets/icon.svg" width="64" height="64" alt="">

# AbletonLiveMCP

An MCP server that lets Claude (or any MCP-capable LLM) assist you inside Ableton Live, with control
as close to native as possible. Not an autonomous producer: you stay in charge, the LLM does the tedious parts.

> **Status: pre-alpha, private development.** The core bridge works in Live 12.2 on Windows; nothing else is supported yet. Roadmap in [`tasks/todo.md`](tasks/todo.md).

## Install and upgrade

1. Close Live, then install the Remote Script into your **User Library** (the one Live is set to
   use; check Settings > Library). The installer only touches a folder it created itself:

   ```
   abletonlivemcp-install "<path to your User Library>"
   ```

   The first run also creates `~/.abletonlivemcp/bridge.json` with a private secret (owner-only).
   Treat that file like a password. A new `AbletonLiveMCP` folder appears under `Remote Scripts`.
2. Start Live, then choose **AbletonLiveMCP** in Settings > Link, Tempo & MIDI > Control Surface.
   Live resets that slot to None if the script fails to load; check `Log.txt` if so.
3. **Writes are off by default.** `bridge.json` ships with `"read_only": true`, so every write is
   refused. Set it to `false` (and nothing else) when you want the assistant to change your Set.
   Live re-reads the file on every write; no restart needed.

**Upgrading from an older build** (before the authenticated bridge): the old script speaks a
different protocol and the new server refuses it. The installer refuses a folder it did not
create, so first move your old `AbletonLiveMCP` folder out of `Remote Scripts` (keep a copy
elsewhere, not inside the library), then run the install step above and restart Live.
Reinstalls keep only the latest backup of the previous version. Do not run the server and the
script from different versions: they will report "protocol 2 verification failed".

On Windows the strict permission check on `bridge.json` runs on the host side. Inside Live the
embedded Python has no `ctypes`, so Live applies a weaker check (location, no links); it logs one
line saying so at startup.

## Goals

- Cover what the other Ableton MCP servers do (sessions, tracks, clips, mixer, devices, browser loading) and go
  further, with verified writes (every change is read back and reported as stored), read-only by default, and
  fewer, batched calls. Parity is tracked in [`docs/plans/v2-detailed-plan.md`](docs/plans/v2-detailed-plan.md) as it lands;
  today's surface is a subset (no arrangement, mixer or note-edit tools yet).
- Build drum racks in a standard layout from the one-shots you actually use in recent projects.
- Set up scenes and plugin stacks; replicate a described vocal chain with the plugins you own.
- Group an FX chain into a rack and label/map macros from a plain-language spec.
- Color-tag and organize plugins by category and how often you use them.

## Knowledge base

[`knowledge/`](knowledge/INDEX.md) holds sourced notes on FX chains (vocals, drums, busses, guitar/bass,
keys/synths, mastering). It is a development resource and is **not shipped** in the package. In a
checkout it is read by the development tooling only; the production server does not expose it as tools.
Anyone can add a Markdown page there; see the index for the two-line convention.

See [`docs/vision.md`](docs/vision.md) for details and [`docs/original-prompt.md`](docs/original-prompt.md)
for the verbatim founding prompt.

## Development

```
python -m pip install -e ".[dev]"
ruff check . && pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed MIT. No telemetry.

---

Created in [T3 Code](https://t3.codes).
