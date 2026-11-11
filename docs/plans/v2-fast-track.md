# v2 fast track: build once, prove at the end

Status: Reviewed recommendation (plan reviewer, 2026-11-11). Not owner release approval.

## Verdict

Replace the nine-wave execution plan. Its capability inventory is useful; its probe-first dependencies, per-ticket Live proofs, simulator and repeated acceptance runs are excessive for a light MCP. Keep the existing bridge, reference gate, leases, receipts, load quarantine, undo grouping and elicitation. Add domain capabilities to those foundations, not another framework.

Complete six build batches below, merge them, and only then open the testing phase. Delegates write their unit tests with the implementation but do not execute tests, builds, smoke scripts, probes or Live during development. No domain gets a later enhancement ticket before the final proof. Static reading and diff review are allowed throughout.

The current checkout has 27 registered tools, implemented core handlers and empty opt-in modules. `server.py` already supplies the registry, decorators, toolsets and refusal handling; `models.py` already supplies selectors, pages and receipts; `dom_common.py` already supplies reference issuing for the full tree. Reuse these. Do not treat the empty `tools/racks.py` or `dom_racks.py` as implemented features.

### Specific cuts, merges and deferrals

| Decision | Ticket / probe / tools | Reason |
|---|---|---|
| KEEP DONE | T-001..T-007 and their recorded successful checks | Foundations are merged; rebuilding or re-proving them mid-build wastes days. Open acceptance dependencies remain final checks. |
| CUT | Wave 1 as a blocking probe campaign | Existing evidence plus guarded implementations is sufficient to start all domains now. |
| CUT | Per-domain `live_*_test.py` runners, per-ticket evidence ceremonies, T-082's replay of every old script | One shared fixture and one final scenario eliminate repeated startup, setup and cleanup. Keep existing scripts as historical utilities. |
| MERGE | T-010 + T-019 + T-073 + T-075 + T-076 | Session state, recording, diagnostics and selection share one implementation ownership boundary. |
| MERGE | T-013 + T-014 + T-071 + T-072 + T-074 | Clip addressing, note edits, markers, arrangement and envelopes must be designed together, not reopen notes/clips later. |
| MERGE | T-015 + T-016 + T-018 + T-031 + T-033 + T-050 + T-051 + T-077, with T-030/T-032 | Browser placement, nested devices, drums and rack assembly share dependencies; one owner must finish the entire device area. |
| SPLIT OWNERSHIP | T-017 | Track/scene operations belong to batch 2, clip operations to batch 3, device operations to batch 4; one public delete/duplicate facade dispatches to fixed domain methods. |
| MERGE | T-034 + T-060 + T-061 + T-062 + T-063 | Reuse the existing offline reader and usage code; labels and usage drive organization without a separate planner service. |
| MERGE | T-020..T-023 into the owning batches and final surface check | Resources delegate to existing read implementations; descriptions, annotations and contracts are part of each tool, not later waves. |
| CUT TOOL | `live_vocal_presets` | Serve the static presets through the vocal-chain prompt/knowledge instead of another tool. |
| CUT TOOL | `live_plan_organize` | A prompt produces one `live_set_tracks` batch from labels and usage; no new execution mechanism is needed. |
| MERGE TOOLS | `live_plan_fx_rack` / `live_build_fx_rack` into `live_plan_chain` / `live_build_chain` | A typed rack mode reuses the existing plan store, target fingerprint and receipts. |
| MERGE TOOLS | `live_get_song_advanced` / `live_set_song_advanced` into session get/set | Groove, Link and available tuning fields are session properties. |
| MERGE TOOLS | `live_select`, `live_preview` into `live_view` | A small fixed action enum covers selection, view and audition without three registrations. |
| MERGE TOOLS | `live_knowledge_search` / `live_knowledge_read` into `live_knowledge` | One read-only tool with explicit `search`/`read` actions preserves both abilities. |
| CUT ALIASES | Old singleton create/set/fire names and `live_browser_roots` | Register only final batch names; roots are `live_browser_list()` and launch is `live_launch`. Update existing consumers once. |
| DEFER | T-052, `live_write_rack_preset`, generated `.adg` loading | P-29 offline inspection does not prove Live accepts generated mappings; do not introduce preset-writing machinery now. |
| DEFER | T-080 simulator, twelve-task eval suite | Duplicates Live semantics and delays delivery; use the real final proof and small boundary tests. |
| DEFER | T-081 competitor parity publication | Verify primary repos immediately before public release; the memory-based matrix is not a build dependency or a verified claim. |
| DEFER | T-083 WAV analysis | Adds a new analysis product; stdlib RMS is not a defensible LUFS implementation. |
| DISABLE ON 12.2 | T-071 split, arrangement move via duplicate/delete, take-lane creation/editing covered only by P-19 | Native crash risk cannot be caught by Python and cannot be allowed to destroy the single final session. Preserve reads and independently proven creation paths. |
| CUT UNSUPPORTED WRITES | T-075 count-in setter, absent tuning fields; native macro mapping, follow actions, freeze, device duplication | Recorded absence/read-only behavior is a product limit, not a reason for more experiments. Expose readable state and explicit refusal. |

