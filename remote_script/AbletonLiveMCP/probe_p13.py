"""P-13: the 6 Live.Conversions functions.

Stub (T-003). Implemented by the P-13 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-13"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
