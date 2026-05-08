"""Tests for CIRPASS-2 semantic validation rules."""

import pytest

from dppvalidator.models import CredentialIssuer, DigitalProductPassport
from dppvalidator.validators.rules.cirpass import (
    CIRPASS_RULES,
    CIRPASSGranularityConsistencyRule,
    CIRPASSMandatoryAttributesRule,
    CIRPASSOperatorIdentifierRule,
    CIRPASSSubstancesOfConcernRule,
    CIRPASSValidityPeriodRule,
    CIRPASSWeightVolumeRule,
)


class TestCIRPASSRulesRegistration:
    """Tests for CIRPASS rules registration."""

    def test_cirpass_rules_list_not_empty(self):
        """Test CIRPASS_RULES list is not empty."""
        assert len(CIRPASS_RULES) > 0

    def test_cirpass_rules_count(self):
        """Test CIRPASS_RULES has expected count."""
        assert len(CIRPASS_RULES) == 6

    def test_all_rules_have_required_attributes(self):
        """Test all CIRPASS rules have required attributes."""
        for rule in CIRPASS_RULES:
            assert hasattr(rule, "rule_id")
            assert hasattr(rule, "description")
            assert hasattr(rule, "severity")
            assert hasattr(rule, "suggestion")
            assert hasattr(rule, "docs_url")
            assert hasattr(rule, "check")
            assert rule.rule_id.startswith("CQ")


