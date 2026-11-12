<img src="assets/icon.svg" width="64" height="64" alt="">

# AbletonLiveMCP

An MCP server that lets Claude (or any MCP-capable LLM) assist you inside Ableton Live, with control
as close to native as possible. Not an autonomous producer: you stay in charge, the LLM does the tedious parts.

> **v0.11.0 beta.** Built for Ableton Live 12.2 on Windows. Ready for hands-on testing;
> [validation and limitations](docs/validation.md) describe what was checked.

## Install and upgrade

With Python 3.10 or later, install a tagged release (or download the wheel from the
[releases page](https://github.com/zdhoward/abletonlivemcp/releases)):

```sh
python -m pip install "git+https://github.com/zdhoward/abletonlivemcp@v0.11.0"
```

From a clone, `python -m pip install .` does the same.

1. Close Live, then install the Remote Script into your **User Library** (the one Live is set to
   use; check Settings > Library). The installer only touches a folder it created itself:

   ```
   abletonlivemcp-install "<path to your User Library>"
   ```

   The first run also creates `~/.abletonlivemcp/bridge.json` with a private secret (owner-only).
   Treat that file like a password. A new `AbletonLiveMCP` folder appears under `Remote Scripts`.
2. Start Live, then choose **AbletonLiveMCP** in Settings > Link, Tempo & MIDI > Control Surface.
   Live resets that slot to None if the script fails to load; check `Log.txt` if so.
3. **Writes are off by default.** `bridge.json` ships with `"read_only": true`, so every write is
   refused. Set it to `false` (and nothing else) when you want the assistant to change your Set.
   Live re-reads the file on every write; no restart needed. New configurations also limit
   writes to `transport` and `edit`; MIDI file operations and structural deletion need their
   own permissions. See [local permissions](docs/permissions.md).

**Upgrading from an older build** (before the authenticated bridge): the old script speaks a
different protocol and the new server refuses it. The installer refuses a folder it did not
create, so first move your old `AbletonLiveMCP` folder out of `Remote Scripts` (keep a copy
elsewhere, not inside the library), then run the install step above and restart Live.
Reinstalls keep only the latest backup of the previous version. Do not run the server and the
script from different versions: they will report "protocol 2 verification failed".

On Windows the strict permission check on `bridge.json` runs on the host side. Inside Live the
embedded Python has no `ctypes`, so Live applies a weaker check (location, no links); it logs one
line saying so at startup.

## Connect your assistant

Use the Python executable where you installed the package. Live runs on one machine and the
bridge secret is per user, so add the server at **user scope** in Claude Code:

```sh
claude mcp add abletonlive --scope user -- python -m abletonlivemcp.server
```

| Scope | Stored in | Use it for |
| --- | --- | --- |
| `user` (recommended) | `~/.claude.json`, top level | Every project on this machine, private to you |
| `local` (default) | `~/.claude.json`, under this project | Trying a development checkout in one project |
| `project` | `.mcp.json`, committed | A shared template repo; put settings in `${VARS}`, never secrets |

Settings are environment variables, so they can differ per scope, for example
`claude mcp add --scope user --env ABLETONLIVEMCP_TOOLSETS=core,drums abletonlive -- python -m abletonlivemcp.server`.
The bridge secret lives only in `~/.abletonlivemcp/bridge.json`; never copy it into an MCP config.

Other clients take the equivalent JSON:

```json
{
  "mcpServers": {
    "abletonlive": {
      "command": "python",
      "args": ["-m", "abletonlivemcp.server"]
    }
  }
}
```

For Codex: `codex mcp add abletonlive -- python -m abletonlivemcp.server`.
Restart the client after changing its MCP configuration. Ask it to call `live_hello`, then
`live_get_session`. To make edits, enable writes in your private bridge config as described above.
Destructive operations also require an MCP client that supports form elicitation.

## Using it on a real project

1. **Save a copy of the Set first.** Writes are verified and most tool writes are one Live undo
   step (`live_undo`). `live_set_mixer` with routing, `live_set_labels`, `live_build_chain`
   and `live_set_cue_points` make several bridge calls (or run as an operation), so one call
   can take several undo steps. A batch has no rollback.
2. Start read-only: ask for `live_hello` and a summary of the Set. Nothing can change yet.
3. When you want edits, set `"read_only": false` in `~/.abletonlivemcp/bridge.json`. The default
   permissions (`transport`, `edit`) allow playback and edits but not deletion or MIDI files.
   Add `"delete"` or `"files"` only when you need them; deletion always asks you to confirm,
   including cue deletes and the replace modes of the clip-creating tools.
4. Enable opt-in toolsets only for the job at hand (`drums`, `racks`, `arrangement`...). Fewer
   tools means faster, more accurate tool choice.
5. If something goes wrong, check Live's `Log.txt` and the server's stderr. Set
   `ABLETONLIVEMCP_AUDIT=1` to log every allowed write (tool and permission, never arguments).
   Report issues with the `live_hello` output and the refusal text.

## What it does

- Cover what the other Ableton MCP servers do (sessions, tracks, clips, mixer, devices, browser loading) and go
  further, with verified writes (every change is read back and reported as stored), read-only by default, and
  fewer, batched calls. Includes mixer/routing, extended note edits and bounded arrangement operations.
- Read and edit stock drum kits, pads and nested Simpler devices; custom pad loading is unavailable on 12.2.
- Set up scenes and plugin stacks; replicate a described vocal chain with the plugins you own.
- Edit existing rack macros; automatic grouping and macro mapping are unavailable on 12.2.
- Organize tracks and maintain local labels and project-usage reports. Native browser Collections are not writable.

## Knowledge base

Knowledge notes are personal, optional local reference material. They are excluded from Git and
from both package formats. Enable the `library` toolset and set `ABLETONLIVEMCP_KNOWLEDGE` to your
own Markdown directory to use `live_knowledge` and knowledge resources. Keep private notes outside
the public source tree (the local `knowledge/` directory is also ignored).

## Toolsets and limits

A default install enables 36 tools: the 30-tool `core` toolset (session/transport/undo,
tracks/mixer/scenes, clips/notes, device parameters/order, browser/load operations, chain
planning/building and confirmed delete/duplicate) plus the 2-tool `automation` toolset (Session-clip
envelopes) and 4-tool `arrangement` toolset (timeline clips and locators). Set
`ABLETONLIVEMCP_TOOLSETS` to add more (`core`, `automation`, `arrangement` stay on), or `all` for 57 tools.
Without the variable, a `"toolsets": "drums,racks"` key in `~/.abletonlivemcp/bridge.json` does the
same. Either is read once when the server starts: start a new client session after a change
(restarting the server process alone keeps the client's old tool list).
Opt-ins: `drums`, `racks`, `organize`, `als`, `library`, `recording`,
`editing`, `view`, `devices-advanced`, `files`. Resources and ten workflow prompts supplement tools.

Live 12.2 cannot insert rack chains or map macros automatically. Custom drum-pad loading and pad
copy refuse unsupported; stock kits, pad reads/mute and rack macro values are available. Unsafe
arrangement split/move/take-lane edits and arrangement automation refuse unsupported. Capabilities
vary by object; `live_hello` explains support and refusals. See [validation](docs/validation.md)
for tested paths and limitations; a listed tool does not imply every action is supported.

Offline scans use `ABLETONLIVEMCP_ALS_ROOTS`; MIDI files use `ABLETONLIVEMCP_FILE_ROOTS`
(both separated with the platform path separator). Global labels use `ABLETONLIVEMCP_DATA_DIR`.
Writes remain off by default and destructive tools require client form elicitation.
Set `ABLETONLIVEMCP_READ_ONLY_TOOLS=1` to list only read tools. This is a discovery filter;
the private bridge configuration still enforces access. MIDI file roots must be explicitly
configured; the home and temporary directories are no longer allowed by default.

## Arrangement buildup demo

Ask: **"Turn Intro into an EDM buildup, with the drop on DROP."** Read locators with
`live_get_arrangement`, build Session automation carriers and envelopes with `live_create_clips` and
`live_set_automation`, then place each with `live_create_arrangement_clips`:

```json
{"clips":[{"track":7,"kind":"from_session","scene":0,"start":0}]}
```

Session automation becomes track automation on the Arrangement. Call
`live_transport(action="back_to_arranger")` before playback. Reading or writing timeline
envelopes directly is unavailable, as are moving, splitting and take-lane edits of
arrangement clips.

Automation takes `points: [{"time":0,"value":0},{"time":16,"value":1}]` (two or three
points, linear segments; requires `clear:true` and spans the whole clip) or `steps`.
There is no curve setter; shape curves in Live.

For a working end-to-end example, `python examples/filter_sweep_buildup.py` talks to the
server over stdio and, on any Set, adds a MIDI track with an Auto Filter and automates a
16-beat high-pass sweep. It leaves existing tracks alone and never saves the Set. Use
`--length` to change the sweep and `--play` to launch the clip.

## Development

```
python -m pip install -e ".[dev]"
ruff check . && pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed MIT. No telemetry.

## Distribution

The repository retains source, public documentation, tests, CI and their reusable proof helpers.
Personal knowledge, research, task notes and one-off development scripts stay local. The root
`.gitignore` uses an explicit public-file allowlist; add new public files deliberately.

Wheels and source archives contain only the runtime source, Remote Script, package metadata and
license/attribution files. They do not contain tests, scripts, knowledge notes, research or the
developer probe modules (`probe_pNN.py`): those exist only in the source tree, load all-or-none,
and run only when the private configuration says `"dev_probes": true`.

To build and verify a clean installation without touching Live:

```sh
python -m pip install build
python -m build --sdist --wheel
python scripts/check_distribution.py dist --smoke
```

---

Created in [T3 Code](https://t3.codes).
