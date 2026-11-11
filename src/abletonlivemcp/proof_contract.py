"""The frozen v2 tool surface and final-proof metadata (batch 1; docs/plans/v2-contracts.md).

``FINAL_SURFACE`` maps each tool module (``tools/<module>.py``) to the exact tool names it
registers when v2 is complete: 30 core + 27 opt-in = 57. The toolset of a module follows the T-002
rule in ``server.toolset_of`` (core domains -> ``core``; else the module name with ``_`` -> ``-``).
``LEGACY_TOOLS`` are the pre-v2 names still registered until their batch replaces them; a batch
removes a legacy name by no longer registering it (this file needs no edit for that).

``tests/test_tool_surface.py`` checks every registered tool against these tables, and
``scripts/live_v2_final.py`` requires a scenario for every registered tool.
"""

from __future__ import annotations

FINAL_SURFACE: dict[str, tuple[str, ...]] = {
    # ---- core (30) ----
    "session": (
        "live_hello",
        "live_get_session",
        "live_set_session",
        "live_transport",
        "live_undo",
    ),
    "tracks": (
        "live_get_tracks",
        "live_create_tracks",
        "live_set_tracks",
        "live_set_mixer",
        "live_delete",
        "live_duplicate",
    ),
    "scenes": ("live_get_scenes", "live_create_scenes", "live_set_scenes", "live_launch"),
    "clips": ("live_get_clips", "live_create_clips", "live_set_clips"),
    "notes": ("live_get_notes", "live_edit_notes"),
    "devices": (
        "live_get_device_parameters",
        "live_set_device_parameters",
        "live_set_devices",
        "live_move_device",
    ),
    "browser": ("live_browser_list", "live_browser_search", "live_get_operation", "live_load_item"),
    "chain": ("live_plan_chain", "live_build_chain"),
    # ---- opt-in (27) ----
    "drums": (
        "live_get_drum_rack",
        "live_set_drum_pads",
        "live_convert",
        "live_get_simpler",
        "live_set_simpler",
        "live_plan_drum_rack",
        "live_build_drum_rack",
    ),
    "racks": ("live_get_rack", "live_set_rack"),
    "organize": ("live_get_labels", "live_set_labels"),
    "als": ("live_scan_projects", "live_usage_report"),
    "library": ("live_knowledge",),
    "arrangement": (
        "live_get_arrangement",
        "live_set_cue_points",
        "live_create_arrangement_clips",
        "live_edit_arrangement_clips",
    ),
    "automation": ("live_get_automation", "live_set_automation"),
    "recording": ("live_record",),
    "editing": ("live_edit_audio_clip",),
    "view": ("live_view",),
    "devices_advanced": ("live_get_device_extras", "live_set_device_extras"),
    "files": ("live_import_midi", "live_export_midi"),
    # compatibility toolsets with no standalone tools (song extras live in session get/set)
    "song": (),
    "experimental": (),
}

# Which batch owns (fills) each tool module; the remote dom_* files follow the same split.
OWNER: dict[str, int] = {
    "session": 2, "tracks": 2, "scenes": 2, "recording": 2, "song": 2, "view": 2,
    "clips": 3, "notes": 3, "arrangement": 3, "automation": 3, "editing": 3, "files": 3,
    "devices": 4, "browser": 4, "chain": 4, "drums": 4, "racks": 4, "devices_advanced": 4,
    "als": 5, "organize": 5, "library": 5,
    "experimental": 1,
}  # fmt: skip

# Pre-v2 names (module -> names) that stay registered until the owning batch replaces them.
LEGACY_TOOLS: dict[str, tuple[str, ...]] = {
    "session": ("live_session_info", "live_get_transport", "live_set_transport"),
    "tracks": ("live_tracks", "live_create_track", "live_set_track"),
    "scenes": ("live_list_scenes", "live_create_scene", "live_set_scene_name", "live_fire_scene"),
    "clips": ("live_get_clip", "live_create_clip", "live_fire_clip", "live_stop_clip"),
    "notes": ("live_add_notes",),
    "devices": ("live_device_parameters",),
    "browser": ("live_browser_roots",),
    "chain": ("live_vocal_presets",),
}

CORE_LIMIT = 30
ALL_LIMIT = 58
CORE_LISTING_BYTES = 40_000  # UTF-8 bytes of the serialized core list_tools result
CORE_LISTING_TARGET = 36_000  # headroom target, reported but not enforced

# The nine ordered phases of the single end-of-project proof (fast-track plan). Scenario files
# in scripts/final_cases/*.json name one of these as their ``phase``.
PHASES: tuple[str, ...] = (
    "connection",
    "shared_fixture",
    "browser_devices",
    "musical_edits",
    "assembly",
    "arrangement_control",
    "safety_destructive",
    "offline_mcp",
    "persistence_finish",
)


def final_tools() -> dict[str, str]:
    """tool name -> module, for every final tool."""
    return {name: module for module, names in FINAL_SURFACE.items() for name in names}


def legacy_tools() -> dict[str, str]:
    return {name: module for module, names in LEGACY_TOOLS.items() for name in names}
