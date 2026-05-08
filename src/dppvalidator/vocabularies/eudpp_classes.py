"""EU DPP Core Ontology class definitions.

Provides dataclass representations of the EU DPP Core Ontology class hierarchy,
based on the official CIRPASS-2 ontology v1.7.1.

Source: EU DPP Core Ontology v1.7.1 (Product and DPP module)
Namespace: http://dpp.taltech.ee/EUDPP#
DOI: 10.5281/zenodo.15270342
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import ClassVar


class EUDPPClass(str, Enum):
    """EU DPP Core Ontology class URIs."""

    # Core classes
    DPP = "eudpp:DPP"
    PRODUCT = "eudpp:Product"
    PROPERTY = "eudpp:Property"
    QUANTITATIVE_PROPERTY = "eudpp:QuantitativeProperty"
    DOCUMENT = "eudpp:Document"
    CLASSIFICATION_CODE = "eudpp:ClassificationCode"

    # Environmental footprint hierarchy
    ENVIRONMENTAL_FOOTPRINT = "eudpp:EnvironmentalFootprint"
    CARBON_FOOTPRINT = "eudpp:CarbonFootprint"
    MATERIAL_FOOTPRINT = "eudpp:MaterialFootprint"

    # Environmental pollution hierarchy
    ENVIRONMENTAL_POLLUTION = "eudpp:EnvironmentalPollution"
    ENVIRONMENTAL_EMISSION = "eudpp:EnvironmentalEmission"
    EMISSION_TO_AIR = "eudpp:EmissionToAir"
    EMISSION_TO_WATER = "eudpp:EmissionToWater"
    EMISSION_TO_SOIL = "eudpp:EmissionToSoil"
    PLASTICS_RELEASE = "eudpp:PlasticsRelease"
    MICROPLASTIC_RELEASE = "eudpp:MicroplasticRelease"
    NANOPLASTIC_RELEASE = "eudpp:NanoplasticRelease"

    # Resource consumption hierarchy
    RESOURCE_CONSUMPTION = "eudpp:ResourceConsumption"
    ENERGY_CONSUMPTION = "eudpp:EnergyConsumption"
    WATER_CONSUMPTION = "eudpp:WaterConsumption"
    LAND_USE = "eudpp:LandUse"
    RECYCLED_MATERIALS_USE = "eudpp:RecycledMaterialsUse"
    SUSTAINABLE_RENEWABLE_MATERIALS_USE = "eudpp:SustainableRenewableMaterialsUse"

    # Circular economy indicators
    CIRCULAR_ECONOMY_INDICATOR = "eudpp:CircularEconomyIndicator"
    RECYCLING_RATE = "eudpp:RecyclingRate"
    RECYCLING_COLLECTION_RATE = "eudpp:RecyclingCollectionRate"
    RECOVERABLE_RATE = "eudpp:RecoverableRate"

    # Waste generation
    WASTE_GENERATION_AMOUNT = "eudpp:WasteGenerationAmount"
    HAZARDOUS_WASTE_AMOUNT = "eudpp:HazardousWasteAmount"
    PACKAGING_WASTE_AMOUNT = "eudpp:PackagingWasteAmount"
    PLASTICS_WASTE_AMOUNT = "eudpp:PlasticsWasteAmount"

    # Quality indicators
    QUALITY_INDICATOR = "eudpp:QualityIndicator"
    DURABILITY = "eudpp:Durability"
    RELIABILITY = "eudpp:Reliability"

    # Product dimensions
    PRODUCT_DIMENSION = "eudpp:ProductDimension"
    HEIGHT = "eudpp:Height"
    LENGTH = "eudpp:Length"
    WIDTH = "eudpp:Width"
    VOLUME = "eudpp:Volume"
    WEIGHT = "eudpp:Weight"

    # Substances of concern
    CONCENTRATION_OF_SOC = "eudpp:ConcentrationOfSubstanceOfConcern"
    THRESHOLD_OF_SOC = "eudpp:ThresholdOfSubstanceOfConcern"

    # Instructions
    DIGITAL_INSTRUCTION = "eudpp:DigitalInstruction"

    # Other
    PRODUCT_TO_PACKAGING_RATIO = "eudpp:ProductToPackagingRatio"


@dataclass(frozen=True, slots=True)
class QuantitativeProperty:
    """Base class for quantitative properties per EU DPP Core Ontology.

    A property of the product that is expressed by a quantity value.
    """

    _class_uri: ClassVar[str] = EUDPPClass.QUANTITATIVE_PROPERTY.value

    numerical_value: Decimal
    measurement_unit: str
    tolerance: Decimal | None = None
    dictionary_reference: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentalFootprint(QuantitativeProperty):
    """Environmental footprint per ESPR Art 2(24).

    A quantification of environmental impacts resulting from a product
    throughout its life cycle, based on the Product Environmental Footprint
    method (Recommendation (EU) 2021/2279).
    """

    _class_uri: ClassVar[str] = EUDPPClass.ENVIRONMENTAL_FOOTPRINT.value


@dataclass(frozen=True, slots=True)
class CarbonFootprint(EnvironmentalFootprint):
    """Carbon footprint per ESPR Art 2(25).

    The sum of greenhouse gas emissions and removals in a product system,
    expressed as CO2 equivalents, based on life cycle assessment using
    the single impact category of climate change.
    """

    _class_uri: ClassVar[str] = EUDPPClass.CARBON_FOOTPRINT.value


@dataclass(frozen=True, slots=True)
class MaterialFootprint(EnvironmentalFootprint):
    """Material footprint per ESPR Art 2(26).

    The total amount of raw materials extracted to meet final consumption
    demands.
    """

    _class_uri: ClassVar[str] = EUDPPClass.MATERIAL_FOOTPRINT.value


@dataclass(frozen=True, slots=True)
class EnvironmentalPollution(QuantitativeProperty):
    """Environmental pollution base class.

    The addition of any substance or form of energy to the environment
    at a rate faster than it can be dispersed or safely stored.
    """

    _class_uri: ClassVar[str] = EUDPPClass.ENVIRONMENTAL_POLLUTION.value


@dataclass(frozen=True, slots=True)
class EnvironmentalEmission(EnvironmentalPollution):
    """Environmental emission base class per ESPR Annex I (q).

    Emissions to air, water or soil released in one or more lifecycle
    stages of the product.
    """

    _class_uri: ClassVar[str] = EUDPPClass.ENVIRONMENTAL_EMISSION.value

    lifecycle_stage: str | None = None


@dataclass(frozen=True, slots=True)
class EmissionToAir(EnvironmentalEmission):
    """Emission to air per ESPR Annex I (q)."""

    _class_uri: ClassVar[str] = EUDPPClass.EMISSION_TO_AIR.value


@dataclass(frozen=True, slots=True)
class EmissionToWater(EnvironmentalEmission):
    """Emission to water per ESPR Annex I (q)."""

    _class_uri: ClassVar[str] = EUDPPClass.EMISSION_TO_WATER.value


@dataclass(frozen=True, slots=True)
class EmissionToSoil(EnvironmentalEmission):
    """Emission to soil per ESPR Annex I (q)."""

    _class_uri: ClassVar[str] = EUDPPClass.EMISSION_TO_SOIL.value


@dataclass(frozen=True, slots=True)
class PlasticsRelease(EnvironmentalPollution):
    """Plastics release base class per ESPR Annex I (p).

    Microplastic and nanoplastic release during relevant product life
    cycle stages, including manufacturing, transport, use and end of life.
    """

    _class_uri: ClassVar[str] = EUDPPClass.PLASTICS_RELEASE.value

    lifecycle_stage: str | None = None


@dataclass(frozen=True, slots=True)
class MicroplasticRelease(PlasticsRelease):
    """Microplastic release per ESPR Annex I (p)."""

    _class_uri: ClassVar[str] = EUDPPClass.MICROPLASTIC_RELEASE.value


@dataclass(frozen=True, slots=True)
class NanoplasticRelease(PlasticsRelease):
    """Nanoplastic release per ESPR Annex I (p)."""

    _class_uri: ClassVar[str] = EUDPPClass.NANOPLASTIC_RELEASE.value


@dataclass(frozen=True, slots=True)
class ResourceConsumption(QuantitativeProperty):
    """Resource consumption base class.

    Resource consumption of the product during its lifecycle.
    """

    _class_uri: ClassVar[str] = EUDPPClass.RESOURCE_CONSUMPTION.value


@dataclass(frozen=True, slots=True)
class EnergyConsumption(ResourceConsumption):
    """Energy consumption of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.ENERGY_CONSUMPTION.value


