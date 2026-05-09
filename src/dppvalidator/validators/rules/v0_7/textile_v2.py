"""Textile v2 rule pack — MVP Textile DPP v2 (2025-12-04).

Phase 7 task 7.1 of [docs/plans/CIRPASS_2_MIGRATION.md]. The v2 pack
tightens the v1 baseline (in :mod:`textile`) against the MVP
Textile DPP v2 deliverable published 2025-12-04 by the EU CIRPASS-2
textile pilot working group:

- ``TXT001`` (v2): same — HS chapters 50–63 still mandatory.
- ``TXT002`` (v2): mass-fraction sum is now strictly ``== 1.0``
  (v1 was lenient on partial declarations); plus every Material
  carries ``materialType.code`` (v1 only required composition presence).
- ``TXT003`` (v2): synthetic-fibre microplastic disclosure is now
  ``error`` severity (v1 was ``info``); the rule fires whenever a
  synthetic fibre is present *without* a ``microplastic-release``
  performance claim — not just whenever there's no claim at all.
- ``TXT004`` (v2): durability metric required (was ``info``);
  the rule looks for ``performanceClaim`` with
  ``conformityTopic`` containing ``durability``.
- ``TXT005`` (v2): care instructions are now required (was ``info``)
  and must include a non-empty ``mediaType`` — purely linking to a
  resource without declaring its type fails the v2 contract.
- ``TXT006`` (v2, NEW): minimum recycled content disclosure for
  garments. Either a ``Material.recycledMassFraction`` ≥ 0 *or* a
  performance-claim with ``recycled-content`` topic must be present.
- ``TXT007`` (v2, NEW): repair / spare-parts information. ESPR
  Annex II requires a relatedDocument link tagged
  ``relationship=repair-information`` (or ``spare-parts``).

The v2 rule IDs are the same ``TXT0NN`` numerals as v1 — there's
no collision because the validator's profile dispatch picks one or
the other (never both for the same payload). The two rule sets are
*alternatives* keyed on ``--profile textile-v1`` / ``textile-v2``.

Profile dispatch
================

The :data:`TEXTILE_RULES_V0_7_V2` tuple is registered as the
``textile-v2`` validator entry-point in ``pyproject.toml``. The CLI
``validate --profile textile-v2`` flag toggles which pack the
engine loads. Default profile is ``textile-v1`` (the legacy
:data:`dppvalidator.validators.rules.v0_7.TEXTILE_RULES_V0_7` pack)
for back-compat with pre-Phase-7 callers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from dppvalidator.validators.rules.v0_6.textile import TEXTILE_HS_CHAPTERS

if TYPE_CHECKING:
    from dppvalidator.models.v0_7.envelope import DigitalProductPassport


__all__ = [
    "TEXTILE_RULES_V0_7_V2",
    "TextileV2CareInstructionsRule",
    "TextileV2DurabilityRule",
    "TextileV2HSCodeRule",
    "TextileV2MaterialCompositionRule",
    "TextileV2MicroplasticRule",
    "TextileV2RecycledContentRule",
    "TextileV2RepairInfoRule",
    "is_textile_product_v2",
]


# Synthetic fibres that trigger TXT003 (v2): the MVP Textile DPP v2
# expanded the list to include the bio-based / regenerated cellulosic
# fibres that JRC's preparatory study flagged as microplastic-shedding
# under wet conditions.
_SYNTHETIC_FIBERS_V2 = frozenset(
    [
        "POLYESTER",
        "PL",
        "PET",
        "NYLON",
        "PA",
        "ACRYLIC",
        "PC",
        "ELASTANE",
        "EL",
        "POLYPROPYLENE",
        "PP",
        # New in v2: regenerated / bio-synthetic fibres that the JRC
        # preparatory study identified as microplastic-shedding.
        "VISCOSE",
        "CV",
        "MODAL",
        "CMD",
        "LYOCELL",
        "CLY",
    ]
)


def _topic_contains(claim: object, needle: str) -> bool:
    """True when one of ``claim.conformity_topic[*].name`` contains ``needle``.

    The v0.7 ``Claim.conformityTopic`` is a list of structured
    topic descriptors. The v2 rules pattern-match the topic name
    by substring (case-insensitive) so authors can still use
    ``"durability"``, ``"durability-metric"``, etc. without breaking.
    """
    topics = getattr(claim, "conformity_topic", None) or []
    needle_lower = needle.lower()
    for topic in topics:
        name = (getattr(topic, "name", "") or "").lower()
        ident = (getattr(topic, "id", "") or "").lower()
        if needle_lower in name or needle_lower in ident:
            return True
    return False


# =============================================================================
# TXT001 (v2) — HS code (same as v1, kept here for self-contained registration)
# =============================================================================


class TextileV2HSCodeRule:
    """TXT001 (v2): textile product must have valid HS code.

    Identical to v1's :class:`TextileHSCodeRule`; restated here so
    the v2 pack is a self-contained tuple that can be registered as
    its own entry-point.
    """

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
                    "Textile HS code (chapters 50-63) not found in productCategory",
                )
            )
        return violations


# =============================================================================
# TXT002 (v2) — Material composition is now stricter
# =============================================================================


class TextileV2MaterialCompositionRule:
    """TXT002 (v2): material composition is fully declared.

    Tighter than v1: every Material must carry both ``massFraction``
    *and* ``materialType.code``. The mass-fraction sum is checked
    against 1.0 with a ±0.005 tolerance (was ±0.01 in v1).
    """

    rule_id: str = "TXT002"
    description: str = "Textile material composition must be fully declared (v2)"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Each Material must carry massFraction and materialType.code; the "
        "sum of massFraction across all materials must equal 1.0 (±0.005)."
    )
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
        # Per-material checks
        total = 0.0
        for i, material in enumerate(materials):
            mt = getattr(material, "material_type", None)
            code = getattr(mt, "code", None) if mt else None
            if not code:
                violations.append(
                    (
                        f"$.credentialSubject.materialProvenance[{i}].materialType.code",
                        "Textile Material is missing materialType.code (v2 requires "
                        "an explicit fibre code).",
                    )
                )
            mass_fraction = material.mass_fraction
            if mass_fraction is None:
                violations.append(
                    (
                        f"$.credentialSubject.materialProvenance[{i}].massFraction",
                        "Textile Material is missing massFraction (v2 requires every "
                        "fibre's contribution to be declared).",
                    )
                )
            else:
                total += float(mass_fraction)
        # Sum check (only when every entry contributed)
        if all(m.mass_fraction is not None for m in materials) and abs(total - 1.0) > 0.005:
            violations.append(
                (
                    "$.credentialSubject.materialProvenance",
                    f"Mass-fraction sum is {total:.4f}; v2 requires the sum to "
                    "equal 1.0 within ±0.005.",
                )
            )
        return violations


# =============================================================================
# TXT003 (v2) — Microplastic disclosure is now an error
# =============================================================================


class TextileV2MicroplasticRule:
    """TXT003 (v2): synthetic textiles must declare microplastic release.

    Promoted from ``info`` to ``error``. The rule fires whenever a
    synthetic fibre is present and the passport carries no
    performanceClaim with a ``microplastic-release`` /
    ``microplastic`` topic.
    """

    rule_id: str = "TXT003"
    description: str = "Synthetic textiles must declare microplastic-release data (v2)"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Add a performanceClaim entry with conformityTopic containing "
        "'microplastic-release' or 'microplastic' for synthetic-fibre garments."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT003"

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
            mt = getattr(material, "material_type", None)
            code = (getattr(mt, "code", None) or "").upper() if mt else ""
            if any(fiber in name for fiber in _SYNTHETIC_FIBERS_V2) or (
                code in _SYNTHETIC_FIBERS_V2
            ):
                has_synthetic = True
                break
        if not has_synthetic:
            return violations
        claims = getattr(product, "performance_claim", []) or []
        if any(_topic_contains(c, "microplastic") for c in claims):
            return violations
        violations.append(
            (
                "$.credentialSubject.performanceClaim",
                "Synthetic textile product missing microplastic-release performance "
                "claim (v2: required per JRC preparatory study; promoted to error).",
            )
        )
        return violations


# =============================================================================
# TXT004 (v2) — Durability metric required
# =============================================================================


class TextileV2DurabilityRule:
    """TXT004 (v2): textile products must declare durability metrics.

    v1 was a soft ``info``-level suggestion to populate
    ``Product.characteristics``; v2 requires a structured
    ``performanceClaim`` whose ``conformityTopic`` contains
    ``durability``.
    """

    rule_id: str = "TXT004"
    description: str = "Textile must declare durability performance claim (v2)"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Add a performanceClaim entry with conformityTopic containing "
        "'durability' (e.g. abrasion resistance, pilling resistance)."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT004"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations
        claims = getattr(product, "performance_claim", []) or []
        if any(_topic_contains(c, "durability") for c in claims):
            return violations
        violations.append(
            (
                "$.credentialSubject.performanceClaim",
                "Textile product missing durability performance claim (v2: required "
                "per ESPR Annex I).",
            )
        )
        return violations


# =============================================================================
# TXT005 (v2) — Care instructions required + mediaType
# =============================================================================


class TextileV2CareInstructionsRule:
    """TXT005 (v2): care-instruction relatedDocument required.

    v1 was an ``info`` hint; v2 makes it a hard requirement and
    additionally requires the linked document to declare a
    ``mediaType`` (so consumers can decide how to render it).
    """

    rule_id: str = "TXT005"
    description: str = "Textile must declare care-instruction document with mediaType (v2)"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Add a relatedDocument entry with a non-empty mediaType (e.g. "
        "application/pdf) linking to the care-instruction sheet."
    )
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
                    "Textile product missing relatedDocument with care instructions "
                    "(v2: required).",
                )
            )
            return violations
        if not any(getattr(doc, "media_type", None) for doc in documents):
            violations.append(
                (
                    "$.credentialSubject.relatedDocument",
                    "Textile relatedDocument entries are all missing mediaType (v2: "
                    "consumers need to know how to render the linked resource).",
                )
            )
        return violations


# =============================================================================
# TXT006 (v2, NEW) — Recycled content disclosure
# =============================================================================


class TextileV2RecycledContentRule:
    """TXT006 (v2, NEW): recycled-content disclosure for garments.

    Either:
    - At least one Material declares ``recycledMassFraction`` (any
      value, including ``0``), OR
    - A ``performanceClaim`` declares a ``recycled-content`` topic.

    v2 wants the producer to make an *explicit* statement (zero is
    fine; silence is not).
    """

    rule_id: str = "TXT006"
    description: str = "Textile must disclose recycled-content data (v2 — new)"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Either populate Material.recycledMassFraction on at least one "
        "fibre, or add a performanceClaim with conformityTopic containing "
        "'recycled-content'."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT006"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations
        materials = getattr(product, "material_provenance", []) or []
        if any(getattr(m, "recycled_mass_fraction", None) is not None for m in materials):
            return violations
        claims = getattr(product, "performance_claim", []) or []
        if any(_topic_contains(c, "recycled") for c in claims):
            return violations
        violations.append(
            (
                "$.credentialSubject",
                "Textile product missing recycled-content disclosure (v2 — new).",
            )
        )
        return violations


# =============================================================================
# TXT007 (v2, NEW) — Repair / spare-parts information
# =============================================================================


class TextileV2RepairInfoRule:
    """TXT007 (v2, NEW): repair / spare-parts information.

    ESPR Annex II requires a repair-information surface for
    garments. The rule fires when no ``relatedDocument`` carries a
    ``relationship`` containing ``repair`` or ``spare-parts``.
    """

    rule_id: str = "TXT007"
    description: str = "Textile must declare repair / spare-parts information (v2 — new)"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = (
        "Add a relatedDocument entry with relationship='repair-information' "
        "(or 'spare-parts') linking to the repair guide."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TXT007"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations
        documents = getattr(product, "related_document", []) or []
        for doc in documents:
            rel = (getattr(doc, "relationship", "") or "").lower()
            if "repair" in rel or "spare-parts" in rel or "spare_parts" in rel:
                return violations
        violations.append(
            (
                "$.credentialSubject.relatedDocument",
                "Textile product missing repair / spare-parts relatedDocument "
                "(v2 — new; ESPR Annex II).",
            )
        )
        return violations


# =============================================================================
# Public dispatch
# =============================================================================


TEXTILE_RULES_V0_7_V2: tuple[object, ...] = (
    TextileV2HSCodeRule(),
    TextileV2MaterialCompositionRule(),
    TextileV2MicroplasticRule(),
    TextileV2DurabilityRule(),
    TextileV2CareInstructionsRule(),
    TextileV2RecycledContentRule(),
    TextileV2RepairInfoRule(),
)


def is_textile_product_v2(passport: DigitalProductPassport) -> bool:
    """Same heuristic as v1 ``is_textile_product``; re-exported for v2 callers.

    The textile-vs-non-textile decision is purely structural (HS
    chapter 50-63 lookup) and doesn't change between v1 and v2.
    """
    product = passport.credential_subject
    if product is None:
        return False
    for classification in getattr(product, "product_category", []) or []:
        code = (getattr(classification, "code", None) or "").replace(".", "").replace(" ", "")
        if len(code) >= 2 and code[:2] in TEXTILE_HS_CHAPTERS:
            return True
    return False
