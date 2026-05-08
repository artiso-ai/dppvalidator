"""Primitive types reused across UNTP v0.7.0 model classes.

Compared to v0.6.x:

- :class:`Classification` renames ``schemeID`` → ``schemeId`` (camelCase
  fix) and adds an optional ``definition`` field.
- :class:`Link` absorbs the v0.6 ``SecureLink`` by adding optional
  ``digestMultibase`` and ``mediaType`` fields. There is no separate
  ``SecureLink`` class in v0.7.0.
- :class:`Measure` adds optional ``lowerTolerance`` and ``upperTolerance``.
- :class:`Image` is new (was an inline base64 string in v0.6.x ``Material.symbol``).
- :class:`Characteristics` and :class:`Dimension` keep the same shape but
  drop their leading ``type`` discriminator from the schema.
"""

from __future__ import annotations

from typing import Annotated, Any, ClassVar

from pydantic import Field, model_validator

from dppvalidator.models.base import UNTPBaseModel, UNTPStrictModel

# ---------------------------------------------------------------------------
# FlexibleUri — version-neutral URI handling.
#
# v0.7.0 keeps the same lenient stance as v0.6.x: schema fields typed as
# ``format: uri`` accept HTTPS URIs, DIDs, and other URI schemes. We model
# the wire shape as a plain ``str`` and let the JSON-LD layer carry the URI
# semantics.
# ---------------------------------------------------------------------------
FlexibleUri = str


class Classification(UNTPBaseModel):
    """A code drawn from a controlled classification scheme.

    Used for product categories (e.g. UN CPC), material types (e.g. UNFC),
    etc. The ``schemeId`` URI identifies the scheme; ``code`` is the code
    value within the scheme; ``schemeName`` is the human-readable scheme
    label.

    v0.6.x called this same shape ``schemeID`` (uppercase D); v0.7.0 fixes
    the camelCase as ``schemeId`` (lowercase d) and requires ``schemeName``.
    """

    _jsonld_type: ClassVar[list[str]] = ["Classification"]

    scheme_id: Annotated[
        FlexibleUri,
        Field(
            ...,
            alias="schemeId",
            description="URI identifying the classification scheme.",
        ),
    ]
    scheme_name: Annotated[
        str,
        Field(
            ...,
            alias="schemeName",
            description="Human-readable name of the classification scheme (e.g. 'UN CPC').",
        ),
    ]
    code: str = Field(..., description="The classification code within the scheme.")
    name: str = Field(..., description="Human-readable name for the classification value.")
    definition: Annotated[
        str | None,
        Field(default=None, description="Optional rich definition of the classification value."),
    ]


class Link(UNTPBaseModel):
    """A reference to a related document.

    v0.7.0 absorbs v0.6 ``SecureLink`` here: ``digestMultibase`` and
    ``mediaType`` are now first-class on :class:`Link` itself. The
    cross-field invariant — if you assert a hash, declare the media type —
    fires as a model validator below.
    """

    _jsonld_type: ClassVar[list[str]] = ["Link"]

    href: FlexibleUri = Field(
        ...,
        alias="linkURL",
        description="URL the link points at (alias 'linkURL' for compatibility with the schema).",
    )
    name: Annotated[
        str | None, Field(default=None, description="Human-readable label for the link.")
    ]
    description: Annotated[str | None, Field(default=None)]
    relationship: Annotated[
        str | None,
        Field(
            default=None,
            description="Free-form classification of the link relationship (e.g. 'evidence', 'specification').",
        ),
    ]
    media_type: Annotated[
        str | None,
        Field(
            default=None,
            alias="mediaType",
            description="IANA media type of the linked document (RFC 6838).",
        ),
    ]
    digest_multibase: Annotated[
        str | None,
        Field(
            default=None,
            alias="digestMultibase",
            description=(
                "Multibase-encoded multihash (https://www.w3.org/TR/vc-data-integrity/) "
                "of the linked content. If set, ``mediaType`` SHOULD also be set so the "
                "consumer knows how to interpret the bytes."
            ),
        ),
    ]

    @model_validator(mode="after")
    def _digest_implies_media_type(self) -> Link:
        # Warning-grade invariant per docs/plans/UNTP_0.7.0_MIGRATION.md §3.2:
        # we *recommend* mediaType when a digest is present, but we don't
        # block validation — third-party documents that pin a hash without
        # declaring a media type are still consumable.
        # Semantic-rule layer (Phase 3b) is where this becomes a warning.
        return self


