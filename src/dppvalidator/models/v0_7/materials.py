"""Material provenance for UNTP v0.7.0.

Compared to v0.6.x:

- ``materialType``, ``originCountry``, and ``massFraction`` are now
  **required** (per the upstream schema). v0.6.x permitted all three to be
  absent. The Phase 4 compatibility shim emits an ``UPG004`` warning when
  upgrading legacy data that lacks any of these.
- ``originCountry`` shape moved from a bare ISO-3166 string (``"DE"``) to a
  :class:`Country` object (``{"countryCode": "DE", "countryName": "Germany"}``).
- ``symbol`` moved from a bare base64 string to a structured
  :class:`Image` (``{"contentType": …, "content": …}``).

Cross-field invariants (per the plan):

- ``hazardous=True`` requires ``materialSafetyInformation`` (port of the
  v0.6.x SEM-class rule into a model-level invariant).
- Mass-fraction sum across an array of ``Material`` lives at the parent
  (Product) level, not here — see :class:`dppvalidator.models.v0_7.product.Product`.
"""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import Field, model_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.v0_7.identifiers import Country
from dppvalidator.models.v0_7.primitives import (
    Classification,
    Image,
    Link,
    Measure,
)


class Material(UNTPBaseModel):
    """Origin and composition info for one material in a product.

    Required: ``name``, ``originCountry``, ``materialType``, ``massFraction``.
    Optional fields fill in mass / safety / recycled-content metadata.
    """

    _jsonld_type: ClassVar[list[str]] = ["Material"]

    name: str = Field(..., description="Material name (e.g. 'Egyptian Cotton').")
    origin_country: Annotated[
        Country,
        Field(
            ...,
            alias="originCountry",
            description="ISO-3166 country of origin (now structured, was a bare string in v0.6.x).",
        ),
    ]
    material_type: Annotated[
        Classification,
        Field(
            ...,
            alias="materialType",
            description="Classification of the material (e.g. drawn from UNFC).",
        ),
    ]
    mass_fraction: Annotated[
        float,
        Field(
            ...,
            ge=0,
            le=1,
            alias="massFraction",
            description="Mass fraction of the product represented by this material (0..1).",
        ),
    ]
    mass: Measure | None = Field(
        default=None, description="Optional absolute mass of the material."
    )
    recycled_mass_fraction: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            le=1,
            alias="recycledMassFraction",
            description="Fraction of this material that is recycled content (0..1).",
        ),
    ]
    hazardous: bool | None = Field(
        default=None,
        description="Whether the material is hazardous (drives the ``materialSafetyInformation`` requirement).",
    )
    symbol: Annotated[
        Image | None,
        Field(
            default=None,
            description="Visual symbol for the material (was a bare base64 string in v0.6.x).",
        ),
    ]
    material_safety_information: Annotated[
        Link | None,
        Field(
            default=None,
            alias="materialSafetyInformation",
            description="Link to a material safety data sheet — required when ``hazardous`` is true.",
        ),
    ]

    @model_validator(mode="after")
    def _hazardous_implies_safety_info(self) -> Material:
        if self.hazardous and self.material_safety_information is None:
            raise ValueError(
                "Material.materialSafetyInformation is required when ``hazardous`` is true.",
            )
        return self
