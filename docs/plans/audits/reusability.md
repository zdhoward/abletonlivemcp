# Reusability audit: can a stranger install, run and extend AbletonLiveMCP?

Date: 2026-11-10. Status: audit complete; no fixes implemented. Inspected checkout HEAD: `eda269e`.

## Release assessment and evidence limits

**A stranger cannot currently complete a normal packaged installation using the repository's instructions.** The installer depends on files outside the wheel, and the README provides neither a user installation procedure nor MCP client configuration. The underlying separation between Live's stdlib-only Remote Script, the Python MCP server, and role adapters is a useful foundation; it needs distribution and onboarding work before a public v1.

The minimum honest support claim is **Live 12.2+ as the intended target, Windows Live 12.2 as historically exercised, macOS unverified, Live 11 unsupported**. The corrected decision is explicit in `docs/vision.md:42`; the historical Windows checks are in `HANDOFF.md:11-18`. Those historical claims are not fresh verification.

Method: read the requested product, source, installer, Remote Script, scripts, tests and CI files. Ran one collection-only check with bytecode, pytest caching and third-party plugin autoload disabled: **332 tests collected, exit 0**, under local Python **3.13.1**. Installed metadata reports `mcp 2.3.0`, requiring Python `>=3.10`, consistent with the project's floor. Ran a few in-memory, socket-free checks of preference and inventory behavior. Did not execute test bodies, build/install a distribution, access port 9877, invoke Live scripts, read research-note contents, change settings, or contact a paid service. Therefore collection health is established; current test pass/fail, fresh install success and macOS/Live compatibility are not established. Only this report was created.

Repository-relative `file:line` citations refer to the inspected files. Missing-document findings cite the existing document or configuration that would need the material. In-memory reproductions below establish Python behavior, not actual Live browser layouts.

Severity means impact on a public release: **blocker** prevents the advertised basic install; **high** prevents a major workflow or reliable operation for a meaningful user group; **medium** causes avoidable failure or misunderstanding; **low** is release polish or an expansion that can wait.

## Findings

### R01 — Packaged installs do not contain the installer's Remote Script source

- **Severity:** blocker.
- **Evidence:** `pyproject.toml:22-24`, `pyproject.toml:30-34`; `src/abletonlivemcp/install.py:12-14`, `src/abletonlivemcp/install.py:23`; checkout-only installer test at `tests/test_client_server_install.py:58-65`.
- **Stranger's problem:** pip, pipx and uvx normally execute an installed wheel. That wheel selects only `src/abletonlivemcp`, leaving out `remote_script/AbletonLiveMCP`. The installer nevertheless walks two parents above its module. In a Windows wheel layout this resolves to `<venv>/Lib/remote_script/AbletonLiveMCP`, not packaged resources; the equivalent macOS site-packages layout also has no selected source there. Copying fails with an uncaught filesystem error. A non-editable install from a checkout has the same issue. The editable developer test conceals it.
- **Smallest fix:** include the three Remote Script files as package data, locate them through package resources, and exercise the installer from an installed wheel outside the checkout. Do not include `knowledge/` to solve this.
- **Verdict:** **WORTH-DOING-FOR-V1** — both processes must be distributable together for any standard install path.

### R02 — A failed reinstall can delete the existing working Remote Script

- **Severity:** high.
- **Evidence:** `src/abletonlivemcp/install.py:17-23`; reinstall test at `tests/test_client_server_install.py:65` covers success only.
- **Stranger's problem:** upgrading removes `Remote Scripts/AbletonLiveMCP` before confirming the replacement source exists or can be copied. R01 therefore becomes destructive to a previous installation. Read/permission/disk failures can also leave no working script, with no rollback or recovery advice.
- **Smallest fix:** verify the bundled source first, copy to a sibling temporary directory, then replace with recovery on failure; convert filesystem failures to an actionable installer message. Tell users how to restore/reinstall and restart Live.
- **Verdict:** **WORTH-DOING-FOR-V1** — a routine upgrade must preserve a working install when replacement fails.

### R03 — The README has no stranger installation or Remote Script activation path

- **Severity:** high.
- **Evidence:** `README.md:8`, `README.md:29-36`; `src/abletonlivemcp/install.py:17-31`; the installer command currently appears in `HANDOFF.md:6`.
- **Stranger's problem:** the only README command is an editable development install. The installer does **not** discover a User Library: it requires one positional path and checks only for a `Presets` subdirectory. No argument yields `usage: python -m abletonlivemcp.install <path to User Library>`; an invalid path yields `<path> does not look like an Ableton User Library`. Neither explains where to find the real library, which may be relocated, or how to enable the script. A successful copy alone does not enable the control surface.
- **Smallest fix:** document Windows and macOS paths, selecting the actual User Library in Live's Library settings, the quoted installer command, its `Remote Scripts/AbletonLiveMCP` destination, restarting Live, and selecting **AbletonLiveMCP** in the control-surface settings with MIDI input/output set to None. Common starting locations are Windows `%USERPROFILE%\Documents\Ableton\User Library` and macOS `~/Music/Ableton/User Library`; Live's configured location wins, including redirected Documents. Explain missing-library and permissions errors. Explicit-path installation is sufficient; automatic discovery is optional.
- **Verdict:** **WORTH-DOING-FOR-V1** — users need one complete path from download to enabled bridge on each advertised OS.

### R04 — No copy-paste MCP client configuration or supported launch recipe