@dataclass(frozen=True, slots=True)
class WaterConsumption(ResourceConsumption):
    """Water consumption of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.WATER_CONSUMPTION.value


@dataclass(frozen=True, slots=True)
class LandUse(ResourceConsumption):
    """Land use of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.LAND_USE.value


@dataclass(frozen=True, slots=True)
class RecycledMaterialsUse(ResourceConsumption):
    """Recycled materials use of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.RECYCLED_MATERIALS_USE.value


@dataclass(frozen=True, slots=True)
class SustainableRenewableMaterialsUse(ResourceConsumption):
    """Sustainable renewable materials use of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.SUSTAINABLE_RENEWABLE_MATERIALS_USE.value


@dataclass(frozen=True, slots=True)
class CircularEconomyIndicator(QuantitativeProperty):
    """Circular economy indicator base class.

    Measures for monitoring the transition to a circular economy and
    measuring the effects of new policy and trends.
    """

    _class_uri: ClassVar[str] = EUDPPClass.CIRCULAR_ECONOMY_INDICATOR.value


@dataclass(frozen=True, slots=True)
class RecyclingRate(CircularEconomyIndicator):
    """Recycling rate of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.RECYCLING_RATE.value


@dataclass(frozen=True, slots=True)
class RecyclingCollectionRate(CircularEconomyIndicator):
    """Recycling collection rate of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.RECYCLING_COLLECTION_RATE.value


