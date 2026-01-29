"""Pluggable semantic validation rules."""

from dppvalidator.validators.rules.base import (
    CircularityContentRule,
    ConformityClaimRule,
    GranularitySerialNumberRule,
    HazardousMaterialRule,
    MassFractionSumRule,
    OperationalScopeRule,
    ValidityDateRule,
)

ALL_RULES = [
    MassFractionSumRule(),
    ValidityDateRule(),
    HazardousMaterialRule(),
    CircularityContentRule(),
    ConformityClaimRule(),
    GranularitySerialNumberRule(),
    OperationalScopeRule(),
]

__all__ = [
    "ALL_RULES",
    "MassFractionSumRule",
    "ValidityDateRule",
    "HazardousMaterialRule",
    "CircularityContentRule",
    "ConformityClaimRule",
    "GranularitySerialNumberRule",
    "OperationalScopeRule",
]
