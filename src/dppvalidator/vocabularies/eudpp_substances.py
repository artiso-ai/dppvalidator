"""EU DPP Core Ontology substances of concern definitions.

Provides dataclass representations of substances of concern from the EU DPP
Core Ontology, based on ESPR Art 2(28) and Art 7(5) substance tracking.

Source: EU DPP Core Ontology v1.4.7 (Substances of Concern module)
Namespace: http://dpp.taltech.ee/EUDPP#
DOI: 10.5281/zenodo.15270342
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import ClassVar

# =============================================================================
# SOC Class Enums
# =============================================================================


class EUDPPSubstanceClass(str, Enum):
    """EU DPP Core Ontology substance class URIs."""

    SUBSTANCE = "eudpp:Substance"
    SUBSTANCE_OF_CONCERN = "eudpp:SubstanceOfConcern"
    CONCENTRATION = "eudpp:Concentration"
    THRESHOLD = "eudpp:Threshold"


class LifeCycleStage(str, Enum):
    """Life cycle stages for substances of concern per ESPR Annex I(f)."""

    PRODUCTION = "production"
    IN_PRODUCT = "in_product"
    USE = "use"
    END_OF_LIFE = "end_of_life"
    WASTE = "waste"
    RECYCLING = "recycling"


class HazardCategory(str, Enum):
    """Hazard categories per ESPR Art 2(28) / Regulation (EC) No 1272/2008.

    Substances of concern are classified per these hazard classes.
    """

    # Carcinogenicity (Art 2(28)(b)(i))
    CARCINOGENICITY_1 = "carcinogenicity_cat_1"
    CARCINOGENICITY_2 = "carcinogenicity_cat_2"

    # Germ cell mutagenicity (Art 2(28)(b)(ii))
    MUTAGENICITY_1 = "mutagenicity_cat_1"
    MUTAGENICITY_2 = "mutagenicity_cat_2"

    # Reproductive toxicity (Art 2(28)(b)(iii))
    REPRODUCTIVE_TOXICITY_1 = "reproductive_toxicity_cat_1"
    REPRODUCTIVE_TOXICITY_2 = "reproductive_toxicity_cat_2"

    # Endocrine disruption human health (Art 2(28)(b)(iv))
    ENDOCRINE_DISRUPTION_HUMAN_1 = "endocrine_disruption_human_cat_1"
    ENDOCRINE_DISRUPTION_HUMAN_2 = "endocrine_disruption_human_cat_2"

    # Endocrine disruption environment (Art 2(28)(b)(v))
    ENDOCRINE_DISRUPTION_ENV_1 = "endocrine_disruption_env_cat_1"
    ENDOCRINE_DISRUPTION_ENV_2 = "endocrine_disruption_env_cat_2"

    # Persistent, mobile, toxic (Art 2(28)(b)(vi))
    PMT = "persistent_mobile_toxic"
    VPVM = "very_persistent_very_mobile"

    # Persistent, bioaccumulative, toxic (Art 2(28)(b)(vii))
    PBT = "persistent_bioaccumulative_toxic"
    VPVB = "very_persistent_very_bioaccumulative"

    # Respiratory sensitisation (Art 2(28)(b)(viii))
    RESPIRATORY_SENSITISATION_1 = "respiratory_sensitisation_cat_1"

    # Skin sensitisation (Art 2(28)(b)(ix))
    SKIN_SENSITISATION_1 = "skin_sensitisation_cat_1"

    # Aquatic hazard (Art 2(28)(b)(x))
    AQUATIC_CHRONIC_1 = "aquatic_chronic_cat_1"
    AQUATIC_CHRONIC_2 = "aquatic_chronic_cat_2"
    AQUATIC_CHRONIC_3 = "aquatic_chronic_cat_3"
    AQUATIC_CHRONIC_4 = "aquatic_chronic_cat_4"

    # Ozone layer (Art 2(28)(b)(xi))
    OZONE_LAYER = "hazardous_to_ozone_layer"

    # STOT repeated exposure (Art 2(28)(b)(xii))
    STOT_RE_1 = "stot_repeated_exposure_cat_1"
    STOT_RE_2 = "stot_repeated_exposure_cat_2"

    # STOT single exposure (Art 2(28)(b)(xiii))
    STOT_SE_1 = "stot_single_exposure_cat_1"
    STOT_SE_2 = "stot_single_exposure_cat_2"

    # SVHC per REACH (Art 2(28)(a))
    SVHC = "svhc_reach_art_57"

    # POP per Regulation (EU) 2019/1021 (Art 2(28)(c))
    POP = "persistent_organic_pollutant"


# =============================================================================
# Validation Patterns
# =============================================================================


# CAS Number format: 2-7 digits, hyphen, 2 digits, hyphen, 1 digit
# Example: 50-00-0 (Formaldehyde), 7440-23-5 (Sodium)
CAS_NUMBER_PATTERN = re.compile(r"^\d{2,7}-\d{2}-\d$")

# EC Number format: 3 digits, hyphen, 3 digits, hyphen, 1 digit
# Example: 200-001-8 (Formaldehyde), 231-132-9 (Sodium)
EC_NUMBER_PATTERN = re.compile(r"^\d{3}-\d{3}-\d$")


def is_valid_cas_number(cas_number: str) -> bool:
    """Validate CAS number format.

    CAS numbers follow the format: NNNNNNN-NN-N
    where N is a digit, with 2-7 digits before the first hyphen.

    Args:
        cas_number: CAS number string to validate

    Returns:
        True if format is valid

    Examples:
        >>> is_valid_cas_number("50-00-0")  # Formaldehyde
        True
        >>> is_valid_cas_number("7440-23-5")  # Sodium
        True
        >>> is_valid_cas_number("invalid")
        False
    """
    return bool(CAS_NUMBER_PATTERN.match(cas_number))


def is_valid_ec_number(ec_number: str) -> bool:
    """Validate EC number format.

    EC numbers follow the format: NNN-NNN-N
    where N is a digit.

    Args:
        ec_number: EC number string to validate

    Returns:
        True if format is valid

    Examples:
        >>> is_valid_ec_number("200-001-8")  # Formaldehyde
        True
        >>> is_valid_ec_number("239-934-0")  # Mercurous Oxide
        True
        >>> is_valid_ec_number("invalid")
        False
    """
    return bool(EC_NUMBER_PATTERN.match(ec_number))


def validate_cas_checksum(cas_number: str) -> bool:
    """Validate CAS number checksum.

    The last digit of a CAS number is a checksum digit, calculated
    by taking the rightmost digit times 1, the next times 2, etc.,
    summing the products, and taking modulo 10.

    Args:
        cas_number: CAS number string to validate

    Returns:
        True if checksum is valid

    Examples:
        >>> validate_cas_checksum("50-00-0")  # Formaldehyde
        True
        >>> validate_cas_checksum("50-00-1")  # Invalid checksum
        False
    """
    if not is_valid_cas_number(cas_number):
        return False

    # Remove hyphens and get digits
    digits = cas_number.replace("-", "")

    # Last digit is the check digit
    check_digit = int(digits[-1])

    # Calculate checksum from remaining digits
    checksum = 0
    remaining = digits[:-1]
    for i, digit in enumerate(reversed(remaining)):
        checksum += int(digit) * (i + 1)

    return checksum % 10 == check_digit


# =============================================================================
# Substance Dataclasses
# =============================================================================


@dataclass(frozen=True, slots=True)
class Substance:
    """Substance per Regulation (EC) No 1907/2006 Art 3(1).

    Means a chemical element and its compounds in the natural state or
    obtained by any manufacturing process, including any additive necessary
    to preserve its stability and any impurity deriving from the process used.

    Source: soc_v1.4.7.ttl
    """

    _class_uri: ClassVar[str] = EUDPPSubstanceClass.SUBSTANCE.value

    name_iupac: str | None = None
    name_cas: str | None = None
    other_name: str | None = None


@dataclass(frozen=True, slots=True)
class SubstanceOfConcern(Substance):
    """Substance of concern per ESPR Art 2(28).

    A substance that meets criteria from:
    - REACH Article 57 (SVHC)
    - CLP Regulation hazard classes (carcinogenicity, mutagenicity, etc.)
    - Regulation (EU) 2019/1021 (POPs)
    - Or negatively affects reuse/recycling

    Source: soc_v1.4.7.ttl
    """

    _class_uri: ClassVar[str] = EUDPPSubstanceClass.SUBSTANCE_OF_CONCERN.value

    # Identification per ESPR Art 7(5)
    number_cas: str | None = None
    number_ec: str | None = None
    abbreviation: str | None = None
    trade_name: str | None = None
    usual_name: str | None = None

    # Location & lifecycle per ESPR Art 7(5) / Annex I(f)
    substance_location: str | None = None
    lifecycle_stage: str | None = None

    # Impact per ESPR Annex I(f)
    impact_on_health: str | None = None
    impact_on_environment: str | None = None

    # Hazard classification
    hazard_category: str | None = None

    def validate_identifiers(self) -> list[str]:
        """Validate substance identifiers format.

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        if self.number_cas and not is_valid_cas_number(self.number_cas):
            errors.append(
                f"Invalid CAS number format: {self.number_cas}. "
                f"Expected format: NN-NN-N to NNNNNNN-NN-N"
            )

        if self.number_ec and not is_valid_ec_number(self.number_ec):
            errors.append(f"Invalid EC number format: {self.number_ec}. Expected format: NNN-NNN-N")

        return errors

    def has_valid_identification(self) -> bool:
        """Check if substance has at least one valid identifier.

        Per ESPR Art 7(5), substances should be identifiable by at least
        one of: IUPAC name, CAS name/number, EC number, or other names.

        Returns:
            True if at least one identifier is present
        """
        identifiers = [
            self.name_iupac,
            self.name_cas,
            self.number_cas,
            self.number_ec,
            self.abbreviation,
            self.trade_name,
            self.usual_name,
            self.other_name,
        ]
        return any(id is not None for id in identifiers)


