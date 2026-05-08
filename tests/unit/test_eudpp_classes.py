"""Tests for EU DPP Core Ontology class hierarchy."""

from decimal import Decimal

import pytest

from dppvalidator.vocabularies.eudpp_classes import (
    EUDPP_CLASS_HIERARCHY,
    EUDPP_DPP,
    CarbonFootprint,
    ClassificationCode,
    DigitalInstruction,
    Document,
    Durability,
    EmissionToAir,
    EmissionToSoil,
    EmissionToWater,
    EnergyConsumption,
    EnvironmentalFootprint,
    EUDPPClass,
    EUDPPProduct,
    HazardousWasteAmount,
    Height,
    LandUse,
    Length,
    MaterialFootprint,
    MicroplasticRelease,
    NanoplasticRelease,
    PackagingWasteAmount,
    PlasticsWasteAmount,
    QuantitativeProperty,
    RecoverableRate,
    RecycledMaterialsUse,
    RecyclingCollectionRate,
    RecyclingRate,
    Reliability,
    SustainableRenewableMaterialsUse,
    Volume,
    WaterConsumption,
    Weight,
    Width,
    get_all_circular_economy_classes,
    get_all_environmental_classes,
    get_class_hierarchy,
    is_subclass_of,
)

# Note: CircularEconomyIndicator, EnvironmentalEmission, EnvironmentalPollution,
# PlasticsRelease, ProductDimension, QualityIndicator, ResourceConsumption,
# and WasteGenerationAmount are tested indirectly through their subclasses


class TestEUDPPClass:
    """Tests for EUDPPClass enum."""

    def test_core_classes_exist(self):
        """Test core class URIs exist."""
        assert EUDPPClass.DPP.value == "eudpp:DPP"
        assert EUDPPClass.PRODUCT.value == "eudpp:Product"
        assert EUDPPClass.QUANTITATIVE_PROPERTY.value == "eudpp:QuantitativeProperty"

    def test_environmental_classes_exist(self):
        """Test environmental class URIs exist."""
        assert EUDPPClass.ENVIRONMENTAL_FOOTPRINT.value == "eudpp:EnvironmentalFootprint"
        assert EUDPPClass.CARBON_FOOTPRINT.value == "eudpp:CarbonFootprint"
        assert EUDPPClass.MATERIAL_FOOTPRINT.value == "eudpp:MaterialFootprint"

    def test_emission_classes_exist(self):
        """Test emission class URIs exist."""
        assert EUDPPClass.EMISSION_TO_AIR.value == "eudpp:EmissionToAir"
        assert EUDPPClass.EMISSION_TO_WATER.value == "eudpp:EmissionToWater"
        assert EUDPPClass.EMISSION_TO_SOIL.value == "eudpp:EmissionToSoil"

    def test_plastics_release_classes_exist(self):
        """Test plastics release class URIs exist."""
        assert EUDPPClass.MICROPLASTIC_RELEASE.value == "eudpp:MicroplasticRelease"
        assert EUDPPClass.NANOPLASTIC_RELEASE.value == "eudpp:NanoplasticRelease"

    def test_resource_consumption_classes_exist(self):
        """Test resource consumption class URIs exist."""
        assert EUDPPClass.ENERGY_CONSUMPTION.value == "eudpp:EnergyConsumption"
        assert EUDPPClass.WATER_CONSUMPTION.value == "eudpp:WaterConsumption"
        assert EUDPPClass.LAND_USE.value == "eudpp:LandUse"

    def test_circular_economy_classes_exist(self):
        """Test circular economy class URIs exist."""
        assert EUDPPClass.RECYCLING_RATE.value == "eudpp:RecyclingRate"
        assert EUDPPClass.RECOVERABLE_RATE.value == "eudpp:RecoverableRate"

    def test_quality_classes_exist(self):
        """Test quality class URIs exist."""
        assert EUDPPClass.DURABILITY.value == "eudpp:Durability"
        assert EUDPPClass.RELIABILITY.value == "eudpp:Reliability"

    def test_dimension_classes_exist(self):
        """Test dimension class URIs exist."""
        assert EUDPPClass.HEIGHT.value == "eudpp:Height"
        assert EUDPPClass.LENGTH.value == "eudpp:Length"
        assert EUDPPClass.WIDTH.value == "eudpp:Width"
        assert EUDPPClass.VOLUME.value == "eudpp:Volume"
        assert EUDPPClass.WEIGHT.value == "eudpp:Weight"


