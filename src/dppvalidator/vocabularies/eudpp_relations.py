"""EU DPP Core Ontology product relationship properties.

Defines object and datatype properties for product relationships
based on the official CIRPASS-2 ontology v1.7.1.

Source: EU DPP Core Ontology v1.7.1 (Product and DPP module)
Namespace: http://dpp.taltech.ee/EUDPP#
DOI: 10.5281/zenodo.15270342
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum


class EUDPPObjectProperty(str, Enum):
    """EU DPP Core Ontology object property URIs.

    Object properties define relationships between instances.
    """

    # DPP-Product relations
    HAS_DPP = "eudpp:hasDPP"
    APPLIES_TO_PRODUCT = "eudpp:appliesToProduct"

    # Product hierarchy relations (transitive)
    IS_COMPONENT_OF = "eudpp:isComponentOf"
    IS_SPARE_PART_OF = "eudpp:isSparePartOf"

    # Actor relations
    HAS_ISSUER = "eudpp:hasIssuer"
    HAS_MANUFACTURER = "eudpp:hasManufacturer"
    HAS_ECONOMIC_OPERATOR = "eudpp:hasEconomicOperator"
    HAS_BACKUP_COPY_HOST = "eudpp:hasBackUpCopyHost"
    IS_RESPONSIBLE_FOR_PRODUCT = "eudpp:isResponsibleForProduct"

    # Actor-Role relations (Phase 2)
    HAS_ROLE = "eudpp:hasRole"
    IS_ROLE_OF = "eudpp:isRoleOf"

    # Actor-Facility relations (Phase 2)
    USES_FACILITY = "eudpp:usesFacility"
    IS_USED_BY_ACTOR = "eudpp:isUsedByActor"

    # Actor location relations (Phase 2)
    IS_ESTABLISHED_IN = "eudpp:isEstablishedIn"
    IS_RESIDING_IN = "eudpp:isResidingIn"

    # Authorised representative relations (Phase 2)
    REPRESENTS_MANUFACTURER = "eudpp:representsManufacturer"
    IS_REPRESENTED_BY = "eudpp:isRepresentedBy"

    # Product classification
    HAS_PRODUCT_GROUP = "eudpp:hasProductGroup"

    # Property relations
    HAS_PROPERTY = "eudpp:hasProperty"
    HAS_MEASUREMENT_UNIT = "eudpp:hasMeasurementUnit"

    # Substance relations
    CONTAINS_SUBSTANCE_OF_CONCERN = "eudpp:containsSubstanceOfConcern"

    # Substance of Concern relations (Phase 3)
    HAS_CONCENTRATION = "eudpp:hasConcentration"
    HAS_LIFECYCLE_STAGE = "eudpp:hasLifeCycleStage"
    HAS_THRESHOLD = "eudpp:hasThreshold"

    # LCA relations (Phase 4)
    QUANTIFIES = "lca:quantifies"
    QUANTIFIED_BY = "lca:quantified_by"
    ICI_ASSESS_IC = "lca:ICI_assess_IC"
    ICI_COMPUTES_IR = "lca:ICI_computes_IR"
    CF_QUANTIFIES_ICI = "lca:CF_quantifies_ICI"
    CM_CALCULATES_CF = "lca:CM_calculates_CF"
    METHOD_USES_CM = "lca:method_uses_CM"
    INCLUDES = "lca:includes"
    IMPOSES = "lca:imposes"
    CORRESPONDS_TO_IC = "lca:corresponds_to_IC"


class EUDPPDatatypeProperty(str, Enum):
    """EU DPP Core Ontology datatype property URIs.

    Datatype properties define relationships to literal values.
    """

    # DPP identification
    UNIQUE_DPP_ID = "eudpp:uniqueDPPID"
    UNIQUE_PRODUCT_ID = "eudpp:uniqueProductID"
    GTIN = "eudpp:GTIN"
    COMMODITY_CODE = "eudpp:commodityCode"
    FACILITY_ID = "eudpp:facilityID"

    # Product information
    PRODUCT_NAME = "eudpp:productName"
    DESCRIPTION = "eudpp:description"
    PRODUCT_IMAGE = "eudpp:productImage"

    # DPP lifecycle
    VALID_FROM = "eudpp:validFrom"
    VALID_UNTIL = "eudpp:validUntil"
    LAST_UPDATE = "eudpp:lastUpdate"
    STATUS = "eudpp:status"
    SCHEMA_VERSION = "eudpp:schemaVersion"
    LINK_TO_PREVIOUS_DPP = "eudpp:linkToPreviousDPP"

    # Granularity
    GRANULARITY = "eudpp:granularity"

    # Product characteristics
    IS_ENERGY_RELATED = "eudpp:isEnergyRelated"

    # Quantitative values
    NUMERICAL_VALUE = "eudpp:numericalValue"
    TOLERANCE = "eudpp:tolerance"
    VALUE = "eudpp:value"

    # Classification
    CODE_SET = "eudpp:codeSet"
    CODE_VALUE = "eudpp:codeValue"
    DICTIONARY_REFERENCE = "eudpp:dictionaryReference"

    # Documents
    CONTENT_TYPE = "eudpp:contentType"
    WEB_LINK = "eudpp:webLink"

    # Actor properties (Phase 2)
    ACTOR_NAME = "eudpp:actorName"
    ELECTRONIC_CONTACT = "eudpp:electronicContact"
    POSTAL_ADDRESS = "eudpp:postalAddress"
    REGISTERED_TRADE_NAME = "eudpp:registeredTradeName"
    REGISTERED_TRADEMARK = "eudpp:registeredTrademark"
    UNIQUE_OPERATOR_ID = "eudpp:uniqueOperatorID"

    # Facility properties (Phase 2)
    UNIQUE_FACILITY_ID = "eudpp:uniqueFacilityID"

    # Substance of Concern properties (Phase 3)
    NAME_IUPAC = "eudpp:nameIUPAC"
    NAME_CAS = "eudpp:nameCAS"
    NUMBER_CAS = "eudpp:numberCAS"
    NUMBER_EC = "eudpp:numberEC"
    ABBREVIATION = "eudpp:abbreviation"
    TRADE_NAME = "eudpp:tradeName"
    USUAL_NAME = "eudpp:usualName"
    OTHER_NAME = "eudpp:otherName"
    SUBSTANCE_LOCATION = "eudpp:substanceLocation"
    HAS_IMPACT_ON_ENVIRONMENT = "eudpp:hasImpactOnEnvironment"
    HAS_IMPACT_ON_HUMAN_HEALTH = "eudpp:hasImpactOnHumanHealth"

    # LCA properties (Phase 4)
    LCA_HAS_UNIT = "lca:has_unit"
    LCA_NUMERIC_VALUE = "qudt:numericValue"


@dataclass(frozen=True, slots=True)
class ObjectPropertyDefinition:
    """Definition of an EU DPP object property."""

    uri: str
    domain: str
    range: str
    description: str
    is_transitive: bool = False
    is_functional: bool = False
    espr_reference: str | None = None


@dataclass(frozen=True, slots=True)
class DatatypePropertyDefinition:
    """Definition of an EU DPP datatype property."""

    uri: str
    domain: str
    range: str
    description: str
    espr_reference: str | None = None


# Object property definitions from official ontology
OBJECT_PROPERTIES: tuple[ObjectPropertyDefinition, ...] = (
    # DPP-Product relations
    ObjectPropertyDefinition(
        uri="eudpp:hasDPP",
        domain="eudpp:Product",
        range="eudpp:DPP",
        description="Product has an associated DPP",
        espr_reference="ESPR Art 8",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:appliesToProduct",
        domain="eudpp:DPP",
        range="eudpp:Product",
        description="DPP applies to a product",
        espr_reference="ESPR Art 8",
    ),
    # Product hierarchy (transitive)
    ObjectPropertyDefinition(
        uri="eudpp:isComponentOf",
        domain="eudpp:Product",
        range="eudpp:Product",
        description="Product is a component of another product",
        is_transitive=True,
        espr_reference="ESPR Art 2(2)",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:isSparePartOf",
        domain="eudpp:Product",
        range="eudpp:Product",
        description="Product is a spare part of another product",
        espr_reference="ESPR Art 2",
    ),
    # Actor relations
    ObjectPropertyDefinition(
        uri="eudpp:hasIssuer",
        domain="eudpp:DPP",
        range="eudpp:Actor",
        description="Economic operator issuing the DPP",
        espr_reference="ESPR Annex III (g)",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:hasManufacturer",
        domain="eudpp:Product",
        range="eudpp:Actor",
        description="Product manufacturer",
        espr_reference="ESPR Annex III (g)",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:hasEconomicOperator",
        domain="eudpp:Product",
        range="eudpp:Actor",
        description="Economic operator responsible for placing product on market",
        espr_reference="ESPR Art 2(18)",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:hasBackUpCopyHost",
        domain="eudpp:DPP",
        range="eudpp:Actor",
        description="Actor hosting backup copy of DPP",
        espr_reference="ESPR Art 10(4)",
    ),
    # Product classification
    ObjectPropertyDefinition(
        uri="eudpp:hasProductGroup",
        domain="eudpp:Product",
        range="eudpp:ClassificationCode",
        description="Product group classification",
        espr_reference="ESPR Art 2(4)",
    ),
    # Properties
    ObjectPropertyDefinition(
        uri="eudpp:hasProperty",
        domain="eudpp:Product",
        range="eudpp:Property",
        description="Product has a property",
        espr_reference="ESPR Annex I",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:hasMeasurementUnit",
        domain="eudpp:QuantitativeProperty",
        range="si:Unit",
        description="Measurement unit for quantitative property",
    ),
    # Substances
    ObjectPropertyDefinition(
        uri="eudpp:containsSubstanceOfConcern",
        domain="eudpp:Product",
        range="eudpp:SubstanceOfConcern",
        description="Product contains a substance of concern",
        espr_reference="ESPR Art 7(5)",
    ),
    # Actor-Role relations (Phase 2)
    ObjectPropertyDefinition(
        uri="eudpp:hasRole",
        domain="eudpp:Actor",
        range="eudpp:Role",
        description="Relates an actor to a role",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:isRoleOf",
        domain="eudpp:Role",
        range="eudpp:Actor",
        description="Relates role to an actor",
    ),
    # Actor-Facility relations (Phase 2)
    ObjectPropertyDefinition(
        uri="eudpp:usesFacility",
        domain="eudpp:Actor",
        range="eudpp:Facility",
        description="Relates an actor to facility",
        espr_reference="ESPR Art 2(33)",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:isUsedByActor",
        domain="eudpp:Facility",
        range="eudpp:Actor",
        description="Relates a facility to an actor",
        espr_reference="ESPR Art 2(33)",
    ),
    # Actor location relations (Phase 2)
    ObjectPropertyDefinition(
        uri="eudpp:isEstablishedIn",
        domain="eudpp:LegalPerson",
        range="dcterms:Location",
        description="Relates a legal person to the location where it is established",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:isResidingIn",
        domain="eudpp:NaturalPerson",
        range="dcterms:Location",
        description="Relates a natural person to the location where they reside",
    ),
    # Authorised representative relations (Phase 2)
    ObjectPropertyDefinition(
        uri="eudpp:representsManufacturer",
        domain="eudpp:Actor",
        range="eudpp:Actor",
        description="Relates an authorised representative to the manufacturer",
        espr_reference="ESPR Art 2(43)",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:isRepresentedBy",
        domain="eudpp:Actor",
        range="eudpp:Actor",
        description="Relates a manufacturer to an authorised representative",
        espr_reference="ESPR Art 2(43)",
    ),
    # Substance of Concern relations (Phase 3)
    ObjectPropertyDefinition(
        uri="eudpp:hasConcentration",
        domain="eudpp:SubstanceOfConcern",
        range="eudpp:Concentration",
        description="Concentration of substance in product",
        espr_reference="ESPR Art 7(5)",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:hasLifeCycleStage",
        domain="eudpp:SubstanceOfConcern",
        range="eudpp:Event",
        description="Life cycle stage during which substance occurs",
        espr_reference="ESPR Annex I(f)",
    ),
    ObjectPropertyDefinition(
        uri="eudpp:hasThreshold",
        domain="eudpp:SubstanceOfConcern",
        range="eudpp:Threshold",
        description="Regulatory threshold for substance",
        espr_reference="ESPR FAQ 10.115",
    ),
)


# Datatype property definitions from official ontology
DATATYPE_PROPERTIES: tuple[DatatypePropertyDefinition, ...] = (
    # DPP identification
    DatatypePropertyDefinition(
        uri="eudpp:uniqueDPPID",
        domain="eudpp:DPP",
        range="xsd:anyURI",
        description="Unique DPP identifier as URI",
        espr_reference="ESPR Art 9(1)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:uniqueProductID",
        domain="eudpp:Product",
        range="xsd:string",
        description="Unique product identifier",
        espr_reference="ESPR Art 2(30)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:GTIN",
        domain="eudpp:Product",
        range="xsd:string",
        description="Global Trade Identification Number",
        espr_reference="ISO/IEC 15459-6",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:commodityCode",
        domain="eudpp:Product",
        range="xsd:string",
        description="TARIC or commodity code",
        espr_reference="Council Regulation (EEC) No 2658/87",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:facilityID",
        domain="eudpp:Product",
        range="xsd:string",
        description="Unique facility identifier",
        espr_reference="ESPR Art 2(33)",
    ),
    # Product information
    DatatypePropertyDefinition(
        uri="eudpp:productName",
        domain="eudpp:Product",
        range="xsd:string",
        description="Product name",
        espr_reference="ESPR Annex III",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:description",
        domain="eudpp:Product",
        range="xsd:string",
        description="Product description",
        espr_reference="ESPR Annex III",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:productImage",
        domain="eudpp:Product",
        range="xsd:anyURI",
        description="Product image URI",
        espr_reference="ESPR Annex III",
    ),
    # DPP lifecycle
    DatatypePropertyDefinition(
        uri="eudpp:validFrom",
        domain="eudpp:DPP",
        range="xsd:dateTime",
        description="DPP valid from date",
        espr_reference="ESPR Art 9(2i)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:validUntil",
        domain="eudpp:DPP",
        range="xsd:dateTime",
        description="DPP valid until date",
        espr_reference="ESPR Art 9(2i)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:lastUpdate",
        domain="eudpp:DPP",
        range="xsd:dateTime",
        description="Last DPP update timestamp",
        espr_reference="ESPR Art 11",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:status",
        domain="eudpp:DPP",
        range="xsd:string",
        description="DPP status (Active/Archived)",
        espr_reference="ESPR Art 11",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:schemaVersion",
        domain="eudpp:DPP",
        range="xsd:string",
        description="Reference standard version",
        espr_reference="ESPR Art 9",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:linkToPreviousDPP",
        domain="eudpp:DPP",
        range="xsd:anyURI",
        description="Link to previous DPP version",
        espr_reference="ESPR Art 11(d)",
    ),
    # Granularity
    DatatypePropertyDefinition(
        uri="eudpp:granularity",
        domain="eudpp:DPP",
        range="xsd:string",
        description="DPP granularity (model/batch/product)",
        espr_reference="SR5423 Annex II Part B 1.1",
    ),
    # Product characteristics
    DatatypePropertyDefinition(
        uri="eudpp:isEnergyRelated",
        domain="eudpp:Product",
        range="xsd:boolean",
        description="Product is energy-related per ESPR Art 2(4)",
        espr_reference="ESPR Art 2(4)",
    ),
    # Quantitative values
    DatatypePropertyDefinition(
        uri="eudpp:numericalValue",
        domain="eudpp:QuantitativeProperty",
        range="xsd:decimal",
        description="Numerical value of property",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:tolerance",
        domain="eudpp:QuantitativeProperty",
        range="xsd:decimal",
        description="Tolerance of quantitative property",
    ),
    # Actor properties (Phase 2)
    DatatypePropertyDefinition(
        uri="eudpp:actorName",
        domain="eudpp:Actor",
        range="xsd:string",
        description="Name of an actor",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:electronicContact",
        domain="eudpp:Actor",
        range="xsd:string",
        description="Electronic contact detail for an actor",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:postalAddress",
        domain="eudpp:Actor",
        range="xsd:string",
        description="Postal address associated with an actor",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:registeredTradeName",
        domain="eudpp:Actor",
        range="xsd:string",
        description="Trade name under which a legal person operates",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:registeredTrademark",
        domain="eudpp:Actor",
        range="xsd:string",
        description="A trademark officially registered and owned by an actor",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:uniqueOperatorID",
        domain="eudpp:Actor",
        range="xsd:string",
        description="Unique operator identifier",
        espr_reference="ESPR Art 2(31)",
    ),
    # Facility properties (Phase 2)
    DatatypePropertyDefinition(
        uri="eudpp:uniqueFacilityID",
        domain="eudpp:Facility",
        range="xsd:string",
        description="Unique facility identifier",
        espr_reference="ESPR Art 2(33)",
    ),
    # Substance of Concern properties (Phase 3)
    DatatypePropertyDefinition(
        uri="eudpp:nameIUPAC",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="IUPAC name of substance",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:nameCAS",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="CAS name of substance",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:numberCAS",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="CAS number of substance",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:numberEC",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="EC number of substance",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:abbreviation",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="Abbreviation for substance",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:tradeName",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="Trade name of substance",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:usualName",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="Usual name of substance",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:otherName",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="Other names for substance",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:substanceLocation",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="Location of substance in product",
        espr_reference="ESPR Art 7(5)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:hasImpactOnEnvironment",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="Impact of substance on environment",
        espr_reference="ESPR Annex I(f)",
    ),
    DatatypePropertyDefinition(
        uri="eudpp:hasImpactOnHumanHealth",
        domain="eudpp:SubstanceOfConcern",
        range="xsd:string",
        description="Impact of substance on human health",
        espr_reference="ESPR Annex I(f)",
    ),
)


class ProductRelationMapper:
    """Maps and validates product relationships per EU DPP ontology."""

    def __init__(self) -> None:
        """Initialize mapper with property definitions."""
        self._object_props = {p.uri: p for p in OBJECT_PROPERTIES}
        self._datatype_props = {p.uri: p for p in DATATYPE_PROPERTIES}

    def get_object_property(self, uri: str) -> ObjectPropertyDefinition | None:
        """Get object property definition by URI."""
        return self._object_props.get(uri)

    def get_datatype_property(self, uri: str) -> DatatypePropertyDefinition | None:
        """Get datatype property definition by URI."""
        return self._datatype_props.get(uri)

    def is_transitive(self, uri: str) -> bool:
        """Check if an object property is transitive."""
        prop = self._object_props.get(uri)
        return prop.is_transitive if prop else False

    def get_domain(self, uri: str) -> str | None:
        """Get domain of a property."""
        prop = self._object_props.get(uri) or self._datatype_props.get(uri)
        return prop.domain if prop else None

    def get_range(self, uri: str) -> str | None:
        """Get range of a property."""
        prop = self._object_props.get(uri) or self._datatype_props.get(uri)
        return prop.range if prop else None

    def iter_object_properties(self) -> Iterator[ObjectPropertyDefinition]:
        """Iterate over all object property definitions."""
        yield from OBJECT_PROPERTIES

    def iter_datatype_properties(self) -> Iterator[DatatypePropertyDefinition]:
        """Iterate over all datatype property definitions."""
        yield from DATATYPE_PROPERTIES

    @property
    def object_property_count(self) -> int:
        """Number of object properties."""
        return len(OBJECT_PROPERTIES)

    @property
    def datatype_property_count(self) -> int:
        """Number of datatype properties."""
        return len(DATATYPE_PROPERTIES)


def get_product_hierarchy_properties() -> list[str]:
    """Get URIs of product hierarchy properties.

    Returns:
        List of transitive product relation URIs
    """
    return [
        EUDPPObjectProperty.IS_COMPONENT_OF.value,
        EUDPPObjectProperty.IS_SPARE_PART_OF.value,
    ]


def get_actor_properties() -> list[str]:
    """Get URIs of actor-related properties.

    Returns:
        List of actor relation URIs
    """
    return [
        EUDPPObjectProperty.HAS_ISSUER.value,
        EUDPPObjectProperty.HAS_MANUFACTURER.value,
        EUDPPObjectProperty.HAS_ECONOMIC_OPERATOR.value,
        EUDPPObjectProperty.HAS_BACKUP_COPY_HOST.value,
        EUDPPObjectProperty.HAS_ROLE.value,
        EUDPPObjectProperty.IS_ROLE_OF.value,
        EUDPPObjectProperty.USES_FACILITY.value,
        EUDPPObjectProperty.IS_USED_BY_ACTOR.value,
        EUDPPObjectProperty.IS_ESTABLISHED_IN.value,
        EUDPPObjectProperty.IS_RESIDING_IN.value,
        EUDPPObjectProperty.REPRESENTS_MANUFACTURER.value,
        EUDPPObjectProperty.IS_REPRESENTED_BY.value,
    ]


def get_actor_datatype_properties() -> list[str]:
    """Get URIs of actor datatype properties (Phase 2).

    Returns:
        List of actor datatype property URIs
    """
    return [
        EUDPPDatatypeProperty.ACTOR_NAME.value,
        EUDPPDatatypeProperty.ELECTRONIC_CONTACT.value,
        EUDPPDatatypeProperty.POSTAL_ADDRESS.value,
        EUDPPDatatypeProperty.REGISTERED_TRADE_NAME.value,
        EUDPPDatatypeProperty.REGISTERED_TRADEMARK.value,
        EUDPPDatatypeProperty.UNIQUE_OPERATOR_ID.value,
    ]


def get_facility_properties() -> list[str]:
    """Get URIs of facility-related properties (Phase 2).

    Returns:
        List of facility property URIs
    """
    return [
        EUDPPObjectProperty.USES_FACILITY.value,
        EUDPPObjectProperty.IS_USED_BY_ACTOR.value,
        EUDPPDatatypeProperty.UNIQUE_FACILITY_ID.value,
    ]


def get_lifecycle_properties() -> list[str]:
    """Get URIs of DPP lifecycle properties.

    Returns:
        List of lifecycle datatype property URIs
    """
    return [
        EUDPPDatatypeProperty.VALID_FROM.value,
        EUDPPDatatypeProperty.VALID_UNTIL.value,
        EUDPPDatatypeProperty.LAST_UPDATE.value,
        EUDPPDatatypeProperty.STATUS.value,
        EUDPPDatatypeProperty.SCHEMA_VERSION.value,
        EUDPPDatatypeProperty.LINK_TO_PREVIOUS_DPP.value,
    ]


def get_substance_properties() -> list[str]:
    """Get URIs of substance of concern properties (Phase 3).

    Returns:
        List of SOC property URIs
    """
    return [
        EUDPPObjectProperty.CONTAINS_SUBSTANCE_OF_CONCERN.value,
        EUDPPObjectProperty.HAS_CONCENTRATION.value,
        EUDPPObjectProperty.HAS_LIFECYCLE_STAGE.value,
        EUDPPObjectProperty.HAS_THRESHOLD.value,
        EUDPPDatatypeProperty.NAME_IUPAC.value,
        EUDPPDatatypeProperty.NAME_CAS.value,
        EUDPPDatatypeProperty.NUMBER_CAS.value,
        EUDPPDatatypeProperty.NUMBER_EC.value,
        EUDPPDatatypeProperty.ABBREVIATION.value,
        EUDPPDatatypeProperty.TRADE_NAME.value,
        EUDPPDatatypeProperty.USUAL_NAME.value,
        EUDPPDatatypeProperty.OTHER_NAME.value,
        EUDPPDatatypeProperty.SUBSTANCE_LOCATION.value,
        EUDPPDatatypeProperty.HAS_IMPACT_ON_ENVIRONMENT.value,
        EUDPPDatatypeProperty.HAS_IMPACT_ON_HUMAN_HEALTH.value,
    ]


def get_lca_properties() -> list[str]:
    """Get URIs of LCA-related properties (Phase 4).

    Returns:
        List of LCA property URIs
    """
    return [
        EUDPPObjectProperty.QUANTIFIES.value,
        EUDPPObjectProperty.QUANTIFIED_BY.value,
        EUDPPObjectProperty.ICI_ASSESS_IC.value,
        EUDPPObjectProperty.ICI_COMPUTES_IR.value,
        EUDPPObjectProperty.CF_QUANTIFIES_ICI.value,
        EUDPPObjectProperty.CM_CALCULATES_CF.value,
        EUDPPObjectProperty.METHOD_USES_CM.value,
        EUDPPObjectProperty.INCLUDES.value,
        EUDPPObjectProperty.IMPOSES.value,
        EUDPPObjectProperty.CORRESPONDS_TO_IC.value,
        EUDPPDatatypeProperty.LCA_HAS_UNIT.value,
        EUDPPDatatypeProperty.LCA_NUMERIC_VALUE.value,
    ]


def is_product_relation(uri: str) -> bool:
    """Check if a URI is a product relationship property.

    Args:
        uri: Property URI to check

    Returns:
        True if URI is a product relation property
    """
    return uri in get_product_hierarchy_properties()
