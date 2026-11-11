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

Release 0.10.0 passed 398 local tests, Ruff, archive checks (no developer probes in either
archive) and a clean wheel stdio install. Over stdio against Live 12.2.0, seven read-only tools
(`live_hello`, session, tracks, scenes, clips, device list, browser roots) returned output that
validated against their schemas. The 0.9 mutation ledger above has not been rerun against a
freshly installed 0.10 bridge; new permissions are not a claim of full Live qualification.
Report write problems found in real projects as issues.

## Known limits

Targeted P-19, 2026-11-11, Basic on Live 12.2: copying PAD's 16-beat Session clip with
`Track.duplicate_clip_to_arrangement` to beat 0 returned a clip at [0,16] without a crash.
Deleting it and restoring it also succeeded. With the clip deleted, the Auto Filter Frequency
curve remained visible in PAD's track automation lane; the parameter's automation_state stayed
1 (automated). Samples taken after the short buildup had passed were static, so those samples
do not establish ramp playback. Basic was never saved; no saved-file claim is made for these
unsaved edits. This qualifies Session-to-Arrangement copy only, not the full P-19 probe.

The complete buildup demo then passed twice in the same Set: eight timeline clips with full
note readback at [0,16] and [16,32], six buildup/drop Session envelopes, actual Intro/DROP
locators and transport stopped at 0. The repeat confirmed automation_state=1 for PAD/Hats
Frequency and Core Saturator Drive. All three curves were inspected on screen. 401 repository
tests and Ruff passed. Server wheel and Remote Script were reinstalled before this Live proof.

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
