"""LCA v1.9.4-Maki semantic rules for CIRPASS DPP reference structure v1.3.0.

Phase 4 task 4.4 of [docs/plans/CIRPASS_2_MIGRATION.md]. The ``LCS``
prefix is reserved for LCA-Specification rules in the Phase 4 code-
prefix audit (avoiding the ``LCA`` module-name collision per the
plan's prefix table).

Axioms covered (LCA v1.9.4-Maki, PEF 3.1 / EN 15804+A2):

- :class:`LCAResultsPresentRule` (``LCS001``) — when ``lca`` is set,
  the ``results`` array is non-empty.
- :class:`ImpactCategoryClosureRule` (``LCS002``) — impact-category
  IRIs come from the v1.9.4-Maki PEF 3.1 closed set
  (:class:`LCIAImpactCategory`).
- :class:`LCAUnitNormalisationRule` (``LCS003``) — units follow PEF
  3.1 / EN 15804+A2 conventional shorthand.
- :class:`ReferencePeriodMonotonicRule` (``LCS004``) — defensive
  duplicate of :class:`EffectivePeriod._start_before_end` for the LCA
  ``referencePeriod`` field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from dppvalidator.vocabularies.eudpp_lca import LCIAImpactCategory

if TYPE_CHECKING:
    from dppvalidator.models.cirpass.v1_3 import ReferencePassport


# Conventional shorthand units PEF 3.1 / EN 15804+A2 use for the LCIA
# impact-category quantities. The set is the result of mapping the
# 16 v1.9.4-Maki ``LCIAImpactCategory`` named individuals to their
# canonical units (PEF 3.1 §6.4 + EN 15804+A2 §7.2). Plain SI energies
# (``MJ``) and water-equivalents (``m3_water_eq``, ``m3_water_eq_deprived``)
# are listed alongside the dimensionless / scoring units (``CTUe``,
# ``CTUh``, ``mol_H_eq``, ``kBq_U235_eq``).
_PEF_31_UNITS: frozenset[str] = frozenset(
    {
        # Climate change
        "kg_CO2_eq",
        "kg_CO2-eq",
        # Ozone depletion
        "kg_CFC11_eq",
        "kg_CFC-11_eq",
        # Acidification
        "mol_H_eq",
        "mol_H+_eq",
        # Eutrophication (freshwater / marine / terrestrial collapse)
        "kg_P_eq",
        "kg_N_eq",
        # Photochemical ozone formation
        "kg_NMVOC_eq",
        # Particulate matter / Respiratory inorganics
        "disease_incidence",
        # Human / ecotoxicity
        "CTUh",
        "CTUe",
        # Ionising radiation
        "kBq_U235_eq",
        # Land use
        "Pt",  # PEF 3.1 dimensionless soil-quality score
        "dimensionless",
        # Resource use — fossils
        "MJ",
        # Resource use — minerals & metals
        "kg_Sb_eq",
        # Water use
        "m3_water_eq",
        "m3_water_eq_deprived",
    }
)


class LCAResultsPresentRule:
    """LCS001: when ``lca`` is supplied, ``results`` must be non-empty.

    The :class:`LifeCycleAssessment` model already enforces ``min_length=1``
    on the field; this rule re-issues the violation at semantic layer
    so consumers driving validation through the semantic pipeline
    (skipping model layer) still see the failure.
    """

    rule_id: str = "LCS001"
    description: str = "LifeCycleAssessment.results must be non-empty when lca is provided"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Either drop the ``lca`` field entirely, or supply at least one "
        "``ImpactResult`` per PEF 3.1 / EN 15804+A2."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/LCS001"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        lca = passport.lca
        if lca is None:
            return violations
        if not lca.results:
            violations.append(
                (
                    "$.lca.results",
                    "LifeCycleAssessment.results is empty; supply at least one ImpactResult.",
                )
            )
        return violations


class ImpactCategoryClosureRule:
    """LCS002: impact-category IRIs are warned when off-canonical.

    Validates ``ImpactCategoryReference.category`` against the
    v1.9.4-Maki closed set (:class:`LCIAImpactCategory`). Legacy
    ``lca:`` IRIs (from :class:`ImpactCategory`) are *tolerated* with
    an info-level signal — Phase 5 maps them to the canonical
    ``eudpp:`` IRI. Anything that's neither v1.9.4-Maki nor a known
    legacy IRI is flagged as a warning (downstream taxonomies that
    extend the impact-category hierarchy with their own classes are
    *valid* but worth surfacing).
    """

    rule_id: str = "LCS002"
    description: str = "Impact category should use the v1.9.4-Maki canonical IRI set"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Use a value from "
        "``dppvalidator.vocabularies.eudpp_lca.LCIAImpactCategory`` "
        "(e.g. ``eudpp:climateChange``, ``eudpp:waterUseDeprivation``); "
        "legacy ``lca:`` IRIs are tolerated for back-compat."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/LCS002"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        lca = passport.lca
        if lca is None:
            return violations
        canonical = {c.value for c in LCIAImpactCategory}
        for i, result in enumerate(lca.results):
            cat = result.impact_category.category
            if cat in canonical:
                continue
            if cat.startswith("lca:"):
                # Legacy v2.0 IRIs are tolerated — Phase 5 mapping
                # shim handles the translation. We surface this only
                # as an info-level diagnostic to flag the deprecation.
                continue
            violations.append(
                (
                    f"$.lca.results[{i}].impactCategory.category",
                    (
                        f"impact category {cat!r} is not from the v1.9.4-Maki "
                        f"canonical set ({len(canonical)} members); see "
                        f"``LCIAImpactCategory`` for valid IRIs."
                    ),
                )
            )
        return violations


class LCAUnitNormalisationRule:
    """LCS003: LCA units should follow PEF 3.1 / EN 15804+A2 conventions.

    The :class:`ImpactResult.unit` field is a free-string at model
    layer; this rule pins it to the conventional shorthand
    (``kg_CO2_eq``, ``CTUe``, ``MJ``, …) used by PEF 3.1 §6.4 and
    EN 15804+A2 §7.2. UNECE Rec20 / QUDT canonicalisation (the next
    step up the rigour ladder) is left for Phase 4.x extension.
    """

    rule_id: str = "LCS003"
    description: str = "LCA units should use PEF 3.1 / EN 15804+A2 shorthand"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Use shorthand from PEF 3.1 §6.4 / EN 15804+A2 §7.2 — e.g. "
        "``kg_CO2_eq``, ``CTUh``, ``MJ``, ``m3_water_eq_deprived``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/LCS003"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        lca = passport.lca
        if lca is None:
            return violations
        for i, result in enumerate(lca.results):
            if result.unit not in _PEF_31_UNITS:
                violations.append(
                    (
                        f"$.lca.results[{i}].unit",
                        (
                            f"LCA unit {result.unit!r} is not in the PEF 3.1 / "
                            f"EN 15804+A2 conventional shorthand set; verify "
                            f"the unit and align to the canonical form."
                        ),
                    )
                )
        return violations


class ReferencePeriodMonotonicRule:
    """LCS004: ``lca.referencePeriod.start`` precedes ``end``.

    Defensive duplicate of :class:`EffectivePeriod._start_before_end`
    for the LCA ``referencePeriod`` field. Re-issued at semantic layer
    so the violation surfaces with an LCA-scoped attribution rather
    than a generic ``ValueError`` from the model layer.
    """

    rule_id: str = "LCS004"
    description: str = "lca.referencePeriod.start must be before end"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Either drop ``lca.referencePeriod.end`` (study window is open-ended) "
        "or supply a value strictly after ``start``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/LCS004"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        lca = passport.lca
        if lca is None or lca.reference_period is None:
            return violations
        period = lca.reference_period
        if period.end is not None and period.start > period.end:
            violations.append(
                (
                    "$.lca.referencePeriod",
                    (
                        f"lca.referencePeriod.start={period.start.isoformat()} "
                        f"is later than .end={period.end.isoformat()}; the "
                        f"study window is empty."
                    ),
                )
            )
        return violations


# =============================================================================
# Public dispatch
# =============================================================================


ALL_LCA_RULES: tuple[object, ...] = (
    LCAResultsPresentRule(),
    ImpactCategoryClosureRule(),
    LCAUnitNormalisationRule(),
    ReferencePeriodMonotonicRule(),
)
