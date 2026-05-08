"""W3C VC envelope and DPP credential class for UNTP v0.7.0.

This module is what callers reach for when they want to validate a v0.7.0
Digital Product Passport. The :class:`DigitalProductPassport` carries the
W3C VC v2 envelope (``@context``, ``id``, ``issuer``, ``validFrom``,
``validUntil``, …) and a :class:`Product` as its ``credentialSubject``
— there is **no** ``ProductPassport`` envelope class in v0.7.0.

New top-level fields compared to v0.6.x (now first-class):

- :class:`IssuingSoftware` — software-vendor metadata for the credential.
- :class:`RenderTemplate2024` — render-method spec (stored, not executed).
- :class:`BitstringStatusListEntry` — first-class status-list shape.
- ``name`` is now a required envelope field.

Cross-field invariants:

- ``validFrom`` MUST precede ``validUntil`` when both are set (port from v0.6).
- ``name`` MUST be non-empty (now required by the schema).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import Field, model_validator

from dppvalidator.models.base import UNTPBaseModel, UNTPStrictModel
from dppvalidator.models.v0_7.identifiers import Party
from dppvalidator.models.v0_7.primitives import FlexibleUri
from dppvalidator.models.v0_7.product import Product


class CredentialIssuer(UNTPStrictModel):
    """The party that issued a v0.7.0 DPP.

    The shape is the same as v0.6.x ``CredentialIssuer`` (id, name,
    issuerAlsoKnownAs[]). The ``id`` MUST be a W3C DID per the spec; the
    model accepts any URI to stay forgiving on intake.
    """

    _jsonld_type: ClassVar[list[str]] = ["CredentialIssuer"]

    id: FlexibleUri = Field(
        ...,
        description="W3C DID (did:web, did:webvh, …) or HTTPS identifier of the issuer.",
    )
    name: str = Field(..., description="Human-readable issuer name.")
    issuer_also_known_as: Annotated[
        list[Party] | None,
        Field(
            default=None,
            alias="issuerAlsoKnownAs",
            description="Other registered identities (parties) for this issuer.",
        ),
    ]


class SoftwareVendor(UNTPBaseModel):
    """Vendor of the software that issued the credential.

    Used by :class:`IssuingSoftware`. The ``id`` is typically a
    ``did:web:`` for the vendor's domain.
    """

    _jsonld_type: ClassVar[list[str]] = ["SoftwareVendor"]

    id: FlexibleUri = Field(..., description="DID or URI identifying the vendor.")
    name: str = Field(..., description="Vendor company / organisation name.")


class IssuingSoftware(UNTPBaseModel):
    """Metadata about the software that emitted this credential.

    New top-level field in v0.7.0 — captures the software supply chain so
    consumers can trace which tool generated a passport. Optional but
    recommended.
    """

    _jsonld_type: ClassVar[list[str]] = ["IssuingSoftware"]

    id: FlexibleUri = Field(..., description="URI identifying the issuing software product.")
    name: str = Field(..., description="Product name (e.g. 'Sample Passport Builder').")
    version: str = Field(..., description="Software version (e.g. '2026.04.1').")
    vendor: SoftwareVendor = Field(..., description="The vendor that publishes this software.")


class RenderTemplate2024(UNTPBaseModel):
    """A render-method specification (W3C VC 2.0 Render Method 2024).

    v0.7.0 stores rendering hints alongside the credential. We capture the
    fields without executing them — actual rendering is a downstream
    concern (out of scope per the migration plan §9).
    """

    _jsonld_type: ClassVar[list[str]] = ["RenderTemplate2024"]

    id: Annotated[FlexibleUri | None, Field(default=None)]
    type: Annotated[
        str | list[str] | None,
        Field(
            default=None, description="Render-method type identifier (overrides the base default)."
        ),
    ]
    name: Annotated[str | None, Field(default=None)]
    template: Annotated[
        str | None,
        Field(
            default=None,
            description="Inline template body (often a URL to a template file).",
        ),
    ]
    digest_multibase: Annotated[
        str | None,
        Field(default=None, alias="digestMultibase"),
    ]
    media_type: Annotated[
        str | None,
        Field(default=None, alias="mediaType"),
    ]


class BitstringStatusListEntry(UNTPBaseModel):
    """W3C VC Bitstring Status List entry.

    Used by :attr:`DigitalProductPassport.credentialStatus`. v0.7.0 lifts
    this to a first-class type (was a free-form ``CredentialStatus`` in
    v0.6.x).
    """

    _jsonld_type: ClassVar[list[str]] = ["BitstringStatusListEntry"]

    id: FlexibleUri = Field(..., description="URI of this status entry.")
    type: str = Field(default="BitstringStatusListEntry")
    status_purpose: Annotated[
        str | None,
        Field(default=None, alias="statusPurpose", description="e.g. 'revocation', 'suspension'."),
    ]
    status_list_index: Annotated[
        str | None,
        Field(default=None, alias="statusListIndex"),
    ]
    status_list_credential: Annotated[
        FlexibleUri | None,
        Field(default=None, alias="statusListCredential"),
    ]


# Type alias kept compatible with v0.6 for the engine's ``credentialStatus``
# field. v0.7.0 narrows the shape to BitstringStatusListEntry but a generic
# alias helps downstream code that branches on version.
CredentialStatus = BitstringStatusListEntry


class DigitalProductPassport(UNTPBaseModel):
    """Root model for a UNTP v0.7.0 Digital Product Passport.

    Required envelope fields (per the upstream JSON Schema):
    ``@context``, ``id``, ``issuer``, ``validFrom``, ``name``, ``credentialSubject``.

    Cross-field invariants:

    - ``validFrom`` < ``validUntil`` when both present.
    - ``name`` is non-empty (delegated to Pydantic ``min_length=1``).

    The ``credentialSubject`` is a :class:`Product` directly — there is no
    ``ProductPassport`` envelope class in v0.7.0.
    """

    _jsonld_type: ClassVar[list[str]] = ["DigitalProductPassport", "VerifiableCredential"]

    context: Annotated[
        list[str],
        Field(
            ...,
            alias="@context",
            description="JSON-LD context URIs. First entry is W3C VC v2; second is the UNTP 0.7.0 context.",
            min_length=2,
        ),
    ]
    id: FlexibleUri = Field(..., description="Globally unique DPP credential identifier (URI).")
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable credential title (now required by the v0.7.0 schema).",
    )
    issuer: CredentialIssuer = Field(..., description="The party issuing this credential.")
    valid_from: Annotated[
        datetime,
        Field(
            ...,
            alias="validFrom",
            description="Credential validity start (now required by the v0.7.0 schema).",
        ),
    ]
    valid_until: Annotated[
        datetime | None,
        Field(default=None, alias="validUntil", description="Credential expiry (optional)."),
    ]
    issuing_software: Annotated[
        IssuingSoftware | None,
        Field(
            default=None,
            alias="issuingSoftware",
            description="Metadata about the software that emitted this credential.",
        ),
    ]
    render_method: Annotated[
        list[RenderTemplate2024] | None,
        Field(
            default=None,
            alias="renderMethod",
            description="Render-method specifications for human display.",
        ),
    ]
    credential_status: Annotated[
        BitstringStatusListEntry | list[BitstringStatusListEntry] | None,
        Field(
            default=None,
            alias="credentialStatus",
            description="Revocation / suspension status entries.",
        ),
    ]
    credential_subject: Annotated[
        Product,
        Field(
            ...,
            alias="credentialSubject",
            description="The product that this DPP describes (now a Product directly, no envelope).",
        ),
    ]

    @model_validator(mode="after")
    def _validate_dates(self) -> DigitalProductPassport:
        if (
            self.valid_until is not None
            and self.valid_from is not None
            and self.valid_from >= self.valid_until
        ):
            raise ValueError(
                "DigitalProductPassport.validFrom must be strictly before validUntil "
                f"(got {self.valid_from.isoformat()} >= {self.valid_until.isoformat()}).",
            )
        return self
