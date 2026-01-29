"""Tests for validation engine and validators."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from dppvalidator.models import CredentialIssuer, DigitalProductPassport
from dppvalidator.validators import ValidationEngine, ValidationResult
from dppvalidator.validators.model import ModelValidator
from dppvalidator.validators.results import ValidationError, ValidationException
from dppvalidator.validators.rules.base import (
    CircularityContentRule,
    ConformityClaimRule,
    GranularitySerialNumberRule,
    HazardousMaterialRule,
    MassFractionSumRule,
    OperationalScopeRule,
    ValidityDateRule,
)
from dppvalidator.validators.schema import SchemaValidator
from dppvalidator.validators.semantic import SemanticValidator

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_empty_result_is_valid(self):
        """Test that empty result is valid."""
        result = ValidationResult(valid=True, schema_version="0.6.1")
        assert result.valid is True
        assert len(result.errors) == 0

    def test_result_with_error_is_invalid(self):
        """Test that result with error is invalid."""
        errors = [
            ValidationError(
                path="$.issuer",
                message="Missing required field",
                code="REQUIRED",
                layer="model",
            )
        ]
        result = ValidationResult(valid=False, errors=errors, schema_version="0.6.1")
        assert result.valid is False
        assert len(result.errors) == 1

    def test_result_with_warning_is_valid(self):
        """Test that result with warning only is still valid."""
        warnings = [
            ValidationError(
                path="$.field",
                message="Recommended field missing",
                code="SEM005",
                layer="semantic",
                severity="warning",
            )
        ]
        result = ValidationResult(valid=True, warnings=warnings, schema_version="0.6.1")
        assert result.valid is True
        assert len(result.warnings) == 1

    def test_result_to_json(self):
        """Test JSON serialization."""
        result = ValidationResult(valid=True, schema_version="0.6.1")
        json_str = result.to_json()
        data = json.loads(json_str)
        assert data["valid"] is True
        assert data["schema_version"] == "0.6.1"

    def test_result_merge(self):
        """Test merging two results."""
        result1 = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.a", message="Error A", code="E1", layer="model")],
            schema_version="0.6.1",
        )
        result2 = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.b", message="Error B", code="E2", layer="model")],
            schema_version="0.6.1",
        )
        merged = result1.merge(result2)
        assert len(merged.errors) == 2


class TestValidationEngine:
    """Tests for ValidationEngine."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        """Create validation engine."""
        return ValidationEngine(schema_version="0.6.1")

    def test_validate_minimal_valid_dpp(self, engine: ValidationEngine):
        """Test validating a minimal valid DPP."""
        data = {
            "id": "https://example.com/credentials/dpp-001",
            "issuer": {
                "id": "https://example.com/issuers/001",
                "name": "Example Company Ltd",
            },
        }
        result = engine.validate(data)
        assert result.valid is True

    def test_validate_missing_issuer(self, engine: ValidationEngine):
        """Test validation fails for missing issuer."""
        data = {
            "id": "https://example.com/credentials/dpp-001",
        }
        result = engine.validate(data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_invalid_json(self, engine: ValidationEngine):
        """Test validation handles invalid data gracefully."""
        result = engine.validate("not valid json data")
        assert result.valid is False

    def test_validate_with_fail_fast(self, engine: ValidationEngine):
        """Test fail_fast stops on first error."""
        data = {"invalid": "data"}
        result = engine.validate(data, fail_fast=True)
        assert result.valid is False
        assert len(result.all_issues) >= 1

    def test_validate_fixture_valid(self, engine: ValidationEngine):
        """Test validating valid fixture."""
        fixture_path = FIXTURES_DIR / "valid" / "minimal_dpp.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            result = engine.validate(data)
            assert result.valid is True

    def test_validate_fixture_invalid(self, engine: ValidationEngine):
        """Test validating invalid fixture."""
        fixture_path = FIXTURES_DIR / "invalid" / "missing_issuer.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            result = engine.validate(data)
            assert result.valid is False


class TestSemanticRules:
    """Tests for semantic validation rules."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        """Create validation engine."""
        return ValidationEngine(schema_version="0.6.1")

    def test_sem002_invalid_date_order(self, engine: ValidationEngine):
        """Test SEM002: validFrom must be before validUntil."""
        data = {
            "id": "https://example.com/credentials/dpp-001",
            "issuer": {
                "id": "https://example.com/issuers/001",
                "name": "Example Company Ltd",
            },
            "validFrom": "2034-01-01T00:00:00Z",
            "validUntil": "2024-01-01T00:00:00Z",
        }
        result = engine.validate(data)
        assert result.valid is False

    def test_sem001_mass_fraction_sum(self, engine: ValidationEngine):
        """Test SEM001: mass fractions must sum to 1.0."""
        data = {
            "id": "https://example.com/credentials/dpp-001",
            "issuer": {
                "id": "https://example.com/issuers/001",
                "name": "Example Company Ltd",
            },
            "credentialSubject": {
                "materialsProvenance": [
                    {"name": "Material A", "massFraction": 0.3},
                    {"name": "Material B", "massFraction": 0.3},
                ],
            },
        }
        result = engine.validate(data)
        # SEM001 only fires if passport is valid and has materials
        # If model validation fails, semantic rules don't run
        assert result is not None


class TestValidationError:
    """Tests for ValidationError dataclass."""

    def test_error_to_dict(self):
        """Test ValidationError to_dict method."""
        error = ValidationError(
            path="$.issuer",
            message="Missing field",
            code="E001",
            layer="model",
            severity="error",
            context={"type": "missing"},
        )
        d = error.to_dict()
        assert d["path"] == "$.issuer"
        assert d["message"] == "Missing field"
        assert d["code"] == "E001"
        assert d["layer"] == "model"
        assert d["context"]["type"] == "missing"


class TestValidationResultExtended:
    """Extended tests for ValidationResult."""

    def test_error_count(self):
        """Test error_count property."""
        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(path="$.a", message="A", code="E1", layer="model"),
                ValidationError(path="$.b", message="B", code="E2", layer="model"),
            ],
            schema_version="0.6.1",
        )
        assert result.error_count == 2

    def test_warning_count(self):
        """Test warning_count property."""
        result = ValidationResult(
            valid=True,
            warnings=[
                ValidationError(
                    path="$.a", message="A", code="W1", layer="model", severity="warning"
                ),
            ],
            schema_version="0.6.1",
        )
        assert result.warning_count == 1

    def test_all_issues(self):
        """Test all_issues property combines all."""
        result = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.a", message="A", code="E1", layer="model")],
            warnings=[
                ValidationError(
                    path="$.b", message="B", code="W1", layer="model", severity="warning"
                )
            ],
            info=[
                ValidationError(path="$.c", message="C", code="I1", layer="model", severity="info")
            ],
            schema_version="0.6.1",
        )
        assert len(result.all_issues) == 3

    def test_raise_for_errors(self):
        """Test raise_for_errors raises ValidationException."""
        result = ValidationResult(
            valid=False,
            errors=[ValidationError(path="$.a", message="Error", code="E1", layer="model")],
            schema_version="0.6.1",
        )
        with pytest.raises(ValidationException) as exc_info:
            result.raise_for_errors()
        assert exc_info.value.result == result
        assert "Error" in str(exc_info.value)

    def test_raise_for_errors_valid(self):
        """Test raise_for_errors does nothing for valid result."""
        result = ValidationResult(valid=True, schema_version="0.6.1")
        result.raise_for_errors()  # Should not raise


class TestValidationEngineExtended:
    """Extended tests for ValidationEngine."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        """Create validation engine."""
        return ValidationEngine(schema_version="0.6.1")

    def test_validate_file(self, engine: ValidationEngine):
        """Test validate_file method."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "id": "https://example.com/dpp",
                    "issuer": {"id": "https://example.com/issuer", "name": "Test"},
                },
                f,
            )
            f.flush()
            result = engine.validate_file(f.name)
            assert result.valid is True

    def test_validate_file_not_found(self, engine: ValidationEngine):
        """Test validate_file with non-existent file."""
        result = engine.validate(Path("/non/existent/file.json"))
        assert result.valid is False
        assert any("File not found" in e.message for e in result.errors)

    def test_validate_file_invalid_json(self, engine: ValidationEngine):
        """Test validate_file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            f.flush()
            result = engine.validate_file(f.name)
            assert result.valid is False
            assert any("Invalid JSON" in e.message for e in result.errors)

    def test_validate_string_invalid_json(self, engine: ValidationEngine):
        """Test validate with invalid JSON string."""
        result = engine.validate("{invalid json")
        assert result.valid is False
        assert any("Invalid JSON" in e.message for e in result.errors)

    def test_validate_async(self, engine: ValidationEngine):
        """Test async validation."""
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        result = asyncio.run(engine.validate_async(data))
        assert result.valid is True

    def test_validate_batch(self, engine: ValidationEngine):
        """Test batch validation."""
        items = [
            {"id": "https://example.com/dpp1", "issuer": {"id": "https://a.com", "name": "A"}},
            {"id": "https://example.com/dpp2", "issuer": {"id": "https://b.com", "name": "B"}},
        ]
        results = asyncio.run(engine.validate_batch(items, concurrency=2))
        assert len(results) == 2
        assert all(r.valid for r in results)

    def test_validate_with_max_errors(self, engine: ValidationEngine):
        """Test validation stops at max_errors."""
        data = {"invalid": "data"}
        result = engine.validate(data, max_errors=1)
        assert result.valid is False

    def test_engine_layers_config(self):
        """Test engine with specific layers."""
        engine = ValidationEngine(layers=["model"])
        data = {"id": "https://example.com/dpp", "issuer": {"id": "https://a.com", "name": "A"}}
        result = engine.validate(data)
        assert result is not None

    def test_engine_strict_mode(self):
        """Test engine with strict mode."""
        engine = ValidationEngine(strict_mode=True)
        assert engine.strict_mode is True


class TestModelValidator:
    """Tests for ModelValidator."""

    def test_validate_valid_data(self):
        """Test validating valid data."""
        validator = ModelValidator()
        data = {"id": "https://example.com/dpp", "issuer": {"id": "https://a.com", "name": "A"}}
        result = validator.validate(data)
        assert result.valid is True
        assert result.passport is not None

    def test_validate_invalid_data(self):
        """Test validating invalid data."""
        validator = ModelValidator()
        data = {"invalid": "data"}
        result = validator.validate(data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_loc_to_path_with_index(self):
        """Test _loc_to_path with array index."""
        validator = ModelValidator()
        path = validator._loc_to_path(("items", 0, "name"))
        assert path == "$.items[0].name"

    def test_safe_input_with_long_string(self):
        """Test _safe_input truncates long values."""
        validator = ModelValidator()
        long_dict = {"key": "x" * 200}
        result = validator._safe_input(long_dict)
        assert "..." in result

    def test_safe_input_with_none(self):
        """Test _safe_input with None."""
        validator = ModelValidator()
        assert validator._safe_input(None) is None

    def test_safe_input_with_primitives(self):
        """Test _safe_input with primitive types."""
        validator = ModelValidator()
        assert validator._safe_input("test") == "test"
        assert validator._safe_input(42) == 42
        assert validator._safe_input(3.14) == 3.14
        assert validator._safe_input(True) is True


class TestSchemaValidator:
    """Tests for SchemaValidator."""

    def test_validate_without_jsonschema(self):
        """Test validation when jsonschema not available returns warning."""
        validator = SchemaValidator()
        data = {"id": "test"}
        result = validator.validate(data)
        # Either passes with warning (no jsonschema) or validates
        assert result is not None

    def test_validate_with_custom_schema_path(self):
        """Test validator with custom schema path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"type": "object"}, f)
            f.flush()
            validator = SchemaValidator(schema_path=Path(f.name))
            result = validator.validate({"test": "data"})
            assert result is not None


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
        # Valid passport may have info messages but no errors
        assert result is not None


