"""P-16: set_or_delete_cue, CuePoint name/time/jump, jump_to_next/prev_cue.

Stub (T-003). Implemented by the P-16 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-16"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
