# v1 public release plan

Status: Reviewed
Approved by owner 2026-11-10 (via /goal)
Size: L
Date: 2026-11-10

## 1. Goal and meaning of v1

Deliver a small, stock-first, user-directed chain and Session View assistant that a stranger can install from an artifact, connect through an MCP client, understand, and use without silent substitutions, wrong-target writes, hidden paid calls, or destructive upgrades. The client supplies language understanding and musical judgment; the server supplies established mixing conventions, explicit device mappings, bounded actions, and readbacks. The user chooses the work and evaluates the sound. Here “v1” names the first useful release scope, not a commitment to a `1.0.0` tag. Completion means **ready for the owner to flip**: verified artifacts and instructions, a recorded Windows Live 12.2 acceptance pass, and an owner release checklist. It does not authorize publication, tags, account changes, a new name, or a licence change.

## 2. Scope IN and scope OUT (WON'T-YET)

### IN: the release contract

| User story | Bounded outcome |
| --- | --- |
| US1: Install, connect, and diagnose | One pinned local-wheel/venv installation recipe outside the checkout; bundled Remote Script; safe reinstall; one tested stdio client recipe; authenticated status reporting server/script/protocol/Live versions, supported methods, write policy, and actionable failures. |
| US2: Inspect the current Set | Bounded tracks, returns, master, scenes, clip slots, top-level devices, and exposed parameters, with explicit omissions/continuations and stable target references. Empty slots are data, not errors in a slot listing. |
| US3: Plan and build a stock vocal chain | Four existing roles (`eq`, `compressor`, `saturation`, `reverb`), both existing vocal starting points, custom stages, exact browser paths, physical settings, and a read-only preview. Build starts on an empty regular audio track; later stages append only to that operation's verified device prefix. |
| US4: Use my own devices and taste | Validated per-user preferences and a small declarative adapter file, without editing site-packages. Stock fallback is deterministic. Pro-C 2 is the first optional third-party profile if real evidence passes; its absence never blocks stock release. Unverified mappings and unsupported intentions stay explicit. |
| US5: Adjust an existing processor | Raw or physical-unit batch writes to an identified top-level device, options before dependent values, automation/enabled-state checks, discovered activator bypass, original-value receipts, and verified readback. Applies to devices on regular/return/master tracks where supported. |
| US6: Organize and mix an existing track | Name/color regular tracks; inspect and set level in dB, pan in a declared normalized domain, mute/solo, and existing sends addressed by return identity. Inspect return/master mixers; only supported fields are writable. No new routing system. |
| US7: Set up a Session scene | Create/name a scene and audio/MIDI tracks; create/name/color a MIDI clip in an empty slot; add/read notes; change tempo; launch/stop clip/scene/transport with honest triggered/pending/playing state. |
| US8: Refuse safely and explain partial work | Wrong credentials, old scripts, read-only policy, stale objects, occupied chain/slot, incomplete inventory, unsupported settings, timeouts, and failed later stages cannot become misleading success or automatic retries. Report what changed, what did not start, and what remains unknown. |

Mixing conventions are labelled starting points. Reverb inline/return intent, input-dependent compressor thresholds, and monitoring level belong in examples. No claim of measured gain reduction, loudness compliance, artist authenticity, or listening-based optimization is made without audio evidence. Both vocal presets must expose stock compressor `style` omissions; either execute a revised explicit plan without that intent or report incomplete fulfillment. Never erase the omission to make `ok` green.

### WON'T-YET

| Deferred outcome | Reason and re-entry gate |
| --- | --- |
| Arbitrary occupied-chain insertion, hot-swap, sample/instrument/Set/preset loading | Replacement and selection semantics are unverified. v1 loads supported audio-effect profiles only, on an empty audio track or the same build's verified prefix. Expand after proving preservation with an existing selected device in real Live. |
| Rack grouping, macro naming/mapping/ranges, arbitrary `.adg`/`.adv` creation/export | Missing end-to-end implementation and unverified 12.2 API route. First post-v1 feasibility task: two stock effects into a rack, two mapped/ranged/named macros, preserved state, save/reopen. A failed gate records the precise limit. |
| Usage-derived or explicit-sample Drum Rack building | Sample evidence, numeric pad layout, sample loading, choke behavior, and playback are separate unfinished layers. First prove an explicit two-sample numeric-note rack before connecting usage inference. |
| Browser Collections/tag/database writes | No verified safe writer/reload contract. Track color is not plugin tagging. |
| Offline `.als` and usage MCP tools | Not needed for the chain/Session outcome; root confinement, XML/resource limits, serialization and reference semantics need their own milestone. Remove their registration from the production entry point; do not expose an unfinished optional profile. Preserve parser code for future work. |
| Knowledge and classifier MCP tools, remote judging | Development material and unrelated cost/privacy surface. Remove production registrations, including automatic checkout knowledge discovery. `knowledge/`, `research/`, and `tasks/` never ship. Keep existing development modules unadvertised; no enable-everything switch. |
| Universal plugins, automatic Configure, vendor-state/preset round trips | Installed does not mean controllable, licensed, or semantically mapped. Add one measured profile at a time. VintageVerb's guessed decay levels are ineligible for default execution. |
| Artist-article ingestion and direct hardware-emulation catalogue | External client can interpret supplied material into an explicit plan. Source extraction, emulation provenance and exact sound matching are separate work. |
| New returns/routing, delay/Utility roles, audio import, note edit/delete, nested rack control | Useful next additions but would dilute three sessions. Existing return inspection/sends remain in v1. |
| Arrangement, envelopes, recording/export, deletion, global undo/rollback, autonomous audition/producer | Outside this release outcome; destructive/recovery semantics need independent proof. No general property executor or Python evaluation. |
| Full upstream parity, macOS/Live 11 certification, multi-Live-instance routing | Replace the unbounded parity release promise with the explicit stories above. Preserve founding goals as roadmap. Windows Live 12.2 is the acceptance baseline; later versions need capability checks and their own evidence. |

## 3. Assumptions and owner decisions

### Engineering assumptions

- Baseline inspected: `eda269e61fe1a162c1d5aac7f133a021b4b7029c`, plus current working files, on 2026-11-10. Recheck assigned files before coding because Gemini is changing documentation concurrently. HANDOFF is historical, not evidence.
- Windows, Live **12.2** (record exact patch/edition/language at runtime), English device/display names, host Python >=3.10, MCP 2.x. The current environment has MCP 2.3.0 and Hatchling 1.33.0. Host Python and Live's embedded Python are distinct runtimes. Live 12.3-only APIs cannot be assumed.
- Stock example requires EQ Eight, Compressor, Saturator and Reverb. Record actual edition availability; missing stock devices produce a clear refusal. Do not promise every edition or localized setup works.
- One active Live bridge on `127.0.0.1:9877`; multiple clients cannot interleave mutation workflows. Ordinary calls cost about 0.9 s, so batch useful work and record durations/call counts. Never sleep on Live's main thread.
- Basic is disposable. The implementation agent may restart Live, enable/reinstall the script, and exercise stock operations there. No other Set is a test target. No samples, paid service or owner provisioning are prerequisites.
- Default installation starts read-only. A trusted local configuration change enables writes; no MCP tool can change that policy. This is setup, not a repeated approval ritual. Already-authorized user edits do not need artificial confirmation booleans.
- Every implementation worker is Sol in its own orchestrator-created worktree, branched from its dependency's merged head. The planner is itself the delegated design worker and starts no further agents. This plan is the only file changed by this task; `tasks/todo.md` is deliberately not updated.
- All tickets forbid edits to `knowledge/**`, `research/**`, `tasks/**`, audit inputs, `docs/original-prompt.md`, and unrelated work. No ticket stages Gemini's paths. Evidence goes in the ticket response or the assigned `docs/release/` record, never those directories.

### Owner-only decisions at the final gate

| Decision | Recommendation and settled context |
| --- | --- |
| Public name/package name | Keep `AbletonLiveMCP` / `abletonlivemcp` for this small release unless owner requests a rename; verify package-name availability before an eventual PyPI publication. Do not reserve/change accounts or rename on this plan's authority. |
| Licence | Retain the existing MIT licence, already present in LICENSE, metadata and the vision decision log. This is settled; do not reopen it as a blocker. Only the owner may choose a change. Bundle no commercial presets/plugin state/audio. |
| Release version/tag | Recommend `0.1.1` for the first release of this bounded scope: local tag `v0.1.0` already exists while both metadata values are `0.0.1`. Confirm remote/published history at implementation time; never move an existing tag. Stage metadata consistency and an unreleased changelog before owner selection; tagging remains owner-only. |
| Visibility, timing, PyPI | Keep private throughout preparation. After all exits pass, recommend making the repository public and a manual release from the reviewed artifact; PyPI is optional. No publishing workflow is needed. Owner performs/authorizes the release actions. |
| Account reporting routes | Recommend GitHub private vulnerability reporting plus a separate owner-selected conduct contact. Prepare accurate text and a checklist; enabling settings and selecting a personal contact are owner-only. Never invent contact details. |

The proposed v1 scope is a recommendation for review, not a retroactive rewrite of the founding prompt. On adoption, M3 records the narrowed release contract in vision while preserving the longer-term goals. Routine technical choices, tests and service restarts are not owner decisions.

## 4. Audit reconciliation and verified evidence

All three audit files were read in full. Findings below were traced to current source before adoption. The scope audit has no finding IDs; references to it use its numbered section and exact topic, rather than invent IDs. No Live calls, test suite execution, artifact builds, installs, network judging, or browser experiments were performed for this plan.

