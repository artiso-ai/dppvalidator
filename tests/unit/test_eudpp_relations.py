"""Tests for EU DPP Core Ontology product relationship properties."""

import pytest

from dppvalidator.vocabularies.eudpp_relations import (
    DATATYPE_PROPERTIES,
    OBJECT_PROPERTIES,
    DatatypePropertyDefinition,
    EUDPPDatatypeProperty,
    EUDPPObjectProperty,
    ObjectPropertyDefinition,
    ProductRelationMapper,
    get_actor_properties,
    get_lifecycle_properties,
    get_product_hierarchy_properties,
    is_product_relation,
)


class TestEUDPPObjectProperty:
    """Tests for EUDPPObjectProperty enum."""

    def test_dpp_product_relations_exist(self):
        """Test DPP-Product relation URIs exist."""
        assert EUDPPObjectProperty.HAS_DPP.value == "eudpp:hasDPP"
        assert EUDPPObjectProperty.APPLIES_TO_PRODUCT.value == "eudpp:appliesToProduct"

    def test_product_hierarchy_relations_exist(self):
        """Test product hierarchy relation URIs exist."""
        assert EUDPPObjectProperty.IS_COMPONENT_OF.value == "eudpp:isComponentOf"
        assert EUDPPObjectProperty.IS_SPARE_PART_OF.value == "eudpp:isSparePartOf"

    def test_actor_relations_exist(self):
        """Test actor relation URIs exist."""
        assert EUDPPObjectProperty.HAS_ISSUER.value == "eudpp:hasIssuer"
        assert EUDPPObjectProperty.HAS_MANUFACTURER.value == "eudpp:hasManufacturer"
        assert EUDPPObjectProperty.HAS_ECONOMIC_OPERATOR.value == "eudpp:hasEconomicOperator"
        assert EUDPPObjectProperty.HAS_BACKUP_COPY_HOST.value == "eudpp:hasBackUpCopyHost"

    def test_classification_relations_exist(self):
        """Test classification relation URIs exist."""
        assert EUDPPObjectProperty.HAS_PRODUCT_GROUP.value == "eudpp:hasProductGroup"

    def test_property_relations_exist(self):
        """Test property relation URIs exist."""
        assert EUDPPObjectProperty.HAS_PROPERTY.value == "eudpp:hasProperty"
        assert EUDPPObjectProperty.HAS_MEASUREMENT_UNIT.value == "eudpp:hasMeasurementUnit"

    def test_substance_relations_exist(self):
        """Test substance relation URIs exist."""
        assert (
            EUDPPObjectProperty.CONTAINS_SUBSTANCE_OF_CONCERN.value
            == "eudpp:containsSubstanceOfConcern"
        )


class TestEUDPPDatatypeProperty:
    """Tests for EUDPPDatatypeProperty enum."""

    def test_identification_properties_exist(self):
        """Test identification property URIs exist."""
        assert EUDPPDatatypeProperty.UNIQUE_DPP_ID.value == "eudpp:uniqueDPPID"
        assert EUDPPDatatypeProperty.UNIQUE_PRODUCT_ID.value == "eudpp:uniqueProductID"
        assert EUDPPDatatypeProperty.GTIN.value == "eudpp:GTIN"
        assert EUDPPDatatypeProperty.COMMODITY_CODE.value == "eudpp:commodityCode"

    def test_product_info_properties_exist(self):
        """Test product info property URIs exist."""
        assert EUDPPDatatypeProperty.PRODUCT_NAME.value == "eudpp:productName"
        assert EUDPPDatatypeProperty.DESCRIPTION.value == "eudpp:description"
        assert EUDPPDatatypeProperty.PRODUCT_IMAGE.value == "eudpp:productImage"

    def test_lifecycle_properties_exist(self):
        """Test lifecycle property URIs exist."""
        assert EUDPPDatatypeProperty.VALID_FROM.value == "eudpp:validFrom"
        assert EUDPPDatatypeProperty.VALID_UNTIL.value == "eudpp:validUntil"
        assert EUDPPDatatypeProperty.LAST_UPDATE.value == "eudpp:lastUpdate"
        assert EUDPPDatatypeProperty.STATUS.value == "eudpp:status"
        assert EUDPPDatatypeProperty.SCHEMA_VERSION.value == "eudpp:schemaVersion"
        assert EUDPPDatatypeProperty.LINK_TO_PREVIOUS_DPP.value == "eudpp:linkToPreviousDPP"

    def test_granularity_property_exists(self):
        """Test granularity property URI exists."""
        assert EUDPPDatatypeProperty.GRANULARITY.value == "eudpp:granularity"

    def test_energy_related_property_exists(self):
        """Test energy-related property URI exists."""
        assert EUDPPDatatypeProperty.IS_ENERGY_RELATED.value == "eudpp:isEnergyRelated"

    def test_quantitative_properties_exist(self):
        """Test quantitative property URIs exist."""
        assert EUDPPDatatypeProperty.NUMERICAL_VALUE.value == "eudpp:numericalValue"
        assert EUDPPDatatypeProperty.TOLERANCE.value == "eudpp:tolerance"


