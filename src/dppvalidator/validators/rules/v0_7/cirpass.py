"""CIRPASS-2 CQ-based rules adapted for the UNTP v0.7.0 envelope.

Same CQ-coded rules as :mod:`dppvalidator.validators.rules.v0_6.cirpass`,
walking the new v0.7.0 shape:

- ``credentialSubject`` is :class:`Product` directly (no
  ``ProductPassport`` wrapper). The ``CIRPASSMandatoryAttributesRule``
  check that v0.6.x ran for ``credentialSubject.product`` is dropped
  because the *presence* of the product subject IS the
  ``credentialSubject``.
- ``materialsProvenance`` is renamed ``materialProvenance``.
- ``granularityLevel`` is renamed ``idGranularity`` and lives on
  ``credentialSubject`` directly (not nested inside a ProductPassport).
- ``product.serial_number`` is now ``credentialSubject.item_number``.
- All CQ codes (CQ001, CQ004, CQ011, CQ016, CQ017, CQ020) are preserved.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from dppvalidator.models.v0_7.envelope import DigitalProductPassport


class CIRPASSMandatoryAttributesRule:
    """CQ001 (v0.7): DPP must have mandatory attributes per ESPR.

    For v0.7.0 the check simplifies: there is no ``credentialSubject.product``
    nesting, so we verify ``credentialSubject`` itself is present (which is
    a Product) plus the mandatory envelope fields (``issuer``, ``validFrom``).
    """

    rule_id: str = "CQ001"
    description: str = "DPP must have mandatory ESPR attributes"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add required attributes: issuer, validFrom, credentialSubject"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ001"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []

        if not passport.issuer:
            violations.append(("$.issuer", "Missing issuer - required per ESPR Annex III (g)"))

        if not passport.valid_from:
            violations.append(("$.validFrom", "Missing validFrom - required per ESPR Art 9(2i)"))

        if not passport.credential_subject:
            violations.append(
                (
                    "$.credentialSubject",
                    "Missing credentialSubject - DPP has no product data",
                )
            )

        return violations


class CIRPASSSubstancesOfConcernRule:
    """CQ004 (v0.7): substances of concern must have proper identification."""

    rule_id: str = "CQ004"
    description: str = "Substances of concern must have CAS numbers"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add CAS number or EINECS number for each substance of concern"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ004"

    CAS_PATTERN = re.compile(r"^\d{2,7}-\d{2}-\d$")

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        materials = getattr(product, "material_provenance", []) or []
        for i, material in enumerate(materials):
            if material.hazardous:
                has_cas = False
                if material.name and self.CAS_PATTERN.search(material.name):
                    has_cas = True
                mt = getattr(material, "material_type", None)
                code = getattr(mt, "code", None) if mt else None
                if code and (self.CAS_PATTERN.match(code) or code.startswith("EINECS")):
                    has_cas = True

                if not has_cas:
                    violations.append(
                        (
                            f"$.credentialSubject.materialProvenance[{i}]",
                            f"Hazardous material '{material.name}' missing CAS/EINECS "
                            "number per ESPR Art 7(5a)",
                        )
                    )
        return violations


class CIRPASSOperatorIdentifierRule:
    """CQ011 (v0.7): manufacturer must have unique operator identifier.

    Same shape as v0.6 (issuer.id is unchanged across versions); the rule
    is duplicated only so the v0.7 ALL_RULES set carries it independently.
    """

    rule_id: str = "CQ011"
    description: str = "Manufacturer must have unique operator identifier"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add issuer.id with GLN, DUNS, or LEI identifier"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ011"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []

        if not passport.issuer:
            violations.append(("$.issuer", "Missing issuer - cannot verify operator identifier"))
            return violations

        if not passport.issuer.id:
            violations.append(
                (
                    "$.issuer.id",
                    "Missing issuer.id - manufacturer requires unique operator "
                    "identifier per ESPR Annex III (g)",
                )
            )
        return violations


class CIRPASSValidityPeriodRule:
    """CQ016 (v0.7): DPP must have validity period information."""

    rule_id: str = "CQ016"
    description: str = "DPP must have validity period"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Add validFrom and validUntil dates per ESPR Art 9(2i)"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ016"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []

        if not passport.valid_from:
            violations.append(
                (
                    "$.validFrom",
                    "Missing validFrom - market placement date required per ESPR Art 9(2i)",
                )
            )

        if not passport.valid_until:
            violations.append(
                (
                    "$.validUntil",
                    "Missing validUntil - DPP validity duration recommended per ESPR Art 9(2i)",
                )
            )
        return violations


class CIRPASSWeightVolumeRule:
    """CQ020 (v0.7): product should declare weight and volume."""

    rule_id: str = "CQ020"
    description: str = "Product should declare weight and volume"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Add product dimensions (weight/volume) per ESPR Annex I(j)"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ020"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        dim = getattr(product, "dimensions", None)
        has_dimension = bool(dim) and any(
            getattr(dim, attr, None) is not None
            for attr in ("weight", "length", "width", "height", "volume")
        )

        if not has_dimension:
            violations.append(
                (
                    "$.credentialSubject.dimensions",
                    "Missing weight/volume - product dimensions recommended per ESPR Annex I(j)",
                )
            )
        return violations


class CIRPASSGranularityConsistencyRule:
    """CQ017 (v0.7): granularity level must be consistent with identifiers.

    v0.7 renames ``granularityLevel`` → ``idGranularity`` and
    ``serialNumber`` → ``itemNumber``. Codes and ESPR references unchanged.
    """

    rule_id: str = "CQ017"
    description: str = "Granularity level must match identifier granularity"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Ensure idGranularity matches available identifiers"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ017"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        violations: list[tuple[str, str]] = []
        product = passport.credential_subject
        if product is None:
            return violations

        granularity = str(getattr(product, "id_granularity", "") or "").lower()

        if granularity == "item" and not getattr(product, "item_number", None):
            violations.append(
                (
                    "$.credentialSubject.itemNumber",
                    "idGranularity is 'item' but itemNumber is missing - "
                    "per SR5423 Annex II Part B 1.1(4)",
                )
            )

        if granularity == "batch" and not getattr(product, "batch_number", None):
            violations.append(
                (
                    "$.credentialSubject.batchNumber",
                    "idGranularity is 'batch' but batchNumber is missing - "
                    "per SR5423 Annex II Part B 1.1(3)",
                )
            )
        return violations


CIRPASS_RULES_V0_7 = [
    CIRPASSMandatoryAttributesRule(),
    CIRPASSSubstancesOfConcernRule(),
    CIRPASSOperatorIdentifierRule(),
    CIRPASSValidityPeriodRule(),
    CIRPASSWeightVolumeRule(),
    CIRPASSGranularityConsistencyRule(),
]
