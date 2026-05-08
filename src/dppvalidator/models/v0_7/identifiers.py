"""Identifier and party-related types for UNTP v0.7.0.

Compared to v0.6.x:

- :class:`Country` is new. v0.6 stored ISO-3166 country codes as bare
  strings (``Material.originCountry: "DE"``); v0.7 wraps them as
  ``{"countryCode": "DE", "countryName": "Germany"}`` objects with
  ``countryCode`` required and ``countryName`` recommended.
- :class:`Address` is new and reuses schema.org PostalAddress shape.
- :class:`Party` adds ``description``, ``registeredId``, and a nested
  ``idScheme`` (replacing the v0.6 top-level ``IdentifierScheme`` class
  inlined into Party).
- :class:`PartyRole` is new and wraps a Party with a ``role`` enum.

Cross-field invariants (per the plan):

- :class:`Country` ``countryCode`` matches ISO-3166-1 alpha-2 (two ASCII
  uppercase letters). Validators import the existing alpha-2 enforcer from
  ``dppvalidator.vocabularies.code_lists``.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, ClassVar

from pydantic import Field, field_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.v0_7.primitives import FlexibleUri

_ISO_3166_ALPHA2_RE = re.compile(r"^[A-Z]{2}$")


class IdentifierScheme(UNTPBaseModel):
    """Reference to an identifier scheme that defines a code or URI space.

    v0.7.0 inlines this on :class:`Party.idScheme` and
    :attr:`dppvalidator.models.v0_7.product.Product.idScheme`. v0.6 had it
    as a top-level reusable class; the shape is the same (``id`` + ``name``).
    """

    _jsonld_type: ClassVar[list[str]] = ["IdentifierScheme"]

    id: FlexibleUri = Field(..., description="URI of the identifier scheme.")
    name: str = Field(..., description="Human-readable name of the identifier scheme.")


class Country(UNTPBaseModel):
    """ISO-3166 country code + name.

    Wire shape: ``{"countryCode": "DE", "countryName": "Germany"}``.
    Only ``countryCode`` is strictly required; ``countryName`` is
    recommended for human display but ``Country`` payloads from automated
    sources may legitimately omit it.
    """

    _jsonld_type: ClassVar[list[str]] = ["Country"]

    country_code: Annotated[
        str,
        Field(
            ...,
            alias="countryCode",
            description="ISO-3166-1 alpha-2 country code (two uppercase ASCII letters).",
        ),
    ]
    country_name: Annotated[
        str | None,
        Field(
            default=None,
            alias="countryName",
            description="Country name as published by ISO-3166-1.",
        ),
    ]

    @field_validator("country_code")
    @classmethod
    def _validate_alpha2(cls, value: str) -> str:
        if not _ISO_3166_ALPHA2_RE.match(value):
            raise ValueError(
                f"Country.countryCode must be a two-letter ISO-3166-1 alpha-2 code "
                f"(got {value!r}).",
            )
        return value


class Address(UNTPBaseModel):
    """Postal address — schema.org-compatible.

    v0.7.0 introduces this for facility / party addresses; v0.6.x had no
    direct equivalent (addresses lived as free-form strings).
    """

    _jsonld_type: ClassVar[list[str]] = ["Address"]

    street_address: Annotated[
        str | None,
        Field(default=None, alias="streetAddress"),
    ]
    postal_code: Annotated[str | None, Field(default=None, alias="postalCode")]
    address_locality: Annotated[
        str | None,
        Field(default=None, alias="addressLocality", description="City / town / village."),
    ]
    address_region: Annotated[
        str | None,
        Field(default=None, alias="addressRegion", description="State / province / region."),
    ]
    address_country: Annotated[
        Country | None,
        Field(default=None, alias="addressCountry"),
    ]


class Party(UNTPBaseModel):
    """An entity (legal or otherwise) referenced by a credential.

    v0.7.0 adds ``description``, ``registeredId``, and a nested
    :class:`IdentifierScheme` on ``idScheme`` — the v0.6 ``Party`` had
    only ``id`` and ``name`` plus optionally a top-level ``IdentifierScheme``
    reference.
    """

    _jsonld_type: ClassVar[list[str]] = ["Party"]

    id: FlexibleUri = Field(..., description="Globally unique identifier of the party (URI / DID).")
    name: str = Field(..., description="Legal registered name of the party.")
    description: Annotated[str | None, Field(default=None)]
    registered_id: Annotated[
        str | None,
        Field(
            default=None,
            alias="registeredId",
            description="The registration number within the identifier scheme (alphanumeric).",
        ),
    ]
    id_scheme: Annotated[
        IdentifierScheme | None,
        Field(
            default=None,
            alias="idScheme",
            description="The scheme that the ``id`` and ``registeredId`` are drawn from.",
        ),
    ]


class Facility(UNTPBaseModel):
    """A facility (production site, warehouse, smelter, …).

    Used as ``Product.producedAtFacility`` and as the credential subject of
    a :class:`DigitalFacilityRecord` (out of scope — Phase 3 only models
    DPP). Shape is permissive in v0.7 because the upstream schema treats
    facility metadata as extension-friendly.
    """

    _jsonld_type: ClassVar[list[str]] = ["Facility"]

    id: FlexibleUri = Field(..., description="Globally unique identifier of the facility.")
    name: Annotated[str | None, Field(default=None)]
    id_scheme: Annotated[
        IdentifierScheme | None,
        Field(default=None, alias="idScheme"),
    ]
    address: Annotated[Address | None, Field(default=None)]


class PartyRoleEnum(str, Enum):
    """Closed enumeration of party-relationship roles in UNTP v0.7.0.

    Mirrors the schema's enum at ``$defs.PartyRole.properties.role.enum``.
    """

    OWNER = "owner"
    PRODUCER = "producer"
    MANUFACTURER = "manufacturer"
    PROCESSOR = "processor"
    REMANUFACTURER = "remanufacturer"
    RECYCLER = "recycler"
    OPERATOR = "operator"
    SERVICE_PROVIDER = "serviceProvider"
    INSPECTOR = "inspector"
    CERTIFIER = "certifier"
    LOGISTICS_PROVIDER = "logisticsProvider"
    CARRIER = "carrier"
    CONSIGNOR = "consignor"
    CONSIGNEE = "consignee"
    IMPORTER = "importer"
    EXPORTER = "exporter"
    DISTRIBUTOR = "distributor"
    RETAILER = "retailer"
    BRAND_OWNER = "brandOwner"
    REGULATOR = "regulator"


class PartyRole(UNTPBaseModel):
    """A :class:`Party` plus the role it plays in a relationship.

    v0.7.0 introduces this so ``Product.relatedParty`` can be a list of
    typed (role, party) pairs — replacing the v0.6 single
    ``producedByParty: Party`` field with something more expressive.
    """

    _jsonld_type: ClassVar[list[str]] = ["PartyRole"]

    role: PartyRoleEnum = Field(
        ..., description="The role played by the party in this relationship."
    )
    party: Party = Field(..., description="The party that has the specified role.")
