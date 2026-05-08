"""EU DPP Core Ontology LCA and Environmental Footprint definitions.

Provides dataclass representations of Life Cycle Assessment (LCA) and
Environmental Footprint (EF) entities from the EU DPP Core Ontology,
based on PEF 3.1 methodology and ESPR requirements.

Source: EU DPP Core Ontology v2.0 (LCA module)
Namespace: http://dpp.cea.fr/EUDPP/LCA#
Note: Different namespace from other modules (cea.fr not taltech.ee)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import ClassVar

# =============================================================================
# LCA Namespace
# =============================================================================


LCA_NAMESPACE = "http://dpp.cea.fr/EUDPP/LCA#"
LCA_PREFIX = "lca"


# =============================================================================
# LCA Class Enums
# =============================================================================


class LCAClass(str, Enum):
    """EU DPP LCA module class URIs."""

    ENVIRONMENTAL_FOOTPRINT = "lca:Environmental_Footprint"
    CARBON_FOOTPRINT = "lca:Carbon_Footprint"
    MATERIAL_FOOTPRINT = "lca:Material_Footprint"
    ENVIRONMENTAL_IMPACT = "lca:Environmental_Impact"
    IMPACT_CATEGORY = "lca:Impact_Category"
    IMPACT_CATEGORY_INDICATOR = "lca:Impact_Category_Indicator"
    IMPACT_POTENTIAL_RESULT = "lca:Impact_potential_result"
    CHARACTERIZATION_FACTOR = "lca:Characterization_Factor"
    CHARACTERIZATION_MODEL = "lca:Characterization_Model"
    METHOD = "lca:Method"
    METHODOLOGY = "lca:Methodology"


class ImpactCategory(str, Enum):
    """PEF 3.1 impact categories per ESPR Annex I.

    The 16 environmental impact categories defined in the Product
    Environmental Footprint (PEF) methodology version 3.1.

    Source: lca_v2.0.ttl
    """

    ACIDIFICATION = "lca:Acidification"
    CLIMATE_CHANGE = "lca:Climate_change_total"
    ECOTOXICITY_FRESHWATER = "lca:Ecotoxicity_freshwater"
    EUTROPHICATION_FRESHWATER = "lca:Eutrophication_freshwater"
    EUTROPHICATION_MARINE = "lca:Eutrophication_marine"
    EUTROPHICATION_TERRESTRIAL = "lca:Eutrophication_terrestrial"
    HUMAN_TOXICITY_CANCER = "lca:Human_toxicity_cancer"
    HUMAN_TOXICITY_NON_CANCER = "lca:Human_toxicity_non_cancer"
    IONISING_RADIATION = "lca:Ionising_radiation_human_health"
    LAND_USE = "lca:Land_use_occupation_and_transformation"
    OZONE_DEPLETION = "lca:Ozone_depletion"
    PARTICULATE_MATTER = "lca:Particulate_matter"
    PHOTOCHEMICAL_OZONE = "lca:Photochemical_ozone_formation_human_health"
    RESOURCE_FOSSILS = "lca:Resource_use_fossils"
    RESOURCE_MINERALS = "lca:Resource_use_minerals_and_metals"
    WATER_USE = "lca:Water_use"


class ImpactCategoryIndicator(str, Enum):
    """PEF 3.1 impact category indicators.

    Metrics used to quantify impact categories.

    Source: lca_v2.0.ttl
    """

    # Climate change
    GWP100 = "lca:Global_Warming_Potential_GWP100"

    # Acidification / Eutrophication terrestrial
    ACCUMULATED_EXCEEDANCE = "lca:Accumulated_Exceedance_AE"

    # Eutrophication freshwater
    FRESHWATER_NUTRIENTS_P = "lca:Fraction_of_nutrients_reaching_freshwater_end_compartment_P"

    # Eutrophication marine
    MARINE_NUTRIENTS_N = "lca:Fraction_of_nutrients_reaching_marine_end_compartment_N"

    # Human toxicity (cancer and non-cancer)
    CTUH = "lca:Comparative_Toxic_Unit_for_humans_CTUh"

    # Ecotoxicity freshwater
    CTUE = "lca:Comparative_Toxic_Unit_for_ecosystems_CTUe"

    # Ionising radiation
    HUMAN_EXPOSURE_U235 = "lca:Human_exposure_efficiency_relative_to_U235"

    # Land use
    SOIL_QUALITY_INDEX = "lca:Soil_quality_index_dimensionless"

    # Ozone depletion
    ODP = "lca:Ozone_Depletion_Potential_ODP"

    # Particulate matter
    DISEASE_INCIDENCE = "lca:Impact_on_human_health"

    # Photochemical ozone formation
    TROPOSPHERIC_OZONE = "lca:Tropospheric_ozone_concentration_increase"

    # Resource use fossils
    ADP_FOSSIL = "lca:Biotic_resource_depletion_-_fossil_fuels_ADP_fossil"

    # Resource use minerals and metals
    ADP_ULTIMATE = "lca:Abiotic_resource_depletion_ADP_ultimate_reserves"

    # Water use
    AWARE = "lca:User_deprivation_potential_deprivation_weighted_consumption"


class CharacterizationModel(str, Enum):
    """LCA characterization models per PEF 3.1.

    Mathematical frameworks used to quantify impact categories.

    Source: lca_v2.0.ttl
    """

    # Climate change
    IPCC_2021 = "lca:Bern_model_based_on_IPCC_2021"

    # Human/ecotoxicity
    USETOX_2_1 = "lca:Based_on_USEtox2.1_model"

    # Water use
    AWARE = "lca:Available_WAter_REmaining_AWARE_model"

    # Acidification / Eutrophication terrestrial
    ACCUMULATED_EXCEEDANCE = "lca:Accumulated_Exceedance"

    # Eutrophication freshwater/marine
    EUTREND = "lca:EUTREND_model"

    # Particulate matter
    PM_MODEL = "lca:PM_model"

    # Ionising radiation
    HUMAN_HEALTH_EFFECT = "lca:Human_health_effect_model"

    # Ozone depletion
    EDIP = "lca:EDIP_model"

    # Land use
    LANCA = "lca:LANCA_model"

    # Photochemical ozone formation
    LOTOS_EUROS = "lca:LOTOS_EUROS_model"

    # Resource use
    CML_2002 = "lca:CML_2002_method_v.4.8"


# =============================================================================
# Impact Category Units
# =============================================================================


IMPACT_CATEGORY_UNITS: dict[str, str] = {
    ImpactCategory.CLIMATE_CHANGE.value: "kg CO2-eq",
    ImpactCategory.ACIDIFICATION.value: "mol H+-eq",
    ImpactCategory.EUTROPHICATION_FRESHWATER.value: "kg P-eq",
    ImpactCategory.EUTROPHICATION_MARINE.value: "kg N-eq",
    ImpactCategory.EUTROPHICATION_TERRESTRIAL.value: "mol N-eq",
    ImpactCategory.ECOTOXICITY_FRESHWATER.value: "CTUe",
    ImpactCategory.HUMAN_TOXICITY_CANCER.value: "CTUh",
    ImpactCategory.HUMAN_TOXICITY_NON_CANCER.value: "CTUh",
    ImpactCategory.IONISING_RADIATION.value: "kBq U235-eq",
    ImpactCategory.LAND_USE.value: "Pt",
    ImpactCategory.OZONE_DEPLETION.value: "kg CFC-11-eq",
    ImpactCategory.PARTICULATE_MATTER.value: "disease incidence",
    ImpactCategory.PHOTOCHEMICAL_OZONE.value: "kg NMVOC-eq",
    ImpactCategory.RESOURCE_FOSSILS.value: "MJ",
    ImpactCategory.RESOURCE_MINERALS.value: "kg Sb-eq",
    ImpactCategory.WATER_USE.value: "m³ world-eq",
}


# =============================================================================
# LCA Dataclasses
# =============================================================================


@dataclass(frozen=True, slots=True)
class EnvironmentalFootprint:
    """Environmental Footprint per EU DPP LCA module.

    Quantifies environmental impacts of a product system.

    Source: lca_v2.0.ttl
    """

    _class_uri: ClassVar[str] = LCAClass.ENVIRONMENTAL_FOOTPRINT.value


@dataclass(frozen=True, slots=True)
class CarbonFootprint(EnvironmentalFootprint):
    """Carbon Footprint per ESPR Art 2(25).

    The sum of greenhouse gas emissions and removals in a product system,
    expressed as CO2 equivalents based on life cycle assessment using
    the single impact category of climate change.

    Source: lca_v2.0.ttl
    """

    _class_uri: ClassVar[str] = LCAClass.CARBON_FOOTPRINT.value

    value: Decimal | None = None
    unit: str = "kg CO2-eq"
    methodology: str | None = None
    scope: str | None = None


@dataclass(frozen=True, slots=True)
class MaterialFootprint(EnvironmentalFootprint):
    """Material Footprint per ESPR Art 2(26).

    The total amount of raw materials extracted to meet final
    consumption demands.

    Source: lca_v2.0.ttl
    """

    _class_uri: ClassVar[str] = LCAClass.MATERIAL_FOOTPRINT.value

    value: Decimal | None = None
    unit: str = "kg"
    methodology: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentalImpact:
    """Environmental Impact per ESPR Art 2(14).

    Any change to the environment, whether adverse or beneficial,
    wholly or partially resulting from a product during its life cycle.

    Source: lca_v2.0.ttl
    """

    _class_uri: ClassVar[str] = LCAClass.ENVIRONMENTAL_IMPACT.value

    description: str | None = None
    lifecycle_stage: str | None = None


@dataclass(frozen=True, slots=True)
class ImpactResult:
    """Impact assessment result per PEF methodology.

    Links an impact category indicator to a product reference flow
    with its computed value.

    Source: lca_v2.0.ttl
    """

    _class_uri: ClassVar[str] = LCAClass.IMPACT_POTENTIAL_RESULT.value

    category: str
    value: Decimal
    unit: str
    indicator: str | None = None
    model: str | None = None

    def validate(self) -> list[str]:
        """Validate impact result values.

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        # Validate category is known
        valid_categories = [c.value for c in ImpactCategory]
        if self.category not in valid_categories:
            errors.append(f"Unknown impact category: {self.category}")

        return errors