Do not defer the ordinary native capabilities merely to hit a tool count. Mixer, routing, extended notes, session automation, device ordering, racks, pads, Simpler, conversions, recording, MIDI files and arrangement reads all remain in the build. Unverified branches are advertised accurately and gated as described below.

### Tool and payload budget

**Hard caps: 30 core tools; 58 tools across every toolset combined. Planned total: 57 (30 core + 27 opt-in).** No aliases, no probe tools, no generated per-device tools. The spare slot is not permission for scope growth.

Core retains the detailed plan's surface minus `live_vocal_presets`: hello; session get/set; transport; undo; tracks get/create/set; mixer set; scenes get/create/set; launch; clips get/create/set; notes get/edit; device parameters get/set; devices set/move; browser list/search; operation get; chain plan/build; load item; delete/duplicate. That is exactly 30 registrations.

| Opt-in surface | Count |
|---|---:|
| Drums: get/set pads, convert, get/set Simpler, plan/build drum rack | 7 |
| Racks: get/set rack (FX assembly uses core chain plan/build) | 2 |
| Organize: get/set labels | 2 |
| ALS: scan projects, usage report | 2 |
| Library: `live_knowledge` | 1 |
| Arrangement: get, cue edits, create clips, edit clips | 4 |
| Automation: get/set | 2 |
| Recording: record | 1 |
| Editing: audio clip edit | 1 |
| View: `live_view`, including selection and preview | 1 |
| Advanced devices: extras get/set | 2 |
| Files: MIDI import/export | 2 |
| **Opt-in total** | **27** |

Keep `core` default and opt-ins explicit. Preserve existing toolset names as configuration compatibility entries even when they contain no standalone tools; `experimental` remains empty and excluded from `all`.

Retain the existing **40 * 1024 byte** serialized core listing limit, with a stricter **40,000 UTF-8 byte** release target including tool names, descriptions, annotations, input and output schemas. Target 36,000 bytes to leave headroom. Count bytes, not Python characters. Tool count alone does not establish this budget.

Each tool gets a short purpose, units and safety semantics, not a 150-word mini-manual. Put examples, bar/beat conversion and tutorials in prompts/resources. Reuse the current compact page/write envelopes; avoid repeating deeply expanded selector and result schemas in every union branch. Keep validation typed: if the final listing is too large, simplify equivalent schema structure and prose, never replace inputs with opaque JSON or silently drop abilities. The offline final surface check is a release blocker until both count and byte limits pass.

## Evidence to build from, not rerun

Read the individual observations, not just the verdict label. All paths below are under `docs/release/probes/` unless stated otherwise.