class TestQuantitativeProperty:
    """Tests for QuantitativeProperty base class."""

    def test_create_quantitative_property(self):
        """Test creating a quantitative property."""
        prop = QuantitativeProperty(
            numerical_value=Decimal("100.5"),
            measurement_unit="kg",
        )
        assert prop.numerical_value == Decimal("100.5")
        assert prop.measurement_unit == "kg"
        assert prop.tolerance is None

    def test_create_with_tolerance(self):
        """Test creating with tolerance."""
        prop = QuantitativeProperty(
            numerical_value=Decimal("100"),
            measurement_unit="kg",
            tolerance=Decimal("0.5"),
        )
        assert prop.tolerance == Decimal("0.5")

    def test_immutable(self):
        """Test property is immutable (frozen)."""
        prop = QuantitativeProperty(
            numerical_value=Decimal("100"),
            measurement_unit="kg",
        )
        with pytest.raises(AttributeError):
            prop.numerical_value = Decimal("200")  # type: ignore[misc]


class TestEnvironmentalFootprint:
    """Tests for environmental footprint classes."""

    def test_create_environmental_footprint(self):
        """Test creating an environmental footprint."""
        ef = EnvironmentalFootprint(
            numerical_value=Decimal("250.0"),
            measurement_unit="kg CO2-eq",
        )
        assert ef._class_uri == "eudpp:EnvironmentalFootprint"
        assert ef.numerical_value == Decimal("250.0")

    def test_create_carbon_footprint(self):
        """Test creating a carbon footprint."""
        cf = CarbonFootprint(
            numerical_value=Decimal("125.5"),
            measurement_unit="kg CO2-eq",
        )
        assert cf._class_uri == "eudpp:CarbonFootprint"
        assert cf.measurement_unit == "kg CO2-eq"

    def test_create_material_footprint(self):
        """Test creating a material footprint."""
        mf = MaterialFootprint(
            numerical_value=Decimal("500.0"),
            measurement_unit="kg",
        )
        assert mf._class_uri == "eudpp:MaterialFootprint"


class TestEmissions:
    """Tests for emission classes."""

    def test_create_emission_to_air(self):
        """Test creating emission to air."""
        emission = EmissionToAir(
            numerical_value=Decimal("10.0"),
            measurement_unit="g/unit",
            lifecycle_stage="manufacturing",
        )
        assert emission._class_uri == "eudpp:EmissionToAir"
        assert emission.lifecycle_stage == "manufacturing"

    def test_create_emission_to_water(self):
        """Test creating emission to water."""
        emission = EmissionToWater(
            numerical_value=Decimal("5.0"),
            measurement_unit="mg/L",
        )
        assert emission._class_uri == "eudpp:EmissionToWater"

    def test_create_emission_to_soil(self):
        """Test creating emission to soil."""
        emission = EmissionToSoil(
            numerical_value=Decimal("2.0"),
            measurement_unit="mg/kg",
        )
        assert emission._class_uri == "eudpp:EmissionToSoil"


class TestPlasticsRelease:
    """Tests for plastics release classes."""

    def test_create_microplastic_release(self):
        """Test creating microplastic release."""
        release = MicroplasticRelease(
            numerical_value=Decimal("0.5"),
            measurement_unit="mg/wash",
            lifecycle_stage="use",
        )
        assert release._class_uri == "eudpp:MicroplasticRelease"
        assert release.lifecycle_stage == "use"

    def test_create_nanoplastic_release(self):
        """Test creating nanoplastic release."""
        release = NanoplasticRelease(
            numerical_value=Decimal("0.01"),
            measurement_unit="mg/wash",
        )
        assert release._class_uri == "eudpp:NanoplasticRelease"


class TestResourceConsumption:
    """Tests for resource consumption classes."""

    def test_create_energy_consumption(self):
        """Test creating energy consumption."""
        ec = EnergyConsumption(
            numerical_value=Decimal("150.0"),
            measurement_unit="kWh",
        )
        assert ec._class_uri == "eudpp:EnergyConsumption"

    def test_create_water_consumption(self):
        """Test creating water consumption."""
        wc = WaterConsumption(
            numerical_value=Decimal("50.0"),
            measurement_unit="L",
        )
        assert wc._class_uri == "eudpp:WaterConsumption"

    def test_create_land_use(self):
        """Test creating land use."""
        lu = LandUse(
            numerical_value=Decimal("10.0"),
            measurement_unit="m2",
        )
        assert lu._class_uri == "eudpp:LandUse"

    def test_create_recycled_materials_use(self):
        """Test creating recycled materials use."""
        rmu = RecycledMaterialsUse(
            numerical_value=Decimal("30.0"),
            measurement_unit="%",
        )
        assert rmu._class_uri == "eudpp:RecycledMaterialsUse"

    def test_create_sustainable_materials_use(self):
        """Test creating sustainable materials use."""
        smu = SustainableRenewableMaterialsUse(
            numerical_value=Decimal("25.0"),
            measurement_unit="%",
        )
        assert smu._class_uri == "eudpp:SustainableRenewableMaterialsUse"


