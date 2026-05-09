"""Phase 9 task 9.8 — PartyRoleEnum acceptance gradient + PRT001 advisory.

Verifies the dual-tier acceptance:

- **Pydantic-permissive (Layer 2):** all 20 values of ``PartyRoleEnum``
  parse without error.
- **Schema-strict (Layer 1):** only the 6 in ``SCHEMA_STRICT_ROLES``
  survive the upstream JSON Schema enum check.

Plus the advisory rule's behaviour:

- ``info`` severity by default → emitted under ``ValidationResult.info``.
- ``error`` severity when ``ValidationEngine(strict_role_enum=True)`` →
  emitted under ``ValidationResult.errors``; ``valid`` flips to False.

The tests do **not** mutate the rule object — strict-mode upgrade is
applied at the SemanticValidator emit boundary.
"""

from __future__ import annotations

from typing import Any

import pytest

from dppvalidator.models.v0_7.identifiers import (
    SCHEMA_STRICT_ROLES,
    PartyRoleEnum,
)
from dppvalidator.validators.engine import ValidationEngine
from dppvalidator.validators.rules.v0_7.party_role import (
    SUGGESTED_STRICT_REMAP,
    PartyRoleAcceptanceGradientRule,
)

# ---------------------------------------------------------------------------
# Surface invariants
# ---------------------------------------------------------------------------


class TestSchemaStrictSurface:
    def test_strict_set_size_matches_schema_closed_enum(self) -> None:
        assert len(SCHEMA_STRICT_ROLES) == 6

    def test_strict_set_values(self) -> None:
        assert (
            frozenset(
                {
                    "owner",
                    "producer",
                    "manufacturer",
                    "processor",
                    "remanufacturer",
                    "recycler",
                }
            )
            == SCHEMA_STRICT_ROLES
        )

    def test_pydantic_enum_is_superset_of_strict_set(self) -> None:
        pydantic_values = {e.value for e in PartyRoleEnum}
        assert SCHEMA_STRICT_ROLES.issubset(pydantic_values)
        assert len(pydantic_values) == 20

    def test_is_schema_strict_method(self) -> None:
        assert PartyRoleEnum.MANUFACTURER.is_schema_strict() is True
        assert PartyRoleEnum.IMPORTER.is_schema_strict() is False

    def test_suggested_remap_covers_all_14_wider_values(self) -> None:
        wider = {e.value for e in PartyRoleEnum} - SCHEMA_STRICT_ROLES
        assert wider == set(SUGGESTED_STRICT_REMAP.keys())

    def test_suggested_remap_targets_are_all_strict(self) -> None:
        for source, target in SUGGESTED_STRICT_REMAP.items():
            assert target in SCHEMA_STRICT_ROLES, (
                f"remap target {target!r} for {source!r} is not in the schema-strict 6"
            )


# ---------------------------------------------------------------------------
# PRT001 rule behaviour
# ---------------------------------------------------------------------------


def _build_minimal_passport_with_role(role_value: str) -> dict[str, Any]:
    """Return a minimal v0.7.0 DPP dict with one relatedParty role."""
    return {
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.7.0/",
        ],
        "id": "https://example.com/credentials/dpp-1",
        "name": "Smoke test DPP",
        "issuer": {
            "type": ["CredentialIssuer"],
            "id": "did:web:example.com",
            "name": "Example Co",
        },
        "validFrom": "2026-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["Product"],
            "id": "https://example.com/products/p1",
            "name": "Widget",
            "idScheme": {
                "type": ["IdentifierScheme"],
                "id": "https://example.com/scheme",
                "name": "Example scheme",
            },
            "idGranularity": "model",
            "productCategory": [
                {
                    "type": ["Classification"],
                    "schemeId": "https://unstats.un.org/cpc",
                    "schemeName": "UN CPC",
                    "code": "14110",
                    "name": "Widgets",
                }
            ],
            "producedAtFacility": {
                "type": ["Facility"],
                "id": "https://example.com/facility/1",
                "name": "Main plant",
            },
            "countryOfProduction": {
                "type": ["Country"],
                "countryCode": "DE",
                "countryName": "Germany",
            },
            "productionDate": "2025-01-01",
            "relatedParty": [
                {
                    "type": ["PartyRole"],
                    "role": role_value,
                    "party": {
                        "type": ["Party"],
                        "id": "did:web:related.example.com",
                        "name": "Related Co",
                    },
                }
            ],
        },
    }


