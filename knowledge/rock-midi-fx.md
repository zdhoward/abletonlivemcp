# Rock MIDI FX and Programming Techniques (knowledge page)

Synthesized from `research/raw/2026-11-10-rock-midi-fx.md` and verified against virtual instrument specifications (Superior Drummer 3, Steven Slate Drums, Ample Guitar, Trilian Bass), Sound On Sound sequencing masterclasses, and premier rock production literature.

Related pages: [rock](rock.md), [rock-songwriting-production](rock-songwriting-production.md), [drums](drums.md), [guitar-bass](guitar-bass.md).

---

## 1. Scope and how to read this page

- Covers MIDI effects, sequencing humanization, drum velocity dynamics, guitar/bass strumming mechanics, keyboard/organ controller automation, and Ableton Live MIDI device chains for rock and alternative productions.
- Evidence labels:
  - **FACT** = Documented for a specific plugin engine, MIDI specification, or verified masterclass.
  - **CONVENTION** = Universally accepted rock MIDI programming and humanization convention.
  - **OPINION** = Individual producer philosophy or personal sequencing tip.

---

## 2. Drum Programming and Humanization Techniques

### 2a. Multi-Velocity Hierarchy and Articulations (CONVENTION / FACT)
- **Multi-Velocity Sample Switching**: High-end acoustic rock drum libraries utilize 16 to 32 discrete velocity layers per drum. Static velocities trigger the artificial "machine-gun" effect.
- **Velocity Target Hierarchy**:
  - Primary Kick (Downbeats 1 & 3): Velocity 105 - 120.
  - Weak Beat Kicks (Syncopated offbeats): Velocity 80 - 95.
  - Ghost Kicks: Velocity 45 - 65.
  - Primary Backbeat Snare (Beats 2 & 4): Velocity 110 - 125 (triggers rimshot sample layer).
  - Ghost Snares: Velocity 30 - 55. Placed on 16th-note offbeats immediately preceding or following backbeats.
  - Snare Flams: Two hits separated by 15 - 30 milliseconds; primary hit at velocity 115, grace hit at velocity 75 - 85.
  - Hi-Hat 8th-Note Dynamics: Strong downbeat (velocity 95 - 105) alternating with weaker upbeat (velocity 70 - 80).
  - Hi-Hat Pedal Chokes: Triggering dedicated foot-close MIDI note (note 44) to silence sustaining open hi-hat (note 46).

### 2b. Ableton Live Device Setup: Drum Humanizer Chain (CONVENTION)
- Insert a MIDI Effect Rack before the drum instrument:
  - **Live Velocity Device**:
    - Mode: Random
    - Random: +/- 8 to 12
    - Range: 40 to 127
    - Compand: Parabolic curve (+0.15) to preserve heavy accents while varying intermediate hits.
  - **Live Groove Pool**: Apply 15% - 25% "Rock 8ths" or "Half-Time Shuffle" timing offset with 20% Velocity randomization.

### 2c. Micro-Timing and Pocket Offsets
- **The Bonham Behind-the-Beat Drag (FACT)**: Lock the kick drum firmly to beat 1, but drag backbeat snare hits 8 to 18 milliseconds *late* relative to the grid. Delivers a relaxed, heavy, arena-sized groove.
- **The Punk / Metal Snare Rush (CONVENTION)**: Nudge backbeat snares 4 to 10 milliseconds *early* (ahead of the grid) to impart urgency, aggression, and forward propulsion.

---

## 3. Bass and Guitar MIDI Simulation

### 3a. Virtual Bass Sequencing (CONVENTION / FACT)
- **Monophonic Legato and Note Overlaps**: Overlap consecutive bass notes by 10 to 25 ms. Virtual bass engines (Scarbee, Trilian, MODO Bass) detect the overlap to trigger hammer-ons, pull-offs, or fret glide transitions instead of fresh string plucks.
- **Keyswitch Articulations**: Sequence low keyswitches (C-1 to B-1) on the first 16th note of a riff to toggle between pick attack, fingerstyle, palm mutes, and dead notes.
- **Pitch Wheel Slides**: Automate MIDI Pitch Bend (+/- 2 or +/- 12 semitones) over 60-120 ms entering verse sections to simulate sliding up the neck into the root note.

### 3b. Rock Rhythm Guitar Strumming and Voicings
- **Strum Time Offsets (Downstroke vs. Upstroke) (FACT)**:
  - Downstroke: The plectrum sweeps from low strings to high strings across 25 to 45 ms.
  - Upstroke: The plectrum sweeps from high strings to low strings across 15 to 30 ms (usually brushing only the top 3-4 strings).
- **Ableton Live 12 Strum MIDI Tool**: Set to a positive slope for downstrokes (arpeggiating low to high) and negative slope for upstrokes, with velocity decaying by 15-25% across the sweep.
- **Power Chord Voicing (Root - 5th - Octave)**: Sequence simple 3-note power chord voicings (e.g. E2 - B2 - E3). Full 6-string barre chords through high-gain distortion plugins cause intermodulation mud.

---

## 4. Keyboards and Tone-Wheel Organs

### 4a. Hammond B3 Organ Controller Configuration (FACT)
- **Fixed Velocity**: Authentic mechanical tone-wheel organs are physically non-velocity sensitive. Lock MIDI velocity to a fixed value (e.g. 100 or 127) using Live's Velocity device (Mode: Fixed).
- **Expression Pedal (MIDI CC11)**: Dynamically automate MIDI CC11 (Expression) to control volume swells into choruses and solos.
- **Leslie Speed Switching**: Automate MIDI CC1 (Mod Wheel) or CC64 (Sustain Pedal) between values 0 (Chorale/Slow) and 127 (Tremolo/Fast) directly before chorus downbeats.

### 4b. Piano Voicings and Sustain Pedal (CC64)
- **Sustain Pedal Automation (CC64)**: Clear CC64 (value 0) immediately before every chord change and retrigger (value 127) 20 ms after the downbeat to prevent harmonic mud build-up.
- **Wide Bass Voicings**: Sequence tenths (Root + 10th / octave + 3rd) in the left hand rather than dense triads below C3.

---

## 5. Rock MIDI Implementation Matrix

| Instrument | MIDI Devices / Tools | Velocity Strategy | Micro-Timing | Key Controller / CC |
|---|---|---|---|---|
| **Rock Drums** | Velocity (Random +/- 10) + Groove Pool | Kick: 110-120, Snare: 115-125, Ghost: 35-50 | Snare dragged 8-15 ms late | Hi-hat pedal choke (Note 44) |
| **Rock Bass** | Note Length + Pitch Bend | Velocities 95-115, ghost notes 40-60 | Overlap 15 ms for legato | Keyswitches (palm mute, slide) |
| **Rhythm Guitar**| Live 12 Strum Tool + Note Length | Downstroke 110->85, Upstroke 95->70 | Down: 30 ms spread, Up: 20 ms | Pitch wheel slides into chords |
| **Hammond Organ**| Velocity (Fixed @ 110) | Fixed velocity (zero touch sensitivity) | 100% on the grid | CC11 Expression + CC1 Leslie |
| **Rock Piano** | Velocity (Compand) + Groove Pool | Wide range (50 to 115), accented downbeats| Subtle humanization (10-15%) | CC64 Sustain pedal clearing |