@dataclass(frozen=True, slots=True)
class CharacterizationFactor:
    """Characterization Factor per LCA methodology.

    Factors that quantify the relative impact of different substances
    within the same category, used to convert emissions into impact scores.

    Source: lca_v2.0.ttl
    """

    _class_uri: ClassVar[str] = LCAClass.CHARACTERIZATION_FACTOR.value

    name: str
    value: Decimal | None = None
    unit: str | None = None
    model: str | None = None


@dataclass(frozen=True, slots=True)
class LCAMethodology:
    """LCA Methodology per PEF framework.

    Groups related LCIA methods. Examples include EN15804+A2,
    EF v3.1, Impact World.

    Source: lca_v2.0.ttl
    """

    _class_uri: ClassVar[str] = LCAClass.METHODOLOGY.value

    name: str
    version: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class LCAMethod:
    """LCA Method per PEF framework.

    LCIA methods allow transforming and aggregating emissions to
    environment and resource use data into interpretable impact scores.

    Source: lca_v2.0.ttl
    """

    _class_uri: ClassVar[str] = LCAClass.METHOD.value

    name: str
    methodology: str | None = None
    characterization_model: str | None = None


@dataclass(frozen=True, slots=True)
class ProductEnvironmentalFootprint:
    """Product Environmental Footprint (PEF) result.

    Complete PEF assessment result for a product, containing
    impact results for all 16 PEF 3.1 categories.

    This is a convenience class for aggregating PEF results.
    """

    _class_uri: ClassVar[str] = "lca:ProductEnvironmentalFootprint"

    product_name: str | None = None
    functional_unit: str | None = None
    methodology_version: str = "PEF 3.1"
    impact_results: tuple[ImpactResult, ...] = ()

    def get_impact(self, category: ImpactCategory) -> ImpactResult | None:
        """Get impact result for a specific category.

        Args:
            category: Impact category to retrieve

        Returns:
            ImpactResult for the category, or None if not found
        """
        for result in self.impact_results:
            if result.category == category.value:
                return result
        return None

    def has_all_categories(self) -> bool:
        """Check if all 16 PEF categories are present.

        Returns:
            True if all categories have results
        """
        categories_present = {r.category for r in self.impact_results}
        all_categories = {c.value for c in ImpactCategory}
        return all_categories.issubset(categories_present)

    def missing_categories(self) -> list[str]:
        """Get list of missing impact categories.

        Returns:
            List of missing category URIs
        """
        categories_present = {r.category for r in self.impact_results}
        all_categories = {c.value for c in ImpactCategory}
        return list(all_categories - categories_present)


