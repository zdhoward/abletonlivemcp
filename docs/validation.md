# v0.9.0 beta: validation and limits

This beta targets Ableton Live 12.2 on Windows. Host Python is 3.10 or later. Other Live
versions and operating systems have not been qualified against a running DAW.

The final real-Live scenario ledger records 34 passing scenarios and 3 scenarios with explicit
unsupported results, with no failed or blocked scenarios. It covers the 57 registered tools,
including connection, mixer/routing, clips/notes, MIDI files, device loading/parameters/movement,
stock racks/drums, nested Simpler read/write/readback, arrangement, undo, confirmed deletion,
offline usage, labels, resources and prompts. Tool coverage does not prove every enum/target combination.

The offline suite covers protocol authentication/bounds, installer safety, path confinement,
bounded XML parsing, schemas, confirmations and tool contracts. CI runs Python 3.10 and 3.13
on Windows and Linux. The 0.10 development contracts keep request schemas below 30,000 UTF-8
bytes and the complete 30-tool listing below 68,000 bytes, including typed output schemas.

Distribution CI builds wheel and source archives, checks their allowed contents and embedded
Remote Script completeness, then installs the wheel in an isolated environment and initializes
the stdio MCP server from outside the checkout. This check lists tools without connecting to Live.
Personal knowledge and development artifacts are excluded from both package formats.

The unreleased 0.10 changes passed 391 local tests, including from a clean source snapshot,
Ruff, archive checks and a clean wheel stdio install. Five read-only Live responses passed
output-schema roundtrips. The 0.9 mutation ledger above has not been rerun against a freshly
installed 0.10 bridge; new permissions are not a claim of full Live qualification.

## Known limits

- Automatic rack-chain insertion/grouping and macro mapping are unavailable on Live 12.2.
- Custom drum-pad browser loading/building and pad copying refuse unsupported. Stock kit
  loading, pad reads/mute, rack macro edits and nested Simpler edits were exercised.
- Plugin preset selection depends on the plugin and exposed API; the tested unsupported path refuses.
- Unsafe arrangement split/move/take-lane writes and arrangement automation are disabled.
- Native browser Collections cannot be written; organization uses local labels and track properties.
- Set labels passed an in-session roundtrip. Persistence after saving/reopening is unproved.
- Knowledge is optional local reference material, not an audio analysis or automatic mixing engine.

Writes are off by default. Unknown mutation outcomes must be read back before any further edits;
never retry blindly. Keep backups of valuable Sets while testing the beta.
