"""Tests for ModelValidator."""

from dppvalidator.validators.model import ModelValidator


class TestModelValidator:
    """Tests for ModelValidator."""

    def test_validate_valid_data(self):
        """Test validating valid data."""
        validator = ModelValidator()
        data = {"id": "https://example.com/dpp", "issuer": {"id": "https://a.com", "name": "A"}}
        result = validator.validate(data)
        assert result.valid is True
        assert result.passport is not None

    def test_validate_invalid_data(self):
        """Test validating invalid data."""
        validator = ModelValidator()
        data = {"invalid": "data"}
        result = validator.validate(data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_loc_to_path_with_index(self):
        """Test _loc_to_path with array index."""
        validator = ModelValidator()
        path = validator._loc_to_path(("items", 0, "name"))
        assert path == "$.items[0].name"

    def test_safe_input_with_long_string(self):
        """Test _safe_input truncates long values."""
        validator = ModelValidator()
        long_dict = {"key": "x" * 200}
        result = validator._safe_input(long_dict)
        assert "..." in result

    def test_safe_input_with_none(self):
        """Test _safe_input with None."""
        validator = ModelValidator()
        assert validator._safe_input(None) is None

    def test_safe_input_with_primitives(self):
        """Test _safe_input with primitive types."""
        validator = ModelValidator()
        assert validator._safe_input("test") == "test"
        assert validator._safe_input(42) == 42
        assert validator._safe_input(3.14) == 3.14
        assert validator._safe_input(True) is True


class TestModelValidatorEdgeCases:
    """Edge case tests for ModelValidator."""

    def test_safe_input_with_object(self):
        """Test _safe_input with custom object."""
        validator = ModelValidator()

        class CustomObj:
            def __str__(self):
                return "x" * 200

        result = validator._safe_input(CustomObj())
        assert len(result) <= 100
