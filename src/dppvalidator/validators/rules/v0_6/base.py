"""Semantic validation rule implementations."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from dppvalidator.vocabularies.code_lists import (
    is_valid_hs_code as _is_valid_hs_code,
)
from dppvalidator.vocabularies.code_lists import (
    is_valid_material_code as _is_valid_material_code,
)
from dppvalidator.vocabularies.code_lists import (
    validate_gtin as _validate_gtin,
)

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class MassFractionSumRule:
    """SEM001: Material mass fractions should sum to 1.0.

    Per UNTP spec, partial declarations (sum < 1.0) are valid but should
    be flagged as a warning. Only sum > 1.0 is physically impossible.
    """

    rule_id: str = "SEM001"
    description: str = "Material mass fractions should sum to 1.0"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Adjust material mass fractions to sum to 1.0 (100%)"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM001"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check mass fraction sum."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        materials = passport.credential_subject.materials_provenance
        if not materials:
            return violations

        fractions = [m.mass_fraction for m in materials if m.mass_fraction is not None]
        if fractions:
            total = sum(fractions)
            # Only flag if significantly different from 1.0
            # Partial declarations (< 1.0) are valid per UNTP spec
            if abs(total - 1.0) > 0.01:
                violations.append(
                    (
                        "$.credentialSubject.materialsProvenance",
                        f"Mass fractions sum to {total:.3f}, expected 1.0 (partial declaration)",
                    )
                )

        return violations


class ValidityDateRule:
    """SEM002: validFrom must be before validUntil."""

    rule_id: str = "SEM002"
    description: str = "validFrom must be before validUntil"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Ensure validFrom is before validUntil"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM002"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check validity date ordering."""
        violations: list[tuple[str, str]] = []

        if (
            passport.valid_from
            and passport.valid_until
            and passport.valid_from >= passport.valid_until
        ):
            violations.append(
                (
                    "$.validFrom",
                    f"validFrom ({passport.valid_from}) must be before validUntil ({passport.valid_until})",
                )
            )

        return violations


class HazardousMaterialRule:
    """SEM003: hazardous=true requires materialSafetyInformation."""

    rule_id: str = "SEM003"
    description: str = "Hazardous materials require safety information"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add materialSafetyInformation for hazardous materials"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM003"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check hazardous material safety info."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        materials = passport.credential_subject.materials_provenance
        if not materials:
            return violations

        for i, material in enumerate(materials):
            if material.hazardous and not material.material_safety_information:
                violations.append(
                    (
                        f"$.credentialSubject.materialsProvenance[{i}]",
                        f"Material '{material.name}' is hazardous but missing materialSafetyInformation",
                    )
                )

        return violations


class CircularityContentRule:
    """SEM004: recycledContent should not exceed recyclableContent."""

    rule_id: str = "SEM004"
    description: str = "recycledContent should not exceed recyclableContent"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "recycledContent cannot exceed recyclableContent"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM004"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check circularity content consistency."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        scorecard = passport.credential_subject.circularity_scorecard
        if not scorecard:
            return violations

        recycled = scorecard.recycled_content
        recyclable = scorecard.recyclable_content

        if recycled is not None and recyclable is not None and recycled > recyclable:
            violations.append(
                (
                    "$.credentialSubject.circularityScorecard",
                    f"recycledContent ({recycled}) exceeds recyclableContent ({recyclable})",
                )
            )

        return violations


class ConformityClaimRule:
    """SEM005: At least one conformityClaim is recommended."""

    rule_id: str = "SEM005"
    description: str = "At least one conformityClaim is recommended"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = "Add conformity claims for sustainability or compliance"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM005"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check for conformity claims."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        claims = passport.credential_subject.conformity_claim
        if not claims:
            violations.append(
                (
                    "$.credentialSubject.conformityClaim",
                    "No conformity claims present. Consider adding sustainability or compliance claims.",
                )
            )

        return violations


class GranularitySerialNumberRule:
    """SEM006: granularityLevel=item requires serialNumber."""

    rule_id: str = "SEM006"
    description: str = "Item-level passports require serial numbers"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Add serialNumber for item-level granularity passports"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM006"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check serial number for item-level passports."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        granularity = passport.credential_subject.granularity_level
        product = passport.credential_subject.product

        if (
            granularity
            and str(granularity) == "item"
            and (not product or not product.serial_number)
        ):
            violations.append(
                (
                    "$.credentialSubject.product.serialNumber",
                    "granularityLevel is 'item' but serialNumber is missing",
                )
            )

        return violations


