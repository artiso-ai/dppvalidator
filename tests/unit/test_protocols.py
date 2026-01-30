"""Tests for validator protocols."""

from dppvalidator.validators.model import ModelValidator
from dppvalidator.validators.protocols import SemanticRule, Validator
from dppvalidator.validators.rules.base import MassFractionSumRule
from dppvalidator.validators.schema import SchemaValidator


class TestProtocols:
    """Tests for validator protocols."""

    def test_validator_protocol_compliance(self):
        """Test that ModelValidator implements Validator protocol."""
        validator = ModelValidator()
        assert isinstance(validator, Validator)

    def test_semantic_rule_protocol_compliance(self):
        """Test that rules implement SemanticRule protocol."""
        rule = MassFractionSumRule()
        assert isinstance(rule, SemanticRule)
        assert rule.rule_id == "SEM001"
        assert rule.severity in ("error", "warning", "info")
        assert rule.description is not None

    def test_schema_validator_implements_validator(self):
        """Test SchemaValidator implements Validator protocol."""
        validator = SchemaValidator()
        assert isinstance(validator, Validator)
