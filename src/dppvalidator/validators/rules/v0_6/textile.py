"""CIRPASS-2 textile sector validation rules.

Source: DPP Granularity Options for Textiles/Apparel
DOI: 10.5281/zenodo.17582219

These rules implement textile-specific validation based on CIRPASS-2
granularity analysis and JRC preparatory study environmental categories.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class TextileEnvironmentalCategory(str, Enum):
    """Environmental impact categories for textiles per JRC preparatory study."""

    WATER_CONSUMPTION = "water_consumption"
    ENERGY_CONSUMPTION = "energy_consumption"
    CHEMICAL_SUBSTANCES = "chemical_substances"
    TEXTILE_WASTE = "textile_waste"
    GHG_EMISSIONS = "ghg_emissions"
    MICROPLASTIC_RELEASE = "microplastic_release"
    POLLUTION = "pollution"  # COD/NOx/SOx


# HS code chapters for textiles (50-63)
TEXTILE_HS_CHAPTERS = frozenset(str(i) for i in range(50, 64))

# Textile fiber material codes (UNECE Rec 46 subset)
TEXTILE_MATERIAL_CODES = frozenset(
    [
        "COTTON",
        "CO",
        "WOOL",
        "WO",
        "SILK",
        "SE",
        "LINEN",
        "LI",
        "POLYESTER",
        "PL",
        "NYLON",
        "PA",
        "ACRYLIC",
        "PC",
        "VISCOSE",
        "VI",
        "ELASTANE",
        "EL",
        "MODAL",
        "MD",
        "LYOCELL",
        "CLY",
        "HEMP",
        "HA",
        "JUTE",
        "JU",
        "RAMIE",
        "RA",
        "CASHMERE",
        "WS",
        "ALPACA",
        "WP",
        "MOHAIR",
        "WM",
        "ANGORA",
        "WA",
    ]
)


class TextileHSCodeRule:
    """TXT001: Product must have valid textile HS code.

    Validates that textile products have HS codes in chapters 50-63.
    """

    rule_id: str = "TXT001"
    description: str = "Textile product must have valid HS code (chapters 50-63)"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Add product category with HS code in chapters 50-63"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT001"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check textile product has valid HS code."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        product = passport.credential_subject.product
        if not product:
            return violations

        # Check product category for HS codes
        if not product.product_category:
            violations.append(
                (
                    "$.credentialSubject.product.productCategory",
                    "Textile product missing product category with HS code",
                )
            )
            return violations

        has_textile_hs = False
        for classification in product.product_category:
            if classification.code:
                code = classification.code.replace(".", "").replace(" ", "")
                if len(code) >= 2 and code[:2] in TEXTILE_HS_CHAPTERS:
                    has_textile_hs = True
                    break

        if not has_textile_hs:
            violations.append(
                (
                    "$.credentialSubject.product.productCategory",
                    "No textile HS code found (chapters 50-63 required)",
                )
            )

        return violations


class TextileMaterialCompositionRule:
    """TXT002: Textile must declare material composition.

    Per ESPR requirements, textile products must declare fiber composition.
    """

    rule_id: str = "TXT002"
    description: str = "Textile must declare material composition"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add materialsProvenance with fiber types and mass fractions"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT002"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check textile has material composition."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        materials = passport.credential_subject.materials_provenance
        if not materials:
            violations.append(
                (
                    "$.credentialSubject.materialsProvenance",
                    "Textile product missing material composition declaration",
                )
            )
            return violations

        # Check at least one material has mass fraction
        has_fraction = False
        for material in materials:
            if material.mass_fraction is not None:
                has_fraction = True
                break

        if not has_fraction:
            violations.append(
                (
                    "$.credentialSubject.materialsProvenance",
                    "Textile materials missing mass fraction (fiber %) declaration",
                )
            )

        return violations


class TextileMicroplasticRule:
    """TXT003: Synthetic textiles should declare microplastic release.

    Per JRC preparatory study, synthetic fiber products should declare
    microplastic release potential.
    """

    rule_id: str = "TXT003"
    description: str = "Synthetic textiles should declare microplastic release"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = "Add microplastic release data for synthetic fiber products"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT003"

    # Synthetic fiber codes that may release microplastics
    SYNTHETIC_FIBERS = frozenset(
        [
            "POLYESTER",
            "PL",
            "NYLON",
            "PA",
            "ACRYLIC",
            "PC",
            "ELASTANE",
            "EL",
            "POLYPROPYLENE",
            "PP",
        ]
    )

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check synthetic textile declares microplastic release."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        materials = passport.credential_subject.materials_provenance
        if not materials:
            return violations

        # Check if product contains synthetic fibers
        has_synthetic = False
        for material in materials:
            if material.name:
                name_upper = material.name.upper()
                if any(fiber in name_upper for fiber in self.SYNTHETIC_FIBERS):
                    has_synthetic = True
                    break
            if material.material_type and material.material_type.code:
                code_upper = material.material_type.code.upper()
                if code_upper in self.SYNTHETIC_FIBERS:
                    has_synthetic = True
                    break

        if not has_synthetic:
            return violations

        # Check for environmental footprint data
        scorecard = passport.credential_subject.circularity_scorecard
        emissions = passport.credential_subject.emissions_scorecard

        # If synthetic but no environmental data, suggest microplastic info
        if not scorecard and not emissions:
            violations.append(
                (
                    "$.credentialSubject",
                    "Synthetic textile product - consider adding microplastic "
                    "release data per JRC preparatory study",
                )
            )

        return violations


class TextileDurabilityRule:
    """TXT004: Textile products should have durability information.

    Per ESPR Annex I, durability is a key product parameter for textiles.
    """

    rule_id: str = "TXT004"
    description: str = "Textile should declare durability information"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = "Add product characteristics with durability data"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT004"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check textile has durability information."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        product = passport.credential_subject.product
        if not product:
            return violations

        # Check for characteristics (where durability info would be)
        if not product.characteristics:
            violations.append(
                (
                    "$.credentialSubject.product.characteristics",
                    "Textile product - consider adding durability characteristics "
                    "per ESPR Annex I requirements",
                )
            )

        return violations


class TextileCareInstructionsRule:
    """TXT005: Textile products should have care instructions.

    Care instructions are required for consumer textiles per EU labeling
    requirements and extend product lifetime.
    """

    rule_id: str = "TXT005"
    description: str = "Textile should have care instructions"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = "Add furtherInformation link to care instructions"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT005"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check textile has care instructions."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        product = passport.credential_subject.product
        if not product:
            return violations

        # Check for further information links
        if not product.further_information:
            violations.append(
                (
                    "$.credentialSubject.product.furtherInformation",
                    "Textile product - consider adding care instructions link",
                )
            )

        return violations


# List of all textile rules for easy registration
TEXTILE_RULES = [
    TextileHSCodeRule(),
    TextileMaterialCompositionRule(),
    TextileMicroplasticRule(),
    TextileDurabilityRule(),
    TextileCareInstructionsRule(),
]


def is_textile_product(passport: DigitalProductPassport) -> bool:
    """Check if a passport represents a textile product.

    Args:
        passport: Digital Product Passport to check

    Returns:
        True if product has textile HS code (chapters 50-63)
    """
    if not passport.credential_subject:
        return False

    product = passport.credential_subject.product
    if not product or not product.product_category:
        return False

    for classification in product.product_category:
        if classification.code:
            code = classification.code.replace(".", "").replace(" ", "")
            if len(code) >= 2 and code[:2] in TEXTILE_HS_CHAPTERS:
                return True

    return False


def get_textile_environmental_categories() -> list[str]:
    """Get list of textile environmental impact categories."""
    return [cat.value for cat in TextileEnvironmentalCategory]
