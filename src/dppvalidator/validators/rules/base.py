"""Semantic validation rule implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

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
