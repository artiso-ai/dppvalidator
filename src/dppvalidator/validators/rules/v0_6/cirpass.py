"""CIRPASS-2 semantic validation rules based on Competency Questions.

Source: Ontology Requirements Specification for an EU DPP Core Ontology Proposal
DOI: 10.5281/zenodo.14892665

These rules implement validation checks derived from CIRPASS-2 Competency Questions
(CQs) which define functional requirements for the EU DPP Core Ontology.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class CIRPASSMandatoryAttributesRule:
    """CQ001: DPP must have mandatory attributes per ESPR.

    Based on CQ1: "What are the values of all or selected mandatory attributes
    of a DPP required by ESPR and delegated acts?"

    Checks that essential DPP attributes are present.
    """

    rule_id: str = "CQ001"
    description: str = "DPP must have mandatory ESPR attributes"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add required attributes: issuer, validFrom, credentialSubject"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ001"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check mandatory DPP attributes are present."""
        violations: list[tuple[str, str]] = []

        # Check issuer (ESPR Annex III (g))
        if not passport.issuer:
            violations.append(("$.issuer", "Missing issuer - required per ESPR Annex III (g)"))

        # Check validFrom (ESPR Art 9(2i))
        if not passport.valid_from:
            violations.append(("$.validFrom", "Missing validFrom - required per ESPR Art 9(2i)"))

        # Check credentialSubject
        if not passport.credential_subject:
            violations.append(
                (
                    "$.credentialSubject",
                    "Missing credentialSubject - DPP has no product data",
                )
            )
            return violations

        # Check product (core content)
        if not passport.credential_subject.product:
            violations.append(
                (
                    "$.credentialSubject.product",
                    "Missing product information - required per ESPR",
                )
            )

        return violations


class CIRPASSSubstancesOfConcernRule:
    """CQ004: Substances of concern must have proper identification.

    Based on CQ4: "What are the names and numeric codes of substances of
    concern present in the product?"

    Checks that substances of concern have CAS numbers or other identifiers.
    """

    rule_id: str = "CQ004"
    description: str = "Substances of concern must have CAS numbers"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add CAS number or EINECS number for each substance of concern"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ004"

    # CAS number pattern: NNNNNN-NN-N (digits with hyphens)
    CAS_PATTERN = re.compile(r"^\d{2,7}-\d{2}-\d$")

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check substances of concern have proper identification."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        materials = passport.credential_subject.materials_provenance
        if not materials:
            return violations

        for i, material in enumerate(materials):
            # Check if material is flagged as hazardous but lacks identifier
            if material.hazardous:
                has_cas = False
                # Check if name contains CAS-like pattern or has ID
                if material.name and self.CAS_PATTERN.search(material.name):
                    has_cas = True
                # Check material_type for code
                if material.material_type and material.material_type.code:
                    code = material.material_type.code
                    if self.CAS_PATTERN.match(code) or code.startswith("EINECS"):
                        has_cas = True

                if not has_cas:
                    violations.append(
                        (
                            f"$.credentialSubject.materialsProvenance[{i}]",
                            f"Hazardous material '{material.name}' missing CAS/EINECS "
                            "number per ESPR Art 7(5a)",
                        )
                    )

        return violations


class CIRPASSOperatorIdentifierRule:
    """CQ011: Manufacturer must have unique operator identifier.

    Based on CQ11: "What is the manufacturer's unique operator identifier
    of a product?"

    Checks that the issuer (manufacturer) has a proper identifier.
    """

    rule_id: str = "CQ011"
    description: str = "Manufacturer must have unique operator identifier"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = "Add issuer.id with GLN, DUNS, or LEI identifier"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ011"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check manufacturer has unique operator identifier."""
        violations: list[tuple[str, str]] = []

        if not passport.issuer:
            violations.append(
                (
                    "$.issuer",
                    "Missing issuer - cannot verify operator identifier",
                )
            )
            return violations

        # Check issuer has an ID
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
    """CQ016: DPP must have validity period information.

    Based on CQ16: "What is the date the product was placed on the EU market
    and what is the duration of validity period of the DPP?"

    Checks that DPP has market placement date and validity period.
    """

    rule_id: str = "CQ016"
    description: str = "DPP must have validity period"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Add validFrom and validUntil dates per ESPR Art 9(2i)"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ016"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check DPP has validity period."""
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
    """CQ020: Product must declare weight and volume.

    Based on CQ20: "What are the weight and volume of the product and its
    packaging, and the product-to-packaging ratio?"

    Checks that product has weight/volume declarations per ESPR Annex I(j).
    """

    rule_id: str = "CQ020"
    description: str = "Product should declare weight and volume"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Add product dimension (weight/volume) per ESPR Annex I(j)"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ020"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check product has weight/volume declarations."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        product = passport.credential_subject.product
        if not product:
            return violations

        # Check for dimensions data
        has_dimension = False
        if product.dimensions:
            dim = product.dimensions
            if dim.weight or dim.length or dim.width or dim.height or dim.volume:
                has_dimension = True

        if not has_dimension:
            violations.append(
                (
                    "$.credentialSubject.product.dimension",
                    "Missing weight/volume - product dimensions recommended per ESPR Annex I(j)",
                )
            )

        return violations


class CIRPASSGranularityConsistencyRule:
    """CQ017: Granularity level must be consistent with identifiers.

    Based on CQ17 and Standardisation Request 5423: granularityLevel must
    align with available identifiers (model/batch/item).

    Checks granularity level consistency with identifier presence.
    """

    rule_id: str = "CQ017"
    description: str = "Granularity level must match identifier granularity"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Ensure granularityLevel matches available identifiers"
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/CQ017"

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check granularity level consistency."""
        violations: list[tuple[str, str]] = []

        if not passport.credential_subject:
            return violations

        granularity = passport.credential_subject.granularity_level
        product = passport.credential_subject.product

        if not granularity or not product:
            return violations

        granularity_str = str(granularity).lower()

        # Item level requires serial number
        if granularity_str == "item" and not product.serial_number:
            violations.append(
                (
                    "$.credentialSubject.product.serialNumber",
                    "granularityLevel is 'item' but serialNumber is missing - "
                    "per SR5423 Annex II Part B 1.1(4)",
                )
            )

        # Batch level requires batch number
        if granularity_str == "batch" and not product.batch_number:
            violations.append(
                (
                    "$.credentialSubject.product.batchNumber",
                    "granularityLevel is 'batch' but batchNumber is missing - "
                    "per SR5423 Annex II Part B 1.1(3)",
                )
            )

        return violations


# List of all CIRPASS rules for easy registration
CIRPASS_RULES = [
    CIRPASSMandatoryAttributesRule(),
    CIRPASSSubstancesOfConcernRule(),
    CIRPASSOperatorIdentifierRule(),
    CIRPASSValidityPeriodRule(),
    CIRPASSWeightVolumeRule(),
    CIRPASSGranularityConsistencyRule(),
]