class OperationalScopeRule:
    """SEM007: carbonFootprint should have operationalScope defined."""

    rule_id: str = "SEM007"
    description: str = "Emissions data should specify operational scope"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Specify operationalScope with carbonFootprint data"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM007"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check operational scope for emissions data."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        scorecard = passport.credential_subject.emissions_scorecard
        if not scorecard:
            return violations

        if scorecard.carbon_footprint and not scorecard.operational_scope:
            violations.append(
                (
                    "$.credentialSubject.emissionsScorecard.operationalScope",
                    "carbonFootprint is specified but operationalScope is missing",
                )
            )

        return violations


class MaterialCodeRule:
    """VOC003: Material code must be valid per UNECE Rec 46.

    Validates material codes in materialsProvenance against the
    UNECE Recommendation 46 material classification codes.
    """

    rule_id: str = "VOC003"
    description: str = "Material code must be in UNECE Rec 46"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Use a valid UNECE Rec 46 material code"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/VOC003"

    def __init__(
        self,
        material_validator: Callable[[str], bool] | None = None,
    ) -> None:
        """Initialize with optional custom validator."""
        self._is_valid_material_code = material_validator or _is_valid_material_code

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check material codes against UNECE Rec 46."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        materials = passport.credential_subject.materials_provenance
        if not materials:
            return violations

        for i, material in enumerate(materials):
            # Check material_type.code if present
            if material.material_type and material.material_type.code:
                code = material.material_type.code
                if not self._is_valid_material_code(code):
                    violations.append(
                        (
                            f"$.credentialSubject.materialsProvenance[{i}].materialType.code",
                            f"Invalid material code '{code}' - not found in UNECE Rec 46",
                        )
                    )

        return violations


class HSCodeRule:
    """VOC004: HS code must be valid for product category.

    Validates HS codes in product information against the
    Harmonized System textile chapters (50-63).
    """

    rule_id: str = "VOC004"
    description: str = "HS code must be valid for product category"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Use a valid HS code for textiles (chapters 50-63)"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/VOC004"

    def __init__(
        self,
        hs_validator: Callable[[str], bool] | None = None,
    ) -> None:
        """Initialize with optional custom validator."""
        self._is_valid_hs_code = hs_validator or _is_valid_hs_code

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check HS codes for validity."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        product = passport.credential_subject.product
        if not product:
            return violations

        # Check product category classifications for HS codes
        if product.product_category:
            for i, classification in enumerate(product.product_category):
                code = classification.code if classification.code else ""
                # Only validate if it looks like an HS code (4+ digits)
                if code.isdigit() and len(code) >= 4 and not self._is_valid_hs_code(code):
                    violations.append(
                        (
                            f"$.credentialSubject.product.productCategory[{i}].code",
                            f"Invalid HS code '{code}' - not found in textile chapters (50-63)",
                        )
                    )

        return violations


class GTINChecksumRule:
    """VOC005: GTIN must have valid check digit.

    Validates GTIN (Global Trade Item Number) checksums in product
    identifiers using the GS1 check digit algorithm.
    """

    rule_id: str = "VOC005"
    description: str = "GTIN must have valid check digit"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Verify the GTIN check digit using GS1 algorithm"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/VOC005"

    def __init__(
        self,
        gtin_validator: Callable[[str], bool] | None = None,
    ) -> None:
        """Initialize with optional custom validator."""
        self._validate_gtin = gtin_validator or _validate_gtin

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check GTIN checksums."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        product = passport.credential_subject.product
        if not product:
            return violations

        # Check product ID if it looks like a GTIN
        if product.id:
            product_id = product.id
            # Extract GTIN from GS1 Digital Link or plain number
            if "/01/" in product_id:
                match = re.search(r"/01/(\d{8,14})", product_id)
                if match:
                    gtin = match.group(1)
                    if not self._validate_gtin(gtin):
                        violations.append(
                            (
                                "$.credentialSubject.product.id",
                                f"Invalid GTIN checksum in '{gtin}'",
                            )
                        )
            elif product_id.isdigit() and len(product_id) in (8, 12, 13, 14):
                if not self._validate_gtin(product_id):
                    violations.append(
                        (
                            "$.credentialSubject.product.id",
                            f"Invalid GTIN checksum in '{product_id}'",
                        )
                    )

        return violations
