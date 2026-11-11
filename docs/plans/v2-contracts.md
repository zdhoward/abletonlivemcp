# v2 shared integration contract (batch 1, frozen)

Status: frozen by batch 1 on 2026-11-11. Batches 2-6 build against this and **do not edit** the
shared files: `server.py`, `models.py`, `tools/__init__.py`, `proof_contract.py`,
`remote_script/AbletonLiveMCP/{handlers,safety,dom_common,operations}.py`,
`scripts/live_harness.py`, `scripts/live_v2_final.py`, `tests/test_tool_surface.py`,
`pyproject.toml`. A missing helper is reported to the integrator, not added locally.

Source plan: `docs/plans/v2-fast-track.md` (budget, batches, evidence); tool and selector detail:
`docs/plans/v2-detailed-plan.md` section 2.

## 1. Modules, toolsets, ownership

Every module already exists and is already imported, installed and packaged: host
`src/abletonlivemcp/tools/<module>.py` (imported by `tools/__init__.py`), remote
`remote_script/AbletonLiveMCP/dom_<domain>.py` (in `safety.DOMAINS` and the installer's
`install.DOMAINS`/`REQUIRED`). Batches fill them; nothing else needs to change. The wheel packages
the whole `src/abletonlivemcp` tree plus the Remote Script, so a new flat `models_<area>.py` or
helper module in `src/abletonlivemcp/` is packaged automatically. A new *remote* file cannot be
added without editing the installer list, so a batch keeps its remote code in its `dom_*` files.

Toolset rule (T-002, `server.toolset_of`): a module in `CORE_MODULES` (session, tracks, scenes,
clips, notes, devices, browser, chain) is `core`; every other module is its own toolset, with `_`
written as `-`. The final surface is frozen in `src/abletonlivemcp/proof_contract.py`
(`FINAL_SURFACE`, `OWNER`, `LEGACY_TOOLS`); `tests/test_tool_surface.py` refuses a registered tool
that is not listed there under its own module.

| Module (host) | Remote domain(s) | Toolset | Batch | Final tools |
|---|---|---|---:|---|
| session | dom_session | core | 2 | live_hello, live_get_session, live_set_session, live_transport, live_undo |
| tracks | dom_tracks | core | 2 | live_get_tracks, live_create_tracks, live_set_tracks, live_set_mixer, live_delete, live_duplicate |
| scenes | dom_scenes | core | 2 | live_get_scenes, live_create_scenes, live_set_scenes, live_launch |
| recording | dom_recording | recording | 2 | live_record |
| song | dom_song | song | 2 | (none: song extras are fields of session get/set; compatibility toolset) |
| view | dom_view | view | 2 | live_view |
| clips | dom_clips | core | 3 | live_get_clips, live_create_clips, live_set_clips |
| notes | dom_notes | core | 3 | live_get_notes, live_edit_notes |
| arrangement | dom_arrangement | arrangement | 3 | live_get_arrangement, live_set_cue_points, live_create_arrangement_clips, live_edit_arrangement_clips |
| automation | dom_automation | automation | 3 | live_get_automation, live_set_automation |
| editing | dom_editing | editing | 3 | live_edit_audio_clip |
| files | (host only, via dom_clips/dom_notes) | files | 3 | live_import_midi, live_export_midi |
| devices | dom_devices | core | 4 | live_get_device_parameters, live_set_device_parameters, live_set_devices, live_move_device |
| browser | dom_browser | core | 4 | live_browser_list, live_browser_search, live_get_operation, live_load_item |
| chain | (host, via browser/devices) | core | 4 | live_plan_chain, live_build_chain |
| drums | dom_drums | drums | 4 | live_get_drum_rack, live_set_drum_pads, live_convert, live_get_simpler, live_set_simpler, live_plan_drum_rack, live_build_drum_rack |
| racks | dom_racks | racks | 4 | live_get_rack, live_set_rack |
| devices_advanced | dom_devx | devices-advanced | 4 | live_get_device_extras, live_set_device_extras |
| als | (host only) | als | 5 | live_scan_projects, live_usage_report |
| organize | dom_labels | organize | 5 | live_get_labels, live_set_labels |
| library | (host only) | library | 5 | live_knowledge |
| experimental | - | experimental | - | (none; excluded from `all`) |
| resources.py, prompts.py | - | - | 6 | MCP resources and prompts (not tools) |

