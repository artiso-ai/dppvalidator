"""Tests for ValidationEngine."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from dppvalidator.validators import ValidationEngine

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestValidationEngine:
    """Tests for ValidationEngine."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        """Create validation engine (model + semantic only for unit tests)."""
        return ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])

    def test_validate_minimal_valid_dpp(self, engine: ValidationEngine):
        """Test validating a minimal valid DPP."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/credentials/dpp-001",
            "issuer": {
                "id": "https://example.com/issuers/001",
                "name": "Example Company Ltd",
            },
        }
        result = engine.validate(data)
        assert result.valid is True

    def test_validate_missing_issuer(self, engine: ValidationEngine):
        """Test validation fails for missing issuer."""
        data = {
            "id": "https://example.com/credentials/dpp-001",
        }
        result = engine.validate(data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_invalid_json(self, engine: ValidationEngine):
        """Test validation handles invalid data gracefully."""
        result = engine.validate("not valid json data")
        assert result.valid is False

    def test_validate_with_fail_fast(self, engine: ValidationEngine):
        """Test fail_fast stops on first error."""
        data = {"invalid": "data"}
        result = engine.validate(data, fail_fast=True)
        assert result.valid is False
        assert len(result.all_issues) >= 1

    def test_validate_fixture_valid(self, engine: ValidationEngine):
        """Test validating valid fixture."""
        fixture_path = FIXTURES_DIR / "valid" / "minimal_dpp.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            result = engine.validate(data)
            assert result.valid is True

    def test_validate_fixture_invalid(self, engine: ValidationEngine):
        """Test validating invalid fixture."""
        fixture_path = FIXTURES_DIR / "invalid" / "missing_issuer.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            result = engine.validate(data)
            assert result.valid is False

    def test_validate_official_untp_dpp_instance_schema_only(self):
        """Test validating the official UNTP DPP 0.6.1 example with schema layer only."""
        fixture_path = FIXTURES_DIR / "valid" / "untp-dpp-instance-0.6.1.json"
        assert fixture_path.exists(), "Official UNTP DPP example fixture not found"
        data = json.loads(fixture_path.read_text())

        schema_engine = ValidationEngine(layers=["schema"], schema_version="0.6.1")
        result = schema_engine.validate(data)
        schema_errors = [e for e in result.errors if e.layer == "schema"]
        assert len(schema_errors) == 0, f"Schema validation errors: {schema_errors}"

    def test_validate_official_untp_dpp_instance_full(self):
        """Test validating the official UNTP DPP 0.6.1 example with full validation."""
        fixture_path = FIXTURES_DIR / "valid" / "untp-dpp-instance-0.6.1.json"
        assert fixture_path.exists(), "Official UNTP DPP example fixture not found"
        data = json.loads(fixture_path.read_text())

        engine = ValidationEngine(schema_version="0.6.1")
        result = engine.validate(data)

        model_errors = [e for e in result.errors if e.layer == "model"]
        assert len(model_errors) == 0, f"Model validation errors: {model_errors}"
        assert result.valid is True, f"Validation failed: {result.errors}"

    def test_validate_official_untp_dpp_instance_structure(self):
        """Test that official UNTP DPP example has expected structure."""
        fixture_path = FIXTURES_DIR / "valid" / "untp-dpp-instance-0.6.1.json"
        assert fixture_path.exists(), "Official UNTP DPP example fixture not found"
        data = json.loads(fixture_path.read_text())

        assert "@context" in data, "Missing @context"
        assert "type" in data, "Missing type"
        assert "id" in data, "Missing id"
        assert "issuer" in data, "Missing issuer"
        assert "credentialSubject" in data, "Missing credentialSubject"
        assert "product" in data.get("credentialSubject", {}), (
            "Missing product in credentialSubject"
        )

    def test_validate_product_passport_instance(self):
        """Test validating the official UNTP ProductPassport 0.6.1 example."""
        from dppvalidator.models import ProductPassport

        fixture_path = FIXTURES_DIR / "valid" / "product_passport_instance_0.6.1.json"
        assert fixture_path.exists(), "ProductPassport example fixture not found"
        data = json.loads(fixture_path.read_text())

        assert "type" in data, "Missing type"
        assert "ProductPassport" in data["type"], "Missing ProductPassport type"
        assert "id" in data, "Missing id"
        assert "product" in data, "Missing product"

        passport = ProductPassport.model_validate(data)
        assert passport is not None
        assert passport.product is not None
        assert passport.product.name == "EV battery 300Ah."


class TestValidationEngineExtended:
    """Extended tests for ValidationEngine."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        """Create validation engine (model + semantic only)."""
        return ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])

    def test_validate_file(self, engine: ValidationEngine):
        """Test validate_file method."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "@context": [
                        "https://www.w3.org/ns/credentials/v2",
                        "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
                    ],
                    "id": "https://example.com/dpp",
                    "issuer": {"id": "https://example.com/issuer", "name": "Test"},
                },
                f,
            )
            f.flush()
            result = engine.validate_file(f.name)
            assert result.valid is True

    def test_validate_file_not_found(self, engine: ValidationEngine):
        """Test validate_file with non-existent file."""
        result = engine.validate(Path("/non/existent/file.json"))
        assert result.valid is False
        assert any("File not found" in e.message for e in result.errors)

    def test_validate_file_invalid_json(self, engine: ValidationEngine):
        """Test validate_file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            f.flush()
            result = engine.validate_file(f.name)
            assert result.valid is False
            assert any("Invalid JSON" in e.message for e in result.errors)

    def test_validate_string_invalid_json(self, engine: ValidationEngine):
        """Test validate with invalid JSON string."""
        result = engine.validate("{invalid json")
        assert result.valid is False
        assert any("Invalid JSON" in e.message for e in result.errors)

    def test_validate_async(self, engine: ValidationEngine):
        """Test async validation."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        result = asyncio.run(engine.validate_async(data))
        assert result.valid is True

    def test_validate_batch(self, engine: ValidationEngine):
        """Test batch validation."""
        ctx = [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ]
        items = [
            {
                "@context": ctx,
                "id": "https://example.com/dpp1",
                "issuer": {"id": "https://a.com", "name": "A"},
            },
            {
                "@context": ctx,
                "id": "https://example.com/dpp2",
                "issuer": {"id": "https://b.com", "name": "B"},
            },
        ]
        results = asyncio.run(engine.validate_batch(items, concurrency=2))
        assert len(results) == 2
        assert all(r.valid for r in results)

    def test_validate_with_max_errors(self, engine: ValidationEngine):
        """Test validation stops at max_errors."""
        data = {"invalid": "data"}
        result = engine.validate(data, max_errors=1)
        assert result.valid is False

    def test_engine_layers_config(self):
        """Test engine with specific layers."""
        engine = ValidationEngine(layers=["model"])
        data = {"id": "https://example.com/dpp", "issuer": {"id": "https://a.com", "name": "A"}}
        result = engine.validate(data)
        assert result is not None

    def test_engine_strict_mode(self):
        """Test engine with strict mode."""
        engine = ValidationEngine(strict_mode=True)
        assert engine.strict_mode is True


