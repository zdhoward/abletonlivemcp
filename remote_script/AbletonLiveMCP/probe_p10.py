"""P-10: automation_envelope, insert_step, events_in_range, value_at_time, clear.

Stub (T-003). Implemented by the P-10 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-10"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
