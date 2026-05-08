"""Pydantic models for UNTP DPP **v0.6.x**.

Phase 3 of docs/plans/UNTP_0.7.0_MIGRATION.md splits the model package into
version-namespaced subpackages so 0.6.x and 0.7.x classes can coexist. This
subpackage holds the legacy 0.6.x shapes; the top-level
``dppvalidator.models`` and ``dppvalidator.models.passport`` re-export from
here for backward compatibility through the 0.4.x line. Phase 9 (validator
release 0.5.0) flips the default and re-exports v0.7 instead; Phase 10
(release 0.6.0) removes this subpackage entirely.

The ``examples/dppvalidator_example_plugin/`` and any third-party plugin
that imports ``from dppvalidator.models.passport import DigitalProductPassport``
keeps working because of the re-export shim — see §4.1.8 / §7.6 of the plan.
"""

from dppvalidator.models.v0_6.claims import (
    Claim,
    Criterion,
    Metric,
    Regulation,
    Standard,
)
from dppvalidator.models.v0_6.credential import (
    CredentialIssuer,
    CredentialStatus,
    ProductPassport,
)
from dppvalidator.models.v0_6.enums import (
    ConformityTopic,
    CriterionStatus,
    EncryptionMethod,
    GranularityLevel,
    HashMethod,
    OperationalScope,
)
from dppvalidator.models.v0_6.identifiers import Facility, IdentifierScheme, Party
from dppvalidator.models.v0_6.materials import Material
from dppvalidator.models.v0_6.passport import DigitalProductPassport
from dppvalidator.models.v0_6.performance import (
    CircularityPerformance,
    EmissionsPerformance,
    TraceabilityPerformance,
)
from dppvalidator.models.v0_6.primitives import (
    Classification,
    FlexibleUri,
    Link,
    Measure,
    SecureLink,
)
from dppvalidator.models.v0_6.product import Characteristics, Dimension, Product

__all__ = [
    # Claims
    "Claim",
    "Criterion",
    "Metric",
    "Regulation",
    "Standard",
    # Credential
    "CredentialIssuer",
    "CredentialStatus",
    "ProductPassport",
    # Enums
    "ConformityTopic",
    "CriterionStatus",
    "EncryptionMethod",
    "GranularityLevel",
    "HashMethod",
    "OperationalScope",
    # Identifiers
    "Facility",
    "IdentifierScheme",
    "Party",
    # Materials
    "Material",
    # Passport (envelope)
    "DigitalProductPassport",
    # Performance scorecards (collapse into Claim.claimedPerformance in v0.7)
    "CircularityPerformance",
    "EmissionsPerformance",
    "TraceabilityPerformance",
    # Primitives
    "Classification",
    "FlexibleUri",
    "Link",
    "Measure",
    "SecureLink",
    # Product
    "Characteristics",
    "Dimension",
    "Product",
]