# =============================================================================
# Helper Functions
# =============================================================================


def get_all_impact_categories() -> list[str]:
    """Get all PEF 3.1 impact category URIs.

    Returns:
        List of 16 impact category URIs
    """
    return [c.value for c in ImpactCategory]


def get_impact_category_unit(category: str) -> str | None:
    """Get the standard unit for an impact category.

    Args:
        category: Impact category URI

    Returns:
        Unit string, or None if category unknown
    """
    return IMPACT_CATEGORY_UNITS.get(category)


def get_all_characterization_models() -> list[str]:
    """Get all characterization model URIs.

    Returns:
        List of characterization model URIs
    """
    return [m.value for m in CharacterizationModel]


def get_all_impact_indicators() -> list[str]:
    """Get all impact category indicator URIs.

    Returns:
        List of impact category indicator URIs
    """
    return [i.value for i in ImpactCategoryIndicator]


def is_climate_related(category: str) -> bool:
    """Check if impact category is climate-related.

    Args:
        category: Impact category URI

    Returns:
        True if category is climate change
    """
    return category == ImpactCategory.CLIMATE_CHANGE.value


def is_toxicity_related(category: str) -> bool:
    """Check if impact category is toxicity-related.

    Args:
        category: Impact category URI

    Returns:
        True if category relates to human or ecosystem toxicity
    """
    toxicity_categories = {
        ImpactCategory.HUMAN_TOXICITY_CANCER.value,
        ImpactCategory.HUMAN_TOXICITY_NON_CANCER.value,
        ImpactCategory.ECOTOXICITY_FRESHWATER.value,
    }
    return category in toxicity_categories


def is_resource_related(category: str) -> bool:
    """Check if impact category is resource-related.

    Args:
        category: Impact category URI

    Returns:
        True if category relates to resource use
    """
    resource_categories = {
        ImpactCategory.RESOURCE_FOSSILS.value,
        ImpactCategory.RESOURCE_MINERALS.value,
        ImpactCategory.WATER_USE.value,
        ImpactCategory.LAND_USE.value,
    }
    return category in resource_categories


def expand_lca_uri(compact_uri: str) -> str:
    """Expand compact LCA URI to full URI.

    Args:
        compact_uri: URI with lca: prefix

    Returns:
        Full URI with namespace
    """
    if compact_uri.startswith(f"{LCA_PREFIX}:"):
        return compact_uri.replace(f"{LCA_PREFIX}:", LCA_NAMESPACE)
    return compact_uri


def compact_lca_uri(full_uri: str) -> str:
    """Compact full LCA URI to prefixed form.

    Args:
        full_uri: Full URI with namespace

    Returns:
        Compact URI with lca: prefix
    """
    if full_uri.startswith(LCA_NAMESPACE):
        return full_uri.replace(LCA_NAMESPACE, f"{LCA_PREFIX}:")
    return full_uri
