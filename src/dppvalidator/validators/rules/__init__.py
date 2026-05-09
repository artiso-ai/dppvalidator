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
from dppvalidator.validators.rules.v0_7 import (
    ALL_RULES_V0_7,
    TEXTILE_RULES_V0_7,
    TEXTILE_RULES_V0_7_V2,
)

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


# Phase 7 task 7.2 of [docs/plans/CIRPASS_2_MIGRATION.md]: profile-keyed
# dispatch for the textile rule packs. ``textile-v1`` is the legacy
# pack (already in :data:`TEXTILE_RULES` for v0.6 and inside
# :data:`ALL_RULES_V0_7` for v0.7); ``textile-v2`` is the MVP Textile
# DPP v2 (2025-12-04) rule pack at v0.7.
#
# The CLI ``validate --profile`` flag selects the active profile;
# ``SemanticValidator`` consults this table when ``profile`` is set.
# The default profile is ``textile-v1`` for back-compat with pre-
# Phase-7 callers.
TEXTILE_PROFILES: dict[str, list] = {
    # ``textile-v1`` uses the v0.7-shaped legacy textile pack (the
    # original pre-Phase-7 textile rules ported to v0.7 envelope
    # access in ``rules/v0_7/textile.py``). The v0.6 pack is still
    # available via :data:`TEXTILE_RULES`, but mixing v0.6 textile
    # rules with a v0.7 engine produces wrong-envelope crashes.
    "textile-v1": list(TEXTILE_RULES_V0_7),
    "textile-v2": list(TEXTILE_RULES_V0_7_V2),
}

# Stable canonical name for the default textile profile. Pinned
# here so the CLI / tests can reference it without hardcoding.
DEFAULT_TEXTILE_PROFILE = "textile-v1"

__all__ = [
    "ALL_RULES",
    "ALL_RULES_BY_VERSION",
    "ALL_RULES_V0_6",
    "ALL_RULES_V0_7",
    # Phase 7 textile profile dispatch
    "DEFAULT_TEXTILE_PROFILE",
    "TEXTILE_PROFILES",
    "TEXTILE_RULES_V0_7_V2",
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
