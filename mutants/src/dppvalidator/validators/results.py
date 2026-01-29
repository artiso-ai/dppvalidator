"""Validation result types using the Result pattern."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport
from inspect import signature as _mutmut_signature
from typing import Annotated, Callable, ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg=None):
    """Forward call to original or mutated function, depending on the environment"""
    import os

    mutant_under_test = os.environ["MUTANT_UNDER_TEST"]
    if mutant_under_test == "fail":
        from mutmut.__main__ import MutmutProgrammaticFailException

        raise MutmutProgrammaticFailException("Failed programmatically")
    elif mutant_under_test == "stats":
        from mutmut.__main__ import record_trampoline_hit

        record_trampoline_hit(orig.__module__ + "." + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + "." + orig.__name__ + "__mutmut_"
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition(".")[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


@dataclass(frozen=True, slots=True)
class ValidationError:
    """Represents a single validation error with full context.

    Attributes:
        path: JSON path to the error location (e.g., "$.credentialSubject.product.id")
        message: Human-readable error description
        code: Machine-readable error code (e.g., "SEM001")
        layer: Validation layer that produced this error
        severity: Error severity level
        context: Additional context for debugging
    """

    path: str
    message: str
    code: str
    layer: Literal["schema", "model", "semantic", "plugin"]
    severity: Literal["error", "warning", "info"] = "error"
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": self.path,
            "message": self.message,
            "code": self.code,
            "layer": self.layer,
            "severity": self.severity,
            "context": self.context,
        }


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

    def xǁValidationExceptionǁ__init____mutmut_orig(self, result: ValidationResult) -> None:
        self.result = result
        error_msgs = [f"  - {e.path}: {e.message} [{e.code}]" for e in result.errors]
        message = f"Validation failed with {len(result.errors)} error(s):\n" + "\n".join(error_msgs)
        super().__init__(message)

    def xǁValidationExceptionǁ__init____mutmut_1(self, result: ValidationResult) -> None:
        self.result = None
        error_msgs = [f"  - {e.path}: {e.message} [{e.code}]" for e in result.errors]
        message = f"Validation failed with {len(result.errors)} error(s):\n" + "\n".join(error_msgs)
        super().__init__(message)

    def xǁValidationExceptionǁ__init____mutmut_2(self, result: ValidationResult) -> None:
        self.result = result
        error_msgs = None
        message = f"Validation failed with {len(result.errors)} error(s):\n" + "\n".join(error_msgs)
        super().__init__(message)

    def xǁValidationExceptionǁ__init____mutmut_3(self, result: ValidationResult) -> None:
        self.result = result
        error_msgs = [f"  - {e.path}: {e.message} [{e.code}]" for e in result.errors]
        message = None
        super().__init__(message)

    def xǁValidationExceptionǁ__init____mutmut_4(self, result: ValidationResult) -> None:
        self.result = result
        error_msgs = [f"  - {e.path}: {e.message} [{e.code}]" for e in result.errors]
        message = f"Validation failed with {len(result.errors)} error(s):\n" - "\n".join(error_msgs)
        super().__init__(message)

    def xǁValidationExceptionǁ__init____mutmut_5(self, result: ValidationResult) -> None:
        self.result = result
        error_msgs = [f"  - {e.path}: {e.message} [{e.code}]" for e in result.errors]
        message = f"Validation failed with {len(result.errors)} error(s):\n" + "\n".join(None)
        super().__init__(message)

    def xǁValidationExceptionǁ__init____mutmut_6(self, result: ValidationResult) -> None:
        self.result = result
        error_msgs = [f"  - {e.path}: {e.message} [{e.code}]" for e in result.errors]
        message = f"Validation failed with {len(result.errors)} error(s):\n" + "XX\nXX".join(
            error_msgs
        )
        super().__init__(message)

    def xǁValidationExceptionǁ__init____mutmut_7(self, result: ValidationResult) -> None:
        self.result = result
        error_msgs = [f"  - {e.path}: {e.message} [{e.code}]" for e in result.errors]
        message = f"Validation failed with {len(result.errors)} error(s):\n" + "\n".join(error_msgs)
        super().__init__(None)

    xǁValidationExceptionǁ__init____mutmut_mutants: ClassVar[MutantDict] = {
        "xǁValidationExceptionǁ__init____mutmut_1": xǁValidationExceptionǁ__init____mutmut_1,
        "xǁValidationExceptionǁ__init____mutmut_2": xǁValidationExceptionǁ__init____mutmut_2,
        "xǁValidationExceptionǁ__init____mutmut_3": xǁValidationExceptionǁ__init____mutmut_3,
        "xǁValidationExceptionǁ__init____mutmut_4": xǁValidationExceptionǁ__init____mutmut_4,
        "xǁValidationExceptionǁ__init____mutmut_5": xǁValidationExceptionǁ__init____mutmut_5,
        "xǁValidationExceptionǁ__init____mutmut_6": xǁValidationExceptionǁ__init____mutmut_6,
        "xǁValidationExceptionǁ__init____mutmut_7": xǁValidationExceptionǁ__init____mutmut_7,
    }

    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(
            object.__getattribute__(self, "xǁValidationExceptionǁ__init____mutmut_orig"),
            object.__getattribute__(self, "xǁValidationExceptionǁ__init____mutmut_mutants"),
            args,
            kwargs,
            self,
        )
        return result

    __init__.__signature__ = _mutmut_signature(xǁValidationExceptionǁ__init____mutmut_orig)
    xǁValidationExceptionǁ__init____mutmut_orig.__name__ = "xǁValidationExceptionǁ__init__"
