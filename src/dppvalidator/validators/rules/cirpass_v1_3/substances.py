"""SOC v1.9.1 semantic rules for CIRPASS DPP reference structure v1.3.0.

Phase 4 task 4.3 of [docs/plans/CIRPASS_2_MIGRATION.md]. The ``SUB``
prefix is reserved for substance rules in the Phase 4 code-prefix
audit (avoiding the ``SOC`` module-name collision per the plan's
prefix table).

Axioms covered (SOC v1.9.1, ESPR Art 7(5) / Art 2(28)):

- :class:`SubstanceIdentificationRule` (``SUB001``) — every SOC entry
  carries at least one identifier (IUPAC / CAS-name / CAS-number /
  EC-number).
- :class:`HazardCategoryClosureRule` (``SUB002``) — hazard categories
  use closed enumerations from the bundled
  :class:`HazardCategory`.
- :class:`MassFractionConcentrationBoundRule` (``SUB003``) —
  ``mass_fraction``-unit concentrations are bounded to [0, 1].
- :class:`LifeCycleStageClosureRule` (``SUB004``) — lifecycle stages
  use closed enumerations from the bundled :class:`LifeCycleStage`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from dppvalidator.vocabularies.eudpp_substances import HazardCategory, LifeCycleStage

if TYPE_CHECKING:
    from dppvalidator.models.cirpass.v1_3 import ReferencePassport


class SubstanceIdentificationRule:
    """SUB001: every substance of concern must be identifiable.

    Per ESPR Art 7(5), substances must be reportable by at least one
    of: IUPAC name, CAS name, CAS number, or EC number. The
    :class:`SubstanceOfConcern` model already exposes
    :meth:`is_identified` for this; the rule re-runs the check at
    semantic layer for parity with UNTP rule reporting.
    """

    rule_id: str = "SUB001"
    description: str = "Every SubstanceOfConcern must carry at least one identifier"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Populate at least one of ``nameIUPAC``, ``nameCAS``, ``numberCAS``, "
        "or ``numberEC`` per ESPR Art 7(5)."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SUB001"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        if not passport.substances_of_concern:
            return violations
        for i, soc in enumerate(passport.substances_of_concern):
            if not soc.is_identified():
                violations.append(
                    (
                        f"$.substancesOfConcern[{i}]",
                        (
                            "SubstanceOfConcern carries no identifier "
                            "(IUPAC / CAS / EC); per ESPR Art 7(5) it must "
                            "be identifiable by at least one."
                        ),
                    )
                )
        return violations


class HazardCategoryClosureRule:
    """SUB002: hazard categories must be from the closed CLP / SVHC set.

    The :class:`HazardClassification.category` field is typed as
    :class:`HazardCategory` (a string-enum), so model validation
    catches *most* mismatches. The rule fires when a passport has
    been constructed via ``model_construct`` (skipping validation)
    or post-processed in a way that demotes the field to a plain
    string — which is enough of a real risk in mapping-shim code
    that the closure check is worth doing at semantic layer too.
    """

    rule_id: str = "SUB002"
    description: str = "HazardClassification.category must be from the SOC v1.9.1 enum"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Use a value from "
        "``dppvalidator.vocabularies.eudpp_substances.HazardCategory`` "
        "(e.g. ``carcinogenicity_cat_1``, ``svhc_reach_art_57``)."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SUB002"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        if not passport.substances_of_concern:
            return violations
        valid = {c.value for c in HazardCategory}
        for i, soc in enumerate(passport.substances_of_concern):
            if not soc.hazards:
                continue
            for j, h in enumerate(soc.hazards):
                # The Pydantic field is typed HazardCategory, so at
                # runtime ``h.category`` is an enum member; we read its
                # ``.value`` if it has one, otherwise the bare string.
                category_value = getattr(h.category, "value", h.category)
                if category_value not in valid:
                    violations.append(
                        (
                            f"$.substancesOfConcern[{i}].hazards[{j}].category",
                            (
                                f"hazard category {category_value!r} is not in the "
                                f"SOC v1.9.1 closed set; see "
                                f"``HazardCategory`` for valid values."
                            ),
                        )
                    )
        return violations


class MassFractionConcentrationBoundRule:
    """SUB003: ``mass_fraction``-unit concentrations are bounded to [0, 1].

    The model enforces ``ge=0`` on every Concentration; the
    ``mass_fraction``-specific upper bound (1.0) is rule territory
    because some legitimate units (``mg_per_kg``, ``ppm``) carry
    larger values. Concentrations expressed as a fraction of total
    mass cannot exceed 100%.
    """

    rule_id: str = "SUB003"
    description: str = "mass_fraction concentrations must be ≤ 1.0"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Either correct the value (mass-fraction units are dimensionless and "
        "bounded to [0, 1]) or switch to a ratio unit such as ``mg_per_kg`` "
        "or ``ppm`` for values > 100%."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SUB003"

    _ONE: Decimal = Decimal("1")

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        if not passport.substances_of_concern:
            return violations
        for i, soc in enumerate(passport.substances_of_concern):
            for j, c in enumerate(soc.concentrations):
                if c.unit == "mass_fraction" and c.value > self._ONE:
                    violations.append(
                        (
                            f"$.substancesOfConcern[{i}].concentrations[{j}]",
                            (
                                f"concentration value {c.value} exceeds 1.0 for "
                                f"unit ``mass_fraction``; mass-fractions are "
                                f"bounded to [0, 1]."
                            ),
                        )
                    )
        return violations


class LifeCycleStageClosureRule:
    """SUB004: lifecycle stages must be from the closed enumeration.

    Mirror of :class:`HazardCategoryClosureRule` for the
    ``Concentration.lifecycleStage`` field. The model field is typed
    :class:`LifeCycleStage`; this rule runs at semantic layer for
    the same ``model_construct`` / shim-level safety net.
    """

    rule_id: str = "SUB004"
    description: str = "Concentration.lifecycleStage must be from the SOC enum"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Use a value from "
        "``dppvalidator.vocabularies.eudpp_substances.LifeCycleStage`` "
        "(``production``, ``in_product``, ``use``, ``end_of_life``, "
        "``waste``, ``recycling``)."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SUB004"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        if not passport.substances_of_concern:
            return violations
        valid = {s.value for s in LifeCycleStage}
        for i, soc in enumerate(passport.substances_of_concern):
            for j, c in enumerate(soc.concentrations):
                if c.lifecycle_stage is None:
                    continue
                stage_value = getattr(c.lifecycle_stage, "value", c.lifecycle_stage)
                if stage_value not in valid:
                    violations.append(
                        (
                            f"$.substancesOfConcern[{i}].concentrations[{j}].lifecycleStage",
                            (
                                f"lifecycleStage {stage_value!r} is not in the "
                                f"SOC closed set; see ``LifeCycleStage`` for "
                                f"valid values."
                            ),
                        )
                    )
        return violations


# =============================================================================
# Public dispatch
# =============================================================================


ALL_SUBSTANCE_RULES: tuple[object, ...] = (
    SubstanceIdentificationRule(),
    HazardCategoryClosureRule(),
    MassFractionConcentrationBoundRule(),
    LifeCycleStageClosureRule(),
)
