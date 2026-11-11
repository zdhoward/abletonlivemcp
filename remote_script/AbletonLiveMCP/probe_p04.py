"""P-04: Song.move_device and find_device_position: reorder, cross-track, into/out of chains.

Stub (T-003). Implemented by the P-04 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-04"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
