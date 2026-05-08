"""Regression tests: VOC003/VOC004 must be scheme-aware.

Both rules check classification codes against textile-pilot
validators (UNECE Rec 46 for materials, HS chapters 50-63 for
products). Before the fix, they fired unconditionally on every
``Classification.code`` regardless of the scheme — producing false
positives for UN CPC, NACE, GS1 GPC, and any other classification.

The fix gates the validator call on the ``schemeId``:

- When ``schemeId`` is set AND matches the rule's scheme: validate.
- When ``schemeId`` is set AND does NOT match: skip silently.
- When ``schemeId`` is missing: fall back to pre-fix best-effort
  behaviour (a length/digit heuristic for VOC004, validate
  unconditionally for VOC003) for back-compat with legacy fixtures.

These tests pin the contract end-to-end through both v0.6 and v0.7
rule implementations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "valid"


# ---------------------------------------------------------------------------
# Real-fixture round-trip — the canonical regression
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture_name",
    [
        "untp-dpp-instance-0.7.0.json",
        "untp-dpp-battery-instance-0.7.0.json",
        "untp-dpp-cathode-instance-0.7.0.json",
    ],
)
def test_v07_un_cpc_fixtures_emit_no_voc003_or_voc004(fixture_name: str) -> None:
    """v0.7 UN CPC fixtures must not trip the textile-pilot rules.

    All three vendored upstream samples use UN CPC scheme IDs
    (``https://unstats.un.org/unsd/classifications/Econ/cpc/``).
    Before the scheme-aware fix, every classification code in these
    fixtures spuriously emitted VOC003 + VOC004 because the rules
    blindly ran textile validators on UN CPC codes. The fix gates
    the validation on the scheme — UN CPC isn't UNECE Rec 46 or HS,
    so the rules skip silently.
    """
    from dppvalidator.validators import ValidationEngine

    fixture_path = _FIXTURES / fixture_name
    if not fixture_path.is_file():
        pytest.skip(f"fixture not vendored: {fixture_name}")

    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    engine = ValidationEngine(schema_version="0.7.0", layers=["semantic"])
    result = engine.validate(data)

    voc003 = [w for w in result.warnings + result.errors if w.code == "VOC003"]
    voc004 = [w for w in result.warnings + result.errors if w.code == "VOC004"]
    assert voc003 == [], (
        f"{fixture_name} unexpectedly emitted VOC003 (scheme-aware fix regressed):\n"
        + "\n".join(f"  {w.path}: {w.message}" for w in voc003)
    )
    assert voc004 == [], (
        f"{fixture_name} unexpectedly emitted VOC004 (scheme-aware fix regressed):\n"
        + "\n".join(f"  {w.path}: {w.message}" for w in voc004)
    )


def test_v06_un_cpc_fixture_emits_no_voc003_or_voc004() -> None:
    """The vendored v0.6.1 UN CPC fixture is also clean after the fix."""
    from dppvalidator.validators import ValidationEngine

    fixture_path = _FIXTURES / "untp-dpp-instance-0.6.1.json"
    if not fixture_path.is_file():
        pytest.skip("v0.6 fixture not vendored")

    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    engine = ValidationEngine(schema_version="0.6.1", layers=["semantic"])
    result = engine.validate(data)

    voc003 = [w for w in result.warnings + result.errors if w.code == "VOC003"]
    voc004 = [w for w in result.warnings + result.errors if w.code == "VOC004"]
    assert voc003 == []
    assert voc004 == []


# ---------------------------------------------------------------------------
# v0.7 unit-level: rule check() with constructed Material / Classification
# ---------------------------------------------------------------------------


def _build_v07_passport_with(
    materials: list[dict[str, Any]] | None = None, categories: list[dict[str, Any]] | None = None
) -> Any:
    """Construct a minimal v0.7 ``DigitalProductPassport`` for rule tests."""
    from dppvalidator.models.v0_7.envelope import DigitalProductPassport

    payload: dict[str, Any] = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/credentials/test",
        "name": "Test DPP",
        "issuer": {
            "type": ["CredentialIssuer"],
            "id": "did:example:1",
            "name": "Example",
        },
        "validFrom": "2024-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["Product"],
            "id": "https://example.com/products/1",
            "name": "Test product",
            "idScheme": {
                "type": ["IdentifierScheme"],
                "id": "https://example.com/scheme",
                "name": "Internal",
            },
            "idGranularity": "model",
            "productCategory": categories
            or [
                {
                    "type": ["Classification"],
                    "schemeId": "https://example.com/scheme",
                    "schemeName": "Internal",
                    "code": "X",
                    "name": "x",
                }
            ],
            "producedAtFacility": {
                "type": ["Facility"],
                "id": "https://example.com/facilities/1",
                "name": "Facility",
            },
            "countryOfProduction": {"countryCode": "DE", "countryName": "Germany"},
            "materialProvenance": materials or [],
        },
    }
    return DigitalProductPassport.model_validate(payload)


class TestV07MaterialCodeRule:
    """Scheme-gating on the v0.7 ``MaterialCodeRule`` (VOC003)."""

    def _material(self, *, scheme_id: str | None, code: str = "9999") -> dict[str, Any]:
        material_type: dict[str, Any] = {
            "type": ["Classification"],
            "schemeName": "Test",
            "code": code,
            "name": "x",
        }
        if scheme_id is not None:
            material_type["schemeId"] = scheme_id
        return {
            "name": "Test material",
            "originCountry": {"countryCode": "DE", "countryName": "Germany"},
            "materialType": material_type,
            "massFraction": 1.0,
        }

    def test_un_cpc_scheme_skips_validation(self) -> None:
        from dppvalidator.validators.rules.v0_7.base import MaterialCodeRule

        # ``9999`` is not a real UNECE Rec 46 code — but the rule
        # must not fire because the scheme isn't Rec 46.
        passport = _build_v07_passport_with(
            materials=[
                self._material(
                    scheme_id="https://unstats.un.org/unsd/classifications/Econ/cpc/",
                    code="9999",
                ),
            ],
            categories=[
                {
                    "type": ["Classification"],
                    "schemeId": "https://unstats.un.org/unsd/classifications/Econ/cpc/",
                    "schemeName": "UN CPC",
                    "code": "12345",
                    "name": "x",
                },
            ],
        )
        rule = MaterialCodeRule(material_validator=lambda code: code == "0000")
        assert rule.check(passport) == []

    def test_unece_rec46_scheme_fires_on_invalid_code(self) -> None:
        from dppvalidator.validators.rules.v0_7.base import MaterialCodeRule

        passport = _build_v07_passport_with(
            materials=[
                self._material(
                    scheme_id="https://vocabulary.uncefact.org/UNECERec46/",
                    code="9999",
                ),
            ],
            categories=[
                {
                    "type": ["Classification"],
                    "schemeId": "https://vocabulary.uncefact.org/UNECERec46/",
                    "schemeName": "UNECE Rec 46",
                    "code": "12345",
                    "name": "x",
                },
            ],
        )
        # Stub validator: accepts only "0000".
        rule = MaterialCodeRule(material_validator=lambda code: code == "0000")
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "9999" in violations[0][1]


class TestV07HSCodeRule:
    """Scheme-gating on the v0.7 ``HSCodeRule`` (VOC004)."""

    def _category(self, *, scheme_id: str | None, code: str = "12345") -> dict[str, Any]:
        cat: dict[str, Any] = {
            "type": ["Classification"],
            "schemeName": "Test",
            "code": code,
            "name": "x",
        }
        if scheme_id is not None:
            cat["schemeId"] = scheme_id
        return cat

    def test_un_cpc_scheme_skips_validation(self) -> None:
        from dppvalidator.validators.rules.v0_7.base import HSCodeRule

        passport = _build_v07_passport_with(
            categories=[
                self._category(
                    scheme_id="https://unstats.un.org/unsd/classifications/Econ/cpc/",
                    code="9999",  # would trip the textile validator if not gated
                ),
            ],
        )
        rule = HSCodeRule(hs_validator=lambda _code: False)
        assert rule.check(passport) == []

    def test_hs_scheme_fires_on_invalid_code(self) -> None:
        from dppvalidator.validators.rules.v0_7.base import HSCodeRule

        passport = _build_v07_passport_with(
            categories=[
                self._category(
                    scheme_id="https://wcoomd.org/hs-nomenclature/2017",
                    code="9999",
                ),
            ],
        )
        rule = HSCodeRule(hs_validator=lambda _code: False)
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "9999" in violations[0][1]
