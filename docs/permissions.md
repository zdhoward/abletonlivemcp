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
| `delete` | Structural deletion, with human form confirmation at the MCP layer |

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
without arguments, object names, file contents, or secrets. A denial says `permission_denied`
and `(not applied)`. Read state after an unknown write outcome; never retry it blindly.

Tool annotations guide clients; they are not authorization checks. Destructive confirmation
is a separate safeguard and cannot substitute for the `delete` permission.
