"""Tests for EU DPP Core Ontology substances of concern (Phase 3)."""

from decimal import Decimal

import pytest

from dppvalidator.vocabularies.eudpp_substances import (
    CAS_NUMBER_PATTERN,
    EC_NUMBER_PATTERN,
    Concentration,
    ConcentrationOfSubstanceOfConcern,
    EUDPPSubstanceClass,
    HazardCategory,
    LifeCycleStage,
    Substance,
    SubstanceOfConcern,
    Threshold,
    get_all_hazard_categories,
    get_lifecycle_stages,
    is_pop,
    is_svhc,
    is_valid_cas_number,
    is_valid_ec_number,
    validate_cas_checksum,
)


class TestEUDPPSubstanceClass:
    """Tests for EUDPPSubstanceClass enum."""

    def test_substance_classes_exist(self):
        """Test substance class URIs exist."""
        assert EUDPPSubstanceClass.SUBSTANCE.value == "eudpp:Substance"
        assert EUDPPSubstanceClass.SUBSTANCE_OF_CONCERN.value == "eudpp:SubstanceOfConcern"
        assert EUDPPSubstanceClass.CONCENTRATION.value == "eudpp:Concentration"
        assert EUDPPSubstanceClass.THRESHOLD.value == "eudpp:Threshold"


class TestLifeCycleStage:
    """Tests for LifeCycleStage enum."""

    def test_lifecycle_stages_exist(self):
        """Test lifecycle stage values exist."""
        assert LifeCycleStage.PRODUCTION.value == "production"
        assert LifeCycleStage.IN_PRODUCT.value == "in_product"
        assert LifeCycleStage.USE.value == "use"
        assert LifeCycleStage.END_OF_LIFE.value == "end_of_life"
        assert LifeCycleStage.WASTE.value == "waste"
        assert LifeCycleStage.RECYCLING.value == "recycling"


class TestHazardCategory:
    """Tests for HazardCategory enum."""

    def test_carcinogenicity_categories(self):
        """Test carcinogenicity hazard categories."""
        assert HazardCategory.CARCINOGENICITY_1.value == "carcinogenicity_cat_1"
        assert HazardCategory.CARCINOGENICITY_2.value == "carcinogenicity_cat_2"

    def test_mutagenicity_categories(self):
        """Test mutagenicity hazard categories."""
        assert HazardCategory.MUTAGENICITY_1.value == "mutagenicity_cat_1"
        assert HazardCategory.MUTAGENICITY_2.value == "mutagenicity_cat_2"

    def test_svhc_and_pop(self):
        """Test SVHC and POP categories."""
        assert HazardCategory.SVHC.value == "svhc_reach_art_57"
        assert HazardCategory.POP.value == "persistent_organic_pollutant"


class TestCASNumberValidation:
    """Tests for CAS number validation."""

    def test_valid_cas_numbers(self):
        """Test valid CAS number formats."""
        assert is_valid_cas_number("50-00-0")  # Formaldehyde
        assert is_valid_cas_number("7440-23-5")  # Sodium
        assert is_valid_cas_number("15829-53-5")  # Mercurous Oxide
        assert is_valid_cas_number("1234567-89-0")  # Max digits

    def test_invalid_cas_numbers(self):
        """Test invalid CAS number formats."""
        assert not is_valid_cas_number("invalid")
        assert not is_valid_cas_number("50-00")  # Missing check digit
        assert not is_valid_cas_number("5-00-0")  # Too few leading digits
        assert not is_valid_cas_number("50-0-0")  # Wrong middle format
        assert not is_valid_cas_number("50-00-00")  # Too many check digits

    def test_cas_pattern(self):
        """Test CAS_NUMBER_PATTERN regex."""
        assert CAS_NUMBER_PATTERN.match("50-00-0")
        assert not CAS_NUMBER_PATTERN.match("invalid")


class TestECNumberValidation:
    """Tests for EC number validation."""

    def test_valid_ec_numbers(self):
        """Test valid EC number formats."""
        assert is_valid_ec_number("200-001-8")  # Formaldehyde
        assert is_valid_ec_number("231-132-9")  # Sodium
        assert is_valid_ec_number("239-934-0")  # Mercurous Oxide

    def test_invalid_ec_numbers(self):
        """Test invalid EC number formats."""
        assert not is_valid_ec_number("invalid")
        assert not is_valid_ec_number("20-001-8")  # Too few leading digits
        assert not is_valid_ec_number("200-01-8")  # Too few middle digits
        assert not is_valid_ec_number("200-001-88")  # Too many check digits

    def test_ec_pattern(self):
        """Test EC_NUMBER_PATTERN regex."""
        assert EC_NUMBER_PATTERN.match("200-001-8")
        assert not EC_NUMBER_PATTERN.match("invalid")


