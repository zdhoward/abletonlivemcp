# P-29: `.adg` rack preset schema (macro mapping)

Status: offline analysis done (Core Library, Live 12.2d1 files). The real-Live acceptance check
(does Live load a generated copy with its mapping?) is **not run**; the orchestrator runs it
(section 5). T-052 stays gated on that result.

## 1. Sources and method

- `.adg` = gzip of one UTF-8 XML document. Root `<Ableton MajorVersion="5"
  MinorVersion="12.0_12203" Creator="Ableton Live 12.2d1" Revision="...">`, then
  `<GroupDevicePreset>` for a rack.
- Read-only scan of `C:\ProgramData\Ableton\Live 12 Suite\Resources` : 1066 `.adg` files, 1043
  of them under `Core Library\Racks`; 1041 of those carry macro mappings, 17,652 mappings in all.
- The User Library (`D:\Beatz\DAWs\Ableton 12\User Library`) holds **no** `.adg` at all, so no
  saved with/without pair exists on disk. Substitute used: inside one rack, mapped and unmapped
  parameters sit side by side, so the diff is read per parameter (section 3). The true
  save-two-racks diff stays in the orchestrator check.
- Tool: `scripts/adg_schema_probe.py` (stdlib; `--corpus DIR` reproduces the numbers above).

## 2. Rack skeleton (what a rack file contains)

```
Ableton > GroupDevicePreset > Device > <Instrument|AudioEffect|MidiEffect|Drum>GroupDevice Id="0"
  LomId, LomIdView, IsExpanded, BreakoutIsExpanded, On, ModulationSourceCount,
  ParametersListWrapper, Pointee, LastSelectedTimeableIndex, LastSelectedClipEnvelopeIndex,
  LastPresetRef, LockedScripts, IsFolded, ShouldShowPresetName, UserName, Annotation,
  SourceContext, MpePitchBendUsesTuning, OverwriteProtectionNumber
  Branches (empty, or listing)           IsBranchesListVisible, IsReturnBranchesListVisible,
  IsRangesEditorVisible, AreDevicesVisible, NumVisibleMacroControls Value="8"
  MacroControls.0 .. MacroControls.15    (always 16 slots, even when 8 are visible)
  MacroDisplayNames.N, MacroDefaults.N, MacroAnnotations.N, ForceDisplayGenericValue.N,
  MacroColor.N, ExcludeMacroFromSnapshots.N, ExcludeMacroFromRandomization.N, ...
  AreMacroControlsVisible, IsAutoSelectEnabled, ChainSelector, ...
GroupDevicePreset > BranchPresets > <Kind>BranchPreset Id="0" > DevicePresets
  > AbletonDevicePreset Id="0" > Device > <DeviceTag> Id="0" > <Param> ...
```

A macro control is a normal parameter element:

```xml
<MacroControls.3>
  <LomId Value="0" />
  <Manual Value="23" />                      <!-- the macro's current value, 0..127 -->
  <MidiControllerRange><Min Value="0" /><Max Value="127" /></MidiControllerRange>
  <AutomationTarget Id="0"><LockEnvelope Value="0" /></AutomationTarget>
  <ModulationTarget Id="0"><LockEnvelope Value="0" /></ModulationTarget>
</MacroControls.3>
```

Macro name and default live on the rack, not on the control: `MacroDisplayNames.N Value="Rate"`
and `MacroDefaults.N Value="53"`. All `Id` attributes are `"0"` in saved presets (Live assigns real
ids on load), so a generator never has to allocate ids.

## 3. The mapping: a `KeyMidi` block on the mapped parameter

A Macro to parameter mapping is stored **on the target parameter**, not on the macro. The
parameter element gains a `KeyMidi` child that points at the macro by index:

```xml
<SyncedRate>                                   <!-- any parameter of any device in a branch -->
  <LomId Value="0" />
  <KeyMidi>                                    <!-- the mapping -->
    <PersistentKeyString Value="" />
    <IsNote Value="false" />
    <Channel Value="16" />                     <!-- 16 = the macro pseudo channel -->
    <NoteOrController Value="1" />             <!-- zero-based MACRO INDEX (1 = macro 2) -->
    <LowerRangeNote Value="-1" />
    <UpperRangeNote Value="-1" />
    <ControllerMapMode Value="0" />
  </KeyMidi>
  <Manual Value="6" />
  <MidiControllerRange><Min Value="2" /><Max Value="12" /></MidiControllerRange>  <!-- range -->
  <AutomationTarget Id="0"><LockEnvelope Value="0" /></AutomationTarget>
  <ModulationTarget Id="0"><LockEnvelope Value="0" /></ModulationTarget>
</SyncedRate>
```

