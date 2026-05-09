"""Shared helpers for the CIRPASS v1.3 rule tree.

Phase 8.5 polish (2026-05-09). Both ``actor.py`` and ``connector.py``
declared their own ``_parse_iso_datetime`` helper; this module
centralises it so a future tightening of the parser (e.g. requiring
timezone-aware inputs at the rule layer) is a single-site edit.

Module-private — the underscore prefix marks it as internal to the
``cirpass_v1_3`` rule package.
"""

from __future__ import annotations

from datetime import datetime


def parse_iso_datetime(value: str) -> datetime | None:
    """Parse an ISO 8601 datetime, tolerating the ``Z`` UTC suffix.

    Returns ``None`` on parse failure rather than raising — the
    model layer is responsible for validating the timestamp shape;
    rule helpers exist so the rule logic can compare endpoints when
    both parse, and silently no-op when one doesn't.
    """
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


__all__ = ["parse_iso_datetime"]
