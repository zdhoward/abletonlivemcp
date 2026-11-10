# Ableton MCP: documentation and feasibility review

Reviewed 2026-11-10 against the immutable `original-prompt.md`. Public documentation and source inspection only; no owner files, Live runtime, third-party code execution, or load/save tests. Public preset bytes were decompressed and inspected in memory. Repository links describe the versions inspected on this date, not permanent API guarantees.

**Verdict:** enough evidence exists to start implementation, but not to promise every workflow end to end. Use a Remote Script for supported live operations, an offline reader for usage analysis, and version-specific preset transformations for experiments that exceed the API. Browser plugin Collections tagging remains unresolved.

Confidence labels: **documented** = explicitly described by Ableton/Cycling ’74; **seen-in-open-source** = implementation, runtime API reference, or fixture observed, without our Live verification; **inferred** = proposed design or extrapolation; **unknown** = evidence insufficient. These labels describe evidence, not production readiness.

| Use case | End-to-end verdict | What can start now / remaining gate |
|---|---|---|
| UC1: recent projects → used one-shots → standard Drum Rack | **Needs sample file** | Offline scanner, usage index, and note layout are buildable now. Validate sample provenance, one-shot classification, generated rack loading, and actual played-note filtering on fixtures. |
| UC2: color-tag frequently used plugins | **Blocked** for reliable automatic Collections writes | Rankings and proposed tags are buildable. No supported write API or verified plugin Collections storage/reload procedure found. A sample diff is necessary but may not resolve the API gap. |
| UC3: described vocal chain → owned equivalents/settings | **Buildable now**, within exposed parameters | Build evidence-backed suggestions, inventory matching, browser loading, and bounded parameter writes. Exact settings and plugin coverage require configured plugin instances and runtime calibration. Installed does not establish licensed/owned. |
| UC4: existing FX → rack, named macros, ranges | **Needs sample file** | Preset transformation is plausible; live grouping and mapping creation are not documented. Preserving an existing chain's state, automation, and routing is a separate, unproven integration step. |
| UC5: scene or VST stack | **Buildable now**, with browser/runtime validation | Track/scene/clip creation and browser-item loading have strong precedent. Target selection, plugin availability, load completion, and nested insertion need tests. |
| UC6: organize/label by category and frequency | **Buildable now** for local index and live names/colors | Collections writes and Live 12 browser tag writes inherit UC2's limitation. Counts describe saved usage, not listening time or a user's preferences. |

## 1. LOM and Python Remote Script capabilities

The Max for Live LOM is an official reference for exposed objects, **not a complete specification of Python Remote Scripts**. Python additionally exposes `Application.browser` and framework scheduling. Conversely, a method appearing in someone else's bridge is not proof it exists in Live. Capability-probe the actual runtime and report unsupported operations explicitly.

