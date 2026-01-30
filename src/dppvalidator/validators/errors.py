"""Error utilities: suggestions, documentation links, and typo correction.

This module provides error context utilities for improved developer experience,
including "Did you mean?" suggestions, fix examples, and documentation links.

Note: The main ValidationError class is in validators/results.py.
This module provides utilities to enhance error messages.
"""

from __future__ import annotations

from difflib import get_close_matches
from typing import Any, TypedDict

# Base URL for error documentation
DOCS_BASE_URL = "https://artiso-ai.github.io/dppvalidator/errors"


class ErrorSuggestionDict(TypedDict, total=False):
    """Type definition for error suggestion dictionaries."""

    text: str
    example: str | None


# Error code registry with suggestions and documentation
ERROR_REGISTRY: dict[str, dict[str, Any]] = {
    # Parse errors
    "PRS001": {
        "title": "File Not Found",
        "suggestion": "Check that the file path is correct and the file exists.",
        "example": "dppvalidator validate ./data/passport.json",
    },
    "PRS002": {
        "title": "Invalid JSON",
        "suggestion": "Validate your JSON syntax. Common issues: trailing commas, unquoted keys.",
        "example": None,
    },
    "PRS003": {
        "title": "Unsupported Input Type",
        "suggestion": "Provide input as a dict, JSON string, or Path to a JSON file.",
        "example": 'engine.validate({"type": ["DigitalProductPassport"]})',
    },
    # Schema errors
    "SCH001": {
        "title": "Schema Validation Failed",
        "suggestion": "Check the JSON structure against the UNTP DPP schema.",
        "example": None,
    },
    "SCH002": {
        "title": "Missing Required Field",
        "suggestion": "Add the missing required field to your DPP data.",
        "example": None,
    },
    "SCH003": {
        "title": "Invalid Type",
        "suggestion": "Ensure the field value matches the expected type from the schema.",
        "example": None,
    },
    # Model errors
    "MDL001": {
        "title": "Model Validation Failed",
        "suggestion": "Check field types and constraints defined in Pydantic models.",
        "example": None,
    },
    "MDL002": {
        "title": "Invalid URL Format",
        "suggestion": "Provide a valid URL with scheme (https://)",
        "example": '"id": "https://example.com/credentials/dpp-001"',
    },
    "MDL003": {
        "title": "Invalid DateTime Format",
        "suggestion": "Use ISO 8601 datetime format.",
        "example": '"validFrom": "2024-01-01T00:00:00Z"',
    },
    # Semantic errors
    "SEM001": {
        "title": "Mass Fraction Sum Invalid",
        "suggestion": "Adjust material mass fractions to sum to 1.0 (100%).",
        "example": '"massFraction": 0.45  # Ensure all fractions sum to 1.0',
    },
    "SEM002": {
        "title": "Invalid Validity Period",
        "suggestion": "Ensure validFrom is before validUntil.",
        "example": '"validFrom": "2024-01-01", "validUntil": "2025-01-01"',
    },
    "SEM003": {
        "title": "Missing Safety Information",
        "suggestion": "Add materialSafetyInformation for hazardous materials.",
        "example": '"materialSafetyInformation": {"dataSheet": "https://..."}',
    },
    "SEM004": {
        "title": "Circularity Content Inconsistency",
        "suggestion": "recycledContent cannot exceed recyclableContent.",
        "example": '"recycledContent": 0.3, "recyclableContent": 0.8',
    },
    "SEM005": {
        "title": "Missing Conformity Claims",
        "suggestion": "Add conformity claims for sustainability or compliance.",
        "example": '"conformityClaim": [{"type": "Certification", "topic": "sustainability"}]',
    },
    "SEM006": {
        "title": "Missing Serial Number",
        "suggestion": "Add serialNumber for item-level granularity passports.",
        "example": '"serialNumber": "SN-2024-001234"',
    },
    "SEM007": {
        "title": "Missing Operational Scope",
        "suggestion": "Specify operationalScope with carbonFootprint data.",
        "example": '"operationalScope": "Scope1"',
    },
}

# Known valid values for "Did you mean?" suggestions
KNOWN_VALUES: dict[str, list[str]] = {
    "type": [
        "DigitalProductPassport",
        "VerifiableCredential",
        "EnvelopedVerifiableCredential",
    ],
    "granularityLevel": ["item", "batch", "model"],
    "operationalScope": ["None", "Scope1", "Scope2", "Scope3", "CradleToGate", "CradleToGrave"],
    "claimType": [
        "Certification",
        "Declaration",
        "Inspection",
        "Testing",
        "Verification",
        "Validation",
        "Assessment",
    ],
    "assessmentLevel": [
        "GovtApproval",
        "ThirdParty",
        "SecondParty",
        "FirstParty",
        "Self",
    ],
}


def get_error_docs_url(code: str) -> str:
    """Generate documentation URL for an error code."""
    return f"{DOCS_BASE_URL}/{code}"


def get_error_suggestion(code: str) -> ErrorSuggestionDict | None:
    """Get suggestion for an error code.

    Args:
        code: Error code to look up

    Returns:
        Dictionary with 'text' and optional 'example', or None if not found
    """
    if code in ERROR_REGISTRY:
        info = ERROR_REGISTRY[code]
        return ErrorSuggestionDict(
            text=info.get("suggestion", ""),
            example=info.get("example"),
        )
    return None


def find_similar_values(value: str, field_name: str, cutoff: float = 0.6) -> list[str]:
    """Find similar valid values for a field (typo correction).

    Args:
        value: The invalid value provided
        field_name: The field name to look up valid values
        cutoff: Similarity threshold (0-1)

    Returns:
        List of similar valid values
    """
    if field_name not in KNOWN_VALUES:
        return []

    valid_values = KNOWN_VALUES[field_name]
    matches = get_close_matches(value, valid_values, n=3, cutoff=cutoff)
    return matches


def get_suggestion_text(code: str) -> str | None:
    """Get suggestion text for an error code.

    Convenience function that returns just the suggestion text.

    Args:
        code: Error code to look up

    Returns:
        Suggestion text string, or None if not found
    """
    suggestion = get_error_suggestion(code)
    return suggestion["text"] if suggestion else None
