"""Tests for ValidationResult and ValidationError."""

import json

import pytest

from dppvalidator.validators import ValidationResult
from dppvalidator.validators.results import ValidationError, ValidationException


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_empty_result_is_valid(self):
        """Test that empty result is valid."""
        result = ValidationResult(valid=True, schema_version="0.6.1")
        assert result.valid is True
        assert len(result.errors) == 0

    def test_result_with_error_is_invalid(self):
        """Test that result with error is invalid."""
        errors = [
            ValidationError(
                path="$.issuer",
                message="Missing required field",
                code="REQUIRED",
                layer="model",
            )
        ]
        result = ValidationResult(valid=False, errors=errors, schema_version="0.6.1")
        assert result.valid is False
        assert len(result.errors) == 1

    def test_result_with_warning_is_valid(self):
        """Test that result with warning only is still valid."""
        warnings = [
            ValidationError(
                path="$.field",
                message="Recommended field missing",
                code="SEM005",
                layer="semantic",
                severity="warning",
            )
        ]
        result = ValidationResult(valid=True, warnings=warnings, schema_version="0.6.1")
        assert result.valid is True
        assert len(result.warnings) == 1

    def test_result_to_json(self):
        """Test JSON serialization."""
        result = ValidationResult(valid=True, schema_version="0.6.1")
        json_str = result.to_json()
        data = json.loads(json_str)
        assert data["valid"] is True
        assert data["schema_version"] == "0.6.1"

    def test_result_merge(self):
        """Test merging two results."""
        result1 = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.a", message="Error A", code="E1", layer="model")],
            schema_version="0.6.1",
        )
        result2 = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.b", message="Error B", code="E2", layer="model")],
            schema_version="0.6.1",
        )
        merged = result1.merge(result2)
        assert len(merged.errors) == 2


class TestValidationResultExtended:
    """Extended tests for ValidationResult."""

    def test_error_count(self):
        """Test error_count property."""
        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(path="$.a", message="A", code="E1", layer="model"),
                ValidationError(path="$.b", message="B", code="E2", layer="model"),
            ],
            schema_version="0.6.1",
        )
        assert result.error_count == 2

    def test_warning_count(self):
        """Test warning_count property."""
        result = ValidationResult(
            valid=True,
            warnings=[
                ValidationError(
                    path="$.a", message="A", code="W1", layer="model", severity="warning"
                ),
            ],
            schema_version="0.6.1",
        )
        assert result.warning_count == 1

    def test_all_issues(self):
        """Test all_issues property combines all."""
        result = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.a", message="A", code="E1", layer="model")],
            warnings=[
                ValidationError(
                    path="$.b", message="B", code="W1", layer="model", severity="warning"
                )
            ],
            info=[
                ValidationError(path="$.c", message="C", code="I1", layer="model", severity="info")
            ],
            schema_version="0.6.1",
        )
        assert len(result.all_issues) == 3

    def test_raise_for_errors(self):
        """Test raise_for_errors raises ValidationException."""
        result = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.a", message="Error", code="E1", layer="model")],
            schema_version="0.6.1",
        )
        with pytest.raises(ValidationException) as exc_info:
            result.raise_for_errors()
        assert exc_info.value.result == result
        assert "Error" in str(exc_info.value)

    def test_raise_for_errors_valid(self):
        """Test raise_for_errors does nothing for valid result."""
        result = ValidationResult(valid=True, schema_version="0.6.1")
        result.raise_for_errors()  # Should not raise

    def test_repr_valid_result(self):
        """Test __repr__ for valid result."""
        result = ValidationResult(valid=True, schema_version="0.6.1")
        repr_str = repr(result)
        assert "ValidationResult" in repr_str
        assert "valid=True" in repr_str

    def test_repr_invalid_result(self):
        """Test __repr__ for invalid result with errors."""
        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(path="$.a", message="A", code="E1", layer="model"),
                ValidationError(path="$.b", message="B", code="E2", layer="model"),
            ],
            schema_version="0.6.1",
        )
        repr_str = repr(result)
        assert "ValidationResult" in repr_str
        assert "valid=False" in repr_str
        assert "errors=2" in repr_str


class TestValidationError:
    """Tests for ValidationError dataclass."""

    def test_error_to_dict(self):
        """Test ValidationError to_dict method."""
        error = ValidationError(
            path="$.issuer",
            message="Missing field",
            code="E001",
            layer="model",
            severity="error",
            context={"type": "missing"},
        )
        d = error.to_dict()
        assert d["path"] == "$.issuer"
        assert d["message"] == "Missing field"
        assert d["code"] == "E001"
        assert d["layer"] == "model"
        assert d["context"]["type"] == "missing"

    def test_error_with_suggestion(self):
        """Test ValidationError with suggestion."""
        error = ValidationError(
            path="$.field",
            message="Invalid value",
            code="E002",
            layer="model",
            suggestion="Use a valid URI",
        )
        d = error.to_dict()
        assert d["suggestion"] == "Use a valid URI"

    def test_error_with_did_you_mean(self):
        """Test ValidationError with did_you_mean."""
        error = ValidationError(
            path="$.field",
            message="Invalid value",
            code="E002",
            layer="model",
            did_you_mean=("option1", "option2"),
        )
        d = error.to_dict()
        assert d["did_you_mean"] == ["option1", "option2"]