| Evidence | Binding implementation consequence |
|---|---|
| P-01 go | Runtime member inventory exists; `insert_device`, follow actions and device duplication are absent on 12.2. `hasattr` establishes presence, not writable behavior. |
| P-02 go | Types and in-session round trips work, including 4 KB JSON; the evidence explicitly says `needs_reopen_check:true`. Persistence after save/reopen is still an outstanding final check. |
| P-03 go | Three changes undo together without swallowing the previous marker. Do not rerun its probe; finish the public-tool acceptance through one final batch undo. |
| P-06 go | dB conversion can be computed entirely inside one remote call; accept numeric tolerance, not an exact `-6.0 dB` string (observed `-5.992 dB`). |
| P-07 go | Mutate objects from the raw tuple returned by `get_notes_extended` and pass that tuple to `apply_note_modifications`. Notes beyond clip end are retained outside the default read window, not necessarily dropped. Use returned IDs and an adequate read span. |
| P-08 go | Session audio import and arrangement audio/MIDI creation have working shapes; use absolute paths, audio-only targets for audio, and identity/readback verification. |
| P-09 go | Construct additions with `type(existing_marker)(...)`; dicts/floats are rejected. Validate bounds before writes; widen markers before narrowing. No existing marker/type means refuse that addition. |
| P-10 go | Session envelopes work; arrangement `automation_envelope` returns None. Refuse arrangement automation explicitly. |
| P-22 go | Scale, groove amount, MIDI recording quantization and Link writes work. Count-in has no setter; named tuning fields are absent; clearing clip groove with None failed. Do not promise those writes. |
| P-23 go | Diagnostics and view names are known. It did not prove every view mutation. |
| P-24 go | Track/scene/detail-clip selection works. `select_device` does not imply selected track changes. Chain and pad selection are explicitly untested. |
| P-27 go | Display writes work for tested controls. Quantized defaults and unquantized value-items can raise; return availability per field. Active overridden automation state was not tested. |
| P-04/P-05 files currently present | These are partial **no-go** evidence, despite the brief's older pending description. Cross-track movement worked; reorder/chain coverage is incomplete. Deletes/duplicates mostly worked, but track-delete undo did not restore the fixture and device deletion was unobserved. Do not call these full passes. |
| P-29 offline helper, `scripts/adg_schema_probe.py` | Schema inspection only; `probe_p29.py` remains a stub. No generated-preset Live proof exists. |

P-11..P-20 have no completed evidence files here. P-14/15/16 are multi-stage; P-11/12 need a loaded rack/kit. Reuse their source as call-shape research, not as acceptance. Do not run those probe runners before implementation.

## Six build batches and file ownership

Batch 1 establishes the complete integration contract in one pass. Then batches 2–6 use separate worktrees based on that contract and run in parallel as capacity permits. They merge only after all five finish. One designated integrator owns merges and the final proof; delegates do not use Live or start further delegates.

Each batch includes all host tools, remote handlers, domain request/result models, small unit tests and scenario data for its area. Tests are authored now and executed only in the final phase. Use at most one small test per feature/boundary; do not build another fake Live. Existing unit suites run once at the end for regression coverage.

Shared-file rule: only batch 1 edits `server.py`, `models.py`, `tools/__init__.py`, `handlers.py`, `safety.py`, `dom_common.py` and the shared harness. Other batches put new domain models in new flat `src/abletonlivemcp/models_<area>.py` files. Flat remote modules remain mandatory for the installer. Freeze exact exported helpers, method names and JSON fixtures in batch 1; no delegate opportunistically edits a shared file.

### Batch 1 — integration and safety contracts

- **Folded tickets:** remaining T-002/T-005/T-006/T-007 integration seams; common parts of T-017/T-020/T-022/T-023/T-082. Do not redo completed implementations.
- **Owns:** shared files named above; `src/abletonlivemcp/proof_contract.py` (if needed for typed scenario metadata); `scripts/live_v2_final.py`; `scripts/live_harness.py`; `tests/test_tool_surface.py`; one shared contract test; final proof manifest and evidence output path `docs/release/v2-fast-track.md`. Owns the final pass over README/HANDOFF/todo and packaging metadata after domain merges; no other worker edits these.
- **One-pass work:** remove stale server re-exports of renamed tools; retain fixed module imports; provide reference resolution for session and arrangement clip addresses, mixed batch references and exact-name checks; define fixed deletion/duplication dispatch routes; define bounded capability states; exclude undo/redo themselves from automatic undo wrapping; retain elicitation. Resources/prompts registration hooks and tool-count/UTF-8 budget checks are settled here.
- **Contract:** a public delete/duplicate facade in batch 2 calls fixed per-domain methods from batches 2–4. Validate all targets and values before writing; sort structural deletions safely and retain identities rather than re-resolving shifted indices. Post-write failure returns a partial/unknown receipt, never `not applied`. Do not claim atomic rollback. Keep the existing reference-read then gated-write pattern; validate/write/readback occur inside that write call wherever possible.
- **Evidence:** P-01/P-03; T-005's 58 passing checks. Outstanding cue, public batch undo and destructive-tool acceptance go only in the final scenario. No probe or test execution.

