"""Phase 5 — every MAP00X code has a reproducible fixture.

Per the Phase 5 exit criteria of [docs/plans/CIRPASS_2_MIGRATION.md]:

> All MAP00X codes have a reproducible fixture.

This file is the registry of fixtures, one per code. Each fixture
is a self-contained payload + assertion about which warning code
the shim emits. The fixtures double as smoke tests for the
:class:`MappingWarning` factory methods.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dppvalidator.compat import (
    MAP_CODE_LOSSY,
    MAP_CODE_REQUIRED_FIELD_MISSING,
    MAP_CODE_SYNTHESISED,
    MAP_CODE_TEMPORAL_COLLAPSE,
    MAP_CODE_UNMAPPED,
    MAP_CODES,
    MappingSeverity,
    MappingWarning,
    to_cirpass_1_3,
    to_untp_0_7,
)
from dppvalidator.compat._untp_cirpass_map import (
    MAPPING_STEPS,
    all_codes_in_use,
    codes_for_step,
    lossless_step_ids,
    step,
)

# =============================================================================
# Code constants
# =============================================================================


def test_map_codes_tuple_lists_every_constant() -> None:
    assert set(MAP_CODES) == {
        MAP_CODE_LOSSY,
        MAP_CODE_SYNTHESISED,
        MAP_CODE_UNMAPPED,
        MAP_CODE_REQUIRED_FIELD_MISSING,
        MAP_CODE_TEMPORAL_COLLAPSE,
    }


def test_map_codes_are_canonically_ordered() -> None:
    """``MAP_CODES`` is sorted ascending so tests can pin against it."""
    assert sorted(MAP_CODES) == list(MAP_CODES)


def test_map_codes_have_canonical_values() -> None:
    assert MAP_CODE_LOSSY == "MAP001"
    assert MAP_CODE_SYNTHESISED == "MAP002"
    assert MAP_CODE_UNMAPPED == "MAP003"
    assert MAP_CODE_REQUIRED_FIELD_MISSING == "MAP004"
    assert MAP_CODE_TEMPORAL_COLLAPSE == "MAP005"


# =============================================================================
# Factory methods
# =============================================================================


@pytest.mark.parametrize(
    "factory_name,expected_code,expected_severity",
    [
        ("lossy", MAP_CODE_LOSSY, MappingSeverity.WARNING),
        ("synthesised", MAP_CODE_SYNTHESISED, MappingSeverity.WARNING),
        ("unmapped", MAP_CODE_UNMAPPED, MappingSeverity.INFO),
        ("required_missing", MAP_CODE_REQUIRED_FIELD_MISSING, MappingSeverity.ERROR),
        ("temporal_collapse", MAP_CODE_TEMPORAL_COLLAPSE, MappingSeverity.WARNING),
    ],
)
def test_factory_emits_correct_code_and_severity(
    factory_name: str, expected_code: str, expected_severity: MappingSeverity
) -> None:
    factory = getattr(MappingWarning, factory_name)
    warning = factory(path="$.x", message="test", step="MXX")
    assert warning.code == expected_code
    assert warning.severity is expected_severity
    # ``details`` is sorted by key for deterministic comparison.
    assert warning.details == (("step", "MXX"),)


def test_warning_details_are_immutable() -> None:
    """``details`` is a tuple so the warning is hashable / frozen."""
    w = MappingWarning.lossy(path="$", message="m", a="1", b="2")
    assert w.details == (("a", "1"), ("b", "2"))
    # Frozen dataclass — assignment raises.
    with pytest.raises(AttributeError):
        w.code = "MAP999"  # type: ignore[misc]


# =============================================================================
# Step-table coverage
# =============================================================================


def test_every_step_has_unique_id() -> None:
    ids = [s.step_id for s in MAPPING_STEPS]
    assert len(ids) == len(set(ids))


def test_every_map_code_referenced_by_at_least_one_step() -> None:
    """Phase 5 exit criterion: every MAP code has a reproducible
    fixture — surfaced via the declarative step table."""
    referenced = all_codes_in_use()
    assert set(MAP_CODES) <= referenced, (
        f"MAP codes never referenced by any step: {set(MAP_CODES) - referenced}"
    )


def test_step_lookup_raises_on_unknown_id() -> None:
    with pytest.raises(KeyError):
        step("M999")


def test_codes_for_step_exposes_declared_codes() -> None:
    assert MAP_CODE_LOSSY in codes_for_step("M01") or codes_for_step("M01")
    # M01 declares MAP002 + MAP004 per the step table.
    assert set(codes_for_step("M01")) == {
        MAP_CODE_SYNTHESISED,
        MAP_CODE_REQUIRED_FIELD_MISSING,
    }


def test_lossless_step_ids_are_subset_of_all_steps() -> None:
    lossless = set(lossless_step_ids())
    all_ids = {s.step_id for s in MAPPING_STEPS}
    assert lossless <= all_ids
    # M01 / M02 / M03 / M07 / M08 are the lossless cornerstone.
    assert {"M01", "M02", "M03", "M07", "M08"} <= lossless


# =============================================================================
# Reproducible per-code fixtures
# =============================================================================
#
# Each test below is a *minimal* payload that triggers exactly one
# of the five MAP codes. The fixture pattern is: build a payload
# that violates one specific contract; run a shim; assert the code
# fires.


def _untp_minimal() -> dict:
    return {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/dpp/min",
        "name": "Minimal",
        "issuer": {"id": "did:web:x", "name": "X", "type": ["CredentialIssuer"]},
        "validFrom": "2026-01-01T00:00:00+00:00",
        "credentialSubject": {
            "type": ["Product"],
            "id": "01234567890128",
            "name": "Min Product",
            "idScheme": {"id": "https://gs1.org/voc/", "name": "GS1 GTIN"},
            "idGranularity": "model",
            "productCategory": [
                {
                    "schemeId": "https://www.wcoomd.org/",
                    "schemeName": "WCO HS",
                    "code": "61091000",
                    "name": "T-shirts",
                }
            ],
            "producedAtFacility": {
                "id": "https://example.com/f/1",
                "name": "F",
                "type": ["Facility"],
            },
            "countryOfProduction": {"countryCode": "DE"},
            "materialProvenance": [],
        },
    }


def _cirpass_minimal() -> dict:
    return {
        "dppIdentifier": {
            "value": "https://example.com/dpp/min",
            "scheme": "https://example.com/dpp-register/",
        },
        "product": {
            "productIdentifier": {
                "value": "01234567890128",
                "scheme": "https://gs1.org/voc/",
            },
            "productName": [{"value": "Min", "language": "en"}],
        },
        "issuedAt": {"timestamp": "2026-01-01T00:00:00+00:00"},
    }


# -----------------------------------------------------------------------------
# MAP001 — Lossy
# -----------------------------------------------------------------------------


def test_map001_fires_on_multilingual_drop() -> None:
    """CIRPASS productName with two languages → UNTP scalar drops one."""
    cirpass = _cirpass_minimal()
    cirpass["product"]["productName"] = [
        {"value": "Hose", "language": "de"},
        {"value": "Trousers", "language": "en"},
    ]
    untp, warns = to_untp_0_7(cirpass, default_language="en")
    lossy = [w for w in warns if w.code == MAP_CODE_LOSSY]
    assert lossy, "expected at least one MAP001 for multilingual drop"
    # The drop should reference the German entry.
    assert any("de" in w.message or "de" in dict(w.details).values() for w in lossy)


def test_map001_fires_on_substances_dropped() -> None:
    """CIRPASS substancesOfConcern has no UNTP equivalent → MAP001."""
    cirpass = _cirpass_minimal()
    cirpass["substancesOfConcern"] = [
        {
            "nameIUPAC": "Bisphenol A",
            "concentrations": [{"value": "0.0008", "unit": "mass_fraction"}],
        }
    ]
    _, warns = to_untp_0_7(cirpass)
    assert any(w.code == MAP_CODE_LOSSY for w in warns)


# -----------------------------------------------------------------------------
# MAP002 — Synthesised
# -----------------------------------------------------------------------------


def test_map002_fires_when_default_scheme_synthesised() -> None:
    """UNTP credentialSubject with empty idScheme → forward synthesises GS1."""
    untp = _untp_minimal()
    # Bypass UNTP idScheme by removing it (model would reject; we test
    # the shim's defensive synthesis path).
    untp["credentialSubject"]["idScheme"] = {}
    _, warns = to_cirpass_1_3(untp)
    assert any(w.code == MAP_CODE_SYNTHESISED for w in warns)


def test_map002_fires_when_language_synthesised() -> None:
    """Forward synthesises BCP-47 tag for product name."""
    untp = _untp_minimal()
    _, warns = to_cirpass_1_3(untp, default_language="de")
    synth = [w for w in warns if w.code == MAP_CODE_SYNTHESISED]
    assert any("language" in w.message for w in synth)


# -----------------------------------------------------------------------------
# MAP003 — Unmapped
# -----------------------------------------------------------------------------


def test_map003_fires_on_unknown_scheme_uri() -> None:
    """Forward shim with an unknown UNTP idScheme.id → MAP003."""
    untp = _untp_minimal()
    untp["credentialSubject"]["idScheme"] = {
        "id": "https://example.com/custom-register/",
        "name": "Custom Register",
    }
    _, warns = to_cirpass_1_3(untp)
    unmapped = [w for w in warns if w.code == MAP_CODE_UNMAPPED]
    assert unmapped, f"expected MAP003 for unknown scheme; got {[w.code for w in warns]}"


# -----------------------------------------------------------------------------
# MAP004 — Required-field-missing
# -----------------------------------------------------------------------------


def test_map004_fires_when_dpp_id_missing() -> None:
    """UNTP envelope with no ``id`` → CIRPASS dppIdentifier required missing."""
    untp = _untp_minimal()
    untp["id"] = ""
    _, warns = to_cirpass_1_3(untp)
    missing = [w for w in warns if w.code == MAP_CODE_REQUIRED_FIELD_MISSING]
    assert missing
    assert all(w.severity is MappingSeverity.ERROR for w in missing)


def test_map004_fires_when_credential_subject_missing() -> None:
    untp = _untp_minimal()
    untp["credentialSubject"] = None  # type: ignore[assignment]
    _, warns = to_cirpass_1_3(untp)
    assert any(w.code == MAP_CODE_REQUIRED_FIELD_MISSING for w in warns)


# -----------------------------------------------------------------------------
# MAP005 — Temporal collapse
# -----------------------------------------------------------------------------


def test_map005_fires_when_valid_until_absent() -> None:
    """Forward shim with no validUntil → effectivePeriod.end empty + MAP005."""
    untp = _untp_minimal()
    untp.pop("validUntil", None)
    cirpass, warns = to_cirpass_1_3(untp)
    collapse = [w for w in warns if w.code == MAP_CODE_TEMPORAL_COLLAPSE]
    assert collapse
    # The output ``effectivePeriod`` has no ``end`` key.
    assert "end" not in cirpass["effectivePeriod"]


# -----------------------------------------------------------------------------
# Sanity: each MAP_CODE has at least one fixture above
# -----------------------------------------------------------------------------


def test_every_code_fired_in_suite() -> None:
    """Run every fixture-emitting test path and assert the union covers MAP_CODES."""
    seen: set[str] = set()

    # MAP001 — multilingual drop
    cirpass = _cirpass_minimal()
    cirpass["product"]["productName"] = [
        {"value": "Hose", "language": "de"},
        {"value": "Trousers", "language": "en"},
    ]
    seen.update(w.code for w in to_untp_0_7(cirpass)[1])

    # MAP002
    untp = _untp_minimal()
    untp["credentialSubject"]["idScheme"] = {}
    seen.update(w.code for w in to_cirpass_1_3(untp)[1])

    # MAP003
    untp["credentialSubject"]["idScheme"] = {
        "id": "https://example.com/custom-register/",
        "name": "Custom",
    }
    seen.update(w.code for w in to_cirpass_1_3(untp)[1])

    # MAP004
    untp_bad = _untp_minimal()
    untp_bad["id"] = ""
    seen.update(w.code for w in to_cirpass_1_3(untp_bad)[1])

    # MAP005
    untp2 = _untp_minimal()
    untp2.pop("validUntil", None)
    seen.update(w.code for w in to_cirpass_1_3(untp2)[1])

    assert set(MAP_CODES) <= seen


def test_warning_message_includes_action() -> None:
    """Every warning carries an actionable message — non-empty + ≥ 10 chars."""
    untp = _untp_minimal()
    _, warns = to_cirpass_1_3(untp)
    for w in warns:
        assert isinstance(w.message, str)
        assert len(w.message) >= 10, f"Warning message too short: {w.message!r}"


def test_isoformat_synthesis_in_required_missing_path() -> None:
    """The ``MAP004`` fallback for missing validFrom emits a placeholder
    timestamp that's a parseable ISO 8601 string."""
    untp = _untp_minimal()
    untp.pop("validFrom", None)
    cirpass, _ = to_cirpass_1_3(untp)
    placeholder = cirpass["issuedAt"]["timestamp"]
    # Parseable as ISO 8601.
    parsed = datetime.fromisoformat(placeholder.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None or "+" in placeholder
    # The placeholder is the Unix epoch — clearly identifiable as
    # synthetic (calls to dppvalidator's MDL-layer timestamp validator
    # will accept it but downstream consumers can detect it).
    assert parsed.year == 1970


def test_warnings_carry_step_id_in_details() -> None:
    """Warnings emitted by the shim carry their originating step ID."""
    untp = _untp_minimal()
    _, warns = to_cirpass_1_3(untp)
    # At least the M-prefixed step IDs should appear.
    step_ids = {dict(w.details).get("step") for w in warns if w.details}
    assert any(s and s.startswith("M") for s in step_ids), step_ids


def test_synthesised_dpp_register_emits_map002() -> None:
    """The forward shim's synthesised dppIdentifier.scheme always emits MAP002."""
    untp = _untp_minimal()
    _, warns = to_cirpass_1_3(untp)
    synthesised = [w for w in warns if w.code == MAP_CODE_SYNTHESISED]
    paths = [w.path for w in synthesised]
    assert "$.dppIdentifier.scheme" in paths


def test_repeatable_warning_order() -> None:
    """Two consecutive runs against the same input produce identical warnings."""
    untp = _untp_minimal()
    _, w1 = to_cirpass_1_3(untp)
    _, w2 = to_cirpass_1_3(untp)
    assert [w.code for w in w1] == [w.code for w in w2]
    assert [w.path for w in w1] == [w.path for w in w2]


def test_today_in_fixture_isoformat() -> None:
    """Smoke: any 'now()' synthesis is properly tz-aware."""
    # The shim does NOT call now() — that would make output non-
    # deterministic. This test pins that contract: on missing validFrom,
    # the shim emits a placeholder, not now().
    untp = _untp_minimal()
    untp.pop("validFrom", None)
    cirpass1, _ = to_cirpass_1_3(untp)
    cirpass2, _ = to_cirpass_1_3(untp)
    assert cirpass1["issuedAt"]["timestamp"] == cirpass2["issuedAt"]["timestamp"]
    assert cirpass1["issuedAt"]["timestamp"] != datetime.now(timezone.utc).isoformat()