| Operation | Concrete capability / boundary | Version and confidence |
|---|---|---|
| Load a device/preset by name | Python `application().browser` exposes category trees; resolve a `BrowserItem`, then `browser.load_item(item)`. Resolve ambiguous names before loading. Upstream selects the target track before loading. | **Seen-in-open-source**, 11/12 ecosystem. Browser API is Python-specific; the official Max LOM does not provide this browser interface. [Browser runtime reference][browser], [upstream bridge][upstream-script]. |
| Load by path | Upstream's slash-separated `path` is a path through browser categories/children, **not an arbitrary OS filename**. `BrowserItem.uri` identifies browsable content. Put generated presets in an indexed User Library/Places location and resolve their items; arbitrary path loading is **unknown** here. | **Seen-in-open-source** for browser paths/URIs; Windows/macOS filesystem-path loading requires a probe. [Upstream bridge][upstream-script]. |
| Insert device at index | `Track.insert_device(device_name, target_index?)` and `Chain.insert_device(...)`: UI name, append if index omitted, valid signal-flow positions only. **Native Live devices only; excludes plugins and Max for Live.** | **Documented, since 12.3**; do not offer on 11 or earlier 12. [Track][track], [Chain][chain]. |
| Insert rack chain | `RackDevice.insert_chain(index?)`, append by default; can fail if insertion is invalid. Does not mean grouping existing devices or moving them into that chain. | **Documented, since 12.3**. [RackDevice][rack]. |
| Read/set macros | Rack parameters expose macro values; parameter `value` is writable, names readable. `visible_macro_count` is read/observe; `add_macro()` / `remove_macro()` change visibility. Discover parameters rather than assuming exactly eight. | **Documented**. Up to **16 already in Live 11**, not introduced in 12. [Live 11 racks][manual11-racks], [Live 12 racks][manual-racks], [RackDevice][rack], [DeviceParameter][parameter]. |
| Create macro mappings / rename macro | No `macro_map` or `rename_macro` in the inspected official RackDevice documentation or unofficial runtime method inventory. `DeviceParameter.name` is officially **get-only**; do not equate writable device names with writable macro names. Read mapping-state indicators are not mapping editors. | Public supported creation/rename API **unknown**; absence in these inventories supports treating it as unsupported. Upstream *attempts* `macro_map` with an `hasattr` guard and raises if missing; that is not successful runtime evidence. [Runtime rack][runtime-rack], [parameter][parameter], [upstream bridge][upstream-script]. |
| Group existing devices into rack | No documented equivalent of selecting devices and invoking Group. Inserting an empty rack/chain does not preserve/move a live FX chain. Exporting or capturing complete arbitrary plugin state through LOM is also not established. | **Unknown** supported live route; offline saved-set transformation is **inferred**. [Track][track], [Chain][chain], [Device][device], [RackDevice][rack]. |
| Drum pads / receiving notes | `rack.drum_pads`, `visible_drum_pads`, pad `chains`, `note` (read-only), `mute`/`solo` (writable), name (get/observe); `copy_pad(source_index, destination_index)`. `DrumChain.in_note` is get/set, with `-1` meaning All Notes; `out_note` and `choke_group` also get/set. | **Documented**. `in_note` explicitly **since 12.3**; don't promise receiving-note reassignment on 11. [DrumPad][pad], [DrumChain][drumchain], [RackDevice][rack]. |
| Load samples into pad/Simpler | GUI dropping a sample on an empty pad creates a chain and Simpler; browser loading has a hotswap target. No `SimplerDevice.load_sample(path)` found in the official or inspected Python reference; `sample` is a read/observe child. Browser-targeted pad loading is a feasibility experiment, not yet a verified recipe. | GUI behavior **documented**, Python targeting **inferred**, arbitrary Simpler path-loader **unknown**. Generated `.adg` is the stronger public precedent. [Manual racks][manual-racks], [Simpler][simpler], [runtime Simpler][runtime-simpler], [Browser][browser]. |
| Track / clip / device color | Track and Clip `color` / `color_index` are get/set. RGB is mapped to Live's palette. Chain colors are exposed too. Generic `Device` has no documented color property; browser Collections are a different feature. | **Documented** for track/clip/chain; generic device color **unknown/unsupported by listed API**. [Track][track], [Clip][clip], [Chain][chain], [Device][device]. |
| Plugin parameters | `Device.parameters` → `DeviceParameter` names, values, min/max, enabled/quantized state, value labels, `str_for_value`. Write `value` in the parameter's internal domain, respecting disabled/macro-controlled parameters and automation state. It is not necessarily linear or 0–1. | Common LOM surface **documented** for 11/12; plugin-specific exposure requires runtime inspection. [Device][device], [DeviceParameter][parameter]. |
| VST2 / VST3 / AU Configure | Live's panel exposes configured/published plugin controls. Configure adds controls by clicking or moving them in the plugin window; some plugin controls are never published. Configurations are per instance and can be saved as defaults. No verified API found to Configure arbitrary hidden parameters. AU applies to macOS. | GUI semantics **documented**; comprehensive parameter coverage **unknown**. “Every plugin parameter requires manual Configure first” is too absolute: default/saved configurations and plugins with panel-only controls exist. [Using Plug-Ins][manual-plugins], [device defaults][manual-devices]. |
| Device names | `Device.name` get/set, `class_name` / `class_display_name` read-only. Preserve class/plugin identity separately from a user rename. Track/clip/chain names are writable; DrumPad name itself is read-only. | **Documented**, 11/12 baseline; test plugins that refresh displayed names after preset changes. [Device][device], [DrumPad][pad]. |

**Threading:** socket workers should only frame/validate JSON and enqueue requests; drain work on Live's control-surface thread through `update_display()` or an appropriate scheduled callback. Return plain data through response queues. Keep Live object access, including reads and browser traversal, on that thread. Never hold Live's thread waiting on a socket, filesystem scan, LLM, or response queue. These are **seen-in-open-source** Remote Script patterns, not an official public Python threading contract: [Ziforge architecture][ziforge], [upstream bridge][upstream-script], [AbletonOSC manager][osc-manager]. Upstream's `schedule_message(0, ...)` plus fallback execution is implementation precedent, not proof that scheduling or fallback execution from any worker is safe. Use bounded per-tick work, explicit timeouts, cancellation state, and postcondition readback. Never automatically repeat a timed-out mutation: it may already have executed.

**Version policy:** negotiate exact Live version, Python/bridge protocol version, and runtime capability flags. 11 and 12 share much of the LOM, but 12.3 additions must be gated individually. Current Cycling ’74 pages are moving documentation; a member without a “since” marker is not proof it existed in every 11 release. Runtime references are unofficial snapshots. Max for Live availability/licensing is relevant to a Max implementation; using a Python Remote Script is a distinct architecture.

## 2. Files: structures, concrete nodes, and reference implementations

There is no public authoritative Ableton XML schema located in this review. Treat these formats as **reverse engineered**, not supported authoring APIs. A plausible XML document is not proof Live accepts it. Do not edit a user's only copy or an open Set on disk.

