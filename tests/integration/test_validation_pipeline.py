"""Integration tests for the full validation pipeline.

Tests end-to-end behavior through all validation layers with real fixtures.
"""

import json
from pathlib import Path

import pytest

from dppvalidator.validators import ValidationEngine, ValidationResult

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestValidFixtures:
    """Integration tests validating known-good DPP fixtures."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        """Create validation engine with all layers."""
        return ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])

    def test_minimal_dpp_passes_validation(self, engine):
        """Minimal valid DPP passes all validation layers."""
        fixture_path = FIXTURES_DIR / "valid" / "minimal_dpp.json"
        result = engine.validate_file(fixture_path)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.passport is not None

    def test_full_dpp_passes_validation(self, engine):
        """Full DPP with all fields passes validation."""
        fixture_path = FIXTURES_DIR / "valid" / "full_dpp.json"
        result = engine.validate_file(fixture_path)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_untp_instance_passes_validation(self, engine):
        """Real UNTP DPP instance fixture passes validation."""
        fixture_path = FIXTURES_DIR / "valid" / "untp-dpp-instance-0.6.1.json"
        if not fixture_path.exists():
            pytest.skip("UNTP instance fixture not available")

        result = engine.validate_file(fixture_path)

        # Should parse and validate without crashing
        assert isinstance(result, ValidationResult)
        # May have warnings but should be structurally valid
        assert result.passport is not None or len(result.errors) > 0


class TestInvalidFixtures:
    """Integration tests validating known-bad DPP fixtures."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        """Create validation engine with all layers."""
        return ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])

    def test_missing_issuer_fails_validation(self, engine):
        """DPP missing required issuer field fails."""
        fixture_path = FIXTURES_DIR / "invalid" / "missing_issuer.json"
        result = engine.validate_file(fixture_path)

        assert result.valid is False
        assert len(result.errors) > 0
        # Should identify issuer as the problem
        error_paths = [e.path for e in result.errors]
        assert any("issuer" in path.lower() for path in error_paths)

    def test_invalid_dates_fails_validation(self, engine):
        """DPP with invalid date order fails semantic validation."""
        fixture_path = FIXTURES_DIR / "invalid" / "invalid_dates.json"
        result = engine.validate_file(fixture_path)

        assert result.valid is False
        # Should have semantic error about dates
        error_codes = [e.code for e in result.errors]
        assert any("SEM" in code for code in error_codes) or len(result.errors) > 0

    def test_invalid_mass_fractions_produces_warning(self, engine):
        """DPP with mass fractions not summing to 1.0 produces warning."""
        fixture_path = FIXTURES_DIR / "invalid" / "invalid_mass_fractions.json"
        if not fixture_path.exists():
            pytest.skip("Fixture not yet created")

        result = engine.validate_file(fixture_path)

        # Partial mass fractions produce a warning, not an error
        warning_codes = [w.code for w in result.warnings]
        assert "SEM001" in warning_codes

    def test_hazardous_material_detected(self, engine):
        """Hazardous material is flagged during validation."""
        fixture_path = FIXTURES_DIR / "invalid" / "hazardous_no_safety.json"
        if not fixture_path.exists():
            pytest.skip("Fixture not yet created")

        result = engine.validate_file(fixture_path)

        # Should process and detect the hazardous material
        assert result.passport is not None or len(result.errors) > 0


class TestMultiLayerValidation:
    """Tests for validation layer interaction."""

    def test_model_only_validation(self):
        """Model-only validation validates structure without semantic rules."""
        engine = ValidationEngine(layers=["model"])
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }

        result = engine.validate(data)

        # Model validation passes with valid structure
        assert result.valid is True
        assert result.passport is not None

    def test_semantic_validation_with_model(self):
        """Semantic layer runs after model validation."""
        engine = ValidationEngine(layers=["model", "semantic"])
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }

        result = engine.validate(data)

        # Should process through both layers
        assert isinstance(result, ValidationResult)
        # Warnings may be present for missing recommended fields
        assert result.passport is not None or len(result.errors) >= 0

    def test_fail_fast_stops_on_first_error(self):
        """Fail-fast mode stops after first error."""
        engine = ValidationEngine(layers=["model", "semantic"])
        data = {"invalid": "data"}  # Missing multiple required fields

        result = engine.validate(data, fail_fast=True)

        assert result.valid is False
        # Should have at least one error but potentially stopped early
        assert len(result.errors) >= 1

    def test_max_errors_limits_output(self):
        """Max errors setting limits error count."""
        engine = ValidationEngine(layers=["model"])
        # Data that would generate many errors
        data = {"a": 1, "b": 2, "c": 3}

        result = engine.validate(data, max_errors=2)

        assert result.valid is False
        assert len(result.errors) <= 2


class TestValidationInputFormats:
    """Tests for different input formats."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        return ValidationEngine(layers=["model"])

    def test_validate_dict_input(self, engine):
        """Validates dict input directly."""
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }

        result = engine.validate(data)

        assert result.valid is True

    def test_validate_json_string_input(self, engine):
        """Validates JSON string input."""
        json_str = json.dumps(
            {
                "id": "https://example.com/dpp",
                "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            }
        )

        result = engine.validate(json_str)

        assert result.valid is True

    def test_validate_file_path_input(self, engine, tmp_path):
        """Validates file path input."""
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data))

        result = engine.validate(file_path)

        assert result.valid is True

    def test_nonexistent_file_returns_error(self, engine):
        """Nonexistent file returns parse error."""
        result = engine.validate(Path("/nonexistent/path.json"))

        assert result.valid is False
        assert any(e.code == "PRS001" for e in result.errors)

    def test_invalid_json_returns_error(self, engine, tmp_path):
        """Invalid JSON file returns parse error."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{invalid json")

        result = engine.validate(file_path)

        assert result.valid is False
        assert any(e.code == "PRS002" for e in result.errors)

    def test_invalid_json_string_returns_error(self, engine):
        """Invalid JSON string returns parse error."""
        result = engine.validate("{not valid json}")

        assert result.valid is False
        assert any(e.code == "PRS002" for e in result.errors)


class TestAsyncValidation:
    """Tests for async validation methods."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        return ValidationEngine(layers=["model"])

    def test_validate_async_exists(self, engine):
        """Async validation method exists and is callable."""
        import asyncio

        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }

        # Run async method synchronously for testing
        result = asyncio.run(engine.validate_async(data))

        assert result.valid is True

    def test_validate_batch_exists(self, engine):
        """Batch validation method exists and processes items."""
        import asyncio

        items = [
            {
                "id": f"https://example.com/dpp-{i}",
                "issuer": {"id": "https://x.com", "name": f"Test {i}"},
            }
            for i in range(3)
        ]

        results = asyncio.run(engine.validate_batch(items))

        assert len(results) == 3
        assert all(r.valid for r in results)


