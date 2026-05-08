"""Tests for dual-mode schema validation (Phase 6)."""

import pytest

from dppvalidator.validators.schema import SchemaType, SchemaValidator


class TestSchemaTypeEdgeCases:
    """Tests for schema_type validation edge cases."""

    def test_invalid_schema_type_raises_value_error(self):
        """Test invalid schema_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid schema_type"):
            SchemaValidator(schema_type="invalid")

    def test_none_schema_type_raises_error(self):
        """Test None schema_type raises error."""
        with pytest.raises((ValueError, TypeError)):
            SchemaValidator(schema_type=None)

    def test_empty_string_schema_type_raises_error(self):
        """Test empty string schema_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid schema_type"):
            SchemaValidator(schema_type="")

    def test_case_sensitive_schema_type(self):
        """Test schema_type is case-sensitive."""
        with pytest.raises(ValueError, match="Invalid schema_type"):
            SchemaValidator(schema_type="UNTP")

        with pytest.raises(ValueError, match="Invalid schema_type"):
            SchemaValidator(schema_type="Cirpass")


class TestSchemaType:
    """Tests for SchemaType literal."""

    def test_schema_type_untp(self):
        """Test UNTP schema type."""
        schema_type: SchemaType = "untp"
        assert schema_type == "untp"

    def test_schema_type_cirpass(self):
        """Test CIRPASS schema type."""
        schema_type: SchemaType = "cirpass"
        assert schema_type == "cirpass"


class TestSchemaValidatorDefaults:
    """Tests for SchemaValidator default behavior."""

    def test_default_schema_type_is_untp(self):
        """Test default schema type is UNTP."""
        validator = SchemaValidator()
        assert validator.schema_type == "untp"

    def test_default_schema_version(self):
        """Test default schema version."""
        validator = SchemaValidator()
        assert validator.schema_version == "0.6.1"

    def test_explicit_untp_mode(self):
        """Test explicit UNTP mode."""
        validator = SchemaValidator(schema_type="untp")
        assert validator.schema_type == "untp"


class TestCIRPASSMode:
    """Tests for CIRPASS schema mode."""

    def test_cirpass_mode_initialization(self):
        """Test CIRPASS mode initialization."""
        validator = SchemaValidator(schema_type="cirpass")
        assert validator.schema_type == "cirpass"

    def test_cirpass_mode_with_version(self):
        """Test CIRPASS mode with version."""
        validator = SchemaValidator(
            schema_type="cirpass",
            schema_version="1.3.0",
        )
        assert validator.schema_type == "cirpass"
        assert validator.schema_version == "1.3.0"

    def test_cirpass_schema_loads(self):
        """Test CIRPASS schema loads correctly."""
        validator = SchemaValidator(schema_type="cirpass")
        schema = validator._load_schema()

        assert schema is not None
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_cirpass_schema_has_dpp_properties(self):
        """Test CIRPASS schema has DPP properties."""
        validator = SchemaValidator(schema_type="cirpass")
        schema = validator._load_schema()

        properties = schema.get("properties", {})
        assert "uniqueDPPID" in properties
        assert "appliesToProduct" in properties


class TestUNTPMode:
    """Tests for UNTP schema mode."""

    def test_untp_mode_initialization(self):
        """Test UNTP mode initialization."""
        validator = SchemaValidator(schema_type="untp")
        assert validator.schema_type == "untp"

    def test_untp_schema_loads(self):
        """Test UNTP schema loads (or returns empty if not bundled)."""
        validator = SchemaValidator(schema_type="untp")
        schema = validator._load_schema()

        # Schema may be empty if not bundled, but should be a dict
        assert isinstance(schema, dict)


class TestDualModeValidation:
    """Tests for dual-mode validation behavior."""

    def test_cirpass_validation_valid_data(self):
        """Test CIRPASS validation with valid data structure."""
        validator = SchemaValidator(schema_type="cirpass")

        # Minimal valid CIRPASS DPP data
        data = {
            "uniqueDPPID": ["urn:uuid:12345678-1234-1234-1234-123456789012"],
        }

        result = validator.validate(data)
        # Should complete without exception
        assert result is not None

    def test_cirpass_validation_invalid_data(self):
        """Test CIRPASS validation detects invalid data."""
        validator = SchemaValidator(schema_type="cirpass")

        # Invalid data - uniqueDPPID should be array
        data = {
            "uniqueDPPID": "not-an-array",
            "unknownProperty": "should-fail-with-strict",
        }

        result = validator.validate(data)
        # Should have errors for type mismatch and additional properties
        assert not result.valid or len(result.errors) > 0 or len(result.warnings) > 0

    def test_strict_mode_with_cirpass(self):
        """Test strict mode works with CIRPASS schema."""
        validator = SchemaValidator(schema_type="cirpass", strict=True)
        schema = validator._load_schema()

        # In strict mode, additionalProperties should be false
        # (already false in CIRPASS schema)
        assert schema.get("additionalProperties") is False


class TestSchemaLoading:
    """Tests for schema loading methods."""

    def test_load_cirpass_schema_method(self):
        """Test _load_cirpass_schema method."""
        validator = SchemaValidator(schema_type="cirpass")
        schema = validator._load_cirpass_schema()

        assert isinstance(schema, dict)
        assert "title" in schema
        assert "CIRPASS" in schema.get("title", "")

    def test_load_untp_schema_method(self):
        """Test _load_untp_schema method."""
        validator = SchemaValidator(schema_type="untp")
        schema = validator._load_untp_schema()

        # May be empty if no bundled schema
        assert isinstance(schema, dict)

    def test_schema_caching(self):
        """Test schema is cached after first load."""
        validator = SchemaValidator(schema_type="cirpass")

        schema1 = validator._load_schema()
        schema2 = validator._load_schema()

        assert schema1 is schema2


class TestValidatorImports:
    """Tests for validator imports from package."""

    def test_import_schema_type_from_validators(self):
        """Test importing SchemaType from validators package."""
        from dppvalidator.validators import SchemaType, SchemaValidator

        assert SchemaType is not None
        assert SchemaValidator is not None

    def test_import_schema_type_from_schema_module(self):
        """Test importing SchemaType from schema module."""

        # Verify it's a type alias
        validator = SchemaValidator(schema_type="cirpass")
        assert validator.schema_type == "cirpass"


class TestBackwardsCompatibility:
    """Tests for backwards compatibility."""

    def test_existing_usage_unchanged(self):
        """Test existing usage pattern still works."""
        # This is how users currently create validators
        validator = SchemaValidator(schema_version="0.6.1")

        assert validator.schema_type == "untp"
        assert validator.schema_version == "0.6.1"

    def test_schema_path_override_still_works(self):
        """Test custom schema path still works."""
        import json
        import tempfile
        from pathlib import Path

        # Create a temporary schema file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"type": "object", "properties": {}}, f)
            temp_path = Path(f.name)

        try:
            validator = SchemaValidator(
                schema_type="cirpass",
                schema_path=temp_path,
            )
            schema = validator._load_schema()

            # Should use custom path, not bundled schema
            assert schema == {"type": "object", "properties": {}}
        finally:
            temp_path.unlink()

    def test_strict_mode_still_works(self):
        """Test strict mode still works."""
        validator = SchemaValidator(strict=True)

        assert validator.strict is True
