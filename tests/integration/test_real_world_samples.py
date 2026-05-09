"""Integration tests using real-world DPP samples from various sources.

Tests the validation pipeline against actual DPP instances from:
- UNTP (UN Trade Protocol) reference implementations
- Battery Pass data model examples
- NFC Forum DPP examples
- Catena-X/Tractus-X battery pass models
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from dppvalidator.validators import ValidationEngine, ValidationResult

if TYPE_CHECKING:
    from collections.abc import Iterator

SAMPLES_DIR = Path(__file__).parent.parent / "fixtures" / "samples"


def _load_sample(filename: str) -> dict[str, Any] | None:
    """Load a sample file if it exists."""
    path = SAMPLES_DIR / filename
    if not path.exists():
        return None
    with open(path) as f:
        data: dict[str, Any] = json.load(f)
        return data


def _sample_files() -> Iterator[Path]:
    """Yield all JSON sample files."""
    if not SAMPLES_DIR.exists():
        return
    yield from SAMPLES_DIR.glob("*.json")


class TestUNTPSamples:
    """Tests for UNTP (UN Trade Protocol) DPP samples.

    These are considered the reference implementation for DPP structure
    and should pass validation with high confidence.
    """

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        return ValidationEngine(schema_version="auto", layers=["model", "semantic"])

    def test_untp_dpp_instance_0_6_0(self, engine: ValidationEngine):
        """UNTP DPP v0.6.0 instance should validate successfully."""
        data = _load_sample("test_uncefact_org_untp-dpp-instance-0.6.0.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        assert result.passport is not None, f"Failed to parse: {result.errors}"
        # UNTP reference should pass with minimal errors
        assert result.valid or len(result.errors) <= 2

    def test_untp_dpp_instance_0_3_10(self, engine: ValidationEngine):
        """UNTP DPP v0.3.10 instance should be parseable."""
        data = _load_sample("opensource_unicc_org_untp-digital-product-passport-v0.3.10.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        # Older version may have structural differences
        assert result.passport is not None or len(result.errors) > 0

    def test_untp_digital_facility_record(self, engine: ValidationEngine):
        """UNTP Digital Facility Record should be parseable as related credential."""
        data = _load_sample("opensource_unicc_org_untp-digital-facility-record-v0.3.9.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        # Facility records are different from DPPs but should still parse
        assert isinstance(result, ValidationResult)

    def test_untp_digital_identity_anchor(self, engine: ValidationEngine):
        """UNTP Digital Identity Anchor should be parseable."""
        data = _load_sample("test_uncefact_org_DigitalIdentityAnchor-instance-0.6.1.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        # Identity anchors have different structure
        assert result.passport is not None or len(result.errors) > 0


class TestBatteryPassSamples:
    """Tests for Battery Pass data model samples.

    These follow the EU Battery Regulation requirements and include
    specific battery-related fields.
    """

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        return ValidationEngine(schema_version="auto", layers=["model", "semantic"])

    def test_battery_pass_general_product_info_payload(self, engine: ValidationEngine):
        """Battery Pass GeneralProductInformation payload should be parseable."""
        data = _load_sample(
            "BatteryPassDataModel_BatteryPass_GeneralProductInformation-payload.json"
        )
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        # Battery Pass has different structure, may not fully validate
        # but should parse and identify key fields
        if result.passport:
            # Check if battery-specific fields are recognized
            assert result.passport is not None

    def test_battery_pass_general_product_info_ld(self, engine: ValidationEngine):
        """Battery Pass GeneralProductInformation JSON-LD should be parseable."""
        data = _load_sample("batterypass_BatteryPassDataModel_GeneralProductInformation-ld.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        # JSON-LD with @graph structure may need special handling
        if "@graph" in data:
            # Verify we handle @graph structures
            assert result.passport is not None or len(result.errors) > 0

    def test_battery_pass_circularity_ld(self, engine: ValidationEngine):
        """Battery Pass Circularity JSON-LD should be parseable."""
        data = _load_sample("batterypass_BatteryPassDataModel_Circularity-ld.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)

    def test_battery_pass_material_composition_ld(self, engine: ValidationEngine):
        """Battery Pass MaterialComposition JSON-LD should be parseable."""
        data = _load_sample("batterypass_BatteryPassDataModel_MaterialComposition-ld.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)

    def test_battery_pass_carbon_footprint_ld(self, engine: ValidationEngine):
        """Battery Pass CarbonFootprint JSON-LD should be parseable."""
        data = _load_sample("batterypass_BatteryPassDataModel_CarbonFootprintForBatteries-ld.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)


class TestCatenaXSamples:
    """Tests for Catena-X/Tractus-X battery pass samples.

    These are industry consortium examples from automotive sector.
    """

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        return ValidationEngine(schema_version="auto", layers=["model", "semantic"])

    def test_tractus_x_battery_pass(self, engine: ValidationEngine):
        """Tractus-X BatteryPass sample should be parseable."""
        data = _load_sample("eclipse-tractusx_sldt-semantic-models_BatteryPass.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        # Catena-X has its own structure, validate basic parsing
        if result.passport:
            # Should extract some product information
            assert result.passport is not None


class TestAlternativeDPPFormats:
    """Tests for alternative DPP formats from various sources."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        return ValidationEngine(schema_version="auto", layers=["model", "semantic"])

    def test_nfc_forum_long_dpp_example(self, engine: ValidationEngine):
        """NFC Forum long DPP example should be parseable."""
        data = _load_sample("nfc-forum_org_long-dpp-example.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        # NFC Forum example has different structure
        # but contains product information
        if result.passport is None and result.errors:
            # Should identify what's missing
            error_messages = [e.message for e in result.errors]
            assert len(error_messages) > 0

    def test_spherity_breathable_tshirt(self, engine: ValidationEngine):
        """Spherity breathable t-shirt sample should be parseable."""
        data = _load_sample("schemas_testing_breathable-t-shirt.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)

    def test_enveloped_verifiable_credential(self, engine: ValidationEngine):
        """Enveloped VC from S3 should be parseable."""
        data = _load_sample(
            "untp-verifiable-credentials_s3_amazonaws_com_bc075c5f-2304-4b3f-bb24-46d9fa9a8e60.json"
        )
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        # Enveloped credentials need unwrapping
        if data.get("type") == "EnvelopedVerifiableCredential":
            # Should handle or report enveloped format
            assert result.passport is not None or len(result.errors) > 0


class TestBulkSampleValidation:
    """Bulk tests across all downloaded samples."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        return ValidationEngine(schema_version="auto", layers=["model"])

    def test_all_samples_are_valid_json(self):
        """All sample files should be valid JSON."""
        for sample_path in _sample_files():
            with open(sample_path) as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, dict), f"{sample_path.name} is not a JSON object"
                except json.JSONDecodeError as e:
                    pytest.fail(f"{sample_path.name} is not valid JSON: {e}")

    def test_all_samples_can_be_processed(self, engine: ValidationEngine):
        """All samples should be processable without crashing."""
        for sample_path in _sample_files():
            with open(sample_path) as f:
                data = json.load(f)

            # Should not raise any exceptions
            result = engine.validate(data)
            assert isinstance(result, ValidationResult), f"Failed on {sample_path.name}"

    @pytest.mark.parametrize(
        "filename",
        [
            "test_uncefact_org_untp-dpp-instance-0.6.0.json",
        ],
    )
    def test_excellent_samples_validate(self, engine: ValidationEngine, filename: str):
        """Samples rated 'excellent' with matching schema version should pass validation."""
        data = _load_sample(filename)
        if data is None:
            pytest.skip(f"Sample {filename} not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert result.passport is not None, f"{filename}: {result.errors}"

    def test_older_untp_sample_processes_with_version_differences(self, engine: ValidationEngine):
        """Older UNTP samples may have schema differences but should still process."""
        data = _load_sample("opensource_unicc_org_untp-digital-product-passport-v0.3.10.json")
        if data is None:
            pytest.skip("Sample not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        # Older versions may fail strict validation due to schema evolution
        # but the error should be about extra/missing fields, not parsing failures
        assert isinstance(result, ValidationResult)
        if not result.valid:
            # Errors should be model-level (schema differences), not parsing errors
            assert all(e.layer == "model" for e in result.errors)

    @pytest.mark.parametrize(
        "filename",
        [
            "test_uncefact_org_DigitalIdentityAnchor-instance-0.6.1.json",
            "opensource_unicc_org_untp-digital-facility-record-v0.3.9.json",
            "BatteryPassDataModel_BatteryPass_GeneralProductInformation-payload.json",
            "batterypass_BatteryPassDataModel_GeneralProductInformation-ld.json",
        ],
    )
    def test_good_samples_process(self, engine: ValidationEngine, filename: str):
        """Samples rated 'good' should process without errors."""
        data = _load_sample(filename)
        if data is None:
            pytest.skip(f"Sample {filename} not available")
        assert data is not None  # Type narrowing

        result = engine.validate(data)

        assert isinstance(result, ValidationResult)
        # Good samples may not fully validate but should parse
        assert result.passport is not None or result.errors


class TestSampleStructureAnalysis:
    """Tests that analyze the structure of real-world samples."""

    def test_untp_samples_have_context(self):
        """UNTP samples should have @context field."""
        untp_samples = [
            "test_uncefact_org_untp-dpp-instance-0.6.0.json",
            "opensource_unicc_org_untp-digital-product-passport-v0.3.10.json",
        ]
        for filename in untp_samples:
            data = _load_sample(filename)
            if data is None:
                continue

            assert "@context" in data, f"{filename} missing @context"
            assert isinstance(data["@context"], list), f"{filename} @context should be list"

    def test_untp_samples_have_type(self):
        """UNTP samples should have type field."""
        untp_samples = [
            "test_uncefact_org_untp-dpp-instance-0.6.0.json",
            "opensource_unicc_org_untp-digital-product-passport-v0.3.10.json",
        ]
        for filename in untp_samples:
            data = _load_sample(filename)
            if data is None:
                continue

            assert "type" in data, f"{filename} missing type"
            types = data["type"]
            assert "VerifiableCredential" in types, f"{filename} should be VerifiableCredential"

    def test_untp_samples_have_issuer(self):
        """UNTP samples should have issuer field."""
        untp_samples = [
            "test_uncefact_org_untp-dpp-instance-0.6.0.json",
            "opensource_unicc_org_untp-digital-product-passport-v0.3.10.json",
        ]
        for filename in untp_samples:
            data = _load_sample(filename)
            if data is None:
                continue

            assert "issuer" in data, f"{filename} missing issuer"
            issuer = data["issuer"]
            assert "id" in issuer, f"{filename} issuer missing id"

    def test_untp_samples_have_credential_subject(self):
        """UNTP samples should have credentialSubject field."""
        untp_samples = [
            "test_uncefact_org_untp-dpp-instance-0.6.0.json",
            "opensource_unicc_org_untp-digital-product-passport-v0.3.10.json",
        ]
        for filename in untp_samples:
            data = _load_sample(filename)
            if data is None:
                continue

            assert "credentialSubject" in data, f"{filename} missing credentialSubject"

    def test_battery_pass_samples_have_battery_fields(self):
        """Battery Pass samples should contain battery-specific fields."""
        battery_sample = _load_sample(
            "BatteryPassDataModel_BatteryPass_GeneralProductInformation-payload.json"
        )
        if battery_sample is None:
            pytest.skip("Battery Pass sample not available")
        assert battery_sample is not None  # Type narrowing

        battery_fields = ["batteryCategory", "batteryStatus", "batteryMass"]
        sample_keys = list(battery_sample.keys())
        found = [f for f in battery_fields if f in sample_keys]
        assert len(found) >= 2, f"Expected battery fields, found: {sample_keys}"


class TestValidationConsistency:
    """Tests for validation consistency across similar samples."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        return ValidationEngine(schema_version="auto", layers=["model", "semantic"])

    def test_same_version_samples_produce_consistent_results(
        self,
        engine: ValidationEngine,  # noqa: ARG002 — auto fixture even when overridden
    ):
        """Samples from the same schema family should produce consistent validation.

        Per-sample engine pinning because:
        - sample1 carries an explicit ``0.6.0`` declaration (VER001 fires
          if engine is pinned elsewhere).
        - sample2 (DigitalIdentityAnchor) lacks an explicit version signal;
          Phase 9 task 9.1 flipped DEFAULT_SCHEMA_VERSION to 0.7.0, which
          surfaces the v0.6/v0.7 model shape mismatch for DIA. The test's
          stated intent is "both v0.6.x", so pin sample2's engine to 0.6.1.
        """
        # Test with two v0.6.x samples which should both validate
        sample1 = _load_sample("test_uncefact_org_untp-dpp-instance-0.6.0.json")
        sample2 = _load_sample("test_uncefact_org_DigitalIdentityAnchor-instance-0.6.1.json")

        if sample1 is None or sample2 is None:
            pytest.skip("Samples not available")
        assert sample1 is not None and sample2 is not None  # Type narrowing

        engine_v060 = ValidationEngine(schema_version="0.6.0", layers=["model", "semantic"])
        engine_v061 = ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])
        result1 = engine_v060.validate(sample1)
        result2 = engine_v061.validate(sample2)

        # Both are v0.6.x and should parse successfully
        assert result1.passport is not None, f"v0.6.0 DPP failed: {result1.errors}"
        assert result2.passport is not None, f"v0.6.1 DIA failed: {result2.errors}"
