"""ACTOR v1.9.1 semantic rules for CIRPASS DPP reference structure v1.3.0.

Phase 4 task 4.5 of [docs/plans/CIRPASS_2_MIGRATION.md]. The ``ACT``
prefix is reserved for actor rules in the Phase 4 code-prefix audit.

Axioms covered (ACTOR v1.9.1, ESPR Art 2(37–55)):

- :class:`ActorIdentificationRule` (``ACT001``) — every Actor carries
  a non-empty identifier value with an http(s) scheme URI.
- :class:`ActorRoleClosureRule` (``ACT002``) — role IRIs come from
  the v1.9.1 closed set (:class:`EUDPPRoleClass`); legacy fine-
  grained ESPR roles are tolerated with an info-level signal.
- :class:`MandatoryEconomicOperatorRule` (``ACT003``) — when a
  passport carries any actor data, at least one must play an
  ``EconomicOperatorRole`` (or one of its subtypes) per ESPR Art
  2(46) / Annex III(g).
- :class:`ActorRoleAssignmentTemporalRule` (``ACT004``) — a role
  assignment with both ``validFrom`` and ``validTo`` requires
  ``validFrom < validTo``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from dppvalidator.validators.rules.cirpass_v1_3._helpers import (
    parse_iso_datetime as _parse_iso_datetime,
)
from dppvalidator.vocabularies.eudpp_actors import EUDPPRoleClass

if TYPE_CHECKING:
    from dppvalidator.models.cirpass.v1_3 import ReferencePassport
    from dppvalidator.models.cirpass.v1_3.actor import Actor


# Subset of :class:`EUDPPRoleClass` IRIs that count as
# *EconomicOperatorRole* instances (ESPR Art 2(46)). Used by
# :class:`MandatoryEconomicOperatorRule` to decide whether the
# passport carries the mandatory operator presence.
_ECONOMIC_OPERATOR_ROLES: frozenset[str] = frozenset(
    {
        EUDPPRoleClass.ECONOMIC_OPERATOR.value,
        EUDPPRoleClass.MANUFACTURER.value,
        EUDPPRoleClass.IMPORTER.value,
        EUDPPRoleClass.DISTRIBUTOR.value,
        EUDPPRoleClass.DEALER.value,
        EUDPPRoleClass.FULFILMENT_PROVIDER.value,
        EUDPPRoleClass.AUTHORISED_REP.value,
    }
)


class ActorIdentificationRule:
    """ACT001: every Actor must carry a non-empty identifier.

    Defensive duplicate of the :class:`Identifier` field-level
    invariants. Walks every Actor reachable from the root —
    ``relatedActors[*].actor`` and ``actorRoleAssignments[*].actor`` —
    so empty / mis-shaped identifiers are reported with a locator
    that points at the offending Actor instance.
    """

    rule_id: str = "ACT001"
    description: str = "Every Actor must carry an identifier with a value and http(s) scheme"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Populate ``actor.actorIdentifier.value`` (typically an LEI, EUID, or "
        "EORI) and set ``actor.actorIdentifier.scheme`` to the issuing "
        "register's URI."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/ACT001"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        for path, actor in _walk_actors(passport):
            ident = actor.actor_identifier
            if not ident.value:
                violations.append(
                    (
                        f"{path}.actorIdentifier.value",
                        f"Actor at {path} has empty actorIdentifier.value.",
                    )
                )
                continue
            if not (ident.scheme.startswith("http://") or ident.scheme.startswith("https://")):
                violations.append(
                    (
                        f"{path}.actorIdentifier.scheme",
                        (
                            f"Actor at {path} has actorIdentifier.scheme="
                            f"{ident.scheme!r}; expected an http(s) URI."
                        ),
                    )
                )
        return violations


class ActorRoleClosureRule:
    """ACT002: actor roles come from the v1.9.1 closed set.

    Validates ``ActorRole.role`` and ``ActorRoleAssignment.role``
    against :class:`EUDPPRoleClass`. Roles in the enum but flagged
    ``-1.9.1`` (legacy ESPR-derived fine-grained roles) are tolerated
    silently — Phase 5 mapping shim normalises them to v1.9.1
    super-roles. Roles outside the enum entirely surface as a
    warning (downstream taxonomies may extend the role hierarchy).
    """

    rule_id: str = "ACT002"
    description: str = "Actor roles should use IRIs from the ACTOR v1.9.1 enum"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Use a value from "
        "``dppvalidator.vocabularies.eudpp_actors.EUDPPRoleClass`` — the "
        "v1.9.1 super-categories or the ESPR fine-grained roles."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/ACT002"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        valid = {r.value for r in EUDPPRoleClass}
        if passport.related_actors:
            for i, ar in enumerate(passport.related_actors):
                if ar.role not in valid:
                    violations.append(
                        (
                            f"$.relatedActors[{i}].role",
                            (
                                f"role {ar.role!r} is not in the ACTOR v1.9.1 "
                                f"enum; see ``EUDPPRoleClass`` for valid IRIs."
                            ),
                        )
                    )
        if passport.actor_role_assignments:
            for i, ara in enumerate(passport.actor_role_assignments):
                if ara.role not in valid:
                    violations.append(
                        (
                            f"$.actorRoleAssignments[{i}].role",
                            (
                                f"role {ara.role!r} is not in the ACTOR v1.9.1 "
                                f"enum; see ``EUDPPRoleClass`` for valid IRIs."
                            ),
                        )
                    )
        return violations


class MandatoryEconomicOperatorRule:
    """ACT003: at least one EconomicOperatorRole when actors are declared.

    ESPR Art 2(46) / Annex III(g) requires every DPP to identify at
    least one economic operator. The rule fires only when the
    passport already declares actors — a passport with no actor
    metadata at all is the responsibility of model-layer presence
    validation, not this rule. Severity is ``warning`` because the
    pure structural check is intentionally lenient (some pilot
    payloads carry only AuthorityRole / NotifiedBodyRole entries
    where the manufacturer is referenced via ``connectorRelations``;
    Phase 5 reconciles).
    """

    rule_id: str = "ACT003"
    description: str = "At least one economic-operator-role actor should be present"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Add an entry in ``relatedActors`` (or ``actorRoleAssignments``) with "
        "``role = eudpp:ManufacturerRole`` (or another EconomicOperatorRole "
        "subtype) per ESPR Annex III(g)."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/ACT003"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        actors_declared = bool(passport.related_actors or passport.actor_role_assignments)
        if not actors_declared:
            return violations
        roles: list[str] = []
        if passport.related_actors:
            roles.extend(ar.role for ar in passport.related_actors)
        if passport.actor_role_assignments:
            roles.extend(ara.role for ara in passport.actor_role_assignments)
        if not any(r in _ECONOMIC_OPERATOR_ROLES for r in roles):
            violations.append(
                (
                    "$.relatedActors",
                    (
                        "Passport carries actor data but no EconomicOperatorRole "
                        "(ESPR Art 2(46)). Add a manufacturer / importer / "
                        "distributor / dealer / fulfilment-provider / authorised-"
                        "representative role."
                    ),
                )
            )
        return violations


class ActorRoleAssignmentTemporalRule:
    """ACT004: ``ActorRoleAssignment.validFrom`` must precede ``validTo``.

    The v1.9.1 ACTOR module promoted role assignment to a first-
    class entity with explicit temporal scoping. When both endpoints
    are populated, ``validFrom < validTo`` must hold. Either endpoint
    may be absent (open-ended) without violation.
    """

    rule_id: str = "ACT004"
    description: str = "ActorRoleAssignment.validFrom must be before validTo"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Either drop one endpoint (open-ended assignment) or supply a "
        "``validFrom`` strictly before ``validTo``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/ACT004"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        if not passport.actor_role_assignments:
            return violations
        for i, ara in enumerate(passport.actor_role_assignments):
            if ara.valid_from is None or ara.valid_to is None:
                continue
            start = _parse_iso_datetime(ara.valid_from)
            end = _parse_iso_datetime(ara.valid_to)
            if start is None or end is None:
                # Malformed timestamps are caught by the model layer;
                # we don't double-report at semantic layer.
                continue
            if start >= end:
                violations.append(
                    (
                        f"$.actorRoleAssignments[{i}]",
                        (
                            f"ActorRoleAssignment.validFrom ({ara.valid_from}) "
                            f"is not before validTo ({ara.valid_to})."
                        ),
                    )
                )
        return violations


# =============================================================================
# Helpers
# =============================================================================


def _walk_actors(passport: ReferencePassport) -> list[tuple[str, Actor]]:
    """Yield every Actor reachable from the root with its JSON path."""
    found: list[tuple[str, Actor]] = []
    if passport.related_actors:
        for i, ar in enumerate(passport.related_actors):
            found.append((f"$.relatedActors[{i}].actor", ar.actor))
    if passport.actor_role_assignments:
        for i, ara in enumerate(passport.actor_role_assignments):
            found.append((f"$.actorRoleAssignments[{i}].actor", ara.actor))
    return found


# =============================================================================
# Public dispatch
# =============================================================================


ALL_ACTOR_RULES: tuple[object, ...] = (
    ActorIdentificationRule(),
    ActorRoleClosureRule(),
    MandatoryEconomicOperatorRule(),
    ActorRoleAssignmentTemporalRule(),
)
