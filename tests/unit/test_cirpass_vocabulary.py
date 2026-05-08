"""Tests for CIRPASS-2 vocabulary module."""

import pytest

from dppvalidator.vocabularies.cirpass_terms import (
    CIRPASS_CORE_TERMS,
    ESPR_ANNEX_I_PARAMETERS,
    CIRPASSTerm,
    CIRPASSVocabulary,
    ESPRAnnexIParameter,
    GranularityLevel,
    get_cirpass_term_count,
    get_espr_parameters,
    is_valid_espr_parameter,
    is_valid_granularity_level,
)


class TestGranularityLevel:
    """Tests for GranularityLevel enum."""

    def test_granularity_levels_exist(self):
        """Test all granularity levels exist."""
        assert GranularityLevel.MODEL.value == "model"
        assert GranularityLevel.BATCH.value == "batch"
        assert GranularityLevel.PRODUCT.value == "product"

    def test_granularity_level_from_string(self):
        """Test creating granularity level from string."""
        assert GranularityLevel("model") == GranularityLevel.MODEL
        assert GranularityLevel("batch") == GranularityLevel.BATCH
        assert GranularityLevel("product") == GranularityLevel.PRODUCT

    def test_item_is_deprecated_alias(self):
        """Test ITEM is deprecated alias for PRODUCT."""
        # ITEM now maps to 'product' for backward compatibility
        assert GranularityLevel.ITEM.value == "product"

    def test_invalid_granularity_level(self):
        """Test invalid granularity level raises ValueError."""
        with pytest.raises(ValueError):
            GranularityLevel("invalid")


class TestESPRAnnexIParameter:
    """Tests for ESPRAnnexIParameter enum."""

    def test_espr_parameters_exist(self):
        """Test key ESPR parameters exist."""
        assert ESPRAnnexIParameter.DURABILITY.value == "durability"
        assert ESPRAnnexIParameter.CARBON_FOOTPRINT.value == "carbon_footprint"
        assert ESPRAnnexIParameter.RECYCLABILITY.value == "recyclability"

    def test_espr_parameter_count(self):
        """Test ESPR parameter count."""
        assert len(ESPRAnnexIParameter) >= 18


class TestCIRPASSTerm:
    """Tests for CIRPASSTerm dataclass."""

    def test_term_creation(self):
        """Test creating a CIRPASS term."""
        term = CIRPASSTerm(
            name="TestTerm",
            definition="A test term definition.",
            source="ESPR",
            article="Art 2(1)",
        )
        assert term.name == "TestTerm"
        assert term.definition == "A test term definition."
        assert term.source == "ESPR"
        assert term.article == "Art 2(1)"

    def test_term_without_article(self):
        """Test creating a term without article reference."""
        term = CIRPASSTerm(
            name="TestTerm",
            definition="A test definition.",
            source="CIRPASS-2",
        )
        assert term.article is None

    def test_term_is_frozen(self):
        """Test CIRPASSTerm is immutable."""
        term = CIRPASSTerm(
            name="TestTerm",
            definition="A test definition.",
            source="ESPR",
        )
        with pytest.raises(AttributeError):
            term.name = "NewName"


class TestCIRPASSCoreTerms:
    """Tests for CIRPASS core terms dictionary."""

    def test_core_terms_not_empty(self):
        """Test core terms dictionary is not empty."""
        assert len(CIRPASS_CORE_TERMS) > 0

    def test_core_terms_minimum_count(self):
        """Test minimum number of core terms."""
        assert len(CIRPASS_CORE_TERMS) >= 20

    def test_product_term_exists(self):
        """Test Product term exists."""
        assert "Product" in CIRPASS_CORE_TERMS
        product = CIRPASS_CORE_TERMS["Product"]
        assert product.source == "ESPR"
        assert "Art 2(1)" in product.article

    def test_model_term_exists(self):
        """Test Model term exists."""
        assert "Model" in CIRPASS_CORE_TERMS
        model = CIRPASS_CORE_TERMS["Model"]
        assert model.source == "SR5423"

    def test_batch_term_exists(self):
        """Test Batch term exists."""
        assert "Batch" in CIRPASS_CORE_TERMS
        batch = CIRPASS_CORE_TERMS["Batch"]
        assert batch.source == "SR5423"

    def test_item_term_exists(self):
        """Test Item term exists."""
        assert "Item" in CIRPASS_CORE_TERMS
        item = CIRPASS_CORE_TERMS["Item"]
        assert item.source == "SR5423"

    def test_unique_product_identifier_exists(self):
        """Test UniqueProductIdentifier term exists."""
        assert "UniqueProductIdentifier" in CIRPASS_CORE_TERMS

    def test_digital_product_passport_exists(self):
        """Test DigitalProductPassport term exists."""
        assert "DigitalProductPassport" in CIRPASS_CORE_TERMS

    def test_all_terms_have_required_fields(self):
        """Test all terms have required fields."""
        for name, term in CIRPASS_CORE_TERMS.items():
            assert term.name == name
            assert term.definition
            assert term.source in {"ESPR", "SR5423", "CIRPASS-2"}


