# Pop MIDI FX and Programming Techniques: raw evidence (collector track)

Collected 2026-11-10. Sourced from commercial pop production breakdowns (Max Martin, Ian Kirkpatrick, Greg Kurstin), Sound On Sound sequencing masterclasses, and Billboard chart stem analyses.
Evidence labels:
- **FACT** = Documented for a specific recording, artist session, or verified score analysis.
- **CONVENTION** = Universally accepted commercial pop standard across modern songwriting teams.
- **OPINION** = Individual producer philosophy or personal sequencing technique.

---

## 1. Pop Synth, Bass, and Key Programming

### 1a. Arpeggiator Patterns and Gate Automation (CONVENTION / FACT)
- **Arpeggiator Integration**: Synchronized to 1/8D (dotted 8th) or 1/16th notes.
- **Gate Length Modulation (FACT)**: Automating the Gate length parameter of the MIDI Arpeggiator:
  - Verses: Gate set to 20-35% (tight staccato plucks).
  - Pre-Chorus: Gate smoothly opens from 40% to 80% (creating melodic expansion).
  - Chorus: Gate set to 95-120% (legato, blooming sustained energy).
- **Sync / Rate Retriggering**: Using "Restart on Note" or beat-synced retrigger so the arp pattern always begins exactly on downbeats.

### 1b. Velocity Compression and Dynamics Locking
- **Velocity Normalization (Live Velocity Device)**:
  - In modern radio pop, virtual keyboards, bass synths, and pianos require extreme consistency to cut through dense walls of vocals and sidechained drums.
  - Live Velocity Device configured with: Drive +25%, Compand active, Out Min set to 90, Out Max set to 115. Shaves extreme dynamic spikes while guaranteeing no note drops below audible threshold.

---

## 2. Harmonic and Melodic MIDI Tools

### 2a. Scale Locking and Vocal Harmony Duplication
- **Live Scale Device for Vocal Harmonies**: Duplicating a vocal melody MIDI track into a synth or vocal harmonizer, inserting the Scale device set to the song's root key, and transposing up 3 or 4 scale steps to generate parallel third and sixth harmonies that never go out of key.
- **Chord Memory and Triggering**: Using Live Chord device to generate parallel disco-pop synth stabs (Root + 5th + Octave or minor 7th voicings) on upbeat 16th notes.

### 2b. Modern Live 12 MIDI Transformers (Strum & Ornament)
- **Strum Tool on Clean Electric / Acoustic Guitars**: Adding 15-25 ms spread across chord notes to make keyboard-played guitar chords sound like an authentic acoustic strum.
- **Ornament Tool on Ear Candy**: Adding instant grace notes, trills, and mordents to lead synth lines in post-choruses.

---

## 3. Pop Bass and Drum MIDI Precision

### 3a. Four-on-the-Floor Precision and Bass Syncopation
- **Kick Drum**: 100% rigid grid quantize on quarter notes (1, 2, 3, 4) at constant velocity (120-127).
- **Syncopated Disco-Funk Bass**:
  - Root note hits strictly on 16th-note offbeats.
  - Octave jumps played at higher velocity (110) on upbeat 8ths.
  - Ghost notes sequenced at velocity 40-60 on the 16th note immediately before the kick downbeat.