- **Severity:** high.
- **Evidence:** `README.md:29-36`; CLI entry points at `pyproject.toml:22-24`; stdio startup at `src/abletonlivemcp/server.py:381-382`; internal client example at `scripts/stdio_smoke.py:12-15`.
- **Stranger's problem:** Claude Desktop, Claude Code and Cursor are named or implied, but no user config exists. A GUI client may not inherit the terminal PATH. Users cannot tell which executable to put in `command`, whether it needs a working directory, how Windows JSON backslashes are escaped, or how the separate installer is run. `uvx abletonlivemcp-install` also needs explicit package selection because that executable name differs from the distribution name. Publication availability was not checked; package-name-only commands should not imply an existing PyPI release.
- **Smallest fix:** choose and verify one primary release install recipe, plus a checkout/virtualenv alternative. After R01, cover `pipx install abletonlivemcp` followed by `abletonlivemcp-install "<library>"`, or version-pinned `uvx --from abletonlivemcp==<release> abletonlivemcp-install "<library>"` and `uvx --from abletonlivemcp==<same-release> abletonlivemcp`. For pip, use a venv and its explicit interpreter/executable. Supply valid Claude Desktop `mcpServers` JSON, the Claude Code `mcp add` command, Cursor's `.cursor/mcp.json` example, OS-specific config locations, and a generic stdio `command`/`args`/`env` recipe. Verify each client schema; use absolute executable paths where GUI PATH is unreliable.
- **Verdict:** **WORTH-DOING-FOR-V1** — a running Python process is useful only once the user's actual MCP client can launch it.

### R05 — Support boundaries are buried; macOS and Live 11 are not established targets

- **Severity:** high.
- **Evidence:** corrected target at `docs/vision.md:41-42`; `CONTRIBUTING.md:18`; `.github/workflows/ci.yml:14-23`; `remote_script/AbletonLiveMCP/core.py:5`; capability probing at `remote_script/AbletonLiveMCP/handlers.py:513-536`.
- **Stranger's problem:** Live 11 users receive no prominent unsupported-version notice. Early Live 12, Live editions with fewer stock effects, localized installations and macOS users have no compatibility table. The Remote Script runs Live's embedded Python, independently of the host Python `>=3.10`; changing a host interpreter cannot fix an embedded-runtime problem. Capability probing is good but does not prove any specific version/edition/OS works.
- **Smallest fix:** put the Python floor, Live 12.2+ intended target, Live 11 exclusion, edition/device requirements and verified OS/version combinations in the quickstart. If macOS is advertised as supported at v1, complete one actual clean macOS install/read/stock-chain acceptance pass. Otherwise label it experimental. Do not claim all Live 12 releases work merely because 12.2 did.
- **Verdict:** **WORTH-DOING-FOR-V1** — an explicit support boundary prevents strangers debugging combinations the project never promised.

### R06 — There is no server/Remote Script compatibility check or upgrade contract

- **Severity:** high.
- **Evidence:** `remote_script/AbletonLiveMCP/core.py:13`; `remote_script/AbletonLiveMCP/handlers.py:145-150`, `remote_script/AbletonLiveMCP/handlers.py:505-507`; `src/abletonlivemcp/server.py:66-69`; `src/abletonlivemcp/bridge.py:28-53`; batch operations at `src/abletonlivemcp/chain.py:155-168`.
- **Stranger's problem:** `hello` returns protocol `1`, Live version and capabilities, but no script build/version or method inventory. The server returns that handshake without validating it and can send writes without handshaking. Updating pipx/uvx/pip leaves the copied script unchanged. An older script can accept a device load and then reject a newer batch-setting method, leaving a partial chain. An unpinned uvx server may upgrade independently of Live's script.
- **Smallest fix:** expose a script/protocol revision and required capabilities, check compatibility before live operations, and fail with reinstall/restart instructions before writes. Document upgrading both halves to the same supported release, retaining preferences, restarting Live and the client, and rechecking `live_hello`. A small protocol compatibility rule is enough; exact package-version equality is unnecessary for compatible releases.
- **Verdict:** **WORTH-DOING-FOR-V1** — the bridge is a separately installed component and must not silently drift from the server.

### R07 — Preferences exist but users cannot discover or confidently create them

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/preferences.py:1-8`, `src/abletonlivemcp/preferences.py:18-37`; `src/abletonlivemcp/server.py:238-253`; `docs/data/example-preferences.json:1-5`; `README.md:18-36`.
- **Stranger's problem:** the default is `%USERPROFILE%\.abletonlivemcp\preferences.json` on Windows and `~/.abletonlivemcp/preferences.json` on macOS, with `ABLETONLIVEMCP_PREFS` as an override. This is documented only in source. No file/directory is created. Missing files mean stock defaults; malformed JSON or a non-object/list-of-strings format causes a tool-visible `ValueError` containing the path. Users are not told that preferences are reread on planning, call-level preferences replace each matching role's list, or that Pro-Q 3 and Pro-R in the sample are skipped as opaque.
- **Smallest fix:** add a README preferences section with folder creation commands, valid JSON using canonical adapter names, all four roles, missing/bad-file behavior, merge/reload behavior, and MCP-client `env` examples. Explain why the sample's opaque devices fall back to stock. Include the effective path/preferences in an existing diagnostic response if practical.
- **Verdict:** **WORTH-DOING-FOR-V1** — per-user selection is a central differentiator and already implemented.

### R08 — Preference typos, inline shape errors and path expansion are inconsistent

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/preferences.py:19-20`, `src/abletonlivemcp/preferences.py:32-37`; `src/abletonlivemcp/server.py:239`; `src/abletonlivemcp/resolve.py:84-92`.
- **Stranger's problem:** `{"compressorr":["Pro-C 2"]}` passes validation and is unused. A call-level `{"compressor":"Pro-C 2"}` is accepted by the broad `dict` schema, then iterated as seven character preferences. Other inline values can raise a generic hidden exception. An override like `~/.abletonlivemcp/preferences.json` is not expanded by `Path`, and relative overrides depend on the client's working directory; a wrong nonexistent override silently becomes stock defaults. These behaviors were confirmed with in-memory inputs without Live.
- **Smallest fix:** share one role-to-list validator for file and inline preferences, reject unknown roles with allowed names, and require an absolute override or explicitly expand/normalize supported path syntax. Warn distinctly when an explicitly configured file is missing; retain stock defaults for an absent default file.
- **Verdict:** **WORTH-DOING-FOR-V1** — otherwise a user's valid-looking personalization can fail silently.

