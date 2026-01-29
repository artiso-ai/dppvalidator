"""Enhanced error messages with suggestions and documentation links.

This module provides rich error context for improved developer experience,
including "Did you mean?" suggestions, fix examples, and documentation links.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Any, Literal

# Base URL for error documentation
DOCS_BASE_URL = "https://artiso-ai.github.io/dppvalidator/errors"


@dataclass(frozen=True, slots=True)
class ErrorSuggestion:
    """A suggested fix for a validation error."""

    text: str
    example: str | None = None


@dataclass(frozen=True, slots=True)
class EnhancedValidationError:
    """Validation error with rich context for improved DX.

    Attributes:
        path: JSON path to the error location
        message: Human-readable error description
        code: Machine-readable error code (e.g., "SEM001")
        layer: Validation layer that produced this error
        severity: Error severity level
        suggestion: Suggested fix with optional example
        docs_url: Link to detailed error documentation
        did_you_mean: Suggested correct values (for typos)
        context: Additional context for debugging
    """

    path: str
    message: str
    code: str
    layer: Literal["schema", "model", "semantic", "plugin"]
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: ErrorSuggestion | None = None
    docs_url: str | None = None
    did_you_mean: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "path": self.path,
            "message": self.message,
            "code": self.code,
            "layer": self.layer,
            "severity": self.severity,
            "context": self.context,
        }
        if self.suggestion:
            result["suggestion"] = {
                "text": self.suggestion.text,
                "example": self.suggestion.example,
            }
        if self.docs_url:
            result["docs_url"] = self.docs_url
        if self.did_you_mean:
            result["did_you_mean"] = self.did_you_mean
        return result


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
    "operationalScope": ["Scope1", "Scope2", "Scope3", "CradleToGate", "CradleToGrave"],
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


def get_error_suggestion(code: str) -> ErrorSuggestion | None:
    """Get suggestion for an error code."""
    if code in ERROR_REGISTRY:
        info = ERROR_REGISTRY[code]
        return ErrorSuggestion(
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


def enhance_error(
    path: str,
    message: str,
    code: str,
    layer: Literal["schema", "model", "semantic", "plugin"],
    severity: Literal["error", "warning", "info"] = "error",
    context: dict[str, Any] | None = None,
    invalid_value: str | None = None,
    field_name: str | None = None,
) -> EnhancedValidationError:
    """Create an enhanced validation error with suggestions.

    Args:
        path: JSON path to error location
        message: Error message
        code: Error code
        layer: Validation layer
        severity: Error severity
        context: Additional context
        invalid_value: The invalid value (for typo suggestions)
        field_name: Field name (for looking up valid values)

    Returns:
        EnhancedValidationError with suggestions and docs link
    """
    suggestion = get_error_suggestion(code)
    docs_url = get_error_docs_url(code)

    did_you_mean: list[str] = []
    if invalid_value and field_name:
        did_you_mean = find_similar_values(invalid_value, field_name)

    return EnhancedValidationError(
        path=path,
        message=message,
        code=code,
        layer=layer,
        severity=severity,
        suggestion=suggestion,
        docs_url=docs_url,
        did_you_mean=did_you_mean,
        context=context or {},
    )


def format_error_for_display(error: EnhancedValidationError) -> str:
    """Format an enhanced error for terminal display.

    Returns a multi-line string with error details, suggestions, and links.
    """
    lines = [
        f"[{error.code}] {error.path}",
        f"  {error.message}",
    ]

    if error.did_you_mean:
        suggestions = ", ".join(f'"{v}"' for v in error.did_you_mean)
        lines.append(f"  Did you mean: {suggestions}?")

    if error.suggestion:
        lines.append(f"  💡 {error.suggestion.text}")
        if error.suggestion.example:
            lines.append(f"     Example: {error.suggestion.example}")

    if error.docs_url:
        lines.append(f"  📖 {error.docs_url}")

    return "\n".join(lines)
