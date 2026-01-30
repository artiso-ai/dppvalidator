"""Tests for error utilities: suggestions, documentation links, and typo correction."""

from dppvalidator.validators.errors import (
    DOCS_BASE_URL,
    ERROR_REGISTRY,
    KNOWN_VALUES,
    find_similar_values,
    get_error_docs_url,
    get_error_suggestion,
    get_suggestion_text,
)

# Note: EnhancedValidationError and ErrorSuggestion classes were removed in Phase 2.
# ValidationError in validators/results.py now has all needed fields (suggestion,
# docs_url, did_you_mean) and is the single error class used throughout the pipeline.


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
        assert "mass fraction" in suggestion["text"].lower()

    def test_returns_none_for_unknown_code(self):
        """Returns None for unregistered error codes."""
        suggestion = get_error_suggestion("UNKNOWN999")
        assert suggestion is None

    def test_suggestion_includes_example_when_available(self):
        """Includes example from registry when available."""
        suggestion = get_error_suggestion("MDL002")
        assert suggestion is not None
        assert suggestion["example"] is not None
        assert "https://" in suggestion["example"]


class TestGetSuggestionText:
    """Tests for get_suggestion_text convenience function."""

    def test_returns_text_for_known_code(self):
        """Returns suggestion text for registered error codes."""
        text = get_suggestion_text("SEM001")
        assert text is not None
        assert "mass fraction" in text.lower()

    def test_returns_none_for_unknown_code(self):
        """Returns None for unregistered error codes."""
        text = get_suggestion_text("UNKNOWN999")
        assert text is None


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
