"""Enumeration types for UNTP DPP models."""

from __future__ import annotations

from enum import Enum


class ConformityTopic(str, Enum):
    """Conformity topic categories per UNTP specification."""

    ENVIRONMENT_ENERGY = "environment.energy"
    ENVIRONMENT_EMISSIONS = "environment.emissions"
    ENVIRONMENT_WATER = "environment.water"
    ENVIRONMENT_WASTE = "environment.waste"
    ENVIRONMENT_DEFORESTATION = "environment.deforestation"
    ENVIRONMENT_BIODIVERSITY = "environment.biodiversity"
    CIRCULARITY_CONTENT = "circularity.content"
    CIRCULARITY_DESIGN = "circularity.design"
    SOCIAL_LABOUR = "social.labour"
    SOCIAL_RIGHTS = "social.rights"
    SOCIAL_COMMUNITY = "social.community"
    SOCIAL_SAFETY = "social.safety"
    GOVERNANCE_ETHICS = "governance.ethics"
    GOVERNANCE_COMPLIANCE = "governance.compliance"
    GOVERNANCE_TRANSPARENCY = "governance.transparency"


class GranularityLevel(str, Enum):
    """Granularity level for product passports."""

    ITEM = "item"
    BATCH = "batch"
    MODEL = "model"


class OperationalScope(str, Enum):
    """Operational scope for emissions performance.

    Supports both GHG Protocol scopes (Scope1/2/3) and lifecycle
    assessment boundaries (CradleToGate/CradleToGrave).
    """

    NONE = "None"
    SCOPE1 = "Scope1"
    SCOPE2 = "Scope2"
    SCOPE3 = "Scope3"
    CRADLE_TO_GATE = "CradleToGate"
    CRADLE_TO_GRAVE = "CradleToGrave"


class HashMethod(str, Enum):
    """Hash algorithm for secure links."""

    SHA_256 = "SHA-256"
    SHA_1 = "SHA-1"


class EncryptionMethod(str, Enum):
    """Encryption method for secure links."""

    NONE = "none"
    AES = "AES"


class CriterionStatus(str, Enum):
    """Lifecycle status of a criterion."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
