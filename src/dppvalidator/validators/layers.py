"""Validation layer abstractions following the Strategy Pattern.

This module provides the ValidationContext and ValidationLayer protocol
for decoupling validation logic from the engine orchestration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from dppvalidator.validators.protocols import Validator
from dppvalidator.validators.results import ValidationError, ValidationResult

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport
    from dppvalidator.plugins.registry import PluginRegistry
    from dppvalidator.validators.semantic import SemanticValidator
    from dppvalidator.verifier.verifier import CredentialVerifier
    from dppvalidator.vocabularies.loader import VocabularyLoader


@dataclass
class ValidationContext:
    """Shared context passed through validation layers.

    Holds the current validation state and configuration, enabling
    layers to access shared data without tight coupling.
    """

    parsed_data: dict[str, Any]
    schema_version: str
    strict_mode: bool = False
    fail_fast: bool = False
    max_errors: int = 100

    passport: DigitalProductPassport | None = None
    result: ValidationResult = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the result after dataclass init."""
        self.result = ValidationResult(
            valid=True,
            schema_version=self.schema_version,
        )

    def merge_result(self, layer_result: ValidationResult) -> None:
        """Merge a layer's result into the cumulative result."""
        self.result = self.result.merge(layer_result)
        if layer_result.passport is not None:
            self.passport = layer_result.passport

    def should_stop(self) -> bool:
        """Check if validation should stop early."""
        if self.fail_fast and not self.result.valid:
            return True
        return self.result.error_count >= self.max_errors


class ValidationLayer(ABC):
    """Abstract base class for validation layers (Strategy Pattern).

    Each layer encapsulates a single validation responsibility,
    following the Single Responsibility Principle.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this layer."""

    @abstractmethod
    def should_run(self, context: ValidationContext) -> bool:
        """Determine if this layer should execute given the context."""

    @abstractmethod
    def execute(self, context: ValidationContext) -> ValidationResult:
        """Execute validation and return results."""


class SchemaLayer(ValidationLayer):
    """JSON Schema validation layer."""

    def __init__(self, validator: Validator | None) -> None:
        self._validator = validator

    @property
    def name(self) -> str:
        return "schema"

    def should_run(self, context: ValidationContext) -> bool:  # noqa: ARG002
        return self._validator is not None

    def execute(self, context: ValidationContext) -> ValidationResult:
        if self._validator is None:
            return ValidationResult(valid=True, schema_version=context.schema_version)
        return self._validator.validate(context.parsed_data)


class ModelLayer(ValidationLayer):
    """Pydantic model validation layer."""

    def __init__(self, validator: Validator | None) -> None:
        self._validator = validator

    @property
    def name(self) -> str:
        return "model"

    def should_run(self, context: ValidationContext) -> bool:  # noqa: ARG002
        return self._validator is not None

    def execute(self, context: ValidationContext) -> ValidationResult:
        if self._validator is None:
            return ValidationResult(valid=True, schema_version=context.schema_version)
        result = self._validator.validate(context.parsed_data)
        if result.passport is not None:
            context.passport = result.passport
        return result


class SemanticLayer(ValidationLayer):
    """Business rules semantic validation layer."""

    def __init__(self, validator: SemanticValidator | None) -> None:
        self._validator = validator

    @property
    def name(self) -> str:
        return "semantic"

    def should_run(self, context: ValidationContext) -> bool:
        return self._validator is not None and context.passport is not None

    def execute(self, context: ValidationContext) -> ValidationResult:
        if self._validator is None or context.passport is None:
            return ValidationResult(valid=True, schema_version=context.schema_version)
        return self._validator.validate(context.passport)


class JsonLdLayer(ValidationLayer):
    """JSON-LD context expansion and term validation layer."""

    def __init__(self, validator: Validator | None) -> None:
        self._validator = validator

    @property
    def name(self) -> str:
        return "jsonld"

    def should_run(self, context: ValidationContext) -> bool:  # noqa: ARG002
        return self._validator is not None

    def execute(self, context: ValidationContext) -> ValidationResult:
        if self._validator is None:
            return ValidationResult(valid=True, schema_version=context.schema_version)
        return self._validator.validate(context.parsed_data)


