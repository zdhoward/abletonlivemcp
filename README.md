<img src="assets/icon.svg" width="64" height="64" alt="AbletonLiveMCP icon">

# AbletonLiveMCP

[![CI](https://github.com/zdhoward/abletonlivemcp/actions/workflows/ci.yml/badge.svg)](https://github.com/zdhoward/abletonlivemcp/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

Connect your AI assistant to Ableton Live. Explore your Set, edit MIDI, adjust
devices and mixer settings, and build effect chains through MCP.

Works with Codex, OpenCode, Claude Code, Claude Desktop, Cursor, VS Code and other
MCP clients.

## Install

You'll need Python 3.10 or later and Ableton Live on the same computer as your AI
client. Live 12.2 on Windows is tested; macOS and other versions are untested.

Find your **User Library** in Live's **Settings > Library**, then close Live and run:

```sh
pip install zx-ableton-live-mcp
abletonlivemcp-install "path to your User Library"
```

Replace the quoted path with your User Library folder.

Reopen Live. In **Settings > Link, Tempo & MIDI > Control Surface**, select
**AbletonLiveMCP** in a free slot.

## Connect your assistant

For Claude Code, run:

```sh
claude mcp add --transport stdio --scope user abletonlive -- abletonlivemcp
```

For Codex, run:

```sh
codex mcp add abletonlive -- abletonlivemcp
```

For OpenCode, run:

```sh
opencode mcp add --global abletonlive -- abletonlivemcp
```

Then start a new session in your chosen client.

Using **Claude Desktop, Cursor or VS Code**? See [client setup](docs/setup.md#client-setup).

## Try it

Open a Set and ask your assistant:

> Check my Ableton connection, then tell me the tempo and what tracks are in my Set.

You can explore tracks, clips, notes, devices and mixer settings immediately.
**Editing starts disabled.** When you're ready to make changes, save a copy of your
Set and [enable writes](docs/setup.md#enable-writes).

Once editing is enabled, try requests such as:

- "Turn the selected track down by 3 dB."
- "Quantize this MIDI clip to sixteenth notes."
- "Add an EQ to this track."

## Help and documentation

- [Setup, alternative installs, upgrades and troubleshooting](docs/setup.md)
- [Tools and usage](docs/usage.md)
- [Permissions and write safety](docs/permissions.md)
- [Supported operations and known limits](docs/validation.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md) · [Report a bug](https://github.com/zdhoward/abletonlivemcp/issues) · [Security](SECURITY.md) · [MIT license](LICENSE)
