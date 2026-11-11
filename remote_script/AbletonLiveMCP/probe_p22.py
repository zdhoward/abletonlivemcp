"""P-22: root_note/scale, groove pool, Clip.groove, tuning_system, Link, count_in_duration.

Stub (T-003). Implemented by the P-22 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-22"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