@dataclass(frozen=True, slots=True)
class RecoverableRate(CircularEconomyIndicator):
    """Recoverable rate of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.RECOVERABLE_RATE.value


@dataclass(frozen=True, slots=True)
class WasteGenerationAmount(QuantitativeProperty):
    """Waste generation amount base class."""

    _class_uri: ClassVar[str] = EUDPPClass.WASTE_GENERATION_AMOUNT.value


@dataclass(frozen=True, slots=True)
class HazardousWasteAmount(WasteGenerationAmount):
    """Hazardous waste amount of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.HAZARDOUS_WASTE_AMOUNT.value


@dataclass(frozen=True, slots=True)
class PackagingWasteAmount(WasteGenerationAmount):
    """Packaging waste amount of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.PACKAGING_WASTE_AMOUNT.value


@dataclass(frozen=True, slots=True)
class PlasticsWasteAmount(WasteGenerationAmount):
    """Plastics waste amount of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.PLASTICS_WASTE_AMOUNT.value


@dataclass(frozen=True, slots=True)
class QualityIndicator(QuantitativeProperty):
    """Quality indicator base class.

    Product characteristics like durability and reliability.
    """

    _class_uri: ClassVar[str] = EUDPPClass.QUALITY_INDICATOR.value


@dataclass(frozen=True, slots=True)
class Durability(QualityIndicator):
    """Durability per ESPR Art 2(22).

    The ability of a product to maintain over time its function and
    performance under specified conditions of use, maintenance and repair.
    """

    _class_uri: ClassVar[str] = EUDPPClass.DURABILITY.value


@dataclass(frozen=True, slots=True)
class Reliability(QualityIndicator):
    """Reliability per ESPR Art 2(16).

    The probability that a product functions as required under given
    conditions for a given duration. Usually expressed in terms of
    mean time between failures (MTBF).
    """

    _class_uri: ClassVar[str] = EUDPPClass.RELIABILITY.value

    mtbf_hours: Decimal | None = None


@dataclass(frozen=True, slots=True)
class ProductDimension(QuantitativeProperty):
    """Product dimension base class per ESPR Annex I.

    Measurements of length, width, height, volume, and weight.
    """

    _class_uri: ClassVar[str] = EUDPPClass.PRODUCT_DIMENSION.value


@dataclass(frozen=True, slots=True)
class Height(ProductDimension):
    """Height of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.HEIGHT.value


@dataclass(frozen=True, slots=True)
class Length(ProductDimension):
    """Length of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.LENGTH.value


