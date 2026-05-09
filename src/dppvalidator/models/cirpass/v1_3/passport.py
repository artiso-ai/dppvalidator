"""Root passport type for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.4 of [docs/plans/CIRPASS_2_MIGRATION.md]. Models the
top-level ``ReferencePassport`` that wraps a Product plus the DPP-
envelope metadata (issued-at / effective-period / actors / substances
of concern / LCA / cross-module relations / multilingual labels).

Relationship to UNTP:

- UNTP DPP: Verifiable-Credential envelope wrapping a credentialSubject
  whose root is a Product.
- CIRPASS DPP reference structure v1.3.0: hierarchical message with a
  Product at the root + sibling fields for actors, substances, LCA, …

The Phase 5 mapping shim (``compat/untp_0_7_to_cirpass_1_3.py``)
translates between the two shapes; the structural difference here is
the explicit absence of a ``credentialSubject`` envelope.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.cirpass.v1_3.actor import ActorRole, ActorRoleAssignment
from dppvalidator.models.cirpass.v1_3.connector import ConnectorRelation
from dppvalidator.models.cirpass.v1_3.lca import LifeCycleAssessment
from dppvalidator.models.cirpass.v1_3.material import Composition
from dppvalidator.models.cirpass.v1_3.product import Identifier, Product
from dppvalidator.models.cirpass.v1_3.substances import SubstanceOfConcern
from dppvalidator.models.cirpass.v1_3.temporal import EffectivePeriod, IssuedAt
from dppvalidator.vocabularies.eudpp_classes import EUDPPClass


class ReferencePassport(UNTPBaseModel):
    """The CIRPASS DPP reference structure root.

    Maps to ``eudpp:DPP`` (P_DPP v1.9.1). Mirrors the v1.3.0 message
    tree-view shape: a Product at the root + sibling fields for the
    DPP-level metadata.

    Wire shape (minimal):
        ``{"dppIdentifier": {...}, "product": <Product>,
           "issuedAt": <IssuedAt>}``

    Cardinality:

    - ``dpp_identifier``: required (1) — uniquely identifies *this*
      DPP (distinct from the product's identifier).
    - ``product``: required (1) — the Product the DPP describes.
    - ``issued_at``: required (1) — when the DPP was issued.
    - ``effective_period``: optional — explicit validity window.
    - ``related_actors``: optional list of (actor, role) pairs.
    - ``actor_role_assignments``: optional list of first-class
      role-assignment relationships (v1.9.1 ACTOR addition).
    - ``composition``: optional — the product's material composition.
    - ``substances_of_concern``: optional (0..n).
    - ``lca``: optional — Life-Cycle Assessment results.
    - ``connector_relations``: optional (0..n) cross-module relations.
    - ``previous_dpp``: optional URI of the DPP this one supersedes
      (maps to ``eudpp:linkToPreviousDPP``).
    """

    _jsonld_type: ClassVar[list[str]] = ["DigitalProductPassport", EUDPPClass.DPP.value]

    dpp_identifier: Identifier = Field(
        ...,
        alias="dppIdentifier",
        description="Unique identifier for this DPP instance (``eudpp:uniqueDPPID``).",
    )
    product: Product = Field(
        ...,
        description="The product this DPP describes.",
    )
    issued_at: IssuedAt = Field(
        ...,
        alias="issuedAt",
        description="When this DPP was issued.",
    )
    effective_period: EffectivePeriod | None = Field(
        default=None,
        alias="effectivePeriod",
        description="Validity window during which this DPP applies.",
    )
    related_actors: list[ActorRole] | None = Field(
        default=None,
        alias="relatedActors",
        description=(
            "Actors associated with this DPP and their roles "
            "(manufacturer, importer, recycler, etc.)."
        ),
    )
    actor_role_assignments: list[ActorRoleAssignment] | None = Field(
        default=None,
        alias="actorRoleAssignments",
        description=(
            "First-class actor-plays-role-in-context relationships "
            "(v1.9.1 ACTOR module). Use this when an assignment "
            "carries its own metadata (temporal scope, conferring "
            "authority, supporting documentation)."
        ),
    )
    composition: Composition | None = Field(
        default=None,
        description="Material composition of the product.",
    )
    substances_of_concern: list[SubstanceOfConcern] | None = Field(
        default=None,
        alias="substancesOfConcern",
        description="REACH / SVHC-tracked substances present in the product.",
    )
    lca: LifeCycleAssessment | None = Field(
        default=None,
        description="Life-Cycle Assessment / EPD results.",
    )
    connector_relations: list[ConnectorRelation] | None = Field(
        default=None,
        alias="connectorRelations",
        description="Cross-module typed relations (CON v1.9.1 predicates).",
    )
    previous_dpp: str | None = Field(
        default=None,
        alias="previousDpp",
        description=(
            "URI of the DPP this one supersedes "
            "(``eudpp:linkToPreviousDPP``). Enables version chains."
        ),
    )
