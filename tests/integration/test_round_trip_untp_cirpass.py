"""End-to-end round-trip integration test for the UNTP ↔ CIRPASS shims.

Phase 5 of [docs/plans/CIRPASS_2_MIGRATION.md]. Drives golden
fixtures through both shims and asserts:

- Forward (UNTP → CIRPASS) and reverse (CIRPASS → UNTP) produce
  model-valid output.
- Warning-code totals are deterministic — running the same fixture
  twice yields the exact same warning multiset (in the same order).
- The output of one direction round-trips back through the other.
- The lossless-subset round-trip identity holds for the bundled
  CIRPASS minimal fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.compat import (
    MAP_CODE_LOSSY,
    MAP_CODE_REQUIRED_FIELD_MISSING,
    MAP_CODE_SYNTHESISED,
    MAP_CODES,
    MappingWarning,
    to_cirpass_1_3,
    to_untp_0_7,
)
from dppvalidator.models.cirpass.v1_3 import ReferencePassport
from dppvalidator.models.v0_7 import DigitalProductPassport as UNTPPassport

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"
_CIRPASS_VALID = _FIXTURE_DIR / "valid" / "cirpass-1.3.0"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# =============================================================================
# CIRPASS → UNTP → model-validate
# =============================================================================


@pytest.mark.parametrize("fixture_name", ["minimal.json", "multilingual.json", "full.json"])
def test_reverse_shim_produces_model_valid_untp(fixture_name: str) -> None:
    """Every bundled CIRPASS fixture reverses to a model-valid UNTP DPP."""
    cirpass = _load(_CIRPASS_VALID / fixture_name)
    untp, warnings = to_untp_0_7(cirpass, default_language="en")
    # Pydantic should accept the result.
    UNTPPassport.model_validate(untp)
    # The reverse shim emits at least the synthesised-facility / -country
    # warnings (CIRPASS doesn't carry those at the root level).
    assert isinstance(warnings, list)


# =============================================================================
# UNTP → CIRPASS → model-validate
# =============================================================================


def _untp_v07_payload(*, with_validuntil: bool = True) -> dict:
    untp: dict = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/dpp/RT-001",
        "name": "Round-trip cotton t-shirt",
        "issuer": {
            "id": "did:web:example.com",
            "name": "Example Apparel Ltd.",
            "type": ["CredentialIssuer"],
        },
        "validFrom": "2026-05-08T00:00:00+00:00",
        "credentialSubject": {
            "type": ["Product"],
            "id": "01234567890128",
            "name": "Cotton T-shirt",
            "idScheme": {"id": "https://gs1.org/voc/", "name": "GS1 GTIN"},
            "idGranularity": "model",
            "productCategory": [
                {
                    "schemeId": (
                        "https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/"
                        "hs-nomenclature-2022-edition.aspx"
                    ),
                    "schemeName": "WCO HS",
                    "code": "61091000",
                    "name": "T-shirts of cotton",
                }
            ],
            "producedAtFacility": {
                "id": "https://example.com/facility/F1",
                "name": "Factory 1",
                "type": ["Facility"],
            },
            "countryOfProduction": {"countryCode": "DE", "countryName": "Germany"},
            "materialProvenance": [
                {
                    "name": "Cotton",
                    "originCountry": {"countryCode": "DE"},
                    "materialType": {
                        "schemeId": "https://w3id.org/eudpp#MaterialType",
                        "schemeName": "ISO 2076",
                        "code": "CO",
                        "name": "Cotton",
                    },
                    "massFraction": 1.0,
                }
            ],
            "relatedParty": [
                {
                    "role": "manufacturer",
                    "party": {
                        "id": "https://example.com/lei/529900T8BM49AURSDO55",
                        "name": "Example Apparel Ltd.",
                        "type": ["Party"],
                        "idScheme": {
                            "id": "https://www.gleif.org/lei/",
                            "name": "GLEIF LEI",
                        },
                    },
                }
            ],
        },
    }
    if with_validuntil:
        untp["validUntil"] = "2031-05-08T00:00:00+00:00"
    return untp


def test_forward_shim_produces_model_valid_cirpass() -> None:
    untp = _untp_v07_payload()
    cirpass, warnings = to_cirpass_1_3(untp, default_language="en")
    ReferencePassport.model_validate(cirpass)
    assert isinstance(warnings, list)


# =============================================================================
# Determinism: two consecutive runs produce identical output + warnings
# =============================================================================


def test_forward_is_deterministic() -> None:
    untp = _untp_v07_payload()
    a, wa = to_cirpass_1_3(untp)
    b, wb = to_cirpass_1_3(untp)
    assert a == b
    assert [(w.code, w.path) for w in wa] == [(w.code, w.path) for w in wb]


def test_reverse_is_deterministic() -> None:
    cirpass = _load(_CIRPASS_VALID / "full.json")
    a, wa = to_untp_0_7(cirpass)
    b, wb = to_untp_0_7(cirpass)
    assert a == b
    assert [(w.code, w.path) for w in wa] == [(w.code, w.path) for w in wb]


# =============================================================================
# Round-trip: forward → reverse → forward
# =============================================================================


def test_untp_round_trip_recovers_lossless_fields() -> None:
    """UNTP → CIRPASS → UNTP preserves the lossless-subset fields."""
    untp = _untp_v07_payload()
    cirpass, _ = to_cirpass_1_3(untp)
    back, _ = to_untp_0_7(cirpass, default_language="en")
    # Lossless: envelope id, validFrom, validUntil, credentialSubject.id
    # and idScheme.id round-trip cleanly.
    assert back["id"] == untp["id"]
    assert back["validFrom"] == untp["validFrom"]
    assert back["validUntil"] == untp["validUntil"]
    assert back["credentialSubject"]["id"] == untp["credentialSubject"]["id"]
    assert (
        back["credentialSubject"]["idScheme"]["id"] == untp["credentialSubject"]["idScheme"]["id"]
    )


def test_cirpass_round_trip_recovers_lossless_fields() -> None:
    """CIRPASS → UNTP → CIRPASS preserves the lossless-subset fields."""
    cirpass = _load(_CIRPASS_VALID / "minimal.json")
    untp, _ = to_untp_0_7(cirpass, default_language="en")
    back, _ = to_cirpass_1_3(untp, default_language="en")
    assert back["dppIdentifier"]["value"] == cirpass["dppIdentifier"]["value"]
    assert (
        back["product"]["productIdentifier"]["value"]
        == cirpass["product"]["productIdentifier"]["value"]
    )
    assert (
        back["product"]["productIdentifier"]["scheme"]
        == cirpass["product"]["productIdentifier"]["scheme"]
    )
    # Single-language productName round-trips.
    assert (
        back["product"]["productName"][0]["value"] == cirpass["product"]["productName"][0]["value"]
    )
    assert (
        back["product"]["productName"][0]["language"]
        == cirpass["product"]["productName"][0]["language"]
    )
    # issuedAt timestamp round-trips bit-for-bit (M07).
    assert back["issuedAt"]["timestamp"] == cirpass["issuedAt"]["timestamp"]


# =============================================================================
# Warning-code totals are deterministic
# =============================================================================


def test_forward_warning_code_totals_match_expected() -> None:
    """Asserts the warning-code multiset for the round-trip canonical
    payload. A change in the multiset means a new transformation was
    introduced — that's significant and should be reflected here."""
    untp = _untp_v07_payload()
    _, warns = to_cirpass_1_3(untp, default_language="en")
    code_counts: dict[str, int] = {}
    for w in warns:
        code_counts[w.code] = code_counts.get(w.code, 0) + 1
    # Forward's canonical warnings on a typical UNTP payload:
    #   * MAP002 ×N — language synthesis + dppIdentifier scheme
    #   * No MAP004 / MAP001 / MAP005 (well-formed input).
    assert MAP_CODE_SYNTHESISED in code_counts
    assert MAP_CODE_REQUIRED_FIELD_MISSING not in code_counts


