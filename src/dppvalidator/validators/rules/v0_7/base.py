"""Base UNTP semantic rules adapted for the v0.7.0 model shape.

The rules carry the same SEM/VOC error codes as their v0.6.x counterparts in
:mod:`dppvalidator.validators.rules.v0_6.base`, but they walk the new
v0.7.0 envelope: ``credentialSubject`` is :class:`Product` directly (no
``ProductPassport`` wrapper), ``materialProvenance`` is the singular noun,
and the three v0.6 scorecard classes are folded into
``performanceClaim: list[Claim]`` keyed by ``conformityTopic``.

Rules dropped (not in :data:`ALL_RULES_V0_7`):

- ``OperationalScopeRule`` (SEM007). v0.7 doesn't expose
  ``EmissionsPerformance.operationalScope`` because the
  ``EmissionsPerformance`` class itself is gone. The plan §Phase 3b says
  to drop with a deprecation note rather than retro-fitting onto a
  metadata claim — see :data:`DROPPED_RULES_V0_6_TO_V0_7`.

Rules ported:

- ``MassFractionSumRule`` (SEM001) — walks ``credential_subject.material_provenance``.
- ``ValidityDateRule`` (SEM002) — same envelope shape; defensive duplicate
  of the model-level ``_validate_validity_window`` invariant.
- ``HazardousMaterialRule`` (SEM003) — walks ``material_provenance``.
- ``CircularityContentRule`` (SEM004) — walks ``performance_claim`` filtered
  by ``conformityTopic.name == "circularity"`` and reads from
  ``claimedPerformance[*].measure`` / ``score``.
- ``ConformityClaimRule`` (SEM005) — walks ``performance_claim``.
- ``GranularitySerialNumberRule`` (SEM006) — defensive duplicate of the
  model-level ``_granularity_implies_serial_or_batch`` invariant; covers
  ``id_granularity == 'item'`` ↔ ``item_number`` and the new
  ``id_granularity == 'batch'`` ↔ ``batch_number`` rule from v0.7.
- ``MaterialCodeRule`` (VOC003) — walks ``material_provenance[*].material_type.code``.
- ``HSCodeRule`` (VOC004) — walks ``credential_subject.product_category[*].code``.
- ``GTINChecksumRule`` (VOC005) — walks ``credential_subject.id``.
"""

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
    from dppvalidator.models.v0_7.claims import Claim
    from dppvalidator.models.v0_7.envelope import DigitalProductPassport

# A note for callers building rule sets manually: these rules don't apply to
# v0.7 because the underlying field/class no longer exists. Phase 3b §Plan
# §3.2 captures the rationale.
DROPPED_RULES_V0_6_TO_V0_7: dict[str, str] = {
    "SEM007": (
        "OperationalScopeRule was tied to v0.6 EmissionsPerformance.operational_scope. "
        "v0.7.0 folds emissions data into Claim.claimedPerformance keyed by "
        "ConformityTopic, so there's no longer a discrete operationalScope field "
        "to validate. Drop the rule rather than retro-fitting."
    ),
}


def _circularity_topic(claim: Claim) -> bool:
    """True when the claim's conformityTopic includes ``"circularity"``.

    Loose match: the schema's ConformityTopic.name field is free-form,
    so we check both the topic name and the topic ID for the substring
    ``"circularity"`` (case-insensitive). Falls back to ``False`` if the
    claim has no conformityTopic entries.
    """
    topics = getattr(claim, "conformity_topic", None) or []
    for t in topics:
        name = (getattr(t, "name", "") or "").lower()
        ident = (getattr(t, "id", "") or "").lower()
        if "circularity" in name or "circularity" in ident:
            return True
    return False