| Findings / audit topic | Verification and plan disposition |
| --- | --- |
| **H12 / R01 (blocker)** | Independently confirmed: `pyproject.toml` selects only `src/abletonlivemcp`; `install.source_dir()` walks `parents[2]/remote_script/AbletonLiveMCP`. Hatchling's `WheelBuilder.recurse_included_files()` selected **16 files, zero Remote Script assets**, without building/writing an artifact. This is stronger than layout inference, but not a clean-install pass. Fix M1a-01; actual wheel and sdist proof remains M3-02. |
| **H11 / R02 (high)** | `install.install()` calls `shutil.rmtree(dest)` before `copytree(source_dir(), dest)`; no staging/backup/ownership check. Confirmed destructive ordering, not a reproduced deletion. Merge into M1a-01. |
| **H01 (high), H02, H03, H05, H06 / R06 (high), R16** | `core.py` accepts unauthenticated JSON, continues after bad lines, creates unbounded threads/queue, and races unsynchronized `cancelled/started`; `bridge.py` lacks reply cap and total deadline. `hello` advertises protocol 1 but client never checks it. Fix together M1a-02; keep single-instance scope. No demonstrated browser exploit/RCE is claimed. |
| **H08 / R18 (high)** | `_track/_device` resolve indices anew; `build_chain()` uses `devices_after - 1`. Installed MCP 2.3.0 dispatches sync functions through `anyio.to_thread.run_sync`; whole workflows can interleave. Wrong-target risk is real in source. M1b-01 identities/lease, M1b-03 receipts; documentation alone is insufficient. |
| **H04, H07 / R10 (high), R11** | `_children()` eagerly lists, search checks budget outside the child loop, loading sets only selected track and reports immediate counts. `Inventory.stock_has()` examines only first-level names and build recreates `[name]`. Confirmed; M1b-02 bounds/loading, M2-01 path-preserving discovery. Empty-target restriction is smaller than promising general append/replace. |
| **H09 / R12 (high), R29 / scope §2 contract problems 1–5** | `_map_intent()` drops intentions into notes; final `ok` considers only retained writes; raw solver results hard-code `exact=True`; later exceptions discard stage history. Adapter data labels VintageVerb full despite unmapped predelay/guessed decay. Fix completeness/readbacks M1b-03 and M2-01. Do not implement automatic fallback after a plugin has already loaded. |
| **H10** | Decorator adds no annotations, source names are returned directly, and no read-only gate exists. Installed SDK supports `ToolAnnotations`. Add provenance and enforced local write policy M1b-01/M1b-03. A plan fingerprint detects drift; it is not human authorization or prompt-injection immunity. |
| **H13–H16, H18 / R17 / scope §1 saved-reference semantics** | Server takes arbitrary `.als` paths; reader has a 512 MiB cap but scan retains paths/summaries; knowledge follows links and fully reads pages. These source issues exist. Remove these tools from the production entry point in M1b-03, rather than hardening two deferred products. Defects remain explicitly deferred and must be fixed before re-exposure; exclusion of content alone is not a fix. |
| **H17 / R19 (high)** | `get_judge()` defaults to `auto` and inherited keys select `JevJudge`; server registers classification unconditionally. Remove those tools/imports from production and make default/`auto` local rules in M1b-03. Explicit private development backend remains unadvertised, not v1 supported. No full provider hardening project. |
| **R03, R04, R05 (all high), R15, R24–R28** | README contains only editable setup and “Nothing is usable yet”; support boundaries live in vision; no user client config/upgrade recipe. Local tag/version mismatch verified. M3-01 addresses docs/metadata and prepared reporting routes. Disagree with requiring three MCP client recipes and macOS certification now: one verified Windows recipe plus generic stdio schema is sufficient. |
| **R07–R09, R13, R14** | Preferences validate lists but not roles; inline prefs use broad dicts; override path is not expanded; `_candidates` compares canonical names differently from inventory normalization. Python registry is the only adapter extension point. M2-01 fixes these. Disagree with R14's complete deferral: a four-role, data-only schema is small enough to make installation reusable; universal discovery/procedural adapters still wait. |
| **R20, R21 (high), R22 (high), R23 / H20** | Clip tests contain the 6×2×7 index matrix and duplicate wrapper/settle checks; knowledge test asserts real page names and `-14 LUFS`; CI only editable-installs on Ubuntu/Windows Python 3.10/3.13. Scripts catch/print failures and use private paths. Confirmed by reading tests/workflow/scripts. M1b-04 prunes/contracts, M1b-05 makes first Live gate honest; M3-02 proves artifacts and CI. The audit's 332 is a historical collection count, not a fresh pass. |
| **H19 / scope §2 execution outcomes and undo** | No useful operation history exists. Keep a small bounded operation receipt/status ring for lost responses; defer persistent audit history, generic undo, cross-request undo groups and rollback. Receipt/readback matters more than a logging platform. |
| **Scope §4 MUST/SHOULD and §5 roadmap** | Adopt four roles, Session assistance, human-unit edits, existing returns/sends, and explicit support matrix. Trim broad renames to merges that remove real ambiguity; no new aliases for every old spelling. Defer SHOULD additions and paid/plugin breadth. Preserve rack/macros as the first bounded post-v1 feasibility investigation. API feasibility claims remain unverified until real Live, not inferred from modern Max LOM docs. |

## 5. Architecture decisions that change the code shape

### A. Two runtime halves, one artifact, one source for each asset

Keep stdio MCP in host Python and a stdlib-only Remote Script in Live. Keep `remote_script/AbletonLiveMCP/` as the canonical script source. Use Hatch force-inclusion to put its files under package resources (for example `abletonlivemcp/_remote_script/AbletonLiveMCP/`), and `importlib.resources` for installation. Do not maintain copied source trees. Both sdist and a wheel built from that sdist must contain all script files and small shipped adapter/preset data. Do not include knowledge/research/tasks, bytecode, credentials, owner paths, Sets, audio, commercial presets, or local probe dumps in either artifact.

Installer order: validate resources and canonical library boundary; reject unexpected symlink/junction/reparse components and overlapping paths; stage/validate a sibling copy; preserve the previous recognized installation; replace with rollback on failure. An ownership manifest identifies managed files. Recognize an exact old repository version as a migration case if useful; an unknown same-name folder is refused intact. Do not silently delete extra files or require routine destructive overwrite approval to upgrade a known installation. Windows directory replacement while Live holds files may fail; preserve old installation and give close/restart instructions.

### B. Authenticated, bounded protocol revision 2

Provision a random per-user secret in `~/.abletonlivemcp/bridge.json` through the installer; apply owner-only Windows ACLs and restrictive POSIX permissions where supported. Both halves read it from the same documented location; no token in project assets, tool results, stdout, or logs. Reinstall preserves it. Missing/unreadable/insecure config fails closed; do not fall back to unauthenticated protocol 1. Configuration may also contain the bridge read-only policy. Define `ABLETONLIVEMCP_CONFIG` as an explicit absolute config-file override shared by installer, host and Remote Script; an invalid explicit path fails closed without falling back to the home file. Every offline install/fault/artifact check sets this override to a private temporary file and isolates home discovery too. Record only existence and equality booleans for the owner's original secret/policy/config bytes and ACLs before/after; never reveal values or change the owner's configuration.

Use a small stdlib HMAC challenge/response handshake with fresh per-connection nonces, domain-separated canonical bytes, and authenticated requests/responses tied to that connection and request ID. Authenticate the server before sending a Live command, reject replay from another connection, and compare MACs in constant time. This addresses port impersonation without TLS infrastructure. Same-user hostile code that can read the secret remains outside this boundary. Do not invent an HTTP/CORS transport.

Initial defaults: maximum 4 connections, queue 16, request/response frame 1 MiB, 5 s idle/frame deadline, 15 s overall ordinary exchange deadline; all are constants with explicit bounded errors. Authentication work happens off Live's thread and before queueing. Strict object envelopes, finite JSON numbers, bounded IDs/method/params, and close-on-first-invalid/HTTP-shaped input. One locked queued→started/cancelled→completed state machine: cancelled-before-start never runs; after transmission/start or response loss is conservatively `may_have_applied`. No mutation retries. Pending jobs have bounded lifetime; shutdown releases sockets/capacity and wakes waiters.

Status handshake exposes protocol, component version/build, bridge session, method inventory and capabilities. Client validates protocol and required capabilities **before every write path**, caching only within the authenticated bridge session. Old-script errors instruct reinstall/restart. Do not require byte-for-byte package-version equality for compatible patch releases.

### C. Safety at the Live write boundary

Add a small Remote Script `safety.py`: bounded opaque references to live objects, bridge/Set generation, validity and current-membership checks, expected device/parameter layout, and a fixed read/write method classification. Resolve a current Song supplier on each dispatch instead of assuming the closure-captured Song survives Set changes. Strong references prevent recycled Python IDs from becoming valid targets. Expire handles on Set/bridge change; on uncertainty refuse and rediscover.

Reads return references plus display indices. Writes require references and expected preconditions; an old numeric index alone is insufficient. Track identity survives simple reorder; stale device/parameter layout causes refusal. Clip/scene identity and send destination identity receive the same protection. Global operations use the expected Set generation. Verify the actual runtime's Song/Live-object validity behavior in M1b-05; if safe generation detection cannot be established, block writes across a Set change until reconnect/reload rather than guessing.

Enforce read-only configuration in both MCP and bridge; no model-supplied `confirm` can override it. Serialize whole MCP mutation workflows with a lock. A bounded bridge mutation lease rejects interleaving writes from other MCP processes during a chain; UI edits still require fresh object/layout checks. Lease expires conservatively, releases in `finally`, and uncertain in-progress loads keep their target quarantined until observed terminal/session reset. Authentication is not the user's task authorization; MCP host policy remains in charge.

### D. Loading and budgets

Only supported audio-effect device items under `audio_effects`/`plugins` are executable. A declared profile is not permission for arbitrary sample/Set/preset loading. Begin on an empty regular audio track. Subsequent stages must match exactly the same build's inserted prefix; user changes or unknown selection state stop the operation. Generic occupied-track loading is refused before a browser call.