Totals: 30 core + 27 opt-in = 57; hard caps 30 core, 58 total (`proof_contract.CORE_LIMIT`,
`ALL_LIMIT`). Core listing: at most **40,000 UTF-8 bytes** (`CORE_LISTING_BYTES`; target 36,000).
At batch 1 the core listing is 27 legacy tools, 17,706 bytes.

**Legacy names.** `LEGACY_TOOLS` lists the pre-v2 names still registered (live_session_info,
live_tracks, live_get_clip, live_vocal_presets, live_browser_roots, ...). The owning batch
replaces them by registering the final name and deleting the legacy function **in the same
change**; it then regenerates only its own snapshots. Do not keep aliases.

`dom_song` and `dom_probe` stay; `dom_probe` is the dev probe table and is never a public tool.

## 2. Host side: registering a tool

```python
# src/abletonlivemcp/tools/clips.py
from ..models import ClipRef, BatchReceipt          # shared selectors and receipts
from ..server import _call, _overwrite, _read, _untrusted, clip_selector, issue_refs, run_steps

@_read
def live_get_clips(...) -> dict: ...
```

- Decorators (all in `server.py`): `_read`, `_create`, `_overwrite`, `_control`, `_destructive`.
  They register the tool in `SPECS` under the module's toolset, add the annotations preset, the
  mutation lock and refusal-to-ToolError conversion. The function name is the tool name; its
  docstring is the description (short: purpose, units, safety; examples go to prompts/resources).
- `_destructive` tools get the human confirmation (elicitation) automatically; the message lists
  every `targets[i]` with its `expect_name`. A tool must not declare `confirm` itself. Every
  delete/destructive target carries `expect_name` (models `BatchTarget`).
- Bridge calls: `_call(method, params)` (adds the lease); `_generation()` for global writes;
  `_untrusted(data)` around any Live object text in a reply; `shape(rows, response_format,
  concise_keys)` for concise/detailed pages; `_settled(...)` for play/stop/launch readback.
- Refusals: raise `ValueError("...")` for bad input before any call (reported as not applied) or
  `server.unsupported(what, reason)` for an ability Live 12.2 lacks (`refused:unsupported: ...`).
- Tests and scripts call tools as `server.live_x` (module `__getattr__`) or `server.tool("live_x")`.
  The static re-export list is gone; nothing new needs to be added to `server.py`.

## 3. Host helpers (frozen signatures)

| Helper | Signature | Use |
|---|---|---|
| `clip_selector` | `(addr: ClipAddr \| ArrangementClipAddr \| dict) -> dict` | ClipRef -> `{"kind": "clip"\|"arr_clip", track, scene \| arrangement[, take_lane]}` for `ref_issue`. |
| `issue_refs` | `(selectors: list[dict]) -> list[dict]` | Batch preflight. Selectors `{kind, <index selectors>, expect_name?}`, mixed kinds allowed, any length (chunked by 64). One `ref_issue` per chunk, then the exact-name check on every row. Raises before any write. Returns `{kind, ref, name, expect_name}` in input order. |
| `run_steps` | `(steps: list[tuple[str, Callable[[], Any]]]) -> dict` | Several bridge writes in one tool call. First-step failure propagates (true "not applied"); after that, never raises: `{status: complete\|partial, items: [{index, label, outcome, result?, error?}], stopped_at, error}`. Outcomes: `applied`, `not_applied` (bridge refusal), `unknown` (may have applied), `not_attempted`. |
| `unsupported` | `(what: str, reason: str) -> Refusal` | Bounded `refused:unsupported` refusal. |
| `tool` | `(name: str) -> Callable` | The guarded registered function. |

Models (`models.py`): `TrackSel`, `ClipAddr`, `ArrangementClipAddr` (now with `take_lane`),
**`ClipRef`** (either clip address; use it in every clip-taking tool), `DevicePath`, `PadSel`,
`ParamSel`, `ExpectName`, `BatchTarget`, `MAX_TARGETS` (64), `ReadPage`, `WriteReply`,
**`ItemReceipt`**, **`BatchReceipt`** (`status`, `items`, `stopped_at`, `error`, `undo_steps`,
`unverified`), `CapabilityState`, `StructKind`, `DELETE_ROUTES`, `DUPLICATE_ROUTES`,
`ROUTE_ORDER`. Area models go in the batch's own flat file: `models_control.py` (batch 2),
`models_clips.py` (3), `models_devices.py` (4), `models_library.py` (5).

