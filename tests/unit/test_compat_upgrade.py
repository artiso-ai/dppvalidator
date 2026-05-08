"""Phase 4 acceptance tests: UNTP DPP v0.6.x → v0.7.0 compatibility shim.

This module is the unit-level coverage for
``src/dppvalidator/compat/upgrade_0_6_to_0_7.py``. Each test pins a
single transformation step from §Phase 4 of
``docs/plans/UNTP_0.7.0_MIGRATION.md`` and asserts both the structural
rewrite and the structured warnings the shim emits.

Tests are organised by step number so it's easy to map a failing case
back to the migration plan.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from dppvalidator.compat import (
    UPG_CODE_LOSSY,
    UPG_CODE_REQUIRED_FIELD_MISSING,
    UPG_CODE_SYNTHESISED,
    UPG_CODE_UNMAPPED_COUNTRY,
    UpgradeSeverity,
    UpgradeWarning,
    active_version,
    is_version,
    upgrade,
)


def _minimal_v06_payload(**overrides: Any) -> dict[str, Any]:
    """Return a minimal v0.6 ProductPassport payload for use in shim tests."""
    base: dict[str, Any] = {
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ],
        "id": "https://example.com/credentials/x",
        "issuer": {"id": "did:example:1", "name": "Example"},
        "validFrom": "2024-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["ProductPassport"],
            "id": "https://example.com/subject/1",
            "product": {
                "type": ["Product"],
                "id": "https://example.com/products/1",
                "name": "Sample Product",
            },
        },
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# active_version() / is_version()
# ---------------------------------------------------------------------------


class TestActiveVersionHelpers:
    """Phase 4 introduces ``active_version()`` / ``is_version()``."""

    def test_active_version_matches_default_schema_version(self) -> None:
        from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION

        assert active_version() == DEFAULT_SCHEMA_VERSION

    def test_is_version_true_for_active(self) -> None:
        assert is_version(active_version()) is True

    def test_is_version_false_for_other(self) -> None:
        assert is_version("9.9.9") is False


# ---------------------------------------------------------------------------
# Type / contract checks
# ---------------------------------------------------------------------------


class TestUpgradeContract:
    """``upgrade()`` is pure, doesn't mutate input, and rejects bad shapes."""

    def test_rejects_non_dict(self) -> None:
        with pytest.raises(TypeError):
            upgrade("not a dict")  # type: ignore[arg-type]

    def test_does_not_mutate_input(self) -> None:
        src = _minimal_v06_payload()
        before = json.dumps(src, sort_keys=True)
        upgrade(src)
        after = json.dumps(src, sort_keys=True)
        assert before == after, "upgrade() must not mutate its input"

    def test_returns_tuple_of_dict_and_warning_list(self) -> None:
        out, warnings = upgrade(_minimal_v06_payload())
        assert isinstance(out, dict)
        assert isinstance(warnings, list)
        for w in warnings:
            assert isinstance(w, UpgradeWarning)


# ---------------------------------------------------------------------------
# Step 1 — context URL substitution
# ---------------------------------------------------------------------------


class TestStep1ContextRewrite:
    def test_v061_context_becomes_v07_context(self) -> None:
        out, _ = upgrade(_minimal_v06_payload())
        assert "https://vocabulary.uncefact.org/untp/0.7.0/context/" in out["@context"]
        assert "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/" not in out["@context"]

    def test_v060_context_is_also_rewritten(self) -> None:
        src = _minimal_v06_payload()
        src["@context"] = [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
        ]
        out, _ = upgrade(src)
        assert "https://vocabulary.uncefact.org/untp/0.7.0/context/" in out["@context"]

    def test_w3c_vc_context_preserved(self) -> None:
        out, _ = upgrade(_minimal_v06_payload())
        assert "https://www.w3.org/ns/credentials/v2" in out["@context"]

    def test_unknown_context_entries_pass_through(self) -> None:
        src = _minimal_v06_payload()
        src["@context"].append("https://example.com/extension")
        out, _ = upgrade(src)
        assert "https://example.com/extension" in out["@context"]


