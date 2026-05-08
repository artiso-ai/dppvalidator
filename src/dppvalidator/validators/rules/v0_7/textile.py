"""Textile sector rules adapted for the UNTP v0.7.0 envelope.

Same TXT-coded rules as :mod:`dppvalidator.validators.rules.v0_6.textile`,
walking the v0.7 shape:

- ``credentialSubject`` is the :class:`Product` directly (no
  ``credentialSubject.product`` traversal).
- ``materialsProvenance`` → ``materialProvenance`` (singular).
- ``furtherInformation`` (v0.6 ``Product.furtherInformation: Link``) is
  replaced by ``relatedDocument: list[Link]`` (v0.7 absorbs both
  ``furtherInformation`` and ``dueDiligenceDeclaration`` into this array).
- The two scorecard classes (``circularityScorecard``, ``emissionsScorecard``)
  are gone; the microplastic-data presence check now looks at
  ``performanceClaim`` instead.

The shared helpers — :class:`TextileEnvironmentalCategory`,
``TEXTILE_HS_CHAPTERS``, ``TEXTILE_MATERIAL_CODES`` — are imported from the
v0.6 module so they live in one place. They're version-neutral data tables.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from dppvalidator.validators.rules.v0_6.textile import (
    TEXTILE_HS_CHAPTERS,
    TextileEnvironmentalCategory,  # re-export — version-neutral enum
)

if TYPE_CHECKING:
    from dppvalidator.models.v0_7.envelope import DigitalProductPassport


__all__ = [
    "TEXTILE_HS_CHAPTERS",
    "TEXTILE_RULES_V0_7",
    "TextileCareInstructionsRule",
    "TextileDurabilityRule",
    "TextileEnvironmentalCategory",
    "TextileHSCodeRule",
    "TextileMaterialCompositionRule",
    "TextileMicroplasticRule",
    "is_textile_product",
]


class TextileHSCodeRule:
    """TXT001 (v0.7): textile product must have valid HS code."""

    rule_id: str = "TXT001"
    description: str = "Textile product must have valid HS code (chapters 50-63)"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Add product category with HS code in chapters 50-63"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT001"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        categories = getattr(product, "product_category", []) or []
        if not categories:
            violations.append(
                (
                    "$.credentialSubject.productCategory",
                    "Textile product missing product category with HS code",
                )
            )
            return violations

        has_textile_hs = False
        for classification in categories:
            code = getattr(classification, "code", None) or ""
            stripped = code.replace(".", "").replace(" ", "")
            if len(stripped) >= 2 and stripped[:2] in TEXTILE_HS_CHAPTERS:
                has_textile_hs = True
                break

        if not has_textile_hs:
            violations.append(
                (
                    "$.credentialSubject.productCategory",
                    "No textile HS code found (chapters 50-63 required)",
                )
            )
        return violations


class TextileMaterialCompositionRule:
    """TXT002 (v0.7): textile must declare material composition."""

    rule_id: str = "TXT002"
    description: str = "Textile must declare material composition"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add materialProvenance with fiber types and mass fractions"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT002"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        materials = getattr(product, "material_provenance", []) or []
        if not materials:
            violations.append(
                (
                    "$.credentialSubject.materialProvenance",
                    "Textile product missing material composition declaration",
                )
            )
            return violations

        if not any(m.mass_fraction is not None for m in materials):
            violations.append(
                (
                    "$.credentialSubject.materialProvenance",
                    "Textile materials missing mass fraction (fiber %) declaration",
                )
            )
        return violations


class TextileMicroplasticRule:
    """TXT003 (v0.7): synthetic textiles should declare microplastic release.

    v0.7 has no scorecard classes; the heuristic for "did the producer
    declare environmental data?" is now "is there at least one
    performanceClaim?". This is a deliberate softening — Phase 5/Phase 7
    can refine this when the topic taxonomy is settled.
    """

    rule_id: str = "TXT003"
    description: str = "Synthetic textiles should declare microplastic release"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = "Add microplastic release data for synthetic fiber products"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT003"

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
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        materials = getattr(product, "material_provenance", []) or []
        if not materials:
            return violations

        has_synthetic = False
        for material in materials:
            name = (material.name or "").upper()
            if any(fiber in name for fiber in self.SYNTHETIC_FIBERS):
                has_synthetic = True
                break
            mt = getattr(material, "material_type", None)
            code = (getattr(mt, "code", None) or "").upper() if mt else ""
            if code in self.SYNTHETIC_FIBERS:
                has_synthetic = True
                break

        if not has_synthetic:
            return violations

        # In v0.7 the "is there environmental data?" heuristic is the
        # presence of any performanceClaim entry. If there's nothing, hint
        # at adding microplastic data.
        claims = getattr(product, "performance_claim", []) or []
        if not claims:
            violations.append(
                (
                    "$.credentialSubject",
                    "Synthetic textile product - consider adding microplastic "
                    "release data per JRC preparatory study",
                )
            )
        return violations


class TextileDurabilityRule:
    """TXT004 (v0.7): textile products should have durability information."""

    rule_id: str = "TXT004"
    description: str = "Textile should declare durability information"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = "Add product characteristics with durability data"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT004"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        if not getattr(product, "characteristics", None):
            violations.append(
                (
                    "$.credentialSubject.characteristics",
                    "Textile product - consider adding durability characteristics "
                    "per ESPR Annex I requirements",
                )
            )
        return violations


class TextileCareInstructionsRule:
    """TXT005 (v0.7): textile products should have care instructions.

    v0.7 absorbs the v0.6 ``furtherInformation`` field into
    ``relatedDocument: list[Link]``. The check now succeeds when at least
    one link is present in ``relatedDocument``.
    """

    rule_id: str = "TXT005"
    description: str = "Textile should have care instructions"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = "Add a relatedDocument link with care instructions"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT005"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        documents = getattr(product, "related_document", []) or []
        if not documents:
            violations.append(
                (
                    "$.credentialSubject.relatedDocument",
                    "Textile product - consider adding care instructions link",
                )
            )
        return violations


TEXTILE_RULES_V0_7 = [
    TextileHSCodeRule(),
    TextileMaterialCompositionRule(),
    TextileMicroplasticRule(),
    TextileDurabilityRule(),
    TextileCareInstructionsRule(),
]


def is_textile_product(passport: DigitalProductPassport) -> bool:
    """Return True when the v0.7 DPP describes a textile product.

    Mirrors the v0.6 helper, but walks the new envelope shape
    (``passport.credential_subject.product_category`` instead of
    ``passport.credential_subject.product.product_category``).
    """
    product = passport.credential_subject
    if product is None:
        return False

    for classification in getattr(product, "product_category", []) or []:
        code = (getattr(classification, "code", None) or "").replace(".", "").replace(" ", "")
        if len(code) >= 2 and code[:2] in TEXTILE_HS_CHAPTERS:
            return True

    return False
