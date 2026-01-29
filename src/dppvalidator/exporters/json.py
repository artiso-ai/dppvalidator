"""Plain JSON export for Digital Product Passports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class JSONExporter:
    """Export DPP to plain JSON without JSON-LD context.

    Useful for systems that don't support JSON-LD or need
    simplified output.
    """

    def __init__(self, exclude_none: bool = True) -> None:
        """Initialize exporter.

        Args:
            exclude_none: Exclude None values from output
        """
        self.exclude_none = exclude_none

    def export(
        self,
        passport: DigitalProductPassport,
        *,
        indent: int | None = 2,
        by_alias: bool = True,
    ) -> str:
        """Export passport to JSON string.

        Args:
            passport: Validated DigitalProductPassport
            indent: JSON indentation (None for compact)
            by_alias: Use field aliases in output (e.g., camelCase)

        Returns:
            JSON formatted string
        """
        data = self.export_dict(passport, by_alias=by_alias)
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def export_dict(
        self,
        passport: DigitalProductPassport,
        *,
        by_alias: bool = True,
    ) -> dict[str, Any]:
        """Export passport to dictionary.

        Args:
            passport: Validated DigitalProductPassport
            by_alias: Use field aliases in output

        Returns:
            Dictionary representation
        """
        return passport.model_dump(
            mode="json",
            by_alias=by_alias,
            exclude_none=self.exclude_none,
        )

    def export_to_file(
        self,
        passport: DigitalProductPassport,
        path: Path | str,
        *,
        indent: int | None = 2,
        by_alias: bool = True,
    ) -> None:
        """Export passport to JSON file.

        Args:
            passport: Validated DigitalProductPassport
            path: Output file path
            indent: JSON indentation
            by_alias: Use field aliases in output
        """
        content = self.export(passport, indent=indent, by_alias=by_alias)
        Path(path).write_text(content, encoding="utf-8")


def export_json(
    dpp: DigitalProductPassport,
    *,
    indent: int = 2,
    by_alias: bool = True,
) -> str:
    """Convert a valid DPP to JSON format.

    Convenience function for simple exports. For more control,
    use JSONExporter directly.

    Args:
        dpp: Validated DigitalProductPassport
        indent: JSON indentation
        by_alias: Use field aliases in output

    Returns:
        JSON formatted string
    """
    exporter = JSONExporter()
    return exporter.export(dpp, indent=indent, by_alias=by_alias)
