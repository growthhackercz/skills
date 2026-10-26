"""Exact contact identity states shared by Sales Scout.

Provider reads, credentials, consent checks and confirmed mutations live in the
shared publisher-style ``sales_ghl_plan`` helper. This runtime-local module
contains only normalization and explicit lookup-result constants used by
``ghl_scout_push.py``.
"""

FOUND = "found"
NOT_FOUND = "not_found"
UNKNOWN = "unknown"


def norm_email(email):
    """Normalize an e-mail only for exact equality checks."""
    return str(email or "").strip().lower()