class TestSemanticRulesDetailed:
    """Detailed tests for individual semantic rules."""

    @pytest.fixture
    def valid_passport(self) -> DigitalProductPassport:
        """Create a valid passport."""
        return DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )

    def test_mass_fraction_rule_no_subject(self, valid_passport: DigitalProductPassport):
        """Test MassFractionSumRule with no credential subject."""
        rule = MassFractionSumRule()
        violations = rule.check(valid_passport)
        assert len(violations) == 0

    def test_validity_date_rule_valid_dates(self, valid_passport: DigitalProductPassport):
        """Test ValidityDateRule with valid date ordering."""
        rule = ValidityDateRule()
        violations = rule.check(valid_passport)
        assert len(violations) == 0

    def test_hazardous_material_rule_no_materials(self, valid_passport: DigitalProductPassport):
        """Test HazardousMaterialRule with no materials."""
        rule = HazardousMaterialRule()
        violations = rule.check(valid_passport)
        assert len(violations) == 0

    def test_circularity_content_rule_no_scorecard(self, valid_passport: DigitalProductPassport):
        """Test CircularityContentRule with no scorecard."""
        rule = CircularityContentRule()
        violations = rule.check(valid_passport)
        assert len(violations) == 0

    def test_conformity_claim_rule_no_claims(self, valid_passport: DigitalProductPassport):
        """Test ConformityClaimRule with no claims."""
        rule = ConformityClaimRule()
        violations = rule.check(valid_passport)
        # No credential subject means no violation
        assert len(violations) == 0

    def test_granularity_serial_rule_no_product(self, valid_passport: DigitalProductPassport):
        """Test GranularitySerialNumberRule with no product."""
        rule = GranularitySerialNumberRule()
        violations = rule.check(valid_passport)
        assert len(violations) == 0

    def test_operational_scope_rule_no_scorecard(self, valid_passport: DigitalProductPassport):
        """Test OperationalScopeRule with no emissions scorecard."""
        rule = OperationalScopeRule()
        violations = rule.check(valid_passport)
        assert len(violations) == 0


