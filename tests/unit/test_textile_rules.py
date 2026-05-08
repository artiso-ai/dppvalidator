"""Tests for CIRPASS-2 textile sector validation rules."""

import pytest

from dppvalidator.models import CredentialIssuer, DigitalProductPassport
from dppvalidator.validators.rules.textile import (
    TEXTILE_RULES,
    TextileCareInstructionsRule,
    TextileDurabilityRule,
    TextileEnvironmentalCategory,
    TextileHSCodeRule,
    TextileMaterialCompositionRule,
    TextileMicroplasticRule,
    get_textile_environmental_categories,
    is_textile_product,
)


class TestTextileRulesRegistration:
    """Tests for textile rules registration."""

    def test_textile_rules_list_not_empty(self):
        """Test TEXTILE_RULES list is not empty."""
        assert len(TEXTILE_RULES) > 0

    def test_textile_rules_count(self):
        """Test TEXTILE_RULES has expected count."""
        assert len(TEXTILE_RULES) == 5

    def test_all_rules_have_required_attributes(self):
        """Test all textile rules have required attributes."""
        for rule in TEXTILE_RULES:
            assert hasattr(rule, "rule_id")
            assert hasattr(rule, "description")
            assert hasattr(rule, "severity")
            assert hasattr(rule, "suggestion")
            assert hasattr(rule, "docs_url")
            assert hasattr(rule, "check")
            assert rule.rule_id.startswith("TXT")


class TestTextileEnvironmentalCategory:
    """Tests for TextileEnvironmentalCategory enum."""

    def test_environmental_categories_exist(self):
        """Test environmental categories exist."""
        assert TextileEnvironmentalCategory.WATER_CONSUMPTION.value == "water_consumption"
        assert TextileEnvironmentalCategory.ENERGY_CONSUMPTION.value == "energy_consumption"
        assert TextileEnvironmentalCategory.MICROPLASTIC_RELEASE.value == "microplastic_release"

    def test_get_textile_environmental_categories(self):
        """Test get_textile_environmental_categories function."""
        categories = get_textile_environmental_categories()
        assert len(categories) == 7
        assert "water_consumption" in categories
        assert "microplastic_release" in categories