class TestCIRPASSMandatoryAttributesRule:
    """Tests for CQ001: Mandatory ESPR attributes."""

    @pytest.fixture
    def rule(self) -> CIRPASSMandatoryAttributesRule:
        """Create rule instance."""
        return CIRPASSMandatoryAttributesRule()

    def test_rule_attributes(self, rule: CIRPASSMandatoryAttributesRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "CQ001"
        assert rule.severity == "error"

    def test_valid_passport_no_violations(self, rule: CIRPASSMandatoryAttributesRule):
        """Test valid passport produces no violations."""
        from dppvalidator.models import Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            validFrom="2024-01-01T00:00:00Z",
            credential_subject=ProductPassport(
                product=Product(id="https://example.com/product", name="Test")
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_missing_valid_from(self, rule: CIRPASSMandatoryAttributesRule):
        """Test missing validFrom produces violation."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert any("validFrom" in v[0] for v in violations)

    def test_missing_credential_subject(self, rule: CIRPASSMandatoryAttributesRule):
        """Test missing credentialSubject produces violation."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            validFrom="2024-01-01T00:00:00Z",
        )
        violations = rule.check(passport)
        assert any("credentialSubject" in v[0] for v in violations)


class TestCIRPASSSubstancesOfConcernRule:
    """Tests for CQ004: Substances of concern identification."""

    @pytest.fixture
    def rule(self) -> CIRPASSSubstancesOfConcernRule:
        """Create rule instance."""
        return CIRPASSSubstancesOfConcernRule()

    def test_rule_attributes(self, rule: CIRPASSSubstancesOfConcernRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "CQ004"
        assert rule.severity == "error"

    def test_no_materials_no_violations(self, rule: CIRPASSSubstancesOfConcernRule):
        """Test no materials produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_non_hazardous_material_no_violation(self, rule: CIRPASSSubstancesOfConcernRule):
        """Test non-hazardous material produces no violation."""
        from dppvalidator.models import Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materials_provenance=[
                    Material(name="Safe Material", hazardous=False),
                ]
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_hazardous_without_cas_produces_violation(self, rule: CIRPASSSubstancesOfConcernRule):
        """Test hazardous material without CAS number produces violation."""
        from dppvalidator.models import Link, Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materials_provenance=[
                    Material(
                        name="Unknown Chemical",
                        hazardous=True,
                        materialSafetyInformation=Link(linkURL="https://example.com/msds"),
                    ),
                ]
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "CAS" in violations[0][1] or "EINECS" in violations[0][1]

    def test_hazardous_with_cas_code_no_violation(self, rule: CIRPASSSubstancesOfConcernRule):
        """Test hazardous material with CAS code in materialType produces no violation."""
        from dppvalidator.models import Classification, Link, Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materials_provenance=[
                    Material(
                        name="Benzene",
                        hazardous=True,
                        material_type=Classification(
                            id="https://cas.org/71-43-2",
                            name="Benzene",
                            code="71-43-2",
                        ),
                        material_safety_information=Link(link_url="https://example.com/msds"),
                    ),
                ]
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0


class TestCIRPASSOperatorIdentifierRule:
    """Tests for CQ011: Operator identifier."""

    @pytest.fixture
    def rule(self) -> CIRPASSOperatorIdentifierRule:
        """Create rule instance."""
        return CIRPASSOperatorIdentifierRule()

    def test_rule_attributes(self, rule: CIRPASSOperatorIdentifierRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "CQ011"
        assert rule.severity == "error"

    def test_valid_issuer_no_violations(self, rule: CIRPASSOperatorIdentifierRule):
        """Test valid issuer produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_issuer_present_no_violations(self, rule: CIRPASSOperatorIdentifierRule):
        """Test issuer with id produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert len(violations) == 0


class TestCIRPASSValidityPeriodRule:
    """Tests for CQ016: Validity period."""

    @pytest.fixture
    def rule(self) -> CIRPASSValidityPeriodRule:
        """Create rule instance."""
        return CIRPASSValidityPeriodRule()

    def test_rule_attributes(self, rule: CIRPASSValidityPeriodRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "CQ016"
        assert rule.severity == "warning"

    def test_both_dates_present_no_violations(self, rule: CIRPASSValidityPeriodRule):
        """Test both dates present produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            validFrom="2024-01-01T00:00:00Z",
            validUntil="2034-01-01T00:00:00Z",
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_missing_valid_from(self, rule: CIRPASSValidityPeriodRule):
        """Test missing validFrom produces violation."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            validUntil="2034-01-01T00:00:00Z",
        )
        violations = rule.check(passport)
        assert any("validFrom" in v[0] for v in violations)

    def test_missing_valid_until(self, rule: CIRPASSValidityPeriodRule):
        """Test missing validUntil produces violation."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            validFrom="2024-01-01T00:00:00Z",
        )
        violations = rule.check(passport)
        assert any("validUntil" in v[0] for v in violations)


class TestCIRPASSWeightVolumeRule:
    """Tests for CQ020: Weight/volume declarations."""

    @pytest.fixture
    def rule(self) -> CIRPASSWeightVolumeRule:
        """Create rule instance."""
        return CIRPASSWeightVolumeRule()

    def test_rule_attributes(self, rule: CIRPASSWeightVolumeRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "CQ020"
        assert rule.severity == "warning"

    def test_no_product_no_violations(self, rule: CIRPASSWeightVolumeRule):
        """Test no product produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_product_with_dimensions_no_violations(self, rule: CIRPASSWeightVolumeRule):
        """Test product with dimensions produces no violations."""
        from dppvalidator.models import Dimension, Measure, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credential_subject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Test",
                    dimensions=Dimension(weight=Measure(value=1.5, unit="KGM")),
                )
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_product_without_dimensions(self, rule: CIRPASSWeightVolumeRule):
        """Test product without dimensions produces violation."""
        from dppvalidator.models import Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credential_subject=ProductPassport(
                product=Product(id="https://example.com/product", name="Test")
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "dimension" in violations[0][0].lower()


class TestCIRPASSGranularityConsistencyRule:
    """Tests for CQ017: Granularity consistency."""

    @pytest.fixture
    def rule(self) -> CIRPASSGranularityConsistencyRule:
        """Create rule instance."""
        return CIRPASSGranularityConsistencyRule()

    def test_rule_attributes(self, rule: CIRPASSGranularityConsistencyRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "CQ017"
        assert rule.severity == "warning"

    def test_no_granularity_no_violations(self, rule: CIRPASSGranularityConsistencyRule):
        """Test no granularity level produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_item_level_with_serial_no_violations(self, rule: CIRPASSGranularityConsistencyRule):
        """Test item level with serial number produces no violations."""
        from dppvalidator.models import GranularityLevel, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credential_subject=ProductPassport(
                granularity_level=GranularityLevel.ITEM,
                product=Product(
                    id="https://example.com/product",
                    name="Test",
                    serial_number="SN123456",
                ),
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_item_level_without_serial_produces_violation(
        self, rule: CIRPASSGranularityConsistencyRule
    ):
        """Test item level without serial number produces violation."""
        from dppvalidator.models import GranularityLevel, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credential_subject=ProductPassport(
                granularity_level=GranularityLevel.ITEM,
                product=Product(id="https://example.com/product", name="Test"),
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "serialNumber" in violations[0][0]

    def test_batch_level_with_batch_number_no_violations(
        self, rule: CIRPASSGranularityConsistencyRule
    ):
        """Test batch level with batch number produces no violations."""
        from dppvalidator.models import GranularityLevel, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credential_subject=ProductPassport(
                granularity_level=GranularityLevel.BATCH,
                product=Product(
                    id="https://example.com/product",
                    name="Test",
                    batch_number="BATCH001",
                ),
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_batch_level_without_batch_number_produces_violation(
        self, rule: CIRPASSGranularityConsistencyRule
    ):
        """Test batch level without batch number produces violation."""
        from dppvalidator.models import GranularityLevel, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credential_subject=ProductPassport(
                granularity_level=GranularityLevel.BATCH,
                product=Product(id="https://example.com/product", name="Test"),
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "batchNumber" in violations[0][0]

    def test_model_level_no_violations(self, rule: CIRPASSGranularityConsistencyRule):
        """Test model level produces no violations."""
        from dppvalidator.models import GranularityLevel, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credential_subject=ProductPassport(
                granularity_level=GranularityLevel.MODEL,
                product=Product(id="https://example.com/product", name="Test"),
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0