Main-thread handlers start a native load then return an operation ID. Later scheduled display ticks compare object identities, track/selection context and device layout to find the actual new device; never choose the last device by count. Parameter writes wait for the observed ready state. Timeout/pending is not absence and never permits a second load. A fixed-size recent-operation ring supports readback after response loss; no durable replay engine or automatic rollback.

Browser listing uses bounded pages/continuations; search returns `complete`, `truncated`, `budget_exhausted` and a bounded continuation when available. Limits apply inside child traversal; do not eagerly copy an entire collection merely to slice it. Start with 200 listed/results per page, 4,000 visited nodes per search slice, 4 active cursors and 30 s cursor expiry. Add a soft monotonic 10 ms Python work budget per display tick; measure before claiming responsiveness. Stop/resume browser walking at bounded units. A single native `children` access or plugin load cannot be preempted; report that limit.

Reduce display sampling to at most 129 total display conversions per bridge request, rather than 64×129. Chunk solver sampling to match; finite per-workflow call/deadline budgets stop cleanly. Keep maximum 12 chain stages, 64 explicit writes per batch and 2,000 notes; add bounded parameter/list pages and bounded string lengths. Note retrieval is restricted to the declared clip window; native retrieval cost is a measured limitation, not solved by Python slicing. Record latency; do not trade wrong values or UI freezes for fewer bridge calls.

### E. Plan/execution and adapter data

`live_plan_chain` accepts typed role or exact-device stages and target context, returns immutable canonical stages, resolved actual root/path, adapter version/hash, preference hash, requested/mapped/omitted/uncalibrated intent and target preconditions. A bounded in-memory plan ID/fingerprint is sufficient; restart/expiry requires re-plan. `live_build_chain(plan_id)` executes that plan once, after fresh preconditions, without silently resolving a different device. Repeated use returns the existing receipt or refuses; never starts a second build. Plan ID records reviewable content, not human approval.

Planning does not load a plugin to discover its controls. Report `controls: unverified_until_loaded` where necessary. After load, check the actual instance's requested controls, enabled/automation state and dependent modes. If incompatible, stop with the loaded device in the receipt; do not append a stock substitute after a failed plugin. Automatic stock fallback occurs only while selecting a plan, when absence or unusable mappings are known. Incomplete search means unknown, never “not installed.” Missing edition/device requirements are actionable refusals.

Use a versioned JSON adapter schema for the existing four roles only: ID, aliases, device kind, root/path hints, product/format/version evidence, intent-to-parameter names, display targets, option setup and explicitly calibrated raw mappings. Built-ins and user JSON use the same validation; `ABLETONLIVEMCP_ADAPTERS` names an absolute or expanded local file. No imports, Python expressions, arbitrary code, procedural plugins, new roles, automatic downloads, or implicit built-in replacement. Duplicate IDs/ambiguous aliases fail. A user mapping is visibly user-supplied/unverified until its Live evidence exists. Explicit raw requests stay raw, not physical claims.

Preferences remain role→ordered IDs/names, with one file/inline validator, canonical alias handling that preserves product versions, default missing-file stock behavior, and errors for an explicitly configured missing file. Candidates are user choices in order, then the stock profile; never pick an unrequested third-party plugin merely because it is in the registry. Convert existing Python mapping data without growing a catalogue. Remove guessed VintageVerb level conversion from executable defaults. Keep two vocal presets, custom stages and their caveats; no user-preset framework.

Every mutation receipt contains operation/Set/target identity, requested and actual values, originals for writes, completed stages, stopped-at location, omissions, and unknown outcomes. `status` distinguishes complete/partial/failed/pending; whole-intent fulfillment is separate from successful retained writes. Stop on first unresolved/failed setting by default. An explicitly revised plan may omit unsupported intent, with that omission still visible. No global undo, automatic deletion, or claim of atomicity. Existing automated parameters are refused by default; v1 never silently overrides/re-enables automation.

### F. Public tool surface

Keep typed domain tools and the existing recognizable names where a rename adds no practical value. Make this one pre-release break; update scripts/docs in the owning ticket, without registering old aliases. Proposed default inventory is **32 tools**, subject to the real schema check; count is a check, not a success metric:

- Status/session: `live_hello`, `live_session_info`, `live_tracks`, plus `live_get_track`, `live_list_scenes`, `live_list_devices`.
- Browser: `live_browser_roots`, `live_browser_list`, `live_browser_search`, `live_load_item` (restricted contract).
- Devices: `live_device_parameters`, `live_set_device_parameters` (replaces singleton setter; raw/display target union).
- Tracks/mixer: `live_create_track`, `live_set_track` (merges name/color), `live_get_mixer`, `live_set_mixer`.
- Transport: `live_get_transport`, `live_set_transport` (merges tempo/play/stop).
- Scenes: `live_create_scene`, `live_set_scene_name`, `live_fire_scene`.
- Clips: `live_create_clip`, `live_get_clip`, `live_set_clip`, `live_add_notes`, `live_get_notes`, `live_fire_clip`, `live_stop_clip`.
- Chains: `live_plan_chain`, `live_build_chain` (replaces both builders), `live_vocal_presets`, `live_get_operation`.

Typed models live in `src/abletonlivemcp/models.py`; the Remote Script remains stdlib-only and independently validates the wire boundary. Tool metadata marks reads, mutations and non-idempotent creates honestly. Source-provided names/text are structured untrusted data with provenance; trusted descriptions explain safety and units. Use stable domain error kinds and `retryable`/`may_have_applied`, bounded details, stderr for unexpected traces, and protocol-only stdout. Production registration imports no offline reader, knowledge scanner or judge backend. An explicit removed-tools test covers `.als`, classification, knowledge and gear lookup, even when their environment variables are present.

## 6. Milestones and exits

Four bounded milestones replace the previous three-session schedule; each has a cap of one long Sol session including integration and evidence. Approximately three long sessions remain, so the full release scope is **not budgeted to completion**: M1a, M1b and M2 take priority, and M3 needs remaining capacity demonstrated at the M2 exit or a separate budget/scope re-plan. The split does not create more quota. Never compress unverified Live behavior or drop an IN story to make the estimate fit. Use two independent workers only where file sets permit; all Live use is a single exclusive lane. Aim for about 60% coding, 25% integration/Live proof, 15% fixes. If a ticket expands beyond roughly 60–90 minutes of focused implementation or needs an unplanned subsystem, stop that ticket with evidence and re-plan.

| Milestone | Tickets | Outcome and exit condition |
| --- | --- | --- |
| **M1a — Install and transport gate** | 2 | Packaged assets/safe replacement, isolated private config and authenticated bounded bridge. An outside-checkout artifact install/fault/reinstall check plus ephemeral-port authentication/bounds/cancellation checks pass against the merged head. No Live use and no claim of mutation safety yet. |
| **M1b — Mutation, load and real-Live safety gate** | 5 | Enforced policy/identities/leases, bounded tick-driven loading, honest execution receipts, reduced surface and lean adapted tests. Frozen merged source passes the serial stock safety exercise in disposable Basic; this exit is mandatory before M2. |
| **M2 — Reusable chains and minimum Session workflow** | 4 | Data-only adapters/preferences, stock path discovery, typed combined chain/parameter path, bounded Session inspection, minimum mixer and clip metadata. US2–US7 have serial real-Live evidence; unsupported plugin behavior is honest. |
| **M3 — Stranger proof and owner handoff** | 3 | User docs/support/version metadata, artifact CI, clean outside-checkout install and full real-Live story pass from the final artifact. Readiness evidence lists precise results and owner actions. Conditional on demonstrated remaining capacity or re-planning; no publication action is authorized. |

Total remains **14 tickets**. M1a is a useful install/transport stopping point, but only the passed M1b safety exit allows broader mutation work. M1b is the highest-value safe-core stopping point at quota exhaustion; M2 and M3 remain required before public readiness. Cut optional Pro-C 2 certification and extra client recipes first if useful; further scope cuts require a revised plan with a stated reason. An unfinished or failed gate never becomes release-ready because quota ran out.

## 7. Tickets

### M1a full tickets; M1b safety contracts retained

Every M1a/M1b ticket inherits the forbidden paths in §3 and the release-action prohibition. Each numbered step is one action; its evidence entry is required in the ticket response. Checks run against the ticket's frozen final state at handback; do not repeatedly run the full suite after edits. Include the head SHA, exact commands/exit codes, and any limitation. M1a-02 closes the install/transport gate with its affected batch after integration; M1b-05 runs the affected safety batch after all M1b merges. M1a is the next milestone and is fully briefed below. The existing detailed M1b safety contracts are retained because their interfaces constrain M1a; recheck their steps at the M1b start. M2/M3 numbered implementation steps and per-step evidence ledgers are written when each milestone starts, under the size-L planning rule, before dispatching its tickets.

#### M1a-01 — Bundle assets and preserve installations

**Objective:** Make a wheel/sdist provide a safe Remote Script installer and persistent private bridge configuration.

**Files to edit/create and files that must stay untouched:** Edit `pyproject.toml`, `src/abletonlivemcp/install.py`, installer portion of `tests/test_client_server_install.py`; create `src/abletonlivemcp/config.py` and a focused `tests/test_install.py` if extraction helps. Resource inclusion references canonical Remote Script files without editing them. Keep server, bridge, core, handlers, chain, workflow and documentation unchanged.

**Steps:**

1. Map canonical Remote Script files into package resources and switch installer resource lookup, yielding source-layout-independent discovery.
2. Replace delete-first installation with validated staging/ownership/backup/rollback, yielding preservation of the old recognized installation and unrelated folders on failure.
3. Provision/reuse private per-user secret/read-only configuration and the shared absolute `ABLETONLIVEMCP_CONFIG` override, yielding identical config discovery for both runtimes without printed secrets; an invalid explicit override fails closed.
4. Exercise one compact temporary-library install/reinstall-failure scenario from a locally built artifact, with `ABLETONLIVEMCP_CONFIG` and home discovery redirected to a private temporary root, yielding nonzero actionable failure and unchanged previous content. Compare the owner's existing config/secret/write policy/ACLs before and after using redacted equality checks only; do not provision or modify anything in the owner's real home.