### Batch 2 — session, tracks, scenes and control

- **Folded tickets:** T-010/T-011/T-012/T-019/T-073/T-075/T-076 plus track/scene portions and public facades of T-017.
- **Owns:** `tools/{session,tracks,scenes,recording,song,view}.py`; `dom_{session,tracks,scenes,recording,song,view}.py`; `models_control.py`; domain tests/snapshots for these modules; `scripts/final_cases/control.json`.
- **One-pass work:** finish all session fields, transport, mixer/sends/master, routing, track/scene CRUD, launch, diagnostics/build ID/variant, record controls, view/select/audition. Fold song extras into session tools; register only one view tool. Default ordinary writes retain read-only policy and safety gate.
- **Evidence:** P-01/P-06/P-22/P-23/P-24 and partial P-05. P-17 routing and P-18 recording remain unrun: implement allowlisted member/target checks and clear unsupported refusals; the final session qualifies only safe scratch paths. Never set count-in or absent tuning fields. Track-delete undo restoration remains a required final acceptance, not an assumed capability.

### Batch 3 — clips, notes, arrangement and envelopes

- **Folded tickets:** T-013/T-014/T-070/T-071/T-072/T-074/T-078 plus clip portions of T-017.
- **Owns:** `tools/{clips,notes,arrangement,automation,editing,files}.py`; `dom_{clips,notes,arrangement,automation,editing}.py`; `models_clips.py`; new host MIDI codec module; associated tests/snapshots; `scripts/final_cases/clips.json`.
- **One-pass work:** one final clip-address model used by notes and clip setters from day one; all extended note fields, IDs, transformations, MIDI import/export, clip properties, warp edits, session automation, arrangement reads and P-08-proven direct creation. Clip delete/duplicate handlers follow batch 1's fixed interface.
- **Evidence:** P-07/P-08/P-09/P-10; partial P-05; T-005 cue caveat. P-16 remains unrun: implement asynchronous cue seek/observe/toggle/observe with a bounded operation record, stopped transport and exact-time verification. Reuse `live_get_operation` to observe completion; never immediate seek+toggle. Existing cue at target is reused, never toggled away. End proof discovers safe cue behavior. P-19 crash-prone branches stay disabled on 12.2 and receive refusal checks only; do not run the twenty-operation crash experiment.

### Batch 4 — devices, browser, chains, drums and racks

- **Folded tickets:** T-015/T-016/T-018/T-030/T-031/T-032/T-033/T-050/T-051/T-077 plus device portions of T-017; excludes T-052.
- **Owns:** `tools/{devices,browser,chain,drums,racks,devices_advanced}.py`; `dom_{devices,browser,drums,racks,devx}.py`; `operations.py`; host `chain.py`, `resolve.py`; `models_devices.py`; domain tests/snapshots; `scripts/final_cases/devices.json`.
- **One-pass work:** nested/return/master parameters and defaults; on/off/name/collapse/order; expanded load roots and placement verification; MIDI/return chains; pad edits/copy/clear; conversions; Simpler/slices; rack macros/variations/chain mixers; drum builder; typed FX-rack mode in existing chain plan/build. Keep manual macro-mapping instructions explicit. Device extras remain two opt-in tools.
- **Evidence:** P-01/P-24/P-27, partial P-04/P-05, P-08's audio fixture shapes. P-11/12/13/14/15/20 remain unrun: implement defensively now, with independent gates for each operation/target combination. A stock kit and mapped rack loaded once in the final session supply all fixtures; no plugin shopping or two-plugin probe campaign. Final safe qualification uses existing fixed probes only for unresolved native call shapes that cannot yet be reached safely through a tool; then call the public tool once. P-14's stages share that fixture and Live process. A failure gates just the affected target/action, not the entire device toolset.
- **Limits:** unknown placement is `unknown`, quarantines that target and is never retried. Grouping requires a real destination chain; loading an empty rack does not establish that chain exists. If no safe route creates it, return unsupported before moving anything. Drum construction requires a positively qualified route; no speculative fallback cascade after writes start.