class TestCASChecksumValidation:
    """Tests for CAS checksum validation."""

    def test_valid_checksums(self):
        """Test valid CAS checksums."""
        assert validate_cas_checksum("50-00-0")  # Formaldehyde
        assert validate_cas_checksum("7440-23-5")  # Sodium

    def test_invalid_checksums(self):
        """Test invalid CAS checksums."""
        assert not validate_cas_checksum("50-00-1")  # Wrong check digit
        assert not validate_cas_checksum("invalid")


class TestSubstance:
    """Tests for Substance dataclass."""

    def test_create_substance(self):
        """Test creating a substance."""
        substance = Substance(
            name_iupac="Methanal",
            name_cas="Formaldehyde",
        )
        assert substance._class_uri == "eudpp:Substance"
        assert substance.name_iupac == "Methanal"
        assert substance.name_cas == "Formaldehyde"

    def test_create_substance_minimal(self):
        """Test creating substance with minimal fields."""
        substance = Substance()
        assert substance._class_uri == "eudpp:Substance"
        assert substance.name_iupac is None

    def test_substance_immutable(self):
        """Test substance is immutable."""
        substance = Substance(name_iupac="Test")
        with pytest.raises(AttributeError):
            substance.name_iupac = "Modified"  # type: ignore[misc]


class TestSubstanceOfConcern:
    """Tests for SubstanceOfConcern dataclass."""

    def test_create_soc(self):
        """Test creating a substance of concern."""
        soc = SubstanceOfConcern(
            name_iupac="Methanal",
            name_cas="Formaldehyde",
            number_cas="50-00-0",
            number_ec="200-001-8",
            hazard_category=HazardCategory.CARCINOGENICITY_1.value,
        )
        assert soc._class_uri == "eudpp:SubstanceOfConcern"
        assert soc.number_cas == "50-00-0"
        assert soc.number_ec == "200-001-8"

    def test_soc_validate_identifiers_valid(self):
        """Test validate_identifiers with valid identifiers."""
        soc = SubstanceOfConcern(
            number_cas="50-00-0",
            number_ec="200-001-8",
        )
        errors = soc.validate_identifiers()
        assert len(errors) == 0

    def test_soc_validate_identifiers_invalid_cas(self):
        """Test validate_identifiers with invalid CAS number."""
        soc = SubstanceOfConcern(number_cas="invalid")
        errors = soc.validate_identifiers()
        assert len(errors) == 1
        assert "CAS number" in errors[0]

    def test_soc_validate_identifiers_invalid_ec(self):
        """Test validate_identifiers with invalid EC number."""
        soc = SubstanceOfConcern(number_ec="invalid")
        errors = soc.validate_identifiers()
        assert len(errors) == 1
        assert "EC number" in errors[0]

    def test_soc_has_valid_identification_true(self):
        """Test has_valid_identification returns True."""
        soc = SubstanceOfConcern(name_iupac="Methanal")
        assert soc.has_valid_identification()

    def test_soc_has_valid_identification_false(self):
        """Test has_valid_identification returns False."""
        soc = SubstanceOfConcern()
        assert not soc.has_valid_identification()

    def test_soc_with_location_and_lifecycle(self):
        """Test SOC with location and lifecycle stage."""
        soc = SubstanceOfConcern(
            name_iupac="Lead",
            substance_location="Battery electrode",
            lifecycle_stage=LifeCycleStage.IN_PRODUCT.value,
            impact_on_health="Neurotoxic effects",
            impact_on_environment="Soil contamination",
        )
        assert soc.substance_location == "Battery electrode"
        assert soc.lifecycle_stage == "in_product"


class TestConcentration:
    """Tests for Concentration dataclass."""

    def test_create_concentration(self):
        """Test creating a concentration."""
        conc = Concentration(
            value=Decimal("0.1"),
            unit="%w/w",
        )
        assert conc._class_uri == "eudpp:Concentration"
        assert conc.value == Decimal("0.1")
        assert conc.unit == "%w/w"

    def test_concentration_range(self):
        """Test concentration with range."""
        conc = Concentration(
            value=Decimal("0.15"),
            unit="%w/w",
            range_min=Decimal("0.1"),
            range_max=Decimal("0.2"),
        )
        assert conc.is_range()
        assert conc.range_min == Decimal("0.1")
        assert conc.range_max == Decimal("0.2")

    def test_concentration_not_range(self):
        """Test concentration without range."""
        conc = Concentration(value=Decimal("0.1"), unit="%w/w")
        assert not conc.is_range()

    def test_concentration_validate_valid(self):
        """Test validate with valid concentration."""
        conc = Concentration(
            value=Decimal("0.1"),
            unit="%w/w",
            range_min=Decimal("0.05"),
            range_max=Decimal("0.15"),
        )
        errors = conc.validate()
        assert len(errors) == 0

    def test_concentration_validate_negative_value(self):
        """Test validate with negative value."""
        conc = Concentration(value=Decimal("-0.1"), unit="%w/w")
        errors = conc.validate()
        assert len(errors) == 1
        assert "negative" in errors[0]

    def test_concentration_validate_invalid_range(self):
        """Test validate with min > max."""
        conc = Concentration(
            value=Decimal("0.1"),
            unit="%w/w",
            range_min=Decimal("0.2"),
            range_max=Decimal("0.1"),
        )
        errors = conc.validate()
        assert len(errors) == 1
        assert "cannot exceed" in errors[0]

    def test_concentration_immutable(self):
        """Test concentration is immutable."""
        conc = Concentration(value=Decimal("0.1"), unit="%w/w")
        with pytest.raises(AttributeError):
            conc.value = Decimal("0.2")  # type: ignore[misc]