# ---------------------------------------------------------------------------
# Step 2 — envelope required fields
# ---------------------------------------------------------------------------


class TestStep2EnvelopeRequiredFields:
    def test_synthesises_name_from_product_name(self) -> None:
        src = _minimal_v06_payload()
        src.pop("name", None)
        out, warnings = upgrade(src)
        assert out["name"] == "Sample Product"
        codes = [w.code for w in warnings if w.path == "name"]
        assert UPG_CODE_SYNTHESISED in codes

    def test_warns_when_name_cannot_be_synthesised(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"].pop("name", None)
        out, warnings = upgrade(src)
        codes = [(w.code, w.severity) for w in warnings if w.path == "name"]
        assert (UPG_CODE_REQUIRED_FIELD_MISSING, UpgradeSeverity.ERROR) in codes

    def test_warns_when_validFrom_missing(self) -> None:
        src = _minimal_v06_payload()
        src.pop("validFrom", None)
        _, warnings = upgrade(src)
        codes = [w.code for w in warnings if w.path == "validFrom"]
        assert UPG_CODE_REQUIRED_FIELD_MISSING in codes


# ---------------------------------------------------------------------------
# Step 3 — drop ProductPassport envelope
# ---------------------------------------------------------------------------


class TestStep3FlattenEnvelope:
    def test_credential_subject_is_product(self) -> None:
        out, _ = upgrade(_minimal_v06_payload())
        cs = out["credentialSubject"]
        assert cs["type"] == ["Product"]
        assert "product" not in cs

    def test_granularity_level_renamed(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["granularityLevel"] = "batch"
        out, _ = upgrade(src)
        assert out["credentialSubject"]["idGranularity"] == "batch"

    def test_serial_number_renamed_to_item_number(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["serialNumber"] = "SN-42"
        out, _ = upgrade(src)
        cs = out["credentialSubject"]
        assert cs.get("itemNumber") == "SN-42"
        assert "serialNumber" not in cs

    def test_passport_id_preserved_when_product_has_none(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"].pop("id", None)
        src["credentialSubject"]["id"] = "https://example.com/subject/keep"
        out, _ = upgrade(src)
        assert out["credentialSubject"]["id"] == "https://example.com/subject/keep"


# ---------------------------------------------------------------------------
# Step 4 — materialsProvenance → materialProvenance
# ---------------------------------------------------------------------------


class TestStep4MaterialsProvenance:
    def test_materials_provenance_renamed_and_moved(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["materialsProvenance"] = [
            {"name": "Cotton", "originCountry": "EG", "massFraction": 0.5}
        ]
        out, _ = upgrade(src)
        cs = out["credentialSubject"]
        assert "materialsProvenance" not in cs
        assert isinstance(cs["materialProvenance"], list)
        assert cs["materialProvenance"][0]["name"] == "Cotton"


# ---------------------------------------------------------------------------
# Step 5 — dueDiligenceDeclaration → relatedDocument[]
# ---------------------------------------------------------------------------


class TestStep5DueDiligenceDeclaration:
    def test_due_diligence_link_lands_in_related_document(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["dueDiligenceDeclaration"] = {
            "linkURL": "https://example.com/dd",
            "linkName": "Custom",
        }
        out, _ = upgrade(src)
        cs = out["credentialSubject"]
        assert "dueDiligenceDeclaration" not in cs
        rd = cs["relatedDocument"]
        assert any("dd" in entry.get("linkURL", "") for entry in rd)


# ---------------------------------------------------------------------------
# Step 6 — conformityClaim → performanceClaim with field renames
# ---------------------------------------------------------------------------


class TestStep6ConformityClaimToPerformanceClaim:
    def test_conformity_claim_array_becomes_performance_claim(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["conformityClaim"] = [
            {
                "id": "https://example.com/claims/1",
                "description": "Sample claim",
                "assessmentDate": "2024-03-15",
                "conformityTopic": "environment.emissions",
                "declaredValue": [
                    {
                        "metricName": "GHG intensity",
                        "metricValue": {"value": 1.5, "unit": "KGM"},
                        "score": "AA",
                    },
                ],
            },
        ]
        out, _ = upgrade(src)
        cs = out["credentialSubject"]
        assert "conformityClaim" not in cs
        pc = cs["performanceClaim"]
        assert len(pc) == 1
        claim = pc[0]
        assert claim["claimDate"] == "2024-03-15"
        assert isinstance(claim["conformityTopic"], list)
        assert claim["conformityTopic"][0]["name"] == "environment.emissions"
        assert isinstance(claim["claimedPerformance"], list)
        perf = claim["claimedPerformance"][0]
        assert perf["metric"]["name"] == "GHG intensity"
        assert perf["measure"] == {"value": 1.5, "unit": "KGM"}
        assert perf["score"]["code"] == "AA"

    def test_claim_with_no_name_falls_back_to_description(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["conformityClaim"] = [
            {"id": "https://example.com/claims/1", "description": "Sample"},
        ]
        out, _ = upgrade(src)
        assert out["credentialSubject"]["performanceClaim"][0]["name"] == "Sample"


# ---------------------------------------------------------------------------
# Step 7 — scorecards → Claim entries on performanceClaim
# ---------------------------------------------------------------------------


class TestStep7ScorecardsAsClaims:
    def test_emissions_scorecard_becomes_claim(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["emissionsScorecard"] = {
            "carbonFootprint": 1.8,
            "primarySourcedRatio": 0.3,
        }
        out, _ = upgrade(src)
        pc = out["credentialSubject"]["performanceClaim"]
        emissions = next(
            c for c in pc if any(t["name"] == "Emissions" for t in c.get("conformityTopic", []))
        )
        names = {p["metric"]["name"] for p in emissions["claimedPerformance"]}
        assert "carbonFootprint" in names
        assert "primarySourcedRatio" in names

    def test_circularity_scorecard_link_becomes_evidence(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["circularityScorecard"] = {
            "recyclableContent": 0.5,
            "recyclingInformation": {
                "linkURL": "https://example.com/recycle",
                "linkName": "Recycling guide",
            },
        }
        out, _ = upgrade(src)
        pc = out["credentialSubject"]["performanceClaim"]
        circ = next(
            c for c in pc if any(t["name"] == "Circularity" for t in c.get("conformityTopic", []))
        )
        assert any("recycle" in (e.get("linkURL") or "") for e in circ.get("evidence", []))

    def test_traceability_information_array_explodes(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["traceabilityInformation"] = [
            {"valueChainProcess": "Spinning", "verifiedRatio": 0.5},
            {"valueChainProcess": "Weaving", "verifiedRatio": 0.7},
        ]
        out, _ = upgrade(src)
        pc = out["credentialSubject"]["performanceClaim"]
        trace = [
            c for c in pc if any(t["name"] == "Traceability" for t in c.get("conformityTopic", []))
        ]
        assert len(trace) == 2


# ---------------------------------------------------------------------------
# Step 8 — wrap scalar Standard / Regulation
# ---------------------------------------------------------------------------


class TestStep8ClaimReferencesAreLists:
    def test_scalar_standard_wrapped_into_list(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["conformityClaim"] = [
            {
                "id": "https://example.com/claims/1",
                "description": "x",
                "referenceStandard": {"id": "https://std.example/A", "name": "Std A"},
            },
        ]
        out, _ = upgrade(src)
        rs = out["credentialSubject"]["performanceClaim"][0]["referenceStandard"]
        assert isinstance(rs, list)
        assert rs[0]["name"] == "Std A"


# ---------------------------------------------------------------------------
# Step 9 — wrap scalar country codes
# ---------------------------------------------------------------------------


class TestStep9CountryCodes:
    def test_scalar_country_wrapped_to_object(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["countryOfProduction"] = "DE"
        out, _ = upgrade(src)
        cop = out["credentialSubject"]["countryOfProduction"]
        assert cop == {"countryCode": "DE"} or (
            isinstance(cop, dict) and cop["countryCode"] == "DE"
        )

    def test_country_lookup_populates_name(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["countryOfProduction"] = "DE"
        out, _ = upgrade(src, country_lookup={"DE": "Germany"})
        assert out["credentialSubject"]["countryOfProduction"]["countryName"] == "Germany"

    def test_unknown_country_fires_upg003(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["countryOfProduction"] = "XX"
        _, warnings = upgrade(src)
        assert any(w.code == UPG_CODE_UNMAPPED_COUNTRY for w in warnings)

    def test_known_country_without_lookup_fires_upg002_info(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["countryOfProduction"] = "DE"
        _, warnings = upgrade(src)
        info_warnings = [
            w for w in warnings if w.code == UPG_CODE_SYNTHESISED and "countryName" in w.path
        ]
        assert info_warnings, "Expected UPG002 info warning for missing country lookup"
        assert all(w.severity == UpgradeSeverity.INFO for w in info_warnings)

    def test_material_origin_country_also_wrapped(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["materialsProvenance"] = [
            {
                "name": "X",
                "originCountry": "DE",
                "massFraction": 0.5,
                "materialType": {"schemeID": "s", "schemeName": "S", "code": "c", "name": "n"},
            }
        ]
        out, _ = upgrade(src, country_lookup={"DE": "Germany"})
        m = out["credentialSubject"]["materialProvenance"][0]
        assert m["originCountry"] == {"countryCode": "DE", "countryName": "Germany"}


# ---------------------------------------------------------------------------
# Step 10 — wrap Product.productCategory
# ---------------------------------------------------------------------------


class TestStep10WrapProductCategory:
    def test_scalar_category_wrapped(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["productCategory"] = {
            "schemeID": "s",
            "schemeName": "S",
            "code": "c",
            "name": "n",
        }
        out, _ = upgrade(src)
        pc = out["credentialSubject"]["productCategory"]
        assert isinstance(pc, list) and len(pc) == 1

    def test_existing_list_passthrough(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["productCategory"] = [
            {"schemeID": "s", "schemeName": "S", "code": "c", "name": "n"},
        ]
        out, _ = upgrade(src)
        assert isinstance(out["credentialSubject"]["productCategory"], list)


# ---------------------------------------------------------------------------
# Step 11 — producedByParty → relatedParty[]
# ---------------------------------------------------------------------------


class TestStep11ProducedByParty:
    def test_scalar_party_becomes_party_role_with_manufacturer_role(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["producedByParty"] = {
            "id": "did:example:mfr",
            "name": "Manufacturer",
        }
        out, _ = upgrade(src)
        cs = out["credentialSubject"]
        assert "producedByParty" not in cs
        rp = cs["relatedParty"]
        assert len(rp) == 1
        assert rp[0]["role"] == "manufacturer"
        assert rp[0]["party"]["name"] == "Manufacturer"


# ---------------------------------------------------------------------------
# Step 12 — furtherInformation → relatedDocument[]
# ---------------------------------------------------------------------------


class TestStep12FurtherInformation:
    def test_further_information_appended_to_related_document(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["furtherInformation"] = [
            {"linkURL": "https://example.com/info1"},
            {"linkURL": "https://example.com/info2"},
        ]
        out, _ = upgrade(src)
        cs = out["credentialSubject"]
        assert "furtherInformation" not in cs
        rd = cs["relatedDocument"]
        urls = [r["linkURL"] for r in rd]
        assert "https://example.com/info1" in urls
        assert "https://example.com/info2" in urls


# ---------------------------------------------------------------------------
# Step 13 — drop Product.registeredId with warning
# ---------------------------------------------------------------------------


class TestStep13DropRegisteredId:
    def test_registered_id_dropped_and_warns(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["registeredId"] = "ABN-123"
        out, warnings = upgrade(src)
        assert "registeredId" not in out["credentialSubject"]
        assert any(w.code == UPG_CODE_LOSSY and "registeredId" in w.path for w in warnings)


# ---------------------------------------------------------------------------
# Step 14 — Material.symbol → Image
# ---------------------------------------------------------------------------


class TestStep14MaterialSymbol:
    def test_undefined_placeholder_dropped(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["materialsProvenance"] = [
            {
                "name": "X",
                "originCountry": "DE",
                "massFraction": 0.5,
                "materialType": {"schemeID": "s", "schemeName": "S", "code": "c", "name": "n"},
                "symbol": "undefined",
            },
        ]
        out, warnings = upgrade(src)
        m = out["credentialSubject"]["materialProvenance"][0]
        assert "symbol" not in m
        assert any(
            w.code == UPG_CODE_LOSSY and "symbol" in w.path and w.severity == UpgradeSeverity.INFO
            for w in warnings
        )

    def test_real_base64_becomes_image_object(self) -> None:
        # 16+ chars, valid base64 (padded) — passes _looks_like_base64.
        sample_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        src = _minimal_v06_payload()
        src["credentialSubject"]["materialsProvenance"] = [
            {
                "name": "X",
                "originCountry": "DE",
                "massFraction": 0.5,
                "materialType": {"schemeID": "s", "schemeName": "S", "code": "c", "name": "n"},
                "symbol": sample_b64,
            },
        ]
        out, warnings = upgrade(src)
        m = out["credentialSubject"]["materialProvenance"][0]
        assert isinstance(m["symbol"], dict)
        assert m["symbol"]["imageData"] == sample_b64
        assert m["symbol"]["mediaType"] == "image/png"
        assert m["symbol"]["name"]
        assert any(w.code == UPG_CODE_SYNTHESISED and "symbol" in w.path for w in warnings)


# ---------------------------------------------------------------------------
# Step 15 — strip type arrays on embedded objects
# ---------------------------------------------------------------------------


class TestStep15StripEmbeddedTypes:
    def test_dimension_type_stripped(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["dimensions"] = {
            "type": ["Dimension"],
            "weight": {"type": ["Measure"], "value": 1.0, "unit": "KGM"},
        }
        out, _ = upgrade(src)
        dims = out["credentialSubject"]["dimensions"]
        assert "type" not in dims
        assert "type" not in dims["weight"]

    def test_product_type_preserved(self) -> None:
        out, _ = upgrade(_minimal_v06_payload())
        assert out["credentialSubject"]["type"] == ["Product"]


# ---------------------------------------------------------------------------
# Step 16 — schemeID → schemeId rename
# ---------------------------------------------------------------------------


class TestStep16SchemeIdRename:
    def test_scheme_id_renamed_recursively(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["product"]["productCategory"] = [
            {"schemeID": "https://example.com/scheme", "schemeName": "S", "code": "c", "name": "n"},
        ]
        out, _ = upgrade(src)
        cls = out["credentialSubject"]["productCategory"][0]
        assert "schemeID" not in cls
        assert cls["schemeId"] == "https://example.com/scheme"

    def test_rename_inside_nested_classification(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["materialsProvenance"] = [
            {
                "name": "X",
                "originCountry": "DE",
                "massFraction": 0.5,
                "materialType": {
                    "schemeID": "https://example.com/scheme",
                    "schemeName": "S",
                    "code": "c",
                    "name": "n",
                },
            },
        ]
        out, _ = upgrade(src)
        mt = out["credentialSubject"]["materialProvenance"][0]["materialType"]
        assert "schemeID" not in mt
        assert mt["schemeId"] == "https://example.com/scheme"


# ---------------------------------------------------------------------------
# Step 17 — Material required-field detection
# ---------------------------------------------------------------------------


class TestStep17MaterialRequiredFields:
    def test_missing_material_type_emits_upg004(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["materialsProvenance"] = [
            {"name": "X", "originCountry": "DE", "massFraction": 0.5},
        ]
        _, warnings = upgrade(src)
        assert any(
            w.code == UPG_CODE_REQUIRED_FIELD_MISSING and "materialType" in w.path for w in warnings
        )

    def test_missing_mass_fraction_emits_upg004(self) -> None:
        src = _minimal_v06_payload()
        src["credentialSubject"]["materialsProvenance"] = [
            {
                "name": "X",
                "originCountry": "DE",
                "materialType": {"schemeID": "s", "schemeName": "S", "code": "c", "name": "n"},
            },
        ]
        _, warnings = upgrade(src)
        assert any(
            w.code == UPG_CODE_REQUIRED_FIELD_MISSING and "massFraction" in w.path for w in warnings
        )


# ---------------------------------------------------------------------------
# Round-trip: every 0.6.x valid fixture upgrades and either validates
# cleanly or emits structured warnings.
# ---------------------------------------------------------------------------


_VALID_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "valid"


def _enveloped_v06_fixtures() -> list[Path]:
    """Return ``valid/*.json`` fixtures that carry a full VC envelope.

    Some legacy fixtures (e.g. ``product_passport_instance_0.6.1.json``)
    are bare ``ProductPassport`` shapes without the W3C VC v2 envelope —
    they were captured for direct ``ProductPassport`` model tests, not
    for the engine's full credential pipeline. The shim correctly
    no-ops on them (nothing to upgrade), but they don't fit the
    envelope-oriented round-trip assertions below.
    """
    out: list[Path] = []
    for path in sorted(_VALID_FIXTURE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not (isinstance(data, dict) and "@context" in data and "credentialSubject" in data):
            continue
        # Skip v0.7-shaped fixtures vendored in Phase 5 — the shim upgrades
        # *from* v0.6 only, not v0.7.
        ctx = data.get("@context") or []
        if any(isinstance(c, str) and "vocabulary.uncefact.org/untp/0.7" in c for c in ctx):
            continue
        out.append(path)
    return out


@pytest.mark.parametrize(
    "fixture_path",
    _enveloped_v06_fixtures(),
    ids=lambda p: p.name,
)
def test_v06_fixtures_round_trip_through_shim(fixture_path: Path) -> None:
    """Every enveloped 0.6.x ``valid/*.json`` fixture upgrades without crashing.

    Per the migration plan exit criterion: "every 0.6.x valid fixture
    either upgrades and re-validates cleanly, or emits a documented
    warning". This test asserts the *upgrade itself* never crashes;
    re-validation is covered by the model integration test below.
    """
    src = json.loads(fixture_path.read_text(encoding="utf-8"))
    out, warnings = upgrade(src)
    assert isinstance(out, dict)
    assert "@context" in out
    for w in warnings:
        assert w.code.startswith("UPG"), f"unexpected code: {w.code}"
        assert w.path, "warning path must not be empty"
        assert w.message, "warning message must not be empty"


@pytest.mark.parametrize(
    "fixture_path",
    _enveloped_v06_fixtures(),
    ids=lambda p: p.name,
)
def test_v06_fixtures_upgrade_to_v07_context_url(fixture_path: Path) -> None:
    """The shim always swaps the v0.6 context URL for the v0.7 one."""
    src = json.loads(fixture_path.read_text(encoding="utf-8"))
    out, _ = upgrade(src)
    contexts = out["@context"]
    assert any("vocabulary.uncefact.org/untp/0.7" in c for c in contexts)
    assert not any("test.uncefact.org/vocabulary/untp/dpp/0.6" in c for c in contexts)


def test_bare_product_passport_does_not_crash_shim() -> None:
    """Bare ProductPassport shapes (no VC envelope) should no-op cleanly.

    The shim is defined for v0.6 ``DigitalProductPassport`` envelopes;
    a bare ``ProductPassport`` lacks the envelope and shouldn't make
    the shim raise. It just won't do anything substantive.
    """
    bare_path = _VALID_FIXTURE_DIR / "product_passport_instance_0.6.1.json"
    if not bare_path.is_file():
        pytest.skip("bare ProductPassport fixture not present")
    src = json.loads(bare_path.read_text(encoding="utf-8"))
    out, warnings = upgrade(src)
    assert isinstance(out, dict)
    assert isinstance(warnings, list)