**Evidence to paste per step:** (1) Wheel and sdist member lists for script assets and exclusions. (2) Before/after file hashes for success, injected copy failure and unknown-folder refusal. (3) Temporary config path, ACL/permission principal summary and secret **presence only**, plus unchanged-secret/policy booleans on reinstall. (4) Exact outside-checkout commands, exit codes, restored-content hashes, resolved temporary home/config roots, and unchanged booleans for the owner's original config/secret/write policy/ACLs (or continued absence); do not paste token values or secret-bearing config hashes.

**Acceptance:** Both artifact types contain all canonical script assets; installer never deletes the working destination before replacement validation; config survives reinstall with restrictive access; temp-library fault scenario passes without contacting Live or provisioning config in the owner's home; the owner's existing secret and write policy remain unchanged. `python -m pytest -q tests/test_install.py tests/test_client_server_install.py` (omit the new test file only if its scenario remains in the existing file) records the isolated failure/reinstall outcomes.

**Stop rule:** Stop if packaging requires maintaining duplicate sources, safe path/ACL checks cannot be established, or an unknown user folder would need deletion; report the exact obstruction and preserve it.

**NEEDS-LIVE:** no.

**depends-on:** none.

**parallel group:** P1-A; independent of M1a-02 coding within their file reservations; merge first.

#### M1a-02 — Authenticate and bound the bridge

**Objective:** Reject unauthenticated/incompatible/malformed peers and give bounded, honest request outcomes.

**Files to edit/create and files that must stay untouched:** Edit `remote_script/AbletonLiveMCP/core.py`, `src/abletonlivemcp/bridge.py`, `tests/test_bridge.py`; create `docs/release/bridge-protocol.md` for the concise wire/error contract. Consume M1a-01 config contract without editing its module. Keep handlers, entry point, server, installer, chain and non-bridge tests untouched.

**Steps:**

1. Implement protocol-2 mutual authentication and envelope/version checks, yielding rejection before dispatch of wrong/missing keys, replay and invalid frames.
2. Add connection/queue/frame/reply limits and total/idle deadlines, yielding bounded Busy/protocol/timeout responses and capacity release on stop.
3. Synchronize queued/start/cancel completion transitions, yielding cancellation-before-start or conservative may-have-applied outcomes without automatic retry.
4. After M1a-01 merges, integrate its actual isolated-config/artifact contract and run the compact real-socket scenario on an ephemeral port with inert dispatch, yielding authenticated roundtrip, malformed/HTTP first-line close, bounds and both timeout states; run the affected install/transport checks once to close M1a.

**Evidence to paste per step:** (1) Redacted handshake success/failure and zero-dispatch counts for rejected peers. (2) Configured bounds and observed saturation/deadline/frame outcomes including connection cleanup. (3) Deterministic synchronization trace at the start/cancel boundary. (4) `python -m pytest -q tests/test_bridge.py tests/test_client_server_install.py tests/test_install.py` (omit the optional extracted file if absent), exit code and result table at the merged head; record M1a-01 artifact/fault evidence and shared config-path agreement. Prove the port was ephemeral, never 9877, config/home were temporary, and no Live API/fake Live implementation was involved.

**Acceptance:** Only authenticated protocol-2 work reaches inert dispatch; spoofed replies fail verification; malformed input closes; all buffers/workers/queue lifetimes are bounded; cancelled-before-start work cannot execute; ambiguous outcomes are not retryable success/failure claims. M1a closes only when both tickets' artifact/config and transport checks pass together; no Live or mutation-safety claim follows.

**Stop rule:** Stop if authentication needs third-party packages inside Live or bounded response/cancellation guarantees cannot be stated; do not ship a protocol-1 fallback or claim browser exploit reproduction.

**NEEDS-LIVE:** no.

**depends-on:** M1a-01 config interface fixed before integration; wire coding may start independently using the §5 path/fields.

**parallel group:** P1-B; merge after M1a-01.

### M1b mutation/load gate (revalidate full briefs at milestone start)

#### M1b-01 — Put target and policy checks at dispatch

**Objective:** Make every Live mutation require current object identity, permitted policy and an exclusive workflow context.

**Files to edit/create and files that must stay untouched:** Edit `remote_script/AbletonLiveMCP/__init__.py`, `remote_script/AbletonLiveMCP/handlers.py`, `tests/test_handlers.py`; create `remote_script/AbletonLiveMCP/safety.py`. Wire the M1a-02 core/client interface without editing their files. Keep server, chain, installer, packaging and clip-test matrices untouched.

**Steps:**

1. Replace fixed Song capture with current-Song/generation-aware dispatch and bounded object references, yielding readable targets tied to live identity and membership.
2. Gate all fixed-table mutations on read-only policy and reference/precondition validity, yielding refusal before stale or unauthorized writes.
3. Add a bounded mutation lease and disconnect/session invalidation, yielding non-interleaving chain ownership without treating the lease as user approval.
4. Document the dispatch contract in the ticket and retain one focused safety-contract scenario, yielding evidence that all mutating methods are classified and index-only/stale/read-only writes are refused.

**Evidence to paste per step:** (1) Reference/generation lifecycle and bounded registry limits. (2) Method classification table and refusal-before-write observations. (3) Competing lease, expiry and invalidation outcomes. (4) Focused command/exit code and the unverified Live-object assumptions explicitly reserved for M1b-05.

**Acceptance:** No fixed-table mutation bypasses policy/target checks; no raw numeric index authorizes a write; leases cannot indefinitely block the bridge; song/reference invalidation is conservative. Actual Live lifecycle remains gated by M1b-05.

**Stop rule:** Stop if Live-object identity/validity cannot be represented safely with the current runtime; do not fall back to name/index matching. Escalate the smallest read-only runtime probe to the exclusive Live lane.

**NEEDS-LIVE:** no for this source ticket; real target lifecycle proof is mandatory in M1b-05. Any runtime probe changes this ticket to NEEDS-LIVE and requires the exclusive lane.

**depends-on:** M1a-02.

**parallel group:** P2-A; follows the passed M1a gate and owns handlers/entry point/safety until merged.

#### M1b-02 — Bound browser work and establish safe load completion

**Objective:** Make loading identify a ready inserted effect while browser work stays within explicit budgets.

**Files to edit/create and files that must stay untouched:** Edit `remote_script/AbletonLiveMCP/__init__.py` sequentially after M1b-01, `remote_script/AbletonLiveMCP/handlers.py`, `remote_script/AbletonLiveMCP/safety.py`, browser/load cases in `tests/test_handlers.py`; create `remote_script/AbletonLiveMCP/operations.py` for bounded pending load/receipt state if needed. Keep core/client, server, chain, packaging, installer and other tests untouched.

**Steps:**

1. Bound inner browser traversal/list pagination and total display-sampling work, yielding accurate incomplete/continuation results rather than excess hidden work.
2. Restrict load preconditions to supported audio effects and empty/owned-prefix audio targets, yielding refusal before any ambiguous occupied-target or item-kind load.
3. Add an explicit bounded operations tick in the Remote Script entry point's `update_display()`, alongside queue draining, and disconnect cleanup; it runs on later display ticks even when the request queue is empty. Track native-load readiness there using actual object differences, yielding operation ID, pending/ready/failed/unknown state and the actual added device reference. Preserve M1b-01 dispatch/policy wiring and leave bridge core unchanged.
4. Record one focused bounds/load-state contract scenario, yielding coverage of stop-before-write and pending-not-retried behavior without simulating Live selection semantics.

**Evidence to paste per step:** (1) Visit/conversion/page/cursor caps and boundary results. (2) Supported-kind/precondition table and pre-load refusal observations. (3) Entry-point/tick/cleanup call order and method signatures, an inert lifecycle check proving later idle ticks advance a pending operation and disconnect invalidates it, operation transitions and expiry/quarantine rules; this is wiring proof, not simulated Live loading. (4) Command/exit code plus a list of Live-only assumptions assigned to M1b-05.

**Acceptance:** A wide child loop cannot exceed the Python visit/result budget; display requests cannot multiply to 64×129 conversions; the reserved entry-point tick advances pending operations without an incoming request and stops on disconnect; no stage writes before ready; device count alone never chooses the target; uncertain loads prevent retries/later stages.

**Stop rule:** Stop if append placement needs an unverified selection/hot-swap action or the design grows a general job engine; keep unsupported loads refused and request the specific real-Live probe at M1b-05.

**NEEDS-LIVE:** no for code; selection/readiness/UI responsiveness proof is M1b-05, and any early runtime probe must acquire the exclusive lane.

**depends-on:** M1b-01.

**parallel group:** P3-A; exclusive ownership of entry point/handlers/safety after M1b-01.

#### M1b-03 — Make core execution and failures honest

**Objective:** Expose only the v1 core and preserve complete operation evidence through every chain failure.

**Files to edit/create and files that must stay untouched:** Edit `src/abletonlivemcp/server.py`, `src/abletonlivemcp/chain.py`, `src/abletonlivemcp/judge/__init__.py`, `tests/test_chain_tools.py`, `tests/test_judge.py`; create `src/abletonlivemcp/models.py`. Consume safety/load contracts without editing Remote Script files. M1b-04 owns `tests/test_chain.py` and adapts it after this ticket merges; hand it the new partial/off-target contract rather than overlapping files. Keep adapter/resolver/preferences, installer/packaging and docs untouched.

**Steps:**

