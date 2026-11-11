# v2 fast-track final proof (2026-11-11 10:06)

- Live version: 12.2.0
- Result: exit 1
- Coverage gaps: none
- Log.txt: C:\Users\ZECHS\AppData\Roaming\Ableton\Live 12.2\Preferences\Log.txt
- Ledger: docs/release/v2-fast-track-ledger.json

| Scenario | Phase | Status | Checks | Failures |
|---|---|---|---:|---|
| control-hello | connection | pass | 3 |  |
| clips-fixture | shared_fixture | pass | 1 |  |
| control-fixture | shared_fixture | pass | 10 |  |
| dev-fixture | shared_fixture | pass | 4 |  |
| dev-browser | browser_devices | pass | 4 |  |
| dev-extras | browser_devices | unsupported | 1 |  |
| dev-load-audio | browser_devices | pass | 4 |  |
| dev-load-return | browser_devices | pass | 1 |  |
| dev-move | browser_devices | pass | 3 |  |
| dev-params | browser_devices | pass | 6 |  |
| dev-set-devices | browser_devices | pass | 3 |  |
| automation-session | musical_edits | pass | 5 |  |
| clips-create-set-get | musical_edits | pass | 7 |  |
| midi-file-round-trip | musical_edits | pass | 3 |  |
| notes-read-edit | musical_edits | pass | 9 |  |
| control-tracks-mixer | assembly | fail | 2 | control-tracks-mixer#1 live_set_tracks: unexpected refusal ValueError: Error executing tool live_set_tracks: ValueError: targets[0]: output routing type must be |
| dev-chain | assembly | pass | 5 |  |
| dev-chain-on-return | assembly | pass | 1 |  |
| dev-convert | assembly | pass | 1 |  |
| dev-drums | assembly | fail | 6 | dev-drums#7 live_set_drum_pads: unexpected refusal target_occupied: Error executing tool live_set_drum_pads: refused:target_occupied: the destination pad is not |
| dev-fx-rack | assembly | unsupported | 0 |  |
| dev-rack | assembly | pass | 6 |  |
| arrangement-clips | arrangement_control | pass | 8 |  |
| arrangement-cues | arrangement_control | pass | 3 |  |
| audio-clip-edit | arrangement_control | pass | 1 |  |
| control-record-view | arrangement_control | pass | 6 |  |
| control-session-transport | arrangement_control | pass | 13 |  |
| clips-duplicate-delete | safety_destructive | fail | 1 | clips-duplicate-delete#1 live_delete: unexpected refusal not_confirmed: Error executing tool live_delete: refused:not_confirmed: the human did not confirm live_ |
| control-duplicate-delete | safety_destructive | blocked | 0 | needs ['control-undo'] |
| control-undo | safety_destructive | blocked | 0 | needs ['control-tracks-mixer'] |
| dev-delete-device | safety_destructive | pass | 3 |  |
| als-path-escape-refused | offline_mcp | pass | 1 |  |
| als-scan-usage | offline_mcp | pass | 5 |  |
| library-knowledge | offline_mcp | pass | 6 |  |
| mcp-prompts-list-get | offline_mcp | pass | 11 |  |
| mcp-resources-read | offline_mcp | pass | 14 |  |
| organize-labels-roundtrip | persistence_finish | pass | 8 |  |

## Log.txt (AbletonLiveMCP lines)

