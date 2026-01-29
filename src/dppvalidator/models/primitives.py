"""Primitive types for UNTP DPP models."""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import Field, HttpUrl

from dppvalidator.models.base import UNTPStrictModel
from dppvalidator.models.enums import EncryptionMethod, HashMethod


class Measure(UNTPStrictModel):
    """Numeric value with unit of measure (UNECE Rec20)."""

    _jsonld_type: ClassVar[list[str]] = ["Measure"]

    value: float = Field(..., description="The numeric value of the measure")
    unit: str = Field(
        ...,
        description="Unit of measure from UNECE Rec20 (e.g., KGM, LTR, EA)",
    )


class Link(UNTPStrictModel):
    """URL link with metadata."""

    _jsonld_type: ClassVar[list[str]] = ["Link"]

    link_url: Annotated[
        HttpUrl | None,
        Field(default=None, alias="linkURL", description="The URL of the target resource"),
    ]
    link_name: Annotated[
        str | None,
        Field(default=None, alias="linkName", description="Display name for the target resource"),
    ]
    link_type: Annotated[
        str | None,
        Field(default=None, alias="linkType", description="Type of the target resource"),
    ]


class SecureLink(UNTPStrictModel):
    """Link with hash and optional encryption for tamper evidence."""

    _jsonld_type: ClassVar[list[str]] = ["SecureLink", "Link"]

    link_url: Annotated[
        HttpUrl | None,
        Field(default=None, alias="linkURL", description="The URL of the target resource"),
    ]
    link_name: Annotated[
        str | None,
        Field(default=None, alias="linkName", description="Display name for the target resource"),
    ]
    link_type: Annotated[
        str | None,
        Field(default=None, alias="linkType", description="Type of the target resource"),
    ]
    hash_digest: Annotated[
        str | None,
        Field(default=None, alias="hashDigest", description="Hash of the file"),
    ]
    hash_method: Annotated[
        HashMethod | None,
        Field(
            default=None, alias="hashMethod", description="Hashing algorithm (SHA-256 recommended)"
        ),
    ]
    encryption_method: Annotated[
        EncryptionMethod | None,
        Field(
            default=None,
            alias="encryptionMethod",
            description="Encryption algorithm (AES recommended)",
        ),
    ]


class Classification(UNTPStrictModel):
    """Classification scheme and code representing a category value."""

    _jsonld_type: ClassVar[list[str]] = ["Classification"]

    id: Annotated[
        HttpUrl,
        Field(..., description="Globally unique URI representing the classifier value"),
    ]
    code: Annotated[
        str | None,
        Field(default=None, description="Classification code within the scheme"),
    ]
    name: str = Field(..., description="Name of the classification")
    scheme_id: Annotated[
        HttpUrl | None,
        Field(default=None, alias="schemeID", description="Classification scheme ID"),
    ]
    scheme_name: Annotated[
        str | None,
        Field(default=None, alias="schemeName", description="Name of the classification scheme"),
    ]
