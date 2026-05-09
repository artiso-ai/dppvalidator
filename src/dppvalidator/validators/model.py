"""Pydantic model validation layer (Layer 2)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from dppvalidator.models import v0_6, v0_7
from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION, SchemaFamily
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


def _load_cirpass_v1_3_model() -> type[BaseModel]:
    """Lazy loader for the CIRPASS reference-structure root model.

    Phase 4 task 4.7 of [docs/plans/CIRPASS_2_MIGRATION.md]. The
    cross-cutting workstream X3 (cold-start budget) requires that
    ``import dppvalidator`` not eagerly load the CIRPASS surface;
    that contract is pinned by
    ``tests/unit/test_cold_start_import.py``. Resolution happens
    inside this function rather than at module-import time so the
    CIRPASS package is only loaded when the engine actually needs
    it (auto-detect routes a CIRPASS payload to the CIRPASS pipeline,
    or the caller explicitly configures ``schema_version='1.3.0'``).
    """
    from dppvalidator.models.cirpass.v1_3 import ReferencePassport

    return ReferencePassport


# Phase 4 task 4.7: family-aware model dispatch. Keys are
# ``(SchemaFamily, version)``; values are *either* the resolved model
# class (UNTP — eagerly imported above) or a zero-arg callable that
# resolves the model class lazily (CIRPASS — preserves cold-start
# budget). The two-shape table avoids burning module-import time on
# CIRPASS for callers that only ever exercise the UNTP family.
_MODEL_BY_FAMILY_VERSION: dict[
    tuple[SchemaFamily, str], type[BaseModel] | Callable[[], type[BaseModel]]
] = {
    (SchemaFamily.UNTP, "0.6.0"): v0_6.DigitalProductPassport,
    (SchemaFamily.UNTP, "0.6.1"): v0_6.DigitalProductPassport,
    (SchemaFamily.UNTP, "0.7.0"): v0_7.DigitalProductPassport,
    (SchemaFamily.CIRPASS, "1.3.0"): _load_cirpass_v1_3_model,
}


def _resolve_model(family: SchemaFamily, version: str) -> type[BaseModel] | None:
    """Resolve the Pydantic root model for a ``(family, version)``.

    Returns ``None`` when the pair is unregistered. Callers translate
    ``None`` into a structured ``MDL098`` error (no model registered).
    """
    entry = _MODEL_BY_FAMILY_VERSION.get((family, version))
    if entry is None:
        return None
    # Class objects implement ``BaseModel.model_validate``; lazy
    # loaders are zero-arg callables that return such a class. We
    # discriminate via ``callable``-vs-``isinstance(type)`` here so
    # both branches narrow cleanly.
    if callable(entry) and not isinstance(entry, type):
        return entry()
    # ``entry`` is a model class object at this point. Bypass ty's
    # narrowing of ``isinstance(..., type)`` (which collapses to
    # ``type[Any]``) by routing through Any.
    return cast("type[BaseModel]", entry)


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

    def __init__(
        self,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
        family: SchemaFamily = SchemaFamily.UNTP,
    ) -> None:
        """Initialize model validator.

        Args:
            schema_version: Schema version (UNTP or CIRPASS) used for
                Pydantic root-class lookup and result metadata.
            family: Schema family. Phase 4 of the CIRPASS-2 migration
                added this axis so the validator can pick a CIRPASS
                root model (``ReferencePassport``) instead of the UNTP
                ``DigitalProductPassport`` envelope. Defaults to
                ``SchemaFamily.UNTP`` for back-compat with pre-Phase-4
                callers.
        """
        self.schema_version = schema_version
        self.family = family

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate data using Pydantic models.

        The Pydantic root class is selected from
        :data:`_MODEL_BY_FAMILY_VERSION` keyed on
        ``(self.family, self.schema_version)``. Adding a new version
        means adding one entry there (and shipping the model package);
        no changes are needed in this method.

        Args:
            data: Raw JSON data to validate

        Returns:
            ValidationResult with parsed passport if valid
        """
        start_time = time.perf_counter()
        errors: list[ValidationError] = []
        # Annotated as ``BaseModel | None`` rather than the v0.6
        # ``DigitalProductPassport`` so the dispatch can return any of:
        # v0.6 / v0.7 ``DigitalProductPassport`` or CIRPASS
        # ``ReferencePassport``. Callers downcast or use ``isinstance``
        # when they need a specific shape — see
        # docs/plans/UNTP_0.7.0_MIGRATION.md §3.3.
        passport: BaseModel | None = None

        model_cls = _resolve_model(self.family, self.schema_version)
        if model_cls is None:
            # Unsupported version — fail fast with a structured error rather
            # than silently coercing to whatever the default model accepts.
            available = ", ".join(
                f"({f.value}, {v})"
                for (f, v) in sorted(
                    _MODEL_BY_FAMILY_VERSION,
                    key=lambda k: (k[0].value, k[1]),
                )
            )
            errors.append(
                ValidationError(
                    path="$",
                    message=(
                        f"No Pydantic model registered for "
                        f"{(self.family.value, self.schema_version)!r}. "
                        f"Registered: {available}."
                    ),
                    code="MDL098",
                    layer="model",
                    severity="error",
                    context={
                        "requested_family": self.family.value,
                        "requested_version": self.schema_version,
                    },
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