Evidence (1041 of 1043 rack files, all 17,652 mappings): every mapping has `IsNote=false`,
`Channel=16`, `ControllerMapMode=0`, `LowerRangeNote=UpperRangeNote=-1`, empty
`PersistentKeyString`. `NoteOrController` is 0..15 and matches the macro: in `808 Drifter.adg`
macro 4 is named "Sustain" and maps Drift `Envelope1_Decay` and `Envelope1_Sustain`; macro 7
"Dist Amount" maps `Amp/On`. The corpus contains no `KeyMidi` with another channel, so a real
MIDI-CC mapping would look different (not needed here).

Diff of a mapped vs an unmapped parameter of the same device:

| | unmapped | mapped |
|---|---|---|
| `KeyMidi` | absent | present (7 fields above) |
| `MidiControllerRange` | the parameter's own range | the **macro sweep range**: macro 0 gives `Min`, macro 127 gives `Max` |

`Min > Max` is an inverted mapping (1002 of the 17,652). Boolean parameters (`On`) carry
`MidiCCOnOffThresholds` (`Min 64`, `Max 127`) instead of `MidiControllerRange` (1482 cases); 19
mappings have neither. Mapped values are in the parameter's own units (e.g. seconds,
`SyncedRate` index), not normalized.

## 4. Required fields (minimum for a mapping, inferred)

Per mapped parameter: the whole `KeyMidi` block with Channel 16 and the macro index, plus a
`MidiControllerRange` for non-boolean parameters. Everything else (the `AutomationTarget` /
`ModulationTarget` ids, `LomId`, the rack macro name/default) is boilerplate copied from a real
file. For the rack: 16 `MacroControls.N`, 16 each of `MacroDisplayNames`, `MacroDefaults`,
`MacroAnnotations`, `ForceDisplayGenericValue`, `MacroColor`, and the `Exclude*` flags. Dropping
any is not tested and the safe rule is: **copy a real rack, edit values, never omit elements**.

Not yet known (needs Live): whether Live validates `OverwriteProtectionNumber`, `Revision` or the
`LastPresetRef`/`SourceContext` path (they reference the original file), and whether a mapped
parameter name that does not exist on the device is ignored or rejects the file.

Recommended generation design for T-052: start from a template captured from a rack saved in
Live (a stock Instrument Rack with one chain), keep every element, then (a) set
`MacroDisplayNames.N`/`MacroDefaults.N`/`MacroControls.N/Manual`, (b) insert the `KeyMidi` block
and edit `MidiControllerRange` on each target parameter, (c) write with gzip to a **new** file
under `User Library/AbletonLiveMCP/`. Never touch an existing preset.

## 5. Real-Live check for the orchestrator (kill rule for T-052)

All steps use a temp folder `User Library\AbletonLiveMCP-p29\` (delete it afterwards) and a scratch
MIDI/audio track. No existing user file is modified.

1. Pick `Core Library\Racks\Audio Effect Racks\Performance & DJ\Instant Repeat.adg` (5 mappings).
   `scripts/adg_schema_probe.py PATH` lists them (macro index, parameter, range).
2. Control: copy it byte-for-byte to the temp folder as `control.adg`; refresh the browser
   (`browser.user_library`), load it with `Browser.load_item` onto the scratch track. Expect the
   rack, `has_macro_mappings == True`, `macros_mapped` listing the same macros as the source.
3. Variant A (generated, no mapping): gunzip, remove every `KeyMidi` element in memory with
   `xml.etree`, gzip to `a.adg`, load. Expect it loads and `has_macro_mappings == False`.
4. Variant B (generated, mapping added): from A, add one `KeyMidi` block (Channel 16,
   `NoteOrController` = 0) and a `MidiControllerRange` to one continuous parameter, gzip to
   `b.adg`, load. Expect `has_macro_mappings == True`; set macro 0 to 0 and 127 through
   `DeviceParameter.value` and read the mapped parameter at both ends: they should equal the
   range `Min` and `Max` (use `str_for_value` for display units).
5. Verdict: **go** when B loads and its mapping reads back; **no-go** (T-052 killed) when Live
   rejects or silently drops the mapping (B equals A). Record Live's refusal text, if any.
   Each load is a browser operation: use the existing load helper and delete the scratch track.
