# Pre-release hardening audit

Date: 2026-11-10. Reviewed source: `eda269e61fe1a162c1d5aac7f133a021b4b7029c`, plus the working-tree implementation present during this review. This is a source-only audit for a user-directed v1 intended for other people's Live installations.

The first priorities are authenticating the local bridge, bounding work inside Live, preserving the installed script during upgrades, and preventing chain operations from configuring the wrong object. Loopback is a useful network restriction, but it does not establish which local caller may control a Set. No critical vulnerability or arbitrary-code-execution exploit was established.

## Scope and evidence limits

- Read README, vision, handoff, lessons, packaging/CI configuration, all implementation modules, development scripts, and relevant test implementations. The handoff's older tool count and pre-chain description were not used as current behavior. The source declares 35 unconditional MCP tools and three conditional knowledge tools: `src/abletonlivemcp/server.py:66`, `src/abletonlivemcp/server.py:278`, `src/abletonlivemcp/server.py:381`.
- Inspected the installed MCP SDK's source and metadata: version 2.3.0. Its synchronous tool dispatcher uses `anyio.to_thread.run_sync`: `.venv/Lib/site-packages/mcp/server/mcpserver/utilities/func_metadata.py:149`. This establishes concurrency for this environment, not every future version allowed by the dependency range.
- Did not connect to port 9877, launch the MCP server, import or execute project code, run tests/builds, install dependencies, contact a judge provider, or change Live. No exploit was reproduced against a running process. The failure scenarios below are source traces; browser behavior and Live-specific loading behavior remain explicitly qualified.
- Did not inspect knowledge/research page contents or alter those directories or tasks. Concurrent changes there were already present. Only this report was written. No subdelegation, commits, pushes, tags, or publication occurred.
- Used the security-audit skill's source-first evidence and severity guidance. The owner's single-report restriction and research-worker role supersede its multi-agent, multi-artifact workflow. This report is not a completed independent-verifier audit or a dependency-CVE/history scan, and makes no exhaustive-coverage claim.

Severity reflects consequences and prerequisites. Findings include security boundary failures and operational hardening defects; a release-blocking reliability problem does not imply a remote exploit. Each finding proposes a change for later implementation; none was implemented here.

## Trust model and browser reachability

The normal path is an MCP host over stdio, then `BridgeClient`, then raw TCP at `127.0.0.1:9877`, then the Remote Script's queue, then Live's main thread. The MCP process also reads local files and optionally calls an external classification service. Sources: `src/abletonlivemcp/server.py:23`, `src/abletonlivemcp/server.py:381`, `src/abletonlivemcp/bridge.py:28`, `remote_script/AbletonLiveMCP/core.py:62`, `remote_script/AbletonLiveMCP/__init__.py:30`.

| Caller or input | What the source establishes |
| --- | --- |
| Another machine on the LAN | The actual Remote Script binds IPv4 loopback, so there is no direct LAN listener. No forwarding/proxy configuration was assessed. `remote_script/AbletonLiveMCP/core.py:30`, `remote_script/AbletonLiveMCP/core.py:46`, `remote_script/AbletonLiveMCP/__init__.py:24`. |
| A local process, including another local OS user's process | Can submit the same JSON methods without authentication, subject to OS/network isolation outside this repository. The listener has no per-user access control. See H01. |
| A process occupying 9877 before Live starts | The client has no server authentication; a lookalike reply with the expected request ID can be accepted. Live logs its bind failure, but the MCP client has no trusted handshake. See H01/H06. |
| A normal web page | JavaScript has no general raw-TCP API. However, this parser continues after invalid HTTP header lines and can accept a newline-terminated JSON line in an HTTP body. Browser local-network permissions, mixed-content rules, preflight behavior, and connection timing can prevent delivery. Browser-to-Live exploitation was not established. See H02. |
| DNS rebinding | Does not make a loopback listener reachable directly from another machine. It can affect browser address/origin treatment if a browser permits the local request. The bridge checks neither authentication nor HTTP origin/host and must not rely on DNS or CORS as authorization. See H02. |
| WebSocket JavaScript | No HTTP 101 handshake or WebSocket frame decoder exists. An ordinary WebSocket client cannot simply send application frames through this raw JSON protocol. The HTTP-body parser issue is a separate mechanism. `remote_script/AbletonLiveMCP/core.py:109`, `remote_script/AbletonLiveMCP/core.py:121`, `remote_script/AbletonLiveMCP/core.py:135`. |
| Markdown, Set metadata, browser/device/parameter names | These are data from lower-trust sources returned to an LLM with mutation and filesystem tools available. Data labels help but do not enforce the user's intent. See H10. |

## Mutation and recovery inventory

There is no exposed track/clip/scene/device delete, note-delete, arbitrary shell/eval, Set save, or arbitrary file-write MCP tool. The bridge's fixed method table is the authoritative restriction: `remote_script/AbletonLiveMCP/handlers.py:474`. Its absence of delete methods is also covered in source tests: `tests/test_handlers_clips.py:380`. The installer is a separate CLI that **does delete files**.