```
  MidiRemoteScript 1 [Control Surface="AbletonLiveMCP" Input="None" Output="None"]
  MidiRemoteScript 1 [Control Surface="AbletonLiveMCP" Input="None" Output="None"]
2026-11-11T08:17:40.092357: info: Python: INFO:_Framework.ControlSurface:91 - LOG: (AbletonLiveMCP) Initializing...
2026-11-11T08:17:40.092381: info: RemoteScriptMessage: (AbletonLiveMCP) Initializing...
2026-11-11T08:17:40.095480: info: Python: INFO:_Framework.ControlSurface:94 - LOG: (AbletonLiveMCP) AbletonLiveMCP: python modules ctypes=no msvcrt=yes subprocess=yes hmac=yes hashlib=yes secrets=yes
2026-11-11T08:17:40.095505: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: python modules ctypes=no msvcrt=yes subprocess=yes hmac=yes hashlib=yes secrets=yes
2026-11-11T08:17:40.096052: info: Python: INFO:_Framework.ControlSurface:94 - LOG: (AbletonLiveMCP) AbletonLiveMCP: strict config permission check unavailable in this Python (no ctypes); using weaker location/link checks, ACL not verified
2026-11-11T08:17:40.096068: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: strict config permission check unavailable in this Python (no ctypes); using weaker location/link checks, ACL not verified
2026-11-11T08:17:40.097677: info: Python: INFO:_Framework.ControlSurface:97 - LOG: (AbletonLiveMCP) AbletonLiveMCP: listening on 127.0.0.1:9877
2026-11-11T08:17:40.097695: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: listening on 127.0.0.1:9877
  MidiRemoteScript 1 [Control Surface="AbletonLiveMCP" Input="None" Output="None"]
2026-11-11T08:19:39.544826: info: Python: INFO:_Framework.ControlSurface:544 - LOG: (AbletonLiveMCP) Initializing...
2026-11-11T08:19:39.544846: info: RemoteScriptMessage: (AbletonLiveMCP) Initializing...
2026-11-11T08:19:39.547955: info: Python: INFO:_Framework.ControlSurface:547 - LOG: (AbletonLiveMCP) AbletonLiveMCP: python modules ctypes=no msvcrt=yes subprocess=yes hmac=yes hashlib=yes secrets=yes
2026-11-11T08:19:39.547980: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: python modules ctypes=no msvcrt=yes subprocess=yes hmac=yes hashlib=yes secrets=yes
2026-11-11T08:19:39.548548: info: Python: INFO:_Framework.ControlSurface:547 - LOG: (AbletonLiveMCP) AbletonLiveMCP: strict config permission check unavailable in this Python (no ctypes); using weaker location/link checks, ACL not verified
2026-11-11T08:19:39.548566: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: strict config permission check unavailable in this Python (no ctypes); using weaker location/link checks, ACL not verified
2026-11-11T08:19:39.550469: info: Python: INFO:_Framework.ControlSurface:549 - LOG: (AbletonLiveMCP) AbletonLiveMCP: listening on 127.0.0.1:9877
2026-11-11T08:19:39.550491: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: listening on 127.0.0.1:9877
  MidiRemoteScript 1 [Control Surface="AbletonLiveMCP" Input="None" Output="None"]
  MidiRemoteScript 1 [Control Surface="AbletonLiveMCP" Input="None" Output="None"]
2026-11-11T09:37:52.326515: info: Python: INFO:_Framework.ControlSurface:326 - LOG: (AbletonLiveMCP) Initializing...
2026-11-11T09:37:52.326536: info: RemoteScriptMessage: (AbletonLiveMCP) Initializing...
2026-11-11T09:37:52.329356: info: Python: INFO:_Framework.ControlSurface:328 - LOG: (AbletonLiveMCP) AbletonLiveMCP: python modules ctypes=no msvcrt=yes subprocess=yes hmac=yes hashlib=yes secrets=yes
2026-11-11T09:37:52.329376: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: python modules ctypes=no msvcrt=yes subprocess=yes hmac=yes hashlib=yes secrets=yes
2026-11-11T09:37:52.329885: info: Python: INFO:_Framework.ControlSurface:329 - LOG: (AbletonLiveMCP) AbletonLiveMCP: strict config permission check unavailable in this Python (no ctypes); using weaker location/link checks, ACL not verified
2026-11-11T09:37:52.329901: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: strict config permission check unavailable in this Python (no ctypes); using weaker location/link checks, ACL not verified
2026-11-11T09:37:52.331845: info: Python: INFO:_Framework.ControlSurface:331 - LOG: (AbletonLiveMCP) AbletonLiveMCP: listening on 127.0.0.1:9877
2026-11-11T09:37:52.331874: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: listening on 127.0.0.1:9877
  MidiRemoteScript 1 [Control Surface="AbletonLiveMCP" Input="None" Output="None"]
  MidiRemoteScript 1 [Control Surface="AbletonLiveMCP" Input="None" Output="None"]
  MidiRemoteScript 1 [Control Surface="AbletonLiveMCP" Input="None" Output="None"]
2026-11-11T09:38:51.877018: info: Python: INFO:_Framework.ControlSurface:876 - LOG: (AbletonLiveMCP) Initializing...
2026-11-11T09:38:51.877045: info: RemoteScriptMessage: (AbletonLiveMCP) Initializing...
2026-11-11T09:38:51.880351: info: Python: INFO:_Framework.ControlSurface:879 - LOG: (AbletonLiveMCP) AbletonLiveMCP: python modules ctypes=no msvcrt=yes subprocess=yes hmac=yes hashlib=yes secrets=yes
2026-11-11T09:38:51.880386: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: python modules ctypes=no msvcrt=yes subprocess=yes hmac=yes hashlib=yes secrets=yes
2026-11-11T09:38:51.881070: info: Python: INFO:_Framework.ControlSurface:880 - LOG: (AbletonLiveMCP) AbletonLiveMCP: strict config permission check unavailable in this Python (no ctypes); using weaker location/link checks, ACL not verified
2026-11-11T09:38:51.881092: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: strict config permission check unavailable in this Python (no ctypes); using weaker location/link checks, ACL not verified
2026-11-11T09:38:51.882856: info: Python: INFO:_Framework.ControlSurface:882 - LOG: (AbletonLiveMCP) AbletonLiveMCP: listening on 127.0.0.1:9877
2026-11-11T09:38:51.882878: info: RemoteScriptMessage: (AbletonLiveMCP) AbletonLiveMCP: listening on 127.0.0.1:9877
```

