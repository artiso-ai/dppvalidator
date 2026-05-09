"""Material and composition types for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.7 of [docs/plans/CIRPASS_2_MIGRATION.md]. The MAT
module of EUDPP is **not yet published** as of v1.9.1 (see plan §1.1
"Not published" row), so material modelling here uses the closest
fit from the bundled v1.9.1 ontology + project-specific vocabularies
(ISO 2076 fibre codes, ISO 3166 country codes).

When EUDPP MAT lands in a follow-on release, the §13 add-module
recipe applies: this file's class IRI bindings flip to the canonical
``eudpp:Material`` URI; the rest of the surface stays.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import ClassVar

from pydantic import Field, field_validator, model_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.cirpass.v1_3.i18n import LocalisedText

# ISO 3166-1 alpha-2 country codes (two ASCII uppercase letters).
_ISO_3166_ALPHA2_RE = re.compile(r"^[A-Z]{2}$")
# ISO 2076 textile-fibre codes (two ASCII uppercase letters; e.g. CO=Cotton).
_ISO_2076_RE = re.compile(r"^[A-Z]{2}$")


class Material(UNTPBaseModel):
    """A constituent material of a product.

    Wire shape:
        ``{"materialName": [...], "materialType": "CO",
           "originCountry": "DE", "massFraction": 0.62,
           "isRecycled": true}``

    Cardinality:

    - ``materialName``: required (≥1) — multilingual name of the
      material.
    - ``materialType``: optional ISO 2076 fibre / material code
      (``CO`` = Cotton, ``EL`` = Elastane, …). Bare-string per ISO
      convention; not wrapped in :class:`LocalisedText`.
    - ``originCountry``: optional ISO-3166-1 alpha-2 country code.
    - ``massFraction``: optional Decimal in [0, 1]; sum of all
      ``massFraction`` values across a product's materials should be
      ≤ 1.0 (validated cross-component, not on a single Material).
    - ``isRecycled``: optional flag; True ⇒ material is reclaimed /
      post-consumer.
    """

    _jsonld_type: ClassVar[list[str]] = ["Material"]

    material_name: list[LocalisedText] = Field(
        ...,
        alias="materialName",
        min_length=1,
        description="Material name(s), one per language.",
    )
    material_type: str | None = Field(
        default=None,
        alias="materialType",
        description="ISO 2076 textile-fibre code or equivalent material code.",
    )
    origin_country: str | None = Field(
        default=None,
        alias="originCountry",
        description="ISO-3166-1 alpha-2 country code of material origin.",
    )
    mass_fraction: Decimal | None = Field(
        default=None,
        alias="massFraction",
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Mass fraction in [0, 1]; recycle/composition share.",
    )
    is_recycled: bool | None = Field(
        default=None,
        alias="isRecycled",
        description="True if the material is reclaimed / post-consumer recycled.",
    )

    @field_validator("material_type")
    @classmethod
    def _validate_material_type(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not _ISO_2076_RE.match(value):
            msg = (
                f"Material.materialType={value!r} is not a 2-letter ISO "
                f"2076 code (e.g. ``CO`` for Cotton). Use the bare ISO "
                f"code, not the human-readable name."
            )
            raise ValueError(msg)
        return value

    @field_validator("origin_country")
    @classmethod
    def _validate_origin_country(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not _ISO_3166_ALPHA2_RE.match(value):
            msg = f"Material.originCountry={value!r} is not a 2-letter ISO-3166-1 alpha-2 code."
            raise ValueError(msg)
        return value


class Composition(UNTPBaseModel):
    """The full material composition of a product.

    Wire shape:
        ``{"materials": [<Material>, ...]}``

    The mass-fraction sum invariant is enforced at this level: across
    all entries with non-null ``massFraction``, the sum must be ≤ 1.0
    (slightly less than 1 is valid — non-mass-bearing constituents
    don't carry a fraction).
    """

    _jsonld_type: ClassVar[list[str]] = ["Composition"]

    materials: list[Material] = Field(
        ...,
        min_length=1,
        description="The materials that constitute the product.",
    )

    @model_validator(mode="after")
    def _mass_fractions_sum_within_one(self) -> Composition:
        total = sum(
            (m.mass_fraction for m in self.materials if m.mass_fraction is not None),
            start=Decimal("0"),
        )
        # Allow tiny floating-error tolerance — the spec is a sum of
        # Decimals so exact 1.0 is normal, but 0.9999999 rounding is
        # also seen in upstream feeds.
        if total > Decimal("1.0001"):
            msg = (
                f"Composition.materials mass fractions sum to {total} "
                f"(> 1.0). The sum across all materials with a non-null "
                f"massFraction must be ≤ 1.0."
            )
            raise ValueError(msg)
        return self