| Surface | Effect and existing protection | Recovery / preview affordance |
| --- | --- | --- |
| `live_set_tempo` | Overwrites the current tempo; 20..999 BPM guard and readback. `remote_script/AbletonLiveMCP/handlers.py:330`. | No old value receipt, preview, confirmation requirement, or undo endpoint. |
| `live_set_device_parameter`; internal batch parameter writes used by chains | Overwrite device state within reported min/max and enabled state. Batch inputs are all validated before writing. `remote_script/AbletonLiveMCP/handlers.py:250`, `remote_script/AbletonLiveMCP/handlers.py:285`. | Readback, but no original-value snapshot or rollback after a setter/runtime failure. |
| `live_load_item` | Delegates any uniquely resolved loadable browser item to Live; selects a track and reports device counts. `remote_script/AbletonLiveMCP/handlers.py:213`. | No item-kind/replace policy, preview, undo grouping, or load-completion protocol. See H07. |
| `live_build_chain`, `live_build_role_chain` | Load devices and write parameters over multiple calls. Shape limit is 12 concrete stages. `src/abletonlivemcp/chain.py:236`, `src/abletonlivemcp/chain.py:248`. | `live_plan_chain` resolves roles read-only, but build does not require a prior plan, and planning is not parameter validation or approval. No transaction or rollback. See H08/H09. |
| `live_create_track`, `live_create_scene`, `live_create_clip`, `live_add_notes` | Add session content. Clip creation refuses occupied slots; note batches are validated before writing. `remote_script/AbletonLiveMCP/handlers.py:309`, `remote_script/AbletonLiveMCP/handlers.py:354`, `remote_script/AbletonLiveMCP/handlers.py:392`, `remote_script/AbletonLiveMCP/handlers.py:434`. | No preview, duplicate-operation receipt, or targeted recovery tool. Existing clips are not deliberately cleared; `set_notes` is the legacy add path, not evidence of a replace-all tool. |
| Track/scene names and track color | Overwrite organizational metadata. `remote_script/AbletonLiveMCP/handlers.py:320`, `remote_script/AbletonLiveMCP/handlers.py:370`. | Current value is returned; previous value is not retained. |
| Play/stop, scene/clip launch/stop | Alter performance state and can interrupt or start playback. `remote_script/AbletonLiveMCP/handlers.py:346`, `remote_script/AbletonLiveMCP/handlers.py:378`, `remote_script/AbletonLiveMCP/handlers.py:464`. | Transport and clip tools reread after 0.3 s; scene launch does not. This is a delay, not a completion guarantee: `src/abletonlivemcp/server.py:59`, `src/abletonlivemcp/server.py:177`. |
| Offline Set and knowledge tools | Read data; project scan traverses caller-supplied roots. `src/abletonlivemcp/server.py:278`, `src/abletonlivemcp/server.py:324`. | No writes to source projects. Directory confinement and resource limits need work; see H13-H16. |
| Classification tools | Can send names and folder fragments to a paid external provider when an inherited key enables it. `src/abletonlivemcp/judge/__init__.py:77`. | Status tool describes payloads; no explicit network opt-in is required. See H17. |
| Installer CLI | Recursively deletes its existing fixed-name destination before copying. `src/abletonlivemcp/install.py:17`. | No dry run, backup, transactional replacement, or ownership verification. See H11/H12. |

Native Live undo may recover individual changes. This code neither groups changes into undo steps nor verifies undo behavior, so recovery of an entire chain must not be promised. A global automatic undo command would also risk undoing the user's intervening work; it is not the smallest v1 fix.

## Findings

### H01 — Unauthenticated local bridge bypasses MCP-host permissions

- **Severity:** high.
- **Evidence:** `remote_script/AbletonLiveMCP/core.py:30`, `remote_script/AbletonLiveMCP/core.py:88`, `remote_script/AbletonLiveMCP/core.py:117`, `remote_script/AbletonLiveMCP/handlers.py:474`; client trusts an unauthenticated peer at `src/abletonlivemcp/bridge.py:32` and `src/abletonlivemcp/bridge.py:47`.
- **Wrong:** Any local TCP caller can invoke every bridge method. A request needs only a string method; there is no token, peer-user check, or distinction between read and write authority. MCP-host tool permissions do not protect this direct entry point. A request ID authenticates neither side.
- **Concrete scenario:** Another logged-in local user, without access to the owner's Live process or MCP approval UI, connects to the loopback port and changes tempo, parameters, transport, or loads browser items into the owner's unsaved Set. A process that wins the port first can impersonate Live to the MCP client. This is local unauthorized control, not demonstrated RCE or LAN exposure.
- **Smallest fix:** Provision a random per-install/per-user secret in an owner-readable configuration location and authenticate every request before queueing. Authenticate server replies as well if port impersonation is in scope, using a challenge/MAC or OS-authenticated local IPC. Keep loopback and never place secrets in logs/tool results. This protects against other users and web content; a hostile process already able to read the owner's secret remains outside that protection.
- **Verdict:** **WORTH-DOING-FOR-V1** — strangers should not silently grant every local OS user control of their open Set.

### H02 — Invalid HTTP lines do not terminate the raw-JSON connection

- **Severity:** medium; the protocol permissiveness is established, browser exploitation is unvalidated.
- **Evidence:** `remote_script/AbletonLiveMCP/core.py:109`, `remote_script/AbletonLiveMCP/core.py:118`, `remote_script/AbletonLiveMCP/core.py:124`, `remote_script/AbletonLiveMCP/core.py:137`.
- **Wrong:** Invalid JSON produces an error and returns the successful send result, so the connection remains open. Empty lines are ignored. Thus an HTTP request line and headers can each fail, after which a JSON body line is dispatched. There is no Origin/Host processing because this is not an HTTP server.
- **Concrete scenario:** An HTTP-speaking client sends headers, a blank line, and a newline-terminated JSON command in one connection; provided error replies can be written, the command reaches the queue. A malicious page could attempt the corresponding simple text-body request if its browser permits local-network delivery. CORS response-read denial does not undo a mutation, but browser permission/preflight and early-close behavior are unresolved prerequisites. DNS rebinding and ordinary WebSocket handshakes are not independently proven bypasses.
- **Smallest fix:** Close on the first malformed/non-protocol line, reject HTTP methods/upgrades immediately, and require H01 authentication before accepting work. Do not add a misleading CORS-only fix to raw TCP. If HTTP is ever deliberately supported, implement explicit Host/Origin checks and authentication in that transport.
- **Verdict:** **WORTH-DOING-FOR-V1** — cheaply removes an avoidable cross-protocol path without depending on browser policy.

### H03 — Connections, worker threads, and pending requests have no aggregate limit