class TestEngineEdgeCases:
    """Edge case tests for ValidationEngine."""

    def test_validate_with_only_semantic_layer(self):
        """Test validation with only semantic layer."""
        engine = ValidationEngine(layers=["semantic"])
        data = {"id": "https://example.com/dpp", "issuer": {"id": "https://a.com", "name": "A"}}
        result = engine.validate(data)
        assert result is not None

    def test_validate_with_only_schema_layer(self):
        """Test validation with only schema layer."""
        engine = ValidationEngine(layers=["schema"])
        data = {"id": "https://example.com/dpp"}
        result = engine.validate(data)
        assert result is not None


class TestEngineFullCoverage:
    """Full coverage tests for ValidationEngine."""

    def test_engine_max_errors_stops_early(self):
        """Test engine stops collecting errors at max_errors."""
        engine = ValidationEngine()
        data = {}
        result = engine.validate(data, max_errors=1)
        assert result.valid is False

    def test_engine_fail_fast_in_schema_layer(self):
        """Test fail_fast stops after schema layer."""
        engine = ValidationEngine(layers=["schema", "model"])
        data = {}
        result = engine.validate(data, fail_fast=True)
        assert result is not None

    def test_validate_with_all_layers_disabled(self):
        """Test validation with empty layers list returns result."""
        engine = ValidationEngine(layers=[])
        data = {"id": "https://example.com/dpp", "issuer": {"id": "https://a.com", "name": "A"}}
        result = engine.validate(data)
        assert result is not None

    def test_semantic_layer_skipped_without_passport(self):
        """Test semantic layer skipped when model parsing fails."""
        engine = ValidationEngine(layers=["model", "semantic"])
        data = {}
        result = engine.validate(data)
        assert result.valid is False


class TestValidationEngineBehavior:
    """Behavior tests for ValidationEngine."""

    def test_engine_validates_real_dpp_structure(self):
        """Test engine validates a complete DPP with all components."""
        engine = ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp/001",
            "issuer": {
                "id": "https://example.com/issuer",
                "name": "Test Corporation",
            },
            "credentialSubject": {
                "product": {
                    "id": "https://example.com/product/001",
                    "name": "Test Product",
                    "serialNumber": "SN-001",
                },
                "materialsProvenance": [
                    {"name": "Steel", "massFraction": 0.6},
                    {"name": "Plastic", "massFraction": 0.4},
                ],
            },
        }
        result = engine.validate(data)
        assert result.valid is True
        assert result.passport is not None
        assert result.passport.credential_subject is not None
        assert result.passport.credential_subject.product is not None
        assert result.passport.credential_subject.product.name == "Test Product"

    def test_engine_collects_multiple_errors(self):
        """Test engine collects multiple validation errors."""
        engine = ValidationEngine(schema_version="0.6.1")
        data = {
            "id": "invalid-uri",
        }
        result = engine.validate(data)
        assert result.valid is False
        assert len(result.errors) >= 1

    def test_engine_result_contains_timing_info(self):
        """Test engine result includes timing information."""
        engine = ValidationEngine(schema_version="0.6.1")
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        result = engine.validate(data)
        assert result.parse_time_ms >= 0
        assert result.validated_at is not None

    def test_engine_with_unsupported_input_type(self):
        """Test engine handles unsupported input types gracefully."""
        engine = ValidationEngine(schema_version="0.6.1")
        result = engine.validate(12345)  # type: ignore
        assert result.valid is False
        assert any("Unsupported input type" in e.message for e in result.errors)