| Format | Observed structure and limits | Confidence / applicability |
|---|---|---|
| `.als` | Gzip-compressed XML, root `Ableton` with `Creator`, `MajorVersion`, `MinorVersion`, sometimes `SchemaChangeCount` / `Revision`; `LiveSet`, tracks, device chains, clips, automation, sample/plugin references. | **Seen-in-open-source**. [dawtool][dawtool] includes explicitly named Live 12 fixtures; older parser fixtures cover Live 9/10. Exact 11/12 node coverage still requires fixtures. |
| `.adg` | Inspected gzip XML: `Ableton/GroupDevicePreset`, `Device/DrumGroupDevice`, and sibling `BranchPresets/DrumBranchPreset` containing `DevicePresets` and `ReceivingNote`. Nested preset wrappers differ from a Set's live-device tree. | **Seen-in-open-source**, actual fixture headers Live **12.1.5** and **12.3**. [12.1.5 rack][fixture-rack], [12.3 rack][fixture-rack123]. |
| `.adv` | Inspected gzip XML containing `AbletonDevicePreset/Device/OriginalSimpler`; sample and device state live below it. Wrapper and subtype vary for native versus plugin presets. | **Seen-in-open-source**, fixture header **Live 12.2b11**, not proof of a stable final-release schema. [Simpler fixture][fixture-simpler]. |
| `.alc` | Ableton documents saved clip files containing reusable clip/device information. Gzip/XML is a reasonable family expectation but **not verified by a fixture in this review**; do not hard-code its root/wrapper yet. | Purpose **documented**; encoding/exact schema **unknown**. [Managing Files and Sets][manual-files]. Request one if clip import/export is in the first milestone. |

### Concrete XML evidence

The following are observed names/relationships, **not a complete minimal valid preset**:

```xml
<MacroControls.0>
  <Manual Value="0" />
  <MidiControllerRange><Min Value="0" /><Max Value="127" /></MidiControllerRange>
  <!-- AutomationTarget, ModulationTarget, LomId, etc. also present -->
</MacroControls.0>
<MacroDisplayNames.0 Value="FX1" />
<NumVisibleMacroControls Value="16" />
```

