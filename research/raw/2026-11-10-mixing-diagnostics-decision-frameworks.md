# Audio Mixing Diagnostic Frameworks and Root Cause Analysis: raw evidence (collector track)

Collected 2026-11-10. Sourced from critical listening curricula, sound engineering diagnostic methodologies (Sound On Sound "Mix Rescue"), and top mixing engineer decision processes (Bob Katz, Andrew Scheps, Sylvia Massy, Derek Ali).
Evidence labels:
- **FACT** = Documented for a psychoacoustic law, measurement protocol, or verified diagnostic step.
- **CONVENTION** = Universally accepted professional diagnostic framework.
- **OPINION** = Individual mixer philosophy or personal critical listening habit.

---

## 1. The 4-Tier Diagnostic Hierarchy (Problem Isolation)

### 1a. The "Root-Cause First" Escalation Ladder (CONVENTION / FACT)
When a mix problem is detected (e.g. "the vocal isn't cutting through"), inexperienced mixers reflexively reach for EQ or compression plugins. Professional diagnostic hierarchy resolves problems at the lowest possible tier:
1. **Tier 1: Arrangement & Composition**: Is another instrument playing the same notes in the same octave at the same instant? (Fix: Mute, transpose octave, or stagger phrasing).
2. **Tier 2: Balance & Fader Levels**: Is the element simply too loud or too quiet by 1.5 - 3 dB? (Fix: Fader adjustment or volume automation).
3. **Tier 3: Frequency & Space (EQ & Panning)**: Are two instruments sharing identical frequency space and panning position? (Fix: Complementary EQ cuts, panning separation).
4. **Tier 4: Dynamics & Nonlinear Processing (Compression / Saturation)**: Is the dynamic range of the instrument too wide, causing it to disappear during quiet phrases? (Fix: Fader riding, parallel compression, or gentle leveling).

---

## 2. Critical Diagnostic Tests (How to Analyze Objectively)

### 2a. The Level-Matched Bypass Test (The A/B Verification) (FACT)
- **Psychoacoustic Fact**: The human ear perceives louder audio as having better clarity, punchier bass, and crisper treble. If a plugin adds 1.5 dB of output gain, the mixer will instinctively believe the plugin "improved" the sound, even if the processing degraded the track.
- **The Rule**: Before declaring any processing step successful, match the plugin's output level so that bypassing the plugin produces **zero difference in perceived volume**. If it doesn't sound clearly superior when level-matched, bypass and delete it.

### 2b. The "In-Context" vs. "Solo" Diagnostic Trap
- **The Solo Trap**: EQing an acoustic guitar or snare drum in solo to make it sound "huge, warm, and massive" invariably results in an instrument that overloads the 200-500 Hz region and clashes with the bass and vocal in the full mix.
- **The Diagnostic Rule**: Make 90% of EQ and compression adjustments **with the entire mix playing**. Solo should only be used for 5-10 seconds to detect specific clicks, headphone bleed, hum, or noise artifacts.

### 2c. Static vs. Dynamic Problems (Static EQ vs. Dynamic Treatment)
- **Diagnostic Question**: Is the frequency problem present **all the time** or **only during specific musical moments**?
  - *Static Problem*: Guitar cabinet whistle resonance (present continuously whenever notes are played); 60 Hz hum; microphone capsule presence peak. -> **Treated with Static EQ notch or shelf**.
  - *Dynamic Problem*: Vocal boomy proximity effect (only occurs when the singer leans into the mic on low notes); snare sibilance on crash hits; bass boomy notes on specific frets. -> **Treated with Dynamic EQ, Multiband Compression, or Automation**. (Applying static EQ cuts to dynamic problems leaves the instrument hollow when the problem note is not playing).

---

## 3. Systematic Diagnostic Checklist: Symptom to Root Cause

| Symptom Observed | First False Instinct (Blanket Fix) | Actual Root Cause to Investigate | Targeted Treatment |
|---|---|---|---|
| **Mix lacks punch / drums feel soft** | Slap limiter / bus compressor | Compressor attack too fast (< 10 ms) clamping transients | Slow attack to 30 ms; blend uncompressed transients |
| **Vocal gets buried in chorus** | Boost 3 kHz +4 dB on vocal | Guitars/synths occupying same mid-frequency space | Cut 1-3 kHz on guitars; duck guitar bus by 1.5 dB via vocal sidechain |
| **Muddy, boomy low end** | High-pass everything at 120 Hz | Kick and bass fundamental collision; phase cancellation | Assign dominance (Kick @ 50 Hz vs Bass @ 90 Hz); invert polarity |
| **Mix sounds harsh / fatiguing** | Dark low-pass filter at 8 kHz | Hyped mic capsule; vocal compression without de-essing | Pre-compression de-esser; dynamic EQ notch on harsh peaks |
| **Mix collapses in mono** | Add stereo widener to master | Out-of-phase Haas delays; stereo synth reverbs across sub | Mono low-end below 120 Hz; time-align multi-mics; pan distinct parts |
| **Mix sounds distant / blurry** | Boost highs on every track | Unfiltered reverb tails; 0 ms pre-delay on reverbs | Abbey Road reverb EQ (HPF 400 Hz, LPF 6 kHz); add 30-50 ms pre-delay |
