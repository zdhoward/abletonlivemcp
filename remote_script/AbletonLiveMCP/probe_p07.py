"""P-07: get_notes_extended fields, note modification/removal/duplication, quantize.

Stub (T-003). Implemented by the P-07 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-07"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