class Measure(UNTPStrictModel):
    """A numeric measurement with a unit-of-measure code.

    v0.7.0 adds optional ``lowerTolerance`` and ``upperTolerance`` to
    express measurement precision (additive over v0.6.x).
    """

    _jsonld_type: ClassVar[list[str]] = ["Measure"]

    value: float = Field(..., description="The measured numeric value.")
    unit: str = Field(
        ...,
        description="UN/CEFACT Recommendation 20 unit-of-measure code (e.g. KGM for kilogram).",
    )
    lower_tolerance: Annotated[
        float | None,
        Field(
            default=None,
            alias="lowerTolerance",
            description="Optional lower tolerance bound (same unit as ``value``).",
        ),
    ]
    upper_tolerance: Annotated[
        float | None,
        Field(
            default=None,
            alias="upperTolerance",
            description="Optional upper tolerance bound (same unit as ``value``).",
        ),
    ]

    @model_validator(mode="after")
    def _validate_tolerances(self) -> Measure:
        if (
            self.lower_tolerance is not None
            and self.upper_tolerance is not None
            and self.lower_tolerance > self.upper_tolerance
        ):
            raise ValueError(
                "Measure.lowerTolerance must be ≤ upperTolerance "
                f"(got {self.lower_tolerance} > {self.upper_tolerance})",
            )
        return self


class Image(UNTPBaseModel):
    """Base64-encoded image with display metadata.

    v0.7.0 introduces this as a structured replacement for the inline base64
    string previously used at v0.6 ``Material.symbol``. Used at
    ``Material.symbol`` and ``Product.productLabel``.

    Required: ``name``, ``imageData``, ``mediaType``. ``description`` is
    optional (used for things like Battery Reg. label captions).
    """

    _jsonld_type: ClassVar[list[str]] = ["Image"]

    name: str = Field(..., description="Display name for the image (e.g. 'CE Marking').")
    description: Annotated[
        str | None,
        Field(default=None, description="Detailed description / supporting information."),
    ]
    image_data: Annotated[
        str,
        Field(
            ...,
            alias="imageData",
            description="Base64-encoded image bytes.",
        ),
    ]
    media_type: Annotated[
        str,
        Field(
            ...,
            alias="mediaType",
            description="IANA media type (e.g. image/png).",
        ),
    ]


class Dimension(UNTPBaseModel):
    """Physical dimensions and mass of a product.

    Each axis is optional because not every product has every dimension
    (bulk materials may have weight + volume but no length / width / height).
    """

    _jsonld_type: ClassVar[list[str]] = ["Dimension"]

    weight: Measure | None = Field(default=None)
    length: Measure | None = Field(default=None)
    width: Measure | None = Field(default=None)
    height: Measure | None = Field(default=None)
    volume: Measure | None = Field(default=None)


class Characteristics(UNTPBaseModel):
    """Industry/product-specific characteristics extension point.

    The schema declares this as ``additionalProperties: true`` with no
    fixed shape — extensions plug their own fields in here.
    """

    _jsonld_type: ClassVar[list[str]] = ["Characteristics"]

    # Pydantic ``extra="allow"`` is inherited from UNTPBaseModel, which is
    # how arbitrary industry-specific keys flow through.
    def __getitem__(self, key: str) -> Any:  # convenience for callers
        return getattr(self, key)