class MassFractionSumRule:
    """SEM001 (v0.7): material mass-fractions should sum to 1.0.

    The model-level ``Product._mass_fractions_sum_within_unity`` invariant
    catches sums *above* 1.0 (which are physically impossible). This
    semantic rule warns on partial declarations (sum < 1.0) so the user is
    aware their material list is incomplete.
    """

    rule_id: str = "SEM001"
    description: str = "Material mass fractions should sum to 1.0"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Adjust material mass fractions to sum to 1.0 (100%)"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM001"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        materials = getattr(product, "material_provenance", []) or []
        if not materials:
            return violations

        fractions = [m.mass_fraction for m in materials if m.mass_fraction is not None]
        if not fractions:
            return violations

        total = sum(fractions)
        if abs(total - 1.0) > 0.01:
            violations.append(
                (
                    "$.credentialSubject.materialProvenance",
                    f"Mass fractions sum to {total:.3f}, expected 1.0 (partial declaration)",
                )
            )
        return violations


class ValidityDateRule:
    """SEM002 (v0.7): validFrom must be before validUntil.

    Defensive duplicate — the v0.7 envelope already enforces this as a
    Pydantic model-level invariant (``DigitalProductPassport._validate_validity_window``).
    The rule is kept so semantic-layer error reporting is consistent with
    v0.6.x, where the same check is *only* at the semantic layer.
    """

    rule_id: str = "SEM002"
    description: str = "validFrom must be before validUntil"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Ensure validFrom is before validUntil"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM002"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
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
    """SEM003 (v0.7): hazardous=True requires materialSafetyInformation."""

    rule_id: str = "SEM003"
    description: str = "Hazardous materials require safety information"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add materialSafetyInformation for hazardous materials"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM003"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        materials = getattr(product, "material_provenance", []) or []
        for i, material in enumerate(materials):
            if material.hazardous and not material.material_safety_information:
                violations.append(
                    (
                        f"$.credentialSubject.materialProvenance[{i}]",
                        f"Material '{material.name}' is hazardous but missing materialSafetyInformation",
                    )
                )
        return violations


class CircularityContentRule:
    """SEM004 (v0.7): recycledContent should not exceed recyclableContent.

    v0.7 has no ``CircularityScorecard`` class; circularity is expressed as
    a :class:`Claim` with ``conformityTopic`` containing "circularity",
    whose ``claimedPerformance`` array carries the readings. This rule
    inspects each circularity claim and pairs values whose ``metric.id``
    looks like a content-fraction metric.

    To keep the rule shape-tolerant — the upstream schema doesn't
    constrain ``Performance.metric`` to a specific shape — we look up the
    metric by name keywords (``recycled``, ``recyclable``) and compare
    pairs. Tests in ``test_semantic_rules_v07.py`` exercise this with
    canonical metric IDs.
    """

    rule_id: str = "SEM004"
    description: str = "recycledContent should not exceed recyclableContent"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "recycledContent cannot exceed recyclableContent"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM004"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        for claim_idx, claim in enumerate(getattr(product, "performance_claim", []) or []):
            if not _circularity_topic(claim):
                continue
            recycled = recyclable = None
            for perf in getattr(claim, "claimed_performance", []) or []:
                metric = perf.metric or {}
                key = " ".join(str(metric.get(k, "")) for k in ("id", "name", "label")).lower()
                value = perf.measure.value if perf.measure else None
                if value is None:
                    continue
                if "recycledcontent" in key.replace(" ", "") or "recycled content" in key:
                    recycled = value
                elif "recyclablecontent" in key.replace(" ", "") or "recyclable content" in key:
                    recyclable = value
            if recycled is not None and recyclable is not None and recycled > recyclable:
                violations.append(
                    (
                        f"$.credentialSubject.performanceClaim[{claim_idx}]",
                        f"recycledContent ({recycled}) exceeds recyclableContent ({recyclable})",
                    )
                )
        return violations


class ConformityClaimRule:
    """SEM005 (v0.7): at least one performanceClaim is recommended.

    v0.6's ``conformityClaim`` array is now ``performanceClaim`` on Product;
    the warning text is updated accordingly so users searching for "no
    conformity claims" are still pointed at the right field.
    """

    rule_id: str = "SEM005"
    description: str = "At least one performanceClaim is recommended"
    severity: Literal["error", "warning", "info"] = "info"
    suggestion: str = "Add performance / conformity claims for sustainability or compliance"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM005"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        claims = getattr(product, "performance_claim", []) or []
        if not claims:
            violations.append(
                (
                    "$.credentialSubject.performanceClaim",
                    "No performance claims present. Consider adding sustainability or compliance claims.",
                )
            )
        return violations