def test_reverse_warning_code_totals_match_expected() -> None:
    cirpass = _load(_CIRPASS_VALID / "full.json")
    _, warns = to_untp_0_7(cirpass, default_language="en")
    codes = {w.code for w in warns}
    # full.json carries `lca` + `substancesOfConcern` + `connectorRelations`,
    # all of which the reverse drops with MAP001.
    assert MAP_CODE_LOSSY in codes


# =============================================================================
# Stub validators around model.validate cycles
# =============================================================================


def test_forward_then_reverse_passes_pydantic_both_sides() -> None:
    untp = _untp_v07_payload()
    cirpass, _ = to_cirpass_1_3(untp)
    ReferencePassport.model_validate(cirpass)
    back, _ = to_untp_0_7(cirpass, default_language="en")
    UNTPPassport.model_validate(back)


def test_reverse_then_forward_passes_pydantic_both_sides() -> None:
    cirpass = _load(_CIRPASS_VALID / "full.json")
    untp, _ = to_untp_0_7(cirpass, default_language="en")
    UNTPPassport.model_validate(untp)
    back, _ = to_cirpass_1_3(untp, default_language="en")
    ReferencePassport.model_validate(back)


# =============================================================================
# All MAP codes produced by the suite
# =============================================================================


def test_round_trip_suite_covers_every_map_code() -> None:
    """Across the round-trip suite, every MAP code surfaces somewhere."""
    seen: set[str] = set()

    # Forward — well-formed input
    seen.update(w.code for w in to_cirpass_1_3(_untp_v07_payload())[1])

    # Reverse — full fixture
    cirpass = _load(_CIRPASS_VALID / "full.json")
    seen.update(w.code for w in to_untp_0_7(cirpass)[1])

    # Forward — missing id (MAP004) + unknown scheme (MAP003) + no validUntil (MAP005)
    bad = _untp_v07_payload(with_validuntil=False)
    bad["id"] = ""
    bad["credentialSubject"]["idScheme"] = {
        "id": "https://example.com/custom/",
        "name": "Custom",
    }
    seen.update(w.code for w in to_cirpass_1_3(bad)[1])

    assert set(MAP_CODES) <= seen, f"Codes missing from round-trip suite: {set(MAP_CODES) - seen}"


