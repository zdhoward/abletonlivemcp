"""P-02: Song.get_data/set_data: value types, size limit, survival across Save and reopen.

Stub (T-003). Implemented by the P-02 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-02"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
