"""Three-layer DPP validation engine."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from dppvalidator.logging import get_logger
from dppvalidator.validators.model import ModelValidator
from dppvalidator.validators.results import ValidationError, ValidationResult
from dppvalidator.validators.schema import SchemaValidator
from dppvalidator.validators.semantic import SemanticValidator

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport

logger = get_logger(__name__)


class ValidationEngine:
    """Three-layer validation engine for Digital Product Passports.

    Provides configurable validation through three layers:
    1. Schema validation (JSON Schema Draft 2020-12)
    2. Model validation (Pydantic v2)
    3. Semantic validation (Business rules)

    Following the Result pattern, validation never raises exceptions.
    Check `result.valid` and inspect `result.errors` for details.
    """

    # Default max input size: 10 MB (protects against DoS via huge payloads)
    DEFAULT_MAX_INPUT_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(
        self,
        schema_version: str = "0.6.1",
        strict_mode: bool = False,
        validate_vocabularies: bool = False,
        layers: list[Literal["schema", "model", "semantic"]] | None = None,
        load_plugins: bool = True,
        max_input_size: int | None = None,
    ) -> None:
        """Initialize the validation engine.

        Args:
            schema_version: UNTP DPP schema version to validate against
            strict_mode: If True, enables strict JSON Schema validation
            validate_vocabularies: If True, validates external vocabulary values
            layers: Specific layers to run. None means all layers.
            load_plugins: If True, discovers and loads plugin validators
            max_input_size: Maximum input size in bytes. None uses default (10MB).
                Set to 0 to disable size limits.
        """
        self.schema_version = schema_version
        self.strict_mode = strict_mode
        self.validate_vocabularies = validate_vocabularies
        self.layers = layers or ["schema", "model", "semantic"]
        self._load_plugins = load_plugins
        self.max_input_size = (
            max_input_size if max_input_size is not None else self.DEFAULT_MAX_INPUT_SIZE
        )

        self._schema_validator = SchemaValidator(schema_version, strict=strict_mode)
        self._model_validator = ModelValidator(schema_version)
        self._semantic_validator = SemanticValidator(schema_version)

        # Initialize vocabulary loader if needed
        self._vocab_loader = None
        if validate_vocabularies:
            self._init_vocabulary_loader()

        # Initialize plugin registry if needed
        self._plugin_registry = None
        if load_plugins:
            self._init_plugin_registry()

    def _init_vocabulary_loader(self) -> None:
        """Initialize the vocabulary loader for external vocabulary validation."""
        try:
            from dppvalidator.vocabularies.loader import VocabularyLoader

            self._vocab_loader = VocabularyLoader(offline_mode=False)
            logger.debug("Vocabulary loader initialized")
        except ImportError:
            logger.warning("Vocabulary loader not available")

    def _init_plugin_registry(self) -> None:
        """Initialize the plugin registry for plugin validators."""
        try:
            from dppvalidator.plugins.registry import PluginRegistry

            self._plugin_registry = PluginRegistry(auto_discover=True)
            logger.debug(
                "Plugin registry initialized with %d validators",
                self._plugin_registry.validator_count,
            )
        except (ImportError, AttributeError, TypeError) as e:
            logger.warning("Plugin registry initialization failed: %s", e)

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

        # Run vocabulary validation if enabled
        if self.validate_vocabularies and passport:
            vocab_result = self._validate_vocabularies(passport)
            result = result.merge(vocab_result)

        # Run plugin validators if enabled
        if self._load_plugins and self._plugin_registry and passport:
            plugin_result = self._run_plugin_validators(passport)
            result = result.merge(plugin_result)

        result.passport = passport
        return result

    def _validate_vocabularies(self, passport: DigitalProductPassport) -> ValidationResult:
        """Validate vocabulary values in the passport.

        Args:
            passport: Parsed passport to validate

        Returns:
            ValidationResult with vocabulary violations
        """
        if not self._vocab_loader:
            return ValidationResult(valid=True, schema_version=self.schema_version)

        warnings: list[ValidationError] = []

        # Validate country codes in materials provenance
        if passport.credential_subject and passport.credential_subject.materials_provenance:
            for i, material in enumerate(passport.credential_subject.materials_provenance):
                origin = getattr(material, "origin_country", None)
                if origin and not self._vocab_loader.is_valid_country(origin):
                    warnings.append(
                        ValidationError(
                            path=f"$.credentialSubject.materialsProvenance[{i}].originCountry",
                            message=f"Invalid country code: '{material.origin_country}'",
                            code="VOC001",
                            layer="vocabulary",
                            severity="warning",
                            suggestion="Use ISO 3166-1 alpha-2 country codes",
                        )
                    )

        # Validate unit codes in measures (dimensions, emissions, etc.)
        if passport.credential_subject and passport.credential_subject.product:
            product = passport.credential_subject.product
            dims = getattr(product, "dimensions", None)
            if dims:
                for field_name in ["weight", "length", "width", "height", "volume"]:
                    measure = getattr(dims, field_name, None)
                    unit = getattr(measure, "unit", None) if measure else None
                    if unit and not self._vocab_loader.is_valid_unit(unit):
                        warnings.append(
                            ValidationError(
                                path=f"$.credentialSubject.product.dimensions.{field_name}.unit",
                                message=f"Invalid unit code: '{unit}'",
                                code="VOC002",
                                layer="vocabulary",
                                severity="warning",
                                suggestion="Use UNECE Rec20 unit codes",
                            )
                        )

        return ValidationResult(
            valid=True,  # Vocabulary issues are warnings, not errors
            warnings=warnings,
            schema_version=self.schema_version,
        )

    def _run_plugin_validators(self, passport: DigitalProductPassport) -> ValidationResult:
        """Run all registered plugin validators.

        Args:
            passport: Parsed passport to validate

        Returns:
            ValidationResult with plugin validation results
        """
        if not self._plugin_registry:
            return ValidationResult(valid=True, schema_version=self.schema_version)

        plugin_errors = self._plugin_registry.run_all_validators(passport)

        errors = [e for e in plugin_errors if e.severity == "error"]
        warnings = [e for e in plugin_errors if e.severity == "warning"]
        info = [e for e in plugin_errors if e.severity == "info"]

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
            schema_version=self.schema_version,
        )

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
        return await asyncio.to_thread(self.validate, data)

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
        # Check input size for string inputs (DoS protection)
        if (
            isinstance(data, str)
            and self.max_input_size > 0
            and len(data.encode("utf-8")) > self.max_input_size
        ):
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationError(
                        path="$",
                        message=(
                            f"Input size exceeds maximum allowed "
                            f"({self.max_input_size:,} bytes). "
                            "Consider splitting into smaller documents."
                        ),
                        code="PRS004",
                        layer="model",
                        severity="error",
                    )
                ],
                schema_version=self.schema_version,
            )

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
