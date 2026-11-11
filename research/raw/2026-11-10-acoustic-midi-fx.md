# Acoustic MIDI FX and Programming Techniques: raw evidence (collector track)

Collected 2026-11-10. Sourced from acoustic guitar emulation literature (Ample Guitar, MusicLab RealGuitar, Orange Tree Samples), orchestral sequencing treatises, and Sound On Sound acoustic production archives.
Evidence labels:
- **FACT** = Documented for a specific virtual instrument engine, MIDI specification, or verified score analysis.
- **CONVENTION** = Universally accepted acoustic virtual instrument programming convention.
- **OPINION** = Individual producer philosophy or personal workflow.

---

## 1. Acoustic Guitar Simulation and Strum Mechanics

### 1a. The Anatomy of an Authentic Acoustic Strum (FACT / CONVENTION)
- **Strum Velocity Decay Across Strings**: When a pick sweeps across 6 strings, energy dissipates:
  - Downstroke: Lowest string (E2) receives highest impact (velocity 110), fading gradually across intermediate strings down to high E4 (velocity 85).
  - Upstroke: Highest string (E4) receives the sharpest pick bite (velocity 95), fading down towards low strings (velocity 70). Often only hits the top 3-4 strings.
- **Strum Time Offsets (Slope)**:
  - Slow ballad strum: 40 - 65 ms spread across all 6 strings.
  - Energetic rhythm strum: 20 - 35 ms spread.
  - Fast bluegrass chop: 12 - 20 ms spread.
- **Live 12 Strum MIDI Tool**: Employs variable curve and tension to model realistic human hand pick speed accelerating across strings.

### 1b. Fingerstyle / Travis Picking Sequencing
- **Alternating Thumb Bass vs. Finger Melodies**:
  - Thumb bass notes (strings 6, 5, 4 on beats 1, 2, 3, 4): Velocity 90-105, tight gate lengths (slightly muted or detached).
  - Treble finger notes (strings 3, 2, 1 on offbeats): Velocity 65-85, longer sustaining gate lengths.
- **Key-Release Noises and String Squeaks (FACT)**: Virtual guitars trigger dedicated release samples (fret squeak, pick click, finger scrape) mapped to low velocities or note-off velocity messages.

---

## 2. Upright Bass, Strings, and Acoustic Percussion

### 2a. Upright Double Bass Sequencing
- **Pitch-Wheel Intonation Imperfections**: Authentic fretless upright bass never lands on perfect 100% equal temperament pitch. Adding micro pitch-wheel automation (+/- 3 to 8 cents) on sustained notes simulates human fingerboard placement.
- **Velocity Dynamics**: Wide velocity variations (from 40 on soft walking notes to 115 on aggressive slap/pulls).

### 2b. Acoustic Percussion and Humanization
- **Ableton Live Velocity Device (Random Mode)**: Set to Randomize +/- 12 on shaker, cajon, and brush hits to emulate natural hand movement.
- **Groove Pool Humanization**: Setting Groove Pool Timing parameter to 15-30% and Velocity parameter to 20-40% using "Folk" or "Acoustic" swing templates.