- **Severity:** medium.
- **Evidence:** `remote_script/AbletonLiveMCP/core.py:35`, `remote_script/AbletonLiveMCP/core.py:47`, `remote_script/AbletonLiveMCP/core.py:93`, `remote_script/AbletonLiveMCP/core.py:97`, `remote_script/AbletonLiveMCP/core.py:102`, `remote_script/AbletonLiveMCP/core.py:127`.
- **Wrong:** Every accepted connection creates a daemon thread; the queue is unbounded. The one-second socket timeout loops forever, so it is not an idle deadline. `listen(4)` limits waiting accepts, not active connections. Timed-out queue entries remain until drained.
- **Concrete scenario:** A local process holds many idle or partially written connections open, consuming Live-process threads and memory. If Live is busy loading, many callers can each enqueue a request; cancellation flags do not reclaim those queue slots until Live resumes draining. An accidental reconnect storm can cause the same pressure.
- **Smallest fix:** Add a small active-connection semaphore, a bounded pending queue with immediate Busy errors, and absolute idle/frame deadlines. Release capacity on every exit and close or wake pending connections on stop. Authenticate before reserving expensive work, while still limiting unauthenticated connections.
- **Verdict:** **WORTH-DOING-FOR-V1** — exhaustion occurs inside the DAW process, where availability matters most.

### H04 — Browser and drain budgets do not bound main-thread work

- **Severity:** medium.
- **Evidence:** `remote_script/AbletonLiveMCP/core.py:62`, `remote_script/AbletonLiveMCP/handlers.py:140`, `remote_script/AbletonLiveMCP/handlers.py:178`, `remote_script/AbletonLiveMCP/handlers.py:198`, `remote_script/AbletonLiveMCP/handlers.py:200`, `remote_script/AbletonLiveMCP/handlers.py:299`, `remote_script/AbletonLiveMCP/handlers.py:407`.
- **Wrong:** Search checks its 4,000-node and result limits only in the outer loop; the entire next folder is processed by the inner loop. `_children` first materializes all children, including for listing before slicing to 200. Drain limits request count, not elapsed work. A batch can also call parameter display conversion up to 64 × 129 times in one request. Note limits bound the Python result after Live's retrieval call, not necessarily the native retrieval work.
- **Concrete scenario:** A stranger's sample/User Library folder contains tens of thousands of immediate children. One browser search still processes them all on Live's main thread despite the advertised budget; eight heavy requests can run in one display tick. The socket's ten-second wait cannot interrupt a running handler.
- **Smallest fix:** Enforce visit/result limits inside the child loop, avoid repeated/eager child copies where Live supports iteration, and add monotonic time checks between bounded work units. Yield/reschedule long walks and batches over display ticks. A single blocking native load cannot be preempted safely; use a separate readiness lifecycle for it (H07).
- **Verdict:** **WORTH-DOING-FOR-V1** — ordinary large libraries can make a supposedly bounded read stall the UI/control thread.

### H05 — Timeout cancellation races with starting a mutation

- **Severity:** medium.
- **Evidence:** `remote_script/AbletonLiveMCP/core.py:69`, `remote_script/AbletonLiveMCP/core.py:71`, `remote_script/AbletonLiveMCP/core.py:128`, `remote_script/AbletonLiveMCP/core.py:131`; existing test covers only cancellation before a later drain at `tests/test_bridge.py:111`.
- **Wrong:** Checking `cancelled`, setting `started`, and deciding the timeout kind are unsynchronized across threads. The claim that a plain Timeout means a request can never run late has a race. Caller disconnect is also not observed while a queued request waits for the main thread.
- **Concrete scenario:** Drain observes `cancelled == False`, then the socket thread times out, sets cancellation, observes `started == False`, and sends Timeout. Drain resumes, marks started, and performs the mutation. A caller may retry what it was told never started, creating duplicate tracks/notes or loads. Separately, a caller that disconnects before execution can still leave queued work behind.
- **Smallest fix:** Protect queued→started/cancelled transitions with a lock and one explicit state machine. Make shutdown/disconnect cancellation best-effort before start. After start or any lost connection following request transmission, report an unknown/may-have-applied outcome and require readback; do not retry automatically.
- **Verdict:** **WORTH-DOING-FOR-V1** — correct outcome semantics prevent unintended edits after timeout and duplicate retries.

