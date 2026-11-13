# Toolsets and usage

## Write safety

Save a copy of the Set in Live before editing. Most writes are one Live undo step
(`live_undo`). `live_set_labels`, `live_build_chain`, a `live_delete` or
`live_duplicate` mixing kinds (tracks with scenes, clips or devices: one bridge call per
kind) and `live_set_cue_points` (it runs as an operation) can take several undo steps;
their replies make no `undo_steps` claim. A batch has no rollback.

Read state after an `unknown` outcome before writing again. For asynchronous operations,
poll `live_get_operation` only while `pending`; `ready`, `failed` and `unknown` are final.
The server cannot save or open a Set through Live's API. Save your work in Live.
Set-label persistence after save/reopen remains experimental.

## Toolsets

A default install enables 36 tools: `core` (30), `automation` (2) and `arrangement` (4).
Those toolsets stay enabled. To add others, set `ABLETONLIVEMCP_TOOLSETS` in the MCP
server's environment. Add this field alongside `command` and `args` in your client config:

```json
"env": {"ABLETONLIVEMCP_TOOLSETS": "core,drums,racks"}
```

Other opt-ins are `organize`, `als`, `library`, `recording`, `editing`, `song`, `view`,
`devices-advanced` and `files`. `all` selects every non-experimental toolset (57 tools).
You can instead add `"toolsets": "drums,racks"` to your existing private bridge config.
The environment takes precedence. Both are read when the server starts; open a new
client session so the client refreshes its tool list. Unknown toolset names stop startup.

`live_hello` reports enabled toolsets and capabilities. Capabilities vary by object and
Live version. A tool's presence does not mean every action is supported. See
[known limits](validation.md#known-limits).

Tools name a track by 0-based index, `"return:N"` (return track N) or `"master"`.

## Optional settings

Set these in the MCP server's environment when needed:

| Variable | Purpose |
| --- | --- |
| `ABLETONLIVEMCP_READ_ONLY_TOOLS=1` | List only read tools; private bridge policy still enforces access |
| `ABLETONLIVEMCP_AUDIT=1` | Log allowed writes to stderr with tool/permission names, without arguments |
| `ABLETONLIVEMCP_FILE_ROOTS` | Absolute allowed folders for MIDI import/export |
| `ABLETONLIVEMCP_ALS_ROOTS` | Absolute allowed folders for offline project scans |
| `ABLETONLIVEMCP_DATA_DIR` | Directory for global label storage |
| `ABLETONLIVEMCP_KNOWLEDGE` | Your own Markdown reference directory for the `library` toolset |

Separate file and project roots with `;` on Windows or `:` on macOS/Linux. MIDI tools
have no allowed roots by default. Personal reference material is optional and stays
outside the public package. Tool visibility grants no write permission; see
[local permissions](permissions.md).

## Arrangement buildup example

Ask: "Turn Intro into an EDM buildup, with the drop on DROP." Read locators with
`live_get_arrangement`, create Session automation carriers with `live_create_clips` and
`live_set_automation`, then place them with `live_create_arrangement_clips`:

```json
{"clips":[{"track":7,"kind":"from_session","scene":0,"start":0}]}
```

Read actual track indices from your Set; the example uses track 7. Session automation
becomes track automation on the Arrangement. Call
`live_transport(action="back_to_arranger")` before playback.

Automation accepts `points: [{"time":0,"value":0},{"time":16,"value":1}]` (two or three
points, linear segments; requires `clear:true` and spans the whole clip) or `steps`.
Shape curves in Live. Direct timeline envelope reads/writes and arrangement clip
move/split/take-lane edits are unavailable.

From a source checkout with the package installed, run the
[filter sweep example](../examples/filter_sweep_buildup.py):

```sh
python examples/filter_sweep_buildup.py
```

It adds a MIDI track with an Auto Filter and a 16-beat Session high-pass sweep. It
leaves existing tracks alone and never saves the Set. Writes must be enabled.
Use `--length` to change the sweep or `--play` to launch it.
