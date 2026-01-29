"""Pydantic model validation layer (Layer 2)."""

from __future__ import annotations

import time
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from dppvalidator.models.passport import DigitalProductPassport
from dppvalidator.validators.results import ValidationError, ValidationResult


class ModelValidator:
    """Pydantic model validation layer.

    Provides type coercion, field validation, and model validators
    through Pydantic v2's validation system.
    """

    name: str = "model"
    layer: str = "model"

    def __init__(self, schema_version: str = "0.6.1") -> None:
        """Initialize model validator.

        Args:
            schema_version: UNTP DPP schema version for result metadata
        """
        self.schema_version = schema_version

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate data using Pydantic models.

        Args:
            data: Raw JSON data to validate

        Returns:
            ValidationResult with parsed passport if valid
        """
        start_time = time.perf_counter()
        errors: list[ValidationError] = []
        passport: DigitalProductPassport | None = None

        try:
            passport = DigitalProductPassport.model_validate(data)
        except PydanticValidationError as e:
            for error in e.errors():
                json_path = self._loc_to_path(error.get("loc", ()))
                errors.append(
                    ValidationError(
                        path=json_path,
                        message=error.get("msg", "Validation error"),
                        code=f"MDL{len(errors) + 100:03d}",
                        layer="model",
                        severity="error",
                        context={
                            "type": error.get("type", "unknown"),
                            "input": self._safe_input(error.get("input")),
                        },
                    )
                )

        validation_time = (time.perf_counter() - start_time) * 1000

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            schema_version=self.schema_version,
            passport=passport,
            validation_time_ms=validation_time,
        )

    def _loc_to_path(self, loc: tuple[Any, ...]) -> str:
        """Convert Pydantic error location to JSON path."""
        path_parts = ["$"]
        for part in loc:
            if isinstance(part, int):
                path_parts.append(f"[{part}]")
            else:
                path_parts.append(f".{part}")
        return "".join(path_parts)

    def _safe_input(self, value: Any) -> Any:
        """Safely convert input value for JSON serialization."""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, dict)):
            return str(value)[:100] + "..." if len(str(value)) > 100 else value
        return str(value)[:100]
