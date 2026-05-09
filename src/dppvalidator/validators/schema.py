"""JSON Schema validation layer (Layer 1)."""

from __future__ import annotations

import copy
import json
import time
from importlib import resources
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator

from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION
from dppvalidator.validators.results import ValidationError, ValidationResult

# Schema type for dual-mode validation (Phase 6)
SchemaType = Literal["untp", "cirpass"]

# Stable error code mapping based on JSON Schema validator type
SCHEMA_ERROR_CODES: dict[str, str] = {
    "required": "SCH001",
    "type": "SCH002",
    "enum": "SCH003",
    "format": "SCH004",
    "pattern": "SCH005",
    "minLength": "SCH006",
    "maxLength": "SCH007",
    "minimum": "SCH008",
    "maximum": "SCH009",
    "additionalProperties": "SCH010",
    "minItems": "SCH011",
    "maxItems": "SCH012",
    "uniqueItems": "SCH013",
    "const": "SCH014",
    "allOf": "SCH015",
    "anyOf": "SCH016",
    "oneOf": "SCH017",
    "not": "SCH018",
    "contains": "SCH019",
    "prefixItems": "SCH020",
    "$ref": "SCH021",
}


class SchemaValidator:
    """JSON Schema validation layer.

    Provides strict schema compliance checking using JSON Schema Draft 2020-12.
    This is an optional layer that can be skipped for performance.
    """

    name: str = "schema"
    layer: str = "schema"

    def __init__(
        self,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
        schema_type: SchemaType = "untp",
        schema_path: Path | None = None,
        strict: bool = False,
    ) -> None:
        """Initialize schema validator.

        Args:
            schema_version: Schema version. For ``schema_type="untp"`` use a
                version registered in ``dppvalidator.schemas.SCHEMA_REGISTRY``;
                for ``schema_type="cirpass"`` use a CIRPASS DPP version. Defaults
                to ``DEFAULT_SCHEMA_VERSION``.
            schema_type: Schema type - "untp" (default) or "cirpass" for EU DPP
            schema_path: Optional custom schema path. If None, uses bundled schema.
            strict: If True, disallows additional properties not in schema

        Raises:
            ValueError: If schema_type is not "untp" or "cirpass"
        """
        if schema_type not in ("untp", "cirpass"):
            raise ValueError(f"Invalid schema_type '{schema_type}'. Must be 'untp' or 'cirpass'.")
        self.schema_version = schema_version
        self.schema_type = schema_type
        self.strict = strict
        self._schema: dict[str, Any] | None = None
        self._schema_path = schema_path
        self._validator: Any | None = None

    def _load_schema(self) -> dict[str, Any]:
        """Load JSON schema from bundled resources or custom path."""
        if self._schema is not None:
            return self._schema

        if self._schema_path:
            self._schema = json.loads(self._schema_path.read_text(encoding="utf-8"))
        elif self.schema_type == "cirpass":
            self._schema = self._load_cirpass_schema()
        else:
            self._schema = self._load_untp_schema()

        # Apply strict mode: set additionalProperties to false
        if self.strict and self._schema:
            self._schema = self._apply_strict_mode(self._schema)

        return self._schema

    def _load_untp_schema(self) -> dict[str, Any]:
        """Load UNTP DPP schema from bundled resources."""
        try:
            schema_file = resources.files("dppvalidator.schemas.data").joinpath(
                f"untp-dpp-schema-{self.schema_version}.json"
            )
            return json.loads(schema_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, ModuleNotFoundError):
            # No bundled schema available - validation will be skipped
            return {}

    def _load_cirpass_schema(self) -> dict[str, Any]:
        """Load CIRPASS DPP schema from bundled resources.

        Phase 4 of [docs/plans/CIRPASS_2_MIGRATION.md] prefers the
        Phase-3-derived ``cirpass-reference-{version}.json`` schema
        (the Pydantic-first projection of :class:`ReferencePassport`)
        over the legacy hub-imported ``cirpass_dpp_schema.json`` when
        a versioned bundle exists. Falls through to the legacy bundle
        for back-compat with pre-Phase-4 callers and to the
        :class:`CIRPASSSchemaLoader` for runtime-fetch scenarios.
        """
        # Phase 4 preferred: versioned derived schema.
        try:
            schema_file = resources.files("dppvalidator.schemas.data").joinpath(
                f"cirpass-reference-{self.schema_version}.json"
            )
            return json.loads(schema_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, ModuleNotFoundError):
            pass

        # Legacy hub-loader path.
        try:
            from dppvalidator.schemas.cirpass_loader import CIRPASSSchemaLoader

            loader = CIRPASSSchemaLoader()
            return loader.load()
        except (ImportError, RuntimeError):
            # Final fallback: legacy bundled schema.
            try:
                schema_file = resources.files("dppvalidator.vocabularies.data.schemas").joinpath(
                    "cirpass_dpp_schema.json"
                )
                return json.loads(schema_file.read_text(encoding="utf-8"))
            except (FileNotFoundError, ModuleNotFoundError):
                return {}

    def _apply_strict_mode(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Apply strict mode by setting additionalProperties to false.

        Args:
            schema: Original schema

        Returns:
            Modified schema with strict additionalProperties
        """
        schema = copy.deepcopy(schema)
        self._set_additional_properties_false(schema)
        return schema

    def _set_additional_properties_false(self, obj: dict[str, Any]) -> None:
        """Recursively set additionalProperties to false."""
        if not isinstance(obj, dict):
            return

        # Set additionalProperties to false for objects with properties
        if (
            "properties" in obj
            and "additionalProperties" not in obj
            or "properties" in obj
            and obj.get("additionalProperties") is True
        ):
            obj["additionalProperties"] = False

        # Recurse into $defs
        if "$defs" in obj:
            for def_schema in obj["$defs"].values():
                self._set_additional_properties_false(def_schema)

        # Recurse into properties
        if "properties" in obj:
            for prop_schema in obj["properties"].values():
                self._set_additional_properties_false(prop_schema)

        # Recurse into items
        if "items" in obj and isinstance(obj["items"], dict):
            self._set_additional_properties_false(obj["items"])

    def _get_validator(self) -> Any:
        """Get or create the JSON Schema validator."""
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
            error_code = self._get_error_code(error)
            errors.append(
                ValidationError(
                    path=json_path,
                    message=error.message,
                    code=error_code,
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

    def _get_error_code(self, error: Any) -> str:
        """Get stable error code based on JSON Schema validator type.

        Args:
            error: jsonschema validation error

        Returns:
            Stable error code string
        """
        validator_type = error.validator
        return SCHEMA_ERROR_CODES.get(validator_type, "SCH099")
