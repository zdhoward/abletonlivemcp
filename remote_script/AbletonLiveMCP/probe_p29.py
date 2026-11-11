"""P-29: .adg schema: does Live accept a generated rack with macro mappings.

Stub (T-003). Implemented by the P-29 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-29"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
