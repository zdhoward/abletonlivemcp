"""The frozen v2 tool surface and Live scenario proof metadata.

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
LEGACY_TOOLS: dict[str, tuple[str, ...]] = {}  # every batch has landed; none remain

CORE_LIMIT = 30
ALL_LIMIT = 58
# Typed response contracts add ~23 KB of useful structure. Track input cost separately
# so output coverage cannot silently pay for an increasingly complex request surface.
CORE_INPUT_BYTES = 30_000
CORE_LISTING_BYTES = 68_000  # serialized tools, including concrete output schemas
CORE_LISTING_TARGET = 64_000
# What a default install actually lists: core plus the always-on automation and arrangement
# toolsets. Optional inputs advertise no redundant null branch (server._drop_optional_null).
DEFAULT_INPUT_BYTES = 36_000
DEFAULT_LISTING_BYTES = 84_000  # +4 KB (1.0.x): TrackSel descriptions, read filters

# The nine ordered phases of the complete Live proof. Scenario files
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
