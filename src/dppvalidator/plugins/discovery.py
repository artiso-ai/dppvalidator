"""Plugin discovery via Python entry points."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = get_logger(__name__)

VALIDATOR_ENTRY_POINT = "dppvalidator.validators"
EXPORTER_ENTRY_POINT = "dppvalidator.exporters"


def discover_validators() -> Iterator[tuple[str, Any]]:
    """Discover validator plugins via entry points.

    Yields:
        Tuples of (name, validator_class) for each discovered plugin
    """
    yield from _discover_plugins(VALIDATOR_ENTRY_POINT)


def discover_exporters() -> Iterator[tuple[str, Any]]:
    """Discover exporter plugins via entry points.

    Yields:
        Tuples of (name, exporter_class) for each discovered plugin
    """
    yield from _discover_plugins(EXPORTER_ENTRY_POINT)


def _discover_plugins(group: str) -> Iterator[tuple[str, Any]]:
    """Discover plugins from a specific entry point group.

    Args:
        group: Entry point group name

    Yields:
        Tuples of (name, loaded_object)
    """
    try:
        eps = entry_points(group=group)
    except TypeError:
        eps = entry_points().get(group, [])

    for ep in eps:
        try:
            plugin = ep.load()
            logger.debug("Discovered plugin: %s = %s", ep.name, ep.value)
            yield ep.name, plugin
        except (ImportError, AttributeError, TypeError) as e:
            logger.warning(
                "Failed to load plugin %s from %s: %s",
                ep.name,
                ep.value,
                e,
            )


def list_available_plugins() -> dict[str, list[str]]:
    """List all available plugins by category.

    Returns:
        Dictionary mapping category to list of plugin names
    """
    return {
        "validators": [name for name, _ in discover_validators()],
        "exporters": [name for name, _ in discover_exporters()],
    }
