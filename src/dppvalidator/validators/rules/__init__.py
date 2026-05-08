"""Pluggable semantic validation rules.

Phase 3b of docs/plans/UNTP_0.7.0_MIGRATION.md split this package into
:mod:`dppvalidator.validators.rules.v0_6` and
:mod:`dppvalidator.validators.rules.v0_7` so 0.6.x and 0.7.0 rule sets can
coexist. This module exposes:

* :data:`ALL_RULES_BY_VERSION` — the dispatch table consumed by
  :class:`dppvalidator.validators.semantic.SemanticValidator` when no
  custom ``rules`` list is passed.
* :data:`ALL_RULES` — the default rule set (kept as the v0.6.x list for
  the 0.4.x line so existing callers continue to see the same behaviour).
* All v0.6 rule classes — re-exported for backward compatibility, so
  ``from dppvalidator.validators.rules import MassFractionSumRule`` keeps
  working.

Adding a new UNTP version:

1. Build the ported rules under ``rules/v0_X/`` (one module per topic).
2. Import its ``ALL_RULES_V0_X`` list here and add it to
   :data:`ALL_RULES_BY_VERSION`.
3. The :class:`SemanticValidator` picks it up automatically — no further
   wiring required. See ``.claude/rules/untp-versioning.md`` (rule 2).
"""

from __future__ import annotations

# v0.6 (default in the 0.4.x line) — re-export for backward compat.
from dppvalidator.validators.rules.v0_6 import (
    ALL_RULES_V0_6,
    CIRPASS_RULES,
    TEXTILE_RULES,
    CircularityContentRule,
    CIRPASSGranularityConsistencyRule,
    CIRPASSMandatoryAttributesRule,
    CIRPASSOperatorIdentifierRule,
    CIRPASSSubstancesOfConcernRule,
    CIRPASSValidityPeriodRule,
    CIRPASSWeightVolumeRule,
    ConformityClaimRule,
    GranularitySerialNumberRule,
    GTINChecksumRule,
    HazardousMaterialRule,
    HSCodeRule,
    MassFractionSumRule,
    MaterialCodeRule,
    OperationalScopeRule,
    TextileCareInstructionsRule,
    TextileDurabilityRule,
    TextileEnvironmentalCategory,
    TextileHSCodeRule,
    TextileMaterialCompositionRule,
    TextileMicroplasticRule,
    ValidityDateRule,
    get_textile_environmental_categories,
    is_textile_product,
)
from dppvalidator.validators.rules.v0_7 import ALL_RULES_V0_7

# Backward-compat default. The 0.4.x line ships with v0.6 as the default
# schema version, so ``ALL_RULES`` points at the v0.6 list. Phase 9 flips
# this to the v0.7 list when ``DEFAULT_SCHEMA_VERSION`` flips.
ALL_RULES = list(ALL_RULES_V0_6)

# Version-keyed dispatch table consumed by ``SemanticValidator``. Both
# 0.6.0 and 0.6.1 share the same rule set because the model shape is the
# same; 0.7.0 has its own.
ALL_RULES_BY_VERSION: dict[str, list] = {
    "0.6.0": ALL_RULES_V0_6,
    "0.6.1": ALL_RULES_V0_6,
    "0.7.0": ALL_RULES_V0_7,
}

__all__ = [
    "ALL_RULES",
    "ALL_RULES_BY_VERSION",
    "ALL_RULES_V0_6",
    "ALL_RULES_V0_7",
    # v0.6 re-exports (backward compat)
    "CIRPASS_RULES",
    "CIRPASSGranularityConsistencyRule",
    "CIRPASSMandatoryAttributesRule",
    "CIRPASSOperatorIdentifierRule",
    "CIRPASSSubstancesOfConcernRule",
    "CIRPASSValidityPeriodRule",
    "CIRPASSWeightVolumeRule",
    "CircularityContentRule",
    "ConformityClaimRule",
    "GTINChecksumRule",
    "GranularitySerialNumberRule",
    "HSCodeRule",
    "HazardousMaterialRule",
    "MassFractionSumRule",
    "MaterialCodeRule",
    "OperationalScopeRule",
    "TEXTILE_RULES",
    "TextileCareInstructionsRule",
    "TextileDurabilityRule",
    "TextileEnvironmentalCategory",
    "TextileHSCodeRule",
    "TextileMaterialCompositionRule",
    "TextileMicroplasticRule",
    "ValidityDateRule",
    "get_textile_environmental_categories",
    "is_textile_product",
]
