# Remix plan: owner's finished House track

Status: PLAN ONLY. Nothing has been written to Live. Awaiting owner answers to section 2.
Rule for this project: no self-testing while building. The owner's feedback is the test.
MCP hardening happens when a build step hits a real gap, not before (section 6).

## 1. What the source track is (read-only findings, 2026-11-11)

- 132 BPM, 4/4, Live scale A minor. 26 tracks, 4 returns, 8 empty Session scenes. The song lives
  entirely on the Arrangement: 768 beats (192 bars), vocals/instruments end near beat 640-736.
- Groups: VOX (3 audio tracks) and INSTRUMENTAL > DRUMS / TOP / BOTTOM. Returns: A-VOX Verb,
  B-VOX Delay, C-INSTR Verb, D-INSTR Delay. Master: Utility + Limiter.
- Harmony: A minor. UK Bass is rolling 16ths on A1(45) / E2(52) / F2(53), changing every 16 beats.
  Midy 5th holds A5(81) / E5(76) for 7 beats, 8-beat cells. Core drum track is one note
  (pitch 44) on every beat, 0.25 long (kick-like; map NOT confirmed, see lessons).
- Vocals: "needed you" hook (125 BPM, Dm), "knock me off my feet" hook (128 BPM, Bm), an
  "oh belt ascending" adlib. They are audio clips on the Arrangement, chopped on beat boundaries.
- Structure (beats): Intro 0-60 | Groove 64-128 | Verse/build 128-192 | Voltage section 192-256 |
  Mid 256-384 | Vocal 2 + leads 384-448 | Pre-drop (fill buildup) 448-512 | Drop 513-640 |
  Outro 640-736. Reverse crash 2-6 beats before each major change. Drop-only tracks: Slaps,
  Wobble Sub, Dry Pluck. All melodic tracks end in GHOST//PUMP. Sub is muted.
- Mix state: drums group -3 dB, Core -7, hats/Voltage -9, instrument returns at -inf (sends mostly
  closed), vocal sends -9 dB. Group buses carry Pro-C 2 / Auto Filter; DRUMS also OTT + Pro-L 2.

Not yet read (study phase, section 4 step A): note content of every other clip, bus/FX device
settings, the vocal chain settings, Session automation. Arrangement automation CANNOT be read
on Live 12.2 (capability disabled), so the owner's existing filter/volume moves are invisible to me.

## 2a. Owner decisions so far (2026-11-11)

- Direction: TECH HOUSE (tight, groovy, vocal-chop driven, minimal roster).
- Keep: VOCALS ONLY. New instrumental in the owner's sound; originals not reused.
- Location: SAVE-AS COPY of this Set (owner clicks File > Save Live Set As once; original untouched).
- Still open: tempo/key (proposal: 126 BPM, vocals originally 125/128, tech house sits at 124-128;
  key follows the vocal hooks, so choose after the study phase), length (club ~6 min proposed),
  references.

## 2. Decisions needed from the owner (original list, for reference)

1. Remix direction. Candidates: bass-house / UK garage flip (shuffled 2-step, big sub),
   tech-house (minimal, groovy, vocal-chop driven), melodic/progressive (longer builds, pads),
   or "re-drive": same song, harder club version. Pick one or describe the feel.
2. Keep which parts of the original: vocals only (new instrumental), vocals + a few signature
   sounds (UK Bass, Midy 5th, Airy Saw), or the full instrumental re-arranged?
3. Tempo and key: stay 132 / A minor, or move (vocal hooks are already stretched from 125/128
   and Dm/Bm, so a move costs warping work).
4. Where does it live: new tracks inside this Set (original stays untouched, remix placed at beat
   800+ or in a Save-As copy), or a Save-As copy with the originals muted? A Save-As copy is the
   safest; only the owner can click File > Save Live Set As, so say which you prefer.
5. Length/format target (club extended ~6 min, radio ~3:30, or both) and reference tracks.

## 3. Approach (default if the owner has no strong view)

Work in a Save-As copy so the original is never at risk and I never need destructive operations
(arrangement move/split/duplicate are disabled on 12.2 because they crash Live).
Write all MIDI only after the owner approves note content in text (see lessons: never write notes
unasked). Build the arrangement skeleton first (clip placement + section markers), then fill
sections in energy order, then mix, then automation, then transitions.

## 4. Build phases (each ends with a handoff for owner listening; no self-audition)

A. Study (read-only, safe to do now)
   - Read notes of every MIDI clip once and write a one-page "musical map" (progressions,
     rhythmic cells, per-section instrument roster) to knowledge/ or here.
   - Read device parameters for vocal chain, GHOST//PUMP, group buses, returns; record house
     settings (the "owner preset" values) for reuse.
   - Learn the Nexus kit map for Core/HATS from the Set or ask once (lesson: never infer).
   - Ask the owner for screenshots/descriptions of existing arrangement automation if needed.
B. Blueprint
   - Section map in beats with an energy curve (0-10) and a track-presence matrix.
   - Transition recipes (reverse crash, riser, filter sweep, vocal tail, drum fill) with beat
     positions. Present to the owner; adjust before any write.
C. Skeleton
   - Cue points for every section. Empty/placeholder clips with names and colors on the tracks
     the remix will use. New tracks only where needed, named and colored in the owner's scheme.
D. Fill, in order: drums > bass > main hook/chords > vocals (chops and long phrases) > FX/risers.
   Each fill is one or two batched calls (bridge is ~0.9 s per call, memory note) then stop for
   feedback on a section, not on every clip.
E. Mix: levels, sends, bus processing using the owner's existing chain (GHOST//PUMP, Pro-C 2,
   Wider, Pro-L 2 where present). Stock plugins first for new additions (memory).
F. Automation: 2-3 breakpoint curves, written in Session clips and copied to the Arrangement
   (from_session); arrangement automation itself cannot be written on 12.2.
G. Polish pass driven only by owner feedback.

## 5. How feedback works

- I report what was applied and what could not be verified, then say "ready to preview".
- Read-backs confirm values, not sound. I do not loop playback or audition.
- Every owner correction goes into tasks/lessons.md the same turn.

## 6. Hardening backlog (fix when a build step needs it, with one real-Live check per fix)

| Gap seen so far | Needed by | Plan |
|---|---|---|
| live_get_arrangement errors on the whole Set (too many clips) | Study | Paginate by track group; fix to return partial rows or chunk automatically. |
| Arrangement automation unreadable/unwritable on 12.2 | Phase F | Session-clip automation + from_session copy; document limit. |
| move/split/duplicate arrangement clips disabled | Skeleton, edits | Recreate clips with create_arrangement_clips(replace=True) instead. |
| Take lanes, drum pad loading, device delete/rename unverified | Mix, kit swaps | Verify the one needed capability at first use. |
| Cue points async (unverified) | Phase C | Use the operation poll; verify once when adding section cues. |
| No tool for saving/Save-As | Phase 3 | Owner clicks once, or add if safe. |
| Audio chop creation (warp markers, audio_clip crop) is in the unloaded "editing" toolset | Vocals | Enable the toolset when the vocal phase starts. |

## 7. Open risks

- Existing owner automation is invisible to me; a remix built on it could contradict it.
- Shared Live: one mutation owner at a time; no parallel agents writing to the Set.
- Plugin state (Nexus, Serum 2) is opaque; I can set parameters but not judge patches.
