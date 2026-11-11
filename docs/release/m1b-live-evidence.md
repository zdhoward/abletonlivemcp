# M1b real-Live evidence (2026-11-10)

Environment: Windows 11, Ableton Live 12 Suite 12.2.0, protocol 2, disposable `Basic` set (never saved).
Head under test: `v1-integration` at `af51473` (fast-forwarded to `main` at `4cd4e4b`, which only adds the README).
Live's embedded Python on Windows has **no `ctypes`** (has `msvcrt`, `subprocess`, `hmac`, `hashlib`, `secrets`);
the Remote Script therefore uses the documented weaker config check there.

Commands used (all against `127.0.0.1:9877`, writes enabled only for the duration of each run):

```
python scripts/live_write_test.py --allow-writes --device-path '["Compressor"]'
python scripts/live_clip_test.py  --allow-writes
python scripts/live_chain_test.py --allow-writes --paths-json @paths.json
python scripts/stdio_error_smoke.py --expect-bridge-text refused:unknown_operation
```

`paths.json`: `{"EQ Eight":["EQ Eight"],"Compressor":["Compressor"],"Saturator":["Saturator"],"Reverb":["Reverb"]}`.
Observed: the four devices are direct children of the `audio_effects` root, so each full path is `[name]`.

| Check | Result |
|---|---|
| Read-only probe: `hello`, `session_info`, `get_transport` authenticated | pass (Live 12.2.0, protocol 2) |
| Wrong secret, HTTP first line, unknown method | refused (`AuthenticationOrProtocolError`, `BadFrame`, `ValueError`), nothing applied |
| Write while `read_only` (no generation) | refused `read_only`, nothing applied |
| `live_write_test` (track, rename, colour, index/unknown/stale refusals, Compressor load, parameter write + readback, out-of-range, occupied load) | pass; load reached `ready` in 4.5 s; repeated 3 more times after the final install, 3/3 pass |
| `live_clip_test` (track, scene, clip, notes, occupied-slot and bad-note rejection) | pass |
| `live_chain_test`, append still refused | partial receipt: stage 0 applied, stage 1 `append_unverified`, later stages not attempted; device list matched the receipt |
| `live_chain_test`, verified append (`select_device` then load, last-position check) | pass: EQ Eight, Compressor, Saturator, Reverb in order, status complete, 0 unknown; repeated after the final install, pass |
| `stdio_error_smoke` | pass: refusal and bridge failure surface as readable text |
| Lease: competing acquire, no-token and wrong-token writes, right-token write, release, expiry | `lease_held` / `lease_held` / applied / released / `lease_expired` |
| Set change (new untitled set) | Live reloaded the script; the old reference was refused `unknown_reference`, nothing applied |

## Defects found by the real-Live run (both fixed)

1. `ctypes` missing in Live's Python made the script fail to load (Live then reset the control-surface slot to None). Fixed by lazy imports and a documented fallback (`89804c2`).
2. A reloaded script restarted `generation` at 1, so a stale client's generation could match a different Set. Fixed: the generation now starts at a random positive number (`af51473`). Verified: a generation-1 write after the fix is refused `stale_generation` and tempo stayed 136.

## Follow-up fixes verified in real Live (2026-11-10, after the table above)

- Missing handler parameter: `set_tempo` without `bpm` now returns `ValueError: missing required parameter 'bpm' (not applied)`.
- Handshake advertises `dispatch.methods` (host accepted it; connection and reads work).
- Reinstalled and relaunched Live 12.2.0; `live_write_test` and `live_chain_test` (EQ Eight, Compressor, Saturator, Reverb) pass again. `read_only` restored to `true`.

## Unproved or not run (do not treat as passed)

- Target reorder refusal and a Live-object identity/equality check beyond the above observations.
- A second *process* competing for the lease (acquire was tried from separate bridge calls only).
- A UI/log observation of responsiveness during a load (no hang was seen, but it was not measured).
- Loading from `plugins`, drum kits or racks, and any device not in the four above.
- One `live_write_test` run aborted with "connection lost" a few seconds after Live launched; it did not recur in 3 reruns and the log showed no new error. Cause not established.
- Only Windows and Live 12.2.0 were exercised; the OneDrive reparse-point case (review finding 13) is untested.
- Python version inside Live was not recorded.