### H06 — Framing, reply size, and JSON contracts are incompletely enforced

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/bridge.py:23`, `src/abletonlivemcp/bridge.py:35`, `src/abletonlivemcp/bridge.py:39`, `src/abletonlivemcp/bridge.py:46`; `remote_script/AbletonLiveMCP/core.py:108`, `remote_script/AbletonLiveMCP/core.py:113`, `remote_script/AbletonLiveMCP/core.py:121`.
- **Wrong:** The client accumulates reply bytes without a cap and uses a per-socket-operation timeout rather than an overall deadline. It assumes a decoded object/error shape and does not normalize all malformed-peer failures into BridgeError. The server checks MAX_FRAME only after extracting complete lines: a line can exceed the nominal 1 MiB by up to 65,535 bytes before its terminating newline. It validates method type but not params/id shape; deep JSON can raise RecursionError outside the ValueError handler.
- **Concrete scenario:** A lookalike or faulty bridge sends a never-terminated response in small chunks less than 15 seconds apart, keeping an MCP worker occupied and growing its buffer indefinitely. A valid JSON array reply crashes `.get`. A direct caller can put a non-object params value onto Live's main thread, where it fails unnecessarily.
- **Smallest fix:** Set request and response byte caps before JSON parsing, check every extracted line length, and use a monotonic total deadline. Validate request/reply envelopes, params objects, bounded scalar IDs, and matching protocol version before mutations. Convert decoding, shape and parser-depth failures to bounded protocol errors, closing the connection on invalid input. Use an incrementally filled buffer rather than repeated unbounded byte concatenation.
- **Verdict:** **WORTH-DOING-FOR-V1** — keeps bad peers and compatibility failures from becoming unbounded waits or obscure crashes.

### H07 — Browser loading has neither a replacement policy nor a completion contract

- **Severity:** medium.
- **Evidence:** `remote_script/AbletonLiveMCP/handlers.py:12`, `remote_script/AbletonLiveMCP/handlers.py:213`, `remote_script/AbletonLiveMCP/handlers.py:222`, `remote_script/AbletonLiveMCP/handlers.py:225`, `src/abletonlivemcp/chain.py:271`.
- **Wrong:** Every loadable item under roots including sounds, samples, User Library, plugins and current project is forwarded to `app.browser.load_item`. Only the selected track is set; device selection/insertion context and expected item kind are not constrained. Counts are read immediately, and the chain builder interprets anything other than +1 as an error after the call has already happened.
- **Concrete scenario:** A slow plugin/preset finishes loading after the initial count read, so a chain reports failure even though the device subsequently appears; retry can add another copy. Where Live's selected-device/item context performs replacement rather than append, the current check detects only a count mismatch after potential damage. Whether a particular sample, rack, Set or preset is loadable and what it replaces requires isolated Live validation; arbitrary native-code execution was not established by this audit.
- **Smallest fix:** Define supported item kinds and default to append-only device loads; refuse ambiguous or potentially replacing operations unless the host/user explicitly chose that operation. Capture actual device identity before/after, set a supported insertion context, and report a bounded pending/ready/failed lifecycle via scheduled main-thread checks. Do not sleep on Live's thread or treat an immediate count as proof of completion.
- **Verdict:** **WORTH-DOING-FOR-V1** — library contents and plugin load times differ across installations, and errors must not conceal completed loads.

### H08 — Multi-call edits target shifting indices rather than object identities

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/chain.py:271`, `src/abletonlivemcp/chain.py:274`, `src/abletonlivemcp/chain.py:155`, `src/abletonlivemcp/chain.py:168`, `remote_script/AbletonLiveMCP/handlers.py:109`, `remote_script/AbletonLiveMCP/handlers.py:116`; installed SDK scheduling at `.venv/Lib/site-packages/mcp/server/mcpserver/utilities/func_metadata.py:164`.
- **Wrong:** A valid track/device index is resolved anew on each request. Chain workflows span multiple TCP calls and have no workflow serialization or expected Set/track/device identity. The builder also assumes the added device is the last device based only on a count increase. Main-thread dispatch makes individual handlers sequential, not entire chains atomic.
- **Concrete scenario:** Between parameter read and write, the user inserts/deletes/reorders a device or track. The old index is still valid but now selects a different object, so range-valid settings alter the wrong processor. Two concurrent chain builds can interleave stage order; an insertion before an existing last device can also invalidate the last-index assumption. The latter's exact insertion behavior needs Live validation, whereas the index-shift flaw is inherent in the source.
- **Smallest fix:** Return bridge-owned object handles tied to a Set generation, identify the actual newly added device, and check expected identities at the final write. Reject stale targets. Serialize MCP mutation workflows to avoid self-interleaving; identity checks must still catch owner/UI edits and Set changes.
- **Verdict:** **WORTH-DOING-FOR-V1** — a wrong-target write is more damaging than a clean refusal and violates user-directed editing.

### H09 — Partial chains and parameter batches lack reliable recovery receipts

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/chain.py:257`, `src/abletonlivemcp/chain.py:265`, `src/abletonlivemcp/chain.py:278`, `src/abletonlivemcp/chain.py:287`, `remote_script/AbletonLiveMCP/handlers.py:285`, `src/abletonlivemcp/server.py:247`, `src/abletonlivemcp/server.py:264`.
- **Wrong:** Device-name preflight does not prevalidate explicit paths, actual device parameters or target values. The builder mutates as it goes and continues after some parameter problems. A later BridgeError/ChainError can discard the accumulated stage report. Batch input validation does not roll back setters already executed when a later setter/readback fails. There is no operation-level undo grouping or before-value receipt.
- **Concrete scenario:** The first compressor loads and is configured; a later preset path fails or a plugin throws during parameter write. The host receives an error instead of a complete list of changes that remain. A model retries the whole chain and duplicates the successful prefix. A misspelled parameter can leave a newly active default device even though `ok` is false, as the test explicitly permits: `tests/test_chain.py:243`.
- **Smallest fix:** Return structured partial outcomes on every failure, including operation ID, completed loads/writes, original values and unknown outcomes. Stop subsequent stages on failure by default. Validate resolvable paths/targets before the first mutation and make partial application explicit in tool descriptions. Group bounded edits in Live undo steps where supported, without holding an undo group across unrelated user work. Do not auto-retry or auto-delete successful stages.
- **Verdict:** **WORTH-DOING-FOR-V1** — predictable partial-failure handling is essential even if full transactions and a general undo tool are deferred.

### H10 — Untrusted tool text can steer an LLM into unrestricted mutations

- **Severity:** medium; the exposure is established, successful model manipulation is not demonstrated.
- **Evidence:** `src/abletonlivemcp/knowledge.py:105`, `src/abletonlivemcp/knowledge.py:152`, `src/abletonlivemcp/knowledge.py:207`, `remote_script/AbletonLiveMCP/handlers.py:162`, `remote_script/AbletonLiveMCP/handlers.py:123`, `remote_script/AbletonLiveMCP/handlers.py:240`, `src/abletonlivemcp/server.py:48`, `src/abletonlivemcp/server.py:285`, `src/abletonlivemcp/server.py:306`.
- **Wrong:** Knowledge bodies/headings, browser/device/track names and display/error text enter model-visible results. The knowledge tool descriptions correctly say reference data is never instructions, but returned data has no consistent provenance/untrusted wrapper across tools. There is no server read-only policy, mutation authorization boundary beyond host behavior, or explicit MCP read/destructive/idempotent annotations in registration. An attacker-supplied `confirm: true` would not constitute human approval either.
- **Concrete scenario:** A shared Markdown page or imported Set/device name claims to be a system instruction and asks the model to change tempo, load an unrelated preset, or scan another project directory. If the host/model follows it, the available tools carry out valid but user-unrequested actions. H13 allows additional project metadata disclosure. These tools do not themselves provide shell execution or general outbound arbitrary-URL requests; the risk is unauthorized use of their actual capabilities.
- **Smallest fix:** Consistently mark returned third-party text as untrusted data with provenance and keep instructions in trusted tool descriptions. Add explicit tool annotations and an owner-configured read-only mode enforced at bridge dispatch and MCP entry points. Let the MCP host retain user approval/control of mutation-capable tools; make planning the default research path. A plan ID or model-supplied confirmation boolean is not an approval mechanism. Do not promise prompt sanitization can eliminate this risk.
- **Verdict:** **WORTH-DOING-FOR-V1** — make the user's authority enforceable while allowing already-authorized editing without repeated prompts.

### H11 — Installer destroys the current installation before validating its replacement

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/install.py:17`, `src/abletonlivemcp/install.py:18`, `src/abletonlivemcp/install.py:20`, `src/abletonlivemcp/install.py:22`, `src/abletonlivemcp/install.py:23`.
- **Wrong:** A directory containing Presets is treated as a User Library, and any existing `Remote Scripts/AbletonLiveMCP` is recursively removed before source existence/readability or copy success is established. Fixed naming avoids arbitrary child-name traversal, but proves neither ownership nor canonical location. A linked parent can redirect the destination outside the intended library. There is no backup or interrupted-copy recovery.
- **Concrete scenario:** An upgrade from a broken/missing-source package deletes a working Remote Script and then fails to copy. Disk/permission failure has the same ordering problem. A user-maintained same-name folder loses its extra files. A `Remote Scripts` parent link/junction can place the fixed-name deletion elsewhere; exact platform link behavior was not tested and no claim is made that `rmtree` follows a leaf symlink.
- **Smallest fix:** Resolve and verify source and destination boundaries first, reject unexpected link/reparse-point components, and recognize an owned installation. Copy/validate into a sibling temporary directory, retain the old directory as a backup, then replace with rollback on failure. Refuse an unrecognized existing folder unless the user explicitly selected replacement. Check that source and destination cannot overlap.
- **Verdict:** **WORTH-DOING-FOR-V1** — installation failure should preserve the previously working script and unrelated user files.

