"""Tests for enhanced validation error messages."""

import pytest

from dppvalidator.validators.errors import (
    DOCS_BASE_URL,
    ERROR_REGISTRY,
    KNOWN_VALUES,
    EnhancedValidationError,
    ErrorSuggestion,
    enhance_error,
    find_similar_values,
    format_error_for_display,
    get_error_docs_url,
    get_error_suggestion,
)


class TestErrorSuggestion:
    """Tests for ErrorSuggestion dataclass."""

    def test_suggestion_with_text_only(self):
        """Suggestion can be created with just text."""
        suggestion = ErrorSuggestion(text="Fix the issue")
        assert suggestion.text == "Fix the issue"
        assert suggestion.example is None

    def test_suggestion_with_example(self):
        """Suggestion can include an example."""
        suggestion = ErrorSuggestion(
            text="Add the required field",
            example='"issuer": {"id": "https://example.com", "name": "Test"}',
        )
        assert suggestion.text == "Add the required field"
        assert "issuer" in suggestion.example

    def test_suggestion_is_immutable(self):
        """ErrorSuggestion should be frozen (immutable)."""
        suggestion = ErrorSuggestion(text="Test")
        with pytest.raises(AttributeError):
            suggestion.text = "Modified"


class TestEnhancedValidationError:
    """Tests for EnhancedValidationError dataclass."""

    def test_minimal_error_creation(self):
        """Error can be created with minimal required fields."""
        error = EnhancedValidationError(
            path="$.issuer",
            message="Missing required field",
            code="MDL001",
            layer="model",
        )
        assert error.path == "$.issuer"
        assert error.message == "Missing required field"
        assert error.code == "MDL001"
        assert error.layer == "model"
        assert error.severity == "error"  # default

    def test_error_with_all_fields(self):
        """Error can include all optional fields."""
        suggestion = ErrorSuggestion(text="Add issuer", example='"issuer": {...}')
        error = EnhancedValidationError(
            path="$.issuer",
            message="Missing issuer",
            code="MDL001",
            layer="model",
            severity="warning",
            suggestion=suggestion,
            docs_url="https://docs.example.com/MDL001",
            did_you_mean=["issuer", "issuers"],
            context={"expected_type": "object"},
        )
        assert error.severity == "warning"
        assert error.suggestion == suggestion
        assert "MDL001" in error.docs_url
        assert "issuer" in error.did_you_mean

    def test_error_to_dict_minimal(self):
        """to_dict() works with minimal fields."""
        error = EnhancedValidationError(
            path="$",
            message="Error",
            code="ERR001",
            layer="schema",
        )
        result = error.to_dict()

        assert result["path"] == "$"
        assert result["message"] == "Error"
        assert result["code"] == "ERR001"
        assert result["layer"] == "schema"
        assert result["severity"] == "error"
        assert "suggestion" not in result
        assert "docs_url" not in result
        assert "did_you_mean" not in result

    def test_error_to_dict_with_suggestion(self):
        """to_dict() includes suggestion when present."""
        error = EnhancedValidationError(
            path="$",
            message="Error",
            code="ERR001",
            layer="schema",
            suggestion=ErrorSuggestion(text="Fix it", example="example code"),
        )
        result = error.to_dict()

        assert "suggestion" in result
        assert result["suggestion"]["text"] == "Fix it"
        assert result["suggestion"]["example"] == "example code"

    def test_error_to_dict_with_did_you_mean(self):
        """to_dict() includes did_you_mean when non-empty."""
        error = EnhancedValidationError(
            path="$",
            message="Error",
            code="ERR001",
            layer="schema",
            did_you_mean=["option1", "option2"],
        )
        result = error.to_dict()

        assert "did_you_mean" in result
        assert result["did_you_mean"] == ["option1", "option2"]

    def test_error_is_immutable(self):
        """EnhancedValidationError should be frozen (immutable)."""
        error = EnhancedValidationError(path="$", message="Test", code="ERR", layer="model")
        with pytest.raises(AttributeError):
            error.path = "$.modified"


