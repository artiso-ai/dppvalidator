"""Validation result types using the Result pattern."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


@dataclass(frozen=True, slots=True)
class ValidationError:
    """Represents a single validation error with full context.

    Attributes:
        path: JSON path to the error location (e.g., "$.credentialSubject.product.id")
        message: Human-readable error description
        code: Machine-readable error code (e.g., "SEM001")
        layer: Validation layer that produced this error
        severity: Error severity level
        suggestion: Suggested fix for the error
        docs_url: Link to detailed error documentation
        did_you_mean: Similar valid values (for typo correction)
        context: Additional context for debugging
    """

    path: str
    message: str
    code: str
    layer: Literal["schema", "model", "semantic", "plugin", "vocabulary"]
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str | None = None
    docs_url: str | None = None
    did_you_mean: tuple[str, ...] = ()
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
            result["suggestion"] = self.suggestion
        if self.docs_url:
            result["docs_url"] = self.docs_url
        if self.did_you_mean:
            result["did_you_mean"] = list(self.did_you_mean)
        return result


@dataclass
class ValidationResult:
    """Result of DPP validation following the Result pattern.

    Never raises exceptions for validation failures. Instead, check
    the `valid` property and inspect `errors` for details.

    Attributes:
        valid: Whether the passport passed all validation layers
        errors: List of validation errors (severity="error")
        warnings: List of validation warnings (severity="warning")
        info: List of informational messages (severity="info")
        schema_version: UNTP DPP schema version used
        validated_at: Timestamp of validation
        passport: Parsed DigitalProductPassport if valid, None otherwise
        parse_time_ms: Time spent parsing input
        validation_time_ms: Time spent on validation layers
    """

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    info: list[ValidationError] = field(default_factory=list)
    schema_version: str = "0.6.1"
    validated_at: datetime = field(default_factory=datetime.now)
    passport: DigitalProductPassport | None = None
    parse_time_ms: float = 0.0
    validation_time_ms: float = 0.0

    @property
    def error_count(self) -> int:
        """Total number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Total number of warnings."""
        return len(self.warnings)

    @property
    def all_issues(self) -> list[ValidationError]:
        """All errors, warnings, and info messages combined."""
        return self.errors + self.warnings + self.info

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": [i.to_dict() for i in self.info],
            "schema_version": self.schema_version,
            "validated_at": self.validated_at.isoformat(),
            "parse_time_ms": self.parse_time_ms,
            "validation_time_ms": self.validation_time_ms,
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def raise_for_errors(self) -> None:
        """Raise ValidationException if there are errors.

        This is an opt-in method for users who prefer exception-based flow.
        """
        if not self.valid:
            raise ValidationException(self)

    def __repr__(self) -> str:
        """Return a concise representation for debugging."""
        return (
            f"ValidationResult(valid={self.valid}, "
            f"errors={len(self.errors)}, "
            f"warnings={len(self.warnings)}, "
            f"info={len(self.info)})"
        )

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another result into this one."""
        return ValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            info=self.info + other.info,
            schema_version=self.schema_version,
            validated_at=self.validated_at,
            passport=self.passport if self.valid else other.passport,
            parse_time_ms=self.parse_time_ms + other.parse_time_ms,
            validation_time_ms=self.validation_time_ms + other.validation_time_ms,
        )


class ValidationException(Exception):
    """Exception raised when raise_for_errors() is called on invalid result."""

    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        error_msgs = [f"  - {e.path}: {e.message} [{e.code}]" for e in result.errors]
        message = f"Validation failed with {len(result.errors)} error(s):\n" + "\n".join(error_msgs)
        super().__init__(message)