### R09 — Recognized browser aliases are rejected in the preferences list

- **Severity:** medium.
- **Evidence:** vendor/suffix normalization at `src/abletonlivemcp/resolve.py:23-32`; preference lookup at `src/abletonlivemcp/resolve.py:86-90`; canonical entries at `src/abletonlivemcp/adapters.py:57`, `src/abletonlivemcp/adapters.py:94-105`.
- **Stranger's problem:** a user copies `FabFilter Pro-C 2` or `ValhallaVintageVerb_x64` from Live into preferences. Inventory matching understands these aliases, but adapter selection accepts only lowercase equality with `Pro-C 2` or `ValhallaVintageVerb`. The preference is reported as having no adapter and stock wins. The vendor-prefixed compressor case was reproduced in memory.
- **Smallest fix:** apply the same unambiguous normalization to preference lookup and browser matching, preserving version distinctions. Until then, list the canonical accepted names directly in user documentation.
- **Verdict:** **WORTH-DOING-FOR-V1** — copying a plugin's displayed name should select its existing adapter.

### R10 — Stock fallback assumes flat, English-named browser entries and available devices

- **Severity:** high.
- **Evidence:** `src/abletonlivemcp/adapters.py:54-92`; `src/abletonlivemcp/resolve.py:65-70`, `src/abletonlivemcp/resolve.py:133-145`; `src/abletonlivemcp/chain.py:252-270`; nested browser fixture at `tests/test_handlers.py:75-82`, `tests/test_handlers.py:106-111`; list truncation at `remote_script/AbletonLiveMCP/handlers.py:185-188`.
- **Stranger's problem:** stock inventory examines only the first browser level, ignores `truncated`, and matches literal device names. Chain building independently repeats that assumption and constructs `[device_name]`. In a nested layout, a present Compressor is reported unavailable; an in-memory nested listing confirms the behavior. Users whose edition lacks EQ Eight or another required effect cannot build the full preset. Localized browser/parameter naming is an unverified compatibility risk, not a demonstrated failure on a real localized Live installation.
- **Smallest fix:** resolve stock effects to actual loadable browser paths with the existing bounded browser machinery and preserve those paths through the build. Report missing edition/device requirements clearly. For v1, explicitly state an English-language/device support boundary unless other languages are validated; a complete localization layer can wait.
- **Verdict:** **WORTH-DOING-FOR-V1** — stock fallback is the core promise for users without the owner's plugins.

### R11 — Large plugin inventories can be misreported as “not installed”

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/resolve.py:73-80`, `src/abletonlivemcp/resolve.py:137-140`; `remote_script/AbletonLiveMCP/handlers.py:24`, `remote_script/AbletonLiveMCP/handlers.py:195-209`.
- **Stranger's problem:** plugin lookup takes the first bounded search of 15 hits, then demands an exact normalized name. It ignores `budget_exhausted` and has no indication that the hit limit stopped traversal. Matching folders, similarly named presets or another branch can consume the result window before a desired loadable device is reached. It can also choose a VST2 before ever discovering the installed VST3 it claims to prefer. An exhausted empty response is treated as absence in memory. This matters more as installed-plugin coverage expands.
- **Smallest fix:** preserve “search incomplete” separately from “not installed”, narrow searches to loadable exact candidates, and retain a bounded way to continue or select an explicit browser path. Keep the main-thread budget rather than raising it without limit.
- **Verdict:** **WORTH-DOING-FOR-V1** — false absence undermines per-user plugin selection even with an existing adapter.

### R12 — Installed and statically “full” does not mean this user's plugin is configurable

- **Severity:** high.
- **Evidence:** access claims at `src/abletonlivemcp/adapters.py:11-21`; VintageVerb mapping at `src/abletonlivemcp/adapters.py:94-104`; intent skipping and selection at `src/abletonlivemcp/resolve.py:95-112`, `src/abletonlivemcp/resolve.py:132-159`; success calculation at `src/abletonlivemcp/chain.py:277-288`; demonstrated dropped intent at `tests/test_resolve.py:109-135`.
- **Stranger's problem:** an installed plugin is selected using a global access label; the planner never reads that user's exposed parameter set. Parameter exposure can differ by plugin version, format and Live configuration. If the selected adapter drops an unmapped intent, the plan notes it, but the build can still report `ok: true` for the retained settings—even zero retained settings. VintageVerb is labeled full although predelay is unmapped and decay levels are explicitly guesses. Unlike the preferences module's promise, failure to configure a selected plugin does not automatically try stock afterward.
- **Smallest fix:** distinguish successful writes from complete intent fulfillment; surface unsupported/unverified intent prominently in the top-level result and preview. Document static access labels as measurements from a particular setup. Explain Live's plugin Configure workflow and verify exposed parameters in a disposable Set before using a contributed adapter. Prefer a refusal or explicit partial result over promising automatic fallback after a failed, already-mutating build.
- **Verdict:** **WORTH-DOING-FOR-V1** — users must be able to tell whether their requested musical settings were actually applied.

### R13 — Adding a user's plugin requires editing Python, with no contributor walkthrough

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/adapters.py:7-9`, `src/abletonlivemcp/adapters.py:32-44`, `src/abletonlivemcp/adapters.py:54-113`; unknown adapters at `src/abletonlivemcp/resolve.py:84-92`; `scripts/live_probe_plugins.py:1-4`, `scripts/live_probe_plugins.py:14-16`, `scripts/live_probe_plugins.py:30-43`; `CONTRIBUTING.md:20-26`.
- **Stranger's problem:** preferences are data, but support for a new plugin is a Python `Adapter` entry in the installed source registry. Merely listing an installed VST in JSON cannot map it. The only authoring guide is a source docstring; the named probe creates a new track and loads plugins, rather than merely inspecting a plugin already on a track. It writes a shared checkout-relative JSON file. No walkthrough covers choosing a role, parameter names, units, setup switches, raw values, partial exposure, plugin version/format, or verifying readback before contributing. Arbitrary devices can already be loaded through `live_load_item`; arbitrary role mapping is a separate capability.
- **Smallest fix:** add one documented adapter contribution example and a small checklist: disposable Set, explicit plugin name, captured exposed parameter data, role/intents, honest limitations, one focused mapping check, actual Live version/format/readback, and PR. Explain the distinction between loading a plugin, configuring it, and resolving a musical role. Let probes take an output path rather than overwriting shared evidence by default.
- **Verdict:** **WORTH-DOING-FOR-V1** — a stranger can extend a small Python registry if the contract and evidence requirements are clear.

