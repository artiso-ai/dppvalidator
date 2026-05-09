"""PRT-coded advisory rule for the PartyRole acceptance gradient.

Phase 9 task 9.8 of [docs/plans/CIRPASS_2_MIGRATION.md]. The upstream
JSON Schema closes ``$defs.PartyRole.properties.role.enum`` at exactly
6 strict values (see
:data:`dppvalidator.models.v0_7.identifiers.SCHEMA_STRICT_ROLES`),
while our :class:`~dppvalidator.models.v0_7.identifiers.PartyRoleEnum`
exposes a wider 20-value surface for back-compat with v0.6 fixtures
and information-fidelity through the CIRPASS reverse shim. ``PRT001``
fires (severity ``info``) when a payload uses one of the 14 wider
values, suggesting the canonical schema-allowed counterpart.

Pass ``ValidationEngine(strict_role_enum=True)`` to upgrade
``PRT001`` from ``info`` to ``error``.

The 14 → 6 mapping below is **advisory only** — the rule does NOT
mutate the passport. It surfaces the gap so users can decide whether
to remap manually, accept the gap, or opt into strict enforcement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from dppvalidator.models.v0_7.identifiers import SCHEMA_STRICT_ROLES

if TYPE_CHECKING:
    from dppvalidator.models.v0_7.envelope import DigitalProductPassport


# Advisory mapping from the 14 wider PartyRoleEnum values to a canonical
# schema-allowed counterpart. Used only by PRT001 to format the
# "did-you-mean" suggestion; the package itself never silently rewrites.
SUGGESTED_STRICT_REMAP: dict[str, str] = {
    "operator": "manufacturer",
    "serviceProvider": "processor",
    "inspector": "processor",
    "certifier": "processor",
    "logisticsProvider": "manufacturer",
    "carrier": "manufacturer",
    "consignor": "manufacturer",
    "consignee": "owner",
    "importer": "manufacturer",
    "exporter": "manufacturer",
    "distributor": "manufacturer",
    "retailer": "owner",
    "brandOwner": "manufacturer",
    "regulator": "processor",
}


class PartyRoleAcceptanceGradientRule:
    """PRT001: surface PartyRole.role values outside the schema's closed-6.

    Severity is ``info`` by default; ``ValidationEngine(strict_role_enum=True)``
    upgrades the in-memory severity to ``error`` at engine-level — the
    rule itself stays informational so pilot extensions can opt-in.

    The rule does **not** mutate the passport. It reports the gap and
    a suggested schema-strict remap from
    :data:`SUGGESTED_STRICT_REMAP`.
    """

    rule_id: str = "PRT001"
    description: str = (
        "PartyRole.role uses a value outside the schema's strict 6 (acceptance "
        "gradient — see SCHEMA_STRICT_ROLES)"
    )
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = (
        "Either accept the gap (Pydantic permissively allows the wider 20-value "
        "set), remap to the canonical 6 via the suggested counterpart in the "
        "violation message, or opt into strict mode with "
        "``ValidationEngine(strict_role_enum=True)``."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/PRT001"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = getattr(passport, "credential_subject", None)
        if product is None:
            return violations
        related = getattr(product, "related_party", None) or []
        for i, pr in enumerate(related):
            role = getattr(pr, "role", None)
            role_value = role.value if hasattr(role, "value") else role
            if role_value is None or role_value in SCHEMA_STRICT_ROLES:
                continue
            suggested = SUGGESTED_STRICT_REMAP.get(role_value, "manufacturer")
            violations.append(
                (
                    f"$.credentialSubject.relatedParty[{i}].role",
                    (
                        f"role {role_value!r} is in the wider Pydantic-permissive "
                        f"PartyRoleEnum but NOT in the schema's closed-6. "
                        f"Suggested schema-strict counterpart: {suggested!r}. "
                        f"Strict-mode validation rejects this value."
                    ),
                )
            )
        return violations


__all__ = [
    "PartyRoleAcceptanceGradientRule",
    "SUGGESTED_STRICT_REMAP",
]
