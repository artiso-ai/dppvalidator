"""Product-related models for UNTP DPP."""

from __future__ import annotations

from datetime import date
from typing import Annotated, ClassVar

from pydantic import Field

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.identifiers import Facility, IdentifierScheme, Party
from dppvalidator.models.primitives import Classification, FlexibleUri, Link, Measure


class Dimension(UNTPBaseModel):
    """Physical dimensions (length, width, height) and weight/volume."""

    _jsonld_type: ClassVar[list[str]] = ["Dimension"]

    weight: Measure | None = Field(default=None, description="Weight of the product")
    length: Measure | None = Field(default=None, description="Length of the product")
    width: Measure | None = Field(default=None, description="Width of the product")
    height: Measure | None = Field(default=None, description="Height of the product")
    volume: Measure | None = Field(default=None, description="Displacement volume")


class Characteristics(UNTPBaseModel):
    """Extension point for industry/product-specific characteristics."""

    _jsonld_type: ClassVar[list[str]] = ["Characteristics"]


class Product(UNTPBaseModel):
    """Product information including identification and manufacturer details."""

    _jsonld_type: ClassVar[list[str]] = ["Product"]

    id: Annotated[
        FlexibleUri,
        Field(..., description="Globally unique ID of the product as a URI"),
    ]
    name: str = Field(..., description="Registered name of the product")
    registered_id: Annotated[
        str | None,
        Field(
            default=None,
            alias="registeredId",
            description="Registration number within the register",
        ),
    ]
    id_scheme: Annotated[
        IdentifierScheme | None,
        Field(default=None, alias="idScheme", description="Identifier scheme for this product"),
    ]
    batch_number: Annotated[
        str | None,
        Field(default=None, alias="batchNumber", description="Production batch identifier"),
    ]
    product_image: Annotated[
        Link | None,
        Field(default=None, alias="productImage", description="Reference to product image"),
    ]
    description: str | None = Field(default=None, description="Textual product description")
    characteristics: Characteristics | None = Field(
        default=None, description="Industry-specific characteristics"
    )
    product_category: Annotated[
        list[Classification] | None,
        Field(default=None, alias="productCategory", description="Product classification codes"),
    ]
    further_information: Annotated[
        list[Link] | None,
        Field(default=None, alias="furtherInformation", description="Additional information links"),
    ]
    produced_by_party: Annotated[
        Party | None,
        Field(default=None, alias="producedByParty", description="Manufacturing party"),
    ]
    produced_at_facility: Annotated[
        Facility | None,
        Field(default=None, alias="producedAtFacility", description="Manufacturing facility"),
    ]
    production_date: Annotated[
        date | None,
        Field(default=None, alias="productionDate", description="ISO 8601 production date"),
    ]
    country_of_production: Annotated[
        str | None,
        Field(
            default=None,
            alias="countryOfProduction",
            description="ISO 3166-1 country code of production",
        ),
    ]
    serial_number: Annotated[
        str | None,
        Field(default=None, alias="serialNumber", description="Serialised item identifier"),
    ]
    dimensions: Dimension | None = Field(default=None, description="Physical dimensions")