@dataclass(frozen=True, slots=True)
class Width(ProductDimension):
    """Width of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.WIDTH.value


@dataclass(frozen=True, slots=True)
class Volume(ProductDimension):
    """Volume of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.VOLUME.value


@dataclass(frozen=True, slots=True)
class Weight(ProductDimension):
    """Weight of the product."""

    _class_uri: ClassVar[str] = EUDPPClass.WEIGHT.value


# =============================================================================
# Core Entity Classes (Phase 1: CIRPASS-2 Integration)
# =============================================================================


@dataclass(frozen=True, slots=True)
class Document:
    """Document per EU DPP Core Ontology.

    Represents a document associated with a product or DPP, such as
    user manuals, compliance certificates, or technical specifications.

    Source: product_dpp_v1.7.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPClass.DOCUMENT.value

    content_type: str | None = None
    web_link: str | None = None
    title: str | None = None
    language: str | None = None


@dataclass(frozen=True, slots=True)
class ClassificationCode:
    """Classification code per ESPR Art 2(4).

    Represents a product classification code from a controlled vocabulary
    such as TARIC, HS codes, or other classification systems.

    Source: product_dpp_v1.7.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPClass.CLASSIFICATION_CODE.value

    code_set: str
    code_value: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class DigitalInstruction(Document):
    """Digital instruction per ESPR Art 27(7).

    A specific type of document containing instructions for product use,
    maintenance, repair, or end-of-life handling in digital format.

    Source: product_dpp_v1.7.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPClass.DIGITAL_INSTRUCTION.value

    instruction_type: str | None = None


@dataclass(frozen=True, slots=True)
class EUDPPProduct:
    """Product entity per EU DPP Core Ontology.

    Represents a physical product placed on the market, as defined in
    ESPR Art 2(1). This is the EU DPP vocabulary representation, separate
    from the UNTP Product model to maintain extension-layer separation.

    Source: product_dpp_v1.7.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPClass.PRODUCT.value

    unique_product_id: str | None = None
    product_name: str | None = None
    description: str | None = None
    gtin: str | None = None
    commodity_code: str | None = None
    product_image: str | None = None
    is_energy_related: bool | None = None


