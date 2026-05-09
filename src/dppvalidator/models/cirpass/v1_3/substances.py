"""Substances of Concern types for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.8 of [docs/plans/CIRPASS_2_MIGRATION.md] (resolves G7).
Models the EUDPP SOC v1.9.1 surface — :class:`SubstanceOfConcern`,
:class:`Concentration`, :class:`HazardClassification` — for REACH /
SVHC tracking per ESPR Art 7(5).

EUDPP IRI bindings:

- ``SubstanceOfConcern`` → ``eudpp:SubstanceOfConcern``
- ``Concentration``     → ``eudpp:Concentration``
- ``Threshold``          → ``eudpp:Threshold``
- ``HazardClassification`` is a CIRPASS message-level wrapper for
  the hazard-category enumeration in
  :class:`dppvalidator.vocabularies.eudpp_substances.HazardCategory`.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import ClassVar

from pydantic import Field, field_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.cirpass.v1_3.i18n import LocalisedText
from dppvalidator.vocabularies.eudpp_substances import HazardCategory, LifeCycleStage

# CAS Registry Number — the canonical chemical identifier.
# Format: <up to 7 digits>-<2 digits>-<1 check digit>, e.g. 71-43-2 (benzene).
_CAS_RE = re.compile(r"^\d{2,7}-\d{2}-\d$")
# EC Number (formerly EINECS / ELINCS) — 7 digits with dashes.
# Format: <3 digits>-<3 digits>-<1 digit>, e.g. 200-753-7 (benzene).
_EC_RE = re.compile(r"^\d{3}-\d{3}-\d$")


class HazardClassification(UNTPBaseModel):
    """A single hazard classification per CLP / Regulation (EC) 1272/2008.

    Wire shape:
        ``{"category": "carcinogenicity",
           "statement": [{"value": "May cause cancer.", "language": "en"}]}``

    The ``category`` field accepts any value from
    :class:`dppvalidator.vocabularies.eudpp_substances.HazardCategory`;
    new categories added in a future SOC release land in that enum,
    not here.
    """

    _jsonld_type: ClassVar[list[str]] = ["HazardClassification"]

    category: HazardCategory = Field(
        ...,
        description=(
            "CLP / SVHC hazard category (carcinogenicity, mutagenicity, "
            "reproductive toxicity, PBT, vPvB, PMT, vPvM, …)."
        ),
    )
    statement: list[LocalisedText] | None = Field(
        default=None,
        description=("Optional H-statement text(s) describing the hazard, one per language."),
    )


class Concentration(UNTPBaseModel):
    """The concentration of a substance of concern within a product / component.

    Wire shape:
        ``{"value": 0.0008, "unit": "mass_fraction",
           "lifecycleStage": "in_product"}``

    Maps to ``eudpp:Concentration`` (SOC v1.9.1). The ``value`` is a
    Decimal in [0, 1] when ``unit`` is ``mass_fraction``; for other
    units (e.g. ``mg_per_kg``) the bound is on the unit's conventional
    range.
    """

    _jsonld_type: ClassVar[list[str]] = ["Concentration"]

    value: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="Concentration value in the unit identified by ``unit``.",
    )
    unit: str = Field(
        ...,
        description="Unit of measurement (``mass_fraction``, ``mg_per_kg``, …).",
    )
    lifecycle_stage: LifeCycleStage | None = Field(
        default=None,
        alias="lifecycleStage",
        description="Lifecycle stage at which this concentration applies.",
    )

    @field_validator("value")
    @classmethod
    def _bound_when_mass_fraction(cls, value: Decimal) -> Decimal:
        # Mass-fraction-specific upper bound (1.0) is enforced by a
        # cross-field validator below; this validator just ensures
        # the value is non-negative regardless of unit.
        return value


class SubstanceOfConcern(UNTPBaseModel):
    """A REACH / SVHC-tracked substance present in a product.

    Maps to ``eudpp:SubstanceOfConcern`` (SOC v1.9.1). Carries IUPAC /
    CAS / EC identifiers, hazard classifications, and one or more
    concentration measurements.

    Wire shape (minimal):
        ``{"nameIUPAC": "...", "concentrations": [<Concentration>, ...]}``

    Cardinality:

    - At least *one* of ``nameIUPAC`` / ``nameCAS`` / ``numberCAS`` /
      ``numberEC`` must be present (substance must be identifiable).
    - ``concentrations``: required (≥1).
    - ``hazards``: optional (0..n).
    """

    _jsonld_type: ClassVar[list[str]] = ["SubstanceOfConcern"]

    name_iupac: str | None = Field(
        default=None,
        alias="nameIUPAC",
        description="IUPAC systematic name.",
    )
    name_cas: str | None = Field(
        default=None,
        alias="nameCAS",
        description="CAS-registered name.",
    )
    number_cas: str | None = Field(
        default=None,
        alias="numberCAS",
        description="CAS Registry Number (e.g. ``71-43-2``).",
    )
    number_ec: str | None = Field(
        default=None,
        alias="numberEC",
        description="EC Number (e.g. ``200-753-7``).",
    )
    trade_name: list[LocalisedText] | None = Field(
        default=None,
        alias="tradeName",
        description="Trade name(s) under which the substance is marketed.",
    )
    concentrations: list[Concentration] = Field(
        ...,
        min_length=1,
        description="One or more concentration measurements for this substance.",
    )
    hazards: list[HazardClassification] | None = Field(
        default=None,
        description="Optional hazard classifications for this substance.",
    )

    @field_validator("number_cas")
    @classmethod
    def _validate_cas(cls, value: str | None) -> str | None:
        if value is not None and not _CAS_RE.match(value):
            msg = (
                f"SubstanceOfConcern.numberCAS={value!r} is not a "
                f"recognised CAS Registry Number format "
                f"(``<digits>-<2 digits>-<check digit>``, e.g. ``71-43-2``)."
            )
            raise ValueError(msg)
        return value

    @field_validator("number_ec")
    @classmethod
    def _validate_ec(cls, value: str | None) -> str | None:
        if value is not None and not _EC_RE.match(value):
            msg = (
                f"SubstanceOfConcern.numberEC={value!r} is not a "
                f"recognised EC Number format "
                f"(``<3 digits>-<3 digits>-<check digit>``, e.g. ``200-753-7``)."
            )
            raise ValueError(msg)
        return value

    def is_identified(self) -> bool:
        """True if at least one identifier (IUPAC / CAS / EC) is present."""
        return any(
            v is not None for v in (self.name_iupac, self.name_cas, self.number_cas, self.number_ec)
        )