class TestCircularEconomyIndicators:
    """Tests for circular economy indicator classes."""

    def test_create_recycling_rate(self):
        """Test creating recycling rate."""
        rr = RecyclingRate(
            numerical_value=Decimal("85.0"),
            measurement_unit="%",
        )
        assert rr._class_uri == "eudpp:RecyclingRate"

    def test_create_recycling_collection_rate(self):
        """Test creating recycling collection rate."""
        rcr = RecyclingCollectionRate(
            numerical_value=Decimal("90.0"),
            measurement_unit="%",
        )
        assert rcr._class_uri == "eudpp:RecyclingCollectionRate"

    def test_create_recoverable_rate(self):
        """Test creating recoverable rate."""
        rr = RecoverableRate(
            numerical_value=Decimal("95.0"),
            measurement_unit="%",
        )
        assert rr._class_uri == "eudpp:RecoverableRate"


class TestWasteGeneration:
    """Tests for waste generation classes."""

    def test_create_hazardous_waste(self):
        """Test creating hazardous waste amount."""
        hw = HazardousWasteAmount(
            numerical_value=Decimal("5.0"),
            measurement_unit="kg",
        )
        assert hw._class_uri == "eudpp:HazardousWasteAmount"

    def test_create_packaging_waste(self):
        """Test creating packaging waste amount."""
        pw = PackagingWasteAmount(
            numerical_value=Decimal("2.0"),
            measurement_unit="kg",
        )
        assert pw._class_uri == "eudpp:PackagingWasteAmount"

    def test_create_plastics_waste(self):
        """Test creating plastics waste amount."""
        pw = PlasticsWasteAmount(
            numerical_value=Decimal("1.5"),
            measurement_unit="kg",
        )
        assert pw._class_uri == "eudpp:PlasticsWasteAmount"


class TestQualityIndicators:
    """Tests for quality indicator classes."""

    def test_create_durability(self):
        """Test creating durability."""
        d = Durability(
            numerical_value=Decimal("5.0"),
            measurement_unit="years",
        )
        assert d._class_uri == "eudpp:Durability"

    def test_create_reliability(self):
        """Test creating reliability with MTBF."""
        r = Reliability(
            numerical_value=Decimal("99.5"),
            measurement_unit="%",
            mtbf_hours=Decimal("10000"),
        )
        assert r._class_uri == "eudpp:Reliability"
        assert r.mtbf_hours == Decimal("10000")


class TestProductDimensions:
    """Tests for product dimension classes."""

    def test_create_height(self):
        """Test creating height."""
        h = Height(
            numerical_value=Decimal("50.0"),
            measurement_unit="cm",
        )
        assert h._class_uri == "eudpp:Height"

    def test_create_length(self):
        """Test creating length."""
        length = Length(
            numerical_value=Decimal("100.0"),
            measurement_unit="cm",
        )
        assert length._class_uri == "eudpp:Length"

    def test_create_width(self):
        """Test creating width."""
        w = Width(
            numerical_value=Decimal("30.0"),
            measurement_unit="cm",
        )
        assert w._class_uri == "eudpp:Width"

    def test_create_volume(self):
        """Test creating volume."""
        v = Volume(
            numerical_value=Decimal("150000.0"),
            measurement_unit="cm3",
        )
        assert v._class_uri == "eudpp:Volume"

    def test_create_weight(self):
        """Test creating weight."""
        w = Weight(
            numerical_value=Decimal("2.5"),
            measurement_unit="kg",
        )
        assert w._class_uri == "eudpp:Weight"