class TestGetErrorDocsUrl:
    """Tests for get_error_docs_url function."""

    def test_generates_url_for_known_code(self):
        """Generates documentation URL for known error codes."""
        url = get_error_docs_url("SEM001")
        assert url == f"{DOCS_BASE_URL}/SEM001"

    def test_generates_url_for_unknown_code(self):
        """Generates URL even for unknown error codes."""
        url = get_error_docs_url("UNKNOWN999")
        assert url == f"{DOCS_BASE_URL}/UNKNOWN999"


class TestGetErrorSuggestion:
    """Tests for get_error_suggestion function."""

    def test_returns_suggestion_for_known_code(self):
        """Returns suggestion for registered error codes."""
        suggestion = get_error_suggestion("SEM001")
        assert suggestion is not None
        assert "mass fraction" in suggestion.text.lower()

    def test_returns_none_for_unknown_code(self):
        """Returns None for unregistered error codes."""
        suggestion = get_error_suggestion("UNKNOWN999")
        assert suggestion is None

    def test_suggestion_includes_example_when_available(self):
        """Includes example from registry when available."""
        suggestion = get_error_suggestion("MDL002")
        assert suggestion is not None
        assert suggestion.example is not None
        assert "https://" in suggestion.example


class TestFindSimilarValues:
    """Tests for find_similar_values typo correction."""

    def test_finds_similar_type_values(self):
        """Finds similar values for typos in 'type' field."""
        matches = find_similar_values("DigitalProductPasport", "type")
        assert "DigitalProductPassport" in matches

    def test_finds_similar_granularity_values(self):
        """Finds similar granularity level values."""
        matches = find_similar_values("itme", "granularityLevel")
        assert "item" in matches

    def test_finds_similar_scope_values(self):
        """Finds similar operational scope values."""
        matches = find_similar_values("Scope1", "operationalScope")
        assert "Scope1" in matches

    def test_returns_empty_for_unknown_field(self):
        """Returns empty list for unknown field names."""
        matches = find_similar_values("value", "unknownField")
        assert matches == []

    def test_returns_empty_for_very_different_value(self):
        """Returns empty list when no close matches exist."""
        matches = find_similar_values("xyzabc123", "type")
        assert matches == []

    def test_respects_cutoff_threshold(self):
        """Respects similarity cutoff threshold."""
        # With high cutoff, fewer matches
        matches_strict = find_similar_values("Digita", "type", cutoff=0.9)
        matches_loose = find_similar_values("Digita", "type", cutoff=0.4)
        assert len(matches_loose) >= len(matches_strict)


class TestEnhanceError:
    """Tests for enhance_error factory function."""

    def test_creates_enhanced_error_with_defaults(self):
        """Creates enhanced error with suggestion and docs URL."""
        error = enhance_error(
            path="$.materials[0].massFraction",
            message="Mass fractions do not sum to 1.0",
            code="SEM001",
            layer="semantic",
        )
        assert error.path == "$.materials[0].massFraction"
        assert error.docs_url is not None
        assert error.suggestion is not None

    def test_includes_did_you_mean_for_typos(self):
        """Includes 'did you mean' suggestions for typos."""
        error = enhance_error(
            path="$.type",
            message="Invalid type value",
            code="SCH003",
            layer="schema",
            invalid_value="DigitalProductPasport",
            field_name="type",
        )
        assert "DigitalProductPassport" in error.did_you_mean

    def test_includes_context_when_provided(self):
        """Includes additional context in error."""
        error = enhance_error(
            path="$",
            message="Error",
            code="ERR001",
            layer="model",
            context={"expected": "string", "got": "integer"},
        )
        assert error.context["expected"] == "string"
        assert error.context["got"] == "integer"

    def test_supports_all_severity_levels(self):
        """Supports error, warning, and info severity levels."""
        for severity in ["error", "warning", "info"]:
            error = enhance_error(
                path="$",
                message="Test",
                code="TEST",
                layer="model",
                severity=severity,
            )
            assert error.severity == severity