class TestTextileHSCodeRule:
    """Tests for TXT001: Textile HS code validation."""

    @pytest.fixture
    def rule(self) -> TextileHSCodeRule:
        """Create rule instance."""
        return TextileHSCodeRule()

    def test_rule_attributes(self, rule: TextileHSCodeRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "TXT001"
        assert rule.severity == "warning"

    def test_no_product_no_violations(self, rule: TextileHSCodeRule):
        """Test no product produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_product_with_textile_hs_code(self, rule: TextileHSCodeRule):
        """Test product with textile HS code produces no violations."""
        from dppvalidator.models import Classification, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Cotton T-Shirt",
                    productCategory=[
                        Classification(
                            id="https://hs.org/6109",
                            name="T-shirts",
                            code="6109",
                        )
                    ],
                )
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_product_without_product_category(self, rule: TextileHSCodeRule):
        """Test product without category produces violation."""
        from dppvalidator.models import Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Cotton T-Shirt",
                )
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "productCategory" in violations[0][0]

    def test_product_with_non_textile_hs_code(self, rule: TextileHSCodeRule):
        """Test product with non-textile HS code produces violation."""
        from dppvalidator.models import Classification, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Electronic Device",
                    productCategory=[
                        Classification(
                            id="https://hs.org/8471",
                            name="Computers",
                            code="8471",
                        )
                    ],
                )
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "50-63" in violations[0][1]


class TestTextileMaterialCompositionRule:
    """Tests for TXT002: Material composition validation."""

    @pytest.fixture
    def rule(self) -> TextileMaterialCompositionRule:
        """Create rule instance."""
        return TextileMaterialCompositionRule()

    def test_rule_attributes(self, rule: TextileMaterialCompositionRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "TXT002"
        assert rule.severity == "error"

    def test_no_materials_produces_violation(self, rule: TextileMaterialCompositionRule):
        """Test no materials produces violation."""
        from dppvalidator.models import ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "materialsProvenance" in violations[0][0]

    def test_materials_with_fraction_no_violations(self, rule: TextileMaterialCompositionRule):
        """Test materials with mass fraction produces no violations."""
        from dppvalidator.models import Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materialsProvenance=[
                    Material(name="Cotton", massFraction=0.95),
                    Material(name="Elastane", massFraction=0.05),
                ]
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_materials_without_fraction_produces_violation(
        self, rule: TextileMaterialCompositionRule
    ):
        """Test materials without mass fraction produces violation."""
        from dppvalidator.models import Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materialsProvenance=[
                    Material(name="Cotton"),
                    Material(name="Elastane"),
                ]
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "fiber" in violations[0][1].lower() or "fraction" in violations[0][1].lower()


class TestTextileMicroplasticRule:
    """Tests for TXT003: Microplastic release validation."""

    @pytest.fixture
    def rule(self) -> TextileMicroplasticRule:
        """Create rule instance."""
        return TextileMicroplasticRule()

    def test_rule_attributes(self, rule: TextileMicroplasticRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "TXT003"
        assert rule.severity == "info"

    def test_no_materials_no_violations(self, rule: TextileMicroplasticRule):
        """Test no materials produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_natural_fiber_no_violations(self, rule: TextileMicroplasticRule):
        """Test natural fiber produces no violations."""
        from dppvalidator.models import Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materialsProvenance=[
                    Material(name="Cotton", massFraction=1.0),
                ]
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_synthetic_fiber_without_scorecard_produces_info(self, rule: TextileMicroplasticRule):
        """Test synthetic fiber without scorecard produces info."""
        from dppvalidator.models import Material, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                materialsProvenance=[
                    Material(name="Polyester", massFraction=1.0),
                ]
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "microplastic" in violations[0][1].lower()


class TestTextileDurabilityRule:
    """Tests for TXT004: Durability information validation."""

    @pytest.fixture
    def rule(self) -> TextileDurabilityRule:
        """Create rule instance."""
        return TextileDurabilityRule()

    def test_rule_attributes(self, rule: TextileDurabilityRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "TXT004"
        assert rule.severity == "info"

    def test_no_product_no_violations(self, rule: TextileDurabilityRule):
        """Test no product produces no violations."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_product_without_characteristics_produces_info(self, rule: TextileDurabilityRule):
        """Test product without characteristics produces info."""
        from dppvalidator.models import Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Test Product",
                )
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "durability" in violations[0][1].lower()


class TestTextileCareInstructionsRule:
    """Tests for TXT005: Care instructions validation."""

    @pytest.fixture
    def rule(self) -> TextileCareInstructionsRule:
        """Create rule instance."""
        return TextileCareInstructionsRule()

    def test_rule_attributes(self, rule: TextileCareInstructionsRule):
        """Test rule has correct attributes."""
        assert rule.rule_id == "TXT005"
        assert rule.severity == "info"

    def test_product_with_further_info_no_violations(self, rule: TextileCareInstructionsRule):
        """Test product with further information produces no violations."""
        from dppvalidator.models import Link, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Test Product",
                    furtherInformation=[Link(linkURL="https://example.com/care")],
                )
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 0

    def test_product_without_further_info_produces_info(self, rule: TextileCareInstructionsRule):
        """Test product without further information produces info."""
        from dppvalidator.models import Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Test Product",
                )
            ),
        )
        violations = rule.check(passport)
        assert len(violations) == 1
        assert "care" in violations[0][1].lower()


class TestIsTextileProduct:
    """Tests for is_textile_product function."""

    def test_not_textile_no_subject(self):
        """Test no credential subject returns False."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        assert is_textile_product(passport) is False

    def test_not_textile_no_category(self):
        """Test no product category returns False."""
        from dppvalidator.models import Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Test Product",
                )
            ),
        )
        assert is_textile_product(passport) is False

    def test_is_textile_with_hs_code(self):
        """Test textile HS code returns True."""
        from dppvalidator.models import Classification, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Cotton T-Shirt",
                    productCategory=[
                        Classification(
                            id="https://hs.org/6109",
                            name="T-shirts",
                            code="6109",
                        )
                    ],
                )
            ),
        )
        assert is_textile_product(passport) is True

    def test_not_textile_with_non_textile_hs_code(self):
        """Test non-textile HS code returns False."""
        from dppvalidator.models import Classification, Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product",
                    name="Electronic Device",
                    productCategory=[
                        Classification(
                            id="https://hs.org/8471",
                            name="Computers",
                            code="8471",
                        )
                    ],
                )
            ),
        )
        assert is_textile_product(passport) is False
