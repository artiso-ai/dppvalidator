"""Tests for EU DPP Core Ontology LCA module (Phase 4)."""

from decimal import Decimal

import pytest

from dppvalidator.vocabularies.eudpp_lca import (
    IMPACT_CATEGORY_UNITS,
    LCA_NAMESPACE,
    LCA_PREFIX,
    CharacterizationFactor,
    CharacterizationModel,
    EnvironmentalImpact,
    ImpactCategory,
    ImpactCategoryIndicator,
    ImpactResult,
    LCAClass,
    LCAMethod,
    LCAMethodology,
    ProductEnvironmentalFootprint,
    compact_lca_uri,
    expand_lca_uri,
    get_all_characterization_models,
    get_all_impact_categories,
    get_all_impact_indicators,
    get_impact_category_unit,
    is_climate_related,
    is_resource_related,
    is_toxicity_related,
)


class TestLCANamespace:
    """Tests for LCA namespace constants."""

    def test_namespace_constants(self):
        """Test LCA namespace constants are defined."""
        assert LCA_NAMESPACE == "http://dpp.cea.fr/EUDPP/LCA#"
        assert LCA_PREFIX == "lca"


class TestLCAClass:
    """Tests for LCAClass enum."""

    def test_lca_classes_exist(self):
        """Test LCA class URIs exist."""
        assert LCAClass.ENVIRONMENTAL_FOOTPRINT.value == "lca:Environmental_Footprint"
        assert LCAClass.CARBON_FOOTPRINT.value == "lca:Carbon_Footprint"
        assert LCAClass.MATERIAL_FOOTPRINT.value == "lca:Material_Footprint"
        assert LCAClass.IMPACT_CATEGORY.value == "lca:Impact_Category"
        assert LCAClass.CHARACTERIZATION_MODEL.value == "lca:Characterization_Model"


class TestImpactCategory:
    """Tests for ImpactCategory enum."""

    def test_all_16_pef_categories_exist(self):
        """Test all 16 PEF 3.1 impact categories are defined."""
        categories = list(ImpactCategory)
        assert len(categories) == 16

    def test_climate_change_category(self):
        """Test climate change category."""
        assert ImpactCategory.CLIMATE_CHANGE.value == "lca:Climate_change_total"

    def test_toxicity_categories(self):
        """Test toxicity categories."""
        assert ImpactCategory.HUMAN_TOXICITY_CANCER.value == "lca:Human_toxicity_cancer"
        assert ImpactCategory.HUMAN_TOXICITY_NON_CANCER.value == "lca:Human_toxicity_non_cancer"
        assert ImpactCategory.ECOTOXICITY_FRESHWATER.value == "lca:Ecotoxicity_freshwater"

    def test_eutrophication_categories(self):
        """Test eutrophication categories."""
        assert ImpactCategory.EUTROPHICATION_FRESHWATER.value == "lca:Eutrophication_freshwater"
        assert ImpactCategory.EUTROPHICATION_MARINE.value == "lca:Eutrophication_marine"
        assert ImpactCategory.EUTROPHICATION_TERRESTRIAL.value == "lca:Eutrophication_terrestrial"

    def test_resource_categories(self):
        """Test resource use categories."""
        assert ImpactCategory.RESOURCE_FOSSILS.value == "lca:Resource_use_fossils"
        assert ImpactCategory.RESOURCE_MINERALS.value == "lca:Resource_use_minerals_and_metals"
        assert ImpactCategory.WATER_USE.value == "lca:Water_use"


class TestImpactCategoryIndicator:
    """Tests for ImpactCategoryIndicator enum."""

    def test_gwp100_indicator(self):
        """Test GWP100 indicator."""
        assert ImpactCategoryIndicator.GWP100.value == "lca:Global_Warming_Potential_GWP100"

    def test_toxicity_indicators(self):
        """Test toxicity indicators."""
        assert ImpactCategoryIndicator.CTUH.value == "lca:Comparative_Toxic_Unit_for_humans_CTUh"
        assert (
            ImpactCategoryIndicator.CTUE.value == "lca:Comparative_Toxic_Unit_for_ecosystems_CTUe"
        )


class TestCharacterizationModel:
    """Tests for CharacterizationModel enum."""

    def test_ipcc_model(self):
        """Test IPCC model."""
        assert CharacterizationModel.IPCC_2021.value == "lca:Bern_model_based_on_IPCC_2021"

    def test_usetox_model(self):
        """Test USEtox model."""
        assert CharacterizationModel.USETOX_2_1.value == "lca:Based_on_USEtox2.1_model"

    def test_aware_model(self):
        """Test AWARE model."""
        assert CharacterizationModel.AWARE.value == "lca:Available_WAter_REmaining_AWARE_model"


