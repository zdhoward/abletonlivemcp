"""Bounded chain requests; role intent and exact-device settings stay distinct."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, FiniteFloat, StringConstraints

from .models import RawValue, _Model

Role = Literal["compressor", "eq", "saturation", "reverb"]
BrowserRoot = Literal[
    "audio_effects", "plugins", "max_for_live", "user_library", "packs", "current_project",
    "user_folders", "instruments", "sounds", "drums", "samples", "midi_effects",
]  # fmt: skip
DeviceName = Annotated[str, StringConstraints(min_length=1, max_length=256)]
ParameterName = Annotated[str, StringConstraints(min_length=1, max_length=120)]
DisplayValue = Annotated[str, StringConstraints(max_length=256)] | FiniteFloat | bool


class IntentValue(_Model):
    value: DisplayValue | None = None
    level: Literal["short", "medium", "long"] | None = None


class RoleStage(_Model):
    role: Role
    intent: dict[ParameterName, DisplayValue | IntentValue] = Field(
        default_factory=dict, max_length=32
    )


def _root(value):
    if value not in BrowserRoot.__args__:
        raise ValueError(f"only {list(BrowserRoot.__args__)} items can be built, not {value!r}")
    return value


class DeviceStage(_Model):
    device: DeviceName
    params: dict[ParameterName, DisplayValue | RawValue] = Field(
        default_factory=dict, max_length=64
    )
    root: Annotated[BrowserRoot, BeforeValidator(_root)] | None = None
    path: list[DeviceName] | None = Field(default=None, min_length=1, max_length=8)


ChainStage = RoleStage | DeviceStage
ChainStages = Annotated[list[ChainStage], Field(min_length=1, max_length=12)]


def _lower_roles(value):
    if isinstance(value, dict):
        return {k.lower() if isinstance(k, str) else k: v for k, v in value.items()}
    return value


Preferences = Annotated[
    dict[Role, Annotated[list[DeviceName], Field(max_length=16)]],
    Field(max_length=4),
    BeforeValidator(_lower_roles),
]
