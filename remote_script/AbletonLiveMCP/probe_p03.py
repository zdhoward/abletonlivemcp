"""P-03: begin_undo_step/end_undo_step and Song.undo: is a 3-write batch one undo entry.

Stub (T-003). Implemented by the P-03 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-03"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
