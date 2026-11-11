# Security

This tool runs a local socket server inside Ableton Live and reads/writes local project and preset files.

- The bridge must bind to `127.0.0.1` only.
- File tools must stay within user-configured directories.
- Bridge requests are authenticated with a local secret; never share or commit `bridge.json`.
- Writes are disabled by default. Destructive MCP calls require form confirmation.
- XML/project readers bound decompression and reject entities; no arbitrary Python execution tool is exposed.
- No telemetry or external API credentials are required.

Report vulnerabilities privately via GitHub's "Report a vulnerability" (Security tab) once the repo is
public. Please do not open public issues for security problems.
