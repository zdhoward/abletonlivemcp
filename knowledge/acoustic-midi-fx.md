# Acoustic MIDI FX and Programming Techniques (knowledge page)

Synthesized from `research/raw/2026-11-10-acoustic-midi-fx.md` and verified against acoustic instrument virtual emulation treatises (Ample Guitar, MusicLab RealGuitar, Orange Tree Samples), orchestral sequencing manuals, and Sound On Sound acoustic production archives.

Related pages: [acoustic](acoustic.md), [acoustic-songwriting-production](acoustic-songwriting-production.md), [guitar-bass](guitar-bass.md), [vocals](vocals.md).

---

## 1. Scope and how to read this page

- Covers acoustic guitar strum modeling, Travis picking sequencing, upright bass fretless intonation, acoustic percussion humanization, and Live 12 MIDI Tools for folk, Americana, and acoustic singer-songwriter productions.
- Evidence labels:
  - **FACT** = Documented for a specific virtual instrument engine, MIDI specification, or verified score analysis.
  - **CONVENTION** = Universally accepted acoustic virtual instrument programming convention.
  - **OPINION** = Individual producer philosophy or personal sequencing workflow.

---

## 2. Acoustic Guitar Simulation and Strum Mechanics

### 2a. The Anatomy of an Authentic Acoustic Strum (FACT / CONVENTION)
- **Strum Velocity Decay Across Strings**: A physical plectrum loses kinetic energy as it sweeps across 6 acoustic guitar strings:
  - Downstroke: Lowest string (E2) receives peak velocity (105 - 115), decaying progressively across strings down to high E4 (velocity 80 - 85).
  - Upstroke: Highest string (E4) receives the sharpest pick bite (velocity 90 - 100), decaying down towards the low strings (velocity 65 - 75). In realistic playing, upstrokes often brush only the top 3 or 4 strings.
- **Strum Time Offsets (Slope Spread)**:
  - Slow ballad strum: 40 - 65 ms spread across all 6 strings.
  - Moderate rhythm strum: 20 - 35 ms spread.
  - Fast bluegrass chop: 12 - 20 ms spread.
- **Ableton Live 12 Strum MIDI Tool**: Configured with variable tension to simulate the human wrist accelerating through the strum arc.

### 2b. Fingerstyle and Travis Picking Sequencing
- **Alternating Bass vs. Treble Melodies (FACT)**:
  - Thumb Bass Notes (strings 6, 5, 4 on beats 1, 2, 3, 4): Velocity 90 - 105, tight gate lengths (slightly detached/damped).
  - Treble Finger Notes (strings 3, 2, 1 on offbeats): Velocity 65 - 85, sustained gate lengths.
- **Key-Release Noises and Fret Scrapes (FACT)**: Authentic acoustic guitar VSTs map fret squeaks, finger scrape noise, and body thumps to note-off messages or low-velocity keyswitches.

---

## 3. Upright Bass and Acoustic Strings

### 3a. Upright Double Bass Sequencing
- **Fretless Intonation Drift**: Fretless upright bass naturally exhibits slight micro-tonal pitch drift. Adding subtle pitch-wheel automation (+/- 3 to 8 cents) on sustained notes simulates human fingerboard placement.
- **Wide Velocity Dynamic Range**: Vary velocity widely from 40 on soft walking notes to 115 on aggressive string pull/slap transients.

---

## 4. Acoustic Percussion and Humanization Devices

### 4a. Ableton Live Velocity Device (Random Mode)
- Place Live's Velocity device before cajon, shaker, or brush kits:
  - Mode: Random
  - Randomize: +/- 10 to 15
  - Compand: 0.0 (linear response)
  - Prevents repetitive mechanical loop artifacts on constant 16th-note shaker patterns.

### 4b. Groove Pool and Rubato Tempo Curves
- Apply 25% - 40% Groove Pool timing with "Folk" or "Acoustic" swing templates.
- Automate project master tempo with subtle curves (+/- 2 to 4 BPM) during transitions from verse to chorus to emulate human tempo breathing.

---

## 5. Acoustic MIDI Implementation Matrix

| Instrument | MIDI Devices / Tools | Velocity Strategy | Strum / Timing Spread | Articulations / CC |
|---|---|---|---|---|
| **Acoustic Strum** | Live 12 Strum + Velocity | Down: 110->85, Up: 95->70 | Down: 30 ms, Up: 20 ms | Fret squeak keyswitches |
| **Fingerstyle Guitar**| Note Length + Live 12 Connect | Thumb: 95, Treble: 75 | Overlapping notes for drone | Hammer-on legato overlap |
| **Upright Bass** | Pitch Bend (+/- 5 cents) | Wide dynamics (40 to 115) | Loose pocket (pulled late) | Key-off string release |
| **Cajon / Shaker** | Live Velocity (Random +/- 12) | Random range 55 to 110 | Groove Pool swing 20-30% | Alternate hand accents |
| **Folk Piano** | Live Velocity + Note Length | Soft intimate range (45-90) | Unquantized human rubato | CC64 Sustain pedal clearing |
