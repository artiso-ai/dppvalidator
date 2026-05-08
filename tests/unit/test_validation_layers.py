"""Tests for validation layer implementations."""

from unittest.mock import MagicMock

from dppvalidator.validators.layers import (
    JsonLdLayer,
    PluginLayer,
    SignatureLayer,
    ValidationContext,
    VocabularyLayer,
)


class TestJsonLdLayer:
    """Tests for JsonLdLayer."""

    def test_name_property(self) -> None:
        """JsonLdLayer name is 'jsonld'."""
        layer = JsonLdLayer(validator=None)
        assert layer.name == "jsonld"

    def test_should_run_without_validator(self) -> None:
        """JsonLdLayer should not run when validator is None."""
        layer = JsonLdLayer(validator=None)
        context = ValidationContext(parsed_data={}, schema_version="0.6.1")
        assert layer.should_run(context) is False

    def test_should_run_with_validator(self) -> None:
        """JsonLdLayer should run when validator is provided."""
        mock_validator = MagicMock()
        layer = JsonLdLayer(validator=mock_validator)
        context = ValidationContext(parsed_data={}, schema_version="0.6.1")
        assert layer.should_run(context) is True

    def test_execute_calls_validator(self) -> None:
        """JsonLdLayer.execute calls the validator."""
        mock_validator = MagicMock()
        mock_result = MagicMock()
        mock_validator.validate.return_value = mock_result

        layer = JsonLdLayer(validator=mock_validator)
        context = ValidationContext(parsed_data={"test": "data"}, schema_version="0.6.1")

        result = layer.execute(context)

        mock_validator.validate.assert_called_once_with({"test": "data"})
        assert result is mock_result


class TestVocabularyLayer:
    """Tests for VocabularyLayer."""

    def test_name_property(self) -> None:
        """VocabularyLayer name is 'vocabulary'."""
        layer = VocabularyLayer(loader=None, schema_version="0.6.1")
        assert layer.name == "vocabulary"

    def test_should_run_without_loader(self) -> None:
        """VocabularyLayer should not run when loader is None."""
        layer = VocabularyLayer(loader=None, schema_version="0.6.1")
        context = ValidationContext(parsed_data={}, schema_version="0.6.1")
        assert layer.should_run(context) is False

    def test_should_run_without_passport(self) -> None:
        """VocabularyLayer should not run when passport is None."""
        mock_loader = MagicMock()
        layer = VocabularyLayer(loader=mock_loader, schema_version="0.6.1")
        context = ValidationContext(parsed_data={}, schema_version="0.6.1", passport=None)
        assert layer.should_run(context) is False

    def test_execute_without_passport_returns_valid(self) -> None:
        """VocabularyLayer.execute returns valid result when passport is None."""
        mock_loader = MagicMock()
        layer = VocabularyLayer(loader=mock_loader, schema_version="0.6.1")
        context = ValidationContext(parsed_data={}, schema_version="0.6.1", passport=None)

        result = layer.execute(context)

        assert result.valid is True