### H12 — Wheel installs do not contain the Remote Script the installer expects

- **Severity:** medium.
- **Evidence:** `pyproject.toml:23`, `pyproject.toml:30`, `src/abletonlivemcp/install.py:12`, `.github/workflows/ci.yml:21`, `tests/test_client_server_install.py:58`.
- **Wrong:** The wheel includes only `src/abletonlivemcp`, while `source_dir()` searches a repository-relative `remote_script/AbletonLiveMCP` path outside that package. The exposed installer entry point therefore relies on a checkout layout that a normal wheel lacks. CI and installer tests use that checkout/editable layout.
- **Concrete scenario:** A stranger installs the wheel and runs the advertised installer. Source discovery points outside the installed package and copying fails; if a previous script exists, H11 deletes it first. This conclusion follows from the declared package layout; no wheel was built or installed during this audit.
- **Smallest fix:** Include the Remote Script as package resources and locate it through `importlib.resources`, then check required files before touching the destination. Add one clean-wheel installation/installer check in a temporary library; it must not contact Live.
- **Verdict:** **WORTH-DOING-FOR-V1** — checkout-only installation is incompatible with a public Python package.

### H13 — Offline file tools ignore the repository's configured-directory boundary

- **Severity:** medium.
- **Evidence:** Policy at `SECURITY.md:6`; calls at `src/abletonlivemcp/server.py:325`, `src/abletonlivemcp/server.py:337`; direct opens/traversal at `src/abletonlivemcp/als/reader.py:214`, `src/abletonlivemcp/als/usage.py:35`.
- **Wrong:** There is no configured project-root allowlist or canonical containment check. The MCP caller supplies any path/root readable by the process. Set filenames, track/device names, sample paths and scan errors can then be returned from outside the user's intended project area. The owner sandbox path mentioned in HANDOFF is documentation, not enforcement.
- **Concrete scenario:** An injected tool-output instruction persuades the model to scan an unrelated mounted/client-project folder. The tool discloses private creative metadata to the model even though the user authorized work on one project. On Windows, caller-controlled UNC paths can also initiate filesystem/network access; credential exchange depends on OS policy and was not tested. This is not unrestricted plaintext secret-file read: successful summaries must parse as gzip Live Set XML.
- **Smallest fix:** Require owner-configured allowed project roots, resolve candidate files and scan roots before access, and enforce containment on discovered files too. Reject network/device paths by default unless an explicitly configured root permits them. Do not let a tool call enlarge the allowlist. Document exactly which metadata leaves the local process for the MCP host.
- **Verdict:** **WORTH-DOING-FOR-V1** — fulfills the explicit security policy and bounds prompt-injection-driven discovery.

### H14 — Knowledge discovery follows Markdown file links outside its root

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/knowledge.py:57`, `src/abletonlivemcp/knowledge.py:60`, `src/abletonlivemcp/knowledge.py:93`, `src/abletonlivemcp/knowledge.py:170`.
- **Wrong:** Page IDs come from enumeration, which safely avoids ordinary caller path traversal, but `is_file()` and `read_text()` follow file symlinks. There is no resolved-target containment check. The `.md` test applies to the link name, not the target. Directory-link/junction recursion also depends on platform/Python behavior and is not a control to rely on.
- **Concrete scenario:** A contributed or synced knowledge tree contains `reference.md` pointing to a readable file outside the knowledge root. Reading that page returns the target's content, regardless of target extension. Listing and searching also open it. This requires the link to exist on the host; no link or secret was accessed in this audit.
- **Smallest fix:** Resolve the configured root and each discovered page and require target containment before opening; reject symlink/reparse-point components for an untrusted knowledge tree. If hostile concurrent link swapping is in scope, use no-follow handle-based reads or disallow that writer threat model explicitly; a check followed by an ordinary path open is raceable.
- **Verdict:** **WORTH-DOING-FOR-V1** — closes a concrete escape from the intended Markdown-only reference folder.

### H15 — Knowledge output truncation does not bound ingestion cost

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/knowledge.py:60`, `src/abletonlivemcp/knowledge.py:79`, `src/abletonlivemcp/knowledge.py:82`, `src/abletonlivemcp/knowledge.py:94`, `src/abletonlivemcp/knowledge.py:101`, `src/abletonlivemcp/knowledge.py:133`, `src/abletonlivemcp/knowledge.py:200`.
- **Wrong:** Each call enumerates all pages; list/search read whole files, and read_page reads/splits/parses the whole selected file before truncating text to 60,000 characters. Section boundary discovery repeatedly scans later headings, allowing quadratic work for many same-level headings. Page counts, file bytes, headings, query length and total listing size lack ingestion limits.
- **Concrete scenario:** One oversized or heading-dense contributed page makes routine knowledge_list/search expensive in memory and CPU. A small search result limit and snippet cap do not limit the work needed to produce it. Concurrent readers can multiply that cost.
- **Smallest fix:** Bound file bytes and total scan/page/heading/query budgets before full reads, skip oversized pages with explicit diagnostics, and cap list/error output. Compute section boundaries with a stack in one pass. A simple bounded cache keyed by file metadata can avoid repeated work without requiring a database.
- **Verdict:** **WORTH-DOING-FOR-V1** — knowledge is contributed data, and one page should not monopolize an MCP process.

