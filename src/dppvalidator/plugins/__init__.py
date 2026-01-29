"""Plugin architecture for extending dppvalidator."""

from dppvalidator.plugins.discovery import (
    EXPORTER_ENTRY_POINT,
    VALIDATOR_ENTRY_POINT,
    discover_exporters,
    discover_validators,
    list_available_plugins,
)
from dppvalidator.plugins.registry import (
    PluginRegistry,
    get_default_registry,
    reset_default_registry,
)

__all__ = [
    # Registry
    "PluginRegistry",
    "get_default_registry",
    "reset_default_registry",
    # Discovery
    "discover_validators",
    "discover_exporters",
    "list_available_plugins",
    # Constants
    "VALIDATOR_ENTRY_POINT",
    "EXPORTER_ENTRY_POINT",
]