## Output

```
info 37 scenarios; 0 registered tool(s) without a scenario
info live 12.2.0; 57 tools listed

### phase 2/9: shared_fixture

== dev-fixture (shared_fixture)
PASS dev-fixture#0 live_create_tracks
PASS dev-fixture#1 live_create_tracks
PASS dev-fixture#2 live_create_tracks
PASS dev-fixture#3 live_create_tracks

### phase 3/9: browser_devices

== dev-browser (browser_devices)
PASS dev-browser#0 live_browser_list
PASS dev-browser#0 live_browser_list complete == True: True
PASS dev-browser#1 live_browser_list
PASS dev-browser#2 live_browser_search

== dev-load-audio (browser_devices)
PASS dev-load-audio#0 live_load_item
PASS dev-load-audio#1 live_get_operation
PASS dev-load-audio#2 live_get_operation
PASS dev-load-audio#2 live_get_operation operations.0.state == 'ready': 'ready'

== dev-params (browser_devices)
PASS dev-params#0 live_get_device_parameters
PASS dev-params#1 live_get_device_parameters
PASS dev-params#2 live_get_device_parameters
PASS dev-params#3 live_set_device_parameters
PASS dev-params#3 live_set_device_parameters status == 'complete': 'complete'
PASS dev-params#4 live_set_device_parameters

== dev-set-devices (browser_devices)
PASS dev-set-devices#0 live_set_devices
PASS dev-set-devices#0 live_set_devices status == 'complete': 'complete'
PASS dev-set-devices#1 live_set_devices

== dev-load-return (browser_devices)
PASS dev-load-return#0 live_load_item

== dev-move (browser_devices)
PASS dev-move#0 live_move_device: refused unsupported as expected
PASS dev-move#1 live_move_device
PASS dev-move#1 live_move_device position == 0: 0

== dev-extras (browser_devices)
PASS dev-extras#0 live_get_device_extras
info dev-extras#1 live_set_device_extras: supported refusal: unsupported: Error executing tool live_set_device_extras: refused:unsupported: devx.preset_select: this object has no 'selected_preset_index' (not applied)

### phase 5/9: assembly

== dev-chain (assembly)
PASS dev-chain#0 live_plan_chain
PASS dev-chain#1 live_build_chain
PASS dev-chain#1 live_build_chain status == 'complete': 'complete'
PASS dev-chain#2 live_build_chain
PASS dev-chain#2 live_build_chain already_built == True: True

== dev-fx-rack (assembly)
info dev-fx-rack#0 live_plan_chain: supported refusal: unsupported: Error executing tool live_plan_chain: refused:unsupported: rack.insert_chain is unsupported: this Live has no insert_chain (not applied)
info dev-fx-rack#1 live_build_chain: skipped: its input came from a supported refusal

== dev-rack (assembly)
PASS dev-rack#0 live_load_item
PASS dev-rack#1 live_get_operation
PASS dev-rack#2 live_get_operation
PASS dev-rack#2 live_get_operation state == 'ready': 'ready'
PASS dev-rack#3 live_get_rack
PASS dev-rack#4 live_set_rack

== dev-drums (assembly)
info dev-drums#0 live_plan_drum_rack: supported refusal: unsupported: Error executing tool live_plan_drum_rack: refused:unsupported: load.drum_pad is quarantined: load aa7d96dfb3cd0ecf had an unknown outcome (not applied)
info dev-drums#1 live_build_drum_rack: skipped: its input came from a supported refusal
PASS dev-drums#2 live_load_item
PASS dev-drums#3 live_get_operation
PASS dev-drums#4 live_get_operation
PASS dev-drums#4 live_get_operation state == 'ready': 'ready'
PASS dev-drums#5 live_get_drum_rack
PASS dev-drums#6 live_set_drum_pads
FAIL dev-drums#7 live_set_drum_pads: unexpected refusal target_occupied: Error executing tool live_set_drum_pads: refused:target_occupied: the destination pad is not empty; clear it first (not applied)

== dev-convert (assembly)
PASS dev-convert#0 live_convert

== dev-chain-on-return (assembly)
PASS dev-chain-on-return#0 live_plan_chain

### phase 7/9: safety_destructive

== dev-delete-device (safety_destructive)
PASS dev-delete-device#0 live_set_devices
PASS dev-delete-device#1 live_delete
PASS dev-delete-device#1 live_delete status == 'complete': 'complete'

### phase 8/9: offline_mcp

== library-knowledge (offline_mcp)
PASS library-knowledge#0 live_knowledge
PASS library-knowledge#0 live_knowledge action == 'search': 'search'
PASS library-knowledge#1 live_knowledge
PASS library-knowledge#1 live_knowledge provenance == 'knowledge_base_reference_data': 'knowledge_base_reference_data'
PASS library-knowledge#2 live_knowledge: refused invalid_request as expected
PASS library-knowledge#3 live_knowledge: refused invalid_request as expected

== als-path-escape-refused (offline_mcp)
PASS als-path-escape-refused#0 live_scan_projects: refused invalid_request as expected

== als-scan-usage (offline_mcp)
PASS als-scan-usage#0 live_scan_projects
PASS als-scan-usage#0 live_scan_projects truncated == False: False
PASS als-scan-usage#1 live_usage_report
PASS als-scan-usage#2 live_usage_report
PASS als-scan-usage#3 live_usage_report

== mcp-prompts-list-get (offline_mcp)
PASS prompts/list has every prompt: missing []
PASS prompts/get arrange_sections
PASS prompts/get build_drum_rack
PASS prompts/get diagnose_connection
PASS prompts/get explain_chain
PASS prompts/get macro_fx_rack
PASS prompts/get mix_check
PASS prompts/get organize_session
PASS prompts/get safe_tweak
PASS prompts/get setup_scene
PASS prompts/get vocal_chain

== mcp-resources-read (offline_mcp)
PASS resources/list has docs://conventions/units
PASS resources/list has docs://safety
PASS resources/list has docs://limits
PASS resources/list has live://session
PASS resources/list has live://tracks
PASS resources/list has knowledge://index
PASS resources/read docs://conventions/units: # Units and conventions
- Indices are 0-based (tracks, scenes, devices, clips, p
PASS resources/read docs://safety: # Safety
- read_only is the default. Writes need "read_only": false in the local
PASS resources/read docs://limits: # Known Live 12.2 limits
- No native macro-mapping API: map macros by hand (righ
PASS resources/read knowledge://index: [{"page":"acoustic-midi-fx","title":"Acoustic MIDI FX and Programming Techniques
PASS resources/read live://session: {"provenance":"live_object_text_untrusted","data":{"can_redo":false,"can_undo":t
PASS resources/read live://tracks: {"provenance":"live_object_text_untrusted","data":{"generation":403555315,"retur
PASS resources/read live://track/0: {"error":"live_get_tracks() got an unexpected keyword argument 'response_format'
PASS resources/read live://capabilities: {"build_id":"Live 12.2 Build: 2025-05-20_1c7a2c5dac","capabilities":{"Live.Clip.

### phase 9/9: persistence_finish

== organize-labels-roundtrip (persistence_finish)
PASS organize-labels-roundtrip#0 live_set_labels
PASS organize-labels-roundtrip#0 live_set_labels status == 'complete': 'complete'
PASS organize-labels-roundtrip#1 live_get_labels
PASS organize-labels-roundtrip#1 live_get_labels set.0.kind == 'song': 'song'
PASS organize-labels-roundtrip#1 live_get_labels global.0.key == 'almcp-final:plugin': 'almcp-final:plugin'
PASS organize-labels-roundtrip#2 live_set_labels
PASS organize-labels-roundtrip#2 live_set_labels status == 'complete': 'complete'
PASS organize-labels-roundtrip#3 live_set_labels: refused name_mismatch as expected
RESULT: FAIL (exit 1): 37 scenarios, 5 failed/blocked, 0 coverage gaps
```
