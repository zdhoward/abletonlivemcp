<img src="assets/icon.svg" width="64" height="64" alt="AbletonLiveMCP icon">

# AbletonLiveMCP: MCP server for Ableton Live

[![CI](https://github.com/zdhoward/abletonlivemcp/actions/workflows/ci.yml/badge.svg)](https://github.com/zdhoward/abletonlivemcp/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

AbletonLiveMCP is a Model Context Protocol (MCP) server for Ableton Live. It lets AI
assistants like Claude read and edit your Live Set through a local Remote Script.

## What you can do

- Read your session, tracks, clips, notes and device parameters.
- Edit the mixer and MIDI notes, load installed devices and build effect chains.
- Write Session clip automation and make bounded arrangement edits.
- Work with stock drum kits and existing rack macros through optional toolsets.

Writes start disabled. The server reads changes back and reports what Live stored.
See [supported operations and limits](docs/validation.md#known-limits).

## Requirements

- Ableton Live 12.2 on Windows is the qualified setup. Other Ableton Live 12 versions
  and macOS are untested. The [validation record](docs/validation.md) lists the tested cases.
- Python 3.10 or later, on the same machine and user account as Live.
- An MCP client that supports stdio. Deletion also needs a client with form elicitation.
- Internet access to PyPI, or Git or a downloaded release wheel instead.

## Install

Install [`zx-ableton-live-mcp`](https://pypi.org/project/zx-ableton-live-mcp/) from PyPI
(current release: **1.1.0**). It provides the `abletonlivemcp` server and
`abletonlivemcp-install` Remote Script installer.

Create a virtual environment in a folder you will keep. Run these commands from that
folder; you do not need to activate the environment.

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade zx-ableton-live-mcp
```

macOS (untested):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade zx-ableton-live-mcp
```

For pipx, uv, Git tags or downloaded wheels, see
[installation alternatives](docs/setup.md#installation-alternatives).

## Set up the Remote Script

1. In Live, find your User Library in Preferences/Settings > Library, then close Live.
   Pass that folder to the installer; it must contain a `Presets` folder. Replace the
   placeholder below with your actual User Library path.

   Windows PowerShell:

   ```powershell
   .venv/Scripts/abletonlivemcp-install.exe "<path to your User Library>"
   ```

   macOS:

   ```sh
   .venv/bin/abletonlivemcp-install "<path to your User Library>"
   ```

2. Start Live. In Preferences > Link/Tempo/MIDI > Control Surface (called
   Settings > Link, Tempo & MIDI in Live 12), select `AbletonLiveMCP` in a free slot.

The installer creates `Remote Scripts/AbletonLiveMCP` in your User Library and a private
`~/.abletonlivemcp/bridge.json`. That file contains a secret. Never share it or put it
in an MCP client config.

## Connect your MCP client

Replace `C:/path/to/.venv/Scripts/abletonlivemcp.exe` below with the absolute path to
the environment you created. On macOS, use the absolute `.venv/bin/abletonlivemcp` path.
Open a new client session after saving the configuration.

### Claude Desktop and Cursor

For Claude Desktop, open Settings > Developer > Edit Config and merge this into
`claude_desktop_config.json`. For Cursor, use `~/.cursor/mcp.json`.

```json
{
  "mcpServers": {
    "abletonlive": {
      "command": "C:/path/to/.venv/Scripts/abletonlivemcp.exe",
      "args": []
    }
  }
}
```

Quit and reopen Claude Desktop after saving.

### Claude Code

```powershell
claude mcp add --transport stdio --scope user abletonlive -- "C:/path/to/.venv/Scripts/abletonlivemcp.exe"
```

### VS Code

In your workspace's `.vscode/mcp.json`:

```json
{
  "servers": {
    "abletonlive": {
      "type": "stdio",
      "command": "C:/path/to/.venv/Scripts/abletonlivemcp.exe",
      "args": []
    }
  }
}
```

For any other stdio client, launch `abletonlivemcp` with no arguments, or the installed
environment's Python with `-m abletonlivemcp.server`.

## Enable writes and try it

1. Open a disposable Set or save a copy in Live. Ask your assistant to call
   `live_hello` with `{}`. Check `script.match`, `read_only` and the capability report.
2. Call `live_get_session` with `{}` to read tempo, transport and session counts.
3. Stop playback yourself. In your existing `~/.abletonlivemcp/bridge.json`, change
   `"read_only": true` to `"read_only": false`. Preserve the secret and other fields.
4. Call `live_set_session` with `{"metronome": true}`, then `live_get_session` to check it.
   Restore the original metronome value with the same tool when done.

Set `read_only` back to `true` when you finish. The switch takes effect without a restart.
New configs allow only `transport` and `edit`. Other permissions are opt-in; see
[local permissions](docs/permissions.md). Ordinary edits do not ask for confirmation.
After an unknown outcome, read the state before another write.

## Upgrade an existing installation

Close Live, then upgrade the package in your existing environment and reinstall the
Remote Script into the same User Library:

```powershell
.venv/Scripts/python.exe -m pip install --upgrade zx-ableton-live-mcp
.venv/Scripts/abletonlivemcp-install.exe "<path to your User Library>"
```

On macOS, use `.venv/bin/python` and `.venv/bin/abletonlivemcp-install` instead.
The installer preserves your existing bridge configuration. Restart Live and your
MCP client, then call `live_hello` and check that `script.match` is `true`.
See [upgrade troubleshooting](docs/setup.md#upgrades) if the installer refuses an
older or modified Remote Script folder.

## Troubleshooting

- If Live resets the Control Surface to None, check the User Library and Live's
  `Log.txt`: `%APPDATA%/Ableton/Live 12.2/Preferences/Log.txt` on Windows.
  Use the folder for your exact Live version.
- The bridge uses `127.0.0.1:9877`. Check for a port conflict or another Live instance.
- After upgrading, close Live, rerun the Remote Script installer and restart Live and
  the MCP client. A version/build mismatch in `live_hello` needs this reinstall.
- If the client cannot find the command, use the absolute executable path from your
  installation environment.

See [setup and troubleshooting](docs/setup.md) for macOS log paths and installer errors.

## FAQ

### What is AbletonLiveMCP?

It is an open-source Ableton Live MCP server. An AI assistant uses its tools to inspect
and edit a Live Set through the Model Context Protocol.

### Which Live versions work?

Live 12.2 on Windows is qualified for the cases in the [validation record](docs/validation.md).
Other versions have not been qualified.

### Does it work on Mac?

macOS is untested. The installer has platform-specific file permission handling, but I
have not qualified it against Live on a Mac.

### Is it safe, and can it change my Set without asking?

Writes are disabled by default. Once you enable them, ordinary edits can run without
another prompt. Deletion needs a separate permission and a confirmation form. Keep a
copy of your Set; batches have no rollback. See [write safety](docs/usage.md#write-safety).

### Which AI clients work with it?

Use a client with stdio MCP support, such as Claude Desktop, Claude Code, Cursor or
VS Code. The configurations above launch the same server. Client versions differ in
their support for form elicitation, which destructive tools require.

## More information

- [Setup, upgrades and troubleshooting](docs/setup.md)
- [Toolsets and usage](docs/usage.md)
- [Local permissions](docs/permissions.md)
- [Validation and known limits](docs/validation.md)
- [Changelog](CHANGELOG.md) and [1.0.0 release notes](docs/release-notes-1.0.0.md)
- [Contributing and tests](CONTRIBUTING.md), [security reporting](SECURITY.md) and [MIT license](LICENSE)