### Receipt rule

Before the first write: a refusal or ValueError, and the text "not applied" is true. Once
execution began: always a receipt (`status: complete|partial`) with per-item outcomes and no
rollback claim. Never report "not applied" for a batch after its first write; never retry an
item whose outcome is `unknown`.

## 4. Remote side: a `dom_*` module

```python
# remote_script/AbletonLiveMCP/dom_clips.py
from .dom_common import READ, WRITE, CONTROL, require, two_pass, for_deletion, position_of
from .safety import ANY_KIND  # only for mixed-kind lists

CAPABILITIES = {  # optional: name -> (state, reason)
    "clip.warp_markers": ("unverified", "P-14 shape only; final proof decides"),
}

def delete_clips(ctx, p): ...

METHODS = {
    "get_clips": (get_clips, READ, ()),
    "delete_clips": (delete_clips, WRITE, (("targets", "ref", ANY_KIND),)),
    "set_clip_loop": (set_clip_loop, WRITE, (("clip", "clip"),)),
}
```

- `METHODS = {name: (handler, classification, targets)}`. Classification `READ`, `WRITE` or
  `CONTROL`. Targets: `()` (global; the request must carry `generation`), `(param, kind)` for one
  reference, or `(list_param, item_param, kind)` for a list of objects (max 64). `kind` is a
  reference kind (exactly `safety.PARENTS`: `track`, `return_track`, `master`, `scene`, `cue`,
  `slot`, `clip`, `device`, `chain`, `drum_pad`, `param`, `mixer_param`, `take_lane`,
  `arr_clip`) or `ANY_KIND`, which makes every item name its own `kind`.
- Method names are global: a duplicate across modules fails the import. Handlers receive
  `(ctx, params)` with `ctx.targets[param]` already resolved (`.obj`, `.nodes`, `.path`).
- **Exact-name check is done by the gate**: a single-target method's `params.expect_name`, and
  each list item's `expect_name`, are compared with the object's current `name` before the handler
  runs (`refused:name_mismatch`). Handlers do not re-check.
- Undo: every WRITE runs inside one undo step (handlers.make_dispatch). Exempt: `probe_run`,
  `undo`, `redo` (`handlers.OWN_UNDO_STEPS`). Batch 2 must name its bridge methods exactly
  `undo` (and `redo` if split).

### Remote helpers (`dom_common`)

| Helper | Use |
|---|---|
| `require(ctx, name, members=()) -> state` | Capability gate before any native call: `refused:unsupported` when the capability is undeclared, `disabled`, `unsupported`, quarantined, or an `(obj, attr)` member is missing. Returns `supported`/`unverified`; put `unverified` names in the reply's `unverified` list. |
| `unsupported(what, reason)` | The `Refused("unsupported", ...)` to raise before any write. |
| `quarantine(ctx, name, why)` | After an unknown outcome: closes that capability for the life of the script. |
| `capability_report(ctx)` | `{name: {state, reason}}` for `live_hello` (batch 2 adds it to the hello reply). |
| `two_pass(items, validate, write)` | `validate(i, item)` for all items first (may raise: nothing written), then `run_writes`. |
| `run_writes(prepared, write)` | Pass 2; never raises; `{status, applied, items[{index, outcome, result?, error?}], stopped_at, error}`, outcomes `applied`/`unknown`/`not_attempted`. |
| `for_deletion(resolved)` | Orders structural-delete targets deepest/highest first. Delete by identity: `position_of(seq, obj)` at write time, never the issued index. |
| `position_of(seq, obj)` | Current index by identity. |
| `clip_address_nodes(song, addr)` | `{track, scene}` or `{track, arrangement[, take_lane]}` -> reference nodes (reads that issue clip refs). |
| `reference_nodes(song, p)` | Existing: any selector -> nodes (used by `ref_issue`). |

## 5. Delete / duplicate routes

The public `live_delete` and `live_duplicate` (batch 2, `tools/tracks.py`, `_destructive` for
delete, `_create` for duplicate) take mixed `targets`, run `issue_refs`, group them by kind and
call the fixed bridge methods in `models.DELETE_ROUTES` / `DUPLICATE_ROUTES` in `ROUTE_ORDER`
(clips, devices, scenes, tracks/returns), one `run_steps` step per route. A kind with no route is
refused with `unsupported` before any write (device duplication: absent on 12.2, P-01).

