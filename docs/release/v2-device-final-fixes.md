# Device, library and MCP final fix round (2026-11-11)

Owned subset baseline on real Live 12.2.0: 18 passing scenarios, 2 supported-refusal
scenarios, 1 failure (`dev-drums`: copy destination 37 in the stock 505 kit was occupied).
No full run completed in this worker. The owner stopped further Live runs to free Live
for the other worker; changes below have not been rerun in Live.

- Preserve inherited fixture receipt paths and library reply-shape corrections.
- Preserve the inherited unsupported drum-pad browser loading gate: selecting a pad and
  loading ended with an unknown outcome/ArgumentError. Custom drum-rack planning therefore
  refuses unsupported. Stock-kit loading, rack reading and pad mute passed.
- Disable public drum-pad copy with the shared `unsupported` helper before any write.
  This is an unverified feature at the hard stop, not proof that Live cannot copy pads.
  The scenario now expects that refusal and checks that destination 0 is empty.
- FX-rack wrapping already refuses unsupported because Live 12.2 lacks `insert_chain`.
  Stock rack loading, macro values, device loading/parameters/moves and chain building passed.
- Fix stale resource API arguments (`response_format` on track reads, `device` instead of
  `path` on parameter reads). Strengthen real MCP resource checks to reject error JSON,
  check track selection, and read a device parameter resource when a device exists.

The final full proof, pytest and scratch cleanup remain with the coordinating worker.
