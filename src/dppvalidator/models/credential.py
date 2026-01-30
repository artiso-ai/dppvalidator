"""Credential and ProductPassport models for UNTP DPP."""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import Field

from dppvalidator.models.base import UNTPBaseModel, UNTPStrictModel
from dppvalidator.models.claims import Claim
from dppvalidator.models.enums import GranularityLevel
from dppvalidator.models.identifiers import Party
from dppvalidator.models.materials import Material
from dppvalidator.models.performance import (
    CircularityPerformance,
    EmissionsPerformance,
    TraceabilityPerformance,
)
from dppvalidator.models.primitives import FlexibleUri, Link
from dppvalidator.models.product import Product


class CredentialStatus(UNTPBaseModel):
    """Credential status for revocation checking per W3C VC v2.

    Used to check if a credential has been revoked or suspended.
    Supports multiple status mechanisms (BitstringStatusList, StatusList2021, etc.).
    """

    _jsonld_type: ClassVar[list[str]] = ["CredentialStatus"]

    id: Annotated[
        FlexibleUri,
        Field(..., description="URI identifying the status entry"),
    ]
    type: Annotated[
        str,
        Field(
            ...,
            description="Status type (e.g., BitstringStatusListEntry, StatusList2021Entry)",
        ),
    ]
    status_purpose: Annotated[
        str | None,
        Field(
            default=None,
            alias="statusPurpose",
            description="Purpose of status (revocation, suspension)",
        ),
    ]
    status_list_index: Annotated[
        str | None,
        Field(
            default=None,
            alias="statusListIndex",
            description="Index in the status list",
        ),
    ]
    status_list_credential: Annotated[
        FlexibleUri | None,
        Field(
            default=None,
            alias="statusListCredential",
            description="URI of the status list credential",
        ),
    ]


class CredentialIssuer(UNTPStrictModel):
    """Issuer of a verifiable credential."""

    _jsonld_type: ClassVar[list[str]] = ["CredentialIssuer"]

    id: Annotated[
        FlexibleUri,
        Field(..., description="W3C DID of the issuer (did:web, did:webvh, or https URL)"),
    ]
    name: str = Field(..., description="Name of the issuer person or organisation")
    issuer_also_known_as: Annotated[
        list[Party] | None,
        Field(
            default=None,
            alias="issuerAlsoKnownAs",
            description="Other registered identifiers for this issuer",
        ),
    ]


class ProductPassport(UNTPBaseModel):
    """Product passport credential subject."""

    _jsonld_type: ClassVar[list[str]] = ["ProductPassport"]

    id: Annotated[
        FlexibleUri | None,
        Field(default=None, description="Identifier for the credential subject (URI)"),
    ]
    product: Product | None = Field(default=None, description="Product information")
    granularity_level: Annotated[
        GranularityLevel | None,
        Field(
            default=None,
            alias="granularityLevel",
            description="Item, batch, or model level passport",
        ),
    ]
    conformity_claim: Annotated[
        list[Claim] | None,
        Field(
            default=None,
            alias="conformityClaim",
            description="Conformity claims about the product",
        ),
    ]
    emissions_scorecard: Annotated[
        EmissionsPerformance | None,
        Field(
            default=None,
            alias="emissionsScorecard",
            description="Emissions performance scorecard",
        ),
    ]
    traceability_information: Annotated[
        list[TraceabilityPerformance] | None,
        Field(
            default=None,
            alias="traceabilityInformation",
            description="Traceability events by value chain process",
        ),
    ]
    circularity_scorecard: Annotated[
        CircularityPerformance | None,
        Field(
            default=None,
            alias="circularityScorecard",
            description="Circularity performance scorecard",
        ),
    ]
    due_diligence_declaration: Annotated[
        Link | None,
        Field(
            default=None,
            alias="dueDiligenceDeclaration",
            description="Due diligence declaration link",
        ),
    ]
    materials_provenance: Annotated[
        list[Material] | None,
        Field(
            default=None,
            alias="materialsProvenance",
            description="Material origin and mass fraction information",
        ),
    ]
