"""Backward-compatibility re-export of v0.6.x base UNTP semantic rules.

Phase 3b of docs/plans/UNTP_0.7.0_MIGRATION.md split semantic rules into
``rules/v0_6/`` and ``rules/v0_7/`` subpackages. This shim preserves the
import path used by existing tests and any third-party plugin
(``from dppvalidator.validators.rules.base import CircularityContentRule``) — see
the public-API stability contract in §7.6 of the plan.

Through the 0.4.x line this re-exports v0.6.x rules. Phase 9 will switch
the default to v0.7 and update this shim accordingly.
"""

from __future__ import annotations

from dppvalidator.validators.rules.v0_6.base import (
    CircularityContentRule,
    ConformityClaimRule,
    GranularitySerialNumberRule,
    GTINChecksumRule,
    HazardousMaterialRule,
    HSCodeRule,
    MassFractionSumRule,
    MaterialCodeRule,
    OperationalScopeRule,
    ValidityDateRule,
)

__all__ = [
    "CircularityContentRule",
    "ConformityClaimRule",
    "GTINChecksumRule",
    "GranularitySerialNumberRule",
    "HSCodeRule",
    "HazardousMaterialRule",
    "MassFractionSumRule",
    "MaterialCodeRule",
    "OperationalScopeRule",
    "ValidityDateRule",
]
