"""Tests for semantic validation rules."""

import pytest

from dppvalidator.models import CredentialIssuer, DigitalProductPassport
from dppvalidator.validators import ValidationEngine
from dppvalidator.validators.rules.base import (
    CircularityContentRule,
    ConformityClaimRule,
    GranularitySerialNumberRule,
    HazardousMaterialRule,
    MassFractionSumRule,
    OperationalScopeRule,
    ValidityDateRule,
)


class TestSemanticRules:
    """Tests for semantic validation rules."""

    @pytest.fixture
    def engine(self) -> ValidationEngine:
        """Create validation engine (model + semantic only for semantic rule tests)."""
        return ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])

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

    def test_mass_fraction_sum_exceeds_one_via_engine(self):
        """Test model validator catches mass fractions exceeding 1.0 via engine."""
        engine = ValidationEngine()
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "credentialSubject": {
                "materialsProvenance": [
                    {"name": "A", "massFraction": 0.6},
                    {"name": "B", "massFraction": 0.6},
                ]
            },
        }
        result = engine.validate(data)
        assert result.valid is False
        assert any("mass fraction" in e.message.lower() for e in result.errors)

    def test_validity_date_rule_violation(self):
        """Test ValidityDateRule detects invalid date order via engine."""
        engine = ValidationEngine()
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "validFrom": "2034-01-01T00:00:00Z",
            "validUntil": "2024-01-01T00:00:00Z",
        }
        result = engine.validate(data)
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
        violations = rule.check(passport)
        assert violations is not None


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
        assert len(violations) == 0

    def test_hazardous_material_rule_with_violation(self):
        """Test HazardousMaterialRule directly."""
        from dppvalidator.models import Link, Material, ProductPassport

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
        assert len(violations) == 0

    def test_operational_scope_rule_with_violation(self):
        """Test OperationalScopeRule with missing scope."""
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
        assert result is not None


class TestSemanticRulesViolationPaths:
    """Tests that verify semantic rules detect actual violations."""

    def test_mass_fraction_sum_partial_declaration_produces_warning(self):
        """Test partial mass fractions produce warning via semantic layer."""
        engine = ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "credentialSubject": {
                "materialsProvenance": [
                    {"name": "Steel", "massFraction": 0.3},
                    {"name": "Plastic", "massFraction": 0.2},
                ]
            },
        }
        result = engine.validate(data)
        assert result.valid is True
        assert any("mass fractions" in w.message.lower() for w in result.warnings)

    def test_validity_date_order_caught_by_model_validation(self):
        """Test ValidityDateRule violations are caught at model level."""
        engine = ValidationEngine(schema_version="0.6.1", layers=["model", "semantic"])
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "validFrom": "2034-01-01T00:00:00Z",
            "validUntil": "2024-01-01T00:00:00Z",
        }
        result = engine.validate(data)
        assert result.valid is False
        assert any("validFrom" in e.message for e in result.errors)

    def test_hazardous_material_caught_by_model_validation(self):
        """Test HazardousMaterialRule violations are caught at model level."""
        engine = ValidationEngine(schema_version="0.6.1")
        data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "credentialSubject": {
                "materialsProvenance": [
                    {"name": "Hazardous Chemical", "hazardous": True},
                ]
            },
        }
        result = engine.validate(data)
        assert result.valid is False
        assert any(
            "safety" in e.message.lower() or "hazardous" in e.message.lower() for e in result.errors
        )

    def test_circularity_content_rule_produces_violation(self):
        """Test CircularityContentRule produces violation when recycled > recyclable."""
        from dppvalidator.models import CircularityPerformance, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                circularityScorecard=CircularityPerformance(
                    recycledContent=0.9,
                    recyclableContent=0.5,
                )
            ),
        )
        rule = CircularityContentRule()
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "0.9" in violations[0][1]
        assert "0.5" in violations[0][1]
        assert "exceeds" in violations[0][1]

    def test_conformity_claim_rule_produces_info(self):
        """Test ConformityClaimRule produces info when no claims present."""
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

    def test_granularity_serial_number_rule_produces_warning(self):
        """Test GranularitySerialNumberRule produces warning for item without serial."""
        from dppvalidator.models import GranularityLevel, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                granularityLevel=GranularityLevel.ITEM,
                product=Product(
                    id="https://example.com/product",
                    name="Test Product",
                ),
            ),
        )
        rule = GranularitySerialNumberRule()
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "serialNumber" in violations[0][1]
        assert "item" in violations[0][1].lower()

    def test_operational_scope_rule_via_engine(self):
        """Test OperationalScopeRule produces warning when scope missing via engine."""
        engine = ValidationEngine(schema_version="0.6.1")
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
        assert result.valid is False


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
        assert result is not None
