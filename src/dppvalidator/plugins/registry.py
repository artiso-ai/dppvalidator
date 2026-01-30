"""Plugin registry for validators and exporters."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from dppvalidator.exporters.protocols import Exporter
from dppvalidator.logging import get_logger
from dppvalidator.plugins.discovery import discover_exporters, discover_validators
from dppvalidator.validators.protocols import SemanticRule
from dppvalidator.validators.results import ValidationError

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport

logger = get_logger(__name__)


class PluginRegistry:
    """Registry for validator and exporter plugins.

    Automatically discovers plugins via entry points on initialization,
    or allows manual registration for testing and custom setups.
    """

    def __init__(self, auto_discover: bool = True) -> None:
        """Initialize plugin registry.

        Args:
            auto_discover: If True, discover plugins via entry points
        """
        self._validators: dict[str, type[SemanticRule] | SemanticRule] = {}
        self._exporters: dict[str, type[Exporter] | Exporter] = {}

        if auto_discover:
            self._discover_all()

    def _discover_all(self) -> None:
        """Discover all plugins via entry points."""
        for name, validator in discover_validators():
            self._validators[name] = validator
            logger.info("Registered validator plugin: %s", name)

        for name, exporter in discover_exporters():
            self._exporters[name] = exporter
            logger.info("Registered exporter plugin: %s", name)

    def register_validator(self, name: str, validator: type[SemanticRule] | SemanticRule) -> None:
        """Register a validator plugin.

        Args:
            name: Unique name for the validator
            validator: Validator class or instance implementing SemanticRule protocol
        """
        self._validators[name] = validator
        logger.debug("Manually registered validator: %s", name)

    def register_exporter(self, name: str, exporter: type[Exporter] | Exporter) -> None:
        """Register an exporter plugin.

        Args:
            name: Unique name for the exporter
            exporter: Exporter class or instance implementing Exporter protocol
        """
        self._exporters[name] = exporter
        logger.debug("Manually registered exporter: %s", name)

    def unregister_validator(self, name: str) -> bool:
        """Unregister a validator plugin.

        Args:
            name: Name of validator to unregister

        Returns:
            True if validator was found and removed
        """
        return self._validators.pop(name, None) is not None

    def unregister_exporter(self, name: str) -> bool:
        """Unregister an exporter plugin.

        Args:
            name: Name of exporter to unregister

        Returns:
            True if exporter was found and removed
        """
        return self._exporters.pop(name, None) is not None

    def get_validator(self, name: str) -> type[SemanticRule] | SemanticRule | None:
        """Get a validator by name.

        Args:
            name: Validator name

        Returns:
            Validator or None if not found
        """
        return self._validators.get(name)

    def get_exporter(self, name: str) -> type[Exporter] | Exporter | None:
        """Get an exporter by name.

        Args:
            name: Exporter name

        Returns:
            Exporter or None if not found
        """
        return self._exporters.get(name)

    def run_all_validators(
        self,
        passport: DigitalProductPassport,
    ) -> list[ValidationError]:
        """Run all registered validator plugins.

        Args:
            passport: Parsed passport to validate

        Returns:
            List of validation errors from all plugins
        """
        errors: list[ValidationError] = []

        for name, validator in self._validators.items():
            try:
                instance = validator() if isinstance(validator, type) else validator

                if hasattr(instance, "check"):
                    violations = instance.check(passport)
                    rule_id = getattr(instance, "rule_id", f"PLG_{name.upper()}")
                    severity = getattr(instance, "severity", "error")

                    for path, message in violations:
                        errors.append(
                            ValidationError(
                                path=path,
                                message=message,
                                code=rule_id,
                                layer="plugin",
                                severity=severity,
                            )
                        )

            except (AttributeError, TypeError, ValueError, RuntimeError) as e:
                logger.warning("Plugin %s failed: %s", name, e)
                errors.append(
                    ValidationError(
                        path="$",
                        message=f"Plugin '{name}' failed: {e}",
                        code="PLG_ERROR",
                        layer="plugin",
                        severity="warning",
                    )
                )

        return errors

    @property
    def validator_names(self) -> list[str]:
        """List of registered validator names."""
        return list(self._validators.keys())

    @property
    def exporter_names(self) -> list[str]:
        """List of registered exporter names."""
        return list(self._exporters.keys())

    @property
    def validator_count(self) -> int:
        """Number of registered validators."""
        return len(self._validators)

    @property
    def exporter_count(self) -> int:
        """Number of registered exporters."""
        return len(self._exporters)


@lru_cache(maxsize=1)
def get_default_registry() -> PluginRegistry:
    """Get the default plugin registry (lazy initialization).

    Returns:
        Default PluginRegistry instance
    """
    return PluginRegistry(auto_discover=True)


def reset_default_registry() -> None:
    """Reset the default registry (useful for testing)."""
    get_default_registry.cache_clear()
