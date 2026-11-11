"""Toolset `recording`: live_record (session/arrangement record, overdub, capture)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from ..models_control import RecordAction
from ..server import _call, _control, _generation


@_control
def live_record(
    action: RecordAction,
    value: bool = None,
    length: Annotated[float, Field(gt=0, le=1024)] = None,
    destination: Literal[0, 1, 2] = None,
) -> dict:
    """Recording controls (unverified on Live 12.2). session_record / arrangement_record /
    overdub take `value`; turning one on needs `length` (beats, <= 8 s) and returns an
    operation that restores the switches and play state. trigger_session_record (optional
    `length`), capture_midi (`destination` 0 auto, 1 session, 2 arrangement),
    capture_and_insert_scene."""
    params: dict = {"action": action, "generation": _generation()}
    for key, val in (("value", value), ("length", length), ("destination", destination)):
        if val is not None:
            params[key] = val
    return _call("record", params)