class TestObjectPropertyDefinition:
    """Tests for ObjectPropertyDefinition dataclass."""

    def test_create_object_property(self):
        """Test creating an object property definition."""
        prop = ObjectPropertyDefinition(
            uri="eudpp:testProperty",
            domain="eudpp:Product",
            range="eudpp:Actor",
            description="Test property",
        )
        assert prop.uri == "eudpp:testProperty"
        assert prop.domain == "eudpp:Product"
        assert prop.range == "eudpp:Actor"
        assert prop.is_transitive is False

    def test_create_transitive_property(self):
        """Test creating a transitive property."""
        prop = ObjectPropertyDefinition(
            uri="eudpp:isComponentOf",
            domain="eudpp:Product",
            range="eudpp:Product",
            description="Component relation",
            is_transitive=True,
        )
        assert prop.is_transitive is True

    def test_property_with_espr_reference(self):
        """Test property with ESPR reference."""
        prop = ObjectPropertyDefinition(
            uri="eudpp:hasIssuer",
            domain="eudpp:DPP",
            range="eudpp:Actor",
            description="DPP issuer",
            espr_reference="ESPR Annex III (g)",
        )
        assert prop.espr_reference == "ESPR Annex III (g)"


class TestDatatypePropertyDefinition:
    """Tests for DatatypePropertyDefinition dataclass."""

    def test_create_datatype_property(self):
        """Test creating a datatype property definition."""
        prop = DatatypePropertyDefinition(
            uri="eudpp:productName",
            domain="eudpp:Product",
            range="xsd:string",
            description="Product name",
        )
        assert prop.uri == "eudpp:productName"
        assert prop.range == "xsd:string"

    def test_property_with_espr_reference(self):
        """Test property with ESPR reference."""
        prop = DatatypePropertyDefinition(
            uri="eudpp:isEnergyRelated",
            domain="eudpp:Product",
            range="xsd:boolean",
            description="Energy-related product",
            espr_reference="ESPR Art 2(4)",
        )
        assert prop.espr_reference == "ESPR Art 2(4)"


class TestPropertyCollections:
    """Tests for property collection tuples."""

    def test_object_properties_not_empty(self):
        """Test OBJECT_PROPERTIES is not empty."""
        assert len(OBJECT_PROPERTIES) >= 10

    def test_datatype_properties_not_empty(self):
        """Test DATATYPE_PROPERTIES is not empty."""
        assert len(DATATYPE_PROPERTIES) >= 15

    def test_all_object_properties_have_uri(self):
        """Test all object properties have URI."""
        for prop in OBJECT_PROPERTIES:
            assert prop.uri.startswith("eudpp:")

    def test_all_datatype_properties_have_uri(self):
        """Test all datatype properties have URI."""
        for prop in DATATYPE_PROPERTIES:
            assert prop.uri.startswith("eudpp:")

    def test_is_component_of_is_transitive(self):
        """Test isComponentOf is marked as transitive."""
        component_prop = next(
            (p for p in OBJECT_PROPERTIES if p.uri == "eudpp:isComponentOf"),
            None,
        )
        assert component_prop is not None
        assert component_prop.is_transitive is True