1. Remove deferred tools/imports from production registration and default judge selection to local rules, yielding no filesystem-reader/knowledge/classifier/gear tools or key-triggered network choice.
2. Add typed plan/receipt models, read-only annotations/provenance and a whole-mutation lock, yielding an inspectable limited core surface with host/bridge policy alignment.
3. Route chain execution through stable targets, leased safe loads and stop-on-failure receipts, yielding original/applied/omitted/unknown values and no discarded successful prefix.
4. Merge the two builders into plan-then-build execution and verify real raw/display readbacks, yielding no silent re-plan, duplicate plan execution, or unconditional raw `exact=True`.

**Evidence to paste per step:** (1) MCP `list_tools` names with knowledge directory and external-key variables present (use dummy values), and local backend name without requests. (2) Schema/annotation excerpts and policy/error examples. (3) Partial receipt from a deterministic failing project-owned call boundary, showing no later call; no fake plugin DSP. (4) Reused/expired/changed plan refusal and off-target raw/display result; command/exit codes for focused contract checks.

**Acceptance:** Unsupported profiles are unreachable through production MCP; mutations are serialized, target-checked, never automatically retried, and return structured partial/unknown outcomes; build consumes the exact preview; omitted intent cannot become complete success. M2 adds usability, not an alternate unsafe path.

**Stop rule:** Stop if recovery requires deleting devices, blind undo, hiding omissions, or loading a fallback after a partial plugin failure. Preserve evidence and refuse further stages.

**NEEDS-LIVE:** no; actual runtime proof is M1b-05.

**depends-on:** M1b-02.

**parallel group:** P3-B; may draft alongside M1b-02 using its agreed interface, integrates from and merges after its dependency's merged head. Does not edit M1b-02 files. M1b-04 follows this handback and owns final test-contract adaptation; M1b-05 owns integrated safety checks.

#### M1b-04 — Prune fake duplication and detach research tests

**Objective:** Reduce duplicated synthetic checks while retaining the project's safety and algorithm contracts.

**Files to edit/create and files that must stay untouched:** Edit `tests/test_handlers_clips.py`, `tests/test_server_settle.py`, `tests/test_chain.py`, `tests/test_knowledge.py`, `tests/test_resolve.py`; add a tiny temporary Markdown fixture in the test itself. Keep all production modules, `tests/test_bridge.py`, `tests/test_handlers.py`, `tests/test_client_server_install.py`, `tests/test_chain_tools.py`, and Gemini directories untouched.

**Steps:**

1. Collapse repeated scene/clip index cross-products into a representative shared-guard table, yielding about one behavior scenario per supported feature.
2. Merge duplicate settle/forwarding and option-before-number checks, yielding one authoritative check per contract without a second Live implementation.
3. Replace real-knowledge assertions with a temporary synthetic page and direct module check, yielding tests independent of changing/unshipped research pages.
4. Preserve focused validation/cancellation/bounds/unit/partial-result checks and record collection changes, yielding a concise retained-contract inventory for integration.

**Evidence to paste per step:** (1) Before/after collected counts for the affected file and retained occupied-slot/all-notes-prevalidated coverage. (2) Names removed/kept and their common contract. (3) Fixture content and absence of real-page/prose dependencies. (4) Focused commands/exit codes, before/after totals and the M1b-03 partial/off-target check added against its already merged contract. Do not claim collection means pass.

**Acceptance:** Redundant 84-case clip matrix and repeated scene permutations/forwarding/options checks are removed; no default check requires Gemini's pages; meaningful shared guards, nonlinear unit solver and partial-outcome evidence remain. No new FakeLive hierarchy or substitute plugin implementation.

**Stop rule:** Stop a deletion if it would remove the only safety-contract proof; retain it and explain. Do not chase a numeric test-count target or expand scope into rewriting unrelated parser tests.

**NEEDS-LIVE:** no.

**depends-on:** M1b-03. Start from its merged head; prune and adapt public-contract checks in this single ticket, then hand back passing focused checks. There is no pre-merge handback or unowned later amendment.

**parallel group:** P3-C; sequential after M1b-03 and before M1b-05.

#### M1b-05 — Prove the hardened core in Basic

**Objective:** Validate the merged safety and load contracts in real Windows Live 12.2 before broader feature work.

**Files to edit/create and files that must stay untouched:** Edit `scripts/live_write_test.py`, `scripts/live_chain_test.py`, `scripts/live_clip_test.py`, `scripts/stdio_error_smoke.py` for assertions/arguments/nonzero exits; create `docs/release/m1b-live-evidence.md`. Runtime config and disposable Basic may change. Keep product modules and all other tracked files untouched; return any product defect to its owning ticket rather than editing conflicting files here.

**Steps:**

1. Convert the assigned scripts to fail on required assertion/readback failures and accept explicit test context/output arguments, yielding repeatable commands without owner paths or fixed track numbers.
2. Install/activate the merged script in disposable Basic and check status/read-only/credentials/version rejection, yielding exact component/runtime evidence and refusal without mutation.
3. Observe and record the actual `audio_effects` browser root and full path arrays to EQ Eight, Compressor, Saturator and Reverb via bounded listing/search, then supply those explicit paths to one exact-device chain on an empty audio track. Do not use automatic role resolution or assume `[device_name]`: nested stock discovery belongs to M2-01. Exercise stock creation/load/write plus stale-target/occupied-load/partial-failure scenarios serially, yielding actual inserted identities, displayed values and unchanged unrelated objects.
4. Run the affected offline safety checks once against the merged head and record the Live observations, yielding an explicit pass/fail M1b exit with unresolved assumptions listed; retain the already passed M1a evidence.

**Evidence to paste per step:** (1) Command help, a deliberately failed assertion's nonzero exit, and labels of read/write behavior. (2) OS/Live patch/edition/language/embedded runtime, package/script/protocol versions, redacted auth/policy outcomes. (3) Observed stock root/full path arrays, exact-device plan/receipt proving no role resolver dependency, before/after device/track/parameter identities and displays, target-reorder/Set-switch refusal, a second-client lease refusal, pending/readiness timings, one actual later-stage failure receipt, and a UI/log observation of responsiveness. (4) Exact commands, exit codes, affected-check totals, head SHA and links to the evidence record; mark any skipped check as unproved.

**Acceptance:** The explicit-path EQ Eight → Compressor → Saturator → Reverb chain loads in order and changes only its intended identified targets; unknown/stale/read-only writes and occupied generic loads refuse; Set change invalidates references; a visible partial failure stops later stages and retains evidence. The wrong-token check causes no mutation. Required scripts return nonzero for failure, and affected offline checks pass.

**Stop rule:** Stop mutation testing on an unexpected target, replacement, UI hang or unaccounted late write; stop transport, preserve before/after evidence, and reopen the specific safety ticket. Do not move to M2 with a failed safety exit. Do not retry an uncertain load.

**NEEDS-LIVE:** yes — exclusive lane; no other agent may call port 9877 or operate Live during this ticket.

**depends-on:** M1a-01, M1a-02 and M1b-01 through M1b-04 merged, with the M1a gate passed.

**parallel group:** LIVE-1; code freeze for the exercised product head.

### M2 outlines, reservations and concrete acceptance

Ticket scheduling/NEEDS-LIVE metadata is in §8. Under size-L planning, these are bounded future-milestone contracts: write numbered implementation steps and per-step evidence at the M2 start, then recheck reservations before any worker starts. No deferred SHOULD work is implied. The commands below are **required future acceptance interfaces**, not claims that their flags exist today; each named script owner implements them in its reserved files. Use `python` from the ticket venv. `$evidenceRoot` is an absolute private temporary output directory outside the checkout; configure it once, never include credentials in output, and keep committed summaries redacted. Every required command must exit zero on passing assertions and nonzero on failed assertions.

| Ticket | Objective | Acceptance |
| --- | --- | --- |
| **M2-01 — Make four-role planning user data** | Implement validated built-in/user adapter JSON, shared preferences validation, path-preserving discovery and honest intent capability reports. | A stock plan resolves nested actual paths; incomplete search stays unknown; file/inline preference errors and aliases behave identically; a temporary user compressor profile works without Python edits; no unrequested plugin is selected. Both vocal starting points expose any omissions; VintageVerb guesses cannot execute. One serial stock/custom-profile Live proof; optional Pro-C 2 becomes certified only with format/version/control readbacks, otherwise omitted from tested support. |
| **M2-02 — Expose the minimum Session view** | Add bounded track/return/master/scene/slot/device reads and the needed track/clip metadata mutations using existing safety references. | Run the `session-view` command below and record UI-observed baseline counts for regular tracks, returns, master (exactly one), scenes and top-level devices. Create exactly one MIDI track and one scene: regular-track and scene counts each increase by one, return count is unchanged, and the created track has one slot per scene, initially all empty. Name/color the created track and one four-beat clip, compare exact returned/UI values, and paginate tracks/devices/parameters with page size 2: no duplicated references, exact bounded-page totals, explicit continuation/omission flags. Nested devices are explicitly unsupported; all mutations use policy/references and no delete/Arrangement methods are added. |
| **M2-03 — Complete human-unit edits and minimum mixing** | Expose the batch parameter solver on existing devices and add gain/pan/mute/solo/existing-send controls plus the transport/tool merges. | In real Live, set a stock compressor to 4:1/-18 dB, bypass and restore its discovered activator; refuse disabled/automated targets; level/pan/send readbacks match UI and return identity. Master/return unsupported fields refuse. Final tools/schemas match §5 and no singleton/duplicate builder/transport aliases remain. |
| **M2-04 — Prove one end-to-end user session** | Run the combined US2–US7 workflow with parameterized acceptance scripts and capture the final behavior/latency contract. | New scene/four-beat MIDI clip/exact notes launch and stop with observed pending/playing state; occupied-slot and bad-note batches preserve state; stock/custom-preference chain and existing mixer edits pass in serial real Live. Scripts have meaningful assertions/nonzero exits; one affected-check batch passes and evidence identifies the merged SHA. |

