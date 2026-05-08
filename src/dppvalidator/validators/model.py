"""Pydantic model validation layer (Layer 2)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from dppvalidator.models import v0_6, v0_7
from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION
from dppvalidator.validators.results import ValidationError, ValidationResult

if TYPE_CHECKING:
    pass

# Single dispatch table for "which Pydantic root class validates which UNTP
# version". Adding a new version here is a one-line change — see Phase 3.3
# of docs/plans/UNTP_0.7.0_MIGRATION.md and the cardinal rules in
# .claude/rules/untp-versioning.md (rule 3).
#
# Keep keys aligned with ``SCHEMA_REGISTRY`` keys; the
# ``test_model_dispatch_covers_registry`` test in
# tests/unit/test_v07_models.py guarantees this.
_MODEL_BY_VERSION: dict[str, type[BaseModel]] = {
    "0.6.0": v0_6.DigitalProductPassport,
    "0.6.1": v0_6.DigitalProductPassport,
    "0.7.0": v0_7.DigitalProductPassport,
}

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

    def __init__(self, schema_version: str = DEFAULT_SCHEMA_VERSION) -> None:
        """Initialize model validator.

        Args:
            schema_version: UNTP DPP schema version for result metadata
        """
        self.schema_version = schema_version

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate data using Pydantic models.

        The Pydantic root class is selected from :data:`_MODEL_BY_VERSION`
        keyed on ``self.schema_version``. Adding a new UNTP version means
        adding one entry there (and shipping the model package); no
        changes are needed in this method.

        Args:
            data: Raw JSON data to validate

        Returns:
            ValidationResult with parsed passport if valid
        """
        start_time = time.perf_counter()
        errors: list[ValidationError] = []
        # Annotated as ``BaseModel | None`` rather than the v0.6
        # ``DigitalProductPassport`` so ``_MODEL_BY_VERSION`` can return
        # either a v0.6 or a v0.7 root class. Callers downcast or use
        # ``isinstance`` when they need a specific shape — see
        # docs/plans/UNTP_0.7.0_MIGRATION.md §3.3.
        passport: BaseModel | None = None

        model_cls = _MODEL_BY_VERSION.get(self.schema_version)
        if model_cls is None:
            # Unsupported version — fail fast with a structured error rather
            # than silently coercing to whatever the default model accepts.
            available = ", ".join(sorted(_MODEL_BY_VERSION))
            errors.append(
                ValidationError(
                    path="$",
                    message=(
                        f"No Pydantic model registered for schema version "
                        f"{self.schema_version!r}. Registered: {available}."
                    ),
                    code="MDL098",
                    layer="model",
                    severity="error",
                    context={"requested_version": self.schema_version},
                ),
            )
        else:
            try:
                passport = model_cls.model_validate(data)
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
            # `passport` is a v0.6 or v0.7 DigitalProductPassport at runtime;
            # ``ValidationResult.passport`` is annotated with the v0.6 type
            # under TYPE_CHECKING for backward compat (see plan §3.3).
            passport=passport,  # type: ignore[arg-type]
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