class TestPRT001RuleDefault:
    """Default severity = info; never triggers errors[]."""

    @pytest.mark.parametrize("strict_role", sorted(SCHEMA_STRICT_ROLES))
    def test_strict_roles_do_not_fire(self, strict_role: str) -> None:
        payload = _build_minimal_passport_with_role(strict_role)
        result = ValidationEngine(schema_version="0.7.0").validate(payload)
        prt = [
            i
            for i in (result.errors or []) + (result.warnings or []) + (result.info or [])
            if i.code == "PRT001"
        ]
        assert prt == [], f"PRT001 fired on schema-strict role {strict_role!r}"

    @pytest.mark.parametrize(
        "wider_role",
        sorted({e.value for e in PartyRoleEnum} - SCHEMA_STRICT_ROLES),
    )
    def test_wider_roles_emit_info(self, wider_role: str) -> None:
        payload = _build_minimal_passport_with_role(wider_role)
        result = ValidationEngine(schema_version="0.7.0").validate(payload)
        prt = [i for i in (result.info or []) if i.code == "PRT001"]
        assert len(prt) == 1, f"PRT001 missing for wider role {wider_role!r}"
        suggested = SUGGESTED_STRICT_REMAP[wider_role]
        assert suggested in prt[0].message
        # Also confirm it does NOT appear in errors
        assert all(e.code != "PRT001" for e in (result.errors or []))


class TestPRT001StrictRoleEnumFlag:
    """strict_role_enum=True upgrades PRT001 from info → error."""

    def test_strict_role_does_not_flip_when_compliant(self) -> None:
        payload = _build_minimal_passport_with_role("manufacturer")
        result = ValidationEngine(schema_version="0.7.0", strict_role_enum=True).validate(payload)
        assert all(e.code != "PRT001" for e in (result.errors or []))

    def test_wider_role_flips_to_error_under_strict(self) -> None:
        payload = _build_minimal_passport_with_role("importer")
        result = ValidationEngine(schema_version="0.7.0", strict_role_enum=True).validate(payload)
        prt_errors = [e for e in (result.errors or []) if e.code == "PRT001"]
        assert len(prt_errors) == 1
        assert prt_errors[0].severity == "error"
        # And NOT in info[]
        assert all(i.code != "PRT001" for i in (result.info or []))


class TestPRT001RuleStandalone:
    """Direct rule invocation on a Pydantic passport."""

    def test_check_returns_no_violations_on_strict_roles(self) -> None:
        rule = PartyRoleAcceptanceGradientRule()
        payload = _build_minimal_passport_with_role("manufacturer")
        # Parse via the engine to get a typed passport
        passport = ValidationEngine(schema_version="0.7.0").validate(payload).passport
        violations = rule.check(passport)
        assert violations == []

    def test_check_returns_violation_on_wider_role(self) -> None:
        rule = PartyRoleAcceptanceGradientRule()
        payload = _build_minimal_passport_with_role("importer")
        passport = ValidationEngine(schema_version="0.7.0").validate(payload).passport
        violations = rule.check(passport)
        assert len(violations) == 1
        path, message = violations[0]
        assert path == "$.credentialSubject.relatedParty[0].role"
        assert "'manufacturer'" in message
        assert "'importer'" in message


class TestPRT001ShimCompatibility:
    """Phase 9 compatibility constraint: shim mappings must keep working.

    The forward (UNTP → CIRPASS) and reverse (CIRPASS → UNTP) shims
    rely on the wider 20-value PartyRoleEnum surface. Tightening the
    enum to 6 values would degrade the CIRPASS round-trip's
    information fidelity. PRT001 surfaces the gap without modifying
    the shim's mapping tables.
    """

    def test_reverse_shim_emits_wider_values_unchanged(self) -> None:
        from dppvalidator.compat.cirpass_1_3_to_untp_0_7 import _EUDPP_TO_UNTP_ROLE

        targets = set(_EUDPP_TO_UNTP_ROLE.values())
        # Confirm the 8 documented schema-rejected values still in the table.
        wider_targets = targets - SCHEMA_STRICT_ROLES
        # Subset check: the rich-extension 8 must remain present.
        expected_wider = {
            "importer",
            "distributor",
            "retailer",
            "logisticsProvider",
            "operator",
            "regulator",
            "serviceProvider",
            "certifier",
        }
        assert expected_wider.issubset(wider_targets), (
            "reverse shim mapping table degraded — wider rich-extension targets are missing"
        )