### R14 — A universal user-supplied adapter registry is future expansion

- **Severity:** low.
- **Evidence:** current four-role/static registry at `src/abletonlivemcp/adapters.py:54-121`; role validation at `src/abletonlivemcp/resolve.py:123-127`; per-user data boundary at `src/abletonlivemcp/preferences.py:23-37`.
- **Stranger's problem:** a pipx/uvx user cannot persist a completely new adapter through configuration alone, and an instrument, delay or limiter cannot be introduced as a new role by preferences. Editing site-packages is fragile across upgrades. Discovering all installed VST names does not discover each plugin's musical parameter semantics or calibrate its controls.
- **Smallest fix:** for v1, document the supported registry and contribution path from R13. Later add a versioned user-data adapter schema and loader only when recurring contributions show what must be configurable; reserve Python for genuinely procedural mappings.
- **Verdict:** **DEFER** — automatic support for every installed plugin is a substantial product expansion, not a prerequisite for an honest four-role v1.

### R15 — First-run connection errors are useful, but the recovery steps are absent

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/bridge.py:40-45`; error forwarding at `src/abletonlivemcp/server.py:27-46`; bridge startup logging at `remote_script/AbletonLiveMCP/__init__.py:23-28`; no troubleshooting section in `README.md:29-36`.
- **Stranger's problem:** the server can launch and list tools while Live is closed. The first live tool reports `Unreachable: cannot reach Live bridge at 127.0.0.1:9877 (...) Is Live open with the AbletonLiveMCP control surface enabled?` This is actionable and is forwarded as a tool error, not a server crash. But it conflates Live closed, script not enabled, script startup failure and port conflict. Startup failures are only written to Live's log, whose location the docs never give.
- **Smallest fix:** make `live_hello` the first success criterion and provide a symptom-to-action checklist: actual User Library, folder nesting, restart, selected control surface, one active Live instance, then log inspection. Give typical log locations: Windows `%APPDATA%\Ableton\Live <version>\Preferences\Log.txt`; macOS `~/Library/Preferences/Ableton/Live <version>/Log.txt`. Separate MCP launch/PATH errors from bridge reachability errors. Keep offline tools usable without Live.
- **Verdict:** **WORTH-DOING-FOR-V1** — the existing good error needs a documented route to recovery.

### R16 — The fixed loopback port needs a documented single-instance boundary

- **Severity:** medium.
- **Evidence:** `src/abletonlivemcp/bridge.py:10-24`; fixed server client at `src/abletonlivemcp/server.py:24`; Remote Script port at `remote_script/AbletonLiveMCP/__init__.py:13-28`; bind at `remote_script/AbletonLiveMCP/core.py:43-47`.
- **Stranger's problem:** the production MCP entry point and copied script both use 9877, with no supported user configuration. Two Live processes or another program occupying the port cause one script to fail startup; a client cannot identify the intended Live instance. Multiple MCP clients can use one bridge, so this is not a reason to require a port per client.
- **Smallest fix:** document one active Live bridge, the port and the log symptom. Add configurable matching ports only if supporting multiple Live instances or collisions is a v1 requirement; keep loopback binding fixed.
- **Verdict:** **WORTH-DOING-FOR-V1** — documenting the boundary is cheap; multi-instance routing can wait.

### R17 — Ordinary offline and optional-backend failures lose their useful MCP messages

- **Severity:** medium.
- **Evidence:** exception whitelist at `src/abletonlivemcp/server.py:27-46`; unwrapped offline call at `src/abletonlivemcp/server.py:325-327`; `src/abletonlivemcp/als/reader.py:25-26`, `src/abletonlivemcp/als/reader.py:214-224`; `src/abletonlivemcp/judge/__init__.py:48-49`; backend use at `src/abletonlivemcp/server.py:357-378`.
- **Stranger's problem:** opening a missing/corrupt Set raises `AlsError`, and a failed Jev request raises `JudgeError`. Neither is caught by `_tool`, so these expected user/environment failures take the generic MCP crash path described in the wrapper's own docstring. The user loses the specific file/backend recovery information even though validation and unreachable-Live errors retain it.
- **Smallest fix:** translate the two domain exceptions into `ToolFailure` at the tool boundary, preserving useful messages and existing credential redaction. Keep unexpected programming errors separate.
- **Verdict:** **WORTH-DOING-FOR-V1** — users need to distinguish a bad path or optional service failure from a broken server.

### R18 — Safety documentation omits partial writes, retry behavior and local access scope

- **Severity:** high.
- **Evidence:** `SECURITY.md:3-6`; unauthenticated request dispatch at `remote_script/AbletonLiveMCP/core.py:95-133`; timeout semantics at `src/abletonlivemcp/bridge.py:49-52`; staged mutations at `src/abletonlivemcp/chain.py:264-288`; arbitrary offline paths at `src/abletonlivemcp/server.py:325-340`; filesystem traversal at `src/abletonlivemcp/als/usage.py:35-44`.
- **Stranger's problem:** chain builds append devices and write parameters incrementally, with no rollback. Retrying can append duplicates. A timeout after a write begins means the action may have happened; the bridge deliberately never retries. Transport/clip tools can produce audio, but there is no user-facing disposable-Set/listening-level guidance. Loopback is a useful network boundary, not authentication against other local processes. SECURITY says file tools stay in configured directories, yet no such roots or enforcement exist for `.als` reads/scans; those tools can read paths accessible to the server process.
- **Smallest fix:** add a short safety section: save a copy/use a disposable Set, lower monitoring before playback, preview role plans, inspect partial results, and inspect Live before retrying timed-out writes. Document append/no-rollback behavior and the local-process trust model. Make the file-scope policy truthful: document explicit supplied paths and OS permissions, or implement a small configured-root restriction if that promise is retained. Do not expose the bridge to a network.
- **Verdict:** **WORTH-DOING-FOR-V1** — strangers need accurate expectations before giving an assistant write access to an open Set.

### R19 — An inherited API key can silently enable external, potentially paid classification

- **Severity:** high.
- **Evidence:** `CONTRIBUTING.md:25`; default auto selection at `src/abletonlivemcp/judge/__init__.py:77-95`; payload and HTTP endpoint at `src/abletonlivemcp/judge/jev.py:4-8`, `src/abletonlivemcp/judge/jev.py:27-49`, `src/abletonlivemcp/judge/jev.py:117-139`; disclosure tool at `src/abletonlivemcp/server.py:344-353`.
- **Stranger's problem:** an MCP client inheriting `OPENROUTER_API_KEY` can use Jev without installing the optional SDK extra or explicitly selecting an external backend. Classifying samples sends filenames and the last two folder names; plugin classification sends name/format. A call can classify up to 200 items. This is intentional service use rather than telemetry, but the README never discloses it and CONTRIBUTING's blanket “no network calls home” gives incomplete expectations.
- **Smallest fix:** document exact outbound data, backend selection, optional costs and `ABLETONLIVEMCP_JUDGE=rules` in client env examples. For a predictable v1, default to local rules and require an explicit Jev opt-in rather than treating any inherited key as intent. Keep `judge_status` as a verification step for users who enable it.
- **Verdict:** **WORTH-DOING-FOR-V1** — external data transfer and account usage must be deliberate and discoverable.

### R20 — The fake-Live suite has redundant matrices rather than proportional feature checks

- **Severity:** medium.
- **Evidence:** owner guidance at `tasks/lessons.md:12-14`; overlapping socket setup at `tests/test_bridge.py:51-63` and `tests/test_client_server_install.py:18-29`; fake Live implementation at `tests/test_handlers_clips.py:14-105`; index matrices at `tests/test_handlers_clips.py:177-195`; duplicated wrapper checks at `tests/test_handlers_clips.py:387-421` and `tests/test_server_settle.py:13-34`; repeated option ordering at `tests/test_chain.py:206-219`, `tests/test_chain.py:310-315`.
- **Stranger's problem:** 114 test functions expand to 332 collected cases; **190** are in fake clip/session tests. The six-method × two-index-field × seven-invalid-value clip matrix alone creates **84** cases exercising shared `_track`/`_scene` guards. Scene-index matrices repeat the pattern. Broad forwarding assertions and multiple fakes add maintenance work without establishing actual Live timing, browser behavior or plugin exposure. However, algorithm and safety contract tests remain valuable: fakes themselves are not the defect.
- **Smallest fix:** collapse shared validation matrices into a compact representative guard table, retain one scenario per thin feature, combine duplicate registration/forwarding checks, and remove duplicated synthetic success coverage once a recorded real-Live acceptance scenario covers it. Preserve pre-write validation, cancellation, bounds, unit handling and honest partial-result checks. See the minimum suite below.
- **Verdict:** **WORTH-DOING-FOR-V1** — prune duplication before expanding the suite, so contribution cost reflects actual risk.

### R21 — The default suite depends on research notes deliberately excluded from packages

- **Severity:** high.
- **Evidence:** `tests/test_knowledge.py:6-15`; correct nonshipping policy at `README.md:20-23`; exclusion at `pyproject.toml:33-34`; optional registration at `src/abletonlivemcp/server.py:51-53`; folder availability at `src/abletonlivemcp/knowledge.py:35-43`.
- **Stranger's problem:** the test directly reads the real development knowledge folder, requires named pages, a particular search winner and literal `-14 LUFS` prose. A source distribution is configured to exclude that folder, so its included tests cannot be independently run successfully without separate notes. In the checkout, unrelated research edits can change search ranking and break product tests. This is not a reason to ship the notes.
- **Smallest fix:** replace content-dependent assertions with one temporary synthetic Markdown fixture and a normal-install check that knowledge tools are absent. Keep any real-corpus search check as an explicitly optional developer check, outside the default suite.
- **Verdict:** **WORTH-DOING-FOR-V1** — package tests must stand alone while `knowledge/` remains a development resource.

### R22 — CI verifies editable source, not the artifact a stranger installs, and omits macOS

- **Severity:** high.
- **Evidence:** entire configured matrix and commands at `.github/workflows/ci.yml:14-23`; source-path injection at `tests/test_client_server_install.py:9`; editable install at `CONTRIBUTING.md:12-18`; wheel/sdist selections at `pyproject.toml:30-34`.
- **Stranger's problem:** Linux/Windows Python 3.10 and 3.13 coverage is a good start, but it can be green while the wheel installer is unusable. CI does not build/install a wheel in a clean environment, run from outside the checkout, inspect archive exclusions, initialize MCP over stdio, or validate a macOS path. The historical “244 passed” in HANDOFF is stale relative to 332 collected now and is not a current CI result.
- **Smallest fix:** add one compact artifact acceptance job: build wheel and sdist, inspect contents for the bundled script and absence of `knowledge/`/`research/`, install the wheel outside the repo, install its Remote Script into a temporary fake library, and initialize/list MCP tools without Live. Add a macOS job if support is claimed. Retain a practical minimum-Python/current-supported-Python matrix; testing every Python minor is unnecessary. A manual actual-Live gate remains separate.
- **Verdict:** **WORTH-DOING-FOR-V1** — this catches the main stranger failure more directly than additional fake API cases.

### R23 — Real-Live smoke scripts are developer probes, not reliable acceptance commands

- **Severity:** medium.
- **Evidence:** private sample paths and printed results at `scripts/stdio_smoke.py:9-25`; fixed track 4 at `scripts/live_probe.py:27-29`; caught failures at `scripts/live_write_test.py:10-17`; printed chain failures at `scripts/live_chain_test.py:24-36`, `scripts/live_chain_test.py:50-52`; optional knowledge assumed at `scripts/stdio_error_smoke.py:12-15`.
- **Stranger's problem:** a contributor following the real-Live approach hits `S:/AbletonMCP/projects`, assumes track 4 exists, or receives a process exit code of zero despite printed `FAIL`/`REFUSED`/`ok=False`. The stdio error check includes a knowledge tool that a normal install intentionally lacks. Probe scripts also create unsaved tracks/scenes; a newcomer needs a disposable Set, not the owner's named sandbox. No owner filesystem path was found in production defaults; the coupling is in developer scripts/handoff.
- **Smallest fix:** parameterize project/probe paths, make failed required checks return nonzero, treat optional tools conditionally, and publish one short manual acceptance checklist with actual readbacks and OS/Live/plugin versions. Label which scripts read, mutate or contact a service. Keep these scripts out of a routine first-run path.
- **Verdict:** **WORTH-DOING-FOR-V1** — real-Live evidence should be repeatable by someone without the owner's files.

### R24 — Release version, tag history and user-facing status disagree

- **Severity:** medium.
- **Evidence:** `pyproject.toml:7`, `src/abletonlivemcp/__init__.py:3` both say `0.0.1`; `HANDOFF.md:24` describes tag `v0.1.0`, corroborated by local tag listing; `README.md:8` says nothing is usable; `HANDOFF.md:6`, `HANDOFF.md:34` have obsolete tool/test counts. No tracked root CHANGELOG was found; the release/contribution version guidance is `CONTRIBUTING.md:28-30`.
- **Stranger's problem:** users cannot reliably map an installed version to the tag, bridge requirements or capabilities. The README hides completed functionality while HANDOFF mixes old verification, owner paths and outdated next steps. There is no concise upgrade/change history or `--version` CLI path (`src/abletonlivemcp/server.py:381-382`).
- **Smallest fix:** use one authoritative package version, reconcile the next release's tag and metadata without rewriting published history, add a brief CHANGELOG with bridge reinstall notes, and replace the README status with an accurate supported-feature summary. Expose the installed version in diagnostics. Refresh the handoff when implementation work resumes; it is not an installation manual.
- **Verdict:** **WORTH-DOING-FOR-V1** — users and maintainers need to identify the exact component versions they are debugging.

### R25 — PyPI metadata lacks discovery links and a clear tested-support declaration

- **Severity:** low.
- **Evidence:** `pyproject.toml:5-20`; no `[project.urls]` section in `pyproject.toml`; existing license at `LICENSE:1-21`.
- **Stranger's problem:** the package has a valid MIT license, name, description, Python floor and scripts, but no repository/documentation/issue links in package metadata. Pre-alpha status and the aspirational racks/macros description need reconciliation with the actual v1 scope. No publishing workflow or successful public PyPI release is established by the inspected repository; neither is required just to publish code for manual installation.
- **Smallest fix:** add repository, issues, docs and changelog URLs, and set development-status/support classifiers honestly for the released scope. Follow a short manual release checklist for the built artifacts; do not build an automated publishing system solely for v1.
- **Verdict:** **WORTH-DOING-FOR-V1** — small metadata changes make an otherwise unfamiliar PyPI package traceable and supportable.

### R26 — Tool reference and a safe first workflow are missing from the docs

- **Severity:** medium.
- **Evidence:** tool definitions span `src/abletonlivemcp/server.py:66-378`; optional tools at `src/abletonlivemcp/server.py:278-307`; documented limits in `src/abletonlivemcp/server.py:198-206`, `src/abletonlivemcp/server.py:225-231`; stage bound at `src/abletonlivemcp/chain.py:16`; `README.md:10-27` lists goals and research rather than current tool usage.
- **Stranger's problem:** there are **35 ordinary tools plus 3 optional knowledge tools**, not always 38. There is no user guide distinguishing offline reads, Live reads and mutations, no explained zero-based indices, no role-chain examples with unit-bearing intent, and no discussion of `ok`, `problems`, `skipped`, `truncated` or incomplete search. A user cannot infer which roadmap goals—racks, macros, plugin tagging—are actually implemented. Knowledge prose must remain optional development data and should not be presented as an included product feature.
- **Smallest fix:** add a compact tool table derived from registered names/docstrings with read/write status, examples and key limits (12 build stages, 2000 notes, 200 classification items). Demonstrate `live_hello` → track listing → read-only `live_plan_chain` → reviewed build on a disposable track → inspect actual values. State unimplemented goals plainly. Do not promise a universal VST catalog or rack/macro builder on the basis of the vision document.
- **Verdict:** **WORTH-DOING-FOR-V1** — users need to understand what the tool can safely do today.

### R27 — Issue templates exist but omit the diagnostic fields this architecture needs

- **Severity:** low.
- **Evidence:** `.github/ISSUE_TEMPLATE/bug_report.md:11-17`; `.github/PULL_REQUEST_TEMPLATE.md:7-10`; `.github/ISSUE_TEMPLATE/feature_request.md:7-13`.
- **Stranger's problem:** the existing templates already request OS, Live version/edition, server version, MCP client and logs. They do not request Python/install method, script/protocol version, `live_hello`, effective preference location or plugin version/format/exposure. A server/script mismatch and a missing adapter can look similar. Logs and probe output may disclose personal paths or project names.
- **Smallest fix:** add a short optional diagnostic block for these fields and explicit redaction guidance. Change the PR test checkbox to ask for proportionate evidence rather than implying every change needs another fake test. Keep the current lightweight Markdown templates.
- **Verdict:** **WORTH-DOING-FOR-V1** — a few fields reduce back-and-forth without introducing process overhead.

### R28 — Conduct/security reporting routes are incomplete, but no license blocker exists

- **Severity:** low.
- **Evidence:** `CODE_OF_CONDUCT.md:3-6`; `SECURITY.md:8-9`; MIT grant and disclaimer at `LICENSE:5-21`; contribution entry point at `CONTRIBUTING.md:5-8`.
- **Stranger's problem:** the project has LICENSE, CONTRIBUTING, conduct, security, issue and PR templates. The conduct document directs users to a security “contact”, while SECURITY only names GitHub's vulnerability-report feature once public. There is no conduct contact or pre-public security route, and enabling private vulnerability reporting is an account/release setting not verified here.
- **Smallest fix:** when the owner prepares the public release, choose an actual private reporting route and distinguish security from conduct reports. Keep the existing MIT license; no CLA, DCO, legal-policy expansion or license rewrite is justified by this audit.
- **Verdict:** **DEFER** — coordinate the contact/account setting with the public-release decision; it does not block local installation or adapter contributions.

### R29 — Vocal presets and uncalibrated levels are taste choices, already labeled in code

- **Severity:** low.
- **Evidence:** `src/abletonlivemcp/chain_presets.py:1-6`, `src/abletonlivemcp/chain_presets.py:16-68`; VintageVerb guesses at `src/abletonlivemcp/adapters.py:99-104`; resolver caveats at `src/abletonlivemcp/resolve.py:49-54`; exposed preset disclaimer at `src/abletonlivemcp/server.py:311-314`.
- **Stranger's problem:** the two vocal chains encode particular thresholds, EQ points, saturation and reverb amounts. VintageVerb decay's short/medium/long values are guesses rather than measured seconds. These are not owner filesystem dependencies, and defaults do not force third-party plugins when stock devices are available. The source and tool descriptions already call the chains starting points; a stranger should not mistake them for artist-specific emulations or presets tuned to their recording level.
- **Smallest fix:** carry the existing caveats into the tool reference and R12's completeness reporting. Let callers pass custom stages, as already supported. Calibrate additional plugins or add a user preset file only after actual demand and measurements.
- **Verdict:** **DEFER** — rebuilding the preset system is unnecessary for v1; preserve the existing honest caveats while fixing partial-success reporting.

## Minimum test and acceptance evidence worth keeping

The observed collection result is **332 collected, not 332 passed**. `HANDOFF.md:34` is a historical result only. No test execution or actual Live verification was performed during this audit.

Keep a compact suite around contracts the project owns, rather than maintaining a second implementation of Live:

1. **Artifact and launch contract:** one built-wheel installation/Remote Script copy/reinstall-failure scenario outside the repo, with MCP stdio initialize/list-tools and no Live connection. Check that wheel and sdist omit `knowledge/` and `research/`. This replaces confidence inferred only from editable installation (`tests/test_client_server_install.py:58-65`; `.github/workflows/ci.yml:21-23`).
2. **Bridge safety:** one actual ephemeral-loopback roundtrip for framing/ID/error propagation, one cancelled-before-start case, and an honest after-start timeout case. Keep loopback binding coverage. These test the project's queue/protocol, not Live (`tests/test_bridge.py:75-128`; `remote_script/AbletonLiveMCP/core.py:126-132`). An ephemeral test port is distinct from the real bridge; no such socket tests ran here.
3. **Thin Live guards:** one positive scenario per supported feature, plus a small table for shared index/numeric/boolean/nonfinite handling. Retain occupied-slot refusal, all-notes-validated-before-write and note-read bounds. Reduce the 84-case clip-index cross product and repeated scene-index permutations (`tests/test_handlers_clips.py:152-195`, `tests/test_handlers_clips.py:198-225`, `tests/test_handlers_clips.py:284-322`).
4. **Resolver and preferences:** one table covering stock defaults, preferred installed device, missing/opaque/unknown adapter, canonical aliases, incomplete inventory and unsupported intent; one file/inline preference validation scenario; one adapter-data consistency check. Avoid emulating plugin DSP (`tests/test_resolve.py:44-135`, `tests/test_resolve.py:173-203`; `tests/test_chain_tools.py:27-44`).
5. **Parameter solver:** retain meaningful unit conversion, nonlinear display inversion, option-before-number behavior, raw-value bounds and off-target readback. Use a small generic display stub; combine duplicate option-order/forwarding cases, and keep a coarse batching guard only if it protects Live responsiveness (`tests/test_chain.py:136-175`, `tests/test_chain.py:194-247`, `tests/test_chain.py:292-315`; `tests/test_server_settle.py:13-34`).
6. **Offline Set reader/scanner:** keep one representative nested synthetic Set, corrupt gzip/XML/entity/decompression guards, a drum-pad association case, and one aggregation/Backup-skip scenario. Synthetic parser fixtures test real project-owned logic; they are useful. Reduce the four-sampler × six-classification matrix where aliases use the same branch, but do not delete schema distinctions with real evidence (`tests/test_als.py:58-98`; `tests/test_als_scan.py:68-98`, `tests/test_als_scan.py:113-154`; `src/abletonlivemcp/als/reader.py:84-107`, `src/abletonlivemcp/als/reader.py:214-224`).
7. **Optional features:** keep one local-rule/explicit-backend selection and minimal-payload/redacted-error check with mocked HTTP; no paid calls in CI. Use a synthetic knowledge page and absence-of-tools check, never the changing research corpus. A semver-shape-only test can be folded into version-consistency metadata checks (`tests/test_judge.py:54-61`; `tests/test_judge_jev.py:21-29`, `tests/test_judge_jev.py:85-95`; `tests/test_knowledge.py:6-15`; `tests/test_smoke.py:4-6`).

Then require **one recorded real-Live acceptance pass per claimed OS/Live baseline**, using a disposable Set: install/activate, handshake/capabilities, browser discovery, a stock role chain with readbacks, a supported third-party preference if advertised, one MIDI clip/notes/transport scenario, and a refusal without mutation. Record exact OS, Live version/edition/language, plugin version/format and both component versions. The existing scripts provide starting points, but need R23's parameters and failure exits before serving as acceptance commands (`scripts/live_chain_test.py:19-51`; `scripts/live_clip_test.py:25-32`). This is proposed future verification, not authorization to contact the owner's Live during this audit.

## Ranked top 10 for a public v1

1. **R01 — Bundle and locate the Remote Script in installed artifacts.** Removes the basic installation blocker.
2. **R02 — Preserve the old script on failed reinstall.** Prevents an upgrade from destroying the working bridge.
3. **R03 — Publish the Windows/macOS install and activation procedure.** A stranger must reach an enabled control surface without reading HANDOFF.
4. **R04 — Supply verified client configs and one pinned launch recipe.** Makes installation usable from Claude Desktop, Claude Code, Cursor and generic stdio clients.
5. **R06 — Enforce protocol/capability compatibility and document two-component upgrades.** Refuses stale scripts before writes.
6. **R22 — Verify the built artifact outside the checkout.** Adds the most valuable release check; pair it with R21's research-independent tests.
7. **R05 — State and exercise the actual support boundary.** Include an actual macOS pass before claiming macOS support; explicitly exclude Live 11 for v1.
8. **R10 — Resolve actual stock browser paths and explain edition requirements.** Makes the fallback useful to users without the owner's plugins.
9. **R12 — Make incomplete intent/configurability visible.** Prevents successful writes being mistaken for a fully fulfilled chain request.
10. **R18 — Document mutation, timeout, local-access and recovery semantics.** Makes first use and failure recovery understandable. Fold R19's external-service opt-in/disclosure into the same onboarding pass.

The other WORTH-DOING items are small supporting work, especially preferences documentation/validation, the adapter walkthrough, actionable domain errors and version consistency. Universal plugin mapping, broad preset infrastructure, Live 11 support and a release-automation system are not prerequisites for this v1.

## Proposed stranger quickstart: the eight steps that must work

1. **Check compatibility.** Read the verified OS/Live/edition/language table and host Python floor. Live 11 is unsupported for v1; the host Python install and Live's embedded runtime are separate. Explain which stock effects the example requires and that no paid model key is needed.
2. **Install a specific release through the documented route.** Prefer one verified pipx or uvx route; give venv/pip and checkout alternatives. Identify the exact executable the GUI MCP client will launch. Until publication is verified, label source-install instructions as such rather than implying the package is on PyPI.
3. **Find the actual User Library in Live and install the bundled script there.** Provide quoted Windows and macOS commands, common default locations and relocated-library guidance. Confirm `Remote Scripts/AbletonLiveMCP/{__init__.py,core.py,handlers.py}` and a useful failure message. Installation must not remove a working copy on failure.
4. **Restart Live and enable the AbletonLiveMCP control surface.** Choose None for MIDI I/O, use one active bridge instance, and open a disposable Set. Link directly to the startup/log troubleshooting steps.
5. **Paste the config for the chosen MCP client and restart/reload that client.** Supply separate, syntactically correct Claude Desktop, Claude Code and Cursor examples plus a generic stdio recipe. Include an absolute executable path where necessary and explicit local-only classification configuration.
6. **Prove the read-only connection first.** List tools, call `live_hello`, confirm compatible script/protocol and supported Live version, then inspect tracks/session. Show the exact unreachable-Live message and recovery link. Normal installs should expose 35 ordinary tools, with knowledge tools absent unless separately enabled.
7. **Optionally select supported plugins, then preview a role chain.** Explain both OS preference paths, `ABLETONLIVEMCP_PREFS`, canonical adapter names, valid JSON and fallback reports. Start with a single stock compressor plan; then show a preference override. New plugin names require an adapter, not just a preference string.
8. **Review and build one small chain on a disposable track, then inspect readbacks.** Use unit-bearing values, examine skipped/unsupported intent and `ok`/`problems`, and explain append/no-rollback/retry behavior. Link the adapter contribution guide and the upgrade procedure: update server, reinstall compatible script, restart both, recheck handshake.
