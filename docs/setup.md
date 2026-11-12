# Setup, upgrades and troubleshooting

Start with the [README setup steps](../README.md#install).

## Installation alternatives

These commands use the `v1.0.0` tag after it is published. Both tools need Python 3.10
or later and Git:

```sh
pipx install "git+https://github.com/zdhoward/abletonlivemcp@v1.0.0"
```

Or, with uv:

```sh
uv tool install "git+https://github.com/zdhoward/abletonlivemcp@v1.0.0"
```

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
PyPI publication is optional; these instructions do not depend on it.

## Upgrades

Upgrade the host package in the same environment where you installed it. With pip:

```powershell
.venv/Scripts/python.exe -m pip install --upgrade "git+https://github.com/zdhoward/abletonlivemcp@v1.0.0"
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
