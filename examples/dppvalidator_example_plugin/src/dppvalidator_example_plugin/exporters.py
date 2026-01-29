"""Example custom exporter for dppvalidator.

This exporter demonstrates how to create custom export formats
that are automatically discovered via Python entry points.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport


class CSVExporter:
    """Export DPP summary data to CSV format.

    This example exporter creates a simple CSV with key passport fields,
    useful for spreadsheet analysis or data integration.
    """

    def __init__(self, delimiter: str = ",") -> None:
        """Initialize CSV exporter.

        Args:
            delimiter: CSV field delimiter (default: comma)
        """
        self.delimiter = delimiter

    def export(self, passport: DigitalProductPassport) -> str:
        """Export passport to CSV string.

        Args:
            passport: Validated DigitalProductPassport

        Returns:
            CSV formatted string
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        # Header row
        writer.writerow(
            [
                "id",
                "issuer_id",
                "issuer_name",
                "valid_from",
                "valid_until",
                "product_id",
                "product_name",
                "materials_count",
            ]
        )

        # Data row
        product_id = ""
        product_name = ""
        materials_count = 0

        if passport.credential_subject:
            if passport.credential_subject.product:
                product_id = str(passport.credential_subject.product.id or "")
                product_name = passport.credential_subject.product.name or ""
            if passport.credential_subject.materials_provenance:
                materials_count = len(passport.credential_subject.materials_provenance)

        writer.writerow(
            [
                str(passport.id),
                str(passport.issuer.id),
                passport.issuer.name,
                passport.valid_from.isoformat() if passport.valid_from else "",
                passport.valid_until.isoformat() if passport.valid_until else "",
                product_id,
                product_name,
                materials_count,
            ]
        )

        return output.getvalue()

    def export_to_file(
        self,
        passport: DigitalProductPassport,
        path: Path | str,
    ) -> None:
        """Export passport to CSV file.

        Args:
            passport: Validated DigitalProductPassport
            path: Output file path
        """
        content = self.export(passport)
        Path(path).write_text(content, encoding="utf-8")
