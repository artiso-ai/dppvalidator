"""Acceptance tests for the UNTP v0.7.0 Pydantic models.

Phase 3 of docs/plans/UNTP_0.7.0_MIGRATION.md introduced
``dppvalidator.models.v0_7``. These tests cover:

1. The dispatch table is in lock-step with the schema registry — every
   registered version has a model class.
2. Each vendored 0.7.0 sample (canonical, battery, cathode) parses
   cleanly through ``v0_7.DigitalProductPassport``.
3. The cross-field invariants documented in §3.2 of the plan are wired
   correctly (date order, granularity ↔ id required, hazardous ↔ safety
   info, mass-fraction sum ≤ 1.0, performance has measure or score,
   period ordering, country-code shape, image required fields).

These tests deliberately do not exercise the engine (that's covered by
``test_phase3_engine.py``) — they pin the model layer's behaviour in
isolation so a regression there is identifiable.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from dppvalidator.models import v0_6, v0_7
from dppvalidator.schemas.registry import SCHEMA_REGISTRY
from dppvalidator.validators.model import _MODEL_BY_VERSION

_UPSTREAM_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "upstream" / "v0.7.0"
_SAMPLES = {
    "canonical": _UPSTREAM_DIR / "samples" / "DigitalProductPassport_instance.json",
    "battery": _UPSTREAM_DIR / "samples" / "DigitalProductPassport_battery_instance.json",
    "cathode": _UPSTREAM_DIR / "samples" / "DigitalProductPassport_cathode_instance.json",
}


def _load(name: str) -> dict:
    path = _SAMPLES[name]
    if not path.is_file():  # pragma: no cover - vendored in Phase 0
        pytest.skip(f"Vendor {path} via Phase 0 of the migration plan.")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------------
# Dispatch table contract
# ----------------------------------------------------------------------------


class TestDispatchTable:
    def test_dispatch_table_covers_every_registered_version(self) -> None:
        """Every entry in SCHEMA_REGISTRY has a model in _MODEL_BY_VERSION."""
        missing = sorted(set(SCHEMA_REGISTRY) - set(_MODEL_BY_VERSION))
        assert not missing, (
            f"Versions registered without a Pydantic model: {missing}. "
            "Add an entry to validators/model.py::_MODEL_BY_VERSION."
        )

    def test_dispatch_uses_v0_6_for_legacy_versions(self) -> None:
        assert _MODEL_BY_VERSION["0.6.0"] is v0_6.DigitalProductPassport
        assert _MODEL_BY_VERSION["0.6.1"] is v0_6.DigitalProductPassport

    def test_dispatch_uses_v0_7_for_modern_version(self) -> None:
        assert _MODEL_BY_VERSION["0.7.0"] is v0_7.DigitalProductPassport

    def test_v0_6_and_v0_7_dpp_classes_are_distinct(self) -> None:
        """The two version namespaces must not alias to the same class."""
        assert v0_6.DigitalProductPassport is not v0_7.DigitalProductPassport


# ----------------------------------------------------------------------------
# Canonical sample parsing
# ----------------------------------------------------------------------------


class TestUpstreamSampleParsing:
    @pytest.mark.parametrize("name", sorted(_SAMPLES))
    def test_each_upstream_sample_parses_through_v0_7_model(self, name: str) -> None:
        data = _load(name)
        dpp = v0_7.DigitalProductPassport.model_validate(data)
        assert dpp.id
        assert dpp.name
        assert isinstance(dpp.credential_subject, v0_7.Product)
        assert dpp.credential_subject.name
        assert dpp.credential_subject.id_granularity is not None

    def test_canonical_sample_round_trip_preserves_top_keys(self) -> None:
        """Round-tripping through the model preserves the envelope shape."""
        data = _load("canonical")
        dpp = v0_7.DigitalProductPassport.model_validate(data)
        out = dpp.model_dump(by_alias=True, exclude_none=True)
        assert out["id"] == data["id"]
        assert out["name"] == data["name"]
        assert "credentialSubject" in out


# ----------------------------------------------------------------------------
# Cross-field invariants
# ----------------------------------------------------------------------------


class TestEnvelopeInvariants:
    def test_validfrom_must_precede_validuntil(self) -> None:
        data = _load("canonical")
        # Make validUntil precede validFrom
        data["validFrom"] = "2030-01-01T00:00:00Z"
        data["validUntil"] = "2025-01-01T00:00:00Z"
        with pytest.raises(ValidationError, match="validFrom"):
            v0_7.DigitalProductPassport.model_validate(data)

    def test_validfrom_required(self) -> None:
        """v0.7.0 makes validFrom required (envelope-level)."""
        data = _load("canonical")
        del data["validFrom"]
        with pytest.raises(ValidationError, match="validFrom"):
            v0_7.DigitalProductPassport.model_validate(data)

    def test_name_required_and_non_empty(self) -> None:
        data = _load("canonical")
        data["name"] = ""
        with pytest.raises(ValidationError):
            v0_7.DigitalProductPassport.model_validate(data)


class TestProductInvariants:
    def test_item_granularity_requires_item_number(self) -> None:
        data = _load("canonical")
        data["credentialSubject"]["idGranularity"] = "item"
        data["credentialSubject"].pop("itemNumber", None)
        with pytest.raises(ValidationError, match="itemNumber"):
            v0_7.DigitalProductPassport.model_validate(data)

    def test_batch_granularity_requires_batch_number(self) -> None:
        data = _load("canonical")
        data["credentialSubject"]["idGranularity"] = "batch"
        data["credentialSubject"].pop("batchNumber", None)
        with pytest.raises(ValidationError, match="batchNumber"):
            v0_7.DigitalProductPassport.model_validate(data)

    def test_mass_fraction_sum_above_unity_rejected(self) -> None:
        data = _load("canonical")
        # Pad materialProvenance until the sum exceeds 1.0
        materials = data["credentialSubject"]["materialProvenance"]
        # Inject two materials whose mass fractions sum > 1.0
        proto = materials[0]
        materials.append({**proto, "name": "Padding A", "massFraction": 0.7})
        materials.append({**proto, "name": "Padding B", "massFraction": 0.7})
        with pytest.raises(ValidationError, match="mass.?[Ff]raction"):
            v0_7.DigitalProductPassport.model_validate(data)


class TestMaterialInvariants:
    def _make_minimal_material(self, **overrides) -> dict:
        base = {
            "name": "Lithium",
            "originCountry": {"countryCode": "AU", "countryName": "Australia"},
            "materialType": {
                "schemeId": "https://example.com/scheme",
                "schemeName": "Example",
                "code": "Li",
                "name": "Lithium",
            },
            "massFraction": 0.5,
        }
        return {**base, **overrides}

    def test_hazardous_requires_safety_information(self) -> None:
        with pytest.raises(ValidationError, match="materialSafetyInformation"):
            v0_7.Material.model_validate(self._make_minimal_material(hazardous=True))

    def test_hazardous_with_safety_info_passes(self) -> None:
        m = self._make_minimal_material(
            hazardous=True,
            materialSafetyInformation={
                "linkURL": "https://example.com/sds.pdf",
                "name": "SDS",
                "mediaType": "application/pdf",
            },
        )
        v0_7.Material.model_validate(m)


class TestPerformanceInvariants:
    def test_at_least_one_of_measure_or_score(self) -> None:
        with pytest.raises(ValidationError, match="measure.+score"):
            v0_7.Performance.model_validate({"metric": {"name": "x"}})

    def test_with_measure_only_is_ok(self) -> None:
        v0_7.Performance.model_validate(
            {
                "metric": {"name": "co2"},
                "measure": {"value": 12.5, "unit": "KGM"},
            },
        )

    def test_with_score_only_is_ok(self) -> None:
        v0_7.Performance.model_validate(
            {
                "metric": {"name": "rating"},
                "score": {"code": "A"},
            },
        )


class TestPeriodInvariants:
    def test_start_after_end_rejected(self) -> None:
        with pytest.raises(ValidationError, match="startDate"):
            v0_7.Period.model_validate(
                {"startDate": "2025-12-01", "endDate": "2025-01-01"},
            )

    def test_open_ended_periods_ok(self) -> None:
        v0_7.Period.model_validate({"startDate": "2025-01-01"})  # no end
        v0_7.Period.model_validate({"endDate": "2025-12-31"})  # no start


class TestCountryInvariants:
    def test_iso_3166_alpha2_required(self) -> None:
        with pytest.raises(ValidationError, match="countryCode"):
            v0_7.Country.model_validate({"countryCode": "USA"})  # 3 letters
        with pytest.raises(ValidationError, match="countryCode"):
            v0_7.Country.model_validate({"countryCode": "us"})  # lowercase

    def test_alpha2_uppercase_passes(self) -> None:
        c = v0_7.Country.model_validate({"countryCode": "DE", "countryName": "Germany"})
        assert c.country_code == "DE"


# ----------------------------------------------------------------------------
# Pydantic v2 patterns sanity check (per .claude/rules/dpp-domain.md)
# ----------------------------------------------------------------------------


class TestPydanticV2Patterns:
    def test_models_use_extra_allow_on_envelope(self) -> None:
        """UNTPBaseModel ships extra='allow' so industry extensions flow through."""
        data = _load("canonical")
        data["x:vendor-extension"] = {"key": "value"}
        # Must not raise on extra
        v0_7.DigitalProductPassport.model_validate(data)

    def test_model_dump_uses_aliases_for_jsonld_output(self) -> None:
        """model_dump(by_alias=True) emits camelCase keys."""
        c = v0_7.Country.model_validate({"countryCode": "ES", "countryName": "Spain"})
        d = c.model_dump(by_alias=True, exclude_none=True)
        assert "countryCode" in d
        assert "countryName" in d
        # snake_case must NOT be in the dumped output
        assert "country_code" not in d


# ----------------------------------------------------------------------------
# Smoke test on the constructor — Pydantic v2 import paths
# ----------------------------------------------------------------------------


def test_construct_minimal_v07_dpp_programmatically() -> None:
    """Build a minimal valid 0.7.0 DPP from scratch (not via JSON)."""
    now = datetime.now(timezone.utc)
    dpp = v0_7.DigitalProductPassport(
        **{
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://vocabulary.uncefact.org/untp/0.7.0/context/",
            ],
        },
        id="https://example.com/credentials/dpp-1",
        name="Smoke test DPP",
        issuer=v0_7.CredentialIssuer(id="did:web:example.com", name="Example Co"),
        validFrom=now,
        validUntil=now + timedelta(days=365),
        credentialSubject=v0_7.Product(
            id="https://example.com/products/p1",
            name="Widget",
            idScheme=v0_7.IdentifierScheme(
                id="https://example.com/scheme",
                name="Example scheme",
            ),
            idGranularity=v0_7.product.IdGranularity.MODEL,
            productCategory=[
                v0_7.Classification(
                    schemeId="https://unstats.un.org/cpc",
                    schemeName="UN CPC",
                    code="14110",
                    name="Widgets",
                ),
            ],
            producedAtFacility=v0_7.Facility(
                id="https://example.com/facility/1",
                name="Main plant",
            ),
            countryOfProduction=v0_7.Country(countryCode="DE", countryName="Germany"),
            productionDate=date(2025, 1, 1),
        ),
    )
    assert dpp.credential_subject.name == "Widget"
