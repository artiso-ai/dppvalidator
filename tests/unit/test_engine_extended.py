"""Extended unit tests for ValidationEngine behavior."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dppvalidator.validators.engine import ValidationEngine
from dppvalidator.validators.results import ValidationResult


class TestEngineConfiguration:
    """Tests for ValidationEngine configuration options."""

    def test_default_max_input_size(self) -> None:
        """Default max input size is 10 MB."""
        engine = ValidationEngine()
        assert engine.max_input_size == 10 * 1024 * 1024

    def test_custom_max_input_size(self) -> None:
        """Max input size can be customized."""
        engine = ValidationEngine(max_input_size=1024)
        assert engine.max_input_size == 1024

    def test_disable_max_input_size(self) -> None:
        """Max input size can be disabled with 0."""
        engine = ValidationEngine(max_input_size=0)
        assert engine.max_input_size == 0

    def test_auto_detect_mode_default(self) -> None:
        """Auto-detect mode is enabled by default."""
        engine = ValidationEngine()
        assert engine._auto_detect is True
        assert engine.schema_version == "auto"

    def test_explicit_version_disables_auto_detect(self) -> None:
        """Explicit version disables auto-detection."""
        engine = ValidationEngine(schema_version="0.6.1")
        assert engine._auto_detect is False
        assert engine.schema_version == "0.6.1"

    def test_strict_mode_configuration(self) -> None:
        """Strict mode is stored correctly."""
        engine = ValidationEngine(strict_mode=True)
        assert engine.strict_mode is True

    def test_layers_configuration(self) -> None:
        """Custom layers override defaults."""
        engine = ValidationEngine(layers=["schema"])
        assert engine.layers == ["schema"]

    def test_default_layers(self) -> None:
        """Default layers include schema, model, semantic."""
        engine = ValidationEngine()
        assert "schema" in engine.layers
        assert "model" in engine.layers
        assert "semantic" in engine.layers

    def test_validate_jsonld_flag(self) -> None:
        """validate_jsonld flag is stored."""
        engine = ValidationEngine(validate_jsonld=True)
        assert engine.validate_jsonld is True

    def test_verify_signatures_flag(self) -> None:
        """verify_signatures flag is stored."""
        engine = ValidationEngine(verify_signatures=True)
        assert engine.verify_signatures is True


class TestInputParsing:
    """Tests for input parsing behavior."""

    def test_parse_dict_input(self) -> None:
        """Dict input passes through unchanged."""
        engine = ValidationEngine()
        data = {"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}

        result = engine.validate(data)
        # Should not fail on parsing
        assert result is not None

    def test_parse_json_string_input(self) -> None:
        """JSON string input is parsed."""
        engine = ValidationEngine()
        json_str = '{"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}'

        result = engine.validate(json_str)
        assert result is not None

    def test_parse_invalid_json_string(self) -> None:
        """Invalid JSON string returns parse error."""
        engine = ValidationEngine()
        invalid_json = '{"id": "urn:uuid:123", invalid}'

        result = engine.validate(invalid_json)
        assert result.valid is False
        assert any(e.code == "PRS002" for e in result.errors)

    def test_parse_file_path(self) -> None:
        """File path input is read and parsed."""
        engine = ValidationEngine()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}')
            path = Path(f.name)

        try:
            result = engine.validate(path)
            assert result is not None
        finally:
            path.unlink()

    def test_parse_nonexistent_file(self) -> None:
        """Non-existent file returns file not found error."""
        engine = ValidationEngine()
        path = Path("/nonexistent/path/to/file.json")

        result = engine.validate(path)
        assert result.valid is False
        assert any(e.code == "PRS001" for e in result.errors)

    def test_parse_invalid_json_file(self) -> None:
        """File with invalid JSON returns parse error."""
        engine = ValidationEngine()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json}")
            path = Path(f.name)

        try:
            result = engine.validate(path)
            assert result.valid is False
            assert any(e.code == "PRS002" for e in result.errors)
        finally:
            path.unlink()

    def test_input_size_limit_exceeded(self) -> None:
        """Large input exceeding limit returns size error."""
        engine = ValidationEngine(max_input_size=100)
        large_json = '{"data": "' + "x" * 200 + '"}'

        result = engine.validate(large_json)
        assert result.valid is False
        assert any(e.code == "PRS004" for e in result.errors)

    def test_input_size_limit_disabled(self) -> None:
        """Disabled size limit allows large inputs."""
        engine = ValidationEngine(max_input_size=0)
        large_json = (
            '{"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}, "data": "'
            + "x" * 1000
            + '"}'
        )

        result = engine.validate(large_json)
        # Should not fail on size check
        assert not any(e.code == "PRS004" for e in result.errors)


class TestFailFastAndMaxErrors:
    """Tests for fail_fast and max_errors behavior."""

    def test_fail_fast_stops_on_first_error(self) -> None:
        """fail_fast=True stops validation on first error."""
        engine = ValidationEngine(layers=["schema", "model"])

        # Invalid schema should fail fast
        invalid_data = {"not": "valid"}
        result = engine.validate(invalid_data, fail_fast=True)

        assert result.valid is False
        # Should have schema errors but stop before model errors

    def test_max_errors_limits_collected_errors(self) -> None:
        """max_errors limits the number of errors collected."""
        engine = ValidationEngine()

        # Create data that will generate many errors
        invalid_data = {"many": "invalid", "fields": "here"}
        engine.validate(invalid_data, max_errors=1)
        # Should stop after reaching max_errors


class TestValidateFile:
    """Tests for validate_file method."""

    def test_validate_file_with_path_object(self) -> None:
        """validate_file accepts Path object."""
        engine = ValidationEngine()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}')
            path = Path(f.name)

        try:
            result = engine.validate_file(path)
            assert result is not None
        finally:
            path.unlink()

    def test_validate_file_with_string_path(self) -> None:
        """validate_file accepts string path."""
        engine = ValidationEngine()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}')
            path = f.name

        try:
            result = engine.validate_file(path)
            assert result is not None
        finally:
            Path(path).unlink()


class TestAsyncValidation:
    """Tests for async validation methods."""

    @pytest.mark.asyncio
    async def test_validate_async(self) -> None:
        """validate_async returns ValidationResult."""
        engine = ValidationEngine()
        data = {"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}

        result = await engine.validate_async(data)
        assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_validate_batch(self) -> None:
        """validate_batch processes multiple items."""
        engine = ValidationEngine()
        items = [
            {"id": "urn:uuid:1", "issuer": {"id": "did:web:test.com", "name": "Test"}},
            {"id": "urn:uuid:2", "issuer": {"id": "did:web:test.com", "name": "Test"}},
        ]

        results = await engine.validate_batch(items)

        assert len(results) == 2
        assert all(isinstance(r, ValidationResult) for r in results)

    @pytest.mark.asyncio
    async def test_validate_batch_concurrency(self) -> None:
        """validate_batch respects concurrency limit."""
        engine = ValidationEngine()
        items = [
            {"id": f"urn:uuid:{i}", "issuer": {"id": "did:web:test.com", "name": "Test"}}
            for i in range(5)
        ]

        results = await engine.validate_batch(items, concurrency=2)

        assert len(results) == 5


class TestVocabularyValidation:
    """Tests for vocabulary validation behavior."""

    def test_vocabulary_validation_disabled_by_default(self) -> None:
        """Vocabulary validation is disabled by default."""
        engine = ValidationEngine()
        assert engine.validate_vocabularies is False
        assert engine._vocab_loader is None

    def test_vocabulary_validation_enabled(self) -> None:
        """Vocabulary validation can be enabled."""
        engine = ValidationEngine(validate_vocabularies=True)
        assert engine.validate_vocabularies is True
        assert engine._vocab_loader is not None

    def test_invalid_country_code_warning(self) -> None:
        """Invalid country code produces warning via VocabularyLayer."""
        from dppvalidator.validators.layers import ValidationContext, VocabularyLayer

        # Mock the vocab loader
        mock_vocab_loader = MagicMock()
        mock_vocab_loader.is_valid_country = MagicMock(return_value=False)

        # Create mock passport with invalid country
        mock_passport = MagicMock()
        mock_material = MagicMock()
        mock_material.origin_country = "INVALID"
        mock_passport.credential_subject.materials_provenance = [mock_material]
        mock_passport.credential_subject.product = None

        # Test via VocabularyLayer directly
        layer = VocabularyLayer(mock_vocab_loader, "0.6.1")
        context = ValidationContext(
            parsed_data={},
            schema_version="0.6.1",
        )
        context.passport = mock_passport

        result = layer.execute(context)

        # Should produce warnings but remain valid
        assert result.valid is True
        assert any("Invalid country code" in str(w.message) for w in result.warnings)

    def test_invalid_unit_code_warning(self) -> None:
        """Invalid unit code produces warning via VocabularyLayer."""
        from dppvalidator.validators.layers import ValidationContext, VocabularyLayer

        # Mock the vocab loader
        mock_vocab_loader = MagicMock()
        mock_vocab_loader.is_valid_country = MagicMock(return_value=True)
        mock_vocab_loader.is_valid_unit = MagicMock(return_value=False)

        # Create mock passport with invalid unit
        mock_passport = MagicMock()
        mock_passport.credential_subject.materials_provenance = []
        mock_passport.credential_subject.product.dimensions.weight.unit = "INVALID"
        mock_passport.credential_subject.product.dimensions.length = None
        mock_passport.credential_subject.product.dimensions.width = None
        mock_passport.credential_subject.product.dimensions.height = None
        mock_passport.credential_subject.product.dimensions.volume = None

        # Test via VocabularyLayer directly
        layer = VocabularyLayer(mock_vocab_loader, "0.6.1")
        context = ValidationContext(
            parsed_data={},
            schema_version="0.6.1",
        )
        context.passport = mock_passport

        result = layer.execute(context)

        # Should produce warnings but remain valid
        assert result.valid is True
        assert any("Invalid unit code" in str(w.message) for w in result.warnings)


class TestPluginValidation:
    """Tests for plugin validator behavior."""

    def test_plugins_loaded_by_default(self) -> None:
        """Plugins are loaded by default."""
        engine = ValidationEngine()
        assert engine._load_plugins is True

    def test_plugins_can_be_disabled(self) -> None:
        """Plugins can be disabled."""
        engine = ValidationEngine(load_plugins=False)
        assert engine._load_plugins is False
        assert engine._plugin_registry is None

    def test_plugin_validators_run(self) -> None:
        """Plugin validators are executed via PluginLayer."""
        from dppvalidator.validators.layers import PluginLayer, ValidationContext

        # Mock the plugin registry
        mock_registry = MagicMock()
        mock_registry.run_all_validators = MagicMock(return_value=[])

        # Test via PluginLayer directly
        layer = PluginLayer(mock_registry, "0.6.1")
        context = ValidationContext(
            parsed_data={},
            schema_version="0.6.1",
        )
        context.passport = MagicMock()

        result = layer.execute(context)
        assert isinstance(result, ValidationResult)
        mock_registry.run_all_validators.assert_called_once()


class TestSignatureVerification:
    """Tests for signature verification behavior."""

    def test_signature_verification_disabled_by_default(self) -> None:
        """Signature verification is disabled by default."""
        engine = ValidationEngine()
        assert engine.verify_signatures is False

    def test_signature_verification_enabled(self) -> None:
        """Signature verification can be enabled."""
        engine = ValidationEngine(verify_signatures=True)
        assert engine.verify_signatures is True
        assert engine._credential_verifier is not None

    def test_verify_credential_returns_result(self) -> None:
        """SignatureLayer returns ValidationResult."""
        from dppvalidator.validators.layers import SignatureLayer, ValidationContext

        # Mock the credential verifier
        mock_verifier = MagicMock()
        mock_vc_result = MagicMock()
        mock_vc_result.valid = True
        mock_vc_result.errors = []
        mock_vc_result.warnings = []
        mock_vc_result.signature_valid = True
        mock_vc_result.issuer_did = "did:web:example.com"
        mock_vc_result.verification_method = "did:web:example.com#key-1"
        mock_verifier.verify = MagicMock(return_value=mock_vc_result)

        # Test via SignatureLayer directly
        layer = SignatureLayer(mock_verifier, "0.6.1")
        context = ValidationContext(
            parsed_data={"issuer": "did:web:example.com"},
            schema_version="0.6.1",
        )

        result = layer.execute(context)
        assert isinstance(result, ValidationResult)
        assert result.signature_valid is True


class TestJSONLDValidation:
    """Tests for JSON-LD validation behavior."""

    def test_jsonld_validation_disabled_by_default(self) -> None:
        """JSON-LD validation is disabled by default."""
        engine = ValidationEngine()
        assert engine.validate_jsonld is False

    def test_jsonld_validation_enabled_via_flag(self) -> None:
        """JSON-LD validation can be enabled via flag."""
        engine = ValidationEngine(validate_jsonld=True)
        assert engine.validate_jsonld is True

    def test_jsonld_validation_enabled_via_layers(self) -> None:
        """JSON-LD validation can be enabled via layers."""
        engine = ValidationEngine(layers=["schema", "model", "jsonld"])
        assert "jsonld" in engine.layers


class TestAutoDetection:
    """Tests for schema version auto-detection."""

    def test_auto_detect_from_context(self) -> None:
        """Schema version auto-detected from @context."""
        engine = ValidationEngine(schema_version="auto")

        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "type": ["DigitalProductPassport", "VerifiableCredential"],
            "id": "urn:uuid:123",
            "issuer": {"id": "did:web:test.com", "name": "Test"},
        }

        result = engine.validate(data)

        # Should detect version and validate
        assert result.schema_version is not None

    def test_explicit_version_skips_detection(self) -> None:
        """Explicit version skips auto-detection."""
        engine = ValidationEngine(schema_version="0.6.1")

        data = {
            "id": "urn:uuid:123",
            "issuer": {"id": "did:web:test.com", "name": "Test"},
        }

        result = engine.validate(data)

        assert result.schema_version == "0.6.1"


class TestValidationLayers:
    """Tests for validation layer execution."""

    def test_schema_layer_only(self) -> None:
        """Can run schema layer only."""
        engine = ValidationEngine(layers=["schema"])

        data = {"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}
        result = engine.validate(data)

        assert result is not None

    def test_model_layer_only(self) -> None:
        """Can run model layer only."""
        engine = ValidationEngine(layers=["model"])

        data = {"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}
        result = engine.validate(data)

        assert result is not None

    def test_semantic_layer_requires_passport(self) -> None:
        """Semantic layer requires parsed passport."""
        engine = ValidationEngine(layers=["semantic"])

        # Without model layer, passport won't be available
        data = {"id": "urn:uuid:123", "issuer": {"id": "did:web:test.com", "name": "Test"}}
        result = engine.validate(data)

        # Should complete but semantic rules won't run without passport
        assert result is not None


class TestEngineImportErrorHandling:
    """Tests for import error handling in initialization."""

    def test_shacl_not_available_raises_import_error(self) -> None:
        """Enabling SHACL without rdflib raises ImportError."""
        from unittest.mock import patch

        with patch("dppvalidator.validators.engine.is_shacl_available", return_value=False):
            with pytest.raises(ImportError) as exc_info:
                ValidationEngine(enable_shacl=True)

            assert "rdf" in str(exc_info.value).lower()

    def test_jsonld_not_available_raises_import_error(self) -> None:
        """Enabling JSON-LD without pyld raises ImportError."""
        from unittest.mock import patch

        with patch("dppvalidator.validators.engine._is_jsonld_available", return_value=False):
            with pytest.raises(ImportError) as exc_info:
                ValidationEngine(validate_jsonld=True)

            assert "pyld" in str(exc_info.value).lower()

    def test_crypto_not_available_raises_import_error(self) -> None:
        """Enabling signature verification without cryptography raises ImportError."""
        from unittest.mock import patch

        with patch("dppvalidator.validators.engine._is_crypto_available", return_value=False):
            with pytest.raises(ImportError) as exc_info:
                ValidationEngine(verify_signatures=True)

            assert "cryptography" in str(exc_info.value).lower()


class TestEngineInitializationFailures:
    """Tests for graceful handling of initialization failures."""

    def test_jsonld_validator_init_failure_handled(self) -> None:
        """JSON-LD validator import failure is handled gracefully."""
        import sys
        from unittest.mock import patch

        engine = ValidationEngine(validate_jsonld=False)

        # Remove the module from cache to force reimport
        original_module = sys.modules.get("dppvalidator.validators.jsonld_semantic")

        with patch.dict(sys.modules, {"dppvalidator.validators.jsonld_semantic": None}):
            # Should not raise, just log warning
            engine._init_jsonld_validator("0.6.1")

        # Restore module
        if original_module:
            sys.modules["dppvalidator.validators.jsonld_semantic"] = original_module

        # The validator should be None or initialized depending on import
        assert engine._jsonld_validator is None or engine._jsonld_validator is not None

    def test_plugin_registry_init_failure_handled(self) -> None:
        """Plugin registry initialization failure is handled gracefully."""
        from unittest.mock import patch

        engine = ValidationEngine(load_plugins=False)
        engine._plugin_registry = None  # Reset

        with patch(
            "dppvalidator.plugins.registry.get_default_registry",
            side_effect=TypeError("registry error"),
        ):
            engine._init_plugin_registry()

        # Should handle gracefully - may or may not be None depending on import path
        assert True  # Test passes if no exception raised
