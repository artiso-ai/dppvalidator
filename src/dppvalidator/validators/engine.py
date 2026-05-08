"""Multi-layer DPP validation engine.

Implements seven validation layers:
1. Schema: JSON Schema validation (Draft 2020-12)
2. Model: Pydantic model validation
3. Semantic: Business rule validation
4. JSON-LD: Context expansion validation
5. Vocabulary: External vocabulary validation
6. Plugin: Custom validator plugins
7. Signature: Verifiable Credential verification
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from dppvalidator.logging import get_logger
from dppvalidator.validators.detection import (
    detect_declared_version,
    detect_schema_version,
)
from dppvalidator.validators.layers import (
    JsonLdLayer,
    ModelLayer,
    PluginLayer,
    SchemaLayer,
    SemanticLayer,
    SignatureLayer,
    ValidationContext,
    ValidationLayer,
    VocabularyLayer,
)
from dppvalidator.validators.model import ModelValidator
from dppvalidator.validators.results import ValidationError, ValidationResult
from dppvalidator.validators.schema import SchemaValidator
from dppvalidator.validators.semantic import SemanticValidator
from dppvalidator.vocabularies.rdf_loader import is_shacl_available

if TYPE_CHECKING:
    from dppvalidator.validators.deep import DeepValidationResult


def _is_jsonld_available() -> bool:
    """Check if JSON-LD dependencies (pyld) are available."""
    try:
        import pyld  # noqa: F401

        return True
    except ImportError:
        return False


def _is_crypto_available() -> bool:
    """Check if cryptography dependencies are available for signature verification."""
    try:
        import cryptography  # noqa: F401

        return True
    except ImportError:
        return False


logger = get_logger(__name__)


class ValidationEngine:
    """Seven-layer validation engine for Digital Product Passports.

    Provides configurable validation through seven layers:
    1. Schema validation (JSON Schema Draft 2020-12)
    2. Model validation (Pydantic v2)
    3. Semantic validation (Business rules)
    4. JSON-LD validation (Context expansion and term resolution)
    5. Vocabulary validation (External code lists and ontologies)
    6. Plugin validation (Custom validator plugins)
    7. Signature verification (Verifiable Credential proofs)

    Following the Result pattern, validation never raises exceptions.
    Check `result.valid` and inspect `result.errors` for details.
    """

    # Default max input size: 10 MB (protects against DoS via huge payloads)
    DEFAULT_MAX_INPUT_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(
        self,
        schema_version: str = "auto",
        strict_mode: bool = False,
        validate_vocabularies: bool = False,
        layers: list[Literal["schema", "model", "semantic", "jsonld"]] | None = None,
        validate_jsonld: bool = False,
        verify_signatures: bool = False,
        load_plugins: bool = True,
        max_input_size: int | None = None,
        enable_shacl: bool = False,
    ) -> None:
        """Initialize the validation engine.

        Args:
            schema_version: UNTP DPP schema version to validate against.
                Use "auto" to detect version from input data (default).
            strict_mode: If True, enables strict JSON Schema validation
            validate_vocabularies: If True, validates external vocabulary values
            layers: Specific layers to run. None means all layers.
            validate_jsonld: If True, enables JSON-LD semantic validation (requires pyld)
            verify_signatures: If True, verifies VC signatures (requires cryptography)
            load_plugins: If True, discovers and loads plugin validators
            max_input_size: Maximum input size in bytes. None uses default (10MB).
                Set to 0 to disable size limits.
            enable_shacl: If True, enables SHACL validation against official
                CIRPASS-2 shapes. Requires: uv add dppvalidator[rdf] or
                pip install dppvalidator[rdf]

        Raises:
            ImportError: If optional features are enabled but dependencies not installed:
                - enable_shacl=True requires [rdf] extra
                - validate_jsonld=True requires pyld (included in base install)
                - verify_signatures=True requires cryptography (included in base install)
        """
        # Explicit feature detection for optional dependencies
        if enable_shacl and not is_shacl_available():
            raise ImportError(
                "SHACL validation requires the [rdf] extra. "
                "Install with: uv add dppvalidator[rdf] or pip install dppvalidator[rdf]"
            )

        if validate_jsonld and not _is_jsonld_available():
            raise ImportError(
                "JSON-LD validation requires pyld. Install with: uv add pyld or pip install pyld"
            )

        if verify_signatures and not _is_crypto_available():
            raise ImportError(
                "Signature verification requires cryptography. "
                "Install with: uv add cryptography or pip install cryptography"
            )
        self._auto_detect = schema_version == "auto"
        self.schema_version = schema_version
        self.strict_mode = strict_mode
        self.validate_vocabularies = validate_vocabularies
        self.validate_jsonld = validate_jsonld
        self.verify_signatures = verify_signatures
        self.enable_shacl = enable_shacl
        self.layers = layers or ["schema", "model", "semantic"]
        self._load_plugins = load_plugins
        self.max_input_size = (
            max_input_size if max_input_size is not None else self.DEFAULT_MAX_INPUT_SIZE
        )

        # Defer validator initialization if auto-detecting
        self._schema_validator: SchemaValidator | None = None
        self._model_validator: ModelValidator | None = None
        self._semantic_validator: SemanticValidator | None = None
        self._jsonld_validator: Any = None  # JSONLDValidator (optional)
        self._credential_verifier: Any = None  # CredentialVerifier (optional)

        if not self._auto_detect:
            self._init_validators(schema_version)

        # Initialize vocabulary loader if needed
        self._vocab_loader = None
        if validate_vocabularies:
            self._init_vocabulary_loader()

        # Initialize credential verifier if needed
        if verify_signatures:
            self._init_credential_verifier()

        # Initialize plugin registry if needed
        self._plugin_registry = None
        if load_plugins:
            self._init_plugin_registry()

    def _init_validators(self, version: str) -> None:
        """Initialize validators for a specific schema version.

        Args:
            version: Schema version string

        """
        self._schema_validator = SchemaValidator(version, strict=self.strict_mode)
        self._model_validator = ModelValidator(version)
        self._semantic_validator = SemanticValidator(version)

        # Initialize JSON-LD validator if enabled
        if self.validate_jsonld or "jsonld" in self.layers:
            self._init_jsonld_validator(version)

    def _init_jsonld_validator(self, version: str) -> None:
        """Initialize JSON-LD semantic validator.

        Args:
            version: Schema version string

        """
        try:
            from dppvalidator.validators.jsonld_semantic import JSONLDValidator

            self._jsonld_validator = JSONLDValidator(
                schema_version=version,
                strict=self.strict_mode,
            )
            logger.debug("JSON-LD validator initialized")
        except ImportError:
            logger.warning(
                "pyld import failed - JSON-LD validation disabled. "
                "Try: pip install --force-reinstall dppvalidator"
            )

    def _init_vocabulary_loader(self) -> None:
        """Initialize the vocabulary loader for external vocabulary validation."""
        try:
            from dppvalidator.vocabularies.loader import VocabularyLoader

            self._vocab_loader = VocabularyLoader(offline_mode=False)
            logger.debug("Vocabulary loader initialized")
        except ImportError:
            logger.warning("Vocabulary loader not available")

    def _init_credential_verifier(self) -> None:
        """Initialize the credential verifier for VC signature verification."""
        try:
            from dppvalidator.verifier.verifier import CredentialVerifier

            self._credential_verifier = CredentialVerifier()
            logger.debug("Credential verifier initialized")
        except ImportError:
            logger.warning(
                "cryptography import failed - signature verification disabled. "
                "Try: pip install --force-reinstall dppvalidator"
            )

    def _init_plugin_registry(self) -> None:
        """Initialize the plugin registry for plugin validators.

        Uses the singleton registry via get_default_registry() to avoid
        redundant plugin discovery when multiple ValidationEngine instances
        are created.
        """
        try:
            from dppvalidator.plugins.registry import get_default_registry

            self._plugin_registry = get_default_registry()
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

        # Auto-detect schema version if enabled
        effective_version = self.schema_version
        if self._auto_detect:
            effective_version = detect_schema_version(parsed_data)
            self._init_validators(effective_version)
            logger.debug("Auto-detected schema version: %s", effective_version)

        parse_time = (time.perf_counter() - start_time) * 1000
        context = ValidationContext(
            parsed_data=parsed_data,
            schema_version=effective_version,
            strict_mode=self.strict_mode,
            fail_fast=fail_fast,
            max_errors=max_errors,
        )
        context.result.parse_time_ms = parse_time

        # VER001: when the user explicitly configured a version (NOT
        # auto-detect) and the payload itself declares a different version
        # via ``$schema`` or ``@context`` URLs, fail fast. UNTPBaseModel
        # has ``extra="allow"``, so without this check a mis-versioned
        # payload would silently lose fields. See plan §4.1.7.
        if not self._auto_detect:
            declared = detect_declared_version(parsed_data)
            if declared is not None and declared != effective_version:
                context.result.errors.append(
                    ValidationError(
                        path="$",
                        message=(
                            f"Payload declares UNTP version {declared!r} but the engine is "
                            f"configured for {effective_version!r}. Re-run with "
                            f"`schema_version={declared!r}` (or `schema_version='auto'`) "
                            "to validate against the version the payload actually claims."
                        ),
                        code="VER001",
                        layer="engine",
                        severity="error",
                        context={
                            "declared_version": declared,
                            "configured_version": effective_version,
                        },
                    ),
                )
                context.result.valid = False
                context.result.schema_version = effective_version
                return context.result

        # Build and execute validation layers
        validation_layers = self._build_layers(effective_version)
        for layer in validation_layers:
            if layer.should_run(context):
                layer_result = layer.execute(context)
                context.merge_result(layer_result)
                self._apply_signature_fields(context.result, layer_result, layer)
                if context.should_stop():
                    break

        context.result.passport = context.passport
        return context.result

    def _build_layers(self, schema_version: str) -> list[ValidationLayer]:
        """Build the ordered list of validation layers based on configuration."""
        layers: list[ValidationLayer] = []

        if "schema" in self.layers:
            layers.append(SchemaLayer(self._schema_validator))

        if "model" in self.layers:
            layers.append(ModelLayer(self._model_validator))

        if "semantic" in self.layers:
            layers.append(SemanticLayer(self._semantic_validator))

        if "jsonld" in self.layers or self.validate_jsonld:
            layers.append(JsonLdLayer(self._jsonld_validator))

        if self.validate_vocabularies:
            layers.append(VocabularyLayer(self._vocab_loader, schema_version))

        if self._load_plugins:
            layers.append(PluginLayer(self._plugin_registry, schema_version))

        if self.verify_signatures:
            layers.append(SignatureLayer(self._credential_verifier, schema_version))

        return layers

    def _apply_signature_fields(
        self,
        result: ValidationResult,
        layer_result: ValidationResult,
        layer: ValidationLayer,
    ) -> None:
        """Copy signature verification fields from SignatureLayer result."""
        if layer.name == "signature":
            result.signature_valid = layer_result.signature_valid
            result.issuer_did = layer_result.issuer_did
            result.verification_method = layer_result.verification_method

    def validate_file(self, path: Path | str) -> ValidationResult:
        """Validate a JSON file.

        Args:
            path: Path to JSON file

        Returns:
            ValidationResult

        """
        return self.validate(Path(path))

    async def validate_async(self, data: dict[str, Any]) -> ValidationResult:
        """Validate data asynchronously (thread-offloaded).

        This method wraps the synchronous `validate()` method using
        `asyncio.to_thread()` to avoid blocking the event loop. Use this
        for integrating with async frameworks like FastAPI or aiohttp.

        Note:
            For natively async operations (network I/O), use `validate_deep()`
            which uses httpx.AsyncClient for non-blocking HTTP requests.

        Args:
            data: Raw JSON dict

        Returns:
            ValidationResult

        Example:
            >>> async def handler(request):
            ...     result = await engine.validate_async(request.json())
            ...     return {"valid": result.valid}

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

    async def validate_deep(
        self,
        data: dict[str, Any],
        *,
        max_depth: int = 3,
        follow_links: list[str] | None = None,
        timeout: float = 30.0,
        auth_header: dict[str, str] | None = None,
    ) -> DeepValidationResult:
        """Perform deep/recursive validation following linked documents.

        Crawls the supply chain by following links in the DPP and validates
        each linked document, building a complete validation graph.

        Args:
            data: Root DPP document data
            max_depth: Maximum depth to traverse (0 = root only)
            follow_links: JSON paths to follow for links (uses defaults if None)
            timeout: HTTP request timeout in seconds
            auth_header: Authorization headers for authenticated requests

        Returns:
            DeepValidationResult with all validation results and link graph

        """
        from dppvalidator.validators.deep import DeepValidator

        def validator_factory() -> ValidationEngine:
            return ValidationEngine(
                schema_version=self.schema_version,
                strict_mode=self.strict_mode,
                validate_vocabularies=self.validate_vocabularies,
                validate_jsonld=self.validate_jsonld,
                verify_signatures=self.verify_signatures,
                load_plugins=self._load_plugins,
            )

        deep_validator = DeepValidator(
            validator_factory=validator_factory,
            max_depth=max_depth,
            follow_links=follow_links,
            timeout=timeout,
            auth_header=auth_header,
        )

        return await deep_validator.validate(data)

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
                # Check file size before reading (DoS protection)
                if self.max_input_size > 0:
                    try:
                        file_size = data.stat().st_size
                        if file_size > self.max_input_size:
                            return ValidationResult(
                                valid=False,
                                errors=[
                                    ValidationError(
                                        path="$",
                                        message=(
                                            f"File size ({file_size:,} bytes) exceeds maximum "
                                            f"allowed ({self.max_input_size:,} bytes)."
                                        ),
                                        code="PRS005",
                                        layer="model",
                                        severity="error",
                                    )
                                ],
                                schema_version=self.schema_version,
                            )
                    except OSError:
                        pass  # File doesn't exist yet, will be caught below

                return json.loads(data.read_text(encoding="utf-8"))
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