@dataclass(frozen=True, slots=True)
class Concentration:
    """Concentration of substance of concern per ESPR Art 7(5).

    Defines the concentration, maximum concentration, or concentration range
    of substances of concern at the level of the product, its relevant
    components, or spare parts.

    Source: soc_v1.4.7.ttl
    """

    _class_uri: ClassVar[str] = EUDPPSubstanceClass.CONCENTRATION.value

    value: Decimal
    unit: str
    range_min: Decimal | None = None
    range_max: Decimal | None = None

    def is_range(self) -> bool:
        """Check if concentration is specified as a range.

        Returns:
            True if both range_min and range_max are specified
        """
        return self.range_min is not None and self.range_max is not None

    def validate(self) -> list[str]:
        """Validate concentration values.

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        if self.value < 0:
            errors.append(f"Concentration value cannot be negative: {self.value}")

        if self.range_min is not None and self.range_max is not None:
            if self.range_min > self.range_max:
                errors.append(
                    f"Range minimum ({self.range_min}) cannot exceed maximum ({self.range_max})"
                )

            if self.range_min < 0:
                errors.append(f"Range minimum cannot be negative: {self.range_min}")

        return errors


@dataclass(frozen=True, slots=True)
class Threshold:
    """Regulatory threshold for substance of concern per ESPR.

    By default, information on all substances of concern present in a
    product above the relevant thresholds should be included in the DPP.

    Source: soc_v1.4.7.ttl
    """

    _class_uri: ClassVar[str] = EUDPPSubstanceClass.THRESHOLD.value

    value: Decimal
    unit: str
    regulation_reference: str | None = None

    def validate(self) -> list[str]:
        """Validate threshold value.

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        if self.value < 0:
            errors.append(f"Threshold value cannot be negative: {self.value}")

        return errors


