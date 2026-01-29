"""Material provenance models for UNTP DPP."""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import Field, model_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.primitives import Classification, Link, Measure


class Material(UNTPBaseModel):
    """Material origin and mass fraction information."""

    _jsonld_type: ClassVar[list[str]] = ["Material"]

    name: str = Field(..., description="Material name (e.g., 'Egyptian Cotton')")
    origin_country: Annotated[
        str | None,
        Field(
            default=None,
            alias="originCountry",
            description="ISO 3166-1 country of origin",
        ),
    ]
    material_type: Annotated[
        Classification | None,
        Field(
            default=None,
            alias="materialType",
            description="Material classification (e.g., UNFC)",
        ),
    ]
    mass_fraction: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            le=1,
            alias="massFraction",
            description="Mass fraction of product (0-1, sum should equal 1)",
        ),
    ]
    mass: Measure | None = Field(default=None, description="Mass of the material component")
    recycled_mass_fraction: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            le=1,
            alias="recycledMassFraction",
            description="Fraction of material that is recycled (0-1)",
        ),
    ]
    hazardous: bool | None = Field(
        default=None,
        description="Whether material is hazardous",
    )
    symbol: str | None = Field(
        default=None,
        description="Base64 encoded visual symbol for the material",
    )
    material_safety_information: Annotated[
        Link | None,
        Field(
            default=None,
            alias="materialSafetyInformation",
            description="Link to material safety data sheet",
        ),
    ]

    @model_validator(mode="after")
    def validate_hazardous_requires_safety_info(self) -> Material:
        """Ensure hazardous materials have safety information."""
        if self.hazardous and not self.material_safety_information:
            raise ValueError("materialSafetyInformation is required when hazardous is true")
        return self
