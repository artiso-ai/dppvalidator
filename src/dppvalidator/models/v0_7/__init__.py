"""Pydantic models for UNTP DPP **v0.7.0**.

Built in Phase 3 of docs/plans/UNTP_0.7.0_MIGRATION.md from the bundled
schema at ``src/dppvalidator/schemas/data/untp-dpp-schema-0.7.0.json``
(SHA-pinned to upstream commit ``707cd526...`` of
``opensource.unicc.org/un/unece/uncefact/spec-untp``).

The v0.7.0 envelope is structurally different from v0.6.x: the
``ProductPassport`` envelope class is gone, ``credentialSubject`` is a
:class:`Product` directly, and the three "scorecard" classes
(``EmissionsPerformance``, ``CircularityPerformance``,
``TraceabilityPerformance``) are folded into a single
:class:`Claim.claimedPerformance: list[Performance]` shape on the Product.
See §2 of the plan for the full delta tables.

This subpackage is opt-in for the 0.4.x line: callers reach it explicitly
via ``from dppvalidator.models.v0_7 import DigitalProductPassport``. The
top-level ``dppvalidator.models`` namespace continues to re-export v0.6.x
shapes through 0.4.x; Phase 9 (validator 0.5.0) flips that default.
"""

from dppvalidator.models.v0_7.claims import (
    Claim,
    ConformityTopic,
    Performance,
    Period,
    Score,
)
from dppvalidator.models.v0_7.envelope import (
    BitstringStatusListEntry,
    CredentialIssuer,
    CredentialStatus,
    DigitalProductPassport,
    IssuingSoftware,
    RenderTemplate2024,
    SoftwareVendor,
)
from dppvalidator.models.v0_7.identifiers import (
    Address,
    Country,
    Facility,
    IdentifierScheme,
    Party,
    PartyRole,
    PartyRoleEnum,
)
from dppvalidator.models.v0_7.materials import Material
from dppvalidator.models.v0_7.primitives import (
    Characteristics,
    Classification,
    Dimension,
    FlexibleUri,
    Image,
    Link,
    Measure,
)
from dppvalidator.models.v0_7.product import Package, Product

__all__ = [
    # Envelope
    "DigitalProductPassport",
    "CredentialIssuer",
    "CredentialStatus",
    "BitstringStatusListEntry",
    "IssuingSoftware",
    "SoftwareVendor",
    "RenderTemplate2024",
    # Identifiers
    "Address",
    "Country",
    "Facility",
    "IdentifierScheme",
    "Party",
    "PartyRole",
    "PartyRoleEnum",
    # Primitives
    "Characteristics",
    "Classification",
    "Dimension",
    "FlexibleUri",
    "Image",
    "Link",
    "Measure",
    # Claims
    "Claim",
    "ConformityTopic",
    "Performance",
    "Period",
    "Score",
    # Materials
    "Material",
    # Product
    "Package",
    "Product",
]