class TestImpactCategoryUnits:
    """Tests for impact category units mapping."""

    def test_climate_change_unit(self):
        """Test climate change unit."""
        assert IMPACT_CATEGORY_UNITS[ImpactCategory.CLIMATE_CHANGE.value] == "kg CO2-eq"

    def test_ozone_depletion_unit(self):
        """Test ozone depletion unit."""
        assert IMPACT_CATEGORY_UNITS[ImpactCategory.OZONE_DEPLETION.value] == "kg CFC-11-eq"

    def test_water_use_unit(self):
        """Test water use unit."""
        assert IMPACT_CATEGORY_UNITS[ImpactCategory.WATER_USE.value] == "m³ world-eq"


class TestImpactResult:
    """Tests for ImpactResult dataclass."""

    def test_create_impact_result(self):
        """Test creating an impact result."""
        result = ImpactResult(
            category=ImpactCategory.CLIMATE_CHANGE.value,
            value=Decimal("12.5"),
            unit="kg CO2-eq",
            indicator=ImpactCategoryIndicator.GWP100.value,
            model=CharacterizationModel.IPCC_2021.value,
        )
        assert result.category == "lca:Climate_change_total"
        assert result.value == Decimal("12.5")
        assert result.unit == "kg CO2-eq"

    def test_validate_valid_category(self):
        """Test validate with valid category."""
        result = ImpactResult(
            category=ImpactCategory.CLIMATE_CHANGE.value,
            value=Decimal("12.5"),
            unit="kg CO2-eq",
        )
        errors = result.validate()
        assert len(errors) == 0

    def test_validate_invalid_category(self):
        """Test validate with invalid category."""
        result = ImpactResult(
            category="lca:Unknown_category",
            value=Decimal("12.5"),
            unit="kg CO2-eq",
        )
        errors = result.validate()
        assert len(errors) == 1
        assert "Unknown impact category" in errors[0]

    def test_impact_result_immutable(self):
        """Test impact result is immutable."""
        result = ImpactResult(
            category=ImpactCategory.CLIMATE_CHANGE.value,
            value=Decimal("12.5"),
            unit="kg CO2-eq",
        )
        with pytest.raises(AttributeError):
            result.value = Decimal("20.0")  # type: ignore[misc]


class TestCharacterizationFactor:
    """Tests for CharacterizationFactor dataclass."""

    def test_create_characterization_factor(self):
        """Test creating a characterization factor."""
        cf = CharacterizationFactor(
            name="GWP-100",
            value=Decimal("1.0"),
            unit="kg CO2-eq/kg",
            model=CharacterizationModel.IPCC_2021.value,
        )
        assert cf.name == "GWP-100"
        assert cf.model == "lca:Bern_model_based_on_IPCC_2021"


class TestLCAMethodology:
    """Tests for LCAMethodology dataclass."""

    def test_create_methodology(self):
        """Test creating an LCA methodology."""
        methodology = LCAMethodology(
            name="EF v3.1",
            version="3.1",
            description="Product Environmental Footprint methodology",
        )
        assert methodology.name == "EF v3.1"
        assert methodology.version == "3.1"


class TestLCAMethod:
    """Tests for LCAMethod dataclass."""

    def test_create_method(self):
        """Test creating an LCA method."""
        method = LCAMethod(
            name="Climate change impact assessment",
            methodology="PEF 3.1",
            characterization_model=CharacterizationModel.IPCC_2021.value,
        )
        assert method.name == "Climate change impact assessment"


class TestEnvironmentalImpact:
    """Tests for EnvironmentalImpact dataclass."""

    def test_create_environmental_impact(self):
        """Test creating an environmental impact."""
        impact = EnvironmentalImpact(
            description="CO2 emissions from manufacturing",
            lifecycle_stage="production",
        )
        assert impact.description == "CO2 emissions from manufacturing"


