"""Semantic validation layer (Layer 3)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal

from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION
from dppvalidator.validators.results import ValidationError, ValidationResult
from dppvalidator.validators.rules import ALL_RULES, ALL_RULES_BY_VERSION

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class SemanticValidator:
    """Semantic validation layer for business rules.

    Applies domain-specific validation rules that go beyond
    schema and type validation. Rule-set selection is **version-aware**:
    when ``rules`` is left at the default ``None``, the validator looks
    up the right rule set in :data:`ALL_RULES_BY_VERSION` keyed on
    ``schema_version``. This is what stops the v0.6 ``CQ001`` rule from
    firing as a false positive on a v0.7 payload — see Phase 3b of
    docs/plans/UNTP_0.7.0_MIGRATION.md.
    """

    name: str = "semantic"
    layer: str = "semantic"

    def __init__(
        self,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
        rules: list[Any] | None = None,
    ) -> None:
        """Initialize semantic validator.

        Args:
            schema_version: UNTP DPP schema version. Used to pick the
                appropriate rule set from :data:`ALL_RULES_BY_VERSION`
                when ``rules`` is ``None``.
            rules: Custom rules list. If supplied, it overrides the
                version-keyed dispatch — callers can still inject a
                hand-curated subset for tests or plugin scenarios.
                If ``None``, the version-keyed lookup runs; if the
                version is unknown to the registry the dispatch falls
                back to :data:`ALL_RULES` (the default v0.6.x set).
        """
        self.schema_version = schema_version
        if rules is not None:
            self.rules = rules
        else:
            self.rules = ALL_RULES_BY_VERSION.get(schema_version, ALL_RULES)

    def validate(
        self,
        passport: DigitalProductPassport,
    ) -> ValidationResult:
        """Validate passport against semantic rules.

        Args:
            passport: Parsed DigitalProductPassport to validate

        Returns:
            ValidationResult with semantic violations
        """
        start_time = time.perf_counter()

        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        info: list[ValidationError] = []

        for rule in self.rules:
            violations = rule.check(passport)
            severity: Literal["error", "warning", "info"] = getattr(rule, "severity", "error")
            suggestion: str | None = getattr(rule, "suggestion", None)
            docs_url: str | None = getattr(rule, "docs_url", None)

            for path, message in violations:
                error = ValidationError(
                    path=path,
                    message=message,
                    code=rule.rule_id,
                    layer="semantic",
                    severity=severity,
                    suggestion=suggestion,
                    docs_url=docs_url,
                )

                if severity == "error":
                    errors.append(error)
                elif severity == "warning":
                    warnings.append(error)
                else:
                    info.append(error)

        validation_time = (time.perf_counter() - start_time) * 1000

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
            schema_version=self.schema_version,
            passport=passport,
            validation_time_ms=validation_time,
        )