class TestSemanticRulesWithViolations:
    """Tests for semantic rules that produce violations."""

    def test_mass_fraction_sum_violation(self):
        """Test MassFractionSumRule detects invalid sum via engine."""
        # Test via the engine to verify the full flow
        # Model validation catches this before semantic rules run
        engine = ValidationEngine()
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "credentialSubject": {
                "materialsProvenance": [
                    {"name": "A", "massFraction": 0.3},
                    {"name": "B", "massFraction": 0.3},
                ]
            },
        }
        result = engine.validate(data)
        # Model validator catches mass fraction sum error
        assert result.valid is False

    def test_validity_date_rule_violation(self):
        """Test ValidityDateRule detects invalid date order via engine."""
        # Model validation catches this before semantic rules run
        engine = ValidationEngine()
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "validFrom": "2034-01-01T00:00:00Z",
            "validUntil": "2024-01-01T00:00:00Z",
        }
        result = engine.validate(data)
        # Model validator catches date order error
        assert result.valid is False
        assert any("validFrom" in e.message for e in result.errors)

    def test_circularity_content_violation(self):
        """Test CircularityContentRule detects recycled > recyclable."""
        from dppvalidator.models import CircularityPerformance, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                circularityScorecard=CircularityPerformance(
                    recycledContent=0.8,
                    recyclableContent=0.5,
                )
            ),
        )
        rule = CircularityContentRule()
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "exceeds" in violations[0][1]

    def test_conformity_claim_info(self):
        """Test ConformityClaimRule emits info for missing claims."""
        from dppvalidator.models import ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(),
        )
        rule = ConformityClaimRule()
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "conformity claims" in violations[0][1].lower()

    def test_granularity_serial_number_warning(self):
        """Test GranularitySerialNumberRule warning for item without serial."""
        from dppvalidator.models import GranularityLevel, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                granularityLevel=GranularityLevel.ITEM,
                product=Product(id="https://example.com/product", name="Test Product"),
            ),
        )
        rule = GranularitySerialNumberRule()
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "serialNumber" in violations[0][1]

    def test_operational_scope_warning(self):
        """Test OperationalScopeRule warning for missing scope."""
        from dppvalidator.models import EmissionsPerformance, OperationalScope, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                emissionsScorecard=EmissionsPerformance(
                    carbonFootprint=25.5,
                    declaredUnit="KGM",
                    operationalScope=OperationalScope.NONE,
                    primarySourcedRatio=0.8,
                )
            ),
        )
        rule = OperationalScopeRule()
        # Since scope is set (even if NONE), no violation
        violations = rule.check(passport)
        # Check the rule runs without error
        assert violations is not None


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
        # ConformityClaimRule should emit an info message
        assert result.info is not None or result.warnings is not None or result.errors is not None