### Batch 5 — offline usage, labels and knowledge

- **Folded tickets:** T-034/T-060/T-061/T-062/T-063.
- **Owns:** `tools/{als,organize,library}.py`; `dom_labels.py`; host `als/*.py`, `knowledge.py`; `models_library.py`; labels sidecar implementation; associated tests/snapshots; `scripts/final_cases/library.json`. Read existing `knowledge/`; do not rewrite its content.
- **One-pass work:** reconnect existing reader/index, add confinement and decompression/entity/node limits, plugin recency, labels with atomic global sidecar writes, one read-only knowledge tool. No organize-planner tool; batch 6's prompt uses labels/usage plus one track-set call.
- **Evidence:** P-02 proves in-session metadata. Persistence survives only if final save/reopen passes. Generate a scratch Set containing the Core Library samples used by batch 4 and scan that saved file offline; no private owner sample project is required. Test reparse/path escape offline at the end, not in Live. Knowledge reads need no bridge calls.

### Batch 6 — resources, prompts and distributable integration

- **Folded tickets:** T-020/T-021 and documentation parts of T-022/T-023; necessary private packaging work from roadmap P2. No T-080 simulator or public release.
- **Owns:** new `src/abletonlivemcp/{resources,prompts}.py`; project `SKILL.md`; package-data configuration in a new batch-owned support file if needed; prompt/resource contract tests; `scripts/final_cases/mcp.json`. Batch 1 alone applies any required `pyproject.toml` integration edit from the agreed contract.
- **One-pass work:** resources call the already specified read implementations; prompts cover vocal chains, organization, scene setup, mixing, diagnosis, safe tweaks, drums, manual macro mapping and supported arrangement assembly. Static vocal presets move here. Keep knowledge files included in the distribution. Record genuine limits in tool-facing guidance.
- **Evidence:** existing stdio/harness infrastructure. All registration, resource and prompt checks are offline final checks except one aggregate read-through in the final session. No independent real-Live prompt demonstrations.

## Single end-of-project proof

This is a plan for the implementation phase, not authorization to run anything during this review. No tests or Live runs were performed to write this document.

### Before starting Live

After all six batches merge, run the existing unit suite, new small boundary tests, lint and package/import checks **once** using the repo venv. Generate all surface snapshots in one controlled pass and review their diff; workers must not use the current global snapshot updater concurrently because it deletes other modules' snapshots. Assert core count <=30, all count <=58, core listing <=40,000 UTF-8 bytes, final names only, output schemas and annotations present, unknown-toolset refusal and clean stdio. Validate prompts/resources and offline file confinement in the same run. Fix all collected offline failures together before Live.

Build one coverage manifest from the actual registered 57-tool surface, not a handwritten count. Every tool has a scenario ID, fixture dependencies, expected success or supported refusal, and evidence field. A missing tool scenario fails coverage. Scenario fragments above are data for this one runner, not five separate harness launches.

Install all final remote files once and invoke `scripts/live_restart.ps1 -Reinstall` **once**, opening an agent-created disposable Set. Keep a saved baseline fixture for later reopen. Temporarily enable test writes; turn dev probes on only for fixed unresolved qualifications; restore both private config values in `finally`. Never open the owner's working Set. Every Set, clip, track, cue, output file and label written by this run is scratch, including global labels under an isolated test data directory.

### One ordered script / one Live process

Use `scripts/live_v2_final.py` with the existing harness and a single long-lived MCP client, `all` toolsets enabled, a deterministic elicitation callback and a scratch ownership ledger. Call **every registered tool at least once**; combine fields and targets in those calls. A tool invocation is not every enum permutation. Add calls only where later readback, undo, safety refusal or an asynchronous outcome requires them.

