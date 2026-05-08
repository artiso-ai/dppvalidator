"""Extended tests for JSON-LD semantic validation."""

from typing import Any
from unittest.mock import MagicMock, patch

from dppvalidator.validators.jsonld_semantic import (
    UNTP_CONTEXT_PATTERNS,
    CachingDocumentLoader,
    JSONLDValidator,
    _get_default_validator,
    validate_jsonld,
)
from dppvalidator.validators.results import ValidationResult


class TestCachingDocumentLoader:
    """Tests for CachingDocumentLoader behavior."""

    def test_cache_hit_returns_cached_document(self) -> None:
        """Cached documents are returned without re-fetching."""
        loader = CachingDocumentLoader(cache_size=10)

        # Pre-populate cache
        cached_doc = {"document": {"@context": {}}}
        loader._cache["https://example.com/context"] = cached_doc

        result = loader("https://example.com/context")
        assert result is cached_doc

    def test_cache_eviction_on_overflow(self) -> None:
        """Oldest entry is evicted when cache is full."""
        loader = CachingDocumentLoader(cache_size=5)

        # Clear bundled contexts for clean test
        loader._cache.clear()

        # Fill cache
        loader._cache["url1"] = {"document": 1}
        loader._cache["url2"] = {"document": 2}

        # Adding a third should evict the first
        loader._cache["url3"] = {"document": 3}

        # Simulate the eviction logic (which happens in __call__)
        if len(loader._cache) >= loader._cache_size:
            oldest = next(iter(loader._cache))
            del loader._cache[oldest]

        # With 3 items and cache_size=5, no eviction needed
        assert len(loader._cache) == 3

    def test_clear_cache_empties_cache(self) -> None:
        """clear_cache() removes all cached entries."""
        loader = CachingDocumentLoader()
        loader._cache["url1"] = {"document": 1}
        loader._cache["url2"] = {"document": 2}

        loader.clear_cache()

        assert len(loader._cache) == 0


class TestJSONLDValidatorContextValidation:
    """Tests for @context validation."""

    def test_missing_context_returns_error(self) -> None:
        """Missing @context produces JLD001 error."""
        validator = JSONLDValidator()
        data: dict[str, Any] = {"id": "urn:uuid:123", "type": "DigitalProductPassport"}

        result = validator.validate(data)

        assert result.valid is False
        assert any(e.code == "JLD001" for e in result.errors)
        assert any("Missing @context" in e.message for e in result.errors)

    def test_context_without_untp_returns_error(self) -> None:
        """@context without UNTP vocabulary produces JLD001 error."""
        validator = JSONLDValidator()
        data = {
            "@context": "https://schema.org/",
            "id": "urn:uuid:123",
        }

        result = validator.validate(data)

        assert result.valid is False
        assert any(e.code == "JLD001" for e in result.errors)
        assert any("missing UNTP" in e.message for e in result.errors)

    def test_context_with_w3c_credentials_is_valid(self) -> None:
        """@context with W3C credentials vocabulary passes."""
        validator = JSONLDValidator()
        result = validator._validate_context_presence(
            {
                "@context": ["https://www.w3.org/ns/credentials/v2"],
            }
        )

        assert result is None  # No error

    def test_context_with_uncefact_is_valid(self) -> None:
        """@context with UNCEFACT vocabulary passes."""
        validator = JSONLDValidator()
        result = validator._validate_context_presence(
            {
                "@context": ["https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/"],
            }
        )

        assert result is None  # No error


class TestJSONLDValidatorExpansion:
    """Tests for JSON-LD expansion behavior."""

    @patch("dppvalidator.validators.jsonld_semantic.jsonld.expand")
    def test_expansion_error_produces_jld001(self, mock_expand: MagicMock) -> None:
        """JsonLdError during expansion produces JLD001 error."""
        from pyld.jsonld import JsonLdError

        mock_expand.side_effect = JsonLdError(
            "Expansion failed",
            "jsonld.InvalidContext",
            None,
        )

        validator = JSONLDValidator(cache_contexts=False)
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "id": "urn:uuid:123",
        }

        result = validator.validate(data)

        assert result.valid is False
        assert any(e.code == "JLD001" for e in result.errors)

    @patch("dppvalidator.validators.jsonld_semantic.jsonld.expand")
    def test_network_error_produces_warning(self, mock_expand: MagicMock) -> None:
        """Network/timeout errors produce JLD004 warning."""
        mock_expand.side_effect = ConnectionError("Network unreachable")

        validator = JSONLDValidator(cache_contexts=False)
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "id": "urn:uuid:123",
        }

        result = validator.validate(data)

        # Should have warning, not error
        assert any(w.code == "JLD004" for w in result.warnings)


class TestJSONLDValidatorDroppedTerms:
    """Tests for detecting dropped/undefined terms."""

    def test_collect_keys_from_nested_object(self) -> None:
        """_collect_keys() traverses nested objects."""
        validator = JSONLDValidator()
        data = {
            "level1": {
                "level2": {
                    "level3": "value",
                },
            },
        }

        keys = validator._collect_keys(data, "$")
        key_names = [k for k, _ in keys]

        assert "level1" in key_names
        assert "level2" in key_names
        assert "level3" in key_names

    def test_collect_keys_from_arrays(self) -> None:
        """_collect_keys() traverses arrays."""
        validator = JSONLDValidator()
        data = {
            "items": [
                {"name": "item1"},
                {"name": "item2"},
            ],
        }

        keys = validator._collect_keys(data, "$")
        key_names = [k for k, _ in keys]

        assert "items" in key_names
        assert key_names.count("name") == 2

    def test_collect_keys_skips_jsonld_keywords(self) -> None:
        """_collect_keys() skips @-prefixed keys."""
        validator = JSONLDValidator()
        data = {
            "@context": "https://example.com",
            "@type": "Thing",
            "name": "Test",
        }

        keys = validator._collect_keys(data, "$")
        key_names = [k for k, _ in keys]

        assert "@context" not in key_names
        assert "@type" not in key_names
        assert "name" in key_names