These nodes occur in the inspected [Drum Rack fixture][fixture-rack]. `MacroDefaults.0` and `AreMacroControlsVisible` are also handled by [Device-Creator's configuration script][macro-config]. Dot suffixes are literal element names; scope edits to the intended rack to avoid changing nested rack macros.

For plugin macro mappings, [Device-Creator's mapping writer][macro-writer] explicitly generates this relationship (abridged, not copied implementation code):

```xml
<PluginParameterSettings Id="0">
  <ParameterId Value="101" />
  <Type Value="PluginFloatParameter" />
  <MacroControlIndex Value="0" />
  <MidiControllerRange>
    <MidiControllerRange Id="0"><Min Value="0" /><Max Value="1" /></MidiControllerRange>
  </MidiControllerRange>
</PluginParameterSettings>
```

**Seen-in-open-source**, not an independently load-tested preset. `101` is that script's chosen plugin parameter ID, **not a universal first parameter**. Its hard-coded IDs and assumptions should not become our algorithm. A `MidiControllerRange` alone is not evidence of a macro mapping: ordinary parameters also contain this node. The nested form above and native-device mapping forms need real before/after fixtures. Mapping ranges are in the target's stored domain, not automatically the user's display units.

For drums, verified preset nodes are `DrumGroupDevice`, **`DrumBranchPreset`**, `ReceivingNote`, `DevicePresets`, `SampleRef/FileRef/Path`, `RelativePath`, `RelativePathType`, `OriginalFileSize`, and `OriginalCrc`. The requested bare **`DrumBranch` was not present** in the inspected `.adg` fixtures; do not confuse a Set branch representation with preset wrappers. `OriginalSimpler` is the concrete Simpler XML device tag in the inspected `.adv`; the API class name is `SimplerDevice`. Current Device-Creator input racks can contain **`DrumCell`**, so a parser restricted to Simpler will miss samples. Sources: [rack][fixture-rack], [Simpler][fixture-simpler], [current bundled rack][fixture-current], [template sample replacement][sample-writer].

For **Audio Effect Rack**, `AudioEffectGroupDevice` is the expected identifier, but **no actual Audio Effect Rack XML fixture was verified in this review**. Its complete `AudioEffectBranchPreset` / chain / native mapping structure remains a sample gate. The inspected editor reads `ReturnBranchPresets > AudioEffectBranchPreset` for Drum Rack returns; that does not validate arbitrary FX rack creation. [ADG editor source][adg-editor-source].

For plugins, an actual [Live 9.1.7 Set fixture][fixture-vst] contains:

- `PluginDevice/PluginDesc/VstPluginInfo`: `FileName`, `PlugName`, numeric `UniqueId`, parameter/program counts, and `Preset/VstPreset`.
- `PluginFloatParameter`: `ParameterName`, `ParameterId`, `VisualIndex`, `ParameterValue/Manual`, plus automation/modulation targets and events. Some entries have `ParameterId="-1"` and empty names: not every slot represents a usable configured parameter.
- [DawVert's Ableton reader][dawvert-input] separately handles `Vst3PluginInfo`, preset `Uid/Fields.0` … `Fields.3`, `ProcessorState`, and `ParameterList` entries carrying IDs, names, and values. It also handles VST2 `Buffer` state. This is **seen-in-open-source**, not a verified Live 11/12 VST3 fixture here.

**Implication:** scalar exposed values are only part of plugin state. Opaque state may encode presets, routing, oversampling, and controls missing from the parameter panel. Preserve blobs untouched; do not fabricate them or assume a normalized number is a physical setting. AU XML identity/state was **not verified** here. VST2, VST3, and AU variants must not be merged merely by display name.

### Projects worth studying; licensing boundary

| Project | Useful evidence / limitation | License observed |
|---|---|---|
| [ben-juodvalkis/Ableton-Device-Creator][creator] | Templates, sample references, macro names/values, plugin mapping edits, drum/Simpler generation. Broad archived scripts coexist with current code; inspect provenance and avoid assuming every script is tested. Third-party template content may contain commercial sample references. | **MIT** repository license; no implication that referenced samples are redistributable. |
| [offlinemark/dawtool][dawtool] | Gzip/XML Set parsing and Live 12 regression fixtures. Primarily project/marker/automation analysis, not a complete rack authoring SDK. | **BSD-3-Clause except `flstudio_core.py` GPLv3**; repository LICENSE explicitly warns that the combined package entails GPL unless excluded/replaced. |
| [SatyrDiamond/DawVert][dawvert] | Concrete VST2/VST3 state and identity readers, native device/sample structures, Ableton writer. Cross-DAW conversion is not proof of lossless round-trip preservation. | **GPL-3.0**. |
| [GinoLucianoRojo/ableton][gino] | Actual legacy plugin fixture and parser; useful historical comparisons, not 11/12 compatibility proof. | No repository license identified; do not copy code/assets. |
| [ununu-p2p/als-parser][ununu] | TypeScript XML/FileRef handling and Live 10 fixtures. | No repository license identified; do not assume package availability grants reuse rights. |
| [martincr/adg-editor][adg-editor] | Scoped pad/macro edits and GM note table. Its generated default XML uses a hand-written version header and sparse structure; browser parsing/serialization does not prove Live loadability. | No repository license identified. |
| [Ziforge/ableton-liveapi-tools][ziforge] | Live bridge/runtime limitations, not an `.als` authoring library. | **GPL-3.0**. |

No code is proposed for copying. Write our implementation independently from documented behavior and observed file facts. Do not vendor unlicensed fixtures, commercial presets, or GPL implementation into the project's MIT codebase. Record specific source commits and fixture provenance when implementation begins.

## 3. Standard Drum Rack layout

**Documented:** a Drum Rack has a pad for each of the 128 MIDI notes; its viewport shows a subset and can scroll. Pad assignment is the MIDI note, not screen position. Both [Live 11][manual11-racks] and [Live 12][manual-racks] describe this model. Multiple chains can receive one note. MIDI note-number conventions are stable; octave-label conventions differ between applications.

**Seen-in-open-source:** [ADG editor's GM layout][adg-editor-source] uses notes 36–51. This matches the conventional General MIDI percussion assignments below. This review did not retrieve a working first-party GM specification URL, so it is corroborating implementation evidence, not a formal MIDI-spec citation. Ableton's familiar C1 kick convention corresponds to MIDI 36; **not every factory/custom rack guarantees GM assignments**, and the manual does not mandate kick on C1.

**Proposed default (inferred product choice):** use a named `gm-36-51` profile, bottom row notes 36–39, next row 40–43, then 44–47, top row 48–51. Store numeric notes as canonical; show Live octave names after runtime confirmation.

| Notes | Roles, left to right |
|---|---|
| 36–39 | Kick, side stick, acoustic snare, clap |
| 40–43 | Electric snare / second snare, low floor tom, closed hi-hat, high floor tom |
| 44–47 | Pedal hi-hat, low tom, open hi-hat, low-mid tom |
| 48–51 | High-mid tom, crash, high tom, ride |

Keep GM 35 available for a second acoustic kick and additional GM notes for extended percussion. An optional dance profile may put extra kicks/snares in convenient pads, but must have an explicit profile and MIDI remap table. GM compatibility does not guarantee arbitrary source-rack MIDI transfers: inspect the source's receiving-note map first. Choke open/closed hats intentionally; preserve sample tuning, start/end regions, and one-shot playback behavior separately from pad note assignment.

## 4. Browser color tags, labels, and storage

**Documented:** Collections provide seven color labels; a browser item can be assigned via context menu or keys 1–7, with 0 clearing assignments. Live 12 additionally has browser tags/filter groups and saved searches; these are distinct from Collections and from track/clip colors. [Live 12 browser manual][manual-browser]. Collections also predate Live 11; do not treat them as a new 11-only format.

**Seen-in-open-source:** [merge-ableton-favorites][favorites] describes XMP/RDF/XML files under **`Ableton Folder Info`**, including pack-related metadata filenames. Its implementation merges existing XMP files; this is evidence against assuming that a single preferences/database row is the sole Collections source of truth. It does **not** establish plugin identity keys, all metadata locations, Live version compatibility, or safe hot reload.

| Location | What is known / what to discover |
|---|---|
| User Library, both platforms | Search its actual configured root for `Ableton Folder Info` and XMP files. Conventional roots: Windows `%USERPROFILE%\Documents\Ableton\User Library`; macOS `~/Music/Ableton/User Library`. Libraries can be relocated; these are discovery candidates, not fixed metadata paths. |
| Other Places / Packs | Existing XMP may be associated with library/pack locations. Do not assume the User Library alone contains every Collections assignment. |
| Windows preferences | `%APPDATA%\Ableton\Live <version>\Preferences\` is the usual versioned configuration directory. `Library.cfg` is a library-location discovery candidate; no verified plugin Collections writer/schema was found in it. |
| macOS preferences | `~/Library/Preferences/Ableton/Live <version>/`. Same distinction between library configuration and item metadata. |
| Browser database/cache | Common discovery roots include `%LOCALAPPDATA%\Ableton\Live Database\` and `~/Library/Application Support/Ableton/Live Database/`. Exact current filenames/schema and whether a plugin assignment is authoritative there were **not verified**. Do not update database tables based on these path hints. |

Path conventions above are **inferred discovery hints except where corroborated by the recent-Set utility below**, not a tested inventory of current 11/12 installations. Ableton support pages about preferences could not be read in this run (HTTP 403); plugin-specific `FavoritesInfo` file paths were not verified. Avoid inventing a single `FavoritesInfo.cfg` writer.

**API verdict:** no supported `set_collection`, plugin favorite/color, or Live 12 tag-write API was found in the inspected official LOM / Python browser inventory. A track color setter cannot solve UC2. File edits might be feasible (**inferred**), but need separate before/after metadata captures for a plugin, a preset, and a sample, including Live restart/reindex tests. Initial product can generate ranked recommendations; do not advertise automatic plugin color tags until that gate passes.

## 5. Recent projects and defensible usage counts

**Documented:** Live offers File → Open Recent Set. [Managing Files and Sets][manual-files]. **Seen-in-open-source:** [ableton-open-last-set][recent] extracts paths from binary **`Preferences.cfg`**, splitting around `FileRef`; its source targets macOS and contains commented Windows paths. It explicitly describes a fragile printable-character heuristic that breaks Unicode/emoji. This is not a reliable parser or a current 11/12 specification.

- macOS candidate: `~/Library/Preferences/Ableton/Live <version>/Preferences.cfg`.
- Windows candidate: `%APPDATA%\Ableton\Live <version>\Preferences\Preferences.cfg` (the utility's Windows branch is commented out, not tested evidence).
- `Library.cfg` can help locate library roots; **no evidence found that it is the authoritative recent-project list**. A recent-items binary schema and list ordering for current versions remain unknown.

**Recommended first version (inferred):** scan user-selected project roots for `.als`; combine saved mtime, optional extracted recent-list hints, and explicit date filters. Exclude/deduplicate backups and alternate saves before scoring. Do not imply mtime is last-opened time. Preferences parsing is an optional adapter, not a prerequisite for UC1. Genre is not reliably encoded: use owner-supplied folders/labels or an explicitly uncertain classifier.

Extract recursively through nested device chains:

| Entity | Fields and counting rule |
|---|---|
| Set / track / chain | Source-relative Set ID, saved version, modified time, track and nested device paths; preserve occurrence IDs for provenance. Redact names in published fixtures. |
| Native device | XML tag/class, instance name, active state; count distinct projects and instance occurrences separately. |
| Plugin | Format + VST2 `UniqueId`, VST3 UID, or AU identity once validated; vendor/name/version/platform when available. Keep device rename distinct from plugin identity. Source evidence: [legacy VST fixture][fixture-vst], [VST3 reader][dawvert-input]. |
| Sample | `SampleRef/FileRef` absolute/relative paths, size/CRC hints, sample region, sampler type, receiving note, clip references. Resolve relative paths against the correct project/library context; CRC/size alone are not collision-proof identity. Hash local content optionally. [Sample fixture][fixture-simpler], [FileRef parser fixtures][ununu]. |
| Usage score | Distinct-project presence, total instances, most recent saved use; optionally active references and note-trigger evidence. Return the raw metrics alongside any ranking. |

**Critical UC1 distinction:** a referenced sample is not necessarily *actually used*. An untriggered pad, muted chain, disabled device, alternate take, or unused clip still persists in XML. In sampler racks, correlate MIDI notes, chain key/velocity/selector ranges, receiving notes, and sample zones; account for Session and Arrangement separately. Dynamic routing, randomization, automation, MIDI-generating devices, and internal plugin samplers can prevent proof from static XML. Classify results as `referenced`, `potentially_triggered`, or `confirmed_by_runtime`, not a single “used” boolean.

Duration and file names can suggest drum one-shots, but neither proves them. Preserve sample crop/warp/tuning settings; a region of a long recording can be a one-shot. Plugin-internal drum samples may only be embedded in opaque state and unavailable to the generic scanner. No owner audio needs to be uploaded to build a local index.

## 6. Hardware → owned emulations / alternatives

No comprehensive, clearly licensed structured dataset was verified. A public list is not automatically reusable data.

- [ApexArtist/Acustica][acustica-list] is a public Markdown hardware-inspiration list, but **no license identified**, and several claims use wording such as “or similar.” Treat as research leads, not facts to import or an authoritative crosswalk.
- Manufacturer pages explicitly identify models: [Universal Audio 1176 collection][ua1176] names Rev A, Rev E, and AE; [Teletronix LA-2A collection][uala2a] identifies optical leveler emulations. **Documented vendor claims** are good evidence for individually curated factual relationships. Product-page prose/images remain copyrighted; no bulk dataset reuse permission established.
- Role-based alternatives (FET compressor, optical leveler, broad EQ) are **inferred musical recommendations**, not direct emulations. Keep those relation types separate. Artist-chain articles may omit gain staging, revisions, parallel routing, and automation; preserve citations and gaps.

Use a small independently authored JSON/YAML catalog, with an explicit data license (for example CC0 for original factual records), not a dependency on a scraped catalog:

```json
{
  "hardware_id": "ua:1176:rev-e",
  "plugin_key": {"vendor": "Universal Audio", "product": "1176LN Rev E"},
  "relation": "emulation",
  "role": "fet_compressor",
  "evidence_url": "https://www.uaudio.com/uad-plugins/compressors-limiters/1176-collection.html",
  "confidence": "documented",
  "settings_profile": null
}
```

Keep local inventory separate: format/runtime plugin ID, exact version, browser URI, `installed`, `loadable`, and owner-confirmed `owned`. Parameter profiles should identify plugin version + parameter IDs/names, units, internal domain, conversion/calibration, and validated limits. Do not infer ownership from old Sets. A hardware attack knob, ratio switch, or input level may not translate linearly to a plugin value; show unmapped controls rather than silently guessing. Building a safe suggestion planner is possible now; universal exact settings translation is not established.

## 7. Existing bridges/MCP projects and pitfalls

| Project | Evidence and useful coverage | Gotcha / implication |
|---|---|---|
| [ahujasid/ableton-mcp][upstream] | MIT; Python Remote Script + MCP server, JSON/TCP, browser discovery/loading, tracks/clips/notes/transport and inspection. [Handshake source][handshake] provides script compatibility handling. | Current source has telemetry/dataset components; do not import that behavior into this no-telemetry project. Current bridge binds loopback and queues many mutations, but browser/read paths must also be audited for worker-thread Live access. Tests and `hasattr` guards do not prove undocumented methods exist. `_map_rack_magnitude` specifically fails without `macro_map`. |
| [Ziforge/ableton-liveapi-tools][ziforge] | GPL-3.0; 220 advertised tools; socket → command queue → `update_display()` → response queue. Claims Live 11 compatibility with capability detection. | README explicitly lists operations that return unsupported on its reported Live 12.4 test, including track grouping, freeze/flatten, annotations, follow-actions. These are the author's runtime reports (**seen-in-open-source**), not our verification or blanket proof about device grouping. Tool count overstates actionable capability if unsupported stubs are counted. |
| [ideoforms/AbletonOSC][osc] | MIT; non-MCP Remote Script with substantial song/track/clip/device getter/setter coverage and listeners; useful reference for regular control-surface servicing. | OSC is a different transport/security model; not evidence of browser tagging, macro creation, arbitrary plugin Configure, or safe remote exposure. Validate version-specific note APIs and nested device addressing. |

Recommended protocol decisions (**inferred**):

1. Loopback bind; authenticated session token where practical; no arbitrary Python/eval/shell commands. A local unauthenticated socket still accepts commands from other local processes. Remote access should require a separately secured transport.
2. Explicit message framing (length prefix or newline-delimited JSON), size limits, request IDs, protocol/capability handshake, structured unsupported errors. TCP `recv()` is not a message boundary.
3. Queue **all** Live access; bound queues and per-tick work. Treat browser scans as incremental jobs; do not recursively walk the entire library on every name lookup. Invalidate URI caches after refresh.
4. Separate “accepted,” “executed,” and “verified.” A load request returning without exception is not proof that the intended plugin/pad exists. Snapshot device topology before/after; preserve selection/hotswap state deliberately.
5. Re-resolve object references after topology changes. Track/device numeric indices drift after insertion/deletion; validate identity immediately before mutations. Never retry a mutation automatically just because the caller timed out.
6. Validate sample/preset paths against configured roots; parse XML without external entities, impose decompression limits, preserve unknown XML and opaque plugin state. Use temporary outputs and atomic replacement only for files the tool owns.

## 8. Risks, build order, and smallest useful sample pack

**Highest risks:** unsupported macro/grouping operations; browser target semantics; plugin state and configured-parameter coverage; version-dependent XML; conflating stored sample references with audible use; Collections metadata synchronization. Natural-language planning is not the main feasibility bottleneck.

Recommended order, with explicit acceptance gates:

1. **Read-only bridge + capabilities:** exact Live/protocol version, tracks/devices/parameters, browser roots, nested addressing. Prove every Live call runs through the main-thread queue; verify timeout/disconnect behavior.
2. **Offline reader + local usage index:** gzip/XML detection, version headers, nested devices, sample/plugin identities, deduplicated project metrics. Use public fixtures for parser tests; no claim of writer compatibility yet.
3. **Live parity and stack creation:** transport, scenes/tracks/clips/notes, native insertion where supported, resolved browser-item loads. Read back order and identity; handle plugin load failures without duplicating devices.
4. **Drum Rack generator:** start with owner-created target-version Simpler template, GM profile, a few synthetic samples. Load, trigger each note, save, reopen, and compare references/settings. Keep 11 and 12 templates separate; do not ship a 12.3/DrumCell template as an 11-compatible rack.
5. **Rack/macro proof of concept before broad UC4:** transform a saved copy containing native effects; demonstrate named macros, multiple targets, reversed/restricted ranges, save/reopen. Then test plugin opaque-state preservation and existing automation/routing. Only advertise live “group this chain” after a state-capture/import route is proven.
6. **Hardware matching/settings:** small sourced catalog, local inventory, versioned parameter adapters. Start with a few owned, configured plugins and show omissions.
7. **Collections experiment:** isolated metadata before/after diff, plugin IDs, restart/reindex/rollback. If it fails, retain ranked tag recommendations and state automatic UC2 is unsupported. Do not let this block the other features.

### Request when runtime validation begins

No owner files are needed to begin steps 1–3's implementation. The smallest useful synthetic pack is:

| Item | Exact contents / reason |
|---|---|
| One **Audio Effect Rack `.adg`** | Two native effects (e.g. Utility + Reverb), two renamed macros; macro 1 maps two targets with different ranges, macro 2 maps a restricted or reversed range. Include a short note of UI ranges/units and a screenshot or written mapping table. Save an unmapped version too for a controlled XML diff. |
| One empty/default **Drum Rack `.adg`**, plus one populated version | Same rack before/after adding two self-made short WAVs at notes 36 and 38, named pads, intentional choke setting. Use Simpler first; add a separate DrumCell example if testing 12.3 behavior. This isolates wrappers, sample refs, and pad mapping. |
| One small **`.als`** | One MIDI drum clip triggering one of those samples while another pad remains unused; one audio clip; one native FX chain; one nested rack; one configured plugin. Save once with an intentionally muted/unused item to test counting semantics. Include a copied version with its FX already grouped for a before/after comparison. |
| One configured **VST3 `.adv`**, before/after one parameter change | Prefer a freely available plugin; expose two named controls through Configure. Record plugin vendor/version, format, parameter names and displayed values. Tests parameter IDs, scalar values, and opaque state. VST2 and macOS AU pairs are additional fixtures if those formats will be supported. |
| Collections metadata diff | With Live closed, capture candidate XMP/prefs files; open Live, tag **one plugin** with an otherwise unused Collection color, close, capture again. Include the selected plugin identity and collection number. Also do one sample/preset control case if feasible. Do not send the full database/preferences directory initially. |
| Recent-file diagnostic, optional | First provide exact Live version and a locally generated redacted list of candidate paths/encodings. A full `Preferences.cfg` is unnecessary and potentially private. Request narrowly scoped byte excerpts only if implementing the adapter. |
| `.alc`, optional | One short synthetic MIDI clip saved with a simple device, if clip preset import/export is in scope. Needed to resolve the unverified container details. |

For declared Live 11 compatibility, obtain equivalent rack/Set fixtures **saved by Live 11**, plus the exact targeted Live 12 release; newer-file headers must not be rewritten to pretend backward compatibility.

**Anonymization:** construct a new throwaway project with neutral track/clip/preset names, synthetic recordings, and no commercial sample/audio content. Use a local neutral directory; Collect All and Save only for those synthetic files. Review XML paths, annotations, author/creator metadata, source-context history, and plugin state for personal strings. Preserve structural IDs and version attributes. Opaque plugin blobs can contain names/paths; a fresh free-plugin instance is safer than blindly redacting bytes. For metadata diffs, extract only changed records after a local review. Keep real project paths and file hashes local; do not publish the owner's corpus or copied vendor presets as fixtures.

## Unknowns that only a real Live install can answer

- Exact Python browser capabilities and import/selection/hotswap behavior in each supported 11/12 release; whether generated presets become discoverable without restart and whether nested target loading is deterministic.
- Whether any specific installed release offers a working undocumented macro-map/name or grouping API; official documentation and upstream guarded attempts do not establish one.
- Whether our generated `.adg`/`.adv` opens, sounds correct, survives save/reopen, and preserves hidden state. Valid XML is insufficient.
- Native Audio Effect Rack mapping XML, display-unit conversion, macro 9–16 behavior, one-to-many/reversed ranges, automation preservation, and external sidechains during grouping.
- Actual plugin Configure exposure, stable IDs, physical-unit scaling, missing/license dialogs, VST2/VST3/AU differences, and opaque-state portability.
- Authoritative plugin Collections metadata location/schema, notification/reindex requirements, concurrent-edit safety, and Live 12 custom-tag storage. A sample alone cannot prove a safe write workflow.
- Current recent-Set binary encoding/order, relocated library paths, Unicode behavior, and exact `.alc` wrappers.
- How closely static “potentially triggered” usage matches audible playback in realistic Sets with MIDI generators, routing, round robin, internal plugin samples, and automation.

### Sources

[track]: https://docs.cycling74.com/apiref/lom/track/
[chain]: https://docs.cycling74.com/apiref/lom/chain/
[rack]: https://docs.cycling74.com/apiref/lom/rackdevice/
[device]: https://docs.cycling74.com/apiref/lom/device/
[parameter]: https://docs.cycling74.com/apiref/lom/deviceparameter/
[pad]: https://docs.cycling74.com/apiref/lom/drumpad/
[drumchain]: https://docs.cycling74.com/apiref/lom/drumchain/
[clip]: https://docs.cycling74.com/apiref/lom/clip/
[simpler]: https://docs.cycling74.com/apiref/lom/simplerdevice/
[browser]: https://midiremotescripts.structure-void.com/reference/live12/Live.Browser.runtime/
[runtime-rack]: https://midiremotescripts.structure-void.com/reference/live12/Live.RackDevice.runtime/
[runtime-simpler]: https://midiremotescripts.structure-void.com/reference/live12/Live.SimplerDevice.runtime/
[manual11-racks]: https://www.ableton.com/en/live-manual/11/instrument-drum-and-effect-racks/
[manual-racks]: https://www.ableton.com/en/live-manual/12/instrument-drum-and-effect-racks/
[manual-plugins]: https://www.ableton.com/en/live-manual/12/using-plug-ins/
[manual-devices]: https://www.ableton.com/en/live-manual/12/working-with-instruments-and-effects/
[manual-browser]: https://www.ableton.com/en/live-manual/12/working-with-the-browser/
[manual-files]: https://www.ableton.com/en/live-manual/12/managing-files-and-sets/
[creator]: https://github.com/ben-juodvalkis/Ableton-Device-Creator
[fixture-rack]: https://github.com/ben-juodvalkis/Ableton-Device-Creator/blob/main/templates/input_rack.adg
[fixture-rack123]: https://github.com/ben-juodvalkis/Ableton-Device-Creator/blob/main/templates/drum-racks/Drum%20Rack%20Template.adg
[fixture-current]: https://github.com/ben-juodvalkis/Ableton-Device-Creator/blob/main/src/ableton_device_creator/templates/input_rack.adg
[fixture-simpler]: https://github.com/ben-juodvalkis/Ableton-Device-Creator/blob/main/templates/simpler-template.adv
[macro-config]: https://github.com/ben-juodvalkis/Ableton-Device-Creator/blob/main/archive-v2-scripts/macro-mapping/cc-control/configure_drum_rack_macros.py
[macro-writer]: https://github.com/ben-juodvalkis/Ableton-Device-Creator/blob/main/archive-v2-scripts/conversion/adg-converter/apply_macro_mappings.py
[sample-writer]: https://github.com/ben-juodvalkis/Ableton-Device-Creator/blob/main/archive-v2-scripts/drum-racks/creation/create_from_template.py
[dawtool]: https://github.com/offlinemark/dawtool
[dawvert]: https://github.com/SatyrDiamond/DawVert
[dawvert-input]: https://github.com/SatyrDiamond/DawVert/blob/main/plugins/input/r_ableton.py
[gino]: https://github.com/GinoLucianoRojo/ableton
[fixture-vst]: https://github.com/GinoLucianoRojo/ableton/blob/master/test/plugins.als
[ununu]: https://github.com/ununu-p2p/als-parser
[adg-editor]: https://github.com/martincr/adg-editor
[adg-editor-source]: https://github.com/martincr/adg-editor/blob/main/src/lib/adg.ts
[favorites]: https://github.com/MedicodiBiscotti/merge-ableton-favorites
[recent]: https://github.com/L1fescape/ableton-open-last-set/blob/main/get_recent_set.py
[acustica-list]: https://github.com/ApexArtist/Acustica
[ua1176]: https://www.uaudio.com/uad-plugins/compressors-limiters/1176-collection.html
[uala2a]: https://www.uaudio.com/uad-plugins/compressors-limiters/teletronix-la-2a-collection.html
[upstream]: https://github.com/ahujasid/ableton-mcp
[upstream-script]: https://github.com/ahujasid/ableton-mcp/blob/main/AbletonMCP_Remote_Script/__init__.py
[handshake]: https://github.com/ahujasid/ableton-mcp/blob/main/MCP_Server/script_handshake.py
[ziforge]: https://github.com/Ziforge/ableton-liveapi-tools
[osc]: https://github.com/ideoforms/AbletonOSC
[osc-manager]: https://github.com/ideoforms/AbletonOSC/blob/master/manager.py
