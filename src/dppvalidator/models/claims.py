"""Backward-compatibility re-export of v0.6.x ``claims``.

The actual class definitions live in :mod:`dppvalidator.models.v0_6.claims`.
This shim preserves the import path used by third-party plugins (e.g.
``from dppvalidator.models.claims import Claim``) — see Phase 3 of
docs/plans/UNTP_0.7.0_MIGRATION.md and the public-API stability contract in
§7.6 of that plan.

Through the 0.4.x line this re-exports v0.6.x classes (the current default
schema version). Phase 9 (validator 0.5.0) will switch the default to v0.7
and update this shim accordingly.
"""

from __future__ import annotations

from dppvalidator.models.v0_6.claims import (
    Claim,
    Criterion,
    Metric,
    Regulation,
    Standard,
)

__all__ = [
    "Claim",
    "Criterion",
    "Metric",
    "Regulation",
    "Standard",
]
