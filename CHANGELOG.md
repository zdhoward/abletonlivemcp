# Changelog

All notable changes to this project are recorded here. Format: [Keep a Changelog](https://keepachangelog.com),
versioning: [SemVer](https://semver.org). Versions below 1.0 may change tool names; renames keep an alias for one
minor version once the first public release is tagged.

## [Unreleased]

### Added
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
