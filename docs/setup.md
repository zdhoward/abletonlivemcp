# Setup, upgrades and troubleshooting

Start with the [README setup steps](../README.md#install).

## One-click installer

The Windows launcher `install-claude-code.cmd` downloads and runs
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
macOS and other clients use the manual instructions in the README.

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

Upgrade the host package in the same environment where you installed it. With pip:

```powershell
.venv/Scripts/python.exe -m pip install --upgrade zx-ableton-live-mcp
```

For pipx or uv, replace the environment by repeating the installation command above
with `--force`. Close Live, then rerun `abletonlivemcp-install` for the same User Library.
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
