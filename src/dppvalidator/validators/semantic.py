"""Semantic validation layer (Layer 3)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal

from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION, SchemaFamily
from dppvalidator.validators.results import ValidationError, ValidationResult
from dppvalidator.validators.rules import ALL_RULES, ALL_RULES_BY_VERSION

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


def _load_cirpass_rules_by_version() -> dict[str, tuple[object, ...]]:
    """Lazy loader for the CIRPASS rule set.

    Phase 4 task 4.7 of [docs/plans/CIRPASS_2_MIGRATION.md]. The
    cross-cutting workstream X3 (cold-start budget) requires that
    importing the top-level package not pull the CIRPASS surface;
    that contract is pinned by ``tests/unit/test_cold_start_import.py``.
    Resolution happens inside this function rather than at module
    import time so the CIRPASS rule package is only loaded when
    the engine actually routes a payload to the CIRPASS pipeline.
    """
    from dppvalidator.validators.rules.cirpass_v1_3 import (
        ALL_RULES_BY_VERSION_CIRPASS,
    )

    return ALL_RULES_BY_VERSION_CIRPASS


class SemanticValidator:
    """Semantic validation layer for business rules.

    Applies domain-specific validation rules that go beyond
    schema and type validation. Rule-set selection is
    **family-and-version-aware**: when ``rules`` is left at the
    default ``None``, the validator picks the right rule set based
    on ``(family, schema_version)``. This is what stops the v0.6
    ``CQ001`` rule from firing as a false positive on a v0.7
    payload, and what stops UNTP rules from firing on a CIRPASS
    payload (see Phase 4 of docs/plans/CIRPASS_2_MIGRATION.md).
    """

    name: str = "semantic"
    layer: str = "semantic"

    def __init__(
        self,
        schema_version: str = DEFAULT_SCHEMA_VERSION,
        rules: list[Any] | None = None,
        family: SchemaFamily = SchemaFamily.UNTP,
        profile: str | None = None,
        strict_role_enum: bool = False,
    ) -> None:
        """Initialize semantic validator.

        Args:
            schema_version: Schema version. Used (with ``family``) to
                pick the appropriate rule set when ``rules`` is ``None``.
            rules: Custom rules list. If supplied, it overrides the
                version-keyed dispatch — callers can still inject a
                hand-curated subset for tests or plugin scenarios.
                If ``None``, the family-aware dispatch runs.
            family: Schema family. Phase 4 of the CIRPASS-2 migration
                added this axis so the validator can pick the CIRPASS
                rule set instead of the UNTP set. Defaults to
                ``SchemaFamily.UNTP`` for back-compat with pre-Phase-4
                callers.
            profile: Optional pilot profile name (Phase 7 of the
                migration plan). When set to a key registered in
                :data:`TEXTILE_PROFILES`, the validator *appends* the
                profile's rules to the resolved base set. ``None``
                (default) means no profile is applied — pre-Phase-7
                back-compat.
        """
        self.schema_version = schema_version
        self.family = family
        self.profile = profile
        # Phase 9 task 9.8: when True, PRT001 severity is upgraded
        # from ``info`` to ``error`` at emit-time so consumers can
        # opt into schema-strict PartyRole.role enforcement at the
        # engine boundary without mutating the rule object itself.
        self.strict_role_enum = strict_role_enum
        # Annotated explicitly because the family-aware dispatch can
        # populate ``self.rules`` from either ``ALL_RULES_BY_VERSION``
        # (UNTP — typed as ``list[<UNTP rule classes>]``) or the
        # CIRPASS dispatch (typed as ``tuple[object, ...]`` cast to
        # list). All rule objects share a duck-typed
        # ``check(passport)`` / ``rule_id`` surface; ``Any`` keeps ty
        # from collapsing to the narrower intersection.
        self.rules: list[Any]
        if rules is not None:
            self.rules = rules
        elif family is SchemaFamily.CIRPASS:
            cirpass_rules_by_version = _load_cirpass_rules_by_version()
            self.rules = list(cirpass_rules_by_version.get(schema_version, ()))
        else:
            self.rules = list(ALL_RULES_BY_VERSION.get(schema_version, ALL_RULES))

        # Phase 7 task 7.2: profile rule-pack swap. When ``profile``
        # names a textile profile (``textile-v1`` / ``textile-v2``),
        # we *replace* the v1 textile rules already in the base set
        # with the chosen profile's pack. This keeps the rule-set
        # cardinal and avoids running two textile packs against the
        # same payload.
        if profile is not None:
            from dppvalidator.validators.rules import TEXTILE_PROFILES

            profile_rules = TEXTILE_PROFILES.get(profile)
            if profile_rules is not None:
                # Drop any rule whose ID starts with ``TXT`` from the
                # base set; the profile owns those.
                self.rules = [
                    r for r in self.rules if not getattr(r, "rule_id", "").startswith("TXT")
                ]
                self.rules.extend(profile_rules)

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

            # Phase 9 task 9.8: opt-in PRT001 severity upgrade. The rule
            # itself remains ``info`` (informational by default); the
            # engine-level flag promotes the emitted ValidationErrors to
            # ``error`` so strict-mode consumers see the gradient gap as
            # a hard failure.
            if self.strict_role_enum and getattr(rule, "rule_id", "") == "PRT001":
                severity = "error"

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