class TestProductRelationMapper:
    """Tests for ProductRelationMapper class."""

    @pytest.fixture
    def mapper(self) -> ProductRelationMapper:
        """Create mapper instance."""
        return ProductRelationMapper()

    def test_get_object_property(self, mapper: ProductRelationMapper):
        """Test getting object property by URI."""
        prop = mapper.get_object_property("eudpp:isComponentOf")
        assert prop is not None
        assert prop.uri == "eudpp:isComponentOf"
        assert prop.is_transitive is True

    def test_get_object_property_not_found(self, mapper: ProductRelationMapper):
        """Test getting unknown object property."""
        prop = mapper.get_object_property("eudpp:unknownProperty")
        assert prop is None

    def test_get_datatype_property(self, mapper: ProductRelationMapper):
        """Test getting datatype property by URI."""
        prop = mapper.get_datatype_property("eudpp:productName")
        assert prop is not None
        assert prop.uri == "eudpp:productName"
        assert prop.range == "xsd:string"

    def test_get_datatype_property_not_found(self, mapper: ProductRelationMapper):
        """Test getting unknown datatype property."""
        prop = mapper.get_datatype_property("eudpp:unknownProperty")
        assert prop is None

    def test_is_transitive(self, mapper: ProductRelationMapper):
        """Test checking if property is transitive."""
        assert mapper.is_transitive("eudpp:isComponentOf") is True
        assert mapper.is_transitive("eudpp:hasManufacturer") is False
        assert mapper.is_transitive("eudpp:unknownProperty") is False

    def test_get_domain(self, mapper: ProductRelationMapper):
        """Test getting property domain."""
        assert mapper.get_domain("eudpp:isComponentOf") == "eudpp:Product"
        assert mapper.get_domain("eudpp:productName") == "eudpp:Product"
        assert mapper.get_domain("eudpp:unknownProperty") is None

    def test_get_range(self, mapper: ProductRelationMapper):
        """Test getting property range."""
        assert mapper.get_range("eudpp:isComponentOf") == "eudpp:Product"
        assert mapper.get_range("eudpp:productName") == "xsd:string"
        assert mapper.get_range("eudpp:unknownProperty") is None

    def test_iter_object_properties(self, mapper: ProductRelationMapper):
        """Test iterating object properties."""
        props = list(mapper.iter_object_properties())
        assert len(props) == mapper.object_property_count

    def test_iter_datatype_properties(self, mapper: ProductRelationMapper):
        """Test iterating datatype properties."""
        props = list(mapper.iter_datatype_properties())
        assert len(props) == mapper.datatype_property_count

    def test_property_counts(self, mapper: ProductRelationMapper):
        """Test property counts."""
        assert mapper.object_property_count >= 10
        assert mapper.datatype_property_count >= 15


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_product_hierarchy_properties(self):
        """Test getting product hierarchy properties."""
        props = get_product_hierarchy_properties()
        assert "eudpp:isComponentOf" in props
        assert "eudpp:isSparePartOf" in props
        assert len(props) == 2

    def test_get_actor_properties(self):
        """Test getting actor properties."""
        props = get_actor_properties()
        assert "eudpp:hasIssuer" in props
        assert "eudpp:hasManufacturer" in props
        assert "eudpp:hasEconomicOperator" in props
        assert "eudpp:hasBackUpCopyHost" in props
        # Phase 2 added role and facility relationships
        assert "eudpp:hasRole" in props
        assert "eudpp:usesFacility" in props
        assert len(props) == 12

    def test_get_lifecycle_properties(self):
        """Test getting lifecycle properties."""
        props = get_lifecycle_properties()
        assert "eudpp:validFrom" in props
        assert "eudpp:validUntil" in props
        assert "eudpp:lastUpdate" in props
        assert "eudpp:status" in props
        assert "eudpp:schemaVersion" in props
        assert "eudpp:linkToPreviousDPP" in props
        assert len(props) == 6

    def test_is_product_relation(self):
        """Test checking if URI is a product relation."""
        assert is_product_relation("eudpp:isComponentOf") is True
        assert is_product_relation("eudpp:isSparePartOf") is True
        assert is_product_relation("eudpp:hasManufacturer") is False
        assert is_product_relation("eudpp:productName") is False