@dataclass(frozen=True, slots=True)
class EUDPP_DPP:
    """Digital Product Passport per EU DPP Core Ontology.

    Represents the DPP entity as defined in ESPR Art 2(28). This is the
    EU DPP vocabulary representation, separate from the UNTP
    DigitalProductPassport model to maintain extension-layer separation.

    Source: product_dpp_v1.7.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPClass.DPP.value

    unique_dpp_id: str
    granularity: str | None = None
    status: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    last_update: str | None = None
    schema_version: str | None = None
    link_to_previous_dpp: str | None = None


# Class hierarchy mapping for validation
EUDPP_CLASS_HIERARCHY: dict[str, list[str]] = {
    # Core entity types
    "eudpp:DPP": [],
    "eudpp:Product": [],
    # Document subtypes
    "eudpp:Document": [
        "eudpp:DigitalInstruction",
    ],
    # Classification
    "eudpp:ClassificationCode": [],
    # QuantitativeProperty subtypes
    "eudpp:QuantitativeProperty": [
        "eudpp:EnvironmentalFootprint",
        "eudpp:EnvironmentalPollution",
        "eudpp:ResourceConsumption",
        "eudpp:CircularEconomyIndicator",
        "eudpp:WasteGenerationAmount",
        "eudpp:QualityIndicator",
        "eudpp:ProductDimension",
        "eudpp:ConcentrationOfSubstanceOfConcern",
        "eudpp:ThresholdOfSubstanceOfConcern",
        "eudpp:ProductToPackagingRatio",
    ],
    # Environmental footprint subtypes
    "eudpp:EnvironmentalFootprint": [
        "eudpp:CarbonFootprint",
        "eudpp:MaterialFootprint",
    ],
    # Environmental pollution subtypes
    "eudpp:EnvironmentalPollution": [
        "eudpp:EnvironmentalEmission",
        "eudpp:PlasticsRelease",
    ],
    # Emission subtypes
    "eudpp:EnvironmentalEmission": [
        "eudpp:EmissionToAir",
        "eudpp:EmissionToWater",
        "eudpp:EmissionToSoil",
    ],
    # Plastics release subtypes
    "eudpp:PlasticsRelease": [
        "eudpp:MicroplasticRelease",
        "eudpp:NanoplasticRelease",
    ],
    # Resource consumption subtypes
    "eudpp:ResourceConsumption": [
        "eudpp:EnergyConsumption",
        "eudpp:WaterConsumption",
        "eudpp:LandUse",
        "eudpp:RecycledMaterialsUse",
        "eudpp:SustainableRenewableMaterialsUse",
    ],
    # Circular economy subtypes
    "eudpp:CircularEconomyIndicator": [
        "eudpp:RecyclingRate",
        "eudpp:RecyclingCollectionRate",
        "eudpp:RecoverableRate",
    ],
    # Waste subtypes
    "eudpp:WasteGenerationAmount": [
        "eudpp:HazardousWasteAmount",
        "eudpp:PackagingWasteAmount",
        "eudpp:PlasticsWasteAmount",
    ],
    # Quality subtypes
    "eudpp:QualityIndicator": [
        "eudpp:Durability",
        "eudpp:Reliability",
    ],
    # Dimension subtypes
    "eudpp:ProductDimension": [
        "eudpp:Height",
        "eudpp:Length",
        "eudpp:Width",
        "eudpp:Volume",
        "eudpp:Weight",
    ],
}


def get_class_hierarchy(class_uri: str) -> list[str]:
    """Get all subclasses of a given class.

    Args:
        class_uri: EU DPP class URI (e.g., "eudpp:EnvironmentalFootprint")

    Returns:
        List of subclass URIs
    """
    return EUDPP_CLASS_HIERARCHY.get(class_uri, [])


def is_subclass_of(child_uri: str, parent_uri: str) -> bool:
    """Check if a class is a subclass of another.

    Args:
        child_uri: Potential child class URI
        parent_uri: Potential parent class URI

    Returns:
        True if child is a subclass of parent
    """
    if child_uri == parent_uri:
        return True

    for parent, children in EUDPP_CLASS_HIERARCHY.items():
        if child_uri in children:
            if parent == parent_uri:
                return True
            # Recursive check
            return is_subclass_of(parent, parent_uri)

    return False


def get_all_environmental_classes() -> list[str]:
    """Get all environmental-related class URIs.

    Returns:
        List of environmental class URIs
    """
    return [
        EUDPPClass.ENVIRONMENTAL_FOOTPRINT.value,
        EUDPPClass.CARBON_FOOTPRINT.value,
        EUDPPClass.MATERIAL_FOOTPRINT.value,
        EUDPPClass.ENVIRONMENTAL_POLLUTION.value,
        EUDPPClass.ENVIRONMENTAL_EMISSION.value,
        EUDPPClass.EMISSION_TO_AIR.value,
        EUDPPClass.EMISSION_TO_WATER.value,
        EUDPPClass.EMISSION_TO_SOIL.value,
        EUDPPClass.PLASTICS_RELEASE.value,
        EUDPPClass.MICROPLASTIC_RELEASE.value,
        EUDPPClass.NANOPLASTIC_RELEASE.value,
        EUDPPClass.RESOURCE_CONSUMPTION.value,
        EUDPPClass.ENERGY_CONSUMPTION.value,
        EUDPPClass.WATER_CONSUMPTION.value,
        EUDPPClass.LAND_USE.value,
    ]


def get_all_circular_economy_classes() -> list[str]:
    """Get all circular economy-related class URIs.

    Returns:
        List of circular economy class URIs
    """
    return [
        EUDPPClass.CIRCULAR_ECONOMY_INDICATOR.value,
        EUDPPClass.RECYCLING_RATE.value,
        EUDPPClass.RECYCLING_COLLECTION_RATE.value,
        EUDPPClass.RECOVERABLE_RATE.value,
        EUDPPClass.RECYCLED_MATERIALS_USE.value,
        EUDPPClass.SUSTAINABLE_RENEWABLE_MATERIALS_USE.value,
    ]