**M2 prerequisites, exclusive reservations and acceptance commands** (all paths are relative to the repo; §8 orders shared files):

| Ticket | Prerequisites and reserved files | Commands and visible evidence |
| --- | --- | --- |
| M2-01 | **depends-on:** M1b-05 passed. Own `src/abletonlivemcp/{adapters,resolve,preferences,chain_presets,models,chain}.py`, new `src/abletonlivemcp/data/adapters.json`, `docs/data/example-preferences.json`, `tests/test_chain.py`, `tests/test_resolve.py`, `scripts/live_chain_test.py`, `scripts/live_probe_plugins.py`, `scripts/live_dump_stock_params.py`. `chain.py` edits are limited to sampling chunks/path/plan integration. No server/handler edits. | `python -m pytest -q tests/test_resolve.py tests/test_chain.py`; `python scripts/live_chain_test.py --scenario stock-custom --set Basic --output "$evidenceRoot/m2-planning.json"`. JSON records actual nested root/path arrays, search completeness, both presets' requested/mapped/omitted intent, stock fallback and a temporary custom stock-Compressor profile selected through file and inline preferences (4:1/5 ms readbacks). Include identical alias/typo/missing-file errors and incomplete-search refusal; plugin absence is explicit. Pro-C 2 proof is optional and separately labelled. |
| M2-02 | **depends-on:** M2-01 and passed safety gate. Own `src/abletonlivemcp/{server,models}.py`, `remote_script/AbletonLiveMCP/handlers.py`, `tests/test_handlers.py`, `tests/test_handlers_clips.py`, `tests/test_chain_tools.py`, `tests/test_server_settle.py`, `scripts/live_write_test.py`, `scripts/live_clip_test.py`. Consume safety, never bypass it. | `python scripts/live_write_test.py --scenario session-view --set Basic --page-size 2 --output "$evidenceRoot/m2-session.json"`; `python -m pytest -q tests/test_handlers.py tests/test_handlers_clips.py tests/test_chain_tools.py tests/test_server_settle.py`. JSON records baseline/UI and after counts, exact +1 track/+1 scene deltas, empty/occupied slots, page lengths/totals/references/flags and exact name/color readbacks; a recorded UI comparison lists each checked count/value and any omission. Command fails on any unexplained mismatch; “matches UI” alone is insufficient. |
| M2-03 | **depends-on:** M2-02. Own `src/abletonlivemcp/{server,models,chain}.py`, `remote_script/AbletonLiveMCP/handlers.py`, `tests/test_handlers.py`, `tests/test_chain_tools.py`, `tests/test_server_settle.py`, `tests/test_chain.py`, `scripts/live_write_test.py`, `scripts/stdio_error_smoke.py`. `chain.py` work is existing-device exposure and solver regression only. | `python scripts/live_write_test.py --scenario parameter-mixer --set Basic --output "$evidenceRoot/m2-mixing.json"`; `python scripts/stdio_error_smoke.py --set Basic --output "$evidenceRoot/m2-errors.json"`; `python -m pytest -q tests/test_chain.py tests/test_chain_tools.py tests/test_handlers.py tests/test_server_settle.py`. Record exact ratio/threshold/activator originals and readbacks, UI/display tolerances, mixer dB/pan/send units and return identity, stale/disabled/automated/unsupported refusal with unchanged state, restored values and actual MCP tool/schema inventory matching §5. |
| M2-04 | **depends-on:** M2-03. Own `scripts/live_write_test.py`, `scripts/live_chain_test.py`, `scripts/live_clip_test.py`, `scripts/stdio_error_smoke.py`, new `docs/release/m2-live-evidence.md`; no production edits. Freeze merged product code. | Run serially: `python scripts/live_chain_test.py --scenario release-chains --set Basic --output "$evidenceRoot/m2-chains.json"`, `python scripts/live_write_test.py --scenario parameter-mixer --set Basic --output "$evidenceRoot/m2-mixing-final.json"`, `python scripts/live_clip_test.py --scenario session --set Basic --output "$evidenceRoot/m2-clips.json"`. Record a four-beat clip with exactly three specified notes, additive-note semantics, occupied-slot/invalid-later-note unchanged state, launch pending/playing/stop observations, both presets/custom plan receipts and latency/call counts; run the affected M2 check batch once at frozen head, rather than duplicating every preceding check. Evidence names commands/exits and merged SHA; any required skip fails the gate. |

### M3 outlines, reservations and concrete acceptance

| Ticket | Objective | Acceptance |
| --- | --- | --- |
| **M3-01 — Write the stranger path and release contract** | Align README, support/safety/upgrade/adapter guides, component version metadata and contribution expectations with proven scope. | One absolute-executable Windows venv/wheel/stdin-stdout recipe, valid generic MCP config and one tested client recipe cover install→activate→read-only→enable-authorized-writes→preview→execute→inspect→upgrade/recover. No PyPI availability claim, blanket parity/macOS/plugin claim or default knowledge dependency. Vision records accepted v1 scope, original prompt stays unchanged; MIT remains; unreleased changelog and owner action checklist exist. |
| **M3-02 — Verify the distributable in CI** | Add one clean-artifact acceptance job and a reproducible tested dependency/action baseline without publication automation. | Build wheel+sdist, rebuild wheel from sdist, install outside checkout, copy/reinstall into temporary library, initialize/list tools over actual stdio without Live, assert asset inclusion and content/secret exclusions, and run the lean suite. Ubuntu/Windows Python 3.10/3.13 remain a practical host matrix; Windows artifact path is checked. Actions pinned to reviewed SHAs, read-only job token/no persisted credentials, tested release constraints recorded. No paid calls. |
| **M3-03 — Run the final stranger rehearsal and stop at owner control** | Install the exact reviewed artifact outside the checkout and execute every v1 user story serially in real Live. | Every §9 story passes against the artifact SHA/hash; full lean checks run once at final frozen head; documentation steps are followed literally; no unresolved technical release blocker remains. `docs/release/v1-readiness.md` states tested matrix, limitations, evidence and only genuine owner decisions. Repo visibility, tags, releases, PyPI and account settings remain unchanged. |

Write M3 numbered implementation steps and per-step evidence at its start, after checking the M2 result and remaining budget. The following commands are required future interfaces; M3-02 owns the stdio/artifact runner additions. All artifact checks isolate config and home as required by M1a-01.

