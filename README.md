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
- Run your AI client on the same machine and user account as Live.
- An MCP client such as Claude Desktop, Claude Code, Cursor or VS Code.

## Install

### Windows + Claude Code

Already have [Claude Code](https://code.claude.com/docs/en/setup)? No Python or terminal
commands needed:

1. Close Live, then **[download the installer](https://github.com/zdhoward/abletonlivemcp/raw/refs/heads/main/install-claude-code.cmd)**
   and double-click it.
2. Choose your **User Library** folder when prompted (the one shown in Live's
   Settings > Library). The installer handles Python, the Remote Script and Claude Code.
3. Reopen Live and select **AbletonLiveMCP** under **Settings > Link, Tempo & MIDI >
   Control Surface**. Start a new Claude Code session and ask:

   > Check Ableton with live_hello and tell me the tempo of my Set.

Setup starts in read-only mode. To let your assistant edit, follow
[enable writes](docs/setup.md#enable-writes). See [installer help](docs/setup.md#one-click-installer)
if setup stops.

<details>
<summary>Manual setup / other clients / macOS</summary>

For manual setup, install Python 3.10 or later first.

### 1. Install and add to Live

In Live, open **Settings > Library** and copy your **User Library** path, then close
Live. In PowerShell, open a folder you will keep and run the commands below,
replacing `<User Library path>` with the path you copied:

```powershell
py -3 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade zx-ableton-live-mcp
.venv/Scripts/abletonlivemcp-install.exe "<User Library path>"
(Resolve-Path .venv/Scripts/abletonlivemcp.exe).Path.Replace('\', '/')
```

The last line prints the server path you will use in step 2. No environment activation
is needed.

<details>
<summary>macOS commands (untested)</summary>

In Terminal, run these from a folder you will keep:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade zx-ableton-live-mcp
.venv/bin/abletonlivemcp-install "<User Library path>"
echo "$PWD/.venv/bin/abletonlivemcp"
```

</details>

Reopen Live. Under **Settings > Link, Tempo & MIDI > Control Surface**, select
**AbletonLiveMCP** in a free slot.

### 2. Connect your AI assistant

Expand your client's instructions. Use the server path printed in step 1 wherever
you see `<server path>`, then restart the client.

<details>
<summary>Claude Desktop or Cursor</summary>

For Claude Desktop, open Settings > Developer > Edit Config and merge this into
`claude_desktop_config.json`. For Cursor, use `~/.cursor/mcp.json`.

```json
{
  "mcpServers": {
    "abletonlive": {
      "command": "<server path>",
      "args": []
    }
  }
}
```

</details>

<details>
<summary>Claude Code</summary>

```powershell
claude mcp add --transport stdio --scope user abletonlive -- "<server path>"
```

</details>

<details>
<summary>VS Code</summary>

In your workspace's `.vscode/mcp.json`:

```json
{
  "servers": {
    "abletonlive": {
      "type": "stdio",
      "command": "<server path>",
      "args": []
    }
  }
}
```

</details>

Other clients: use the server path as a stdio command with no arguments.

### 3. Try it

Open a Set in Live and ask your assistant:

> Check the Ableton connection with live_hello, then use live_get_session to tell me
> the tempo and how many tracks are in my Set.

The connection check should show `script.match: true`. You can now explore your Set.
Setup starts in read-only mode; when you want to edit, follow
[enable writes](docs/setup.md#enable-writes).

Need something else? See [alternative installs](docs/setup.md#installation-alternatives),
[upgrades](docs/setup.md#upgrades) or [connection troubleshooting](docs/setup.md#connection-problems).

</details>

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