| Order | Minimal required checks |
|---|---|
| 1. Connection | One hello: version, modules loaded from Log.txt, enabled toolsets, capability reasons, no blocking dialog. Capture initial policy and scratch ownership. |
| 2. Shared fixture | One create-tracks batch for MIDI/audio/return; two scratch scenes in one call; name/color/mute/monitoring and mixer writes in batches. Session get/set and transport play/seek/stop; record control has bounded duration and restores stopped/unarmed state. Master changes occur only in the disposable Set. Check mixer dB within 0.05 dB. |
| 3. Browser/device fixture | Roots/list/search once each; load stock instrument, effects, a mapped rack and a stock drum kit once each, with bounded operation polling and identity placement checks. Reuse them for parameters, extras, device settings/order, racks, pads and Simpler. Qualify unresolved safe P-11/12/14/20 cases here only; conversions use the same loop. Plugins are optional: absent plugin yields a capability/refusal result, never an owner task. |
| 4. Musical edits | Create MIDI/audio clips in one batch; notes add/modify/remove/transform with ID and count readback; set all applicable clip fields together; one audio-edit request; automation write/read/clear with five sampled values <=2% error. MIDI export/import notes compare offline against the same clip. Reads supply assertions for preceding writes. |
| 5. Assembly | Plan/build one short MIDI instrument chain; plan/build one drum rack using the same samples; FX-rack mode runs only after safe chain placement qualification. Verify order/sample identity and receipt status. Cap the drum proof at three roles (kick/snare/hat), not eight copies of the same route. |
| 6. Arrangement/control | Read arrangement; direct P-08-safe create and marker edit; note addressing on that clip. Cue add/rename/jump/delete follows the asynchronous protocol and exact-time checks. View selection/preview runs on the same scratch fixtures and stops audition. P-19-only branches and arrangement automation return `refused:unsupported` without entering native mutation code. |
| 7. Safety and destructive integration | One mixed invalid-target batch must write nothing; one name mismatch; one held old reference must fail after a scratch reorder/delete. Rename three scratch tracks, undo once through the public tool, then verify all three originals (T-006's pending acceptance). Accept deletion of duplicates, decline one delete, and check declined/missing-confirmation targets survive (T-007's pending acceptance). Separately verify scratch track-delete undo restores the deleted track, resolving partial P-05 evidence. Clear/copy/replace branches use proper destructive confirmation. |
| 8. Offline-backed tools and MCP reads | Set/get labels; save the scratch Set via external UI automation; scan it once and run usage aggregation; knowledge search/read; list/get prompts and read all resources using existing fixture values. Organization uses one batch setter already exercised above. |
| 9. Persistence and finish | Close/reopen the **same saved scratch Set without restarting Live**, then verify the 4 KB P-02 sentinel and new labels. This is the outstanding reopen check, not repetition of P-02's in-session cases. Do it last because a Set change invalidates refs/plans. Assert manifest coverage, scratch-only writes, no unexpected Live errors, and restored read-only/dev flags. Leave no recording, audition or transport running. |

Do not run historical per-ticket proofs or standalone completed probe scripts inside this runner. For unrun safe native behavior, permit a bounded fixed-probe qualification immediately before its tool case only when necessary. Gates stay closed if qualification fails. Presence-only `hasattr` checks do not unlock a write, and catching an exception does not make a native crash safe.

The target is **120–180 bridge round trips**, including fixture setup, bounded polling, unresolved safe qualifications, readbacks and cleanup. At 0.9 s/call that is 108–162 seconds of bridge latency. Budget **10–15 minutes total**, including one restart/install, stock loads, save/reopen and settling; **20 minutes is the investigation threshold**, not permission to restart all proofs. Offline final checks budget a separate 3–5 minutes. These are estimates, not measured results. Record actual bridge-call count and wall time. Poll related operations in a single bounded read when the contract supports it; never poll every parameter/note separately.

### What is excluded, and what failure means

Excluded from rerun: completed T-001 split/install regressions as standalone proofs; passed Wave 0 scenarios; T-005's 58 checks; P-01/P-03 and completed cases of P-02/P-06/P-07/P-08/P-09/P-10/P-22/P-23/P-24/P-27; old vocal/audio-chain scenarios; already-passing offline P-29 inspection. The final tool calls exercise their new integration, not the old exhaustive probe cases. Unproved parts identified above are not silently counted as excluded passes.

An expected unsupported result passes the gate check, **not the musical capability**. Evidence must list successful capabilities, safely unavailable capabilities and failures separately. An unrun branch cannot become advertised support just because its tool name was called.