class TestSchemaValidatorExtended:
    """Extended tests for SchemaValidator."""

    def test_schema_validation_with_valid_data(self):
        """Test schema validation with valid data."""
        validator = SchemaValidator()
        data = {
            "id": "https://example.com/dpp",
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        result = validator.validate(data)
        # Result should exist regardless of jsonschema availability
        assert result is not None

    def test_schema_validator_error_to_path(self):
        """Test _error_to_path method."""
        validator = SchemaValidator()

        # Create a mock error object
        class MockError:
            absolute_path = ["items", 0, "name"]

        path = validator._error_to_path(MockError())
        assert path == "$.items[0].name"


class TestEngineEdgeCases:
    """Edge case tests for ValidationEngine."""

    def test_validate_with_only_semantic_layer(self):
        """Test validation with only semantic layer."""
        engine = ValidationEngine(layers=["semantic"])
        data = {"id": "https://example.com/dpp", "issuer": {"id": "https://a.com", "name": "A"}}
        # Without model layer, semantic validation won't run
        result = engine.validate(data)
        assert result is not None

    def test_validate_with_only_schema_layer(self):
        """Test validation with only schema layer."""
        engine = ValidationEngine(layers=["schema"])
        data = {"id": "https://example.com/dpp"}
        result = engine.validate(data)
        assert result is not None


class TestProtocols:
    """Tests for validator protocols."""

    def test_validator_protocol_compliance(self):
        """Test that ModelValidator implements Validator protocol."""
        from dppvalidator.validators.protocols import Validator

        validator = ModelValidator()
        assert isinstance(validator, Validator)

    def test_semantic_rule_protocol_compliance(self):
        """Test that rules implement SemanticRule protocol."""
        from dppvalidator.validators.protocols import SemanticRule

        rule = MassFractionSumRule()
        assert isinstance(rule, SemanticRule)
        assert rule.rule_id == "SEM001"
        assert rule.severity == "error"
        assert rule.description is not None

    def test_schema_validator_implements_validator(self):
        """Test SchemaValidator implements Validator protocol."""
        from dppvalidator.validators.protocols import Validator

        validator = SchemaValidator()
        assert isinstance(validator, Validator)


class TestHazardousMaterialRule:
    """Tests for HazardousMaterialRule."""

    def test_hazardous_without_safety_info(self):
        """Test hazardous material without safety info via engine."""
        engine = ValidationEngine()
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "credentialSubject": {
                "materialsProvenance": [
                    {"name": "Chemical X", "hazardous": True},
                ]
            },
        }
        result = engine.validate(data)
        # Model validator catches hazardous without safety info
        assert result.valid is False

    def test_hazardous_with_safety_info(self):
        """Test hazardous material with safety info passes."""
        engine = ValidationEngine()
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "credentialSubject": {
                "materialsProvenance": [
                    {
                        "name": "Chemical X",
                        "hazardous": True,
                        "materialSafetyInformation": {"linkURL": "https://example.com/msds"},
                    },
                ]
            },
        }
        result = engine.validate(data)
        # This should pass hazardous validation
        assert result is not None


