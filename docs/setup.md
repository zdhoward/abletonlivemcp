# Setup, upgrades and troubleshooting

Start with the [README setup steps](../README.md#install).

## Client setup

The server uses stdio. Your client launches the installed `abletonlivemcp` command;
there is no HTTP URL or API key to enter. Run the client under the same user account
as Live. Restart the client or start a new session after configuring it.

### Codex

After installing the package and Remote Script, run:

```sh
codex mcp add abletonlive -- abletonlivemcp
```

Start a new Codex session and use the README's first-use prompt. Check registration
with `codex mcp list`. If the command cannot be found, use the quoted absolute
executable path from [Find the executable path](#find-the-executable-path) instead
of the final `abletonlivemcp`.

The equivalent entry in `~/.codex/config.toml` is:

```toml
[mcp_servers.abletonlive]
command = "abletonlivemcp"
args = []
```

Codex uses the same stdio server; no Codex-specific server changes are needed.
These configuration instructions follow the [official OpenAI MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
An end-to-end Codex/Live session has not been qualified here. Deletion still requires
the client's form-elicitation support, as described in [permissions](permissions.md).

### OpenCode

After installing the package and Remote Script, run:

```sh
opencode mcp add --global abletonlive -- abletonlivemcp
```

This registers the local stdio server in your user configuration. Omit `--global`
to configure only the current project. Start a new OpenCode session and use the
README's first-use prompt. `opencode mcp list` shows configured servers and their
connection status. If the command cannot be found, replace the final
`abletonlivemcp` with its quoted [absolute executable path](#find-the-executable-path).

See the [official OpenCode MCP documentation](https://opencode.ai/docs/mcp-servers/).
No OpenCode-specific server changes are needed. An end-to-end OpenCode/Live session
has not been qualified here; deletion still requires client form-elicitation support.

### Claude Code

```sh
claude mcp add --transport stdio --scope user abletonlive -- abletonlivemcp
```

If Claude Code cannot find the command, replace the final `abletonlivemcp` with the
quoted absolute executable path described below.

### Claude Desktop and Cursor

For Claude Desktop, open Settings > Developer > Edit Config and merge this into
`claude_desktop_config.json`. For Cursor, use `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "abletonlive": {
      "command": "<absolute path to abletonlivemcp>",
      "args": []
    }
  }
}
```

### VS Code

In your workspace's `.vscode/mcp.json`:

```json
{
  "servers": {
    "abletonlive": {
      "type": "stdio",
      "command": "<absolute path to abletonlivemcp>",
      "args": []
    }
  }
}
```

### Find the executable path

On Windows, run `(Get-Command abletonlivemcp).Source` in PowerShell. On macOS, use
`command -v abletonlivemcp`. Replace the placeholder in the JSON with that path.
Use forward slashes in Windows JSON paths, for example
`D:/Music/mcp/.venv/Scripts/abletonlivemcp.exe`.

If `pip` or an installed command cannot be found, check that Python and its Scripts
directory are on PATH, or use the explicit environment paths below. GUI clients may
not inherit your terminal's PATH. Other stdio clients use the same executable with
no arguments, or the installed environment's Python with `-m abletonlivemcp.server`.

## Virtual environment installation

Use a dedicated environment if you want to keep the MCP's dependencies separate from
other Python tools. Run these commands from a folder you will keep; no activation is
needed. Find your User Library in Live's Settings > Library and close Live first.

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade zx-ableton-live-mcp
.venv/Scripts/abletonlivemcp-install.exe "<path to your User Library>"
(Resolve-Path .venv/Scripts/abletonlivemcp.exe).Path.Replace('\', '/')
```

macOS (untested):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade zx-ableton-live-mcp
.venv/bin/abletonlivemcp-install "<path to your User Library>"
echo "$PWD/.venv/bin/abletonlivemcp"
```

The last command prints the server path to use in your client configuration.
Reopen Live and select AbletonLiveMCP in a free Control Surface slot under Settings >
Link, Tempo & MIDI. Check the connection with `live_hello`; `script.match` should be
`true`. Use `live_get_session` for a first read of the Set.

## One-click installer

The optional [Windows launcher](https://github.com/zdhoward/abletonlivemcp/raw/refs/heads/main/install-claude-code.cmd)
downloads and runs
[`scripts/install-claude-code.ps1`](../scripts/install-claude-code.ps1). It requires
Claude Code and internet access. Close Live before running it; it will not close a Set
for you. Select the User Library that contains your `Presets` folder.

The installer downloads a pinned, SHA-256-checked copy of
[uv](https://github.com/astral-sh/uv), then uses it to install managed Python 3.13 and
`zx-ableton-live-mcp` from PyPI under `%LOCALAPPDATA%/AbletonLiveMCP`. It does not need
administrator access, a system Python or changes to PATH. The existing Remote Script
installer creates the private bridge config and preserves it on upgrades.

Claude Code is registered through `claude mcp add --scope user`. Restart your Claude
Code session afterward. Selecting the Control Surface in Live is still manual.
macOS and other clients use the [client setup](#client-setup) instructions above.

To upgrade an installation made this way, close Live and run the launcher again.
It upgrades the package and reinstalls the Remote Script. A matching Claude entry is
left alone. If `abletonlive` already points to another installation, setup stops and
preserves it. To switch, remove that user-scoped entry with
`claude mcp remove --scope user abletonlive`, then rerun the installer.

If a download or command fails, the window stays open with the error. Fix that error
and rerun the launcher. If Claude Code cannot be found, install it first, then rerun.
An unknown or modified Remote Script folder follows the same refusal and recovery
rules as a [manual upgrade](#upgrades).

## Installation alternatives

The PyPI package is `zx-ableton-live-mcp`. Both tools need Python 3.10 or later:

```sh
pipx install zx-ableton-live-mcp
```

Or, with uv:

```sh
uv tool install zx-ableton-live-mcp
```

To install a Git tag instead, replace the package name with
`"git+https://github.com/zdhoward/abletonlivemcp@v1.1.0"` (needs Git).

Both expose `abletonlivemcp` and `abletonlivemcp-install` on PATH. Run
`abletonlivemcp-install "<path to your User Library>"` with Live closed. A GUI MCP
client may need the absolute executable path because it does not inherit your shell's
PATH. On Windows, `Get-Command abletonlivemcp` shows the command PowerShell finds;
on macOS, use `command -v abletonlivemcp`.

You can install a downloaded wheel with the environment's Python:

```powershell
.venv/Scripts/python.exe -m pip install "<path to downloaded wheel>"
```

For a source checkout, use `python -m pip install .` in an activated environment.

## Enable writes

Setup starts in read-only mode. To let your assistant edit:

1. Save a copy of your Set and stop playback.
2. In your existing `~/.abletonlivemcp/bridge.json`, change `"read_only": true` to
   `"read_only": false`. On Windows, `~` is your user profile folder. Preserve the
   secret and other fields; never share this file or put it in an MCP client config.
3. Ask your assistant to call `live_hello` and confirm `read_only` is `false` and
   `script.match` is `true`.

The switch takes effect without a restart. Set `read_only` back to `true` when you
finish. New configs allow `transport` and `edit`; other permissions are opt-in.
Ordinary edits do not ask for confirmation. Deletion also requires a client with
form elicitation. See [local permissions](permissions.md). After an unknown write
outcome, read the state before trying another edit.

## Upgrades

Close Live and upgrade the package using the same Python environment as the original
installation. For the README's pip installation:

```sh
pip install --upgrade zx-ableton-live-mcp
abletonlivemcp-install "path to your User Library"
```

For a virtual environment, use that environment's Python and installer paths from
[virtual environment installation](#virtual-environment-installation). For pipx, run
`pipx upgrade zx-ableton-live-mcp`; for uv, run `uv tool upgrade zx-ableton-live-mcp`.
Then rerun `abletonlivemcp-install` for the same User Library.
For the optional Windows launcher, follow its [upgrade instructions](#one-click-installer).

Restart Live and open a new MCP client session. Call `live_hello` and check `script.match`.
The host and Remote Script must match in version and build.

The installer preserves the existing bridge config and keeps the newest managed
Remote Script backup. If it refuses an unknown or modified folder, move that
`AbletonLiveMCP` folder outside `Remote Scripts` as a backup, then run the installer
again. This also applies to old scripts from before the authenticated bridge.
Do not put backups inside `Remote Scripts`.

## Connection problems

The Remote Script listens on `127.0.0.1:9877`. The MCP client starts the host server over
stdio; it does not use an HTTP URL. Run one Live instance with this Control Surface
and check for another process using the port. Keep the bridge on loopback.

If Live resets the Control Surface slot to None, the script failed to load. Check
that you installed into the User Library selected in Live's Library settings, then
inspect Live's `Log.txt`. Use the folder for your exact version:

- Windows: `%APPDATA%/Ableton/Live 12.2/Preferences/Log.txt`
- macOS: `~/Library/Preferences/Ableton/Live 12.2/Log.txt` (untested here)

A warning from `live_hello` means the running script differs from the host's bundled
copy. Reinstall the script and restart Live. An older, unauthenticated script may
instead cause `protocol 2 verification failed`.

If the MCP client cannot launch the command, point it at the absolute executable
inside your installation environment. A different Python can load an older package.
Forward slashes avoid JSON backslash escaping in Windows executable paths.

## Config and permission errors

The installer creates `~/.abletonlivemcp/bridge.json`. Both processes use that path
unless `ABLETONLIVEMCP_CONFIG` names an absolute file. A client-only override will
not change Live's environment, so keep the default for normal setup.

Preserve the existing secret and config fields when editing policy. Do not paste a
replacement config from a guide. On Windows the host enforces a private ACL. Live's
embedded Python lacks `ctypes`, so Live checks the location and rejects links but
cannot apply the same ACL check; it logs this at startup. On macOS the host requires
owner-only permissions (`chmod 600`).

For a refused write, check `read_only`, required permissions and the client's support
for form elicitation. See [local permissions](permissions.md). After an unknown write
outcome, read state before trying another edit.

Include redacted `live_hello` output and the refusal text in a
[bug report](https://github.com/zdhoward/abletonlivemcp/issues). Remove private names and
paths. Never attach `bridge.json`.