| Route method | Owner | Remote module | Target spec |
|---|---|---|---|
| `delete_clips`, `duplicate_clips` | batch 3 | dom_clips | `("targets", "ref", ANY_KIND)`, kinds `clip`/`arr_clip` |
| `delete_devices` | batch 4 | dom_devices | `("targets", "ref", "device")` |
| `delete_scenes`, `duplicate_scenes` | batch 2 | dom_scenes | `("targets", "ref", "scene")` |
| `delete_tracks`, `duplicate_tracks` | batch 2 | dom_tracks | `("targets", "ref", ANY_KIND)`, kinds `track`/`return_track` |

Every route takes `targets: [{kind, ref, expect_name}]` and returns a `run_writes` receipt.
Batch 2 may build and test the facade against stubs of the batch-3/4 routes; until its batch
merges, a route method is unclassified and the gate refuses it (fail closed, nothing applied).

## 6. Operations and `live_get_operation`

- Device loads keep the existing pending-load protocol (`operations.Operations.begin/settle`).
- Any other bounded multi-tick operation (cue seek/observe/toggle, slow readbacks) uses
  `ctx.operations.start_task(kind, step, timeout<=10)`: `step()` is called once per tick and
  returns None (pending) or a result dict (`ready`); a raise or timeout makes it `unknown`
  (`may_have_applied`), never retried. Return the snapshot (`{operation, kind, state, ...}`) from
  the write.
- Polling: bridge method `operation` with `operation: id`, or `operations: [ids]` (1..16) for one
  read of several; an unknown id reads as `state: unknown_operation` in its row. `live_get_operation`
  (batch 4 owns the tool) exposes both. States: `pending`, `ready`, `failed`, `unknown`.

## 7. Final proof (`scripts/live_v2_final.py`)

One long-lived stdio client, `ABLETONLIVEMCP_TOOLSETS=all`, deterministic elicitation, scratch
ledger. Scenario data: `scripts/final_cases/{control,clips,devices,library,mcp}.json` (batch 2, 3,
4, 5, 6 respectively; JSON lists, schema in the runner's docstring), optional hooks in
`scripts/final_cases/<file>.py`. Phases, in order: `connection`, `shared_fixture`,
`browser_devices`, `musical_edits`, `assembly`, `arrangement_control`, `safety_destructive`,
`offline_mcp`, `persistence_finish`.

- Every registered tool must be named by a scenario (`--check` verifies the manifest and coverage
  offline, without Live). Run it before handing a batch back.
- Scratch objects are named `ALMCP-FINAL <run> <label>` through the ledger (`"own"` in a step);
  a destructive confirmation is accepted only when the step says `"confirm": "accept"` and every
  target's `expect_name` is ledger-owned.
- `--only id,id` reruns failed scenarios and merges the results. Exit 0 pass, 1 failure or
  coverage gap, 2 could not run. Evidence: `docs/release/v2-fast-track.md` (+ `.json`, ledger).

## 8. Tool-surface snapshots

`ABLETONLIVEMCP_UPDATE_SURFACE=<module>[,<module>]` rewrites only those modules' snapshots (and
deletes a named module's file when it has no tools left); other modules' files are never
touched. `ABLETONLIVEMCP_UPDATE_SURFACE=all` is the integrator's single global refresh after
merges. The test also enforces the counts, the 40,000-byte UTF-8 core listing and the
module/name table.

## 9. Things each batch must know

- Batch 2: `live_undo` bridge methods are `undo`/`redo`; add `capability_report(ctx)` to the
  hello reply; own `live_delete`/`live_duplicate` and the track/scene routes.
- Batch 3: clip tools take `ClipRef` and use `clip_selector`; own `delete_clips`/`duplicate_clips`
  (session and arrangement clips through `ANY_KIND`).
- Batch 4: own `delete_devices`, `live_get_operation` (single and multi-id), and replace
  `live_vocal_presets`/`live_browser_roots` (they are not in the final surface).
- Batch 5: host-only modules; nothing remote except dom_labels.
- Batch 6: fill `resources.register(server)` / `prompts.register(server)`; `server` is the
  `abletonlivemcp.server` module (`server.mcp`, `server.SPECS`).
- Everyone: no new shared helpers; area models in your `models_<area>.py`; refresh only your
  snapshots; add your scenarios to your case file and run `live_v2_final.py --check`.
