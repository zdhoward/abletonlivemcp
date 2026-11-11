# Studio Organization, DAW Templates, and Project Management: raw evidence (collector track)

Collected 2026-11-10. Sourced from AES studio standards, professional studio delivery guidelines (Grammy Producers & Engineers Wing guidelines), Sound On Sound mixing workflow retrospectives, and commercial mix engineer masterclasses (Serban Ghenea, Chris Lord-Alge, John Hanes, Bob Horn).
Evidence labels:
- **FACT** = Documented for an industry specification, DAW technical standard, or verified studio delivery agreement.
- **CONVENTION** = Universally accepted professional studio standard across major recording and mixing facilities.
- **OPINION** = Individual producer philosophy or personal organizational preference.

---

## 1. DAW Session Architecture and Template Design

### 1a. Color Coding and Track Ordering Standards (CONVENTION / FACT)
- **Universal Color Coding Hierarchy**: Major mixing facilities adopt consistent color coding across every project to reduce cognitive load and allow instant visual navigation:
  - **Drums & Percussion**: Red / Deep Orange.
  - **Bass (Electric, Synth, 808)**: Yellow / Gold / Brown.
  - **Rhythm Guitars / Acoustic**: Green / Forest Green.
  - **Keyboards / Synths / Piano**: Cyan / Teal / Light Blue.
  - **Lead Vocals**: Deep Blue / Royal Blue.
  - **Backing / Harmony Vocals**: Magenta / Pink / Violet.
  - **FX / Transitions / Ear Candy**: White / Grey / Silver.
  - **Mix Busses / Subgroups**: Purple / Dark Slate.
  - **Pre-Master / Reference Tracks**: Gold / Bright Orange.
- **Track Layout / Flow Order (Top-to-Bottom / Left-to-Right)**:
  - Standard Professional Order: Reference Track -> Drums -> Percussion -> Bass -> Rhythm Guitars -> Lead Guitars -> Keys/Synths -> Backing Vocals -> Lead Vocals -> FX/Risers -> Aux Returns -> Sub-Busses -> Master.

### 1b. Routing Hierarchy and Bus Consolidation (FACT / CONVENTION)
- **4-Tier Signal Routing Architecture**:
  1. *Tier 1: Individual Audio / MIDI Tracks* (Direct instrument capture with corrective EQ / gate).
  2. *Tier 2: Instrument Group Busses* (Drum Bus, Bass Bus, Guitar Bus, Synth Bus, Vocal Bus).
  3. *Tier 3: Auxiliary Effect Sends* (Fixed parallel compressors, shared reverbs, tempo delays).
  4. *Tier 4: Mix Bus / Pre-Master* (Summing all instrument groups and FX returns ahead of final limiter/master out).
- **Benefits of Pre-Master Busses**: Routing all audio to a "Mix Bus" track before the physical stereo output allows instantaneous A/B comparison against commercial reference tracks routed directly to Master 1/2 without passing through mix-bus processing.

### 1c. Fixed Aux Send Architecture
- Pre-configuring 5-6 core auxiliary return channels in every project template:
  - Aux 1: Short Room / Ambience (0.6 - 1.0s decay, for acoustic placement).
  - Aux 2: Lush Plate Reverb (1.8 - 2.5s decay, for snare, guitars, vocals).
  - Aux 3: Slap Delay (analog tape slap, 80 - 130 ms, 0 feedback).
  - Aux 4: Tempo Delay (1/4 or 1/8D ducked delay with sidechain compressor).
  - Aux 5: Parallel Drum Crush (fast FET limiter crushing drum transients).
  - Aux 6: Vocal Spread / Micro-Shift (pitch shifters set to -7 cents L, +7 cents R).

---

## 2. Track Naming Conventions and Cleanliness

### 2a. Abbreviated Prefix Standards (CONVENTION / FACT)
- Raw tracks received from clients often have cryptic or bloated names (e.g. `Audio_Track_1_01_bip`). Professional engineers batch-rename with standardized 2-to-3 character prefixes:
  - `DR_Kick_In`, `DR_Kick_Out`, `DR_Snare_Top`, `DR_Overhead_L`
  - `BS_Bass_DI`, `BS_Bass_Amp`, `BS_808`
  - `GTR_Elec_Rhy_L`, `GTR_Acoustic_Dbl`
  - `SYN_Supersaw_Lead`, `KEY_Grand_Piano`
  - `VO_Lead_Main`, `VO_Lead_Dbl`, `VO_Harm_Hi_L`
  - `FX_Riser_8bar`, `FX_Sub_Drop`

---

## 3. Project Management, File Systems, and Asset Delivery

### 3a. Directory Structure Hygiene (FACT / CONVENTION)
- **Root Directory Organization**:
  ```text
  [Artist_Name] /
    └── [Project_Album_or_Single] /
          ├── 01_Audio_Recordings /
          ├── 02_Session_Files /
          │     ├── SongTitle_v01_Production.als
          │     ├── SongTitle_v02_RoughMix.als
          │     └── Ableton Project Info /
          ├── 03_Reference_Tracks /
          ├── 04_Bounces /
          │     ├── Rough_Mixes /
          │     └── Final_Mixes /
          ├── 05_Stems_Delivery /
          └── 06_Session_Notes_and_Contracts /
  ```
- **Ableton Live Rule: "Collect All and Save" (FACT)**: Whenever adding external audio samples, loops, or recordings, the user must execute *File > Collect All and Save*. This copies all referenced external files directly into the project's `Samples` subfolder, preventing the dreaded "missing media files" error when opening sessions on secondary machines or archival storage.

### 3b. File Naming and Versioning Protocols (FACT / CONVENTION)
- **The Ban on "Final.wav"**: Never label files as `Final.wav` or `Final_v2.wav`.
- **Standard Industry Syntax**:
  - `[SongTitle]_[Version]_[Stage]_[BPM]_[Key]_[Date].[ext]`
  - Example: `MidnightRun_v03_MixPass_124BPM_Fmin_20261110.wav`

### 3c. Deliverables Checklist for Commercial Release (Grammy P&E Wing Standards)
- **Full Mix Masters**:
  - Mastered WAV: 24-bit, 44.1 kHz / 48 kHz / 96 kHz (stream targets).
  - Unmastered Mix: 24-bit with -6 dBFS true peak headroom for mastering engineers.
- **Mix Alternate Passes**:
  - *TV Track*: Full mix minus lead vocal (backing vocals remain active).
  - *Instrumental*: Full mix minus all vocal tracks.
  - *Acapella*: All vocal tracks soloed with active effects.
  - *Clean Mix*: Explicit lyrics muted or reversed.
  - *Performance Track*: Lead vocal removed, selected backing hooks retained.
- **Consolidated Stems (Archival Delivery)**:
  - All stems consolidated to start at **Bar 1, Beat 1, Time 0:00:00** so importing into any third-party DAW requires zero timeline alignment.
  - Delivered dry and wet where requested, with zero master limiter clipping.

### 3d. The 3-2-1 Backup Strategy (FACT)
- **3 Copies of Data**: Active working file, primary local backup, and secondary remote backup.
- **2 Different Storage Media**: Fast local NVMe SSD (working drive) + Local mechanical RAID / NAS / external HDD.
- **1 Offsite Copy**: Automated encrypted cloud backup (e.g. Backblaze, AWS S3, or offsite hard drive rotation).
