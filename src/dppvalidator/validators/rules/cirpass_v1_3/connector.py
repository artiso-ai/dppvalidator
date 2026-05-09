"""CON v1.9.1 cross-module relation rules for CIRPASS DPP reference structure v1.3.0.

Phase 4 task 4.6 of [docs/plans/CIRPASS_2_MIGRATION.md]. The ``REL``
prefix is reserved for relation/connector rules in the Phase 4
code-prefix audit (avoiding the ``CON`` module-name collision per
the plan's prefix table).

Axioms covered (CON v1.9.1):

- :class:`ConnectorRelationTypeClosureRule` (``REL001``) — relation
  predicates use IRIs from the v1.9.1 closed set
  (:class:`RelationType`).
- :class:`ConnectorSubjectObjectDistinctRule` (``REL002``) — a
  relation cannot connect an entity to itself.
- :class:`ConnectorRelationTemporalRule` (``REL003``) — when both
  ``validFrom`` / ``validTo`` are populated, ``validFrom < validTo``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from dppvalidator.models.cirpass.v1_3.connector import RelationType
from dppvalidator.validators.rules.cirpass_v1_3._helpers import (
    parse_iso_datetime as _parse_iso_datetime,
)

if TYPE_CHECKING:
    from dppvalidator.models.cirpass.v1_3 import ReferencePassport


class ConnectorRelationTypeClosureRule:
    """REL001: relation predicates use the CON v1.9.1 closed set.

    Validates ``ConnectorRelation.relation`` against
    :class:`RelationType`. Predicates outside the enum surface as
    a ``warning`` (downstream taxonomies extend the relation
    hierarchy with their own predicates — pilot extensions are
    valid but worth flagging).
    """

    rule_id: str = "REL001"
    description: str = "ConnectorRelation.relation should use a CON v1.9.1 predicate"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Use a value from "
        "``dppvalidator.models.cirpass.v1_3.connector.RelationType`` — e.g. "
        "``eudpp:hasManufacturer`` or ``eudpp:isConnectedTo``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/REL001"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        if not passport.connector_relations:
            return violations
        valid = {r.value for r in RelationType}
        for i, cr in enumerate(passport.connector_relations):
            if cr.relation not in valid:
                violations.append(
                    (
                        f"$.connectorRelations[{i}].relation",
                        (
                            f"relation predicate {cr.relation!r} is not in the "
                            f"CON v1.9.1 closed set; see ``RelationType``."
                        ),
                    )
                )
        return violations


class ConnectorSubjectObjectDistinctRule:
    """REL002: ``subject`` and ``object`` of a relation must differ.

    A relation that points an entity at itself is structurally
    meaningless for the predicates CON v1.9.1 declares (the only
    legitimate self-referential relation in this space would be
    the not-yet-published ``isPartOf`` reflexive identity, which
    pilot extensions handle separately).
    """

    rule_id: str = "REL002"
    description: str = "ConnectorRelation.subject must differ from object"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Use distinct URIs for ``subject`` and ``object`` — a relation "
        "connects two entities, not an entity to itself."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/REL002"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        if not passport.connector_relations:
            return violations
        for i, cr in enumerate(passport.connector_relations):
            if cr.subject == cr.object:
                violations.append(
                    (
                        f"$.connectorRelations[{i}]",
                        (
                            f"ConnectorRelation.subject and .object are identical "
                            f"({cr.subject!r}); a relation must connect distinct "
                            f"entities."
                        ),
                    )
                )
        return violations


class ConnectorRelationTemporalRule:
    """REL003: ``ConnectorRelation.validFrom`` must precede ``validTo``.

    Mirrors :class:`ActorRoleAssignmentTemporalRule` for the
    optionally-temporal CON relation envelope.
    """

    rule_id: str = "REL003"
    description: str = "ConnectorRelation.validFrom must be before validTo"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Either drop one endpoint (open-ended relation) or supply a "
        "``validFrom`` strictly before ``validTo``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/REL003"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        if not passport.connector_relations:
            return violations
        for i, cr in enumerate(passport.connector_relations):
            if cr.valid_from is None or cr.valid_to is None:
                continue
            start = _parse_iso_datetime(cr.valid_from)
            end = _parse_iso_datetime(cr.valid_to)
            if start is None or end is None:
                continue
            if start >= end:
                violations.append(
                    (
                        f"$.connectorRelations[{i}]",
                        (
                            f"ConnectorRelation.validFrom ({cr.valid_from}) is "
                            f"not before validTo ({cr.valid_to})."
                        ),
                    )
                )
        return violations


# =============================================================================
# Public dispatch
# =============================================================================


ALL_CONNECTOR_RULES: tuple[object, ...] = (
    ConnectorRelationTypeClosureRule(),
    ConnectorSubjectObjectDistinctRule(),
    ConnectorRelationTemporalRule(),
)