| Ticket | Prerequisites and reserved files | Commands and visible evidence |
| --- | --- | --- |
| M3-01 | **depends-on:** M2-04 passed and M3 capacity confirmed or re-planned. Own `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `docs/vision.md`, new `docs/adapters.md`, `docs/tools.md`, `docs/release/v1-readiness.md`, `CHANGELOG.md`, `pyproject.toml`, `src/abletonlivemcp/__init__.py`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, `.github/PULL_REQUEST_TEMPLATE.md`. No LICENSE or founding-prompt edits. | In a fresh isolated venv, follow the documented wheel-install recipe, then run `python -c "import importlib.metadata as m; import abletonlivemcp as p; assert m.version('abletonlivemcp') == p.__version__"` and `python -m pytest -q tests/test_smoke.py`. Record executable/config examples, component metadata comparison, a story-to-doc/tool/support matrix and an unreleased changelog. Readiness record has pending evidence labels and genuine owner-only actions, not invented contacts or unsupported support claims. Actual client/Live recipe verification belongs to M3-03; documentation cannot self-certify it. |
| M3-02 | **depends-on:** M3-01. Own `pyproject.toml`, `tests/test_client_server_install.py`, `tests/test_install.py` if present, `scripts/stdio_smoke.py`, new `scripts/artifact_smoke.py`, `.github/workflows/ci.yml`, new `constraints/release.txt`. No release/publish workflow or account changes. | `python -m build`; `python scripts/artifact_smoke.py --dist-dir dist --temp-root "$evidenceRoot/artifacts" --output "$evidenceRoot/m3-artifacts.json"`; `python -m pytest -q`. Artifact runner rebuilds a wheel from sdist, installs both wheel variants outside checkout into isolated venvs, installs/reinstalls the script into temporary libraries, invokes actual stdio initialize/list-tools without Live, and checks canonical assets and secret/content exclusions in both artifact types. Its JSON records source SHA, wheel/sdist SHA-256, imports resolved outside checkout, temporary config/home paths, owner-config unchanged booleans, asset lists, tool/schema inventory, exact commands/exits and CI job results for Ubuntu/Windows Python 3.10/3.13. Stdout contains protocol only for server launches. Full suite result can be reused at M3-03 only if source/runtime is unchanged. |
| M3-03 | **depends-on:** M3-02 passed. Own only `docs/release/v1-readiness.md`; runtime config and disposable Basic may change. No tracked script/product edits; assign failures back to their source ticket. Exclusive Live lane. | Follow M3-01 instructions literally with the hashed M3-02 wheel in a new external venv and one real MCP client. Run the three M2-04 scenario commands and `python scripts/stdio_error_smoke.py --set Basic --output "$evidenceRoot/m3-errors.json"` using that venv (script imports must resolve to its installed package). Run `python scripts/stdio_smoke.py --python "$artifactPython" --expect-live --set Basic --output "$evidenceRoot/m3-client.json"`; the runner launches that absolute executable. Record §9 US1–US8 pass/fail, exact tested versions/client, UI comparisons, artifact hashes and all commands/exits in the readiness file. Run `ruff check .` and the lean `python -m pytest -q` once at final frozen head, reusing unchanged M3-02 suite evidence where valid; rerun only for fixes. No unresolved technical blocker/required skip passes; publication/name/tag/PyPI/account actions remain owner-only. |

## 8. FILE-CONFLICT MAP, parallel groups and merge order

Paths below are explicit reservations for M2/M3 as well as the M1a/M1b file lists. New production modules are allowed only when named here or in their ticket. A worker needing an extra path reports it to the orchestrator before editing. Same-file tickets always start from the predecessor's merged head; separate sections in a Python file are still a conflict. All worktrees merge through one orchestrator. No independent worker updates this plan, HANDOFF or shared task files as routine cleanup.

| File / area | Tickets touching it, in merge order |
| --- | --- |
| `pyproject.toml` | M1a-01 → M3-01 → M3-02 |
| `src/abletonlivemcp/install.py`, new `config.py` | M1a-01 only |
| `remote_script/AbletonLiveMCP/core.py`, `src/abletonlivemcp/bridge.py`, `tests/test_bridge.py` | M1a-02 only; runtime gate may reopen that ticket for a narrowly assigned fix |
| Remote Script `__init__.py` | M1b-01 → M1b-02; sequential entry-point tick/cleanup edit, no bridge-core change |
| Remote Script `handlers.py` | M1b-01 → M1b-02 → M2-02 → M2-03 |
| Remote Script new `safety.py` | M1b-01 → M1b-02; M2 consumes it rather than bypassing it |
| Remote Script new `operations.py` | M1b-02 only |
| `src/abletonlivemcp/server.py` | M1b-03 → M2-02 → M2-03; M2-01 hands planner interfaces to M2-02, no parallel server edits |
| `src/abletonlivemcp/models.py` | M1b-03 → M2-01 → M2-02 → M2-03 |
| `src/abletonlivemcp/chain.py` | M1b-03 → M2-01 (sampling chunk/path/plan integration only) → M2-03 (existing-device exposure only) |
| `adapters.py`, `resolve.py`, `preferences.py`, `chain_presets.py`, new `src/abletonlivemcp/data/adapters.json`, `docs/data/example-preferences.json` | M2-01 only |
| `src/abletonlivemcp/judge/__init__.py`, `tests/test_judge.py` | M1b-03 only |
| `tests/test_client_server_install.py`, new `tests/test_install.py` | M1a-01 → M3-02 (remove checkout-only assumptions if remaining) |
| `tests/test_handlers.py` | M1b-01 → M1b-02 → M2-02 → M2-03 |
| `tests/test_chain_tools.py` | M1b-03 → M2-02 → M2-03 |
| `tests/test_handlers_clips.py` | M1b-04 → M2-02 |
| `tests/test_server_settle.py` | M1b-04 → M2-02 → M2-03 |
| `tests/test_chain.py` | M1b-04 → M2-01 → M2-03 (solver regression only) |
| `tests/test_resolve.py` | M1b-04 → M2-01 |
| `tests/test_knowledge.py` | M1b-04 only; production removed-tools check belongs to `test_chain_tools.py` |
| `scripts/live_write_test.py` | M1b-05 → M2-02 → M2-03 → M2-04 |
| `scripts/live_chain_test.py` | M1b-05 → M2-01 → M2-04 |
| `scripts/live_clip_test.py` | M1b-05 → M2-02 → M2-04 |
| `scripts/stdio_error_smoke.py` | M1b-05 → M2-03 → M2-04 |
| `scripts/live_probe_plugins.py`, `live_dump_stock_params.py` | M2-01 (explicit output path/read-vs-mutate labels only) |
| `scripts/stdio_smoke.py`, new `scripts/artifact_smoke.py` | M3-02; use artifact module/client contracts, no private project paths |
| `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `docs/vision.md`, new `docs/adapters.md`, `docs/tools.md`, `docs/release/v1-readiness.md`, `CHANGELOG.md`, package `__init__.py`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, `.github/PULL_REQUEST_TEMPLATE.md` | M3-01; readiness record alone handed to M3-03 for final outcomes |
| `.github/workflows/ci.yml`, new `constraints/release.txt` | M3-02 only |
| `docs/release/bridge-protocol.md`, `m1b-live-evidence.md`, new `m2-live-evidence.md` | M1a-02, M1b-05, M2-04 respectively; separate files |
| `knowledge/**`, `research/**`, `tasks/**`, audit docs, founding prompt, LICENSE | **No ticket edits.** Licence is already MIT; future licence changes require separate owner direction. |

| Parallel group / order | Members and execution rule |
| --- | --- |
| **P1 / M1a** | M1a-01 installer and M1a-02 transport may draft against the agreed isolated-config interface in parallel with disjoint reservations. Merge M1a-01 → M1a-02; M1a-02 integrates the actual merged config/artifact interface and closes the no-Live install/transport gate. Test pruning is not in this parallel group. |
| **P2 / M1b** | M1b-01 follows the passed M1a install/transport gate. No other worker touches handlers/entry point/safety until it merges. M1b-02 then owns the sequential entry-point edit for idle-tick load progress and disconnect cleanup. |
| **P3** | Merge M1b-02 Remote Script → M1b-03 host execution → M1b-04 pruning/contract adaptation. Disjoint M1b-03 drafting may overlap M1b-02 using agreed interfaces, but final integration starts from the dependency's merged head. M1b-04 starts and hands back only after M1b-03; no later adaptation amendment is left outside a ticket. |
| **LIVE-1 / M1b exit** | M1b-05 after M1a and all preceding M1b merges, frozen product code. **NEEDS-LIVE yes.** Use observed explicit stock browser paths; M2 discovery is not a prerequisite. Failed safety exit blocks M2. |
| **P4** | M2-01 owns planner/models; finish its source work and merge before M2-02. No false parallelism across models/server/handlers. |
| **LIVE-2A** | M2-01 stock/user-profile mapping proof. **NEEDS-LIVE yes.** May overlap another worker's read-only docs preparation, never another Live operation. |
| **P5 / LIVE-2B** | M2-02 → M2-03 → M2-04, serial because all affect shared contracts. Each is **NEEDS-LIVE yes**; one holds Live at a time. M2-04 freezes merged product state. |
| **P6** | M3-01 docs/version then M3-02 artifact CI; serial merges because both touch metadata. Independent artifact-script drafting can overlap docs, but no shared-file edits. Both **NEEDS-LIVE no**; real client/Live rehearsal is M3-03. |
| **LIVE-3** | M3-03, **NEEDS-LIVE yes**, final frozen artifact; all other agents release Live and shared evidence file ownership. |

Overall merge order: **M1a-01 → M1a-02 → M1b-01 → M1b-02 → M1b-03 → M1b-04 → M1b-05 → M2-01 → M2-02 → M2-03 → M2-04 → M3-01 → M3-02 → M3-03**. M1a closes at M1a-02; the mandatory real-Live safety exit closes at M1b-05. M1b-04 includes the entire post-execution test adaptation before handback, with no unowned integration amendment. A failed gate returns a bounded fix to the original owner; rerun affected evidence only, then continue. Never resolve conflicts by discarding another ticket's safeguards.

## 9. Verification plan: real Live for every v1 story

### Execution rules and lean offline proof

Use the installed artifact at final rehearsal, not editable imports. Record Windows version, Live exact patch/edition/language, embedded Python, host Python/MCP, component/protocol versions, git SHA and artifact SHA-256. All Live work uses one exclusive ticket at a time. Begin with disposable Basic, monitoring low, transport stopped and a before-state record. No fixture audio or third-party plugin is required for stock acceptance. M1b-05 records actual root/full stock browser paths and supplies them directly; automatic nested discovery is tested only in M2-01. Cleanup may reset Basic between scenarios; never save over a real project. Set/selection changes and a second client are deliberate adversarial actions within the same lane.

Use the existing scripts after making them real acceptance commands. Required checks assert actual values/state and exit nonzero; expected refusals assert the specific error and unchanged state. Optional plugin skips identify what was unproved. Capture structured receipts and relevant UI/log observations; no token/config contents, private project/sample names, audio or plugin state in committed evidence. About one feature scenario each is enough; protocol bounds and unit conversion have focused project-owned tests, not fake DAW timing matrices.

Batch offline checks at each milestone's completed merged state, using the affected files once; the final release gate runs `ruff check .` and the lean `pytest` suite once, with reruns limited to fixes. M3 artifact job performs actual build/install/stdin-stdout initialization outside the checkout. Retain one ephemeral-socket transport boundary scenario, one deterministic cancellation/start scenario, compact solver/adapter/preferences data checks and one installer-failure scenario. No offline test contacts paid providers or production port 9877; real-Live acceptance scripts alone use that port under the exclusive lane. CI host coverage proves Python packaging/contracts, not Live support.

### Story evidence matrix

