"""JSON-LD export for Digital Product Passports with W3C VC v2 compliance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.exporters.contexts import DEFAULT_VERSION, ContextManager

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class JSONLDExporter:
    """Export DPP to JSON-LD with W3C VC v2 compliance.

    Produces valid JSON-LD output conforming to UNTP DPP specification
    and W3C Verifiable Credentials v2.
    """

    def __init__(self, version: str = DEFAULT_VERSION) -> None:
        """Initialize exporter.

        Args:
            version: Schema version for context resolution
        """
        self.version = version
        self._context_manager = ContextManager(version)

    def export(
        self,
        passport: DigitalProductPassport,
        *,
        indent: int | None = 2,
        include_type: bool = True,
    ) -> str:
        """Export passport to JSON-LD string.

        Args:
            passport: Validated DigitalProductPassport
            indent: JSON indentation (None for compact)
            include_type: Include type array in output

        Returns:
            JSON-LD formatted string
        """
        data = self._to_jsonld_dict(passport, include_type=include_type)
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def export_dict(
        self,
        passport: DigitalProductPassport,
        *,
        include_type: bool = True,
    ) -> dict[str, Any]:
        """Export passport to JSON-LD dictionary.

        Args:
            passport: Validated DigitalProductPassport
            include_type: Include type array in output

        Returns:
            JSON-LD formatted dictionary
        """
        return self._to_jsonld_dict(passport, include_type=include_type)

    def export_to_file(
        self,
        passport: DigitalProductPassport,
        path: Path | str,
        *,
        indent: int | None = 2,
    ) -> None:
        """Export passport to JSON-LD file.

        Args:
            passport: Validated DigitalProductPassport
            path: Output file path
            indent: JSON indentation
        """
        content = self.export(passport, indent=indent)
        Path(path).write_text(content, encoding="utf-8")

    def _to_jsonld_dict(
        self,
        passport: DigitalProductPassport,
        *,
        include_type: bool = True,
    ) -> dict[str, Any]:
        """Convert passport to JSON-LD dictionary.

        Args:
            passport: Validated DigitalProductPassport
            include_type: Include type array

        Returns:
            JSON-LD dictionary with @context and type
        """
        data = passport.to_jsonld(
            include_context=True,
            context_urls=tuple(self._context_manager.get_context()),
        )

        if include_type and "type" not in data:
            data["type"] = self._context_manager.get_type()

        return data


def export_jsonld(dpp: DigitalProductPassport, *, indent: int = 2) -> str:
    """Convert a valid DPP to JSON-LD format.

    Convenience function for simple exports. For more control,
    use JSONLDExporter directly.

    Args:
        dpp: Validated DigitalProductPassport
        indent: JSON indentation

    Returns:
        JSON-LD formatted string
    """
    exporter = JSONLDExporter()
    return exporter.export(dpp, indent=indent)
