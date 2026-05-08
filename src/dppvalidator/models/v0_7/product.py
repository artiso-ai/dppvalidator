"""Product model for UNTP v0.7.0.

In v0.7.0 the :class:`Product` *is* the credentialSubject of a
:class:`DigitalProductPassport` — there is no longer a ``ProductPassport``
envelope. Conformity claims and material provenance live directly here:

- ``performanceClaim`` (was 0.6 ``conformityClaim`` + 3 scorecards)
- ``materialProvenance`` (singular noun; was 0.6 ``materialsProvenance``)
- ``relatedParty`` (typed list of role/party pairs; was 0.6 ``producedByParty``)
- ``relatedDocument`` (was scattered across 0.6 ``furtherInformation``,
  ``dueDiligenceDeclaration``, etc.)

Cross-field invariants per the plan:

- ``idGranularity`` enum drives whether ``itemNumber`` (item-level passport)
  or ``batchNumber`` (batch-level passport) is required. Replaces the
  v0.6.x ``ProductPassport.granularityLevel`` rule.
- The mass-fraction sum across ``materialProvenance`` should be ≤ 1.0.
  Enforced as an error here because the array context lives on the
  product. Strict equality (sum == 1.0) is too strict — partial
  declarations are valid; only sums *over* 1.0 are physically impossible.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated, ClassVar

from pydantic import Field, model_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.v0_7.claims import Claim
from dppvalidator.models.v0_7.identifiers import (
    Country,
    Facility,
    IdentifierScheme,
    PartyRole,
)
from dppvalidator.models.v0_7.materials import Material
from dppvalidator.models.v0_7.primitives import (
    Characteristics,
    Classification,
    Dimension,
    FlexibleUri,
    Image,
    Link,
)


class IdGranularity(str, Enum):
    """How specifically does the credential identify the product?

    Mirrors the v0.6.x ``GranularityLevel`` enum. The string values are
    case-sensitive and must match the upstream schema's enum exactly.
    """

    ITEM = "item"
    BATCH = "batch"
    MODEL = "model"


class Package(UNTPBaseModel):
    """Product packaging information.

    v0.7.0 introduces this as a structured field on ``Product.packaging``;
    v0.6.x had no equivalent.
    """

    _jsonld_type: ClassVar[list[str]] = ["Package"]

    package_type: Annotated[
        Classification | None,
        Field(default=None, alias="packageType"),
    ]
    weight: Annotated[
        Measure | None,
        Field(default=None, description="Weight of the packaging (separate from product weight)."),
    ]


class Product(UNTPBaseModel):
    """The credential subject of a v0.7.0 DPP.

    All required fields per the upstream schema's ``Product`` $def:
    ``id``, ``name``, ``idScheme``, ``idGranularity``, ``productCategory``,
    ``producedAtFacility``, ``countryOfProduction``. Everything else is
    optional but commonly populated.
    """

    _jsonld_type: ClassVar[list[str]] = ["Product"]

    id: FlexibleUri = Field(
        ...,
        description="Globally unique identifier (URI / DID).",
    )
    name: str = Field(..., description="The product name as known to the market.")
    description: Annotated[str | None, Field(default=None)]

    id_scheme: Annotated[
        IdentifierScheme,
        Field(
            ...,
            alias="idScheme",
            description="The identifier scheme used by ``id`` (e.g. GS1 GTIN).",
        ),
    ]
    model_number: Annotated[str | None, Field(default=None, alias="modelNumber")]
    batch_number: Annotated[str | None, Field(default=None, alias="batchNumber")]
    item_number: Annotated[
        str | None,
        Field(
            default=None,
            alias="itemNumber",
            description="Serialised item number (was ``serialNumber`` in v0.6.x).",
        ),
    ]
    id_granularity: Annotated[
        IdGranularity,
        Field(
            ...,
            alias="idGranularity",
            description="Whether the credential covers a single item, a batch, or a model class.",
        ),
    ]

    product_image: Annotated[Link | None, Field(default=None, alias="productImage")]
    characteristics: Characteristics | None = Field(default=None)
    product_category: Annotated[
        list[Classification],
        Field(
            ...,
            alias="productCategory",
            description=(
                "Product classification codes (e.g. UN CPC). Now an array in v0.7.0; "
                "scalar Classification in v0.6.x."
            ),
            min_length=1,
        ),
    ]
    related_document: Annotated[
        list[Link],
        Field(
            default_factory=list,
            alias="relatedDocument",
            description=(
                "Links to related documents (specifications, brochures, ...). Notably absorbs the "
                "v0.6.x ``furtherInformation`` and ``dueDiligenceDeclaration`` fields."
            ),
        ),
    ]
    related_party: Annotated[
        list[PartyRole],
        Field(
            default_factory=list,
            alias="relatedParty",
            description=(
                "Parties with a defined role on this product (manufacturer, recycler, …). "
                "Replaces the v0.6.x scalar ``producedByParty: Party``."
            ),
        ),
    ]
    produced_at_facility: Annotated[
        Facility,
        Field(
            ...,
            alias="producedAtFacility",
            description="The facility where this product/batch was produced.",
        ),
    ]
    production_date: Annotated[
        date | None,
        Field(default=None, alias="productionDate"),
    ]
    expiry_date: Annotated[
        date | None,
        Field(default=None, alias="expiryDate"),
    ]
    country_of_production: Annotated[
        Country,
        Field(
            ...,
            alias="countryOfProduction",
            description="ISO-3166 country of production (was a bare string in v0.6.x).",
        ),
    ]
    dimensions: Dimension | None = Field(default=None)
    material_provenance: Annotated[
        list[Material],
        Field(
            default_factory=list,
            alias="materialProvenance",
            description=(
                "Material origin / mass fraction information. Singular noun in v0.7.0 "
                "(was ``materialsProvenance`` in v0.6.x)."
            ),
        ),
    ]
    packaging: Package | None = Field(default=None)
    product_label: Annotated[
        list[Image],
        Field(default_factory=list, alias="productLabel"),
    ]
    performance_claim: Annotated[
        list[Claim],
        Field(
            default_factory=list,
            alias="performanceClaim",
            description=(
                "Performance / conformity claims about this product. Replaces the v0.6.x "
                "``conformityClaim`` array AND the three Emissions/Circularity/Traceability scorecards."
            ),
        ),
    ]

    @model_validator(mode="after")
    def _granularity_implies_serial_or_batch(self) -> Product:
        # ``UNTPBaseModel`` ships ``use_enum_values=True``, so by the time
        # this runs ``self.id_granularity`` is the string value, not the
        # IdGranularity instance — compare on value (``==``) rather than
        # identity (``is``).
        if self.id_granularity == IdGranularity.ITEM.value and not self.item_number:
            raise ValueError(
                "Product.itemNumber is required when idGranularity == 'item'.",
            )
        if self.id_granularity == IdGranularity.BATCH.value and not self.batch_number:
            raise ValueError(
                "Product.batchNumber is required when idGranularity == 'batch'.",
            )
        return self

    @model_validator(mode="after")
    def _mass_fractions_sum_within_unity(self) -> Product:
        if not self.material_provenance:
            return self
        # Partial declarations (sum < 1.0) are explicitly allowed by UNTP — that
        # nuance lives in the semantic-rule layer (Phase 3b emits a SEM-class
        # warning). Sums *above* 1.0 are physically impossible regardless and
        # therefore caught here.
        total = sum(m.mass_fraction for m in self.material_provenance)
        if total > 1.0001:  # tiny epsilon for float arithmetic
            raise ValueError(
                f"Sum of materialProvenance.massFraction across {len(self.material_provenance)} "
                f"material(s) is {total:.4f} > 1.0 — physically impossible.",
            )
        return self


# Resolve the forward reference inside Package.weight. We can't import
# Measure at the top of the file because product.py is imported by other
# modules and the cycle would resolve in the wrong direction.
from dppvalidator.models.v0_7.primitives import Measure  # noqa: E402

Package.model_rebuild()
