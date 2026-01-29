"""Example custom validators for dppvalidator.

These validators implement the SemanticRule protocol and are automatically
discovered via Python entry points when the plugin is installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class BrandNameRule:
    """SEM_BRAND: Products should have a brand name for traceability.

    This example validator checks if products have a brand name specified,
    which is important for consumer identification and traceability.
    """

    rule_id: str = "SEM_BRAND"
    description: str = "Products should have a brand name"
    severity: Literal["error", "warning", "info"] = "warning"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check if product has a brand name.

        Args:
            passport: The Digital Product Passport to validate

        Returns:
            List of (path, message) tuples for each violation
        """
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        product = passport.credential_subject.product
        if product and not product.name:
            violations.append(
                (
                    "$.credentialSubject.product.name",
                    "Product should have a name for better traceability",
                )
            )

        return violations


class MinMaterialsRule:
    """SEM_MINMAT: Products should declare at least 2 materials.

    This example validator encourages comprehensive material disclosure
    by checking if at least 2 materials are declared.
    """

    rule_id: str = "SEM_MINMAT"
    description: str = "Products should declare at least 2 materials"
    severity: Literal["error", "warning", "info"] = "info"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check if product has minimum materials declared.

        Args:
            passport: The Digital Product Passport to validate

        Returns:
            List of (path, message) tuples for each violation
        """
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        materials = passport.credential_subject.materials_provenance
        if materials is not None and len(materials) < 2:
            violations.append(
                (
                    "$.credentialSubject.materialsProvenance",
                    f"Only {len(materials)} material(s) declared. "
                    "Consider adding more for comprehensive disclosure.",
                )
            )

        return violations