Collect all independent failures in one report; skip dependents after a fixture failure and record them as blocked, not passed. A mismatch, unexpected refusal on a required supported path, wrong placement, unsafe partial result, missing coverage or policy failure triggers **one fix-batch across all affected areas**. Review all fixes together. Then rerun only failed/blocked scenario IDs and their necessary fixture setup. Include a previously passing check only if a shared fix invalidated its evidence. No whole-suite or whole-Live-proof replay by habit.

A remote-script correction necessarily needs another install/restart for the repair pass; do not claim a universal one-restart guarantee after failures. The first acceptance attempt uses one restart. A native crash stops the session, preserves evidence and disables that operation before the same aggregated repair pass. P-19 remains disabled precisely to avoid this preventable case.

## Risks and cheap guards

| Rework trigger | Guard before the final run |
|---|---|
| Wrong unrun Boost/Python signature | Fixed allowlisted adapter per action; member/target checks; unsupported before writes if shape is unknown; qualify safe unresolved cases only at the end. No argument-driven reflection escape hatch. |
| P-04 reorder fails or destination rack has no chain | Distinguish same-track/cross-track/into-chain gates; refuse unsupported movement before relocating anything; build correct order directly where possible. |
| P-14 hotswap loads into wrong object | Explicit track plus device/chain/pad selection verification; bounded identity-diff completion and target quarantine on unknown. No automatic second load. |
| P-05 delete undo differs from grouped edit undo | Do not promise rollback; destructive confirmation and original identity/name in receipt; deletion-restoration assertion stays in final acceptance. |
| Late playhead makes cues toggle the wrong locator | Multi-tick seek/readback then toggle, stopped transport, exact target time, owned cue identity and bounded timeout. Never use the existing lab's immediate sequence. |
| Native arrangement crash | Disable P-19-dependent paths on 12.2 regardless of `hasattr`; direct creation is limited to P-08-proven shapes. No crash stress probe in acceptance. |
| Note or marker adapters serialize native structs | Preserve the raw note tuple; derive WarpMarker class from an existing marker; plain JSON is host transport only. |
| Partial batch mutation reported as refusal | Two-pass validation; preflight every item; receipt records partial/unknown after execution begins. No false all-or-nothing or undo rollback claim. |
| `live_undo` accidentally wrapped in a new undo step | Batch 1 dispatch excludes undo/redo explicitly; end test uses public batch edit plus undo. |
| Oversized core schema | Fixed 30-tool allocation, compact descriptions/envelopes and one final serialized UTF-8 budget check; no aliases. |
| Parallel models/snapshots conflict | Shared contract frozen first, unique domain models, one owner per existing file, snapshots refreshed globally once after merges. |
| Labels disappear after reopen | Keep new labels/sentinel in saved scratch baseline and verify last without process restart; global sidecar is isolated and atomic. |
| ALS scan/knowledge/file import escapes roots or expands malicious XML | Reuse reader, bound gzip/XML/nodes, reject entities, validate resolved Windows reparse targets; small offline boundary tests at the end. |
| Optional plugins/packs/M4L absent | Stock/Core Library fixtures only; per-capability unavailable reason. Never make purchase/installation a proof prerequisite. |
| Assembly gates close and UC1/UC4 cannot complete | Report those outcomes as unavailable; ship proven pad/rack editing and manual mapping guidance. Do not hide failed assembly behind a successful refusal test. |
| Reference projects contaminate licensing | Ziforge and pylive remain ideas/checklists only; independently implement against API dump and our evidence, never copy their code. |

## Owner-only items remaining

1. Public release decisions: repository public flip, release/tag/version approval, registry publication and final package names if account ownership is involved.
2. Account credentials, registry/API tokens, payments or purchases actually required for publication or optional products; request secrets through the supported secret flow, never chat or committed files.
3. Consent to enable ongoing writes against the owner's real working Sets outside the authorized scratch-test environment; keep read-only default until then.
4. A Live upgrade decision only if the owner wants capabilities unavailable on the 12.2 floor. It is not required to complete this plan.

There are no owner-only development prerequisites. Restarts, installs, service recovery, test execution, scratch samples/Sets, safe cleanup and documentation alignment are agent work. Existing approvals stay settled. Bundled samples and an agent-created saved Set replace the stale HANDOFF requests for owner samples. Manual macro mapping is an explicitly documented Live 12.2 product limit; automatic mapping and T-052 are deferred, not a hidden owner blocker.
