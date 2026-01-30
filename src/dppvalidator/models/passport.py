"""Digital Product Passport root model per UNTP/UNCEFACT v0.6.1."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import Field, model_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.credential import (
    CredentialIssuer,
    CredentialStatus,
    ProductPassport,
)
from dppvalidator.models.primitives import FlexibleUri


class DigitalProductPassport(UNTPBaseModel):
    """Digital Product Passport as a Verifiable Credential.

    Root model for UNTP DPP v0.6.1, combining DigitalProductPassport
    and VerifiableCredential types per W3C VC v2 specification.
    """

    _jsonld_type: ClassVar[list[str]] = ["DigitalProductPassport", "VerifiableCredential"]

    context: Annotated[
        list[str],
        Field(
            alias="@context",
            default=[
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            description="JSON-LD context URIs",
        ),
    ]
    id: Annotated[
        FlexibleUri,
        Field(..., description="Unique identifier (URI) for this passport"),
    ]
    issuer: CredentialIssuer = Field(..., description="Organisation issuing this credential")
    valid_from: Annotated[
        datetime | None,
        Field(default=None, alias="validFrom", description="Credential validity start"),
    ]
    valid_until: Annotated[
        datetime | None,
        Field(default=None, alias="validUntil", description="Credential expiry date"),
    ]
    credential_subject: Annotated[
        ProductPassport | None,
        Field(
            default=None,
            alias="credentialSubject",
            description="The product passport content",
        ),
    ]
    credential_status: Annotated[
        CredentialStatus | list[CredentialStatus] | None,
        Field(
            default=None,
            alias="credentialStatus",
            description="Credential revocation/suspension status per W3C VC v2",
        ),
    ]

    @model_validator(mode="after")
    def validate_dates(self) -> DigitalProductPassport:
        """Ensure validFrom is before validUntil if both are present."""
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("validFrom must be before validUntil")
        return self

    @model_validator(mode="after")
    def validate_material_mass_fractions(self) -> DigitalProductPassport:
        """Validate material mass fractions don't exceed 1.0.

        Per UNTP spec, mass fractions can be partial declarations (sum < 1.0).
        Only sum > 1.0 is physically impossible and should error.
        Semantic validation checks for exact sum when appropriate.
        """
        if not self.credential_subject:
            return self
        materials = self.credential_subject.materials_provenance
        if not materials:
            return self
        fractions = [m.mass_fraction for m in materials if m.mass_fraction is not None]
        if fractions:
            total = sum(fractions)
            if total > 1.01:  # Allow small tolerance for floating point
                raise ValueError(f"Material mass fractions cannot exceed 1.0, got {total:.3f}")
        return self
