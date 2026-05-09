"""LCA types for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.9 of [docs/plans/CIRPASS_2_MIGRATION.md] (resolves G8).
Models the v1.9.4-Maki LCA module's user-facing surface —
:class:`LifeCycleAssessment`, :class:`ImpactResult`,
:class:`ImpactCategoryReference` — for ESPR Annex I impact categories
and PEF / EN 15804 results.

The full v1.9.4-Maki LCA class set (33 classes) is rich; this module
exposes the *message-level* surface that a CIRPASS payload carries.
The full ontology surface lives in
:mod:`dppvalidator.vocabularies.eudpp_lca`; SHACL-driven validation
of LCA payloads against the bundled TTL is Phase 4 territory.
"""

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar

from pydantic import Field

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.cirpass.v1_3.i18n import LocalisedText
from dppvalidator.models.cirpass.v1_3.temporal import EffectivePeriod
from dppvalidator.vocabularies.eudpp_lca import LCIAImpactCategory


class ImpactCategoryReference(UNTPBaseModel):
    """A reference to a PEF / EN 15804 impact category.

    Wire shape:
        ``{"category": "eudpp:climateChange",
           "name": [{"value": "Climate change", "language": "en"}]}``

    The ``category`` field is a compact ``eudpp:`` IRI from
    :class:`dppvalidator.vocabularies.eudpp_lca.LCIAImpactCategory`
    (the v1.9.4-Maki canonical set: 16 PEF/EN15804+A2 individuals).
    Legacy v2.0 ``lca:`` IRIs are tolerated here for back-compat with
    UNTP-sourced payloads — the Phase 5 mapping shim translates them.
    """

    _jsonld_type: ClassVar[list[str]] = ["ImpactCategoryReference"]

    category: str = Field(
        ...,
        description=(
            "Compact ``eudpp:`` IRI of the impact category (canonical "
            "v1.9.4-Maki). Legacy ``lca:`` IRIs accepted for back-compat."
        ),
    )
    name: list[LocalisedText] | None = Field(
        default=None,
        description="Human-readable display name(s) of the impact category.",
    )

    @property
    def category_enum(self) -> LCIAImpactCategory | None:
        """Return the :class:`LCIAImpactCategory` member if ``category`` matches one.

        Returns ``None`` for category IRIs outside the canonical
        v1.9.4-Maki set (e.g. legacy ``lca:`` IRIs, or downstream
        taxonomies that extend the impact-category hierarchy).
        """
        try:
            return LCIAImpactCategory(self.category)
        except ValueError:
            return None


class ImpactResult(UNTPBaseModel):
    """A single quantified environmental impact result.

    Wire shape:
        ``{"impactCategory": <ImpactCategoryReference>,
           "value": 12.34, "unit": "kg_CO2_eq"}``

    Pairs an impact-category reference with a numeric value + unit.
    The ``unit`` field is a free-string for now (PEF 3.1 conventions
    use shorthand like ``kg_CO2_eq``, ``CTUe``); UNECE Rec20 / QUDT
    normalisation is enforced at the validator layer (Phase 4 LCS
    rule pack).
    """

    _jsonld_type: ClassVar[list[str]] = ["ImpactResult"]

    impact_category: ImpactCategoryReference = Field(
        ...,
        alias="impactCategory",
        description="The PEF / EN 15804 impact category quantified.",
    )
    value: Decimal = Field(..., description="The numeric impact value.")
    unit: str = Field(
        ...,
        description=(
            "Unit of measurement (``kg_CO2_eq``, ``CTUe``, …). PEF 3.1 "
            "conventions; Phase 4 enforces UNECE Rec20 / QUDT alignment."
        ),
    )


class LifeCycleAssessment(UNTPBaseModel):
    """A complete LCA / EPD attached to a product.

    Maps to ``eudpp:LCAStudy`` (LCA v1.9.4-Maki). Carries one or more
    impact results plus optional methodology metadata. Phase 4 wires
    SHACL validation of the impact-result set against the bundled
    LCA shape graph.

    Wire shape (minimal):
        ``{"results": [<ImpactResult>, ...]}``

    Cardinality:

    - ``results``: required (≥1).
    - ``methodology``: optional — short label (``PEF 3.1``,
      ``EN 15804+A2``, …) or compact IRI of an
      :class:`dppvalidator.vocabularies.eudpp_lca.LCAClass`
      ``LCIAMethodology`` instance.
    - ``referencePeriod``: optional — when the LCA result was
      computed (production batch, study window, etc.).
    """

    _jsonld_type: ClassVar[list[str]] = ["LifeCycleAssessment"]

    results: list[ImpactResult] = Field(
        ...,
        min_length=1,
        description="The quantified impact results.",
    )
    methodology: str | None = Field(
        default=None,
        description=(
            "LCA methodology label or compact IRI (``PEF 3.1``, ``eudpp:LCIAMethodology``, …)."
        ),
    )
    reference_period: EffectivePeriod | None = Field(
        default=None,
        alias="referencePeriod",
        description="The temporal scope of the LCA results.",
    )