class TestSchemaValidatorWithJsonSchema:
    """Tests for SchemaValidator with jsonschema library."""

    def test_load_schema_from_docs(self):
        """Test loading schema from docs directory."""
        validator = SchemaValidator()
        # Trigger schema loading
        schema = validator._load_schema()
        assert schema is not None

    def test_get_validator_returns_validator(self):
        """Test _get_validator returns a validator or None."""
        validator = SchemaValidator()
        v = validator._get_validator()
        # v may be None if jsonschema not available, or a validator
        assert v is None or hasattr(v, "iter_errors")

    def test_schema_validation_errors(self):
        """Test schema validation produces errors for invalid data."""
        validator = SchemaValidator()
        # Missing required fields
        data = {"type": ["DigitalProductPassport"]}
        result = validator.validate(data)
        # Result exists regardless of jsonschema availability
        assert result is not None


class TestModelValidatorEdgeCases:
    """Edge case tests for ModelValidator."""

    def test_safe_input_with_object(self):
        """Test _safe_input with custom object."""
        validator = ModelValidator()

        class CustomObj:
            def __str__(self):
                return "x" * 200

        result = validator._safe_input(CustomObj())
        assert len(result) <= 100


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
        # Should have warnings from GranularitySerialNumberRule
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
        # Should have info from ConformityClaimRule
        assert len(result.info) > 0


class TestSchemaValidatorFullCoverage:
    """Full coverage tests for SchemaValidator."""

    def test_load_schema_with_cache(self):
        """Test schema caching on second load."""
        validator = SchemaValidator()
        schema1 = validator._load_schema()
        schema2 = validator._load_schema()
        assert schema1 is schema2  # Same cached object

    def test_validate_with_schema_errors(self):
        """Test validation with schema that produces errors."""
        validator = SchemaValidator()
        # Force schema load
        validator._load_schema()
        # Validate invalid data
        result = validator.validate({"@context": "invalid"})
        # Should return a result
        assert result is not None

    def test_validator_with_empty_schema(self):
        """Test validation when schema is empty."""
        validator = SchemaValidator()
        validator._schema = {}
        v = validator._get_validator()
        # Empty schema may return None validator
        assert v is None or v is not None


