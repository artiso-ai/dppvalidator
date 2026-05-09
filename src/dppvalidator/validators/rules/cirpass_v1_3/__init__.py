"""Semantic validation rules for the CIRPASS DPP reference structure v1.3.0.

Phase 4 of [docs/plans/CIRPASS_2_MIGRATION.md]. The CIRPASS rule tree
mirrors the per-module shape of EUDPP v1.9.1 / v1.9.4-Maki:

- :mod:`base`        — root structural rules (codes ``CR001``…).
- :mod:`substances`  — SOC v1.9.1 rules (codes ``SUB001``…).
- :mod:`lca`         — LCA v1.9.4-Maki rules (codes ``LCS001``…).
- :mod:`actor`       — ACTOR v1.9.1 rules (codes ``ACT001``…).
- :mod:`connector`   — CON v1.9.1 cross-module relation rules (``REL001``…).

Code prefixes are *non-colliding with module names* per the Phase 4
audit table in the migration plan: ``SUB`` (avoiding ``SOC``),
``LCS`` (avoiding ``LCA``), ``REL`` (avoiding ``CON``).

Pipeline dispatch (Phase 4.7):

The CIRPASS pipeline is selected by the engine via the
``_PIPELINE_BY_FAMILY`` table; the ordered tuple
:data:`ALL_RULES_CIRPASS_V1_3` is consumed by
:class:`dppvalidator.validators.semantic.SemanticValidator` when
``schema_version == "1.3.0"`` (and the resolved family is CIRPASS).
"""

from __future__ import annotations

from dppvalidator.validators.rules.cirpass_v1_3.actor import (
    ALL_ACTOR_RULES,
    ActorIdentificationRule,
    ActorRoleAssignmentTemporalRule,
    ActorRoleClosureRule,
    MandatoryEconomicOperatorRule,
)
from dppvalidator.validators.rules.cirpass_v1_3.base import (
    ALL_BASE_RULES,
    BCP47LanguageTagRule,
    DPPIdentifierUniqueRule,
    EffectivePeriodMonotonicRule,
    IssuedAtBeforeEffectiveRule,
    PreviousDPPDistinctRule,
    ProductIdentifierShapeRule,
)
from dppvalidator.validators.rules.cirpass_v1_3.connector import (
    ALL_CONNECTOR_RULES,
    ConnectorRelationTemporalRule,
    ConnectorRelationTypeClosureRule,
    ConnectorSubjectObjectDistinctRule,
)
from dppvalidator.validators.rules.cirpass_v1_3.lca import (
    ALL_LCA_RULES,
    ImpactCategoryClosureRule,
    LCAResultsPresentRule,
    LCAUnitNormalisationRule,
    ReferencePeriodMonotonicRule,
)
from dppvalidator.validators.rules.cirpass_v1_3.substances import (
    ALL_SUBSTANCE_RULES,
    HazardCategoryClosureRule,
    LifeCycleStageClosureRule,
    MassFractionConcentrationBoundRule,
    SubstanceIdentificationRule,
)

# Dispatched by ``SemanticValidator`` when the engine is on the CIRPASS
# pipeline at version 1.3.0. Order is module-by-module so that error
# reports are grouped logically (root → SOC → LCA → ACTOR → CON).
ALL_RULES_CIRPASS_V1_3: tuple[object, ...] = (
    *ALL_BASE_RULES,
    *ALL_SUBSTANCE_RULES,
    *ALL_LCA_RULES,
    *ALL_ACTOR_RULES,
    *ALL_CONNECTOR_RULES,
)

# Public, version-keyed dispatch table consumed by
# :class:`SemanticValidator` when the resolved family is CIRPASS.
ALL_RULES_BY_VERSION_CIRPASS: dict[str, tuple[object, ...]] = {
    "1.3.0": ALL_RULES_CIRPASS_V1_3,
}

__all__ = [
    "ALL_ACTOR_RULES",
    "ALL_BASE_RULES",
    "ALL_CONNECTOR_RULES",
    "ALL_LCA_RULES",
    "ALL_RULES_BY_VERSION_CIRPASS",
    "ALL_RULES_CIRPASS_V1_3",
    "ALL_SUBSTANCE_RULES",
    # base (CR)
    "BCP47LanguageTagRule",
    "DPPIdentifierUniqueRule",
    "EffectivePeriodMonotonicRule",
    "IssuedAtBeforeEffectiveRule",
    "PreviousDPPDistinctRule",
    "ProductIdentifierShapeRule",
    # substances (SUB)
    "HazardCategoryClosureRule",
    "LifeCycleStageClosureRule",
    "MassFractionConcentrationBoundRule",
    "SubstanceIdentificationRule",
    # lca (LCS)
    "ImpactCategoryClosureRule",
    "LCAResultsPresentRule",
    "LCAUnitNormalisationRule",
    "ReferencePeriodMonotonicRule",
    # actor (ACT)
    "ActorIdentificationRule",
    "ActorRoleAssignmentTemporalRule",
    "ActorRoleClosureRule",
    "MandatoryEconomicOperatorRule",
    # connector (REL)
    "ConnectorRelationTemporalRule",
    "ConnectorRelationTypeClosureRule",
    "ConnectorSubjectObjectDistinctRule",
]