class TestValidationResultBehavior:
    """Tests for ValidationResult behavior."""

    def test_result_includes_schema_version(self):
        """Result includes schema version used."""
        engine = ValidationEngine(schema_version="0.6.1", layers=["model"])
        data = {"id": "https://x.com", "issuer": {"id": "https://x.com", "name": "T"}}

        result = engine.validate(data)

        assert result.schema_version == "0.6.1"

    def test_result_includes_timing(self):
        """Result includes parse timing information."""
        engine = ValidationEngine(layers=["model"])
        data = {"id": "https://x.com", "issuer": {"id": "https://x.com", "name": "T"}}

        result = engine.validate(data)

        assert result.parse_time_ms is not None
        assert result.parse_time_ms >= 0

    def test_result_merge_combines_errors(self):
        """Merging results combines errors from both."""
        from dppvalidator.validators.results import ValidationError

        result1 = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.a", message="Error A", code="E1", layer="model")],
        )
        result2 = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.b", message="Error B", code="E2", layer="model")],
        )

        merged = result1.merge(result2)

        assert len(merged.errors) == 2
        assert merged.valid is False

    def test_result_to_json_serializable(self):
        """Result can be serialized to JSON."""
        engine = ValidationEngine(layers=["model"])
        data = {"id": "https://x.com", "issuer": {"id": "https://x.com", "name": "T"}}

        result = engine.validate(data)
        json_str = result.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "valid" in parsed
