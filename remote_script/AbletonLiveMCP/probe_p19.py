"""P-19: arrangement_clips, duplicate_clip_to_arrangement, Track.delete_clip, take lanes.

Stub (T-003). Implemented by the P-19 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-19"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
