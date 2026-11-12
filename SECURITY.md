# Security

This tool runs a local socket server inside Ableton Live and reads/writes local project and preset files.

- The bridge must bind to `127.0.0.1` only.
- File tools must stay within user-configured directories.
- Bridge requests are authenticated with a local secret; never share or commit `bridge.json`.
- Writes are disabled by default. Destructive MCP calls require form confirmation.
- Explicit local permissions restrict transport, edits, file operations and deletion independently;
  see [permissions](docs/permissions.md). MIDI file access requires explicit allowed roots.
- XML/project readers bound decompression and reject entities; no arbitrary Python execution tool is exposed.
- No telemetry or external API credentials are required.

## Reporting and supported versions

Security fixes target the latest release; upgrade both the host and Remote Script together.
Use [GitHub private vulnerability reporting](https://github.com/zdhoward/abletonlivemcp/security/advisories/new)
if available. If the form is unavailable, open an issue requesting a private contact without
including vulnerability details. Never post exploit details, secrets or `bridge.json` publicly.
