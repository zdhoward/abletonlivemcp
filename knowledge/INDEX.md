# Knowledge base: FX chains by instrument and stage

Built by `/study` on 2026-11-10 for the Ableton Live MCP server. Each page organizes chains by **role and stage order**, not by brand, so a chain can resolve to whatever plugins a user owns (see `src/abletonlivemcp/adapters.py`). Raw collector notes with citations are in `research/raw/`.

## Using and extending this folder

**Reading.** Use the MCP tools `knowledge_list`, `knowledge_search` (by words, returns sections) and `knowledge_read` (a page, or one section by heading). They rescan this folder on every call, so a page added a minute ago is found at once.

**Adding a page** (several threads and agents write here at the same time):
- Drop any `.md` file in this folder. Subfolders are fine (for example `knowledge/gemini/`, `knowledge/plugins/`). The page name is its path without `.md`.
- Start with a `# Title` line and use `##` headings for sections, so a section can be read by itself. Nothing else is required: no frontmatter, no registration.
- Label evidence as FACT (documented for a named recording or workflow), CONVENTION or OPINION, link the source URL, and tag numbers you could not confirm against the original page with `UNCONFIRMED-NUMBER`, `UNVERIFIED`, `SECOND-HAND` or `LOW CONFIDENCE`. `knowledge_list` counts these tags per page.
- Do **not** add your page to the table below to register it; listing is automatic. The table is a hand-written overview and can lag behind. Editing the same file from two threads causes merge conflicts.
- Commit only your own files (`git add knowledge/<your files>`), and keep raw collector notes in `research/raw/`, not here.

| Page | Covers | Strength of sourcing |
|---|---|---|
| [vocals](vocals.md) | Lead, backing, rap, R&B, EDM chops; named-record chains (Adele, Billie Eilish, Dua Lipa, The Weeknd, Drake, Kendrick Lamar, TWICE) | Best of the set: many Sound on Sound engineer write-ups. Rap/R&B list plugins but few numbers. |
| [drums](drums.md) | Per-drum chains, drum bus, parallel compression, kick/bass ducking, "In the Air Tonight" | Good for acoustic and parallel compression. No gate, snare-reverb or transient-shaper settings found. Trap/808 is snippet-level only. |
| [busses-mixing](busses-mixing.md) | Bus and group processing, sends/returns, gain staging, EQ/compressor order | Good, but most documented examples are 2007-2010 analogue-hybrid mixes. |
| [guitar-bass](guitar-bass.md) | Pedal order, amp-sim chains, DI + amp bass, parallel distortion | Good for bass and amp-sim; many numbers re-verified. Acoustic guitar is blog-snippet level. |
| [keys-synths](keys-synths.md) | Piano, electric piano, pads, strings, supersaw, synth bass, sidechain tiers | Weak. **No chain tied to a famous recording was found**; almost all of it is convention or opinion. |
| [mastering](mastering.md) | Chain order, loudness targets, M/S, what not to do | Strong on Spotify and AES TD1004 (checked against their own pages). YouTube, Apple and TD1008 numbers are second-hand or unverified. |

## Patterns that held across several pages

These appeared independently in more than one page. Details, ranges and sources are on the pages; treat them as conventions, not rules.
- Corrective work (high-pass, mud cut) comes early, and time-based effects (reverb, delay) go on **sends or returns**, usually 100% wet and filtered (about 200 Hz high-pass, about 10 kHz low-pass in Sound on Sound; see [busses-mixing](busses-mixing.md)).
- **Parallel compression** is the most-documented dynamics technique, with fast attack, high ratio and a blend well below the dry signal (drums, vocals, bass).
- **One element owns the low end.** Bass layers, kick and synth sub are high-passed or ducked so only one holds the sub.
- Mix-bus and master compression are gentle: roughly 1-3 dB gain reduction. Limiters come last.
- **Dry is a legitimate choice**: several documented vocal mixes use little or no reverb.

## Conflicts the sources do not settle

Left open on purpose; each is written up on its page. EQ before or after compression; pad and reverb-return high-pass (200 vs 300 Hz); bass compression ratio and DI record level; parallel-compression ratio and attack; kick EQ frequencies; and the YouTube loudness target (-14 vs Katz's -13).

## Read before using any number as a preset

- **Numbers came through two summarizing passes.** Collectors read pages through a summarizing fetch tool. Synthesizers re-opened original pages for headline numbers (they report about 5 to 30 re-verified per page, with no mismatches except the corrections listed on each page). Anything tagged `UNCONFIRMED-NUMBER`, `UNVERIFIED`, `SECOND-HAND` or `LOW CONFIDENCE` has not been confirmed against the original.
- **Synthesizer self-reports are unaudited.** I did not independently re-check the re-verification counts.
- **Several sources are one author's settings, not an engineer's.** For example, the Scheps drum numbers come from a blog author who does not separate Scheps's settings from their own.
- **"Famous" is thin outside vocals and drums.** Where a page says no famous chain was found, that is the finding.

## Known gaps (not yet researched)

- Mix with the Masters, Tape Op, Mix Magazine, Pensado's Place, Nail The Mix (partly) and manufacturer articles (FabFilter, Waves, UAD, Valhalla, Neural DSP, Kemper) were not read in most tracks.
- No documented chains for the mastering engineers Calbi, Kutch, Merrill, Colton or Grundman; no ordered numeric chain for Ludwig or Lazar.
- No sourced numbers for gates, snare reverb, transient shaping, organ/Leslie, trap keys, ambient keys, or CD/club/vinyl delivery.
- Nothing on mid-side vocal chains, podcast or speech, or sound design beyond synth basics.
- Recent community material (the `last30days` lane) was not run; this pass used web search only.
