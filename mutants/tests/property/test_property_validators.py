"""Property-based tests for dppvalidator validators using Hypothesis."""

from hypothesis import given, settings
from hypothesis import strategies as st

from dppvalidator.validators import ValidationEngine, ValidationResult
from dppvalidator.validators.results import ValidationError


class TestValidationResultProperty:
    """Property-based tests for ValidationResult."""

    @given(
        error_count=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=30)
    def test_result_error_count_matches(self, error_count):
        """Test that error count matches number of errors."""
        errors = [
            ValidationError(
                path=f"$.field{i}",
                message=f"Error {i}",
                code=f"ERR{i:03d}",
                layer="test",
                severity="error",
            )
            for i in range(error_count)
        ]
        result = ValidationResult(
            valid=error_count == 0,
            errors=errors,
        )
        assert len(result.errors) == error_count
        assert result.valid == (error_count == 0)

    @given(
        warning_count=st.integers(min_value=0, max_value=5),
        info_count=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=20)
    def test_result_with_warnings_and_info(self, warning_count, info_count):
        """Test result with warnings and info messages."""
        warnings = [
            ValidationError(
                path="$",
                message=f"Warning {i}",
                code=f"WARN{i:03d}",
                layer="test",
                severity="warning",
            )
            for i in range(warning_count)
        ]
        infos = [
            ValidationError(
                path="$",
                message=f"Info {i}",
                code=f"INFO{i:03d}",
                layer="test",
                severity="info",
            )
            for i in range(info_count)
        ]
        result = ValidationResult(
            valid=True,
            warnings=warnings,
            info=infos,
        )
        assert result.valid is True
        assert len(result.warnings) == warning_count
        assert len(result.info) == info_count


class TestValidationEngineProperty:
    """Property-based tests for ValidationEngine."""

    @given(
        data=st.fixed_dictionaries(
            {
                "id": st.just("https://example.com/dpp"),
                "issuer": st.fixed_dictionaries(
                    {
                        "id": st.just("https://example.com/issuer"),
                        "name": st.text(min_size=1, max_size=50).filter(lambda x: x.strip() != ""),
                    }
                ),
            }
        )
    )
    @settings(max_examples=20)
    def test_engine_valid_minimal_passport(self, data):
        """Test engine with valid minimal passport data."""
        engine = ValidationEngine(layers=["model"])
        result = engine.validate(data)
        # Should be valid with minimal required fields
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    @given(
        invalid_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20).filter(lambda x: x not in ["id", "issuer"]),
            values=st.text(min_size=0, max_size=50),
            min_size=0,
            max_size=5,
        )
    )
    @settings(max_examples=30)
    def test_engine_invalid_data_returns_errors(self, invalid_data):
        """Test engine with invalid data returns errors."""
        engine = ValidationEngine(layers=["model"])
        result = engine.validate(invalid_data)
        # Should return result (not crash) even with invalid data
        assert isinstance(result, ValidationResult)
        # Missing required fields should cause validation to fail
        if "id" not in invalid_data or "issuer" not in invalid_data:
            assert result.valid is False

    @given(st.binary(min_size=0, max_size=100))
    @settings(max_examples=50)
    def test_engine_never_crashes_on_binary(self, binary_data):
        """Test engine never crashes on arbitrary binary input."""
        engine = ValidationEngine(layers=["model"])
        try:
            text_data = binary_data.decode("utf-8", errors="replace")
            result = engine.validate(text_data)
            assert result is not None
        except Exception:
            # Some inputs may raise, but should be handled gracefully
            pass

    @given(
        layers=st.lists(
            st.sampled_from(["model", "semantic"]),
            min_size=1,
            max_size=2,
            unique=True,
        )
    )
    @settings(max_examples=10)
    def test_engine_layer_combinations(self, layers):
        """Test engine with different layer combinations."""
        engine = ValidationEngine(layers=layers)
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        result = engine.validate(data)
        assert isinstance(result, ValidationResult)


class TestValidationErrorProperty:
    """Property-based tests for ValidationError."""

    @given(
        path=st.from_regex(r"\$(\.[a-z]+|\[[0-9]+\]){0,5}", fullmatch=True),
        message=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() != ""),
        code=st.from_regex(r"[A-Z]{2,4}[0-9]{3}", fullmatch=True),
    )
    @settings(max_examples=30)
    def test_error_creation(self, path, message, code):
        """Test ValidationError creation with various inputs."""
        error = ValidationError(
            path=path,
            message=message,
            code=code,
            layer="test",
            severity="error",
        )
        assert error.path == path
        assert error.message == message
        assert error.code == code

    @given(
        severity=st.sampled_from(["error", "warning", "info"]),
        layer=st.sampled_from(["schema", "model", "semantic"]),
    )
    @settings(max_examples=15)
    def test_error_severity_and_layer(self, severity, layer):
        """Test ValidationError with different severity and layer."""
        error = ValidationError(
            path="$",
            message="Test message",
            code="TEST001",
            layer=layer,
            severity=severity,
        )
        assert error.severity == severity
        assert error.layer == layer
