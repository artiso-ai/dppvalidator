"""Backward-compatibility re-export of v0.6.x CIRPASS-2 CQ-based rules.

Phase 3b of docs/plans/UNTP_0.7.0_MIGRATION.md split semantic rules into
``rules/v0_6/`` and ``rules/v0_7/`` subpackages. This shim preserves the
import path used by existing tests and any third-party plugin
(``from dppvalidator.validators.rules.cirpass import CIRPASS_RULES``) — see
the public-API stability contract in §7.6 of the plan.

Through the 0.4.x line this re-exports v0.6.x rules. Phase 9 will switch
the default to v0.7 and update this shim accordingly.
"""

from __future__ import annotations

from dppvalidator.validators.rules.v0_6.cirpass import (
    CIRPASS_RULES,
    CIRPASSGranularityConsistencyRule,
    CIRPASSMandatoryAttributesRule,
    CIRPASSOperatorIdentifierRule,
    CIRPASSSubstancesOfConcernRule,
    CIRPASSValidityPeriodRule,
    CIRPASSWeightVolumeRule,
)

__all__ = [
    "CIRPASS_RULES",
    "CIRPASSGranularityConsistencyRule",
    "CIRPASSMandatoryAttributesRule",
    "CIRPASSOperatorIdentifierRule",
    "CIRPASSSubstancesOfConcernRule",
    "CIRPASSValidityPeriodRule",
    "CIRPASSWeightVolumeRule",
]
