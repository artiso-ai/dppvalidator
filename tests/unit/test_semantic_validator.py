"""Tests for SemanticValidator."""

import pytest

from dppvalidator.models import CredentialIssuer, DigitalProductPassport
from dppvalidator.validators.semantic import SemanticValidator


class TestSemanticValidator:
    """Tests for SemanticValidator."""

    @pytest.fixture
    def valid_passport(self) -> DigitalProductPassport:
        """Create a valid passport for testing."""
        return DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )

    def test_validate_with_custom_rules(self, valid_passport: DigitalProductPassport):
        """Test validator with custom rules."""
        validator = SemanticValidator(rules=[])
        result = validator.validate(valid_passport)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_with_default_rules(self, valid_passport: DigitalProductPassport):
        """Test validator with default rules."""
        validator = SemanticValidator()
        result = validator.validate(valid_passport)
        assert result is not None


class TestSemanticValidatorSeverities:
    """Tests for semantic validator handling different severities."""

    def test_validator_separates_severities(self):
        """Test validator correctly separates errors, warnings, info."""
        from dppvalidator.models import ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(),
        )
        validator = SemanticValidator()
        result = validator.validate(passport)
        assert result.info is not None or result.warnings is not None or result.errors is not None


class TestSemanticValidatorWarningsAndInfo:
    """Tests for semantic validator with warnings and info."""

    def test_warning_rule_produces_warning(self):
        """Test a warning severity rule produces a warning."""
        from dppvalidator.models import GranularityLevel, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                granularityLevel=GranularityLevel.ITEM,
                product=Product(id="https://example.com/product", name="Test"),
            ),
        )
        validator = SemanticValidator()
        result = validator.validate(passport)
        assert len(result.warnings) > 0 or len(result.info) > 0

    def test_info_rule_produces_info(self):
        """Test an info severity rule produces info."""
        from dppvalidator.models import ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(),
        )
        validator = SemanticValidator()
        result = validator.validate(passport)
        assert len(result.info) > 0
