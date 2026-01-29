"""Protocol definitions for dependency injection and testability."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dppvalidator.models.base import UNTPBaseModel


@runtime_checkable
class JSONLDSerializable(Protocol):
    """Protocol for models that can be serialized to JSON-LD."""

    def to_jsonld(
        self,
        *,
        include_context: bool = False,
        context_urls: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """Serialize to JSON-LD format."""
        ...


@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can be validated."""

    def model_validate(self, obj: Any) -> UNTPBaseModel:
        """Validate and parse input data."""
        ...


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for entities with an ID."""

    @property
    def id(self) -> str:
        """Unique identifier (typically a URI)."""
        ...


@runtime_checkable
class Named(Protocol):
    """Protocol for entities with a name."""

    @property
    def name(self) -> str:
        """Human-readable name."""
        ...