| Story | Real-Live exercise and evidence required | Gate |
| --- | --- | --- |
| **US1 installation/status** | From an external temp folder/clean venv, install the exact wheel, install bundled script into the actual configured User Library, restart/activate surface with MIDI I/O None, launch one real MCP client with absolute executable. Compare hello's versions/policy/capabilities with Live/log. Disable bridge once and get actionable error. Reinstall compatible script and reconnect; old/wrong-protocol and wrong-token attempts cannot mutate. Default tool list excludes deferred tools even with knowledge/key environment variables. | M1b-05 connection/safety; M3-03 complete stranger rehearsal. |
| **US2 Set inspection** | Compare regular tracks, existing returns, master, scenes, empty/occupied clip slots and top-level devices with Basic's UI. Request two bounded pages and a parameter page; check continuation/omission flags without duplicates. Returned target references identify the same UI objects. Note API capability with zero sampled clips is unknown/not sampled, not proof of absence. | M2-02; final M3-03. |
| **US3 stock chain** | Preview each existing vocal starting point and one explicit four-role request on separate empty audio tracks. Resolve real browser paths to EQ Eight→Compressor→Saturator→Reverb, review omissions, execute the exact accepted/revised plan and compare order plus every applied display/raw value. Prove no unrelated device changed. Reusing plan ID cannot duplicate the chain. Deliberately occupied/selected-device target refuses before load; no occupied-chain support claim. | M1b-05 one compact stock chain; M2-01/M2-04 both presets; M3-03 final plan/build path. |
| **US4 personal preferences/adapters** | With no user file, observe only stock choices. Use a temporary user JSON profile mapping the stock Compressor under an explicit custom ID, choose it via file and inline preference, and get 4:1/5 ms readbacks without source edits. Exercise canonical alias, typo and explicit missing-file errors. A known missing preferred device falls back with evidence; incomplete bounded search remains unknown. If Pro-C 2 is available, separately record product/version/format/exposed controls and requested readbacks; otherwise mark uncertified and keep it out of tested support. | M2-01; M3-03 stock/custom data path mandatory, third-party conditional. |
| **US5 existing processor** | Discover an existing stock compressor's reference/parameters; set ratio 4:1 and threshold -18 dB in a batch, verify readbacks, toggle discovered activator and restore its prior state. Exercise a real disabled/macro-controlled parameter and an automated parameter: refuse without changing them. Reorder/replace a device between discovery/write and assert stale layout refusal, not a write to its neighbor. | M2-03; final M3-03. |
| **US6 organization/mixing** | Rename/color a created regular track; set modest level/pan/mute/solo and one existing reverb send, recording original/actual values and return identity. Inspect return/master devices/mixers. Reorder or change a return before a stale send write and verify refusal. Observe UI units and restore original mixer values by fresh references. No new-return/routing claim. | M2-02/M2-03; final M3-03. |
| **US7 scene/clip/transport** | Create a MIDI track/scene/four-beat clip, name/color it, add three known notes and compare exact pitch/start/duration/velocity/mute. A second add is explicitly additive. Refuse occupied-slot creation and an invalid later note without modifying the existing notes. Launch clip then scene with quantization, observe triggered/pending before playing where applicable, stop clip and transport, change/restore tempo. Set creation returns actual references, not inferred final indices. | M2-04; final M3-03. |
| **US8 policy, concurrency and failure** | In Basic, demonstrate read-only and wrong-key refusal with unchanged tempo/chain; stale Set/track/device references after UI edits/Set switch; second-client mutation Busy during lease; occupied generic-load refusal. Force a real later-stage unsupported-parameter failure after a successful load and retain prefix/current-device receipts while subsequent stages do not run. Delay/lose a response deliberately, read operation status, inspect Live, and prove no retry occurred. Observe large-library search/conversion slice duration and UI responsiveness. | M1b-05 primary safety exit; M2-04 contracts; M3-03 final artifact, reusing unchanged evidence only where component/artifact hashes prove equivalence. |

Real-time timing claims require observed timings. Bounded Python loops do not prove a native plugin cannot block Live. A response lost after transmission always requires readback; a cancelled queued operation has a stronger no-write guarantee only after the synchronized boundary scenario proves it. No screenshot of an empty rack, fake handler assertion, or parsed preset XML substitutes for a deferred musical workflow.

## 10. Risks and containment

| Risk | Containment / stop condition |
| --- | --- |
| Four gates exceed the approximately three remaining sessions | M1a install/transport and M1b mutation/load/Live are separate session caps; M1b safety exit is mandatory before M2. Keep handles/leases/receipts bounded and in memory; no database/job platform. Re-estimate at each exit and stop/re-plan growing tickets. M3 is not funded by this estimate unless measured remaining capacity permits it; additional budget or explicit scope re-plan is required otherwise. Quota exhaustion is not release readiness. |
| Live's object wrappers or Song lifecycle invalidate assumed identities | Runtime proof before broader work; use membership/validity and Set generation together. If uncertain after Set switch, require bridge reconnect/reload; never use names or mutable indices as fallback authorization. |
| Browser loading replaces/misdirects or completes late | Empty-track/owned-prefix restriction, observed device identity/readiness, pending quarantine, one Live lane. Unexpected replacement/late write immediately reopens the safety gate. |
| Native calls block despite Python budgets | Measure on actual library/runtime; slice Python work and reduce sampling. Document indivisible native costs. Never promise hard real-time bounds or solve delays through blind retries. |
| Plugin exposure/version/localization differs | Four-role data schema, requested-intent checks on actual instance, English baseline, incomplete-search semantics, stock-first acceptance. Unverified optional plugins cannot hold stock release hostage. |
| Installer ACL/path/rollback behavior differs on Windows | Temporary-library fault tests isolate home/config as well as the library and prove the owner's secret/write policy unchanged; actual install/reinstall proof follows. Refuse unresolved junctions/unknown folders and preserve backups. Secret leakage or changed owner config fails the gate. |
| Prompt injection through names/reference text | Provenance, limited fixed tools, host permissions and enforced local read-only policy; no claim that text wrapping alone prevents manipulation. Removed filesystem/knowledge/classifier tools eliminate those production paths. |
| Fake-suite pruning removes a real safety guard | Keep a contract inventory and representative guards; remove duplication, not distinct parser/unit/bounds/partial-result semantics. Require real-Live workflow evidence for Live claims. |
| Parallel agents overwrite shared modules or Gemini work | Explicit file reservations, dependency-head worktrees, serial merges, exact-path staging, no knowledge/research/tasks edits, single Live lease owner. Recheck concurrent diffs before handoff. |
| A renamed tool or stale script silently breaks clients | One documented pre-release API break, protocol/capability refusal before writes, pinned launch recipe, two-component upgrade instructions and schema/tool-list artifact check. |
| Release claims outrun evidence or licence/name assumptions | Final record distinguishes verified/experimental/deferred behavior; preserve existing MIT decision; owner alone chooses publication/name/version/account actions. No tag, PyPI upload or visibility change is a ticket step. |

Ready-for-owner-flip means all four milestone exits pass, every IN story has artifact-backed evidence, and remaining items are genuine owner decisions or explicit WON'T-YET roadmap work. This document is Reviewed; it records no owner approval, and no implementation, Live connection or release action has been performed by revising it.

## 11. Review dispositions

The independent reviewer reported no blocking problem. The six findings below are resolved in the plan; existing review evidence was checked against the current source where a code fact affects the decision. Numbered implementation steps for later milestones remain deferred under the size-L planning rule. The coordinator records owner approval separately.

| Finding | Disposition | Reason and tickets touched |
| --- | --- | --- |
| 1. Later-tick readiness lacks a reserved entry point | **ACCEPT** | Rechecked `remote_script/AbletonLiveMCP/__init__.py`: `update_display()` only calls `drain()`; `core.py` has no idle-tick load callback. Reserve the entry point sequentially for M1b-01 → M1b-02. M1b-02 adds a bounded per-display-tick operations callback and disconnect cleanup, proves idle-queue progress with a lean wiring check, and leaves bridge core untouched. Real load timing remains M1b-05 evidence. Tickets: **M1b-01, M1b-02, M1b-05**; §8 reservations updated. |
| 2. Test adaptation depends on execution but merges first | **ACCEPT** | Rechecked the prior plan: the pruning ticket's evidence/depends-on required adaptation after host execution, while its handback preceded that merge. Move all pruning/adaptation and its passing handback after M1b-03 in the same M1b-04 ticket; remove the earlier merge and unowned amendment. M1b-03 no longer depends on its successor; M1b-05 runs the integrated batch afterwards. Tickets: **M1b-03, M1b-04, M1b-05**; §8 merge order corrected. |
| 3. Later milestones need executable steps and evidence | **ACCEPT-IN-PART** | Accept the vague acceptance, missing prerequisites and under-specified reservations. M2/M3 now have explicit dependency/file contracts, future command interfaces and observable outputs for every ticket; M2-02 records UI baselines, exact +1 track/+1 scene deltas, slot counts and page/reference comparisons. Defer numbered steps and per-step ledgers until each milestone starts, as required for an L-size plan; expanding every future ticket now would defeat that staged planning rule. Tickets: **M2-01, M2-02, M2-03, M2-04, M3-01, M3-02, M3-03**. |
| 4. Seven-ticket safety milestone exceeds one session | **ACCEPT** | Split install/transport into M1a (2 tickets) and mutation/load/adapted tests/serial Live into M1b (5 tickets), with distinct exits and consistent IDs. Retain all 14 tickets and their safety conditions. Four capped milestones exceed the roughly three-session budget; §6/§10 state the shortfall and require re-estimation or a budget/scope re-plan rather than promising completion. The M1b real-Live safety exit remains mandatory before M2. Tickets: **M1a-01, M1a-02, M1b-01, M1b-02, M1b-03, M1b-04, M1b-05**; all downstream references and ordering updated. |
| 5. First safety gate must not depend on later nested discovery | **ACCEPT** | Rechecked `resolve.py:Inventory.stock_has()`: it lists `audio_effects` only at `path=[]`; `plan_chain()` constructs first-level stock paths. `chain.py` already distinguishes explicit-path stages, so an observed exact-device path is the appropriate contract. M1b-05 records root/full path arrays and builds the stock chain directly, without role-resolution/discovery; automatic nested discovery remains M2-01. Tickets: **M1b-05, M2-01**; §9 proof clarified. |
| 6. Installer fault test must isolate user config | **ACCEPT** | Rechecked installer source and §5B: current code has no config provisioning, but M1a-01 explicitly adds it at a home location. A temporary library alone would not isolate that new side effect. Specify a common absolute config override plus isolated home discovery for offline checks, redacted before/after comparisons of the owner's existing secret/write policy/config/ACLs, and no fallback to real home on an invalid override. Tickets: **M1a-01, M1a-02, M3-02**; §5B and risk containment updated. |

Consistency check: all ticket IDs referenced in §§6, 8, 9 and 10 are declared in §7; each explicit depends-on precedes its ticket in the overall merge order. Counts are M1a 2 + M1b 5 + M2 4 + M3 3 = 14; there are no legacy safety-ticket IDs or post-handback adaptation amendments. This is a documentation consistency result, not an implementation or Live test pass.
