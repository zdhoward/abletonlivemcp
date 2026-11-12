"""Wire-preserving tool output contracts.

TypedDicts describe the fields Live guarantees without adding defaults or changing the
existing JSON envelopes. Extra Live/version-specific fields remain present. Optional keys
mean "not returned by every action", never a fabricated null/default value. The variable
payload of an individual native action stays extensible; receipts and pagination are typed.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import ConfigDict, with_config
from typing_extensions import NotRequired, TypedDict

open_output = with_config(ConfigDict(extra="allow", strict=True))
Row = dict[str, Any]
Complete = Literal["complete", "partial"]
Outcome = Literal["applied", "not_applied", "unknown", "not_attempted"]


@open_output
class ReceiptItem(TypedDict):
    index: int
    outcome: Outcome
    result: NotRequired[Any]
    error: NotRequired[str]


@open_output
class StepReceipt(TypedDict):
    status: Complete
    items: list[ReceiptItem]
    stopped_at: int | None
    error: str | None


@open_output
class WriteReceipt(StepReceipt):
    applied: list[Any]
    unverified: NotRequired[list[str]]
    undo_steps: NotRequired[int]


@open_output
class SessionState(TypedDict):
    generation: int
    tempo: float
    signature: list[int]
    is_playing: bool
    track_count: int
    return_count: int
    scene_count: int
    current_song_time: NotRequired[float]
    metronome: NotRequired[bool | None]
    loop: NotRequired[Row]
    selection: NotRequired[Row]
    can_undo: NotRequired[bool | None]
    can_redo: NotRequired[bool | None]
    cues: NotRequired[list[Row]]


@open_output
class Toolsets(TypedDict):
    enabled: list[str]
    available: list[str]


@open_output
class Hello(TypedDict):
    protocol: int
    live_version: list[int] | None
    variant: str | None
    build_id: str | None
    generation: int
    diagnostics: Row
    capabilities: Row
    capability_report: dict[str, Row]
    toolsets: Toolsets


@open_output
class Tracks(TypedDict):
    generation: int
    track_count: int
    return_count: int
    tracks: list[Row]


@open_output
class Scenes(TypedDict):
    generation: int
    scene_count: int
    scenes: list[Row]


@open_output
class Clips(TypedDict):
    clips: list[Row]
    truncated: bool


@open_output
class Notes(TypedDict):
    notes: list[Row]
    total: int
    next_offset: int | None
    clip_end: float
    past_clip_end: int


@open_output
class BrowserPage(TypedDict):
    complete: bool
    truncated: bool
    cursor: str | None
    items: list[Row]


@open_output
class BrowserSearch(TypedDict):
    results: list[Row]
    visited: int
    complete: bool
    truncated: bool
    budget_exhausted: bool
    cursor: str | None


@open_output
class Operation(TypedDict):
    operation: str
    state: Literal["pending", "ready", "failed", "unknown", "unknown_operation"]
    reason: NotRequired[str | None]
    applied: NotRequired[bool | None]
    may_have_applied: NotRequired[bool]
    generation: NotRequired[int]
    device: NotRequired[str | None]
    kind: NotRequired[str]
    result: NotRequired[Row | None]


@open_output
class OperationReply(TypedDict, total=False):
    # One operation record, or a batch under operations; no additional result wrapper.
    operation: str
    state: Literal["pending", "ready", "failed", "unknown"]
    reason: str | None
    applied: bool | None
    may_have_applied: bool
    generation: int
    operations: list[Operation]


@open_output
class DeviceListing(TypedDict):
    owner: Row
    container: str
    container_name: str | None
    devices: list[Row]


@open_output
class ParameterPage(TypedDict):
    parameters: list[Row]
    next_offset: int | None


@open_output
class ParameterResult(TypedDict):
    name: str
    requested: Any
    actual: str | None
    actual_raw: float | None
    exact: bool
    off_target: bool
    raw: bool
    original: NotRequired[Row]


@open_output
class ParameterWrite(TypedDict):
    status: Complete
    results: list[ParameterResult]
    problems: list[str]
    unverified: list[str]


@open_output
class MoveDevice(TypedDict):
    moved: str
    position: int
    devices: list[str]
    provenance: Literal["live_object_text_untrusted"]


@open_output
class Transport(TypedDict):
    action: str
    unverified: list[str]
    is_playing: bool
    current_song_time: float
    tempo: float
    settled: Row | None  # None: the command applied but the readback failed (`verification`)
    verification: NotRequired[str]


@open_output
class Undo(TypedDict):
    action: Literal["undo", "redo"]
    requested: int
    done: int
    status: Complete
    error: str | None
    can_undo: bool
    can_redo: bool


@open_output
class PlanTarget(TypedDict):
    track: int | str
    path: list[int | str]
    kind: str
    name: str | None
    generation: int
    devices: list[str]


@open_output
class Plan(TypedDict):
    plan_id: str
    fingerprint: str
    mode: Literal["chain", "fx_rack", "drum_rack"]
    target: PlanTarget
    stages: list[Row]
    intent_complete: bool
    expires_in: float
    unverified: list[str]
    manual_steps: list[str]


@open_output
class Build(TypedDict):
    plan_id: str
    mode: str
    status: Literal["complete", "partial", "failed", "pending"]
    intent_fulfilled: bool
    target: PlanTarget
    completed: list[int]
    stopped_at: int | None
    stop_reason: str | None
    omitted: list[str]
    unknown: list[str]
    stages: list[Row]
    unverified: list[str]
    manual_steps: list[str]
    already_built: NotRequired[bool]


@open_output
class DrumRack(TypedDict):
    name: str
    pads: list[Row]
    selected_note: int | None
    chains: int


@open_output
class Simpler(TypedDict):
    name: str
    device: Row
    sample: Row | None


@open_output
class Rack(TypedDict):
    name: str
    class_name: str
    drum_rack: bool
    macros: list[Row]
    chains: list[Row]
    chains_truncated: bool
    mapping: str


@open_output
class RackWrite(TypedDict):
    status: Complete
    rack: NotRequired[WriteReceipt]
    macros: NotRequired[list[ParameterResult]]
    problems: NotRequired[list[str]]


@open_output
class Conversion(TypedDict):
    action: str
    tracks_before: int
    tracks_after: int
    returned: Any
    unverified: list[str]
    note: str


@open_output
class Arrangement(TypedDict):
    song_length: float
    loop: list[float]
    current_song_time: float
    cues: NotRequired[list[Row]]
    tracks: NotRequired[list[Row]]
    truncated: NotRequired[bool]
    next_track: NotRequired[int]  # whole-Set read: continue from this track


@open_output
class Automation(TypedDict):
    parameter: str
    range: list[float]
    has_envelopes: bool
    has_envelope: bool
    clip_length: float
    events: NotRequired[list[Row]]
    samples: NotRequired[list[Row]]


@open_output
class Recording(TypedDict):
    action: str
    unverified: list[str]
    state: Row
    operation: NotRequired[Operation]
    scenes_added: NotRequired[int]


@open_output
class View(TypedDict, total=False):
    action: str
    unverified: list[str]
    focused: str | None
    visible: dict[str, bool | None]
    # Selection returns the standard untrusted envelope instead.
    provenance: Literal["live_object_text_untrusted"]
    data: Row


@open_output
class DeviceExtras(TypedDict):
    name: str
    class_name: str
    class_display_name: str | None
    latency_samples: int | None
    latency_ms: float | None
    can_compare_ab: bool | None
    using_preset_b: bool | None
    presets: NotRequired[list[str]]
    presets_truncated: NotRequired[bool]
    selected_preset_index: NotRequired[int | None]


@open_output
class DeviceExtrasWrite(TypedDict):
    unverified: list[str]
    selected_preset_index: NotRequired[int]
    saved: NotRequired[bool]
    using_preset_b: NotRequired[bool]


@open_output
class MidiExport(TypedDict):
    file: str
    notes: int
    muted_skipped: int
    bytes: int


@open_output
class Scan(TypedDict):
    scan_id: str
    sets_found: int
    sets_read: int
    truncated: bool
    seconds: float
    sets: list[Row]
    errors: list[Row]


@open_output
class Usage(TypedDict):
    scan_id: str
    kind: Literal["samples", "devices", "plugins"]
    sets_scanned: int
    total_keys: int
    rows: list[Row]


@open_output
class Labels(TypedDict):
    scope: Literal["set", "global", "both"]
    # "global" cannot be spelled as a class field; additional fields are retained.
    set: NotRequired[list[Row]]
    corrupt: NotRequired[list[str]]
    unverified: NotRequired[list[str]]


@open_output
class Knowledge(TypedDict):
    provenance: Literal["knowledge_base_reference_data"]
    action: Literal["search", "read"]
    query: NotRequired[str]
    words: NotRequired[list[str]]
    total_matches: NotRequired[int]
    results: NotRequired[list[Row]]
    page: NotRequired[str]
    section: NotRequired[str | None]
    text: NotRequired[str]
    truncated: NotRequired[bool]


def _untrusted(name: str, payload: Any) -> type:
    return open_output(
        TypedDict(name, {"provenance": Literal["live_object_text_untrusted"], "data": payload})
    )


TOOL_OUTPUTS: dict[str, type] = {
    "live_hello": Hello,
    "live_get_session": _untrusted("SessionReply", SessionState),
    "live_set_session": _untrusted("SessionWriteReply", WriteReceipt),
    "live_transport": Transport,
    "live_undo": Undo,
    "live_get_tracks": _untrusted("TracksReply", Tracks),
    "live_create_tracks": _untrusted("TracksWriteReply", WriteReceipt),
    "live_set_tracks": _untrusted("TrackEditReply", WriteReceipt),
    "live_set_mixer": _untrusted("MixerEditReply", WriteReceipt),
    "live_delete": _untrusted("DeleteReply", StepReceipt),
    "live_duplicate": _untrusted("DuplicateReply", StepReceipt),
    "live_get_scenes": _untrusted("ScenesReply", Scenes),
    "live_create_scenes": _untrusted("SceneCreateReply", WriteReceipt),
    "live_set_scenes": _untrusted("SceneEditReply", WriteReceipt),
    "live_launch": _untrusted("LaunchReply", WriteReceipt),
    "live_get_clips": _untrusted("ClipsReply", Clips),
    "live_create_clips": WriteReceipt,
    "live_set_clips": WriteReceipt,
    "live_get_notes": Notes,
    "live_edit_notes": WriteReceipt,
    "live_get_device_parameters": _untrusted(
        "DeviceParametersReply", DeviceListing | ParameterPage
    ),
    "live_set_device_parameters": ParameterWrite,
    "live_set_devices": WriteReceipt,
    "live_move_device": MoveDevice,
    "live_browser_list": _untrusted("BrowserListReply", BrowserPage),
    "live_browser_search": _untrusted("BrowserSearchReply", BrowserSearch),
    "live_get_operation": OperationReply,
    "live_load_item": Operation,
    "live_plan_chain": Plan,
    "live_build_chain": Build,
    "live_get_drum_rack": _untrusted("DrumRackReply", DrumRack),
    "live_set_drum_pads": WriteReceipt,
    "live_convert": Conversion,
    "live_get_simpler": _untrusted("SimplerReply", Simpler),
    "live_set_simpler": WriteReceipt,
    "live_plan_drum_rack": Plan,
    "live_build_drum_rack": Build,
    "live_get_rack": _untrusted("RackReply", Rack),
    "live_set_rack": RackWrite,
    "live_get_labels": _untrusted("LabelsReply", Labels),
    "live_set_labels": StepReceipt,
    "live_scan_projects": _untrusted("ScanReply", Scan),
    "live_usage_report": _untrusted("UsageReply", Usage),
    "live_knowledge": Knowledge,
    "live_get_arrangement": _untrusted("ArrangementReply", Arrangement),
    "live_set_cue_points": WriteReceipt,
    "live_create_arrangement_clips": WriteReceipt,
    "live_edit_arrangement_clips": WriteReceipt,
    "live_get_automation": Automation,
    "live_set_automation": WriteReceipt,
    "live_record": Recording,
    "live_edit_audio_clip": WriteReceipt,
    "live_view": View,
    "live_get_device_extras": _untrusted("DeviceExtrasReply", DeviceExtras),
    "live_set_device_extras": DeviceExtrasWrite,
    "live_import_midi": WriteReceipt,
    "live_export_midi": MidiExport,
}
