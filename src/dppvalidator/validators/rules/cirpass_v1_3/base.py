"""Root structural semantic rules for CIRPASS DPP reference structure v1.3.0.

Phase 4 task 4.2 of [docs/plans/CIRPASS_2_MIGRATION.md]. The ``CR``
prefix is reserved for CIRPASS reference base rules in the Phase 4
code-prefix audit (see plan §Phase 4 prefix table).

These rules cover the *root* structural axioms of the v1.3.0 message:
identifier uniqueness, monotonic temporal envelopes, BCP-47 well-
formedness across multilingual labels, and DPP supersedence chains.

Rule check signature
====================

Each rule exposes the same ``check(passport)`` shape as the UNTP rule
tree (a list of ``(json_path, message)`` tuples), but the ``passport``
argument is the CIRPASS root :class:`ReferencePassport` rather than a
UNTP envelope. The semantic-layer dispatch picks the right rule set
from the family-aware
:data:`dppvalidator.validators.rules.cirpass_v1_3.ALL_RULES_CIRPASS_V1_3`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from dppvalidator.models.cirpass.v1_3.i18n import is_valid_bcp47

if TYPE_CHECKING:
    from dppvalidator.models.cirpass.v1_3 import LocalisedText, ReferencePassport


class DPPIdentifierUniqueRule:
    """CR001: ``dppIdentifier.value`` differs from the product identifier.

    The DPP identifier and the product identifier address *different*
    things — the DPP is a document about the product. Some upstream
    fixtures conflate the two (e.g. by re-using the GTIN as the DPP
    URI), which makes downstream supersedence chains brittle.
    """

    rule_id: str = "CR001"
    description: str = "DPP identifier must differ from product identifier"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Issue a DPP-specific URI for ``dppIdentifier.value`` (typically a "
        "register-rooted URL) rather than re-using the product GTIN."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CR001"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        dpp_value = passport.dpp_identifier.value
        product_value = passport.product.product_identifier.value
        if dpp_value and dpp_value == product_value:
            violations.append(
                (
                    "$.dppIdentifier.value",
                    (
                        f"dppIdentifier.value ({dpp_value!r}) is identical to "
                        f"product.productIdentifier.value. Issue a DPP-scoped URI "
                        f"so the DPP and the product can be addressed separately."
                    ),
                )
            )
        return violations


class ProductIdentifierShapeRule:
    """CR002: product identifier scheme must be an http(s) URI.

    Defensive duplicate of the model-level
    :func:`Identifier._scheme_is_uri` invariant. Issued at the
    semantic layer for parity with v0.6/v0.7 reporting (where
    ``VOC005`` covers the GTIN check at the same level).
    """

    rule_id: str = "CR002"
    description: str = "Product identifier scheme must be an http(s) URI"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Set ``product.productIdentifier.scheme`` to the issuing register's "
        "URI (e.g. ``https://gs1.org/voc/`` for GTINs)."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CR002"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        scheme = passport.product.product_identifier.scheme
        if not (scheme.startswith("http://") or scheme.startswith("https://")):
            violations.append(
                (
                    "$.product.productIdentifier.scheme",
                    (
                        f"product.productIdentifier.scheme={scheme!r} is not an "
                        f"http(s) URI; the scheme URI is what disambiguates "
                        f"identifier spaces."
                    ),
                )
            )
        return violations


class EffectivePeriodMonotonicRule:
    """CR003: ``effectivePeriod.start`` must precede ``end``.

    Defensive duplicate of the model-level
    :func:`EffectivePeriod._start_before_end` invariant. Re-issued at
    semantic layer so consumers driving validation through the
    semantic pipeline (skipping model layer) still see the violation.
    """

    rule_id: str = "CR003"
    description: str = "effectivePeriod.start must be before end"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Either drop ``effectivePeriod.end`` (DPP effective indefinitely) "
        "or supply a value strictly after ``start``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CR003"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        period = passport.effective_period
        if period is not None and period.end is not None and period.start > period.end:
            violations.append(
                (
                    "$.effectivePeriod",
                    (
                        f"effectivePeriod.start={period.start.isoformat()} is "
                        f"later than .end={period.end.isoformat()}; the period "
                        f"is empty."
                    ),
                )
            )
        return violations


class IssuedAtBeforeEffectiveRule:
    """CR004: ``issuedAt.timestamp`` must be ≤ ``effectivePeriod.end``.

    The DPP cannot be issued *after* it has expired. The reverse
    direction (issued *before* effective start) is normal — DPPs are
    routinely cut early and activate when the product ships.
    """

    rule_id: str = "CR004"
    description: str = "issuedAt.timestamp must precede effectivePeriod.end"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Re-issue the DPP with a timestamp inside the effective window, or "
        "extend ``effectivePeriod.end``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CR004"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        period = passport.effective_period
        if period is None or period.end is None:
            return violations
        issued_at = passport.issued_at.timestamp
        if issued_at > period.end:
            violations.append(
                (
                    "$.issuedAt.timestamp",
                    (
                        f"issuedAt.timestamp={issued_at.isoformat()} is later "
                        f"than effectivePeriod.end={period.end.isoformat()}; "
                        f"a DPP cannot be issued after it has expired."
                    ),
                )
            )
        return violations


class BCP47LanguageTagRule:
    """CR005: every ``LocalisedText.language`` is a recognised BCP-47 tag.

    Defensive duplicate of the :class:`LocalisedText._validate_bcp47`
    invariant. Walks every LocalisedText reachable from the root —
    product names, descriptions, classification names, material names,
    actor names, hazard statements, impact-category names, etc. —
    so a malformed tag in any of those sites is reported with a
    locator that points at the field, not the model construction site.
    """

    rule_id: str = "CR005"
    description: str = "Every LocalisedText.language tag must be valid BCP-47"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Use a primary subtag (2-3 letters), optionally followed by a script "
        "subtag (4 letters), region subtag (2 letters or 3 digits), and "
        "variant subtag (5-8 alnum) — e.g. ``en``, ``de``, ``zh-Hant``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CR005"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        # Walk every LocalisedText reachable from the root. The model
        # has already enforced BCP-47 in its constructors, so this
        # rule fires only when a caller has *bypassed* model validation
        # (e.g. constructed the passport via ``model_construct`` to
        # smuggle in skipped data) — but still acts as the
        # authoritative semantic-layer check for the field.
        for path, lt in _walk_localised_text(passport):
            if not is_valid_bcp47(lt.language):
                violations.append(
                    (
                        path,
                        (
                            f"language tag {lt.language!r} is not a recognised "
                            f"BCP-47 form; expected ``primary[-Script][-REGION]"
                            f"[-variant]``."
                        ),
                    )
                )
        return violations


class PreviousDPPDistinctRule:
    """CR006: ``previousDpp`` must differ from this DPP's identifier.

    A DPP cannot supersede itself — the supersedence chain would be
    a cycle of length 1.
    """

    rule_id: str = "CR006"
    description: str = "previousDpp must differ from this DPP's identifier"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Drop ``previousDpp`` for the first DPP in a chain, or set it to the "
        "URI of an *earlier* DPP (cannot be self-referential)."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CR006"

    def check(self, passport: ReferencePassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        previous = passport.previous_dpp
        this_id = passport.dpp_identifier.value
        if previous is not None and previous == this_id:
            violations.append(
                (
                    "$.previousDpp",
                    (
                        f"previousDpp ({previous!r}) is identical to this "
                        f"DPP's own identifier; supersedence chains cannot "
                        f"be self-referential."
                    ),
                )
            )
        return violations


# =============================================================================
# Helpers
# =============================================================================


def _walk_localised_text(
    passport: ReferencePassport,
) -> list[tuple[str, LocalisedText]]:
    """Walk every LocalisedText reachable from the passport root.

    Returns a list of ``(json_path, LocalisedText)`` tuples so the
    caller can attribute violations to the field that carried the
    malformed tag.
    """
    found: list[tuple[str, LocalisedText]] = []

    def _extend(prefix: str, items: list[LocalisedText] | None) -> None:
        if not items:
            return
        for i, lt in enumerate(items):
            found.append((f"{prefix}[{i}].language", lt))

    # Product
    _extend("$.product.productName", passport.product.product_name)
    _extend("$.product.description", passport.product.description)
    if passport.product.commodity_code:
        for i, c in enumerate(passport.product.commodity_code):
            _extend(f"$.product.commodityCode[{i}].name", c.name)

    # Composition / materials
    if passport.composition is not None:
        for i, m in enumerate(passport.composition.materials):
            _extend(f"$.composition.materials[{i}].materialName", m.material_name)

    # Actors (related and assignments)
    if passport.related_actors:
        for i, ar in enumerate(passport.related_actors):
            _extend(f"$.relatedActors[{i}].actor.actorName", ar.actor.actor_name)
            _extend(
                f"$.relatedActors[{i}].actor.registeredTradeName",
                ar.actor.registered_trade_name,
            )
            _extend(
                f"$.relatedActors[{i}].actor.registeredTrademark",
                ar.actor.registered_trademark,
            )
    if passport.actor_role_assignments:
        for i, ara in enumerate(passport.actor_role_assignments):
            _extend(
                f"$.actorRoleAssignments[{i}].actor.actorName",
                ara.actor.actor_name,
            )

    # Substances of concern
    if passport.substances_of_concern:
        for i, soc in enumerate(passport.substances_of_concern):
            _extend(f"$.substancesOfConcern[{i}].tradeName", soc.trade_name)
            if soc.hazards:
                for j, h in enumerate(soc.hazards):
                    _extend(
                        f"$.substancesOfConcern[{i}].hazards[{j}].statement",
                        h.statement,
                    )

    # LCA impact categories
    if passport.lca is not None:
        for i, r in enumerate(passport.lca.results):
            _extend(f"$.lca.results[{i}].impactCategory.name", r.impact_category.name)

    return found


# =============================================================================
# Public dispatch
# =============================================================================


ALL_BASE_RULES: tuple[object, ...] = (
    DPPIdentifierUniqueRule(),
    ProductIdentifierShapeRule(),
    EffectivePeriodMonotonicRule(),
    IssuedAtBeforeEffectiveRule(),
    BCP47LanguageTagRule(),
    PreviousDPPDistinctRule(),
)
