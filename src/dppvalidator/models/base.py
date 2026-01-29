"""Base model for all UNTP entities with JSON-LD support."""

from __future__ import annotations

from typing import Annotated, Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class UNTPBaseModel(BaseModel):
    """Base model for all UNTP entities.

    Provides:
    - JSON-LD type support via _jsonld_type class variable and 'type' field
    - Flexible serialization with alias support
    - Extra field allowance per UNTP spec (additionalProperties: true)
    - W3C VC pattern support (accepts 'type' arrays from incoming JSON-LD)
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_default=True,
        extra="allow",
        str_strip_whitespace=True,
    )

    _jsonld_type: ClassVar[list[str]] = []

    # W3C VC type field - accepts type arrays from incoming JSON-LD
    type: Annotated[
        list[str] | None,
        Field(default=None, description="JSON-LD type(s) for this entity"),
    ]

    def to_jsonld(
        self,
        *,
        include_context: bool = False,
        context_urls: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """Serialize model to JSON-LD format.

        Args:
            include_context: If True, includes the @context field.
            context_urls: Context URLs to include when include_context is True.

        Returns:
            JSON-LD compatible dictionary with 'type' field.
        """
        data = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        if self._jsonld_type:
            data["type"] = self._jsonld_type.copy()
        if include_context and context_urls:
            data["@context"] = list(context_urls)
        return data


class UNTPStrictModel(UNTPBaseModel):
    """Strict base model that disallows additional properties.

    Used for models where additionalProperties: false in schema.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_default=True,
        extra="forbid",
        str_strip_whitespace=True,
    )