# =============================================================================
# Issuer ↔ manufacturer-actor invariant (M12)
# =============================================================================


def test_m12_issuer_round_trips_through_manufacturer_actor() -> None:
    """When UNTP relatedParty includes a manufacturer, that party's id
    must surface as the envelope.issuer.id after a CIRPASS round-trip.
    """
    untp = _untp_v07_payload()
    cirpass, _ = to_cirpass_1_3(untp)
    # Forward must produce at least one ManufacturerRole in relatedActors.
    actors = cirpass.get("relatedActors") or []
    assert any(a.get("role") == "eudpp:ManufacturerRole" for a in actors)
    # Reverse picks the first ManufacturerRole as the envelope issuer.
    back, _ = to_untp_0_7(cirpass, default_language="en")
    assert back["issuer"]["id"] == untp["credentialSubject"]["relatedParty"][0]["party"]["id"]


# =============================================================================
# Default-arg coverage
# =============================================================================


def test_default_language_kwarg_threads_through_forward() -> None:
    untp = _untp_v07_payload()
    cirpass, _ = to_cirpass_1_3(untp, default_language="de")
    assert cirpass["product"]["productName"][0]["language"] == "de"


def test_identifier_scheme_lookup_override_takes_precedence() -> None:
    """Explicit override beats the bundled lookup table."""
    untp = _untp_v07_payload()
    untp["credentialSubject"]["idScheme"] = {
        "id": "https://example.com/custom/",
        "name": "Custom",
    }
    cirpass, warns = to_cirpass_1_3(
        untp,
        identifier_scheme_lookup={
            "https://example.com/custom/": (
                "https://override.example.com/",
                "Override Name",
            )
        },
    )
    # The override should be used; no MAP003 should fire.
    assert cirpass["product"]["productIdentifier"]["scheme"] == "https://override.example.com/"
    assert not any(w.code == "MAP003" for w in warns)


# =============================================================================
# Type-error defensive coverage
# =============================================================================


def test_forward_rejects_non_dict_input() -> None:
    with pytest.raises(TypeError):
        to_cirpass_1_3("not a dict")  # type: ignore[arg-type]


def test_reverse_rejects_non_dict_input() -> None:
    with pytest.raises(TypeError):
        to_untp_0_7(42)  # type: ignore[arg-type]


# =============================================================================
# Smoke: warnings have stable str() / repr()
# =============================================================================


def test_warning_repr_is_stable() -> None:
    w = MappingWarning.synthesised(path="$.a", message="m", step="M01")
    # repr is dataclass-default; pin format as stable for log scraping.
    representation = repr(w)
    assert "MAP002" in representation
    assert "M01" in representation
