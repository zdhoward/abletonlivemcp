"""P-06: mixer_device volume/panning/sends, master crossfader/cue_volume, str_for_value.

Stub (T-003). Implemented by the P-06 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-06"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
