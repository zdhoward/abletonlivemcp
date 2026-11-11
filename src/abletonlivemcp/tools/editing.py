"""Toolset `editing`: one audio-clip edit per call (warp markers, crop, gain, pitch; P-09)."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ..models import ClipRef, ExpectName
from ..models_clips import WarpMode, WarpOp
from ..server import _call, _overwrite, clip_selector, issue_refs


@_overwrite
def live_edit_audio_clip(
    clip: ClipRef,
    expect_name: ExpectName | None = None,
    warp_markers: Annotated[list[WarpOp], Field(max_length=32)] | None = None,
    crop: bool = False,
    duplicate_loop: bool = False,
    gain: Annotated[float, Field(ge=0, le=1)] | None = None,
    pitch_coarse: Annotated[int, Field(ge=-48, le=48)] | None = None,
    pitch_fine: Annotated[float, Field(ge=-50, le=50)] | None = None,
    warping: bool | None = None,
    warp_mode: WarpMode | None = None,
) -> dict:
    """Edit one clip in order: fields, warp_markers (add needs sample_time seconds and an
    existing marker; move by distance beats; remove at beat_time), crop, duplicate_loop
    (MIDI too). Receipt plus clip and marker readback."""
    ref = issue_refs([{**clip_selector(clip), "expect_name": expect_name}])[0]
    params = {
        "targets": [{"kind": ref["kind"], "ref": ref["ref"], "expect_name": expect_name}],
        "crop": crop,
        "duplicate_loop": duplicate_loop,
    }
    extra = {
        "gain": gain,
        "pitch_coarse": pitch_coarse,
        "pitch_fine": pitch_fine,
        "warping": warping,
        "warp_mode": warp_mode,
    }
    params.update({k: v for k, v in extra.items() if v is not None})
    if warp_markers:
        params["warp_markers"] = [w.model_dump(exclude_none=True) for w in warp_markers]
    return _call("edit_audio_clip", params)
