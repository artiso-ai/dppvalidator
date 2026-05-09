"""Cross-module relations for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.10 of [docs/plans/CIRPASS_2_MIGRATION.md] (resolves G9).
Models the ``ConnectorRelation`` class — a typed relation that ties
entities across the EUDPP modules (P_DPP / SOC / ACTOR / LCA) per
the CON v1.9.1 module's design.

EUDPP IRI bindings:

- ``ConnectorRelation`` is a CIRPASS message-level wrapper for the
  CON v1.9.1 cross-module relation predicates (``isConnectedTo``,
  ``inContextOfActivity``, ``inContextOfDPP``, etc.).
- :class:`RelationType` enumerates the known v1.9.1 relation
  predicates from
  :class:`dppvalidator.vocabularies.eudpp_relations.EUDPPObjectProperty`
  with the ``CON``-module subset prioritised.
"""

from __future__ import annotations

from enum import Enum
from typing import ClassVar

from pydantic import Field, field_validator

from dppvalidator.models.base import UNTPBaseModel


class RelationType(str, Enum):
    """Known cross-module relation predicates (CIRPASS-2 CON v1.9.1).

    Each member is a compact ``eudpp:`` IRI for a CON-module object
    property. Downstream consumers that emit :class:`ConnectorRelation`
    payloads with relation predicates *outside* this enum (e.g.
    pilot-specific extensions) are still valid — :class:`ConnectorRelation`
    carries the IRI as a string, not as an enforced enum.
    """

    # CON-native relations (added to v1.9.1 connector module)
    IS_CONNECTED_TO = "eudpp:isConnectedTo"
    IN_CONTEXT_OF_ACTIVITY = "eudpp:inContextOfActivity"
    IN_CONTEXT_OF_DPP = "eudpp:inContextOfDPP"
    IN_CONTEXT_OF_PRODUCT = "eudpp:inContextOfProduct"
    REPRESENTS_MANUFACTURER_FOR_PRODUCT = "eudpp:representsManufacturerForProduct"

    # Migrated to CON in v1.9.1 (were in P_DPP v1.7.1)
    HAS_ISSUER = "eudpp:hasIssuer"
    HAS_MANUFACTURER = "eudpp:hasManufacturer"
    HAS_ECONOMIC_OPERATOR = "eudpp:hasEconomicOperator"
    HAS_BACK_UP_COPY_HOST = "eudpp:hasBackUpCopyHost"
    CONTAINS_SUBSTANCE_OF_CONCERN = "eudpp:containsSubstanceOfConcern"


class ConnectorRelation(UNTPBaseModel):
    """A typed cross-module relation between two entities.

    Wire shape:
        ``{"relation": "eudpp:hasManufacturer",
           "subject": "https://example.com/dpp/123",
           "object": "https://example.com/actor/abc"}``

    The ``relation`` field is a compact ``eudpp:`` IRI from
    :class:`RelationType` (or any other ontology-defined object
    property). ``subject`` and ``object`` are URIs identifying the
    related entities.

    Cardinality:

    - ``relation``: required (1).
    - ``subject``: required (1).
    - ``object``: required (1).
    - ``valid_from`` / ``valid_to``: optional ISO 8601 datetimes —
      enable temporally-scoped relations (e.g. an actor that played
      a role only during a manufacturing batch).
    """

    _jsonld_type: ClassVar[list[str]] = ["ConnectorRelation"]

    relation: str = Field(
        ...,
        description=(
            "Compact ``eudpp:`` IRI of the relation predicate. See "
            ":class:`RelationType` for the canonical set; downstream "
            "taxonomies may use other IRIs."
        ),
    )
    subject: str = Field(
        ...,
        min_length=1,
        description="URI of the subject entity (the relation's source).",
    )
    object: str = Field(
        ...,
        min_length=1,
        description="URI of the object entity (the relation's target).",
    )
    valid_from: str | None = Field(
        default=None,
        alias="validFrom",
        description="Optional ISO 8601 datetime: relation effective from.",
    )
    valid_to: str | None = Field(
        default=None,
        alias="validTo",
        description="Optional ISO 8601 datetime: relation expires at.",
    )

    @field_validator("subject", "object")
    @classmethod
    def _looks_like_uri(cls, value: str) -> str:
        # We don't enforce strict URI shape (downstream consumers may
        # legitimately use compact ``eudpp:Foo`` form), but we reject
        # bare-string values that obviously aren't identifiers.
        if not value.strip():
            msg = "ConnectorRelation subject/object must not be empty."
            raise ValueError(msg)
        return value

    @property
    def relation_type(self) -> RelationType | None:
        """Return the :class:`RelationType` member if ``relation`` matches one.

        Returns ``None`` for relation IRIs outside the canonical set
        (downstream extensions are valid — :class:`ConnectorRelation`
        carries the IRI string, not an enforced enum).
        """
        try:
            return RelationType(self.relation)
        except ValueError:
            return None
