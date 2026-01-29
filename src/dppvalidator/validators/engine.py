"""Three-layer DPP validation engine."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from dppvalidator.validators.model import ModelValidator
from dppvalidator.validators.results import ValidationResult
from dppvalidator.validators.schema import SchemaValidator
from dppvalidator.validators.semantic import SemanticValidator

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class ValidationEngine:
    """Three-layer validation engine for Digital Product Passports.

    Provides configurable validation through three layers:
    1. Schema validation (JSON Schema Draft 2020-12)
    2. Model validation (Pydantic v2)
    3. Semantic validation (Business rules)

    Following the Result pattern, validation never raises exceptions.
    Check `result.valid` and inspect `result.errors` for details.
    """

    def __init__(
        self,
        schema_version: str = "0.6.1",
        strict_mode: bool = False,
        validate_vocabularies: bool = False,
        layers: list[Literal["schema", "model", "semantic"]] | None = None,
        load_plugins: bool = True,
    ) -> None:
        """Initialize the validation engine.

        Args:
            schema_version: UNTP DPP schema version to validate against
            strict_mode: If True, enables strict JSON Schema validation
            validate_vocabularies: If True, validates external vocabulary values
            layers: Specific layers to run. None means all layers.
            load_plugins: If True, discovers and loads plugin validators
        """
        self.schema_version = schema_version
        self.strict_mode = strict_mode
        self.validate_vocabularies = validate_vocabularies
        self.layers = layers or ["schema", "model", "semantic"]
        self.load_plugins = load_plugins

        self._schema_validator = SchemaValidator(schema_version)
        self._model_validator = ModelValidator(schema_version)
        self._semantic_validator = SemanticValidator(schema_version)

    def validate(
        self,
        data: dict[str, Any] | str | Path,
        *,
        fail_fast: bool = False,
        max_errors: int = 100,
    ) -> ValidationResult:
        """Validate DPP data through configured layers.

        Args:
            data: Raw JSON dict, JSON string, or path to JSON file
            fail_fast: Stop on first error if True
            max_errors: Maximum errors to collect before stopping

        Returns:
            ValidationResult with parsed passport if valid
        """
        start_time = time.perf_counter()

        parsed_data = self._parse_input(data)
        if isinstance(parsed_data, ValidationResult):
            return parsed_data

        parse_time = (time.perf_counter() - start_time) * 1000
        result = ValidationResult(
            valid=True,
            schema_version=self.schema_version,
            parse_time_ms=parse_time,
        )

        passport: DigitalProductPassport | None = None

        if "schema" in self.layers:
            schema_result = self._schema_validator.validate(parsed_data)
            result = result.merge(schema_result)
            if fail_fast and not result.valid:
                return result
            if result.error_count >= max_errors:
                return result

        if "model" in self.layers:
            model_result = self._model_validator.validate(parsed_data)
            result = result.merge(model_result)
            passport = model_result.passport
            if fail_fast and not result.valid:
                return result
            if result.error_count >= max_errors:
                return result

        if "semantic" in self.layers and passport:
            semantic_result = self._semantic_validator.validate(passport)
            result = result.merge(semantic_result)

        result.passport = passport
        return result

    def validate_file(self, path: Path | str) -> ValidationResult:
        """Validate a JSON file.

        Args:
            path: Path to JSON file

        Returns:
            ValidationResult
        """
        return self.validate(Path(path))

    async def validate_async(self, data: dict[str, Any]) -> ValidationResult:
        """Validate data asynchronously.

        Args:
            data: Raw JSON dict

        Returns:
            ValidationResult
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.validate, data)

    async def validate_batch(
        self,
        items: list[dict[str, Any]],
        *,
        concurrency: int = 10,
    ) -> list[ValidationResult]:
        """Validate multiple items concurrently.

        Args:
            items: List of raw JSON dicts
            concurrency: Maximum concurrent validations

        Returns:
            List of ValidationResults in same order as input
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def validate_with_semaphore(item: dict[str, Any]) -> ValidationResult:
            async with semaphore:
                return await self.validate_async(item)

        return await asyncio.gather(*[validate_with_semaphore(item) for item in items])

    def _parse_input(self, data: dict[str, Any] | str | Path) -> dict[str, Any] | ValidationResult:
        """Parse input data to dict.

        Returns:
            Parsed dict or ValidationResult with parse error
        """
        from dppvalidator.validators.results import ValidationError

        if isinstance(data, dict):
            return data

        if isinstance(data, Path):
            try:
                return json.loads(data.read_text())
            except FileNotFoundError:
                return ValidationResult(
                    valid=False,
                    errors=[
                        ValidationError(
                            path="$",
                            message=f"File not found: {data}",
                            code="PRS001",
                            layer="model",
                        )
                    ],
                    schema_version=self.schema_version,
                )
            except json.JSONDecodeError as e:
                return ValidationResult(
                    valid=False,
                    errors=[
                        ValidationError(
                            path="$",
                            message=f"Invalid JSON: {e}",
                            code="PRS002",
                            layer="model",
                        )
                    ],
                    schema_version=self.schema_version,
                )

        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    valid=False,
                    errors=[
                        ValidationError(
                            path="$",
                            message=f"Invalid JSON: {e}",
                            code="PRS002",
                            layer="model",
                        )
                    ],
                    schema_version=self.schema_version,
                )

        return ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    path="$",
                    message=f"Unsupported input type: {type(data).__name__}",
                    code="PRS003",
                    layer="model",
                )
            ],
            schema_version=self.schema_version,
        )


class OpenDPP(ValidationEngine):
    """Backwards-compatible alias for ValidationEngine."""

    def validate_passport(self, json_data: dict[str, Any]) -> ValidationResult:
        """Validate a raw JSON object against the UNTP DPP Schema."""
        return self.validate(json_data)