class TestFormatErrorForDisplay:
    """Tests for format_error_for_display function."""

    def test_formats_minimal_error(self):
        """Formats error with just path and message."""
        error = EnhancedValidationError(
            path="$.issuer",
            message="Missing required field",
            code="MDL001",
            layer="model",
        )
        output = format_error_for_display(error)

        assert "[MDL001]" in output
        assert "$.issuer" in output
        assert "Missing required field" in output

    def test_formats_error_with_did_you_mean(self):
        """Includes 'did you mean' in formatted output."""
        error = EnhancedValidationError(
            path="$.type",
            message="Invalid value",
            code="SCH003",
            layer="schema",
            did_you_mean=["DigitalProductPassport", "VerifiableCredential"],
        )
        output = format_error_for_display(error)

        assert "Did you mean" in output
        assert "DigitalProductPassport" in output

    def test_formats_error_with_suggestion(self):
        """Includes suggestion and example in formatted output."""
        error = EnhancedValidationError(
            path="$",
            message="Error",
            code="SEM001",
            layer="semantic",
            suggestion=ErrorSuggestion(
                text="Adjust fractions to sum to 1.0",
                example='"massFraction": 0.5',
            ),
        )
        output = format_error_for_display(error)

        assert "💡" in output
        assert "Adjust fractions" in output
        assert "Example:" in output
        assert "massFraction" in output

    def test_formats_error_with_docs_url(self):
        """Includes documentation URL in formatted output."""
        error = EnhancedValidationError(
            path="$",
            message="Error",
            code="SEM001",
            layer="semantic",
            docs_url="https://docs.example.com/errors/SEM001",
        )
        output = format_error_for_display(error)

        assert "📖" in output
        assert "https://docs.example.com/errors/SEM001" in output


class TestErrorRegistry:
    """Tests for ERROR_REGISTRY coverage."""

    def test_all_registered_codes_have_required_fields(self):
        """All registered error codes have title and suggestion."""
        for code, info in ERROR_REGISTRY.items():
            assert "title" in info, f"{code} missing title"
            assert "suggestion" in info, f"{code} missing suggestion"

    def test_parse_errors_registered(self):
        """Parse error codes (PRS*) are registered."""
        assert "PRS001" in ERROR_REGISTRY
        assert "PRS002" in ERROR_REGISTRY
        assert "PRS003" in ERROR_REGISTRY

    def test_schema_errors_registered(self):
        """Schema error codes (SCH*) are registered."""
        assert "SCH001" in ERROR_REGISTRY
        assert "SCH002" in ERROR_REGISTRY
        assert "SCH003" in ERROR_REGISTRY

    def test_model_errors_registered(self):
        """Model error codes (MDL*) are registered."""
        assert "MDL001" in ERROR_REGISTRY
        assert "MDL002" in ERROR_REGISTRY
        assert "MDL003" in ERROR_REGISTRY

    def test_semantic_errors_registered(self):
        """Semantic error codes (SEM*) are registered."""
        assert "SEM001" in ERROR_REGISTRY
        assert "SEM002" in ERROR_REGISTRY
        assert "SEM003" in ERROR_REGISTRY


class TestKnownValues:
    """Tests for KNOWN_VALUES vocabulary."""

    def test_type_values_include_dpp(self):
        """Type values include DigitalProductPassport."""
        assert "DigitalProductPassport" in KNOWN_VALUES["type"]
        assert "VerifiableCredential" in KNOWN_VALUES["type"]

    def test_granularity_levels_defined(self):
        """Granularity levels are defined."""
        assert "item" in KNOWN_VALUES["granularityLevel"]
        assert "batch" in KNOWN_VALUES["granularityLevel"]
        assert "model" in KNOWN_VALUES["granularityLevel"]

    def test_operational_scopes_defined(self):
        """Operational scopes are defined."""
        assert "Scope1" in KNOWN_VALUES["operationalScope"]
        assert "CradleToGrave" in KNOWN_VALUES["operationalScope"]
