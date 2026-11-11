# v2 fast-track final proof (2026-11-11 10:24)

- Live version: 12.2.0
- Result: exit 0
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
| control-tracks-mixer | assembly | pass | 7 |  |
| dev-chain | assembly | pass | 5 |  |
| dev-chain-on-return | assembly | pass | 1 |  |
| dev-convert | assembly | pass | 1 |  |
| dev-drums | assembly | unsupported | 18 |  |
| dev-fx-rack | assembly | unsupported | 0 |  |
| dev-rack | assembly | pass | 6 |  |
| arrangement-clips | arrangement_control | pass | 8 |  |
| arrangement-cues | arrangement_control | pass | 3 |  |
| audio-clip-edit | arrangement_control | pass | 1 |  |
| control-record-view | arrangement_control | pass | 6 |  |
| control-session-transport | arrangement_control | pass | 13 |  |
| clips-duplicate-delete | safety_destructive | pass | 2 |  |
| control-duplicate-delete | safety_destructive | pass | 7 |  |
| control-undo | safety_destructive | pass | 5 |  |
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

### phase 5/9: assembly

== dev-drums (assembly)
info dev-drums#0 live_plan_drum_rack: supported refusal: unsupported: Error executing tool live_plan_drum_rack: refused:unsupported: load.drum_pad is quarantined: load aa7d96dfb3cd0ecf had an unknown outcome (not applied)
info dev-drums#1 live_build_drum_rack: skipped: its input came from a supported refusal
PASS dev-drums#2 live_load_item
PASS dev-drums#3 live_get_operation
PASS dev-drums#4 live_get_operation
PASS dev-drums#4 live_get_operation state == 'ready': 'ready'
PASS dev-drums#5 live_get_drum_rack
PASS dev-drums#5 live_get_drum_rack pads.0.chains == 0: 0
PASS dev-drums#6 live_set_drum_pads
PASS dev-drums#7 live_set_drum_pads: refused unsupported as expected
PASS dev-drums#8 live_get_simpler: expected error text 'that device is a InstrumentGroupDevice, not Simpler': ValueError: Error executing tool live_get_simpler: ValueError: that device is a InstrumentGroupDevice, not Simpler (not applied)
PASS dev-drums#8 live_get_simpler: refused ValueError as expected
PASS dev-drums#9 live_set_simpler: expected error text "'device' must be a Simpler": ValueError: Error executing tool live_set_simpler: ValueError: 'device' must be a Simpler (not applied)
PASS dev-drums#9 live_set_simpler: refused ValueError as expected
PASS dev-drums#10 live_get_simpler
PASS dev-drums#11 live_set_simpler
PASS dev-drums#11 live_set_simpler status == 'complete': 'complete'
PASS dev-drums#12 live_get_simpler
PASS dev-drums#12 live_get_simpler device.retrigger == True: True
PASS dev-drums#13 live_set_simpler
RESULT: PASS (exit 0): 37 scenarios, 0 failed/blocked, 0 coverage gaps
```
