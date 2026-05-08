"""Semantic validation rules for UNTP v0.6.x.

Phase 3b of docs/plans/UNTP_0.7.0_MIGRATION.md split the rule modules into
version-namespaced subpackages so the v0.6.x rules and v0.7.0 rules can
coexist. This subpackage holds the legacy v0.6.x rules, preserved verbatim.

Each rule walks the v0.6 model shape (``passport.credential_subject.product.*``,
``passport.credential_subject.materials_provenance``, scorecard classes, etc.).
Rules that no longer apply to v0.7.0 — like
:class:`OperationalScopeRule`, which inspects
``EmissionsPerformance.operational_scope`` (a class that doesn't exist in
v0.7.0) — are kept here but excluded from the v0.7.0 rule set in
``rules/v0_7/__init__.py``.
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
from dppvalidator.validators.rules.v0_6.cirpass import (
    CIRPASS_RULES,
    CIRPASSGranularityConsistencyRule,
    CIRPASSMandatoryAttributesRule,
    CIRPASSOperatorIdentifierRule,
    CIRPASSSubstancesOfConcernRule,
    CIRPASSValidityPeriodRule,
    CIRPASSWeightVolumeRule,
)
from dppvalidator.validators.rules.v0_6.textile import (
    TEXTILE_RULES,
    TextileCareInstructionsRule,
    TextileDurabilityRule,
    TextileEnvironmentalCategory,
    TextileHSCodeRule,
    TextileMaterialCompositionRule,
    TextileMicroplasticRule,
    get_textile_environmental_categories,
    is_textile_product,
)

# The default v0.6.x rule list — includes everything in the base file plus
# CIRPASS-2 CQ-based rules. Textile rules are *not* part of the default set
# (they're sector-specific and opt-in). This list is what
# ``ALL_RULES_BY_VERSION["0.6.x"]`` resolves to.
ALL_RULES_V0_6 = [
    # Base UNTP rules
    MassFractionSumRule(),
    ValidityDateRule(),
    HazardousMaterialRule(),
    CircularityContentRule(),
    ConformityClaimRule(),
    GranularitySerialNumberRule(),
    OperationalScopeRule(),
    MaterialCodeRule(),
    HSCodeRule(),
    GTINChecksumRule(),
    # CIRPASS-2 rules (CQ-based)
    *CIRPASS_RULES,
]

__all__ = [
    "ALL_RULES_V0_6",
    # Base rules
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
    # CIRPASS rules
    "CIRPASS_RULES",
    "CIRPASSGranularityConsistencyRule",
    "CIRPASSMandatoryAttributesRule",
    "CIRPASSOperatorIdentifierRule",
    "CIRPASSSubstancesOfConcernRule",
    "CIRPASSValidityPeriodRule",
    "CIRPASSWeightVolumeRule",
    # Textile sector rules
    "TEXTILE_RULES",
    "TextileCareInstructionsRule",
    "TextileDurabilityRule",
    "TextileEnvironmentalCategory",
    "TextileHSCodeRule",
    "TextileMaterialCompositionRule",
    "TextileMicroplasticRule",
    "get_textile_environmental_categories",
    "is_textile_product",
]
