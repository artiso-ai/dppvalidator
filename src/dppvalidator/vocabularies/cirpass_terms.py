"""CIRPASS-2 core terms and ESPR Annex I product parameters.

Source: Ontology Requirements Specification for an EU DPP Core Ontology Proposal
DOI: 10.5281/zenodo.14892665
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class CIRPASSTerm:
    """Definition of a CIRPASS core term."""

    name: str
    definition: str
    source: str
    article: str | None = None


class GranularityLevel(str, Enum):
    """DPP granularity levels per EU DPP Core Ontology and SR5423.

    Values from official CIRPASS-2 ontology v1.7.1.
    Note: The official ontology uses 'product' not 'item'.
    """

    MODEL = "model"  # All units of a product version
    BATCH = "batch"  # Subset from specific plant/time
    PRODUCT = "product"  # Single unit (official term)

    # Backward compatibility alias
    ITEM = "product"  # Deprecated: use PRODUCT


class ESPRAnnexIParameter(str, Enum):
    """Product parameters from ESPR Annex I."""

    DURABILITY = "durability"
    RELIABILITY = "reliability"
    EASE_OF_REPAIR = "ease_of_repair"
    EASE_OF_UPGRADING = "ease_of_upgrading"
    RECYCLABILITY = "recyclability"
    SUBSTANCES_OF_CONCERN = "substances_of_concern"
    ENERGY_CONSUMPTION = "energy_consumption"
    WATER_CONSUMPTION = "water_consumption"
    RECYCLED_CONTENT = "recycled_content"
    RENEWABLE_CONTENT = "renewable_content"
    CARBON_FOOTPRINT = "carbon_footprint"
    ENVIRONMENTAL_FOOTPRINT = "environmental_footprint"
    MATERIAL_FOOTPRINT = "material_footprint"
    MICROPLASTIC_RELEASE = "microplastic_release"
    EMISSIONS = "emissions"
    WASTE_GENERATED = "waste_generated"
    WEIGHT_VOLUME = "weight_volume"
    LIGHTWEIGHT_DESIGN = "lightweight_design"


CIRPASS_CORE_TERMS: dict[str, CIRPASSTerm] = {
    "Product": CIRPASSTerm(
        name="Product",
        definition="Any physical goods that are placed on the market or put into service.",
        source="ESPR",
        article="Art 2(1)",
    ),
    "Component": CIRPASSTerm(
        name="Component",
        definition="A product intended to be incorporated into another product.",
        source="ESPR",
        article="Art 2(2)",
    ),
    "IntermediateProduct": CIRPASSTerm(
        name="IntermediateProduct",
        definition="A product that requires further manufacturing or transformation.",
        source="ESPR",
        article="Art 2(3)",
    ),
    "ProductGroup": CIRPASSTerm(
        name="ProductGroup",
        definition="A set of products that serve similar purposes and are similar in use.",
        source="ESPR",
        article="Art 2(4)",
    ),
    "Model": CIRPASSTerm(
        name="Model",
        definition="A version of a product of which all units share the same technical "
        "characteristics and the same model identifier.",
        source="SR5423",
        article="Annex II Part B 1.1(2)",
    ),
    "Batch": CIRPASSTerm(
        name="Batch",
        definition="A subset of a specific model composed of all products produced in a "
        "specific manufacturing plant at a specific moment in time.",
        source="SR5423",
        article="Annex II Part B 1.1(3)",
    ),
    "Item": CIRPASSTerm(
        name="Item",
        definition="A single unit of a model.",
        source="SR5423",
        article="Annex II Part B 1.1(4)",
    ),
    "UniqueProductIdentifier": CIRPASSTerm(
        name="UniqueProductIdentifier",
        definition="A unique string of characters for the identification of a product "
        "that also enables a web link to the digital product passport.",
        source="ESPR",
        article="Art 2(30)",
    ),
    "DigitalProductPassport": CIRPASSTerm(
        name="DigitalProductPassport",
        definition="A structured set of product data accessible via electronic means.",
        source="ESPR",
        article="Art 2(28)",
    ),
    "DigitalInstructions": CIRPASSTerm(
        name="DigitalInstructions",
        definition="Instructions in digital format concerning the product in a language "
        "that can be easily understood.",
        source="ESPR",
        article="Art 27(7)",
    ),
    "PerformanceRequirement": CIRPASSTerm(
        name="PerformanceRequirement",
        definition="A quantitative or non-quantitative requirement for a product to "
        "achieve a certain performance level.",
        source="ESPR",
        article="Art 2(8)",
    ),
    "ClassOfPerformance": CIRPASSTerm(
        name="ClassOfPerformance",
        definition="A range of performance levels in relation to one or more product "
        "parameters, ordered to allow for product differentiation.",
        source="ESPR",
        article="Art 2(15)",
    ),
    "Durability": CIRPASSTerm(
        name="Durability",
        definition="The ability of a product to maintain over time its function and "
        "performance under specified conditions of use, maintenance and repair.",
        source="ESPR",
        article="Art 2(22)",
    ),
    "Reliability": CIRPASSTerm(
        name="Reliability",
        definition="The probability that a product functions as required under given "
        "conditions for a given duration.",
        source="ESPR",
        article="Art 2(16)",
    ),
    "ConformityAttestation": CIRPASSTerm(
        name="ConformityAttestation",
        definition="A formal document stating that compliance with specific standards, "
        "regulations, or requirements has been demonstrated.",
        source="CIRPASS-2",
        article=None,
    ),
    "ConformityAssessmentBody": CIRPASSTerm(
        name="ConformityAssessmentBody",
        definition="A body that performs conformity assessment activities including "
        "calibration, testing, certification and inspection.",
        source="ESPR",
        article="Art 2(52)",
    ),
    "EconomicOperator": CIRPASSTerm(
        name="EconomicOperator",
        definition="The manufacturer, authorised representative, importer, distributor, "
        "dealer or other natural or legal person.",
        source="ESPR",
        article="Art 2(37)",
    ),
    "Manufacturer": CIRPASSTerm(
        name="Manufacturer",
        definition="Any natural or legal person who manufactures a product or has a "
        "product designed or manufactured under their name or trademark.",
        source="ESPR",
        article="Art 2(38)",
    ),
    "SubstanceOfConcern": CIRPASSTerm(
        name="SubstanceOfConcern",
        definition="A substance that is hazardous or has negative impacts on human "
        "health or the environment.",
        source="ESPR",
        article="Art 2(28)",
    ),
    "LifeCycleEvent": CIRPASSTerm(
        name="LifeCycleEvent",
        definition="An event that occurs during the lifecycle of a product including "
        "manufacturing, use, repair, refurbishment and end-of-life.",
        source="CIRPASS-2",
        article=None,
    ),
    "CarbonFootprint": CIRPASSTerm(
        name="CarbonFootprint",
        definition="The sum of greenhouse gas emissions expressed as CO2 equivalent.",
        source="ESPR",
        article="Annex I(n)",
    ),
    "EnvironmentalFootprint": CIRPASSTerm(
        name="EnvironmentalFootprint",
        definition="A quantification of the environmental impact of the product.",
        source="ESPR",
        article="Annex I(m)",
    ),
}


ESPR_ANNEX_I_PARAMETERS: frozenset[str] = frozenset(param.value for param in ESPRAnnexIParameter)


class CIRPASSVocabulary:
    """CIRPASS-2 vocabulary access and validation."""

    TERMS: ClassVar[dict[str, CIRPASSTerm]] = CIRPASS_CORE_TERMS

    @classmethod
    def get_term(cls, name: str) -> CIRPASSTerm | None:
        """Get a CIRPASS term definition by name."""
        return cls.TERMS.get(name)

    @classmethod
    def is_valid_term(cls, name: str) -> bool:
        """Check if a term name is a valid CIRPASS core term."""
        return name in cls.TERMS

    @classmethod
    def get_terms_by_source(cls, source: str) -> list[CIRPASSTerm]:
        """Get all terms from a specific source (ESPR, SR5423, CIRPASS-2)."""
        return [t for t in cls.TERMS.values() if t.source == source]

    @classmethod
    def all_term_names(cls) -> frozenset[str]:
        """Get all CIRPASS term names."""
        return frozenset(cls.TERMS.keys())


def is_valid_granularity_level(level: str) -> bool:
    """Check if a granularity level is valid."""
    try:
        GranularityLevel(level.lower())
        return True
    except ValueError:
        return False


def is_valid_espr_parameter(param: str) -> bool:
    """Check if a parameter is a valid ESPR Annex I parameter."""
    normalized = param.lower().replace("-", "_").replace(" ", "_")
    return normalized in ESPR_ANNEX_I_PARAMETERS


def get_espr_parameters() -> frozenset[str]:
    """Get all ESPR Annex I parameter names."""
    return ESPR_ANNEX_I_PARAMETERS


def get_cirpass_term_count() -> int:
    """Get the count of CIRPASS core terms."""
    return len(CIRPASS_CORE_TERMS)
