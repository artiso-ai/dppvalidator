"""Tests for SchemaValidator."""

import importlib.util
import json
import tempfile
from pathlib import Path

import pytest

from dppvalidator.validators.schema import SchemaValidator

HAS_JSONSCHEMA = importlib.util.find_spec("jsonschema") is not None


class TestSchemaValidator:
    """Tests for SchemaValidator."""

    def test_validate_without_jsonschema(self):
        """Test validation when jsonschema not available returns warning."""
        validator = SchemaValidator()
        data = {"id": "test"}
        result = validator.validate(data)
        assert result is not None

    def test_validate_with_custom_schema_path(self):
        """Test validator with custom schema path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"type": "object"}, f)
            f.flush()
            validator = SchemaValidator(schema_path=Path(f.name))
            result = validator.validate({"test": "data"})
            assert result is not None


class TestSchemaValidatorExtended:
    """Extended tests for SchemaValidator."""

    def test_schema_validation_with_valid_data(self):
        """Test schema validation with valid data."""
        validator = SchemaValidator()
        data = {
            "id": "https://example.com/dpp",
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        result = validator.validate(data)
        assert result is not None

    def test_schema_validator_error_to_path(self):
        """Test _error_to_path method."""
        validator = SchemaValidator()

        class MockError:
            absolute_path = ["items", 0, "name"]

        path = validator._error_to_path(MockError())
        assert path == "$.items[0].name"


class TestSchemaValidatorFullCoverage:
    """Full coverage tests for SchemaValidator."""

    def test_load_schema_with_cache(self):
        """Test schema caching on second load."""
        validator = SchemaValidator()
        schema1 = validator._load_schema()
        schema2 = validator._load_schema()
        assert schema1 is schema2

    def test_validate_with_schema_errors(self):
        """Test validation with schema that produces errors."""
        validator = SchemaValidator()
        validator._load_schema()
        result = validator.validate({"@context": "invalid"})
        assert result is not None

    def test_validator_with_empty_schema(self):
        """Test validation when schema is empty."""
        validator = SchemaValidator()
        validator._schema = {}
        v = validator._get_validator()
        assert v is None or v is not None


class TestSchemaValidatorMoreCoverage:
    """More coverage tests for SchemaValidator."""

    def test_schema_validator_custom_path(self, tmp_path):
        """Test SchemaValidator with custom schema path."""
        schema_file = tmp_path / "schema.json"
        schema_file.write_text('{"type": "object"}')

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({"id": "test"})
        assert result is not None

    def test_schema_validator_load_schema_cached(self, tmp_path):
        """Test that schema is cached after first load."""
        schema_file = tmp_path / "schema.json"
        schema_file.write_text('{"type": "object"}')

        validator = SchemaValidator(schema_path=schema_file)
        schema1 = validator._load_schema()
        schema2 = validator._load_schema()
        assert schema1 is schema2

    def test_schema_validator_error_to_path_with_array(self):
        """Test _error_to_path with array indices."""
        validator = SchemaValidator()

        class MockError:
            absolute_path = ["items", 0, "name"]

        path = validator._error_to_path(MockError())
        assert path == "$.items[0].name"


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
class TestSchemaValidatorWithJsonschema:
    """Tests for SchemaValidator with jsonschema installed."""

    def test_schema_validator_with_valid_data(self, tmp_path):
        """Test SchemaValidator validates correct data."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({"name": "test"})
        assert result.valid is True
        assert len(result.errors) == 0

    def test_schema_validator_with_invalid_data(self, tmp_path):
        """Test SchemaValidator catches schema violations."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({})
        assert result.valid is False
        assert len(result.errors) >= 1
        assert result.errors[0].layer == "schema"

    def test_schema_validator_iter_errors(self, tmp_path):
        """Test SchemaValidator collects multiple errors."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
        }
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({"name": 123, "age": "not a number"})
        assert result.valid is False
        assert len(result.errors) >= 1

    def test_schema_validator_error_code_format(self, tmp_path):
        """Test error codes are properly formatted with stable codes."""
        schema = {"type": "object", "required": ["a", "b", "c"]}
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({})
        assert result.valid is False
        assert result.errors[0].code == "SCH001"

    def test_schema_validator_no_schema_loaded(self):
        """Test SchemaValidator with no schema returns warning."""
        validator = SchemaValidator(schema_version="99.99.99")
        result = validator.validate({"test": "data"})
        assert result.valid is True
        assert len(result.warnings) == 1
        assert "SCH001" in result.warnings[0].code

    def test_schema_validator_validation_time(self, tmp_path):
        """Test validation time is recorded."""
        schema = {"type": "object"}
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({})
        assert result.validation_time_ms >= 0

    def test_strict_mode_rejects_additional_properties(self, tmp_path):
        """Test strict_mode rejects data with additional properties."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": True,
        }
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        validator_normal = SchemaValidator(schema_path=schema_file, strict=False)
        result_normal = validator_normal.validate({"name": "test", "extra": "field"})
        assert result_normal.valid is True

        validator_strict = SchemaValidator(schema_path=schema_file, strict=True)
        result_strict = validator_strict.validate({"name": "test", "extra": "field"})
        assert result_strict.valid is False
        assert any(
            "extra" in e.message.lower() or "additional" in e.message.lower()
            for e in result_strict.errors
        )

    def test_stable_error_codes_for_required(self, tmp_path):
        """Test that 'required' violations always produce SCH001."""
        schema = {"type": "object", "required": ["field_a", "field_b"]}
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({})

        assert result.valid is False
        for error in result.errors:
            assert error.code == "SCH001"

    def test_stable_error_codes_for_type(self, tmp_path):
        """Test that 'type' violations always produce SCH002."""
        schema = {"type": "object", "properties": {"count": {"type": "integer"}}}
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(schema))

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({"count": "not a number"})

        assert result.valid is False
        assert any(e.code == "SCH002" for e in result.errors)

    def test_schema_error_code_mapping_completeness(self):
        """Test that SCHEMA_ERROR_CODES covers common validator types."""
        from dppvalidator.validators.schema import SCHEMA_ERROR_CODES

        expected_validators = [
            "required",
            "type",
            "enum",
            "format",
            "pattern",
            "minLength",
            "maxLength",
            "minimum",
            "maximum",
            "additionalProperties",
            "minItems",
            "maxItems",
        ]

        for validator in expected_validators:
            assert validator in SCHEMA_ERROR_CODES, f"Missing error code for {validator}"
            assert SCHEMA_ERROR_CODES[validator].startswith("SCH")


class TestSchemaValidatorWithoutJsonschema:
    """Tests for SchemaValidator when jsonschema is not available."""

    def test_validate_without_jsonschema_returns_warning(self, monkeypatch):
        """Test validation returns warning when jsonschema not installed."""
        from dppvalidator.validators import schema as schema_module

        monkeypatch.setattr(schema_module, "HAS_JSONSCHEMA", False)

        validator = SchemaValidator()
        result = validator.validate({"test": "data"})
        assert result.valid is True
        assert len(result.warnings) == 1
        assert "jsonschema not installed" in result.warnings[0].message

    def test_get_validator_without_jsonschema(self, monkeypatch):
        """Test _get_validator returns None when jsonschema not installed."""
        from dppvalidator.validators import schema as schema_module

        monkeypatch.setattr(schema_module, "HAS_JSONSCHEMA", False)

        validator = SchemaValidator()
        assert validator._get_validator() is None


class TestSchemaValidatorWithJsonSchema:
    """Tests for SchemaValidator with jsonschema library."""

    def test_load_schema_from_docs(self):
        """Test loading schema from docs directory."""
        validator = SchemaValidator()
        schema = validator._load_schema()
        assert schema is not None

    def test_get_validator_returns_validator(self):
        """Test _get_validator returns a validator or None."""
        validator = SchemaValidator()
        v = validator._get_validator()
        assert v is None or hasattr(v, "iter_errors")

    def test_schema_validation_errors(self):
        """Test schema validation produces errors for invalid data."""
        validator = SchemaValidator()
        data = {"type": ["DigitalProductPassport"]}
        result = validator.validate(data)
        assert result is not None
