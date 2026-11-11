"""P-23: Application.View, open_dialog_count, current_dialog_message, process usage.

Stub (T-003). Implemented by the P-23 ticket (plan section 4).
Introspection probe (read): it must not change the Set.
"""

from .dom_common import READ

PROBE_ID = "P-23"
KIND = READ


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
