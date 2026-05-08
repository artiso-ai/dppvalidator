"""Unit tests for schema version auto-detection."""

from dppvalidator.validators.detection import (
    detect_schema_version,
    is_dpp_document,
)


class TestDetectSchemaVersion:
    """Tests for detect_schema_version function."""

    def test_detect_from_schema_url_061(self) -> None:
        """Detect version from $schema URL (0.6.1)."""
        data = {
            "$schema": "https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.1.json",
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.6.1"

    def test_detect_from_schema_url_060(self) -> None:
        """Detect version from $schema URL (0.6.0)."""
        data = {
            "$schema": "https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.0.json",
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.6.0"

    def test_detect_from_context_url_061(self) -> None:
        """Detect version from @context URL (0.6.1)."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.6.1"

    def test_detect_from_context_url_060(self) -> None:
        """Detect version from @context URL (0.6.0)."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
            ],
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.6.0"

    def test_detect_from_context_string(self) -> None:
        """Detect version from @context as single string."""
        data = {
            "@context": "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.6.1"

    def test_schema_url_takes_priority_over_context(self) -> None:
        """$schema URL takes priority over @context."""
        data = {
            "$schema": "https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.1.json",
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
            ],
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.6.1"

    def test_detect_from_dpp_type_fallback(self) -> None:
        """Falls back to default when only type is present."""
        data = {
            "type": ["DigitalProductPassport", "VerifiableCredential"],
            "credentialSubject": {},
        }
        # Should return default (0.6.1) when type is DPP but no version info
        assert detect_schema_version(data) == "0.6.1"

    def test_detect_from_type_string(self) -> None:
        """Detect DPP from type as string (not array)."""
        data = {"type": "DigitalProductPassport"}
        assert detect_schema_version(data) == "0.6.1"

    def test_fallback_to_default_empty_data(self) -> None:
        """Falls back to default for empty data."""
        assert detect_schema_version({}) == "0.6.1"

    def test_fallback_to_default_unknown_version(self) -> None:
        """Falls back to default for unknown version in $schema."""
        data = {
            "$schema": "https://example.com/untp-dpp-schema-9.9.9.json",
            "type": ["DigitalProductPassport"],
        }
        # Unknown version 9.9.9 not in registry, should fallback
        assert detect_schema_version(data) == "0.6.1"

    def test_fallback_to_default_invalid_context(self) -> None:
        """Falls back to default for non-UNTP context."""
        data = {
            "@context": ["https://example.com/other-context"],
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.6.1"

    def test_handles_none_schema(self) -> None:
        """Handles None $schema value."""
        data = {"$schema": None, "type": ["DigitalProductPassport"]}
        assert detect_schema_version(data) == "0.6.1"

    def test_handles_none_context(self) -> None:
        """Handles None @context value."""
        data = {"@context": None, "type": ["DigitalProductPassport"]}
        assert detect_schema_version(data) == "0.6.1"

    # ---- UNTP 0.7.0 detection (Phase 1) ----------------------------------

    def test_detect_from_context_url_070_production(self) -> None:
        """Detect 0.7.0 from the production CloudFront context URL."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://vocabulary.uncefact.org/untp/0.7.0/context/",
            ],
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.7.0"

    def test_detect_from_context_url_070_no_trailing_slash(self) -> None:
        """``/context`` (no trailing slash) is also valid."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://vocabulary.uncefact.org/untp/0.7.0/context",
            ],
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.7.0"

    def test_detect_from_schema_url_070_modern(self) -> None:
        """Detect 0.7.0 from a modern ``…/v0.7.0/dpp/DigitalProductPassport.json`` URL."""
        data = {
            "$schema": (
                "https://opensource.unicc.org/un/unece/uncefact/spec-untp/-/raw/"
                "707cd5267deddede24bb74e453a758561972a109/artefacts/schema/v0.7.0/"
                "dpp/DigitalProductPassport.json"
            ),
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.7.0"

    def test_detect_from_schema_url_070_cloudfront(self) -> None:
        """Detect 0.7.0 from a CloudFront-style schema URL (no ``v`` prefix)."""
        data = {
            "$schema": (
                "https://vocabulary.uncefact.org/untp/0.7.0/schema/dpp/DigitalProductPassport.json"
            ),
            "type": ["DigitalProductPassport"],
        }
        assert detect_schema_version(data) == "0.7.0"

    def test_unregistered_modern_version_falls_back(self) -> None:
        """An unregistered version in a modern URL falls back to default."""
        data = {
            "$schema": ("https://example.com/foo/v9.9.9/bar/DigitalProductPassport.json"),
            "type": ["DigitalProductPassport"],
        }
        # 9.9.9 is not in SCHEMA_REGISTRY so detection ignores it.
        assert detect_schema_version(data) == "0.6.1"

    def test_detect_from_upstream_070_sample(self) -> None:
        """Real-world: vendored 0.7.0 sample is detected as 0.7.0."""
        import json
        from pathlib import Path

        sample_path = (
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "upstream"
            / "v0.7.0"
            / "samples"
            / "DigitalProductPassport_instance.json"
        )
        if not sample_path.is_file():  # pragma: no cover - vendored in Phase 0
            import pytest

            pytest.skip(
                "Upstream 0.7.0 sample missing; vendor via Phase 0 of "
                "docs/plans/UNTP_0.7.0_MIGRATION.md."
            )
        with sample_path.open() as f:
            data = json.load(f)
        assert detect_schema_version(data) == "0.7.0"


class TestIsDppDocument:
    """Tests for is_dpp_document function."""

    def test_dpp_with_type_array(self) -> None:
        """Identifies DPP from type array."""
        data = {"type": ["DigitalProductPassport", "VerifiableCredential"]}
        assert is_dpp_document(data) is True

    def test_dpp_with_type_string(self) -> None:
        """Identifies DPP from type string."""
        data = {"type": "DigitalProductPassport"}
        assert is_dpp_document(data) is True

    def test_dpp_with_credential_subject(self) -> None:
        """Identifies DPP from credentialSubject."""
        data = {"credentialSubject": {"product": {}}}
        assert is_dpp_document(data) is True

    def test_dpp_with_untp_context(self) -> None:
        """Identifies DPP from UNTP context."""
        data = {"@context": ["https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/"]}
        assert is_dpp_document(data) is True

    def test_dpp_with_uncefact_context(self) -> None:
        """Identifies DPP from UNCEFACT context."""
        data = {"@context": ["https://vocabulary.uncefact.org/something"]}
        assert is_dpp_document(data) is True

    def test_not_dpp_empty(self) -> None:
        """Empty dict is not identified as DPP."""
        assert is_dpp_document({}) is False

    def test_not_dpp_other_type(self) -> None:
        """Other credential types are not DPP."""
        data = {"type": ["OtherCredential"]}
        assert is_dpp_document(data) is False

    def test_not_dpp_non_dict(self) -> None:
        """Non-dict input returns False."""
        assert is_dpp_document("not a dict") is False  # type: ignore[arg-type]
        assert is_dpp_document(None) is False  # type: ignore[arg-type]
        assert is_dpp_document([]) is False  # type: ignore[arg-type]


class TestEngineAutoDetection:
    """Integration tests for ValidationEngine auto-detection."""

    def test_engine_auto_detect_from_context(self) -> None:
        """Engine auto-detects version from @context."""
        from dppvalidator.validators import ValidationEngine

        engine = ValidationEngine(schema_version="auto", load_plugins=False)

        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
            ],
            "type": ["DigitalProductPassport", "VerifiableCredential"],
            "credentialSubject": {},
        }

        result = engine.validate(data)
        assert result.schema_version == "0.6.0"

    def test_engine_auto_detect_default(self) -> None:
        """Engine defaults to auto-detection."""
        from dppvalidator.validators import ValidationEngine

        engine = ValidationEngine(load_plugins=False)
        assert engine._auto_detect is True

    def test_engine_explicit_version_no_auto(self) -> None:
        """Engine with explicit version disables auto-detection."""
        from dppvalidator.validators import ValidationEngine

        engine = ValidationEngine(schema_version="0.6.1", load_plugins=False)
        assert engine._auto_detect is False

    def test_engine_auto_detect_from_schema_url(self) -> None:
        """Engine auto-detects version from $schema URL."""
        from dppvalidator.validators import ValidationEngine

        engine = ValidationEngine(schema_version="auto", load_plugins=False)

        data = {
            "$schema": "https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.1.json",
            "type": ["DigitalProductPassport"],
            "credentialSubject": {},
        }

        result = engine.validate(data)
        assert result.schema_version == "0.6.1"