class GranularitySerialNumberRule:
    """SEM006 (v0.7): item-/batch-level granularity require itemNumber/batchNumber.

    Defensive duplicate of the v0.7 model-level
    ``Product._granularity_implies_serial_or_batch`` invariant. Issued at
    semantic layer for parity with v0.6.x reporting (where it's the
    only place the check happens).
    """

    rule_id: str = "SEM006"
    description: str = "Item-/batch-level passports require an item or batch number"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Add itemNumber for 'item' granularity or batchNumber for 'batch' granularity"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/SEM006"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        granularity = str(getattr(product, "id_granularity", "") or "")
        if granularity == "item" and not getattr(product, "item_number", None):
            violations.append(
                (
                    "$.credentialSubject.itemNumber",
                    "idGranularity is 'item' but itemNumber is missing",
                )
            )
        elif granularity == "batch" and not getattr(product, "batch_number", None):
            violations.append(
                (
                    "$.credentialSubject.batchNumber",
                    "idGranularity is 'batch' but batchNumber is missing",
                )
            )
        return violations


class MaterialCodeRule:
    """VOC003 (v0.7): material code must be valid per UNECE Rec 46."""

    rule_id: str = "VOC003"
    description: str = "Material code must be in UNECE Rec 46"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Use a valid UNECE Rec 46 material code"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/VOC003"

    def __init__(
        self,
        material_validator: Callable[[str], bool] | None = None,
    ) -> None:
        self._is_valid_material_code = material_validator or _is_valid_material_code

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        materials = getattr(product, "material_provenance", []) or []
        for i, material in enumerate(materials):
            mt = getattr(material, "material_type", None)
            code = getattr(mt, "code", None) if mt else None
            if code and not self._is_valid_material_code(code):
                violations.append(
                    (
                        f"$.credentialSubject.materialProvenance[{i}].materialType.code",
                        f"Invalid material code '{code}' - not found in UNECE Rec 46",
                    )
                )
        return violations


class HSCodeRule:
    """VOC004 (v0.7): HS code must be valid for product category.

    v0.7 ``Product.product_category`` is a list of :class:`Classification`
    (was a single Classification in v0.6); this rule iterates over them.
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
        self._is_valid_hs_code = hs_validator or _is_valid_hs_code

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        categories = getattr(product, "product_category", []) or []
        for i, classification in enumerate(categories):
            code = getattr(classification, "code", None) or ""
            if code.isdigit() and len(code) >= 4 and not self._is_valid_hs_code(code):
                violations.append(
                    (
                        f"$.credentialSubject.productCategory[{i}].code",
                        f"Invalid HS code '{code}' - not found in textile chapters (50-63)",
                    )
                )
        return violations


class GTINChecksumRule:
    """VOC005 (v0.7): GTIN must have valid check digit.

    Walks ``credential_subject.id`` (was ``credentialSubject.product.id``
    in v0.6) and validates GS1 check-digits when the URI looks like a
    GS1 Digital Link or a bare GTIN.
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
        self._validate_gtin = gtin_validator or _validate_gtin

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        product_id = getattr(product, "id", None)
        if not product_id:
            return violations

        if "/01/" in product_id:
            match = re.search(r"/01/(\d{8,14})", product_id)
            if match:
                gtin = match.group(1)
                if not self._validate_gtin(gtin):
                    violations.append(
                        (
                            "$.credentialSubject.id",
                            f"Invalid GTIN checksum in '{gtin}'",
                        )
                    )
        elif product_id.isdigit() and len(product_id) in (8, 12, 13, 14):
            if not self._validate_gtin(product_id):
                violations.append(
                    (
                        "$.credentialSubject.id",
                        f"Invalid GTIN checksum in '{product_id}'",
                    )
                )
        return violations