class TestClassHierarchy:
    """Tests for class hierarchy functions."""

    def test_class_hierarchy_not_empty(self):
        """Test class hierarchy is not empty."""
        assert len(EUDPP_CLASS_HIERARCHY) > 0

    def test_get_environmental_footprint_subclasses(self):
        """Test getting environmental footprint subclasses."""
        subclasses = get_class_hierarchy("eudpp:EnvironmentalFootprint")
        assert "eudpp:CarbonFootprint" in subclasses
        assert "eudpp:MaterialFootprint" in subclasses

    def test_get_emission_subclasses(self):
        """Test getting emission subclasses."""
        subclasses = get_class_hierarchy("eudpp:EnvironmentalEmission")
        assert "eudpp:EmissionToAir" in subclasses
        assert "eudpp:EmissionToWater" in subclasses
        assert "eudpp:EmissionToSoil" in subclasses

    def test_get_unknown_class_returns_empty(self):
        """Test getting subclasses of unknown class."""
        subclasses = get_class_hierarchy("eudpp:UnknownClass")
        assert subclasses == []

    def test_is_subclass_of_direct(self):
        """Test direct subclass relationship."""
        assert is_subclass_of("eudpp:CarbonFootprint", "eudpp:EnvironmentalFootprint")
        assert is_subclass_of("eudpp:EmissionToAir", "eudpp:EnvironmentalEmission")

    def test_is_subclass_of_transitive(self):
        """Test transitive subclass relationship."""
        assert is_subclass_of("eudpp:CarbonFootprint", "eudpp:QuantitativeProperty")
        assert is_subclass_of("eudpp:EmissionToAir", "eudpp:QuantitativeProperty")

    def test_is_subclass_of_same_class(self):
        """Test class is subclass of itself."""
        assert is_subclass_of("eudpp:CarbonFootprint", "eudpp:CarbonFootprint")

    def test_is_not_subclass(self):
        """Test non-subclass relationship."""
        assert not is_subclass_of("eudpp:CarbonFootprint", "eudpp:EmissionToAir")
        assert not is_subclass_of("eudpp:Weight", "eudpp:CarbonFootprint")


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_all_environmental_classes(self):
        """Test getting all environmental classes."""
        classes = get_all_environmental_classes()
        assert "eudpp:EnvironmentalFootprint" in classes
        assert "eudpp:CarbonFootprint" in classes
        assert "eudpp:EmissionToAir" in classes
        assert "eudpp:MicroplasticRelease" in classes
        assert len(classes) >= 15

    def test_get_all_circular_economy_classes(self):
        """Test getting all circular economy classes."""
        classes = get_all_circular_economy_classes()
        assert "eudpp:CircularEconomyIndicator" in classes
        assert "eudpp:RecyclingRate" in classes
        assert "eudpp:RecycledMaterialsUse" in classes
        assert len(classes) >= 6


# =============================================================================
# Phase 1: Core Entity Classes Tests (CIRPASS-2 Integration)
# =============================================================================


class TestDocument:
    """Tests for Document class."""

    def test_create_document(self):
        """Test creating a document."""
        doc = Document(
            content_type="application/pdf",
            web_link="https://example.com/manual.pdf",
            title="User Manual",
            language="en",
        )
        assert doc._class_uri == "eudpp:Document"
        assert doc.content_type == "application/pdf"
        assert doc.web_link == "https://example.com/manual.pdf"
        assert doc.title == "User Manual"
        assert doc.language == "en"

    def test_create_document_minimal(self):
        """Test creating a document with minimal fields."""
        doc = Document()
        assert doc._class_uri == "eudpp:Document"
        assert doc.content_type is None
        assert doc.web_link is None

    def test_document_immutable(self):
        """Test document is immutable (frozen)."""
        doc = Document(title="Test")
        with pytest.raises(AttributeError):
            doc.title = "Modified"  # type: ignore[misc]


class TestClassificationCode:
    """Tests for ClassificationCode class."""

    def test_create_classification_code(self):
        """Test creating a classification code."""
        code = ClassificationCode(
            code_set="TARIC",
            code_value="8471300000",
            description="Portable digital automatic data processing machines",
        )
        assert code._class_uri == "eudpp:ClassificationCode"
        assert code.code_set == "TARIC"
        assert code.code_value == "8471300000"
        assert code.description == "Portable digital automatic data processing machines"

    def test_create_hs_code(self):
        """Test creating an HS code classification."""
        code = ClassificationCode(
            code_set="HS",
            code_value="6109.10",
        )
        assert code.code_set == "HS"
        assert code.code_value == "6109.10"
        assert code.description is None

    def test_classification_code_immutable(self):
        """Test classification code is immutable."""
        code = ClassificationCode(code_set="HS", code_value="1234")
        with pytest.raises(AttributeError):
            code.code_value = "5678"  # type: ignore[misc]


