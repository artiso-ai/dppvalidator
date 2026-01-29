"""Validate command for CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

logger = get_logger(__name__)

EXIT_VALID = 0
EXIT_INVALID = 1
EXIT_ERROR = 2


def add_parser(subparsers: Any) -> argparse.ArgumentParser:
    """Add validate subparser."""
    parser = subparsers.add_parser(
        "validate",
        help="Validate a Digital Product Passport",
        description="Validate a DPP JSON file against UNTP schema",
    )
    parser.add_argument(
        "input",
        help="Input file path or '-' for stdin",
    )
    parser.add_argument(
        "-s",
        "--strict",
        action="store_true",
        help="Enable strict JSON Schema validation",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "table"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--schema-version",
        default="0.6.1",
        help="Schema version (default: 0.6.1)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first error",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=100,
        help="Maximum errors to report (default: 100)",
    )
    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute validate command."""
    from dppvalidator.validators import ValidationEngine

    data = _load_input(args.input, console)
    if data is None:
        return EXIT_ERROR

    engine = ValidationEngine(
        schema_version=args.schema_version,
        strict_mode=args.strict,
    )

    result = engine.validate(
        data,
        fail_fast=args.fail_fast,
        max_errors=args.max_errors,
    )

    _output_result(result, args.format, args.input, console)

    return EXIT_VALID if result.valid else EXIT_INVALID


def _load_input(input_path: str, console: Console) -> dict[str, Any] | None:
    """Load input data from file or stdin."""
    try:
        if input_path == "-":
            content = sys.stdin.read()
        else:
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


def _output_result(result: Any, fmt: str, input_path: str, console: Console) -> None:
    """Output validation result in specified format."""
    if fmt == "json":
        console.print(result.to_json())
        return

    if fmt == "table":
        _output_table(result, input_path, console)
        return

    _output_text(result, input_path, console)


def _output_text(result: Any, input_path: str, console: Console) -> None:
    """Output result as text."""
    if result.valid:
        console.print(f"\n[bold green]✓ VALID[/bold green]: {input_path}", style="green")
    else:
        console.print(f"\n[bold red]✗ INVALID[/bold red]: {input_path}", style="red")

    console.print(f"Schema version: {result.schema_version}")

    if result.errors:
        console.print(f"\n[bold red]Errors ({len(result.errors)}):[/bold red]", style="red")
        for err in result.errors:
            console.print(f"  [{err.code}] {err.path}: {err.message}")
            if err.did_you_mean:
                suggestions = ", ".join(f'"{v}"' for v in err.did_you_mean)
                console.print(f"    Did you mean: {suggestions}?", style="cyan")
            if err.suggestion:
                console.print(f"    💡 {err.suggestion}", style="dim")
            if err.docs_url:
                console.print(f"    📖 {err.docs_url}", style="dim blue")

    if result.warnings:
        console.print(
            f"\n[bold yellow]Warnings ({len(result.warnings)}):[/bold yellow]", style="yellow"
        )
        for warn in result.warnings:
            console.print(f"  [{warn.code}] {warn.path}: {warn.message}")
            if warn.suggestion:
                console.print(f"    💡 {warn.suggestion}", style="dim")
            if warn.docs_url:
                console.print(f"    📖 {warn.docs_url}", style="dim blue")

    if result.info:
        console.print(f"\nInfo ({len(result.info)}):")
        for info in result.info:
            console.print(f"  [{info.code}] {info.path}: {info.message}")

    console.print(f"\nValidation time: {result.validation_time_ms:.2f}ms")


def _output_table(result: Any, input_path: str, console: Console) -> None:
    """Output result as table."""
    summary = console.create_table(title="Validation Result")
    summary.add_column("Status", style="bold")
    summary.add_column("Path")
    summary.add_column("Schema Version")

    status = "✓ VALID" if result.valid else "✗ INVALID"
    summary.add_row(status, input_path, result.schema_version)
    console.print_table(summary)

    if result.errors or result.warnings:
        issues = console.create_table(title="Issues")
        issues.add_column("Severity")
        issues.add_column("Code")
        issues.add_column("Path")
        issues.add_column("Message")

        for err in result.errors:
            issues.add_row("ERROR", err.code, err.path, err.message[:50])

        for warn in result.warnings:
            issues.add_row("WARNING", warn.code, warn.path, warn.message[:50])

        console.print_table(issues)
