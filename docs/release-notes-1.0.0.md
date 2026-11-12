# AbletonLiveMCP 1.0.0

AbletonLiveMCP is a Model Context Protocol server for Ableton Live. AI assistants like
Claude can read your Live Set and make edits through the bundled Remote Script.

This release adds setup instructions for Claude Desktop, Claude Code, Cursor and
VS Code, along with upgrade guidance and troubleshooting. The package includes the
host server and Remote Script. Python 3.10 or later is required.

## Install

Once the tag is published, install from GitHub:

```sh
python -m pip install "git+https://github.com/zdhoward/abletonlivemcp@v1.0.0"
abletonlivemcp-install "<path to your User Library>"
```

Close Live before running the installer. Restart Live and select AbletonLiveMCP under
Settings > Link, Tempo & MIDI > Control Surface. Follow the
[README setup guide](https://github.com/zdhoward/abletonlivemcp#readme) for an isolated
installation and MCP client configuration. These instructions do not require PyPI.

## Upgrade

Upgrade the host package, close Live and reinstall the Remote Script in the same User
Library. Restart Live and your MCP client, then call `live_hello` to check that both
copies match. Preserve the private bridge config. If the installer refuses an unknown
or modified script folder, move it outside Remote Scripts as a backup before installing.

## Scope and limits

Live 12.2 on Windows is qualified for the cases in the
[validation record](https://github.com/zdhoward/abletonlivemcp/blob/main/docs/validation.md).
macOS and other Live versions are untested. I have kept the Beta package classifier
because the qualification is limited. No new Live run was performed for this packaging
and documentation release; the record preserves the original build IDs.

Writes start disabled. Once enabled, ordinary edits can run without another prompt.
Deletion needs a separate permission and a confirmation form. MIDI file tools require
explicit allowed roots. See
[local permissions](https://github.com/zdhoward/abletonlivemcp/blob/main/docs/permissions.md).

The server cannot save or open a Set through Live's API. Set-label persistence across
save/reopen remains experimental. Some failure paths have offline test coverage only.
Read state after an unknown outcome before writing again.

See the [1.0.0 changelog](https://github.com/zdhoward/abletonlivemcp/blob/main/CHANGELOG.md)
for fixes included since 0.11.0.
