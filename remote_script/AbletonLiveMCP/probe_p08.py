"""P-08: ClipSlot/Track create_audio_clip(path) and Track.create_midi_clip.

Stub (T-003). Implemented by the P-08 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-08"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
