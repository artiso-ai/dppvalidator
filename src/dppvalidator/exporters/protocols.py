"""Protocol definitions for exporter plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


@runtime_checkable
class Exporter(Protocol):
    """Protocol for exporter implementations."""

    def export(
        self,
        passport: DigitalProductPassport,
        **kwargs: Any,
    ) -> str:
        """Export passport to string format.

        Args:
            passport: Validated DigitalProductPassport
            **kwargs: Format-specific options

        Returns:
            Exported string representation
        """
        ...
