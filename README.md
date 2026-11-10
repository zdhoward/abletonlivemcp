<img src="assets/icon.svg" width="64" height="64" alt="">

# AbletonLiveMCP

An MCP server that lets Claude (or any MCP-capable LLM) assist you inside Ableton Live, with control
as close to native as possible. Not an autonomous producer: you stay in charge, the LLM does the tedious parts.

> **Status: pre-alpha, private development.** Nothing is usable yet. Roadmap in [`tasks/todo.md`](tasks/todo.md).

## Goals

- Everything [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) can do (sessions, tracks, clips, devices, browser loading).
- Build drum racks in a standard layout from the one-shots you actually use in recent projects.
- Set up scenes and plugin stacks; replicate a described vocal chain with the plugins you own.
- Group an FX chain into a rack and label/map macros from a plain-language spec.
- Color-tag and organize plugins by category and how often you use them.

## Knowledge base

[`knowledge/`](knowledge/INDEX.md) holds sourced notes on FX chains (vocals, drums, busses, guitar/bass,
keys/synths, mastering). Query it through the MCP tools `knowledge_list`, `knowledge_search` and
`knowledge_read`. Anyone can add a Markdown page there; see the index for the two-line convention.

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
