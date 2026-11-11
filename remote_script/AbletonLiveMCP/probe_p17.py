"""P-17: available routing types/channels and routing setters.

Stub (T-003). Implemented by the P-17 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-17"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
