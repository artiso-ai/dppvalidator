"""Semantic validation layer (Layer 3)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal

from dppvalidator.validators.results import ValidationError, ValidationResult
from dppvalidator.validators.rules import ALL_RULES

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class SemanticValidator:
    """Semantic validation layer for business rules.

    Applies domain-specific validation rules that go beyond
    schema and type validation.
    """

    name: str = "semantic"
    layer: str = "semantic"

    def __init__(
        self,
        schema_version: str = "0.6.1",
        rules: list[Any] | None = None,
    ) -> None:
        """Initialize semantic validator.

        Args:
            schema_version: UNTP DPP schema version
            rules: Custom rules list. If None, uses ALL_RULES.
        """
        self.schema_version = schema_version
        self.rules = rules if rules is not None else ALL_RULES

    def validate(
        self,
        passport: DigitalProductPassport,
    ) -> ValidationResult:
        """Validate passport against semantic rules.

        Args:
            passport: Parsed DigitalProductPassport to validate

        Returns:
            ValidationResult with semantic violations
        """
        start_time = time.perf_counter()

        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        info: list[ValidationError] = []

        for rule in self.rules:
            violations = rule.check(passport)
            severity: Literal["error", "warning", "info"] = getattr(rule, "severity", "error")
            suggestion: str | None = getattr(rule, "suggestion", None)
            docs_url: str | None = getattr(rule, "docs_url", None)

            for path, message in violations:
                error = ValidationError(
                    path=path,
                    message=message,
                    code=rule.rule_id,
                    layer="semantic",
                    severity=severity,
                    suggestion=suggestion,
                    docs_url=docs_url,
                )

                if severity == "error":
                    errors.append(error)
                elif severity == "warning":
                    warnings.append(error)
                else:
                    info.append(error)

        validation_time = (time.perf_counter() - start_time) * 1000

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
            schema_version=self.schema_version,
            passport=passport,
            validation_time_ms=validation_time,
        )
