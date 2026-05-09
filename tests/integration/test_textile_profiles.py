"""Phase 7 task 7.2 — textile-profile dispatch integration test.

Asserts that:

- ``--profile textile-v1`` routes to the legacy textile rule pack
  (TXT001…TXT005, info / warning).
- ``--profile textile-v2`` routes to the MVP Textile DPP v2 pack
  (TXT001…TXT007 with stricter severity).
- A v1 textile fixture passes under ``textile-v1`` (Phase 7 exit
  criterion §2: "Textile v1 fixtures still pass under
  --profile textile-v1").
- The two profiles produce different rule-set lengths and
  different severity ladders for the same rule IDs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.cli.main import EXIT_VALID, main
from dppvalidator.validators import ValidationEngine
from dppvalidator.validators.rules import DEFAULT_TEXTILE_PROFILE, TEXTILE_PROFILES

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


# =============================================================================
# Profile registry / dispatch sanity
# =============================================================================


def test_textile_profiles_registry_has_both_profiles() -> None:
    assert "textile-v1" in TEXTILE_PROFILES
    assert "textile-v2" in TEXTILE_PROFILES


def test_textile_profile_v1_has_five_rules() -> None:
    """v1 has the legacy 5 rules (TXT001…TXT005)."""
    rules = TEXTILE_PROFILES["textile-v1"]
    assert len(rules) == 5
    ids = sorted(r.rule_id for r in rules)
    assert ids == ["TXT001", "TXT002", "TXT003", "TXT004", "TXT005"]


def test_textile_profile_v2_has_seven_rules() -> None:
    """v2 has 7 rules (TXT001…TXT007), TXT006/TXT007 new in v2."""
    rules = TEXTILE_PROFILES["textile-v2"]
    assert len(rules) == 7
    ids = sorted(r.rule_id for r in rules)
    assert ids == [
        "TXT001",
        "TXT002",
        "TXT003",
        "TXT004",
        "TXT005",
        "TXT006",
        "TXT007",
    ]


def test_textile_profile_v2_promotes_severity() -> None:
    """v2 promotes TXT003/TXT004/TXT005 from info → error."""
    by_id_v1 = {r.rule_id: r for r in TEXTILE_PROFILES["textile-v1"]}
    by_id_v2 = {r.rule_id: r for r in TEXTILE_PROFILES["textile-v2"]}
    # TXT003: info → error
    assert by_id_v1["TXT003"].severity == "info"
    assert by_id_v2["TXT003"].severity == "error"
    # TXT004: info → error
    assert by_id_v1["TXT004"].severity == "info"
    assert by_id_v2["TXT004"].severity == "error"
    # TXT005: info → error
    assert by_id_v1["TXT005"].severity == "info"
    assert by_id_v2["TXT005"].severity == "error"


def test_default_textile_profile_is_v1() -> None:
    """Pre-Phase-7 callers default to textile-v1 (back-compat)."""
    assert DEFAULT_TEXTILE_PROFILE == "textile-v1"


# =============================================================================
# Engine: profile threading
# =============================================================================


def test_engine_no_profile_excludes_textile_rules() -> None:
    """Without ``--profile``, no textile rules run on a v0.7 engine.

    Pre-Phase-7 callers got textile rules baked into the v0.7
    rule list; Phase 7 moved them behind explicit profile dispatch
    so non-textile DPPs don't see textile-specific TXT diagnostics.
    """
    engine = ValidationEngine(schema_version="0.7.0", load_plugins=False)
    rules = engine._semantic_validator.rules  # noqa: SLF001 — internal test
    rule_ids = {getattr(r, "rule_id", "") for r in rules}
    txt_rules = {c for c in rule_ids if c.startswith("TXT")}
    assert not txt_rules, (
        f"v0.7 default rule set should not include textile rules; found: {sorted(txt_rules)}"
    )


def test_engine_textile_v2_profile_swaps_in_v2_rules() -> None:
    """Setting profile=textile-v2 swaps the v1 rules out for v2."""
    engine = ValidationEngine(schema_version="0.7.0", load_plugins=False, profile="textile-v2")
    rules = engine._semantic_validator.rules  # noqa: SLF001
    rule_ids = sorted(
        {getattr(r, "rule_id", "") for r in rules if getattr(r, "rule_id", "").startswith("TXT")}
    )
    # v2 has TXT006 / TXT007 which v1 lacks — strong signal that
    # the v2 pack is loaded.
    assert "TXT006" in rule_ids
    assert "TXT007" in rule_ids
    # Severity check: TXT003 in v2 is error.
    by_id = {r.rule_id: r for r in rules if getattr(r, "rule_id", "").startswith("TXT")}
    assert by_id["TXT003"].severity == "error"


def test_engine_textile_v1_profile_keeps_v1_rules() -> None:
    """Explicit profile=textile-v1 leaves the v1 set in place."""
    engine = ValidationEngine(schema_version="0.7.0", load_plugins=False, profile="textile-v1")
    rules = engine._semantic_validator.rules  # noqa: SLF001
    rule_ids = {getattr(r, "rule_id", "") for r in rules}
    # No v2-only rules.
    assert "TXT006" not in rule_ids
    assert "TXT007" not in rule_ids
    # TXT003 stays info.
    by_id = {r.rule_id: r for r in rules if getattr(r, "rule_id", "").startswith("TXT")}
    assert by_id["TXT003"].severity == "info"


# =============================================================================
# CLI: --profile flag
# =============================================================================


def test_cli_profile_flag_is_accepted(capsys: pytest.CaptureFixture) -> None:
    """``validate --profile textile-v2`` accepts the flag without error."""
    fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    if not fixture.exists():
        pytest.skip("no v0.7 fixture available")
    code = main(
        [
            "validate",
            str(fixture),
            "--profile",
            "textile-v2",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    # The fixture isn't necessarily a textile DPP, but the
    # profile-flag plumbing must accept the value without crashing.
    assert code in {EXIT_VALID, 1}, f"Unexpected exit code {code}; stdout={captured.out!r}"


def test_cli_profile_help_lists_both_profiles(capsys: pytest.CaptureFixture) -> None:
    """``validate --help`` shows the profile choices."""
    with pytest.raises(SystemExit):
        main(["validate", "--help"])
    captured = capsys.readouterr()
    assert "textile-v1" in captured.out
    assert "textile-v2" in captured.out


# =============================================================================
# Phase 7 exit criterion §2: v1 fixture under textile-v1 still passes
# =============================================================================


def test_phase7_textile_v1_back_compat_invariant(capsys: pytest.CaptureFixture) -> None:
    """v0.7 textile-shaped fixture under --profile textile-v1 must produce
    the same exit code as without the flag (back-compat)."""
    fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    if not fixture.exists():
        pytest.skip("no v0.7 fixture available")
    code_no_profile = main(["validate", str(fixture)])
    capsys.readouterr()  # drain
    code_v1_profile = main(["validate", str(fixture), "--profile", "textile-v1"])
    capsys.readouterr()
    assert code_no_profile == code_v1_profile, (
        f"--profile textile-v1 should be back-compat with no-profile baseline; "
        f"got {code_no_profile} vs {code_v1_profile}"
    )


def test_phase7_textile_v2_textile_payload_emits_v2_codes() -> None:
    """A textile DPP run under textile-v2 emits at least one TXT-coded
    diagnostic (the v2 rules fire on the textile category).

    This is a coarse signal that the v2 pack is wired correctly;
    the per-rule details are pinned in dedicated unit tests.
    """
    # Build a minimal-but-textile UNTP 0.7 envelope inline.
    payload: dict[str, object] = json.loads(_minimal_textile_v07_payload())
    engine = ValidationEngine(schema_version="auto", load_plugins=False, profile="textile-v2")
    result = engine.validate(payload)
    # Diagnostics fired under v2 — at least the new v2 rules
    # (TXT006 recycled-content disclosure, TXT007 repair-info)
    # should fire because the minimal payload doesn't carry them.
    diagnostic_codes = {
        e.code for e in (*result.errors, *result.warnings, *result.info) if e.code.startswith("TXT")
    }
    assert "TXT006" in diagnostic_codes or "TXT007" in diagnostic_codes, (
        f"Expected v2-only TXT006/TXT007 to fire on a minimal textile "
        f"payload; got TXT codes: {diagnostic_codes}"
    )


def _minimal_textile_v07_payload() -> str:
    """Inline textile DPP payload — minimal v0.7 envelope + HS chapter 61."""
    return json.dumps(
        {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://vocabulary.uncefact.org/untp/0.7.0/context/",
            ],
            "type": ["DigitalProductPassport", "VerifiableCredential"],
            "id": "https://example.com/dpp/textile",
            "name": "Test Textile DPP",
            "issuer": {
                "id": "did:web:example.com",
                "name": "Example",
                "type": ["CredentialIssuer"],
            },
            "validFrom": "2026-01-01T00:00:00+00:00",
            "credentialSubject": {
                "type": ["Product"],
                "id": "01234567890128",
                "name": "Cotton T-shirt",
                "idScheme": {"id": "https://gs1.org/voc/", "name": "GS1 GTIN"},
                "idGranularity": "model",
                "productCategory": [
                    {
                        "schemeId": "https://www.wcoomd.org/",
                        "schemeName": "WCO HS",
                        "code": "61091000",
                        "name": "T-shirts of cotton",
                    }
                ],
                "producedAtFacility": {
                    "id": "https://example.com/f",
                    "name": "F",
                    "type": ["Facility"],
                },
                "countryOfProduction": {"countryCode": "DE"},
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
            },
        }
    )
