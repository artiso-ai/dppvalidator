"""Pydantic model validation layer (Layer 2)."""

from __future__ import annotations

import time
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from dppvalidator.models.passport import DigitalProductPassport
from dppvalidator.validators.results import ValidationError, ValidationResult

# Stable error code mapping based on Pydantic error types
# See: https://docs.pydantic.dev/latest/errors/validation_errors/
PYDANTIC_ERROR_CODES: dict[str, str] = {
    # Missing/required fields
    "missing": "MDL001",
    "value_error": "MDL002",
    # Type errors
    "string_type": "MDL010",
    "int_type": "MDL011",
    "float_type": "MDL012",
    "bool_type": "MDL013",
    "list_type": "MDL014",
    "dict_type": "MDL015",
    "none_required": "MDL016",
    # String validation
    "string_too_short": "MDL020",
    "string_too_long": "MDL021",
    "string_pattern_mismatch": "MDL022",
    # Numeric validation
    "greater_than": "MDL030",
    "greater_than_equal": "MDL031",
    "less_than": "MDL032",
    "less_than_equal": "MDL033",
    # URL/URI validation
    "url_parsing": "MDL040",
    "url_scheme": "MDL041",
    "url_type": "MDL042",
    # Date/time validation
    "datetime_parsing": "MDL050",
    "datetime_type": "MDL051",
    "date_parsing": "MDL052",
    "time_parsing": "MDL053",
    # Enum validation
    "enum": "MDL060",
    "literal_error": "MDL061",
    # JSON parsing
    "json_invalid": "MDL070",
    "json_type": "MDL071",
    # Model validation
    "model_type": "MDL080",
    "model_attributes_type": "MDL081",
    # Union/discriminator errors
    "union_tag_invalid": "MDL090",
    "union_tag_not_found": "MDL091",
}

# Default code for unmapped error types
DEFAULT_ERROR_CODE = "MDL099"


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
                error_type = error.get("type", "unknown")
                errors.append(
                    ValidationError(
                        path=json_path,
                        message=error.get("msg", "Validation error"),
                        code=self._get_error_code(error_type),
                        layer="model",
                        severity="error",
                        context={
                            "type": error_type,
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

    def _get_error_code(self, error_type: str) -> str:
        """Get stable error code for a Pydantic error type.

        Args:
            error_type: Pydantic error type string (e.g., 'missing', 'string_type')

        Returns:
            Stable error code (e.g., 'MDL001')
        """
        return PYDANTIC_ERROR_CODES.get(error_type, DEFAULT_ERROR_CODE)
