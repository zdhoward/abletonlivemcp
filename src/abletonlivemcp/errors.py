"""The one public refusal type of the host (mirrors ``Invalid`` in the Remote Script's core)."""

from __future__ import annotations


class Invalid(ValueError):
    """A deliberate refusal of a tool's arguments, raised by this code before any write; its text
    is shown to the client. Any other exception (a native ValueError included) is reported by
    type only, because its message can hold paths or other private data."""