class TestDigitalInstruction:
    """Tests for DigitalInstruction class."""

    def test_create_digital_instruction(self):
        """Test creating a digital instruction."""
        instruction = DigitalInstruction(
            content_type="text/html",
            web_link="https://example.com/repair-guide",
            title="Repair Guide",
            language="en",
            instruction_type="repair",
        )
        assert instruction._class_uri == "eudpp:DigitalInstruction"
        assert instruction.instruction_type == "repair"
        assert instruction.title == "Repair Guide"

    def test_digital_instruction_inherits_document(self):
        """Test DigitalInstruction inherits from Document."""
        instruction = DigitalInstruction(
            content_type="application/pdf",
            web_link="https://example.com/manual.pdf",
        )
        # DigitalInstruction should have Document fields
        assert instruction.content_type == "application/pdf"
        assert instruction.web_link == "https://example.com/manual.pdf"


class TestEUDPPProduct:
    """Tests for EUDPPProduct class."""

    def test_create_product(self):
        """Test creating a product."""
        product = EUDPPProduct(
            unique_product_id="urn:uuid:12345678-1234-1234-1234-123456789012",
            product_name="Sustainable Laptop",
            description="Energy-efficient laptop computer",
            gtin="01234567890128",
            commodity_code="8471300000",
            is_energy_related=True,
        )
        assert product._class_uri == "eudpp:Product"
        assert product.unique_product_id == "urn:uuid:12345678-1234-1234-1234-123456789012"
        assert product.product_name == "Sustainable Laptop"
        assert product.is_energy_related is True

    def test_create_product_minimal(self):
        """Test creating a product with minimal fields."""
        product = EUDPPProduct()
        assert product._class_uri == "eudpp:Product"
        assert product.unique_product_id is None
        assert product.gtin is None

    def test_product_immutable(self):
        """Test product is immutable."""
        product = EUDPPProduct(product_name="Test")
        with pytest.raises(AttributeError):
            product.product_name = "Modified"  # type: ignore[misc]


class TestEUDPP_DPP:
    """Tests for EUDPP_DPP class."""

    def test_create_dpp(self):
        """Test creating a DPP."""
        dpp = EUDPP_DPP(
            unique_dpp_id="https://example.com/dpp/12345",
            granularity="product",
            status="Active",
            valid_from="2024-01-01T00:00:00Z",
            valid_until="2034-01-01T00:00:00Z",
            schema_version="1.0.0",
        )
        assert dpp._class_uri == "eudpp:DPP"
        assert dpp.unique_dpp_id == "https://example.com/dpp/12345"
        assert dpp.granularity == "product"
        assert dpp.status == "Active"

    def test_create_dpp_required_field(self):
        """Test DPP requires unique_dpp_id."""
        dpp = EUDPP_DPP(unique_dpp_id="https://example.com/dpp/minimal")
        assert dpp.unique_dpp_id == "https://example.com/dpp/minimal"
        assert dpp.granularity is None
        assert dpp.status is None

    def test_dpp_with_previous_link(self):
        """Test DPP with link to previous version."""
        dpp = EUDPP_DPP(
            unique_dpp_id="https://example.com/dpp/v2",
            link_to_previous_dpp="https://example.com/dpp/v1",
            last_update="2024-06-01T12:00:00Z",
        )
        assert dpp.link_to_previous_dpp == "https://example.com/dpp/v1"
        assert dpp.last_update == "2024-06-01T12:00:00Z"

    def test_dpp_immutable(self):
        """Test DPP is immutable."""
        dpp = EUDPP_DPP(unique_dpp_id="https://example.com/dpp/test")
        with pytest.raises(AttributeError):
            dpp.status = "Archived"  # type: ignore[misc]


class TestPhase1ClassHierarchy:
    """Tests for Phase 1 class hierarchy additions."""

    def test_document_in_hierarchy(self):
        """Test Document is in class hierarchy."""
        assert "eudpp:Document" in EUDPP_CLASS_HIERARCHY

    def test_digital_instruction_subclass_of_document(self):
        """Test DigitalInstruction is subclass of Document."""
        subclasses = get_class_hierarchy("eudpp:Document")
        assert "eudpp:DigitalInstruction" in subclasses

    def test_dpp_in_hierarchy(self):
        """Test DPP is in class hierarchy."""
        assert "eudpp:DPP" in EUDPP_CLASS_HIERARCHY

    def test_product_in_hierarchy(self):
        """Test Product is in class hierarchy."""
        assert "eudpp:Product" in EUDPP_CLASS_HIERARCHY

    def test_classification_code_in_hierarchy(self):
        """Test ClassificationCode is in class hierarchy."""
        assert "eudpp:ClassificationCode" in EUDPP_CLASS_HIERARCHY
