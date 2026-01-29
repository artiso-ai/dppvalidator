"""Protocol definitions for validation layers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dppvalidator.validators.results import ValidationResult


@runtime_checkable
class Validator(Protocol):
    """Protocol for validation layer implementations."""

    @property
    def name(self) -> str:
        """Unique name for this validator."""
        ...

    @property
    def layer(self) -> str:
        """Validation layer: 'schema', 'model', 'semantic', or 'plugin'."""
        ...

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate input data and return result."""
        ...


@runtime_checkable
class AsyncValidator(Protocol):
    """Protocol for async validation layer implementations."""

    @property
    def name(self) -> str:
        """Unique name for this validator."""
        ...

    @property
    def layer(self) -> str:
        """Validation layer: 'schema', 'model', 'semantic', or 'plugin'."""
        ...

    async def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate input data asynchronously and return result."""
        ...


@runtime_checkable
class SemanticRule(Protocol):
    """Protocol for individual semantic validation rules."""

    @property
    def rule_id(self) -> str:
        """Unique rule identifier (e.g., 'SEM001')."""
        ...

    @property
    def description(self) -> str:
        """Human-readable rule description."""
        ...

    @property
    def severity(self) -> str:
        """Default severity: 'error', 'warning', or 'info'."""
        ...

    def check(self, passport: Any) -> list[tuple[str, str]]:
        """Check the rule against a parsed passport.

        Returns:
            List of (json_path, error_message) tuples for violations.
        """
        ...