class VocabularyLayer(ValidationLayer):
    """External vocabulary validation layer."""

    def __init__(self, loader: VocabularyLoader | None, schema_version: str) -> None:
        self._loader = loader
        self._schema_version = schema_version

    @property
    def name(self) -> str:
        return "vocabulary"

    def should_run(self, context: ValidationContext) -> bool:
        return self._loader is not None and context.passport is not None

    def execute(self, context: ValidationContext) -> ValidationResult:
        if context.passport is None:
            return ValidationResult(valid=True, schema_version=self._schema_version)

        warnings: list[ValidationError] = []
        passport = context.passport

        if passport.credential_subject and passport.credential_subject.materials_provenance:
            for i, material in enumerate(passport.credential_subject.materials_provenance):
                origin = getattr(material, "origin_country", None)
                if (
                    origin
                    and self._loader is not None
                    and not self._loader.is_valid_country(origin)
                ):
                    warnings.append(
                        ValidationError(
                            path=f"$.credentialSubject.materialsProvenance[{i}].originCountry",
                            message=f"Invalid country code: '{origin}'",
                            code="VOC001",
                            layer="vocabulary",
                            severity="warning",
                            suggestion="Use ISO 3166-1 alpha-2 country codes",
                        )
                    )

        if passport.credential_subject and passport.credential_subject.product:
            product = passport.credential_subject.product
            dims = getattr(product, "dimensions", None)
            if dims:
                for field_name in ["weight", "length", "width", "height", "volume"]:
                    measure = getattr(dims, field_name, None)
                    unit = getattr(measure, "unit", None) if measure else None
                    if unit and self._loader is not None and not self._loader.is_valid_unit(unit):
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
            valid=True,
            warnings=warnings,
            schema_version=self._schema_version,
        )


class PluginLayer(ValidationLayer):
    """Plugin validators execution layer."""

    def __init__(self, registry: PluginRegistry | None, schema_version: str) -> None:
        self._registry = registry
        self._schema_version = schema_version

    @property
    def name(self) -> str:
        return "plugin"

    def should_run(self, context: ValidationContext) -> bool:
        return self._registry is not None and context.passport is not None

    def execute(self, context: ValidationContext) -> ValidationResult:
        if context.passport is None:
            return ValidationResult(valid=True, schema_version=self._schema_version)

        if self._registry is None:
            return ValidationResult(valid=True, schema_version=self._schema_version)
        plugin_errors = self._registry.run_all_validators(context.passport)

        errors = [e for e in plugin_errors if e.severity == "error"]
        warnings = [e for e in plugin_errors if e.severity == "warning"]
        info = [e for e in plugin_errors if e.severity == "info"]

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
            schema_version=self._schema_version,
        )


class SignatureLayer(ValidationLayer):
    """Verifiable Credential signature verification layer."""

    def __init__(self, verifier: CredentialVerifier | None, schema_version: str) -> None:
        self._verifier = verifier
        self._schema_version = schema_version

    @property
    def name(self) -> str:
        return "signature"

    def should_run(self, context: ValidationContext) -> bool:  # noqa: ARG002
        return self._verifier is not None

    def execute(self, context: ValidationContext) -> ValidationResult:
        if self._verifier is None:
            return ValidationResult(valid=True, schema_version=self._schema_version)
        vc_result = self._verifier.verify(context.parsed_data)

        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        for error_msg in vc_result.errors:
            errors.append(
                ValidationError(
                    path="$.proof",
                    message=error_msg,
                    code="VC001",
                    layer="semantic",
                    severity="error",
                    suggestion="Check issuer DID and proof signature",
                    docs_url="https://artiso-ai.github.io/dppvalidator/errors/VC001",
                )
            )

        for warning_msg in vc_result.warnings:
            warnings.append(
                ValidationError(
                    path="$.proof",
                    message=warning_msg,
                    code="VC002",
                    layer="semantic",
                    severity="warning",
                )
            )

        result = ValidationResult(
            valid=vc_result.valid and len(errors) == 0,
            errors=errors,
            warnings=warnings,
            schema_version=self._schema_version,
        )
        result.signature_valid = vc_result.signature_valid
        result.issuer_did = vc_result.issuer_did
        result.verification_method = vc_result.verification_method

        return result
