# Changelog

All notable changes to this project are recorded here. Format: [Keep a Changelog](https://keepachangelog.com),
versioning: [SemVer](https://semver.org). Versions below 1.0 may change tool names; renames keep an alias for one
minor version once the first public release is tagged.

## [Unreleased]

Upgrade: reinstall the Remote Script (`abletonlivemcp-install`) and restart Live.

- Fix: `live_get_arrangement` failed with a bare `HandlerError` whenever the read included a
  group track, which every whole-Set read does. Group rows now say `group: true`, and an
  arrangement-clip reference or placement on a group track refuses with a readable message.
- The Remote Script logs each unexpected handler failure to Live's `Log.txt` (method,
  exception type and code locations; never the message or arguments).
- Optional tool inputs no longer advertise a redundant `null` branch (~3 KB smaller default
  listing; explicit nulls are still accepted). A test now budgets the default 36-tool listing.
- README and validation docs: current version, dated validation status, and the buildup
  section no longer documents flags the example script does not have.

## [0.11.0] - 2026-11-11

Upgrade: reinstall the Remote Script (`abletonlivemcp-install`) and restart Live; server and
script must be the same version.

- `examples/filter_sweep_buildup.py`: a generic buildup on any Set over stdio. The owner-specific
  demo and restart scripts left this repository.
- `live_set_device_parameters` with display targets on two or more continuous parameters
  ("100 Hz", "25 %") no longer returns "partial" with "at most 129 display values": sample
  requests are grouped by the Remote Script's value budget.
- `live_hello` reports `read_only` and `dev_probes`, and `toolsets.how_to_enable`. The bridge
  config is re-read on every call; the read_only refusal says no restart is needed.
- The `clip.*` note-API probe flags are `null` (unknown) when no Session clip was sampled, for
  example on an Arrangement-only Set, instead of a misleading `false`.
- README documents the `toolsets` key in the bridge config. pytest runs against `src/`.
- The restart helper refuses to close Live while a non-Basic Set is open (`-Force` overrides).

- Buildup demo preserves existing Arrangement MIDI and uses a separate instrument effects
  bus with Wider, GHOST//PUMP, Auto Filter and inline Reverb/Delay. Reverb reaches 100% wet;
  wet FX switch off at DROP, restoring the dry beat. Apply FX and invite owner preview.
  Note generation requires both an explicit flag and a MIDI pitch map; occupied slots refuse.
- Session automation accepts 2-3 `points` with linear interpolation, using step insertion
  and interior-event deletion instead of dense steps. Live retains coincident boundary
  guards; `--shape` adjusts the demo's middle point. Native Bezier curvature is unavailable.

- Session-to-Arrangement copying via `live_create_arrangement_clips` (`kind: from_session`,
  `scene`, `start`), with bounds/overlap validation and clip readback. Optional `replace`
  requires delete permission and refuses clips extending outside the destination. Arrangement
  joins the default toolsets (36 default tools).
- Targeted P-19 on Live 12.2: PAD Session copy/delete/restore did not crash; its Frequency
  track lane survived deleting the copy (visible UI and automation_state=1). Other P-19
  operations remain disabled. Restart helper quotes Basic's path and verifies its window title.
- Automation steps now accept beat 0 (and refuse a zero-duration step at the clip end),
  allowing explicit drop/reset envelopes at the first beat.

- `automation` is now a default toolset (32 default tools); `live_set_automation` and
  `live_get_automation` accept a parameter name or index; `live_create_clips` gains
  `if_exists` (`error` | `skip` | `replace`); `live_launch` scene state reports real playback.
- `bridge.json` with a UTF-8 BOM is accepted.

## [0.10.0] - 2026-11-11

### Upgrade notes
- Reinstall the Remote Script (`abletonlivemcp-install`) and restart Live; server and script
  must be the same version.
- MIDI import/export now need `ABLETONLIVEMCP_FILE_ROOTS`; home and temp are no longer allowed.

### Changed
- Advertise typed outputs for all tools and bounded chain, browser, and note inputs.
- Core tool descriptions name the neighbouring tool to use instead.
- Developer probe modules and proof metadata are no longer shipped in wheels or source
  archives; the Remote Script loads probes all-or-none from a source checkout only.
- `ABLETONLIVEMCP_AUDIT=1` logs every allowed write (tool and permissions, no arguments).
- README documents Claude Code config scopes (user scope recommended) and first use on a real project.
- Add local transport/edit/files/delete permissions and optional read-only discovery.
- Require explicit MIDI file roots instead of granting home/temp access by default.
- Keep personal knowledge and development material local; check runtime-only archives
  and clean stdio wheel installation in CI. Preserve tests and their support files in Git.
- Existing private configs without a permission list retain their previous behavior;
  new configurations start read-only with transport/edit permissions only.

## [0.9.0] - 2026-11-11

First public beta for hands-on testing. Tested on Ableton Live 12.2/Windows; see
[validation and limitations](docs/validation.md). Read-only by default.

### Added
- 57 tools across core (30) and opt-in toolsets: mixer/routing, notes, clips, arrangement,
  automation, recording/view, racks/drums/Simpler, MIDI files, offline usage and labels.
- Optional local knowledge access, resources and ten workflow prompts; compact core schemas.
- One serial final Live scenario runner with scratch ownership and confirmation checks.
- Protocol 2 mutually authenticated, bounded bridge; transactional installer; private config file.
- Safety layer: object references with a generation counter, read-only policy (default), bounded mutation lease.
- Bounded browser paging/search and a verified device-load state machine (`pending/ready/failed/unknown`).
- Typed plans and receipts; stop-on-failure chain building with stock vocal presets.
- Handshake advertises the method list.

### Changed
- Remote Script handlers split into per-domain `dom_*.py` modules, each declaring its bridge methods;
  the safety gate merges them and refuses to import on a duplicate or malformed declaration.
- MCP tools split into `abletonlivemcp/tools/<domain>.py`; names, descriptions and schemas unchanged.

### Removed
- The Jev/TypeSafe judge backend, its `jev` extra and the `typesafe-sdk` dev dependency; the local
  rules judge is the only backend.

### Fixed
- A missing request parameter now returns a readable refusal ("not applied") instead of a generic error.
- Remote Script loads without `ctypes` (not available in Live's embedded Python).
- `generation` starts at a random number so a reloaded script never matches a stale client.