### H16 — Offline Set scans can retain unbounded parsed data and fail on hostile XML

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/als/reader.py:20`, `src/abletonlivemcp/als/reader.py:84`, `src/abletonlivemcp/als/reader.py:169`, `src/abletonlivemcp/als/reader.py:211`, `src/abletonlivemcp/als/reader.py:218`, `src/abletonlivemcp/als/usage.py:40`, `src/abletonlivemcp/als/usage.py:85`.
- **Wrong:** The 512 MiB decompression cap is real, but allows a large XML tree plus retained summaries. Scanning collects every path, every SetSummary and every error before aggregation, with no file-count, total-byte or wall-clock budget. Recursive `_walk` can exceed Python recursion depth; scan catches AlsError only. The DTD/entity declaration check examines byte prefixes rather than using parser-level rejection, so padding or other XML encodings can evade its stated rejection policy. ElementTree's external-entity behavior does not establish an XXE file-read exploit here.
- **Concrete scenario:** A large downloaded project collection, or many synthetic Sets under a selected root, consumes substantial memory before results return. A deeply nested valid gzip/XML file raises RecursionError and aborts the entire scan rather than appearing as one corrupt-file error. A padded DTD is outside the promised rejection guard; entity-amplification consequences depend on the installed XML parser and were not tested.
- **Smallest fix:** Stream per-Set summaries into aggregation, cap files/aggregate bytes/time/results, and use a practical configurable per-Set limit. Add an explicit nesting/node budget or iterative traversal, translate parser-limit errors into AlsError, and reject DTD/entities through parser callbacks or a parser that forbids them regardless of encoding/offset. Keep the decompression cap and do not resolve sample references into extra file reads.
- **Verdict:** **WORTH-DOING-FOR-V1** — read-only downloaded Sets must not be able to exhaust or repeatedly crash a normal scan.

### H17 — Inherited API keys silently enable paid external classification

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/judge/__init__.py:77`, `src/abletonlivemcp/judge/__init__.py:86`, `src/abletonlivemcp/judge/jev.py:40`, `src/abletonlivemcp/judge/jev.py:117`, `src/abletonlivemcp/server.py:344`, `src/abletonlivemcp/server.py:358`, `src/abletonlivemcp/server.py:372`; public-facing network expectation at `CONTRIBUTING.md:25`.
- **Wrong:** Auto mode chooses an external backend based on key presence alone. MCP hosts often pass inherited environment credentials for other integrations. Tool descriptions do not require calling judge_status first or explicitly opting in to network use. Up to 200 serial calls can occur per classification tool call, with a 30-second timeout per OpenRouter call and no overall budget. The SDK transport's timeout is not set here.
- **Concrete scenario:** A user expecting local name classification has OPENROUTER_API_KEY in the launching shell. A batch sends client/sample/folder names to OpenRouter and consumes paid quota without a separate feature opt-in. Slow requests can keep a batch busy for roughly 100 minutes at the per-call timeout scale; no such calls were made during this audit.
- **Smallest fix:** Default to rules unless the owner explicitly selects an external backend through configuration; key presence should supply credentials, not select behavior. State payload/provider/cost behavior in tool descriptions and setup docs. Add a modest batch/overall deadline, provider timeout, response-size limit and cancellation checks between items. Do not equate optional inference with telemetry; document the actual data transfer.
- **Verdict:** **WORTH-DOING-FOR-V1** — protects privacy and paid quota across unfamiliar MCP host environments.

### H18 — Expected file/provider failures become opaque MCP crashes

- **Severity:** low.
- **Evidence:** `src/abletonlivemcp/server.py:32`, `src/abletonlivemcp/server.py:45`, `src/abletonlivemcp/als/reader.py:25`, `src/abletonlivemcp/judge/__init__.py:48`, `src/abletonlivemcp/judge/jev.py:50`; installed SDK masking at `.venv/Lib/site-packages/mcp/server/mcpserver/tools/base.py:208`.
- **Wrong:** `_tool` exposes ValueError and BridgeError deliberately, but AlsError and JudgeError inherit directly from Exception. Missing/corrupt files, provider rate limits and ordinary judge outages therefore receive generic error text through the inspected SDK. Malformed bridge JSON also has inconsistent classification (H06). In contrast, bridge exception messages are sent verbatim and preferences errors include absolute paths.
- **Concrete scenario:** A new user supplies a damaged Set or hits a 429. The host sees an execution failure instead of an actionable explanation and may repeat the expensive call. With a Live mutation failure, raw underlying text can reveal local paths or contain attacker-controlled names; no secret-bearing message was found in the reviewed production paths.
- **Smallest fix:** Map the known domain exceptions to bounded, structured ToolFailure messages with stable kinds, retryability and may-have-applied status where appropriate. Preserve useful names/paths only within the authorized scope, classify them as untrusted data, and keep unexpected traceback details on stderr/Live's log. Never expose provider headers or key values.
- **Verdict:** **WORTH-DOING-FOR-V1** — small change that makes ordinary setup/outage problems understandable without weakening error privacy.

### H19 — Remote bridge has no useful bounded operational history

