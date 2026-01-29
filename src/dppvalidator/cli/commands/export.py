"""Export command for CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

logger = get_logger(__name__)

EXIT_VALID = 0
EXIT_ERROR = 2


def add_parser(subparsers: Any) -> argparse.ArgumentParser:
    """Add export subparser."""
    parser = subparsers.add_parser(
        "export",
        help="Export a Digital Product Passport",
        description="Export a validated DPP to different formats",
    )
    parser.add_argument(
        "input",
        help="Input file path",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["jsonld", "json"],
        default="jsonld",
        help="Output format (default: jsonld)",
    )
    parser.add_argument(
        "--schema-version",
        default="0.6.1",
        help="Schema version (default: 0.6.1)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact output (no indentation)",
    )
    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute export command."""
    from dppvalidator.exporters import JSONExporter, JSONLDExporter
    from dppvalidator.validators import ValidationEngine

    data = _load_input(args.input, console)
    if data is None:
        return EXIT_ERROR

    engine = ValidationEngine(schema_version=args.schema_version)
    result = engine.validate(data)

    if not result.valid:
        console.print_error("Input is not a valid DPP")
        for err in result.errors[:5]:
            console.print(f"  {err.path}: {err.message}")
        return EXIT_ERROR

    if result.passport is None:
        console.print_error("Failed to parse passport")
        return EXIT_ERROR

    indent = None if args.compact else 2

    if args.format == "jsonld":
        exporter = JSONLDExporter(version=args.schema_version)
        output = exporter.export(result.passport, indent=indent)
    else:
        exporter = JSONExporter()
        output = exporter.export(result.passport, indent=indent)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        console.print_success(f"Exported to: {args.output}")
    else:
        console.print(output)

    return EXIT_VALID


def _load_input(input_path: str, console: Console) -> dict[str, Any] | None:
    """Load input data from file."""
    try:
        path = Path(input_path)
        if not path.exists():
            logger.error("File not found: %s", input_path)
            console.print_error(f"File not found: {input_path}")
            return None
        content = path.read_text()
        return json.loads(content)

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON: %s", e)
        console.print_error(f"Invalid JSON: {e}")
        return None
    except Exception as e:
        logger.exception("Unexpected error loading input")
        console.print_error(str(e))
        return None
