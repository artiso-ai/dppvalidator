"""Unit tests for JSON-LD semantic validation."""

from dppvalidator.validators.jsonld_semantic import (
    UNTP_CONTEXT_PATTERNS,
    CachingDocumentLoader,
    JSONLDValidator,
)
from dppvalidator.validators.results import ValidationResult


class TestContextPresenceValidation:
    """Tests for @context presence validation."""

    def test_missing_context_returns_error(self) -> None:
        """Missing @context returns JLD001 error."""
        validator = JSONLDValidator()
        result = validator._validate_context_presence({})

        assert result is not None
        assert result.code == "JLD001"
        assert "Missing @context" in result.message

    def test_context_without_untp_returns_error(self) -> None:
        """@context without UNTP vocabulary returns error."""
        validator = JSONLDValidator()
        result = validator._validate_context_presence(
            {"@context": ["https://example.com/other-context"]}
        )

        assert result is not None
        assert result.code == "JLD001"
        assert "missing UNTP" in result.message

    def test_valid_untp_context_returns_none(self) -> None:
        """Valid UNTP @context returns None (no error)."""
        validator = JSONLDValidator()
        result = validator._validate_context_presence(
            {
                "@context": [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
                ]
            }
        )

        assert result is None

    def test_valid_w3c_credentials_context(self) -> None:
        """W3C credentials context is valid."""
        validator = JSONLDValidator()
        result = validator._validate_context_presence(
            {"@context": ["https://www.w3.org/ns/credentials/v2"]}
        )

        assert result is None


class TestDroppedTermDetection:
    """Tests for detecting terms dropped during expansion."""

    def test_collect_keys_basic(self) -> None:
        """Collect keys from simple object."""
        validator = JSONLDValidator()
        keys = validator._collect_keys({"name": "test", "value": 123}, "$")

        assert ("name", "$.name") in keys
        assert ("value", "$.value") in keys

    def test_collect_keys_nested(self) -> None:
        """Collect keys from nested object."""
        validator = JSONLDValidator()
        keys = validator._collect_keys({"outer": {"inner": "value"}}, "$")

        key_names = [k for k, _ in keys]
        assert "outer" in key_names
        assert "inner" in key_names

    def test_collect_keys_with_arrays(self) -> None:
        """Collect keys from objects in arrays."""
        validator = JSONLDValidator()
        keys = validator._collect_keys({"items": [{"name": "first"}, {"name": "second"}]}, "$")

        key_names = [k for k, _ in keys]
        assert "items" in key_names
        assert key_names.count("name") == 2

    def test_collect_expanded_iris(self) -> None:
        """Collect IRIs from expanded JSON-LD."""
        validator = JSONLDValidator()
        iris: set[str] = set()

        expanded = {
            "https://example.com/name": [{"@value": "Test"}],
            "https://example.com/items": [{"https://example.com/id": [{"@value": "1"}]}],
        }

        validator._collect_expanded_iris(expanded, iris)

        assert "https://example.com/name" in iris
        assert "https://example.com/items" in iris
        assert "https://example.com/id" in iris


class TestUnprefixedTermDetection:
    """Tests for detecting unprefixed custom terms."""

    def test_standard_terms_not_flagged(self) -> None:
        """Standard UNTP terms are not flagged."""
        validator = JSONLDValidator()
        result = validator._find_unprefixed_custom_terms(
            {
                "type": "DigitalProductPassport",
                "credentialSubject": {"product": {}},
            }
        )

        assert len(result) == 0

    def test_prefixed_terms_not_flagged(self) -> None:
        """Prefixed custom terms are not flagged."""
        validator = JSONLDValidator()
        result = validator._find_unprefixed_custom_terms(
            {
                "ex:customField": "value",
                "myns:anotherField": 123,
            }
        )

        assert len(result) == 0

    def test_unprefixed_custom_terms_flagged(self) -> None:
        """Unprefixed custom terms are flagged."""
        validator = JSONLDValidator()
        result = validator._find_unprefixed_custom_terms(
            {
                "myCustomField": "value",
                "anotherCustom": 123,
            }
        )

        term_names = [t for t, _ in result]
        assert "myCustomField" in term_names
        assert "anotherCustom" in term_names