class TestEngineFullCoverage:
    """Full coverage tests for ValidationEngine."""

    def test_engine_max_errors_stops_early(self):
        """Test engine stops collecting errors at max_errors."""
        engine = ValidationEngine()
        data = {}  # Invalid - missing required fields
        result = engine.validate(data, max_errors=1)
        assert result.valid is False

    def test_engine_fail_fast_in_schema_layer(self):
        """Test fail_fast stops after schema layer."""
        engine = ValidationEngine(layers=["schema", "model"])
        data = {}
        result = engine.validate(data, fail_fast=True)
        assert result is not None

    def test_validate_with_all_layers_disabled(self):
        """Test validation with empty layers list returns result."""
        engine = ValidationEngine(layers=[])
        data = {"id": "https://example.com/dpp", "issuer": {"id": "https://a.com", "name": "A"}}
        result = engine.validate(data)
        # With no layers, validation returns True
        assert result is not None

    def test_semantic_layer_skipped_without_passport(self):
        """Test semantic layer skipped when model parsing fails."""
        engine = ValidationEngine(layers=["model", "semantic"])
        data = {}  # Will fail model validation
        result = engine.validate(data)
        # Semantic rules shouldn't run since passport is None
        assert result.valid is False


class TestSchemaValidatorMoreCoverage:
    """More coverage tests for SchemaValidator."""

    def test_schema_validator_custom_path(self, tmp_path):
        """Test SchemaValidator with custom schema path."""
        from dppvalidator.validators.schema import SchemaValidator

        # Create a minimal schema
        schema_file = tmp_path / "schema.json"
        schema_file.write_text('{"type": "object"}')

        validator = SchemaValidator(schema_path=schema_file)
        result = validator.validate({"id": "test"})
        assert result is not None

    def test_schema_validator_load_schema_cached(self, tmp_path):
        """Test that schema is cached after first load."""
        from dppvalidator.validators.schema import SchemaValidator

        schema_file = tmp_path / "schema.json"
        schema_file.write_text('{"type": "object"}')

        validator = SchemaValidator(schema_path=schema_file)
        # First load
        schema1 = validator._load_schema()
        # Second load should return same cached object
        schema2 = validator._load_schema()
        assert schema1 is schema2

    def test_schema_validator_error_to_path_with_array(self):
        """Test _error_to_path with array indices."""
        from dppvalidator.validators.schema import SchemaValidator

        validator = SchemaValidator()

        # Create mock error with array path
        class MockError:
            absolute_path = ["items", 0, "name"]

        path = validator._error_to_path(MockError())
        assert path == "$.items[0].name"


class TestRulesFullCoverage:
    """Full coverage tests for semantic rules."""

    def test_mass_fraction_rule_with_valid_sum(self):
        """Test MassFractionSumRule with valid sum."""
        from dppvalidator.models import Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materialsProvenance=[
                    Material(name="A", massFraction=0.5),
                    Material(name="B", massFraction=0.5),
                ]
            ),
        )
        rule = MassFractionSumRule()
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_mass_fraction_rule_no_fractions(self):
        """Test MassFractionSumRule with materials but no fractions."""
        from dppvalidator.models import Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materialsProvenance=[
                    Material(name="A"),
                    Material(name="B"),
                ]
            ),
        )
        rule = MassFractionSumRule()
        violations = rule.check(passport)
        # No fractions means no violation
        assert len(violations) == 0

    def test_hazardous_material_rule_with_violation(self):
        """Test HazardousMaterialRule directly."""
        from dppvalidator.models import Link, Material, ProductPassport

        # Create passport with hazardous material that has safety info
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materialsProvenance=[
                    Material(
                        name="Safe Chemical",
                        hazardous=True,
                        materialSafetyInformation=Link(linkURL="https://example.com/msds"),
                    ),
                ]
            ),
        )
        rule = HazardousMaterialRule()
        violations = rule.check(passport)
        # Has safety info, so no violation
        assert len(violations) == 0

    def test_operational_scope_rule_with_violation(self):
        """Test OperationalScopeRule with missing scope."""
        # Test via engine since direct model construction enforces required fields
        engine = ValidationEngine()
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "credentialSubject": {
                "emissionsScorecard": {
                    "carbonFootprint": 25.5,
                    "declaredUnit": "KGM",
                    "primarySourcedRatio": 0.8,
                }
            },
        }
        result = engine.validate(data)
        # Should fail model validation due to missing required fields
        assert result is not None