class TestSignatureLayer:
    """Tests for SignatureLayer."""

    def test_name_property(self) -> None:
        """SignatureLayer name is 'signature'."""
        layer = SignatureLayer(verifier=None, schema_version="0.6.1")
        assert layer.name == "signature"

    def test_should_run_without_verifier(self) -> None:
        """SignatureLayer should not run when verifier is None."""
        layer = SignatureLayer(verifier=None, schema_version="0.6.1")
        context = ValidationContext(parsed_data={}, schema_version="0.6.1")
        assert layer.should_run(context) is False

    def test_should_run_with_verifier(self) -> None:
        """SignatureLayer should run when verifier is provided."""
        mock_verifier = MagicMock()
        layer = SignatureLayer(verifier=mock_verifier, schema_version="0.6.1")
        context = ValidationContext(parsed_data={}, schema_version="0.6.1")
        assert layer.should_run(context) is True

    def test_execute_calls_verifier(self) -> None:
        """SignatureLayer.execute calls the verifier and processes result."""
        mock_verifier = MagicMock()
        mock_vc_result = MagicMock()
        mock_vc_result.valid = True
        mock_vc_result.signature_valid = True
        mock_vc_result.issuer_did = "did:web:example.com"
        mock_vc_result.verification_method = "did:web:example.com#key-1"
        mock_vc_result.errors = []
        mock_vc_result.warnings = []
        mock_verifier.verify.return_value = mock_vc_result

        layer = SignatureLayer(verifier=mock_verifier, schema_version="0.6.1")
        context = ValidationContext(parsed_data={"test": "data"}, schema_version="0.6.1")

        result = layer.execute(context)

        mock_verifier.verify.assert_called_once_with({"test": "data"})
        assert result.valid is True
        assert result.signature_valid is True
        assert result.issuer_did == "did:web:example.com"

    def test_execute_with_errors(self) -> None:
        """SignatureLayer.execute processes verification errors."""
        mock_verifier = MagicMock()
        mock_vc_result = MagicMock()
        mock_vc_result.valid = False
        mock_vc_result.signature_valid = False
        mock_vc_result.issuer_did = None
        mock_vc_result.verification_method = None
        mock_vc_result.errors = ["Invalid signature"]
        mock_vc_result.warnings = ["Missing proof"]
        mock_verifier.verify.return_value = mock_vc_result

        layer = SignatureLayer(verifier=mock_verifier, schema_version="0.6.1")
        context = ValidationContext(parsed_data={}, schema_version="0.6.1")

        result = layer.execute(context)

        assert result.valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1


class TestPluginLayer:
    """Tests for PluginLayer."""

    def test_name_property(self) -> None:
        """PluginLayer name is 'plugin'."""
        layer = PluginLayer(registry=None, schema_version="0.6.1")
        assert layer.name == "plugin"

    def test_should_run_without_registry(self) -> None:
        """PluginLayer should not run when registry is None."""
        layer = PluginLayer(registry=None, schema_version="0.6.1")
        context = ValidationContext(parsed_data={}, schema_version="0.6.1")
        assert layer.should_run(context) is False

    def test_should_run_without_passport(self) -> None:
        """PluginLayer should not run when passport is None."""
        mock_registry = MagicMock()
        layer = PluginLayer(registry=mock_registry, schema_version="0.6.1")
        context = ValidationContext(parsed_data={}, schema_version="0.6.1", passport=None)
        assert layer.should_run(context) is False


class TestValidationContextMethods:
    """Tests for ValidationContext helper methods."""

    def test_should_stop_fail_fast_with_errors(self) -> None:
        """should_stop returns True when fail_fast and has errors."""
        context = ValidationContext(
            parsed_data={},
            schema_version="0.6.1",
            fail_fast=True,
        )
        # Add an error to make result invalid
        from dppvalidator.validators.results import ValidationError, ValidationResult

        error_result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    path="$", message="Error", code="E001", layer="test", severity="error"
                )
            ],
            schema_version="0.6.1",
        )
        context.merge_result(error_result)

        assert context.should_stop() is True

    def test_should_stop_max_errors_reached(self) -> None:
        """should_stop returns True when max_errors reached."""
        from dppvalidator.validators.results import ValidationError, ValidationResult

        context = ValidationContext(
            parsed_data={},
            schema_version="0.6.1",
            max_errors=2,
        )

        # Add multiple errors
        errors = [
            ValidationError(
                path=f"$.field{i}",
                message=f"Error {i}",
                code="E001",
                layer="test",
                severity="error",
            )
            for i in range(3)
        ]
        error_result = ValidationResult(
            valid=False,
            errors=errors,
            schema_version="0.6.1",
        )
        context.merge_result(error_result)

        assert context.should_stop() is True

    def test_merge_result_updates_passport(self) -> None:
        """merge_result updates passport from layer result."""
        from dppvalidator.validators.results import ValidationResult

        context = ValidationContext(parsed_data={}, schema_version="0.6.1")
        mock_passport = MagicMock()

        result_with_passport = ValidationResult(
            valid=True,
            schema_version="0.6.1",
        )
        result_with_passport.passport = mock_passport

        context.merge_result(result_with_passport)

        assert context.passport is mock_passport

    def test_should_stop_returns_false_when_valid(self) -> None:
        """should_stop returns False when no errors."""
        context = ValidationContext(
            parsed_data={},
            schema_version="0.6.1",
            fail_fast=True,
        )
        # No errors merged, should not stop
        assert context.should_stop() is False
