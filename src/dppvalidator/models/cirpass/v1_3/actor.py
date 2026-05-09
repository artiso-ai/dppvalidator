"""Actor and role types for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.6 of [docs/plans/CIRPASS_2_MIGRATION.md]. Models the
``Actor`` / ``Role`` axes from EUDPP ACTOR v1.9.1 plus the new
``ActorRoleAssignment`` first-class assignment relationship.

Mapping highlights:

- ESPR Annex distinguishes ~24 specific economic-operator role types
  (Manufacturer, Importer, Distributor, …); EUDPP v1.9.1 consolidates
  these into 6 super-role classes. :class:`ActorRole` accepts
  finer-grained ESPR roles AND the v1.9.1 super-categories — the
  Phase 5 mapping shim handles the granularity gap.
- :class:`Facility` is now in ACTOR (was P_DPP in v1.7.1, removed in
  v1.9.1 per the P_DPP changelog).
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.cirpass.v1_3.i18n import LocalisedText
from dppvalidator.models.cirpass.v1_3.product import Identifier
from dppvalidator.vocabularies.eudpp_actors import EUDPPRoleClass


class Actor(UNTPBaseModel):
    """An economic operator, regulator, or other party.

    Maps to ``eudpp:Actor`` (ACTOR v1.9.1). Carries the actor's
    primary identifier, a multilingual name, and optional contact /
    address fields.

    Wire shape (minimal):
        ``{"actorIdentifier": {...}, "actorName": [...]}``
    """

    _jsonld_type: ClassVar[list[str]] = ["Actor"]

    actor_identifier: Identifier = Field(
        ...,
        alias="actorIdentifier",
        description="Primary actor identifier (LEI, EUID, EORI, …).",
    )
    actor_name: list[LocalisedText] = Field(
        ...,
        alias="actorName",
        min_length=1,
        description="Actor's legal / trade name(s), one per language.",
    )
    registered_trade_name: list[LocalisedText] | None = Field(
        default=None,
        alias="registeredTradeName",
        description="Registered trade-name(s) where distinct from the legal name.",
    )
    registered_trademark: list[LocalisedText] | None = Field(
        default=None,
        alias="registeredTrademark",
        description="Registered trademark(s) associated with the actor.",
    )


class Facility(UNTPBaseModel):
    """A physical site where production / processing occurs.

    Maps to ``eudpp:Facility`` (ACTOR v1.9.1 — relocated from P_DPP in
    the v1.9.1 spec rewrite). The CIRPASS message references a Facility
    via the actor's ``usesFacility`` relation; the facility itself
    carries an identifier scheme (so e.g. a permit ID and an ECEFACT
    ID for the same facility don't collide).
    """

    _jsonld_type: ClassVar[list[str]] = ["Facility"]

    facility_identifier: Identifier = Field(
        ...,
        alias="facilityIdentifier",
        description="Primary facility identifier with scheme.",
    )
    facility_name: list[LocalisedText] = Field(
        ...,
        alias="facilityName",
        min_length=1,
        description="Facility name(s), one per language.",
    )


class ActorRole(UNTPBaseModel):
    """An actor playing a specific role on this DPP.

    Wire shape:
        ``{"actor": <Actor>, "role": "eudpp:ManufacturerRole"}``

    The ``role`` field accepts the compact ``eudpp:`` IRI of any role
    class — both the v1.9.1 super-categories
    (``EconomicOperatorRole``, ``CircularEconomyRole``, etc.) and the
    finer-grained ESPR-derived roles
    (``ManufacturerRole``, ``RecyclerRole``, etc.) that
    :class:`EUDPPRoleClass` exposes for back-compat.
    """

    _jsonld_type: ClassVar[list[str]] = ["ActorRole"]

    actor: Actor = Field(..., description="The actor playing the role.")
    role: str = Field(
        ...,
        description=(
            "Compact ``eudpp:`` IRI of the role class. See "
            ":class:`dppvalidator.vocabularies.eudpp_actors.EUDPPRoleClass` "
            "for the canonical set."
        ),
    )

    @property
    def role_enum(self) -> EUDPPRoleClass | None:
        """Return the :class:`EUDPPRoleClass` member if ``role`` matches one.

        Returns ``None`` for roles outside the registered set
        (downstream taxonomies that extend the EUDPP role hierarchy
        with their own classes are still legal — :class:`ActorRole`
        carries the IRI string, not an enforced enum).
        """
        try:
            return EUDPPRoleClass(self.role)
        except ValueError:
            return None


class ActorRoleAssignment(UNTPBaseModel):
    """First-class actor-plays-role-in-context relationship (ACTOR v1.9.1).

    +1.9.1: ACTOR v1.9.1 introduced ``eudpp:ActorRoleAssignment`` as a
    first-class entity (rather than a binary edge) so that role
    assignments can carry their own metadata — temporal scoping,
    authority that conferred the role, supporting documentation, etc.

    Wire shape:
        ``{"actor": <Actor>, "role": "eudpp:...",
           "validFrom": "2026-01-01T00:00:00Z",
           "validTo": "2031-12-31T23:59:59Z"}``
    """

    _jsonld_type: ClassVar[list[str]] = ["ActorRoleAssignment"]

    actor: Actor = Field(..., description="The actor receiving the role.")
    role: str = Field(
        ...,
        description="Compact ``eudpp:`` IRI of the role class assigned.",
    )
    valid_from: str | None = Field(
        default=None,
        alias="validFrom",
        description=(
            "ISO 8601 UTC datetime from which the assignment is "
            "effective (``eudpp:assignmentValidFrom``)."
        ),
    )
    valid_to: str | None = Field(
        default=None,
        alias="validTo",
        description=(
            "ISO 8601 UTC datetime after which the assignment expires "
            "(``eudpp:assignmentValidTo``). Absent ⇒ open-ended."
        ),
    )
