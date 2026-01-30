"""Pydantic models for UNTP Digital Product Passport entities."""

from dppvalidator.models.base import UNTPBaseModel, UNTPStrictModel
from dppvalidator.models.claims import Claim, Criterion, Metric, Regulation, Standard
from dppvalidator.models.credential import CredentialIssuer, CredentialStatus, ProductPassport
from dppvalidator.models.enums import (
    ConformityTopic,
    CriterionStatus,
    EncryptionMethod,
    GranularityLevel,
    HashMethod,
    OperationalScope,
)
from dppvalidator.models.identifiers import Facility, IdentifierScheme, Party
from dppvalidator.models.materials import Material
from dppvalidator.models.passport import DigitalProductPassport
from dppvalidator.models.performance import (
    CircularityPerformance,
    EmissionsPerformance,
    TraceabilityPerformance,
)
from dppvalidator.models.primitives import (
    Classification,
    FlexibleUri,
    Link,
    Measure,
    SecureLink,
)
from dppvalidator.models.product import Characteristics, Dimension, Product

__all__ = [
    # Base
    "UNTPBaseModel",
    "UNTPStrictModel",
    # Enums
    "ConformityTopic",
    "CriterionStatus",
    "EncryptionMethod",
    "GranularityLevel",
    "HashMethod",
    "OperationalScope",
    # Primitives
    "Classification",
    "FlexibleUri",
    "Link",
    "Measure",
    "SecureLink",
    # Identifiers
    "Facility",
    "IdentifierScheme",
    "Party",
    # Product
    "Characteristics",
    "Dimension",
    "Product",
    # Claims
    "Claim",
    "Criterion",
    "Metric",
    "Regulation",
    "Standard",
    # Performance
    "CircularityPerformance",
    "EmissionsPerformance",
    "TraceabilityPerformance",
    # Materials
    "Material",
    # Credential
    "CredentialIssuer",
    "CredentialStatus",
    "ProductPassport",
    # Root
    "DigitalProductPassport",
]