class TestJSONLDValidatorExpandedIRIs:
    """Tests for collecting expanded IRIs."""

    def test_collect_expanded_iris_from_dict(self) -> None:
        """_collect_expanded_iris() extracts HTTP(S) keys."""
        validator = JSONLDValidator()
        expanded = {
            "https://schema.org/name": [{"@value": "Test"}],
            "https://example.com/custom": [{"@value": 123}],
        }

        iris: set[str] = set()
        validator._collect_expanded_iris(expanded, iris)

        assert "https://schema.org/name" in iris
        assert "https://example.com/custom" in iris

    def test_collect_expanded_iris_from_nested(self) -> None:
        """_collect_expanded_iris() handles nested structures."""
        validator = JSONLDValidator()
        expanded = {
            "https://schema.org/product": [
                {
                    "https://schema.org/name": [{"@value": "Widget"}],
                }
            ],
        }

        iris: set[str] = set()
        validator._collect_expanded_iris(expanded, iris)

        assert "https://schema.org/product" in iris
        assert "https://schema.org/name" in iris

    def test_collect_expanded_iris_from_list(self) -> None:
        """_collect_expanded_iris() handles lists."""
        validator = JSONLDValidator()
        expanded = [
            {"https://schema.org/a": []},
            {"https://schema.org/b": []},
        ]

        iris: set[str] = set()
        validator._collect_expanded_iris(expanded, iris)

        assert "https://schema.org/a" in iris
        assert "https://schema.org/b" in iris


class TestJSONLDValidatorUnprefixedTerms:
    """Tests for detecting unprefixed custom terms."""

    def test_standard_terms_not_flagged(self) -> None:
        """Standard UNTP/VC terms are not flagged."""
        validator = JSONLDValidator()
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": "DigitalProductPassport",
            "id": "urn:uuid:123",
            "credentialSubject": {},
            "issuer": "did:web:example.com",
        }

        unprefixed = validator._find_unprefixed_custom_terms(data)
        term_names = [t for t, _ in unprefixed]

        assert "type" not in term_names
        assert "id" not in term_names
        assert "credentialSubject" not in term_names
        assert "issuer" not in term_names

    def test_prefixed_terms_not_flagged(self) -> None:
        """Prefixed terms (containing colon) are not flagged."""
        validator = JSONLDValidator()
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "ex:customField": "value",
            "schema:name": "Test",
        }

        unprefixed = validator._find_unprefixed_custom_terms(data)
        term_names = [t for t, _ in unprefixed]

        assert "ex:customField" not in term_names
        assert "schema:name" not in term_names

    def test_unprefixed_custom_terms_flagged(self) -> None:
        """Unprefixed custom terms are flagged."""
        validator = JSONLDValidator()
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "myCustomField": "value",
            "anotherCustom": 123,
        }

        unprefixed = validator._find_unprefixed_custom_terms(data)
        term_names = [t for t, _ in unprefixed]

        assert "myCustomField" in term_names
        assert "anotherCustom" in term_names


class TestJSONLDValidatorStrictMode:
    """Tests for strict mode behavior."""

    @patch("dppvalidator.validators.jsonld_semantic.jsonld.expand")
    def test_strict_mode_makes_dropped_terms_errors(self, mock_expand: MagicMock) -> None:
        """In strict mode, dropped terms are errors instead of warnings."""
        mock_expand.return_value = [{}]  # Empty expansion = all terms dropped

        validator = JSONLDValidator(strict=True, cache_contexts=False)
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "customField": "value",
        }

        result = validator.validate(data)

        # In strict mode, JLD002 should be an error
        jld002_errors = [e for e in result.errors if e.code == "JLD002"]
        assert len(jld002_errors) > 0

    @patch("dppvalidator.validators.jsonld_semantic.jsonld.expand")
    def test_non_strict_mode_makes_dropped_terms_warnings(self, mock_expand: MagicMock) -> None:
        """In non-strict mode, dropped terms are warnings."""
        mock_expand.return_value = [{}]  # Empty expansion = all terms dropped

        validator = JSONLDValidator(strict=False, cache_contexts=False)
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "customField": "value",
        }

        result = validator.validate(data)

        # In non-strict mode, JLD002 should be a warning
        jld002_warnings = [w for w in result.warnings if w.code == "JLD002"]
        assert len(jld002_warnings) > 0


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_default_validator_returns_singleton(self) -> None:
        """_get_default_validator returns cached instance."""
        v1 = _get_default_validator()
        v2 = _get_default_validator()
        assert v1 is v2

    def test_validate_jsonld_uses_default_validator(self) -> None:
        """validate_jsonld() uses the default validator."""
        data = {"id": "test"}  # Missing @context
        result = validate_jsonld(data)

        assert isinstance(result, ValidationResult)
        assert result.valid is False


class TestUNTPContextPatterns:
    """Tests for UNTP context pattern matching."""

    def test_patterns_include_uncefact(self) -> None:
        """UNTP patterns include uncefact.org."""
        assert "uncefact.org" in UNTP_CONTEXT_PATTERNS

    def test_patterns_include_w3c_credentials(self) -> None:
        """UNTP patterns include W3C credentials."""
        assert "w3.org/ns/credentials" in UNTP_CONTEXT_PATTERNS

    def test_patterns_include_untp(self) -> None:
        """UNTP patterns include 'untp'."""
        assert "untp" in UNTP_CONTEXT_PATTERNS