class TestCIRPASSVocabulary:
    """Tests for CIRPASSVocabulary class."""

    def test_get_term_exists(self):
        """Test getting an existing term."""
        term = CIRPASSVocabulary.get_term("Product")
        assert term is not None
        assert term.name == "Product"

    def test_get_term_not_exists(self):
        """Test getting a non-existent term."""
        term = CIRPASSVocabulary.get_term("NonExistentTerm")
        assert term is None

    def test_is_valid_term_true(self):
        """Test is_valid_term returns True for valid term."""
        assert CIRPASSVocabulary.is_valid_term("Product") is True
        assert CIRPASSVocabulary.is_valid_term("Model") is True

    def test_is_valid_term_false(self):
        """Test is_valid_term returns False for invalid term."""
        assert CIRPASSVocabulary.is_valid_term("InvalidTerm") is False

    def test_get_terms_by_source_espr(self):
        """Test getting terms by ESPR source."""
        espr_terms = CIRPASSVocabulary.get_terms_by_source("ESPR")
        assert len(espr_terms) > 0
        for term in espr_terms:
            assert term.source == "ESPR"

    def test_get_terms_by_source_sr5423(self):
        """Test getting terms by SR5423 source."""
        sr_terms = CIRPASSVocabulary.get_terms_by_source("SR5423")
        assert len(sr_terms) > 0
        for term in sr_terms:
            assert term.source == "SR5423"

    def test_get_terms_by_source_cirpass2(self):
        """Test getting terms by CIRPASS-2 source."""
        cp_terms = CIRPASSVocabulary.get_terms_by_source("CIRPASS-2")
        assert len(cp_terms) > 0
        for term in cp_terms:
            assert term.source == "CIRPASS-2"

    def test_all_term_names(self):
        """Test getting all term names."""
        names = CIRPASSVocabulary.all_term_names()
        assert isinstance(names, frozenset)
        assert len(names) == len(CIRPASS_CORE_TERMS)
        assert "Product" in names
        assert "Model" in names


class TestGranularityValidation:
    """Tests for granularity level validation."""

    def test_valid_granularity_levels(self):
        """Test valid granularity levels."""
        assert is_valid_granularity_level("model") is True
        assert is_valid_granularity_level("batch") is True
        assert is_valid_granularity_level("product") is True

    def test_valid_granularity_case_insensitive(self):
        """Test granularity validation is case insensitive."""
        assert is_valid_granularity_level("MODEL") is True
        assert is_valid_granularity_level("Batch") is True
        assert is_valid_granularity_level("PRODUCT") is True

    def test_invalid_granularity_level(self):
        """Test invalid granularity level."""
        assert is_valid_granularity_level("invalid") is False
        assert is_valid_granularity_level("") is False
        assert is_valid_granularity_level("item") is False  # 'item' is no longer valid


class TestESPRParameterValidation:
    """Tests for ESPR parameter validation."""

    def test_valid_espr_parameters(self):
        """Test valid ESPR parameters."""
        assert is_valid_espr_parameter("durability") is True
        assert is_valid_espr_parameter("carbon_footprint") is True
        assert is_valid_espr_parameter("recyclability") is True

    def test_espr_parameter_normalization(self):
        """Test ESPR parameter normalization."""
        assert is_valid_espr_parameter("carbon-footprint") is True
        assert is_valid_espr_parameter("carbon footprint") is True
        assert is_valid_espr_parameter("DURABILITY") is True

    def test_invalid_espr_parameter(self):
        """Test invalid ESPR parameter."""
        assert is_valid_espr_parameter("invalid_param") is False
        assert is_valid_espr_parameter("") is False

    def test_get_espr_parameters(self):
        """Test getting all ESPR parameters."""
        params = get_espr_parameters()
        assert isinstance(params, frozenset)
        assert len(params) >= 18
        assert "durability" in params
        assert "carbon_footprint" in params


class TestESPRAnnexIParameters:
    """Tests for ESPR_ANNEX_I_PARAMETERS constant."""

    def test_parameters_is_frozenset(self):
        """Test ESPR_ANNEX_I_PARAMETERS is a frozenset."""
        assert isinstance(ESPR_ANNEX_I_PARAMETERS, frozenset)

    def test_key_parameters_present(self):
        """Test key parameters are present."""
        assert "durability" in ESPR_ANNEX_I_PARAMETERS
        assert "reliability" in ESPR_ANNEX_I_PARAMETERS
        assert "ease_of_repair" in ESPR_ANNEX_I_PARAMETERS
        assert "recyclability" in ESPR_ANNEX_I_PARAMETERS
        assert "carbon_footprint" in ESPR_ANNEX_I_PARAMETERS
        assert "environmental_footprint" in ESPR_ANNEX_I_PARAMETERS


class TestTermCount:
    """Tests for term count function."""

    def test_get_cirpass_term_count(self):
        """Test getting CIRPASS term count."""
        count = get_cirpass_term_count()
        assert count >= 20
        assert count == len(CIRPASS_CORE_TERMS)
