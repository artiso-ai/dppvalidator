"""JSON Schema validation layer (Layer 1)."""

from __future__ import annotations

import json
import time
from importlib import resources
from pathlib import Path
from typing import Any

from dppvalidator.validators.results import ValidationError, ValidationResult

try:
    from jsonschema import Draft202012Validator
    from jsonschema import ValidationError as JsonSchemaError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    Draft202012Validator = None  # type: ignore[misc, assignment]
    JsonSchemaError = Exception  # type: ignore[misc, assignment]


class SchemaValidator:
    """JSON Schema validation layer.

    Provides strict schema compliance checking using JSON Schema Draft 2020-12.
    This is an optional layer that can be skipped for performance.
    """

    name: str = "schema"
    layer: str = "schema"

    def __init__(
        self,
        schema_version: str = "0.6.1",
        schema_path: Path | None = None,
    ) -> None:
        """Initialize schema validator.

        Args:
            schema_version: UNTP DPP schema version
            schema_path: Optional custom schema path. If None, uses bundled schema.
        """
        self.schema_version = schema_version
        self._schema: dict[str, Any] | None = None
        self._schema_path = schema_path
        self._validator: Any | None = None

    def _load_schema(self) -> dict[str, Any]:
        """Load JSON schema from bundled resources or custom path."""
        if self._schema is not None:
            return self._schema

        if self._schema_path:
            self._schema = json.loads(self._schema_path.read_text())
        else:
            try:
                schema_file = resources.files("dppvalidator.schemas.data").joinpath(
                    f"untp_dpp_{self.schema_version.replace('.', '_')}.json"
                )
                self._schema = json.loads(schema_file.read_text())
            except (FileNotFoundError, ModuleNotFoundError):
                # No bundled schema available - validation will be skipped
                self._schema = {}

        return self._schema

    def _get_validator(self) -> Any:
        """Get or create the JSON Schema validator."""
        if not HAS_JSONSCHEMA:
            return None

        if self._validator is None:
            schema = self._load_schema()
            if schema:
                self._validator = Draft202012Validator(schema)

        return self._validator

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate data against JSON Schema.

        Args:
            data: Raw JSON data to validate

        Returns:
            ValidationResult with any schema violations
        """
        start_time = time.perf_counter()

        if not HAS_JSONSCHEMA:
            return ValidationResult(
                valid=True,
                warnings=[
                    ValidationError(
                        path="$",
                        message="jsonschema not installed, skipping schema validation",
                        code="SCH000",
                        layer="schema",
                        severity="warning",
                    )
                ],
                schema_version=self.schema_version,
                validation_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        validator = self._get_validator()
        if validator is None:
            return ValidationResult(
                valid=True,
                warnings=[
                    ValidationError(
                        path="$",
                        message="No schema loaded, skipping schema validation",
                        code="SCH001",
                        layer="schema",
                        severity="warning",
                    )
                ],
                schema_version=self.schema_version,
                validation_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        errors: list[ValidationError] = []

        for error in validator.iter_errors(data):
            json_path = self._error_to_path(error)
            errors.append(
                ValidationError(
                    path=json_path,
                    message=error.message,
                    code=f"SCH{len(errors) + 100:03d}",
                    layer="schema",
                    severity="error",
                    context={"schema_path": list(error.schema_path)},
                )
            )

        validation_time = (time.perf_counter() - start_time) * 1000

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            schema_version=self.schema_version,
            validation_time_ms=validation_time,
        )

    def _error_to_path(self, error: Any) -> str:
        """Convert jsonschema error to JSON path string."""
        path_parts = ["$"]
        for part in error.absolute_path:
            if isinstance(part, int):
                path_parts.append(f"[{part}]")
            else:
                path_parts.append(f".{part}")
        return "".join(path_parts)