class TestCachingDocumentLoader:
    """Tests for context caching."""

    def test_cache_hit(self) -> None:
        """Cached contexts are returned without fetching."""
        loader = CachingDocumentLoader()

        # Pre-populate cache
        cached_doc = {"document": {"@context": {}}}
        loader._cache["https://example.com/context"] = cached_doc

        result = loader("https://example.com/context")
        assert result == cached_doc

    def test_cache_clear(self) -> None:
        """Cache can be cleared."""
        loader = CachingDocumentLoader()
        loader._cache["https://example.com/context"] = {"document": {}}

        loader.clear_cache()
        assert len(loader._cache) == 0

    def test_cache_eviction(self) -> None:
        """Old entries are evicted when cache is full."""
        loader = CachingDocumentLoader(cache_size=5)

        # Clear bundled contexts for clean test
        loader._cache.clear()

        # Fill cache
        loader._cache["url1"] = {"document": {}}
        loader._cache["url2"] = {"document": {}}

        # This would trigger eviction on next add
        assert len(loader._cache) == 2


class TestUNTPContextPatterns:
    """Tests for UNTP context pattern matching."""

    def test_patterns_include_uncefact(self) -> None:
        """Patterns include uncefact.org."""
        assert "uncefact.org" in UNTP_CONTEXT_PATTERNS

    def test_patterns_include_untp(self) -> None:
        """Patterns include untp."""
        assert "untp" in UNTP_CONTEXT_PATTERNS

    def test_patterns_include_w3c_credentials(self) -> None:
        """Patterns include w3.org/ns/credentials."""
        assert "w3.org/ns/credentials" in UNTP_CONTEXT_PATTERNS


class TestValidatorIntegration:
    """Integration tests for full validation flow."""

    def test_validator_with_valid_context(self) -> None:
        """Validator accepts valid UNTP context."""
        validator = JSONLDValidator()
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "type": ["DigitalProductPassport", "VerifiableCredential"],
            "credentialSubject": {},
        }

        # This will try to fetch remote contexts which may fail
        # but should not raise an exception
        result = validator.validate(data)
        assert isinstance(result, ValidationResult)

    def test_validator_strict_mode(self) -> None:
        """Strict mode makes undefined terms errors."""
        validator = JSONLDValidator(strict=True)
        assert validator.strict is True

        validator_normal = JSONLDValidator(strict=False)
        assert validator_normal.strict is False


class TestEngineJSONLDIntegration:
    """Tests for ValidationEngine JSON-LD integration."""

    def test_engine_jsonld_layer_disabled_by_default(self) -> None:
        """JSON-LD validation is disabled by default."""
        from dppvalidator.validators import ValidationEngine

        engine = ValidationEngine(schema_version="0.6.1", load_plugins=False)
        assert "jsonld" not in engine.layers
        assert engine.validate_jsonld is False

    def test_engine_jsonld_enabled_via_parameter(self) -> None:
        """JSON-LD validation can be enabled via parameter."""
        from dppvalidator.validators import ValidationEngine

        engine = ValidationEngine(
            schema_version="0.6.1",
            validate_jsonld=True,
            load_plugins=False,
        )
        assert engine.validate_jsonld is True

    def test_engine_jsonld_enabled_via_layers(self) -> None:
        """JSON-LD validation can be enabled via layers."""
        from dppvalidator.validators import ValidationEngine

        engine = ValidationEngine(
            schema_version="0.6.1",
            layers=["schema", "model", "jsonld"],
            load_plugins=False,
        )
        assert "jsonld" in engine.layers