@dataclass(frozen=True, slots=True)
class ConcentrationOfSubstanceOfConcern:
    """Combined concentration and threshold for a substance of concern.

    Per ESPR Art 7(5), relates a SubstanceOfConcern to its Concentration
    and optionally its regulatory Threshold.

    This is a convenience class for linking the ontology entities.
    """

    _class_uri: ClassVar[str] = "eudpp:ConcentrationOfSubstanceOfConcern"

    substance: SubstanceOfConcern
    concentration: Concentration
    threshold: Threshold | None = None

    def exceeds_threshold(self) -> bool | None:
        """Check if concentration exceeds the threshold.

        Returns:
            True if exceeds, False if not, None if no threshold specified
        """
        if self.threshold is None:
            return None

        # Compare in same units (assumes units are compatible)
        if self.concentration.unit != self.threshold.unit:
            return None  # Cannot compare different units

        return self.concentration.value > self.threshold.value


# =============================================================================
# Helper Functions
# =============================================================================


def get_all_hazard_categories() -> list[str]:
    """Get all hazard category values.

    Returns:
        List of hazard category strings
    """
    return [cat.value for cat in HazardCategory]


def get_lifecycle_stages() -> list[str]:
    """Get all lifecycle stage values.

    Returns:
        List of lifecycle stage strings
    """
    return [stage.value for stage in LifeCycleStage]


def is_svhc(hazard_category: str) -> bool:
    """Check if hazard category is SVHC (Substances of Very High Concern).

    SVHC are identified per REACH Article 57.

    Args:
        hazard_category: Hazard category value

    Returns:
        True if substance is SVHC
    """
    return hazard_category == HazardCategory.SVHC.value


def is_pop(hazard_category: str) -> bool:
    """Check if hazard category is POP (Persistent Organic Pollutant).

    POPs are regulated under Regulation (EU) 2019/1021.

    Args:
        hazard_category: Hazard category value

    Returns:
        True if substance is POP
    """
    return hazard_category == HazardCategory.POP.value
