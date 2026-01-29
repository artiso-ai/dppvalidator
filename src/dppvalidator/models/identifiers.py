"""Identifier-related models for UNTP DPP."""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import Field

from dppvalidator.models.base import UNTPBaseModel, UNTPStrictModel
from dppvalidator.models.primitives import FlexibleUri


class IdentifierScheme(UNTPStrictModel):
    """Identifier registration scheme for products, facilities, or organisations."""

    _jsonld_type: ClassVar[list[str]] = ["IdentifierScheme"]

    id: Annotated[
        FlexibleUri | None,
        Field(
            default=None,
            description="Globally unique identifier of the registration scheme",
        ),
    ]
    name: Annotated[
        str | None,
        Field(default=None, description="Name of the identifier scheme"),
    ]


class Party(UNTPBaseModel):
    """A party (person or organisation) with identifier."""

    _jsonld_type: ClassVar[list[str]] = ["Party"]

    id: Annotated[
        FlexibleUri,
        Field(..., description="Globally unique ID of the party as a URI"),
    ]
    name: str = Field(..., description="Registered name of the party")
    registered_id: Annotated[
        str | None,
        Field(
            default=None,
            alias="registeredId",
            description="Registration number within the register",
        ),
    ]


class Facility(UNTPBaseModel):
    """A facility where products are manufactured."""

    _jsonld_type: ClassVar[list[str]] = ["Facility"]

    id: Annotated[
        FlexibleUri,
        Field(..., description="Globally unique ID of the facility as URI"),
    ]
    name: str = Field(..., description="Registered name of the facility")
    registered_id: Annotated[
        str | None,
        Field(
            default=None,
            alias="registeredId",
            description="Registration number within the identifier scheme",
        ),
    ]
