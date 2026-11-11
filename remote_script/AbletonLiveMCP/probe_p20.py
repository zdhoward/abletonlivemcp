"""P-20: SimplerDevice and Sample slice fields.

Stub (T-003). Implemented by the P-20 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-20"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
