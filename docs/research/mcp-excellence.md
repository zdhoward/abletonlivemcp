# What makes an excellent, maintainable, public MCP server (applied to Ableton Live MCP)

Researched 2026-11-10 against the repo at `main` (a79d95c). Latest MCP spec revision read: **2026-07-28**.
Evidence tags: **[V]** read from the primary source this session; **[M]** measured by running our code;
**[I]** my inference; **[U]** not re-verified this session (treat as a lead, not a fact).

Spec base URL: `https://modelcontextprotocol.io/specification/2026-07-28/`. Abbreviations used below:
`spec/tools` = `server/tools`, `spec/resources` = `server/resources`, `spec/prompts` = `server/prompts`.

---

## 0. Bottom line

The server is already ahead of most Ableton MCPs on the thing users complain about most: silent wrong writes
(read-back, refusals, read-only default, mutation lock). It is behind on the MCP surface itself (no
structured output, no titles, no resources, no prompts, no progress) and has zero distribution machinery
(no CHANGELOG, `server.json`, release workflow, MCPB, client snippets). The biggest strategic decision is
**scope honesty**: the v1 plan deliberately omits Arrangement, which the largest competitor's own gap map
calls "the biggest hole" ([ableton-mcp #142](https://github.com/ahujasid/ableton-mcp/issues/142) [V]).
That is defensible, but say so loudly in the README.

---

## 1. Quality checklist and how we score

Scale: 3 = excellent, 2 = good with gaps, 1 = weak, 0 = absent. "Evidence" is what I read in the code.

### 1.1 Tool design

| # | Quality | Source | Our evidence | Score |
|---|---|---|---|---|
| 1 | Few, purpose-built tools; consolidate chained steps; avoid endpoint wrappers | "More tools don't always lead to better outcomes"; a `schedule_event` tool can replace list+create ([Anthropic, Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) [V]) | 27 tools [M]. `live_plan_chain`/`live_build_chain` consolidate a multi-call workflow. Plan merges setters (32 target, `docs/plans/v1-public-release.md` section 5F). Singleton setters (`live_set_scene_name`, `live_stop_clip`, `live_fire_clip` per call) still exist. | 2 |
| 2 | Namespaced, unambiguous names (1-128 chars, `[A-Za-z0-9_.-]`) | Anthropic (prefix grouping); spec/tools "Tool Names" [V] | Uniform `live_` prefix, all valid. | 3 |
| 3 | Batch operations to cut round trips | ableton-mcp #130: one-call-at-a-time cost an estimated "26M input tokens", no scene launch, no bulk locators [V] | `live_set_device_parameters` takes a list, `live_add_notes` takes a list, `live_fire_scene` exists. No batch for tracks/clips/scenes. Each bridge call is about 0.9 s (repo memory + plan section 3) so batching also matters for wall-clock. | 2 |
| 4 | Token-efficient responses: pagination, filtering, range selection, `response_format` concise/detailed | Anthropic [V]: concise used about a third of the tokens; Claude Code warns at 10k and caps MCP output at 25k tokens ([Claude Code MCP docs](https://code.claude.com/docs/en/mcp) [V]) | Cursor pagination on browser list/search. No `response_format`; `live_tracks`, `live_device_parameters`, `live_get_notes` return full rows. Plan has bounded pages for parameter lists. | 2 |
| 5 | Meaningful context: names not opaque ids, ids still available for follow-up | Anthropic [V] | Rows carry display index plus references (plan C). Not individually audited for naming. | 2 |
| 6 | Descriptions written like onboarding a new hire; units and formats explicit; unambiguous params | Anthropic [V] | Docstrings are one-liners (first defs are about 320-340 chars including schema) [M]. Units (dB, normalized pan, beats) are not systematically in descriptions. | 1 |
| 7 | `title` for human display | spec/tools Data Types [V] | `title` is None on every tool [M]. | 0 |
| 8 | Deterministic tool order (cache-friendly) | spec/tools: servers SHOULD return a deterministic order [V] | Decorator registration order; deterministic. | 3 |

### 1.2 MCP features used

| # | Quality | Source | Our evidence | Score |
|---|---|---|---|---|
| 9 | Tool annotations set honestly (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) | Spec says clients MUST treat annotations as untrusted unless the server is trusted [V], so they are hints, but they drive client approval UX [I] | Three presets READ / CREATE / OVERWRITE applied by decorator, `openWorldHint=False` everywhere (`server.py` lines 41-111). Good. One check: `live_fire_clip` and `live_set_transport(playing)` change audible state; classify deliberately. | 3 |
| 10 | `outputSchema` plus `structuredContent` (and the text fallback) | spec/tools "Structured Content" and "Output Schema": servers MUST conform to a declared schema; SHOULD also return serialized JSON in a TextContent block [V] | Every tool returns `dict`/`list`; `output_schema` is None on the tools I inspected [M]. Clients cannot know the shape. Typed models exist in `models.py` and could be the return types. | 1 |
| 11 | Errors that teach: execution errors (`isError: true`) for model-fixable problems, protocol errors only for malformed requests | spec/tools "Error Handling" [V]; Anthropic "specific and actionable improvements", show correct input [V] | `ToolFailure(ToolError)` with stable `refused:<code>: <message> (not applied)`. Excellent on the "did it apply" axis. Not yet: a corrected-input example, `retryable`, `may_have_applied` (planned, plan 5F). Repo memory notes plain exceptions hide the message; already handled. | 2 |
| 12 | Resources for read-only context | spec/resources: application-driven [V] | None registered (no `@mcp.resource` in `server.py`). | 0 |
| 13 | Prompts for user-triggered workflows | spec/prompts: user-controlled, "slash commands" [V] | None registered. | 0 |
| 14 | Progress and cancellation for long operations | Spec utilities; not re-read this session [U] | No `Context` use in `server.py`. `live_build_chain` is a multi-call workflow (12 stages x about 0.9 s plus settle). Claude Code auto-backgrounds MCP calls after 2 min and enforces `MCP_TOOL_TIMEOUT` [V]. | 1 |
| 15 | Elicitation for human confirmation | spec/tools: `InputRequiredResult` with `elicitation/create` (MRTR) [V]; Claude Code supports elicitation and hooks on it [V] | Not used. The plan correctly rejects a model-supplied `confirm` flag, but has no alternative; elicitation is the non-forgeable one. | 0 |
| 16 | Sampling | Marked **deprecated** as of 2026-07-28 [V, header only] | Not used. Correct to skip. | n/a |
| 17 | Logging to stderr / protocol-only stdout | Reference-server note: stdio server waits on stdin ([servers repo](https://github.com/modelcontextprotocol/servers) [V]); plan 5F says protocol-only stdout [V] | Plan states it; not audited line by line. | 2 |
| 18 | `listChanged` / subscriptions | spec/tools, spec/resources: `subscriptions/listen` replaces the old session-bound mechanism [V]; Claude Code re-fetches on `list_changed` [V] | Not used. Only relevant if the tool list becomes dynamic. Bridge is request/response, so Live-state subscriptions would be polling. | n/a |

### 1.3 Safety and security

| # | Quality | Source | Our evidence | Score |
|---|---|---|---|---|
| 19 | Validate inputs, access control, rate limit, sanitize outputs | spec/tools "Security Considerations": servers MUST do all four [V] | Typed args plus `_row` bounds checks; `read_only` gate; mutation lock with 5 s wait; bounded frames/queues per plan 5B. Output sanitization is the `_untrusted()` wrapper (provenance + data). | 3 |
| 20 | Read-only mode that cannot be overridden by the model | GitHub MCP: `--read-only` "takes priority", write tools skipped even if requested via `--tools` ([github-mcp-server](https://github.com/github/github-mcp-server) [V]) | `_writable()` refuses unless config has `read_only: false`; default is read-only; enforced again in the bridge (plan 5C). Matches best practice. | 3 |
| 21 | Treat text from the host app as untrusted (indirect prompt injection) | spec/prompts and /resources: validate inputs and outputs [V]; this exact risk (track/browser names written by a stranger's project) is [I] | `_untrusted()` wraps names and text with provenance. Applied to which tools? Needs an audit that every string from Live passes through it. | 2 |
| 22 | Local-server hardening: loopback only, authenticated | [MCP security best practices](https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices) lists local-server compromise and confused deputy [V, headings only] | Bridge binds `127.0.0.1:9877` [V in code]. Per-user HMAC secret is specified in plan 5B; I did not confirm it is implemented. | 2 |
| 23 | Honest security claims | Playwright MCP: "not a security boundary"; origin filter "does not serve as a security boundary" ([playwright-mcp](https://github.com/microsoft/playwright-mcp) [V]) | `SECURITY.md` exists. Add a threat-model paragraph in that style (same-user hostile code is out of scope, as plan 5B already says). | 2 |
| 24 | No dangerous generic executor | Playwright names `browser_run_code_unsafe` as RCE-equivalent [V]; plan: "No general property executor or Python evaluation" [V] | Satisfied by design. This is a differentiator against servers that expose arbitrary code. | 3 |

### 1.4 Distribution and maintenance

| # | Quality | Source | Our evidence | Score |
|---|---|---|---|---|
| 25 | One-command install via PyPI + `uvx` | Reference servers use `uvx`/`npx` ([servers repo](https://github.com/modelcontextprotocol/servers) [V]) | Console scripts `abletonlivemcp` and `abletonlivemcp-install` defined; wheel force-includes the Remote Script. Not on PyPI. README documents only `pip install -e .[dev]`. | 1 |
| 26 | MCP Registry listing | [Registry docs](https://modelcontextprotocol.io/registry/package-types) [V] | No `server.json`, no `mcp-name:` README token. Registry is "in preview" [V]. | 0 |
| 27 | MCPB one-click bundle | [MCPB manifest](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md) [V] | No `manifest.json`. | 0 |
| 28 | Per-client config snippets | Playwright: one standard block then collapsible per-client sections [V] | None in README. | 0 |
| 29 | Semver, CHANGELOG, tagged releases | convention [I] | `pyproject` is 0.0.1 "Pre-Alpha"; no `CHANGELOG.md`; no release workflow. Owner global rule says semver. | 1 |
| 30 | CI: lint, tests, OS/Python matrix | convention [I] | `.github/workflows/ci.yml`: ruff + pytest on ubuntu/windows x py3.10/3.13. No lockfile, no type check, no build/wheel-content job. Real-Live evidence is manual (documented in plan section 9). | 2 |
| 31 | Evals on realistic multi-step tasks | Anthropic: realistic tasks, verifiable outcomes, track accuracy, runtime, tool calls, tokens, errors; read transcripts [V] | Unit/integration tests only (about 20 test modules). No agent-level evals. | 0 |
| 32 | Community hygiene | [I] | CONTRIBUTING, CoC, SECURITY, issue and PR templates exist. | 3 |
| 33 | Diagnostics (`doctor`) | LivePilot ships `--status` and `--doctor` ([LivePilot](https://github.com/dreamrec/LivePilot) [V]) | `live_hello` handshake plus installer; no doctor command. | 1 |

**Net:** strong on safety (rows 19-24), middling on tool ergonomics, weak on MCP-surface completeness and
almost entirely absent on distribution. The distribution gap is cheap to close; the surface gap is where
design thought is needed.

---

## 2. Recommended tool-surface design for a DAW

### 2.1 How many tools, how granular

Evidence on count:
- Anthropic: fewer purpose-built tools beat wrappers; overlap "can distract agents" [V].
- GitHub MCP (34.4k stars) manages a large API with **toolsets** (default set is small, rest opt-in), a `--tools` allowlist, `--read-only`, and **consolidated tools with a `method` parameter** (`issue_write`, `actions_get`) [V].
- Playwright MCP (39.5k stars) keeps the core small and puts riskier or niche groups behind `--caps` [V].
- LivePilot went the other way (474 tools) and had to retrofit a 26-tool default plus `search_tools`/`call_tool` and profiles in v1.30.0 [V]. That is evidence that large surfaces force a discovery layer.
- ableton-mcp main: 37 tools, 46% of 65 mapped Live capabilities working, with 19-20 more stuck in unmerged PRs [V, #142].
- Claude Code has tool search on by default [V], which softens the cost of many tools in that one client; other clients may load every schema [I].

**Recommendation: target 25-35 default tools, designed around nouns with a small `method`/field set, plus an opt-in toolset switch for growth.** Our planned 32 is in range. Principles:
1. **Read tools return a bounded subtree, write tools take a list.** One `live_get_*` per noun (session, track, mixer, clip, device, transport, scene). Every setter accepts `targets: [...]` (tracks, clips, notes, parameters) so a 16-track organize pass is one call, not 16 (fixes #130 pattern).
2. **Merge fire/stop into one `live_launch(target, action)`** only if descriptions stay unambiguous; otherwise keep separate. Test both against evals before deciding (Anthropic says prefix/naming effects are model-dependent and should be measured [V]).
3. **Workflow tools stay plan/execute split** (`live_plan_chain` then `live_build_chain`): read-only preview, one-shot execution, receipt. This is the strongest pattern in the repo; extend it to "scene setup" and "organize" (see prompts).
4. **Toolsets, not more tools in the default**: add `ABLETONLIVEMCP_TOOLSETS` (default: `session,clips,devices,chains`; opt-in: `arrangement`, `automation`, `library`, `als`). Copy GitHub's rules: invalid names fail at startup; read-only wins over everything; keep old names as aliases after the first public release [V].
5. **Never add a generic "run arbitrary LiveAPI/Python" tool.** It is the main security smell in other DAW servers (and is what ruled out bschoepke-style designs in the vision doc; I did not read that repo [U]).
6. **Response shape:** add `response_format: "concise" | "detailed"` (default concise) to list/get tools; concise returns display names plus compact refs, detailed adds raw values and ids [V, Anthropic]. Add `outputSchema` from `models.py` types and keep the text fallback.
7. **Descriptions:** state units (dB, beats, normalized 0-1), index base, what "applied" means (readback), and one correct example call. Keep each under about 150 words.

### 2.2 Tools vs resources vs prompts

Spec control model [V]: tools are model-controlled; resources are application-driven (host decides what to attach); prompts are user-controlled (slash commands). Because host support for resources varies [I], **every resource must also be reachable via a tool**; resources are an optimization, never the only path.

**Make these resources** (read-only, stable URIs, text/markdown or JSON, with `audience`/`priority` annotations [V]):
| URI | Content | Why a resource |
|---|---|---|
| `live://session` | tempo, signature, track/scene counts, Live version, write policy | cheap context the user can attach once |
| `live://tracks` and template `live://track/{index}` | track summaries / one track's devices | natural picker items; template args can use the completion API [V] |
| `live://track/{t}/device/{d}/parameters` | parameter names, units, ranges | large read, better attached than called repeatedly |
| `live://browser/{root}` | one bounded page of the browser tree | cursors map to pagination [V] |
| `live://operation/{id}` | build receipt/status | already `live_get_operation` |
| `docs://conventions/units`, `docs://chain/vocal-presets`, `docs://safety` | static markdown: units, preset rationale, what the server will refuse | "mixing conventions" belong in context, not in every tool description |

Subscriptions (`subscriptions/listen` with `resourceSubscriptions` [V]) are low priority: the bridge has no push channel and each read costs about 0.9 s, so subscribing would just be server-side polling. Revisit only if the Remote Script gains change notifications.

**Keep as tools:** everything that mutates, and reads that need arguments or budgets (search, notes in a clip window, plan preview).

### 2.3 Prompts and workflows to ship (user-invoked)

Ship 6-8 prompts, each a short recipe that tells the model which tools to call in what order and what to ask the user first (spec: prompts can embed resources [V]):
1. `vocal_chain` (args: track, style, preferred plugins) -> plan, show preview, wait for approval, build.
2. `organize_session` -> read tracks, propose names/colors, apply in one batched call after approval.
3. `setup_scene` (args: genre/tempo/instrument list) -> create scene, tracks, empty clips, set tempo.
4. `mix_check` (read-only) -> inspect levels/pan/sends and list observations; no writes.
5. `explain_chain` -> read a track's devices and parameters and describe the signal path in plain language.
6. `diagnose_connection` -> call `live_hello`, report versions/policy, say which step of install to redo.
7. `safe_tweak` (args: device, goal) -> read parameters, propose changes, apply with originals recorded.

Also ship the same recipes as a portable Agent Skill (`SKILL.md`): Producer Pal does this for runtimes without MCP prompt support ([producer-pal.org](https://producer-pal.org/) [V]).

### 2.4 Optional protocol features, ranked by value

1. **Structured output** (high, cheap): typed returns -> `outputSchema` + `structuredContent`.
2. **Elicitation for write confirmation** (high, matches plan 5C): on first write in a session, or on any `OVERWRITE` operation, ask the human via `elicitation/create` (form mode, no secrets [U for form-mode rules]); fall back to read-only refusal when the client lacks the capability. Unlike a `confirm` argument the model cannot answer it. Verify Claude Code behavior: elicitation is supported but "not auto-backgrounded" and, for tasks, only in interactive sessions [V].
3. **Progress** (medium): `ctx` progress per stage in `live_build_chain`, so a 12-stage build does not look hung.
4. **Cancellation** (medium): cancel-before-start only, consistent with the plan's "cancelled-before-start never runs; after start is `may_have_applied`" [V]. Never retry mutations.
5. **Logging**: stderr only; optional MCP logging notifications at `info`.
6. **Roots**: skip until offline `.als` scanning returns; then use `roots/list` (Claude Code answers it with the launch directory plus `--add-dir`) [V] instead of an env var path.
7. **Sampling**: do not use (deprecated) [V]. **Subscriptions/listChanged**: skip for now.

### 2.5 Reliability patterns worth keeping (differentiators)

- Readback after every write and report the stored state, not the request. ableton-mcp #138: `add_notes_to_clip` reported 3 notes written when Live kept 2; the count came from `len(notes)` [V]. Our `_settled()` pattern is the fix; say so in the README with that example.
- Receipts with `complete/partial/failed/pending`, `may_have_applied`, originals for writes (plan 5E).
- Stable references that expire on Set change, instead of raw indices.

---

## 3. Distribution and maintenance plan

### 3.1 Packaging order (do in this sequence)

1. **Pick and reserve the name** now: `abletonlivemcp` on PyPI (availability not checked [U]) and registry name `io.github.<owner>/abletonlivemcp`. Registry names are namespaced by auth method (GitHub login gives `io.github.*`) [V]. Owner decision (account/release gate).
2. **PyPI + `uvx`.** Both entry points already exist. Document:
   - run server: `uvx abletonlivemcp`
   - install Remote Script: `uvx --from abletonlivemcp abletonlivemcp-install` (uv syntax [U], verify on a clean machine)
   - Publish through PyPI Trusted Publishing from GitHub Actions (no long-lived token) [U, PyPI docs not fetched].
3. **Wheel hygiene test** in CI: build sdist, build wheel from sdist, assert the Remote Script files are present and `knowledge/`, `research/`, `tasks/`, `.als`, audio and bytecode are absent (plan 5A already requires this [V]). Then `uvx --from dist/*.whl abletonlivemcp` in a clean venv and run `live_hello` against a fake bridge.
4. **MCP Registry** (`server.json`, `registryType: "pypi"`, `transport: {type: "stdio"}`) with `<!-- mcp-name: io.github.<owner>/abletonlivemcp -->` in the README, because PyPI ownership is verified by that string in the package description [V]. Publish from CI with `mcp-publisher login github-oidc` (needs `permissions: id-token: write`), triggered on `v*` tags, after the PyPI step succeeds [V]. Registry is in preview and may reset [V]; do not build anything that depends on it.
5. **MCPB bundle** for Claude Desktop one-click. Use `server.type: "uv"` (manifest 0.4): ships `pyproject.toml`, about 100 KB, host installs deps; plain `python` type requires bundling all deps [V]. Expose `read_only` as a `user_config` boolean. Attach the `.mcpb` to the GitHub Release and add a second `packages` entry with `registryType: "mcpb"` plus `fileSha256` (URL must contain "mcp") [V]. Caveat [I]: the bundle cannot install the Live Remote Script by itself; the README must make that a visible step 1, or the first-run tool response (`live_hello` failing) must say exactly how. Producer Pal avoids this by being a Max for Live device ([V]); we can't, so the installer and `doctor` carry that weight.
6. **Client snippets** in README, Playwright style: one standard `mcpServers` block, then collapsible sections for Claude Desktop, Claude Code (`claude mcp add abletonlivemcp -- uvx abletonlivemcp`; the `--` separator is required [V]), Cursor, VS Code. Windows is the acceptance platform, so test the Windows `command` forms on Windows rather than copying macOS snippets [I].

### 3.2 Versioning, compatibility, deprecation

- Semver. Stay on `0.x` until the Windows/Live 12.2 acceptance pass is recorded; the plan already says v1 scope does not commit to a `1.0.0` tag [V].
- Three numbers surfaced by `live_hello`: package version, **bridge protocol** version, Remote Script version. Compatibility rule: protocol must match; patch versions of script and package may differ (plan 5B [V]).
- Tool names are public API after the first release. Policy: renames keep the old name as an alias for one minor version, with the description starting "Deprecated alias of ..." (GitHub does exactly this [V]). The plan's "one pre-release break, no aliases" is fine only before the first public tag.
- Add a **tool-surface snapshot test**: dump `list_tools()` (names, input schemas, annotations, output schemas) to a committed JSON; PRs that change it must update the file and the CHANGELOG. Also assert a size budget on the serialized tool list so descriptions do not bloat.
- Keep a Keep-a-Changelog `CHANGELOG.md` ([convention, U](https://keepachangelog.com)); GitHub Releases generated from it.
- State support matrix in README: OS (Windows tested, others unsupported), Live 12.2+ (12.3+ APIs gated by `probe()`), edition requirements for stock devices (plan 3 [V]).

### 3.3 CI/CD

| Job | When | Purpose |
|---|---|---|
| lint + test matrix | PR, main | exists (ruff, pytest, ubuntu/windows x 3.10/3.13) |
| `mcp` conformance | PR | in-process stdio client against the server with a **fake bridge**: list tools, snapshot schemas, call every read tool, assert refusals are `isError` with the stable text, assert stdout carries only protocol frames |
| build + wheel contents | PR | see 3.1 step 3 |
| type check (`pyright` or `mypy`) | PR | cheap; needed once `outputSchema` is derived from types |
| release | tag `v*` | build, `twine check`, publish PyPI (trusted publisher), build `.mcpb`, create GitHub Release, `mcp-publisher publish` |
| real-Live acceptance | manual before each minor release | recorded in `docs/release/` (already the practice) |
| dependabot / weekly `pip` resolve | weekly | `mcp>=2,<3` is a major-version pin; watch 2.x releases and spec revisions |

### 3.4 Evals (the missing quality gate)

Follow Anthropic's method [V]: 10-15 realistic multi-step tasks, each with a verifiable end state, measured for accuracy, wall-clock, tool-call count, tokens, and errors; hold out some tasks; read transcripts.
- Backend: an **in-memory Live simulator** behind the same bridge interface (so evals run in CI cheaply, and real-Live runs are a nightly/manual variant).
- Tasks: "name and color 8 tracks by instrument type", "build the stock vocal chain on track 3 then lower reverb wet", "create a scene with drums/bass/keys MIDI clips and 4 notes each", "read-only audit with writes disabled (must not write)", "stale reference after Set change (must refuse)", "prompt injection in a track name (must not follow it)".
- Track the numbers in the repo (`docs/evals/`), so claims like "N calls for a 16-track organize" are reproducible.

### 3.5 Maintainability rules (competitors show the failure mode)

- ableton-mcp: 15 open issues and 32 open PRs; #142's author says "merge throughput, not missing ideas, is the bottleneck" and started a community fork (#138's fix also lives in a fork) [V]. Lesson: publish a short **triage SLA** (first response within a week), label `good first issue`, keep PRs small, keep a public ROADMAP derived from the plan's WON'T-YET table.
- Producer Pal (371 stars) had one open issue at read time, a 504 timeout on 2.5.0 [V]. Timeouts when Live is busy are the failure users will hit first; make timeouts return actionable text (what step, whether it may have applied), and document Live-busy conditions (modal dialogs, plugin scans).
- Keep `HANDOFF.md`/`knowledge/` out of the public surface (plan already excludes them [V]).

---

## 4. Competitors

Read: READMEs, issue pages and project sites as of 2026-11-10. Star counts are from the repo pages I fetched [V]. Pages for the bschoepke server and two comparison blog posts failed to load, so they are not in the table [U].

| Project | Stars / license | Architecture | Surface | Strengths (evidence) | Complaints / gaps (evidence) |
|---|---|---|---|---|---|
| [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) | 3.3k, 458 forks | Python MCP over socket to Remote Script (port 9877) | 37 tools on main (31 excluding telemetry) per #142 | First mover and mindshare; broad basic coverage | 15 issues, 32 open PRs; #142: about 54% of mapped capabilities missing or unmerged; #130: heavy token use (no batching, no scene launch, oversized reads); #138: reports notes written that Live dropped; no reply on #130 |
| [adamjmurray/producer-pal](https://github.com/adamjmurray/producer-pal) | 371, MIT | Max for Live device hosting MCP + REST + Agent Skill; also `.mcpb` and `npx producer-pal` | not listed on pages I read | Zero Remote-Script copy, broad client support (Claude Desktop, ChatGPT app, LM Studio, built-in chat UI), skill for non-MCP agents, active releases (v2.5.0) | Requires Live 12.3+ **with Max for Live** (12.4 recommended); 504 timeouts report (#1294) |
| [uisato/ableton-mcp-extended](https://github.com/uisato/ableton-mcp-extended) | 282, MIT | Fork lineage; TCP + UDP for low-latency control | not listed | ElevenLabs audio integration, VST loading, UDP real-time | Automation "isn't working perfectly yet"; arrangement not done; manual clone + `pip install -e .`; README path inconsistency |
| [dreamrec/LivePilot](https://github.com/dreamrec/LivePilot) | 96, BSL 1.1 | `npx` server + Remote Script, optional M4L analyzer | 474 tools in 57 domains; 26-tool default + `search_tools`/`call_tool`; profiles | `.mcpb` double-click, `--setup`/`--status`/`--doctor`, audio analysis | Not OSI open source (BSL); large surface needed a discovery layer; double-registration warning (two install paths collide on port 9878) |
| [nozomi-koborinai/ableton-osc-mcp](https://github.com/nozomi-koborinai/ableton-osc-mcp) | 16, MIT | Go server, OSC/UDP to AbletonOSC plus its own Remote Script patch | about 100 tools | Audio analysis, bouncing, arrangement writing | Needs AbletonOSC plus patched script and a full Live restart; primary target Live 11.0.12 |

### Patterns from widely loved non-music servers

| Server | Pattern to copy | Source |
|---|---|---|
| GitHub MCP (34.4k stars) | Toolsets and `--tools` allowlist; `--read-only` wins; consolidated tools with `method`; per-tool required scopes; old tool names kept as aliases; `fields` param to trim output; remote + Docker + source install; per-client guides | [repo](https://github.com/github/github-mcp-server) [V] |
| Playwright MCP (39.5k) | Accessibility snapshot as the cheap default, pixels as opt-in; `--caps` for niche tools; CLI flag = env var = JSON config; one standard config + per-client sections; blunt "not a security boundary" | [repo](https://github.com/microsoft/playwright-mcp) [V] |
| Context7 | Very small surface (two tools: `resolve-library-id`, `query-docs`), clear client rules, cross-client install snippets. I could only confirm tool names, not stars or install detail | [repo](https://github.com/upstash/context7) [V, partial] |
| MCP reference servers (Filesystem, Git, Memory, Fetch, Time) | Allowed paths via arguments, stdio only, `uvx`/`npx` launch; explicitly "educational examples", with 13 servers archived (GitHub, Slack, Postgres...) - a reminder that maintenance, not launch, decides survival | [repo](https://github.com/modelcontextprotocol/servers) [V] |

### Gaps we can own

1. **Trustworthy writes.** Readback-verified, receipts with `may_have_applied`, refusal on stale references. Competitors' issues show the opposite (#138). None of the five projects' pages I read advertise plan/preview/receipt semantics [I, absence of evidence].
2. **Token and call efficiency, with numbers.** Batch setters plus `response_format`; publish eval numbers against #130's complaint.
3. **Safe by default.** Read-only default, non-overridable by the model, mutation lock and lease, no code-execution tool. Playwright shows users reward candor about security [V].
4. **Works without Max for Live.** Producer Pal requires it [V]; a Remote-Script server serves Live Standard users (inference: edition requirement for the Remote Script path is not verified, check before claiming).
5. **Stock-first chain building** for vocals/mixing starting points with exact browser paths and explicit omissions: no competitor advertises it [I].
6. **Installer quality.** Ownership manifest, rollback, no destructive upgrade, `doctor`; LivePilot's `--doctor` shows users value this and its double-registration warning shows what goes wrong without it [V].
7. **Maintenance responsiveness.** The largest project's own contributors describe merge throughput as the bottleneck [V]. A predictable triage SLA is a real differentiator.

### Gaps we should not pretend to own yet

- Arrangement editing (biggest hole per #142), automation, audio analysis, drum rack/usage-derived builds: all WON'T-YET in the plan. Publish the roadmap so users see "not yet" rather than "missing".

---

## 5. Prioritized actions

**Before the first public tag (cheap, high value)**
1. Add `title`, units, and examples to every tool description; add `response_format` on the three heaviest reads.
2. Return typed models so tools publish `outputSchema`; keep text fallback.
3. Add the fake-bridge conformance test and tool-surface snapshot test.
4. Write `CHANGELOG.md`, README install/snippets/support matrix/threat model, `mcp-name` token, `server.json`.
5. Release workflow: build, wheel-content test, PyPI trusted publish, `.mcpb`, registry publish (owner flips the switch).
6. `abletonlivemcp doctor` subcommand.

**Shortly after**
7. Elicitation for writes (fallback: read-only refusal).
8. Progress notifications in `live_build_chain`.
9. Resources (`live://session`, tracks, device parameters, operation) and 6-7 prompts plus a `SKILL.md`.
10. Eval suite (10-15 tasks) against an in-memory simulator.

**Owner-only decisions**: PyPI/registry names and accounts, tagging and publication, `1.0.0` timing, license (unchanged: MIT).

## 6. What I did not verify

- Elicitation form-mode restrictions, progress, cancellation, roots and logging utility pages were not re-read; statements about them rely on the Claude Code docs excerpt and the plan.
- PyPI Trusted Publishing and `uvx --from` syntax, Keep a Changelog: conventions from memory.
- Whether the HMAC bridge handshake from plan 5B is implemented in code (I only confirmed loopback bind, the lease, and read-only enforcement).
- That every Live-originating string passes through `_untrusted()`.
- bschoepke/ableton-live-mcp and two blog comparisons: fetch failed.
- Claude Code behavior for MCP prompts as slash commands and resources via `@`: page truncated before that section; spec describes the intent only.