- **Severity:** low.
- **Evidence:** Logger stored but never used at `remote_script/AbletonLiveMCP/core.py:34`; handler errors are returned at `remote_script/AbletonLiveMCP/core.py:80`; startup logging only at `remote_script/AbletonLiveMCP/__init__.py:26` and `remote_script/AbletonLiveMCP/__init__.py:28`.
- **Wrong:** Startup success/failure is logged, but accepted methods, duration, queue pressure, timeout state and unexpected runtime failures are not recorded through the provided logger. Once a mutation response is lost, there is no bridge-side receipt/history to help distinguish failure from completion.
- **Concrete scenario:** A user reports that a plugin load timed out and later appeared, or that repeated Busy/timeouts preceded a UI stall. The current log establishes only that the server started, making diagnosis dependent on the host's conversation and uncertain state.
- **Smallest fix:** Add bounded/rate-limited event logging or an in-memory recent-operation ring containing request/operation ID, method, status and duration. Log unexpected exceptions locally, never tokens, full Markdown pages, plugin state or complete request bodies. Keep MCP stdout protocol-only. Mutation receipts in H09 matter more than a persistent audit subsystem.
- **Verdict:** **DEFER** — a full operational history is useful after v1; basic timeout/failure counters can accompany the higher-priority fixes without building a logging platform.

### H20 — Release verification resolves mutable dependencies and action tags

- **Severity:** low; exposure/reproducibility risk, not an identified compromised dependency.
- **Evidence:** `pyproject.toml:2`, `pyproject.toml:20`, `pyproject.toml:27`, `pyproject.toml:28`, `.github/workflows/ci.yml:17`, `.github/workflows/ci.yml:18`, `.github/workflows/ci.yml:21`.
- **Wrong:** Builds use unconstrained hatchling; optional SDK/dev packages have only lower bounds; MCP has a major-version range but no tested release constraints/lock or hashes. CI actions use mutable major tags, and the workflow declares neither explicit token permissions nor disabled persisted checkout credentials. Actual repository token defaults were not inspected and are not assumed to be write-enabled.
- **Concrete scenario:** Reinstalling the same release or rerunning CI later selects new dependencies with changed behavior. A compromised/moved dependency or action tag would execute code during install/CI; no current compromise or applicable CVE was established. Editable-install-only CI also misses H12.
- **Smallest fix:** Keep sensible public library compatibility ranges, but record a tested release/CI constraints set or lock with hashes; constrain the optional SDK to supported versions. Pin action SHAs with update automation, declare `permissions: contents: read`, disable checkout credential persistence when unused, and add the clean-wheel check. Public users need not be forced onto permanently frozen transitive versions.
- **Verdict:** **WORTH-DOING-FOR-V1** — a small reproducible release baseline is proportionate; a full SBOM/provenance pipeline can wait.

## Verification still needed in an isolated environment

These are follow-up acceptance checks, not instructions to touch the owner's active session. None ran here.

- Use a disposable local bridge harness with inert dispatch and strict process/resource limits to check malformed/HTTP-shaped input, exact frame boundaries, reply caps, idle deadlines, queue saturation and timeout state transitions. It must use an isolated loopback namespace and never port 9877 on this host. The browser hypothesis additionally needs a real browser in that isolation; record browser version and local-network/preflight policy.
- On an owner-authorized disposable Live Set, verify append-versus-replace behavior by item kind and selected-device context, delayed plugin loading/readiness, actual device identity, Set switching, concurrent UI edits and native undo behavior. Source review cannot settle those Live-specific outcomes.
- After fixes, use one packaging check from a clean wheel into a temporary User Library and one focused regression per boundary. Do not expand the fake-Live suite indiscriminately or repeatedly run all tests. Existing tests prove intended simple behavior in source, not these adverse interleavings: `tests/test_bridge.py:111`, `tests/test_handlers.py:125`, `tests/test_client_server_install.py:58`, `tests/test_chain.py:236`.
- Review the precise release dependency resolution/advisories and repository token/release settings when preparing the public artifact. No online advisory query, historical secret scan, artifact build, or release action was performed here.

## Ranked top 10

Ranking balances unauthorized control, data preservation and likelihood for a first-time user; several medium reliability defects deserve action before lower-likelihood security refinements.

| Rank | Finding | First action |
| --- | --- | --- |
| 1 | H01 — unauthenticated local control | Authenticate requests before enqueueing; protect configuration secrets and establish the peer identity. |
| 2 | H11 — destructive installer ordering | Validate/stage replacement and preserve the current installation. |
| 3 | H12 — missing wheel Remote Script | Package and locate resources; validate installation from the wheel. |
| 4 | H08 — changing target indices | Verify stable Set/track/device identity at the write boundary. |
| 5 | H03 — unlimited bridge workers/queue | Cap connections and pending work; add real idle deadlines. |
| 6 | H04 — ineffective main-thread budgets | Stop/yield inside browser loops and bound per-tick work. |
| 7 | H07 — ambiguous and unfinished loads | Restrict load semantics and track completion/actual added device. |
| 8 | H09 — incomplete failure/recovery reports | Return partial-operation receipts and stop further stages by default. |
| 9 | H05 — cancellation/start race | Synchronize state transitions and expose unknown mutation outcomes. |
| 10 | H13 — unrestricted project roots | Enforce owner-configured canonical roots before filesystem access. |

H02's fail-closed parser change belongs with H01/H06; it should not wait for a demonstrated browser exploit. H10's provenance, tool metadata and read-only mode should accompany the mutation-boundary work. H14 and H17 are also worthwhile before enabling shared knowledge trees or external classification for strangers.

## Things checked that were fine, within the stated limits