class TestValidationEngineEdgeCases:
    """Edge case tests for ValidationEngine."""

    def test_validate_empty_dict(self):
        """Test validation with empty dictionary."""
        engine = ValidationEngine()
        result = engine.validate({})
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_with_all_layers_disabled(self):
        """Test validation with empty layers list."""
        engine = ValidationEngine(layers=[])
        result = engine.validate({"id": "test"})
        assert result is not None

    def test_validate_dict_input(self):
        """Test validation accepts dict input directly."""
        engine = ValidationEngine(layers=["model", "semantic"])
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://a.com", "name": "Test"},
        }
        result = engine.validate(data)
        assert result.valid is True

    def test_validate_path_input_invalid_path(self):
        """Test validation with Path that doesn't exist."""
        engine = ValidationEngine()
        result = engine.validate(Path("/nonexistent/path/to/file.json"))
        assert result.valid is False
        assert any("File not found" in e.message for e in result.errors)


class TestPhase2Features:
    """Tests for Phase 2 features."""

    def test_engine_strict_mode_passed_to_schema_validator(self):
        """Test ValidationEngine passes strict_mode to SchemaValidator."""
        engine = ValidationEngine(strict_mode=True, layers=["schema"])
        assert engine._schema_validator.strict is True

        engine_normal = ValidationEngine(strict_mode=False, layers=["schema"])
        assert engine_normal._schema_validator.strict is False

    def test_engine_validate_vocabularies_initializes_loader(self):
        """Test validate_vocabularies=True initializes vocabulary loader."""
        engine = ValidationEngine(validate_vocabularies=True, layers=["model"])
        assert engine._vocab_loader is not None

        engine_no_vocab = ValidationEngine(validate_vocabularies=False, layers=["model"])
        assert engine_no_vocab._vocab_loader is None

    def test_engine_load_plugins_initializes_registry(self):
        """Test load_plugins=True initializes plugin registry."""
        engine = ValidationEngine(load_plugins=True, layers=["model"])
        assert engine._plugin_registry is not None

        engine_no_plugins = ValidationEngine(load_plugins=False, layers=["model"])
        assert engine_no_plugins._plugin_registry is None


class TestPhase3InputSizeLimits:
    """Tests for Phase 3: Input size limits for DoS protection."""

    def test_default_max_input_size(self):
        """Test default max input size is 10 MB."""
        engine = ValidationEngine()
        assert engine.max_input_size == 10 * 1024 * 1024

    def test_custom_max_input_size(self):
        """Test custom max input size can be set."""
        engine = ValidationEngine(max_input_size=1000)
        assert engine.max_input_size == 1000

    def test_disable_input_size_limit(self):
        """Test input size limit can be disabled with 0."""
        engine = ValidationEngine(max_input_size=0)
        assert engine.max_input_size == 0

    def test_input_size_exceeded_returns_error(self):
        """Test that exceeding input size returns validation error."""
        engine = ValidationEngine(max_input_size=100, layers=[])
        large_input = '{"data": "' + "x" * 200 + '"}'

        result = engine.validate(large_input)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "PRS004"
        assert "exceeds maximum" in result.errors[0].message

    def test_input_within_size_limit_passes(self):
        """Test that input within size limit is processed normally."""
        engine = ValidationEngine(max_input_size=10000, layers=["model", "semantic"])
        small_input = json.dumps(
            {
                "@context": [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
                ],
                "id": "https://example.com/dpp",
                "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            }
        )

        result = engine.validate(small_input)
        assert result.valid is True

    def test_dict_input_bypasses_size_check(self):
        """Test that dict input is not size-checked (already in memory)."""
        engine = ValidationEngine(max_input_size=1, layers=[])
        result = engine.validate({"large": "data" * 1000})

        assert not any(e.code == "PRS004" for e in result.errors)

    def test_disabled_size_limit_allows_large_input(self):
        """Test that disabled size limit (0) allows any size input."""
        engine = ValidationEngine(max_input_size=0, layers=[])
        large_input = '{"data": "' + "x" * 100000 + '"}'

        result = engine.validate(large_input)
        assert not any(e.code == "PRS004" for e in result.errors)
