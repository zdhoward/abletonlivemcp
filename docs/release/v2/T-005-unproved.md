# T-005: unproved in real Live

Real-Live proof of everything else: `docs/release/v2/T-005.md` (PASS, 58 checks).

- `cue` kind: unit-covered only. The lab cue create/delete is off by default (`--with-cues`) because Live applies `Song.current_song_time` late, so a cue lands at the old playhead (observed 4 -> 16, 24 -> 1.5). Needs a two-call goto/toggle design.
- Device-level reorder inside a drum pad chain: `Song.move_device` refused ("Couldn't move device"); the nested-move-out-to-another-track path was proved instead.
- Set-change refusal (`--set-change-wait`): not run; covered by the generation check already proved in T-001.
- Chain/take-lane delete and arrangement-clip/cue move have no 12.2 API; proved via parent deletion/move.