class TestProductEnvironmentalFootprint:
    """Tests for ProductEnvironmentalFootprint dataclass."""

    def test_create_pef(self):
        """Test creating a PEF result."""
        pef = ProductEnvironmentalFootprint(
            product_name="Test Product",
            functional_unit="1 kg",
            methodology_version="PEF 3.1",
        )
        assert pef.product_name == "Test Product"
        assert pef.methodology_version == "PEF 3.1"

    def test_get_impact_found(self):
        """Test get_impact when category exists."""
        result = ImpactResult(
            category=ImpactCategory.CLIMATE_CHANGE.value,
            value=Decimal("12.5"),
            unit="kg CO2-eq",
        )
        pef = ProductEnvironmentalFootprint(
            product_name="Test",
            impact_results=(result,),
        )
        found = pef.get_impact(ImpactCategory.CLIMATE_CHANGE)
        assert found is not None
        assert found.value == Decimal("12.5")

    def test_get_impact_not_found(self):
        """Test get_impact when category doesn't exist."""
        pef = ProductEnvironmentalFootprint(product_name="Test")
        found = pef.get_impact(ImpactCategory.CLIMATE_CHANGE)
        assert found is None

    def test_has_all_categories_false(self):
        """Test has_all_categories returns False when incomplete."""
        pef = ProductEnvironmentalFootprint(product_name="Test")
        assert not pef.has_all_categories()

    def test_has_all_categories_true(self):
        """Test has_all_categories returns True when complete."""
        results = tuple(
            ImpactResult(
                category=cat.value,
                value=Decimal("1.0"),
                unit="unit",
            )
            for cat in ImpactCategory
        )
        pef = ProductEnvironmentalFootprint(
            product_name="Test",
            impact_results=results,
        )
        assert pef.has_all_categories()

    def test_missing_categories(self):
        """Test missing_categories returns correct list."""
        result = ImpactResult(
            category=ImpactCategory.CLIMATE_CHANGE.value,
            value=Decimal("12.5"),
            unit="kg CO2-eq",
        )
        pef = ProductEnvironmentalFootprint(
            product_name="Test",
            impact_results=(result,),
        )
        missing = pef.missing_categories()
        assert len(missing) == 15  # 16 - 1 = 15
        assert ImpactCategory.CLIMATE_CHANGE.value not in missing


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_all_impact_categories(self):
        """Test get_all_impact_categories returns 16 categories."""
        categories = get_all_impact_categories()
        assert len(categories) == 16
        assert "lca:Climate_change_total" in categories

    def test_get_impact_category_unit(self):
        """Test get_impact_category_unit returns correct unit."""
        unit = get_impact_category_unit(ImpactCategory.CLIMATE_CHANGE.value)
        assert unit == "kg CO2-eq"

    def test_get_impact_category_unit_unknown(self):
        """Test get_impact_category_unit returns None for unknown."""
        unit = get_impact_category_unit("lca:Unknown")
        assert unit is None

    def test_get_all_characterization_models(self):
        """Test get_all_characterization_models returns all models."""
        models = get_all_characterization_models()
        assert len(models) == len(CharacterizationModel)
        assert "lca:Bern_model_based_on_IPCC_2021" in models

    def test_get_all_impact_indicators(self):
        """Test get_all_impact_indicators returns all indicators."""
        indicators = get_all_impact_indicators()
        assert len(indicators) == len(ImpactCategoryIndicator)

    def test_is_climate_related_true(self):
        """Test is_climate_related returns True for climate change."""
        assert is_climate_related(ImpactCategory.CLIMATE_CHANGE.value)

    def test_is_climate_related_false(self):
        """Test is_climate_related returns False for other categories."""
        assert not is_climate_related(ImpactCategory.WATER_USE.value)

    def test_is_toxicity_related_true(self):
        """Test is_toxicity_related returns True for toxicity categories."""
        assert is_toxicity_related(ImpactCategory.HUMAN_TOXICITY_CANCER.value)
        assert is_toxicity_related(ImpactCategory.HUMAN_TOXICITY_NON_CANCER.value)
        assert is_toxicity_related(ImpactCategory.ECOTOXICITY_FRESHWATER.value)

    def test_is_toxicity_related_false(self):
        """Test is_toxicity_related returns False for other categories."""
        assert not is_toxicity_related(ImpactCategory.CLIMATE_CHANGE.value)

    def test_is_resource_related_true(self):
        """Test is_resource_related returns True for resource categories."""
        assert is_resource_related(ImpactCategory.RESOURCE_FOSSILS.value)
        assert is_resource_related(ImpactCategory.RESOURCE_MINERALS.value)
        assert is_resource_related(ImpactCategory.WATER_USE.value)
        assert is_resource_related(ImpactCategory.LAND_USE.value)

    def test_is_resource_related_false(self):
        """Test is_resource_related returns False for other categories."""
        assert not is_resource_related(ImpactCategory.CLIMATE_CHANGE.value)


class TestURIExpansion:
    """Tests for URI expansion and compaction."""

    def test_expand_lca_uri(self):
        """Test expanding compact LCA URI."""
        compact = "lca:Climate_change_total"
        full = expand_lca_uri(compact)
        assert full == "http://dpp.cea.fr/EUDPP/LCA#Climate_change_total"

    def test_expand_lca_uri_already_full(self):
        """Test expanding already full URI."""
        full = "http://example.org/other"
        result = expand_lca_uri(full)
        assert result == full

    def test_compact_lca_uri(self):
        """Test compacting full LCA URI."""
        full = "http://dpp.cea.fr/EUDPP/LCA#Climate_change_total"
        compact = compact_lca_uri(full)
        assert compact == "lca:Climate_change_total"

    def test_compact_lca_uri_already_compact(self):
        """Test compacting already compact URI."""
        compact = "other:prefix"
        result = compact_lca_uri(compact)
        assert result == compact
