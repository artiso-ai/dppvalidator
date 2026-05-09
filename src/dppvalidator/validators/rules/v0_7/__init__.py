"""Semantic validation rules for UNTP v0.7.0.

Phase 3b of docs/plans/UNTP_0.7.0_MIGRATION.md added this subpackage to
hold semantic rules adapted to the v0.7.0 model shape. Each rule walks
the new envelope (``credentialSubject`` is :class:`Product` directly,
``materialProvenance`` is the singular noun, scorecards collapse into
``performanceClaim``). Rules whose underlying field/class no longer
exists in v0.7 are dropped — see
:data:`dppvalidator.validators.rules.v0_7.base.DROPPED_RULES_V0_6_TO_V0_7`.

The v0.7 :data:`ALL_RULES_V0_7` list mirrors the v0.6 default-set with
those drops applied (e.g. ``OperationalScopeRule``).
"""

from __future__ import annotations

from dppvalidator.validators.rules.v0_7.base import (
    DROPPED_RULES_V0_6_TO_V0_7,
    CircularityContentRule,
    ConformityClaimRule,
    GranularitySerialNumberRule,
    GTINChecksumRule,
    HazardousMaterialRule,
    HSCodeRule,
    MassFractionSumRule,
    MaterialCodeRule,
    ValidityDateRule,
)
from dppvalidator.validators.rules.v0_7.cirpass import (
    CIRPASS_RULES_V0_7,
    CIRPASSGranularityConsistencyRule,
    CIRPASSMandatoryAttributesRule,
    CIRPASSOperatorIdentifierRule,
    CIRPASSSubstancesOfConcernRule,
    CIRPASSValidityPeriodRule,
    CIRPASSWeightVolumeRule,
)
from dppvalidator.validators.rules.v0_7.party_role import (
    SUGGESTED_STRICT_REMAP,
    PartyRoleAcceptanceGradientRule,
)
from dppvalidator.validators.rules.v0_7.textile import (
    TEXTILE_RULES_V0_7,
    TextileCareInstructionsRule,
    TextileDurabilityRule,
    TextileEnvironmentalCategory,
    TextileHSCodeRule,
    TextileMaterialCompositionRule,
    TextileMicroplasticRule,
    is_textile_product,
)
from dppvalidator.validators.rules.v0_7.textile_v2 import (
    TEXTILE_RULES_V0_7_V2,
    TextileV2CareInstructionsRule,
    TextileV2DurabilityRule,
    TextileV2HSCodeRule,
    TextileV2MaterialCompositionRule,
    TextileV2MicroplasticRule,
    TextileV2RecycledContentRule,
    TextileV2RepairInfoRule,
    is_textile_product_v2,
)

# v0.7 default rule list. Note the absence of OperationalScopeRule
# (SEM007 — folded into Claim/Performance in v0.7; see DROPPED_RULES).
ALL_RULES_V0_7 = [
    # Base UNTP rules (v0.7 shape)
    MassFractionSumRule(),
    ValidityDateRule(),
    HazardousMaterialRule(),
    CircularityContentRule(),
    ConformityClaimRule(),
    GranularitySerialNumberRule(),
    MaterialCodeRule(),
    HSCodeRule(),
    GTINChecksumRule(),
    # PRT-coded acceptance-gradient advisory rule (Phase 9 task 9.8)
    PartyRoleAcceptanceGradientRule(),
    # CIRPASS-2 CQ-coded rules (v0.7 shape)
    *CIRPASS_RULES_V0_7,
]

__all__ = [
    "ALL_RULES_V0_7",
    "DROPPED_RULES_V0_6_TO_V0_7",
    # Base
    "CircularityContentRule",
    "ConformityClaimRule",
    "GTINChecksumRule",
    "GranularitySerialNumberRule",
    "HSCodeRule",
    "HazardousMaterialRule",
    "MassFractionSumRule",
    "MaterialCodeRule",
    "ValidityDateRule",
    # CIRPASS
    "CIRPASS_RULES_V0_7",
    "CIRPASSGranularityConsistencyRule",
    "CIRPASSMandatoryAttributesRule",
    "CIRPASSOperatorIdentifierRule",
    "CIRPASSSubstancesOfConcernRule",
    "CIRPASSValidityPeriodRule",
    "CIRPASSWeightVolumeRule",
    # PartyRole acceptance gradient (Phase 9 task 9.8)
    "PartyRoleAcceptanceGradientRule",
    "SUGGESTED_STRICT_REMAP",
    # Textile v1
    "TEXTILE_RULES_V0_7",
    "TextileCareInstructionsRule",
    "TextileDurabilityRule",
    "TextileEnvironmentalCategory",
    "TextileHSCodeRule",
    "TextileMaterialCompositionRule",
    "TextileMicroplasticRule",
    "is_textile_product",
    # Textile v2 (Phase 7)
    "TEXTILE_RULES_V0_7_V2",
    "TextileV2CareInstructionsRule",
    "TextileV2DurabilityRule",
    "TextileV2HSCodeRule",
    "TextileV2MaterialCompositionRule",
    "TextileV2MicroplasticRule",
    "TextileV2RecycledContentRule",
    "TextileV2RepairInfoRule",
    "is_textile_product_v2",
]
