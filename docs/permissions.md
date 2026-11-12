# Local permissions and visibility

AbletonLiveMCP uses stdio and a mutually authenticated loopback bridge. These are local
capabilities, not OAuth scopes. Tool visibility does not grant authority.

New private bridge configurations contain:

```json
{
  "read_only": true,
  "permissions": ["transport", "edit"]
}
```

Keep the installer's existing secret and other configuration fields. Setting `read_only`
to false enables only the listed capabilities:

| Permission | Allows |
| --- | --- |
| `transport` | Playback, launches, selection, and view changes |
| `edit` | Track/clip/device edits, recording, chain builds, and undo/redo |
| `files` | MIDI export; MIDI import additionally requires `edit` |
| `delete` | Deletion, with human form confirmation at the MCP layer (see below) |

`delete` covers `live_delete` and every call that deletes as part of another tool: cue deletes
in `live_set_cue_points` (`action: "delete"`), `live_create_clips(if_exists="replace")` and
`live_create_arrangement_clips` with `replace: true`. Those calls need `edit` and `delete`, and
the server asks the human to confirm them through the same form as `live_delete`; the same
tool's non-deleting calls need only `edit` and ask nothing.

Before asking, the server reads the objects the call would delete from Live and lists them
(names, cue times, clip spans). The write is bound to exactly those objects through bridge
references (`expect_clip` / `expect_replace` for replaces): if the Set changes while the form
is open, the call refuses (`stale_target`, `target_changed`) and nothing is deleted. An
acceptance that does not match a question shown for these same arguments refuses
`confirmation_stale`.

The Remote Script decides whether a bridge call deletes from strictly typed arguments: a
`replace` that is not a JSON boolean is refused before any permission decision, so a string
like `"true"` cannot delete with only `edit`.

An empty permissions list permits no writes. Unknown names or a malformed list grant no
capabilities. The host and Live bridge independently enforce their respective operations;
the read-only switch always takes precedence. Existing configurations without a permissions
field retain their previous behavior. Add an explicit list to narrow them. The server never
edits the configuration to grant itself more access.

For a smaller read-only tool listing, set `ABLETONLIVEMCP_READ_ONLY_TOOLS=1` in the MCP client's
server environment. This removes mutation tools from discovery. Continue to use `read_only`
and permissions for enforcement, including against direct bridge clients.

MIDI import/export additionally require `ABLETONLIVEMCP_FILE_ROOTS`: absolute folders separated
by the platform path separator (`;` on Windows, `:` on Linux/macOS). No home or temporary
directory is granted by default. Existing files are never overwritten by export.

Authorization denials are logged to stderr using tool identifiers and required permissions,
without arguments, object names, file contents, or secrets. Set `ABLETONLIVEMCP_AUDIT=1` in the
MCP server environment to also log every allowed write in the same form. A denial says `permission_denied`
and `(not applied)`. Read state after an unknown write outcome; never retry it blindly.

Tool annotations guide clients; they are not authorization checks. Destructive confirmation
is a separate safeguard and cannot substitute for the `delete` permission.