class TestThreshold:
    """Tests for Threshold dataclass."""

    def test_create_threshold(self):
        """Test creating a threshold."""
        threshold = Threshold(
            value=Decimal("0.1"),
            unit="%w/w",
            regulation_reference="REACH Annex XVII",
        )
        assert threshold._class_uri == "eudpp:Threshold"
        assert threshold.value == Decimal("0.1")
        assert threshold.regulation_reference == "REACH Annex XVII"

    def test_threshold_validate_valid(self):
        """Test validate with valid threshold."""
        threshold = Threshold(value=Decimal("0.1"), unit="%w/w")
        errors = threshold.validate()
        assert len(errors) == 0

    def test_threshold_validate_negative(self):
        """Test validate with negative threshold."""
        threshold = Threshold(value=Decimal("-0.1"), unit="%w/w")
        errors = threshold.validate()
        assert len(errors) == 1
        assert "negative" in errors[0]


class TestConcentrationOfSubstanceOfConcern:
    """Tests for ConcentrationOfSubstanceOfConcern dataclass."""

    def test_create_concentration_of_soc(self):
        """Test creating a concentration of SOC."""
        soc = SubstanceOfConcern(name_iupac="Lead", number_cas="7439-92-1")
        conc = Concentration(value=Decimal("0.15"), unit="%w/w")
        threshold = Threshold(value=Decimal("0.1"), unit="%w/w")

        csoc = ConcentrationOfSubstanceOfConcern(
            substance=soc,
            concentration=conc,
            threshold=threshold,
        )
        assert csoc.substance.name_iupac == "Lead"
        assert csoc.concentration.value == Decimal("0.15")

    def test_exceeds_threshold_true(self):
        """Test exceeds_threshold returns True."""
        soc = SubstanceOfConcern(name_iupac="Lead")
        conc = Concentration(value=Decimal("0.15"), unit="%w/w")
        threshold = Threshold(value=Decimal("0.1"), unit="%w/w")

        csoc = ConcentrationOfSubstanceOfConcern(
            substance=soc, concentration=conc, threshold=threshold
        )
        assert csoc.exceeds_threshold() is True

    def test_exceeds_threshold_false(self):
        """Test exceeds_threshold returns False."""
        soc = SubstanceOfConcern(name_iupac="Lead")
        conc = Concentration(value=Decimal("0.05"), unit="%w/w")
        threshold = Threshold(value=Decimal("0.1"), unit="%w/w")

        csoc = ConcentrationOfSubstanceOfConcern(
            substance=soc, concentration=conc, threshold=threshold
        )
        assert csoc.exceeds_threshold() is False

    def test_exceeds_threshold_no_threshold(self):
        """Test exceeds_threshold returns None without threshold."""
        soc = SubstanceOfConcern(name_iupac="Lead")
        conc = Concentration(value=Decimal("0.15"), unit="%w/w")

        csoc = ConcentrationOfSubstanceOfConcern(substance=soc, concentration=conc, threshold=None)
        assert csoc.exceeds_threshold() is None

    def test_exceeds_threshold_different_units(self):
        """Test exceeds_threshold returns None for different units."""
        soc = SubstanceOfConcern(name_iupac="Lead")
        conc = Concentration(value=Decimal("1500"), unit="ppm")
        threshold = Threshold(value=Decimal("0.1"), unit="%w/w")

        csoc = ConcentrationOfSubstanceOfConcern(
            substance=soc, concentration=conc, threshold=threshold
        )
        assert csoc.exceeds_threshold() is None


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_all_hazard_categories(self):
        """Test get_all_hazard_categories function."""
        categories = get_all_hazard_categories()
        assert len(categories) > 0
        assert "carcinogenicity_cat_1" in categories
        assert "svhc_reach_art_57" in categories

    def test_get_lifecycle_stages(self):
        """Test get_lifecycle_stages function."""
        stages = get_lifecycle_stages()
        assert len(stages) == 6
        assert "production" in stages
        assert "waste" in stages

    def test_is_svhc(self):
        """Test is_svhc function."""
        assert is_svhc(HazardCategory.SVHC.value)
        assert not is_svhc(HazardCategory.CARCINOGENICITY_1.value)

    def test_is_pop(self):
        """Test is_pop function."""
        assert is_pop(HazardCategory.POP.value)
        assert not is_pop(HazardCategory.SVHC.value)
