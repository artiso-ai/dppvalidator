"""Product, Identifier, and Classification types for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.5 of [docs/plans/CIRPASS_2_MIGRATION.md]. Models the
core ``Product`` class from EUDPP P_DPP v1.9.1 plus the
``ClassificationCode`` and identifier-scheme support introduced in the
v1.9.1 spec (the new ``uniqueProductIdentifierScheme`` datatype
property).

EUDPP IRI bindings:

- ``Product`` → ``eudpp:Product``
- ``ClassificationCode`` → ``eudpp:ClassificationCode``
- ``Identifier`` is a CIRPASS message-level wrapper around the v1.9.1
  ``uniqueProductIdentifier`` + ``uniqueProductIdentifierScheme``
  datatype properties (the spec exposes them as separate predicates;
  the message wraps them as a structured object for ergonomics).
"""

from __future__ import annotations

import re
from typing import ClassVar

from pydantic import Field, field_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.cirpass.v1_3.i18n import LocalisedText
from dppvalidator.vocabularies.eudpp_classes import EUDPPClass

# Pragmatic GTIN-13 regex: 13 ASCII digits. Full GTIN family (8/12/13/14)
# accepts 8–14 digits; we accept all five canonical lengths.
_GTIN_RE = re.compile(r"^\d{8}(?:\d{4,6})?$")


class Identifier(UNTPBaseModel):
    """A typed product or DPP identifier.

    Wire shape:
        ``{"value": "01234567890128", "scheme": "https://gs1.org/voc/", "schemeName": "GS1 GTIN"}``

    ``value`` carries the identifier itself; ``scheme`` is the URI of
    the issuing authority's identifier register; ``schemeName`` is a
    short human label (e.g. ``GS1 GTIN``, ``ISO/IEC 15459``).

    The scheme URI is what disambiguates collisions between identifier
    spaces (a 13-digit string can be a GTIN-13, an EAN-13, or
    something else entirely depending on the issuing authority).
    """

    _jsonld_type: ClassVar[list[str]] = ["Identifier"]

    value: str = Field(..., min_length=1, description="The identifier value.")
    scheme: str = Field(
        ...,
        description=(
            "URI of the identifier scheme (the issuing authority's "
            "register, e.g. ``https://gs1.org/voc/``)."
        ),
    )
    scheme_name: str | None = Field(
        default=None,
        alias="schemeName",
        description="Human-readable scheme name (``GS1 GTIN``, ``ISO/IEC 15459``).",
    )

    @field_validator("scheme")
    @classmethod
    def _scheme_is_uri(cls, value: str) -> str:
        if not (value.startswith("http://") or value.startswith("https://")):
            msg = (
                f"Identifier.scheme must be an http(s) URI; got {value!r}. "
                f"The scheme URI is what disambiguates identifier spaces — "
                f"a bare label (e.g. ``GTIN``) is not enough."
            )
            raise ValueError(msg)
        return value


class ClassificationCode(UNTPBaseModel):
    """A taxonomy classification (commodity code, HS code, etc.).

    Wire shape:
        ``{"code": "61091000", "scheme": "https://www.wcoomd.org/.../HS",
           "name": [{"value": "T-shirts...", "language": "en"}]}``

    Maps to ``eudpp:ClassificationCode`` (P_DPP v1.9.1). The CIRPASS
    spec uses this for HS / TARIC / commodity codes; the ``scheme``
    URI tells consumers which taxonomy the code belongs to.
    """

    _jsonld_type: ClassVar[list[str]] = ["ClassificationCode"]

    code: str = Field(..., min_length=1, description="The classification code value.")
    scheme: str = Field(
        ...,
        description="URI of the classification scheme (HS, TARIC, CPV, …).",
    )
    name: list[LocalisedText] | None = Field(
        default=None,
        description="Human-readable description of the code, in one or more languages.",
    )

    @field_validator("scheme")
    @classmethod
    def _scheme_is_uri(cls, value: str) -> str:
        if not (value.startswith("http://") or value.startswith("https://")):
            msg = f"ClassificationCode.scheme must be an http(s) URI; got {value!r}."
            raise ValueError(msg)
        return value


class Product(UNTPBaseModel):
    """A physical product placed on the EU market.

    Maps to ``eudpp:Product`` (P_DPP v1.9.1). Carries the product's
    primary identifier, optional commodity classification, and
    multilingual product names.

    Wire shape (minimal):
        ``{"productIdentifier": {...}, "productName": [{"value": "...", "language": "en"}]}``

    Cardinality:

    - ``productIdentifier``: required (1).
    - ``productName``: required (≥1) — at least one language must be
      provided. Multiple are encouraged for ESPR multilingual reach.
    - ``description``: optional (0..1 list of LocalisedText).
    - ``commodityCode``: optional (0..n list of ClassificationCode).
    - ``isComponentOf`` / ``isSparePartOf``: optional self-references
      modelling the v1.9.1 transitive product hierarchy.
    """

    _jsonld_type: ClassVar[list[str]] = ["Product", EUDPPClass.PRODUCT.value]

    product_identifier: Identifier = Field(
        ...,
        alias="productIdentifier",
        description="Primary product identifier (typically a GTIN or SPC URI).",
    )
    product_name: list[LocalisedText] = Field(
        ...,
        alias="productName",
        min_length=1,
        description="Product name(s), one entry per supported language.",
    )
    description: list[LocalisedText] | None = Field(
        default=None,
        description="Product description(s), one entry per language.",
    )
    commodity_code: list[ClassificationCode] | None = Field(
        default=None,
        alias="commodityCode",
        description="Commodity / taxonomy classifications for this product.",
    )
    is_component_of: list[str] | None = Field(
        default=None,
        alias="isComponentOf",
        description="URIs of products this product is a component of (transitive).",
    )
    is_spare_part_of: list[str] | None = Field(
        default=None,
        alias="isSparePartOf",
        description="URIs of products this product is a spare part of.",
    )


def looks_like_gtin(value: str) -> bool:
    """Heuristic: True if ``value`` matches a GTIN-shape (8–14 digits).

    Used by tests + mapping shims; not enforced at the
    :class:`Identifier` level because non-GTIN scheme values
    legitimately use other formats.
    """
    return bool(_GTIN_RE.match(value))