- **Actual bind is loopback IPv4 and MCP defaults to stdio.** No LAN/HTTP MCP listener is started by the entry point: `remote_script/AbletonLiveMCP/core.py:46`, `remote_script/AbletonLiveMCP/__init__.py:24`, `src/abletonlivemcp/server.py:382`.
- **Live API handlers run on the main thread.** Socket workers parse/enqueue; `update_display()` drains. Socket send/receive is outside the drain, so the main thread does not wait on network I/O: `remote_script/AbletonLiveMCP/core.py:62`, `remote_script/AbletonLiveMCP/core.py:117`, `remote_script/AbletonLiveMCP/__init__.py:30`.
- **No eval, shell-command bridge, arbitrary attribute dispatch, remote download, Set-save or delete tool was found.** Dispatch uses a fixed allowlist: `remote_script/AbletonLiveMCP/handlers.py:474`, `remote_script/AbletonLiveMCP/handlers.py:505`. Loading trusted installed plugins is still native code managed by Live; no arbitrary-code-execution claim follows from this method table alone.
- **Ordinary knowledge traversal strings do not become filesystem paths.** `..` components are rejected and selection uses enumerated page IDs; the remaining issue is discovered links, H14: `src/abletonlivemcp/knowledge.py:170`, `tests/test_knowledge.py:17`.
- **Browser paths are exact child names, not filesystem paths.** Roots are allowlisted; loading refuses missing/ambiguous children and non-loadable folders. A caller cannot get filesystem `../` traversal simply by passing browser path segments: `remote_script/AbletonLiveMCP/handlers.py:132`, `remote_script/AbletonLiveMCP/handlers.py:217`. Read-only browser_list does choose the first duplicate name; it is not the loading guard.
- **Important numeric/index guards are deliberate.** Track/device/scene/parameter indexes reject booleans and out-of-range values; tempo rejects out-of-range/nonfinite values through its range comparison; note pitch/velocity/mute and finite timing are validated: `remote_script/AbletonLiveMCP/handlers.py:31`, `remote_script/AbletonLiveMCP/handlers.py:54`, `remote_script/AbletonLiveMCP/handlers.py:69`, `remote_script/AbletonLiveMCP/handlers.py:109`, `remote_script/AbletonLiveMCP/handlers.py:245`, `remote_script/AbletonLiveMCP/handlers.py:330`. This does not mean every handler has equally strict schemas: track creation/color still coerce values, and strings lack length caps (`remote_script/AbletonLiveMCP/handlers.py:309`, `remote_script/AbletonLiveMCP/handlers.py:320`).
- **Occupied MIDI clips are protected and note batches prevalidate.** Clip creation refuses an occupied slot; add_notes checks batch fields and read API availability before mutating: `remote_script/AbletonLiveMCP/handlers.py:392`, `remote_script/AbletonLiveMCP/handlers.py:434`.
- **Parameter sampling is read-only and write ranges/enabled state are checked.** Up to 129 samples and 64 batch items are enforced. All batch validation precedes assignment, while runtime setter atomicity is not promised: `remote_script/AbletonLiveMCP/handlers.py:250`, `remote_script/AbletonLiveMCP/handlers.py:263`, `remote_script/AbletonLiveMCP/handlers.py:273`, `remote_script/AbletonLiveMCP/handlers.py:285`.
- **There is no automatic retry in the bridge client or handlers.** IDs are correlated and TimeoutAfterStart is surfaced. Pre-start cancellation works in the simple nonracing case; H05 narrows its guarantee: `src/abletonlivemcp/bridge.py:47`, `src/abletonlivemcp/bridge.py:51`, `remote_script/AbletonLiveMCP/core.py:128`, `tests/test_bridge.py:111`.
- **Known closure/startup failures are contained.** EOF becomes ConnectionClosed; connection errors become an actionable Live-unreachable message; Remote Script startup catches/logs exceptions so a bind failure should not escape initialization. Shutdown stops accepts, though queued waits/worker cleanup need H03: `src/abletonlivemcp/bridge.py:37`, `src/abletonlivemcp/bridge.py:40`, `remote_script/AbletonLiveMCP/__init__.py:27`, `remote_script/AbletonLiveMCP/core.py:53`.
- **Offline file tools do not modify Sets or follow sample references into reads.** They parse gzip/XML and return metadata. A finite decompression guard exists, and scans prune Backup folders; broader budgets are H16: `src/abletonlivemcp/als/reader.py:134`, `src/abletonlivemcp/als/reader.py:214`, `src/abletonlivemcp/als/usage.py:35`.
- **Knowledge text is explicitly called reference data.** Evidence labels and truncation flags exist, and tools register only when a knowledge directory exists at server import. Knowledge/research are excluded from the declared distribution paths: `src/abletonlivemcp/server.py:51`, `src/abletonlivemcp/server.py:285`, `src/abletonlivemcp/server.py:306`, `src/abletonlivemcp/knowledge.py:201`, `pyproject.toml:30`, `pyproject.toml:33`. No artifact was built to independently verify exclusion.
- **Role planning is read-only and explains substitutions/guesses.** Opaque plugins are skipped, and missing devices/unsupported intents are reported. It is a useful preview primitive, subject to H04/H15-style bounds and the distinction from approval: `src/abletonlivemcp/resolve.py:115`, `src/abletonlivemcp/resolve.py:137`, `src/abletonlivemcp/resolve.py:95`, `src/abletonlivemcp/server.py:247`.
- **No embedded credentials were found in the reviewed source/config/scripts.** Keys are referenced by environment-variable name, .env files are ignored, and OpenRouter errors expose status/type rather than response headers/key text: `src/abletonlivemcp/judge/jev.py:34`, `src/abletonlivemcp/judge/jev.py:45`, `src/abletonlivemcp/judge/jev.py:50`, `.gitignore:10`, `tests/test_judge_jev.py:85`. This is not certification of Git history, excluded page content, local environments, or all SDK logging paths.
- **External classifier payloads are intentionally narrow.** Sample file name plus two folder fragments, or plugin name/format; no audio/Set contents are read for classification. The default OpenRouter URL is HTTPS and the rules backend requires no key/network. H17 concerns selecting and budgeting the external backend, not fabricated full-file uploads: `src/abletonlivemcp/server.py:365`, `src/abletonlivemcp/judge/jev.py:27`, `src/abletonlivemcp/judge/jev.py:117`, `src/abletonlivemcp/judge/jev.py:138`, `src/abletonlivemcp/judge/__init__.py:84`.
- **CI uses ordinary push/pull_request tests rather than a privileged pull_request_target execution path.** Its declared matrix covers Linux/Windows and Python 3.10/3.13. This describes configuration, not fresh passing results: `.github/workflows/ci.yml:3`, `.github/workflows/ci.yml:14`, `.github/workflows/ci.yml:21`.
