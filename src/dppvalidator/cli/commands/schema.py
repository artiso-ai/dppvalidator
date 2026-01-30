"""Schema command for CLI."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

logger = get_logger(__name__)

EXIT_VALID = 0
EXIT_ERROR = 2


def add_parser(subparsers: Any) -> argparse.ArgumentParser:
    """Add schema subparser."""
    parser = subparsers.add_parser(
        "schema",
        help="Manage DPP schemas",
        description="List and download UNTP DPP schemas",
    )

    schema_subparsers = parser.add_subparsers(dest="schema_command")

    schema_subparsers.add_parser(
        "list",
        help="List available schema versions",
    )

    download_parser = schema_subparsers.add_parser(
        "download",
        help="Download a schema version",
    )
    download_parser.add_argument(
        "-v",
        "--version",
        default="0.6.1",
        help="Schema version to download (default: 0.6.1)",
    )
    download_parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: current directory)",
    )

    info_parser = schema_subparsers.add_parser(
        "info",
        help="Show schema information",
    )
    info_parser.add_argument(
        "-v",
        "--version",
        default="0.6.1",
        help="Schema version (default: 0.6.1)",
    )

    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute schema command."""
    if args.schema_command == "list":
        return _list_schemas(console)
    elif args.schema_command == "download":
        return _download_schema(args.version, args.output, console)
    elif args.schema_command == "info":
        return _show_info(args.version, console)
    else:
        console.print("Usage: dppvalidator schema {list|download|info}")
        return EXIT_ERROR


def _list_schemas(console: Console) -> int:
    """List available schema versions."""
    from dppvalidator.exporters.contexts import CONTEXTS, DEFAULT_VERSION

    table = console.create_table(title="Available UNTP DPP Schema Versions")
    table.add_column("Version")
    table.add_column("Default", justify="center")
    table.add_column("Contexts")

    for version, ctx in CONTEXTS.items():
        is_default = "✓" if version == DEFAULT_VERSION else ""
        contexts = ", ".join(ctx.contexts)
        table.add_row(version, is_default, contexts)

    console.print_table(table)
    return EXIT_VALID


def _download_schema(version: str, output_dir: str | None, console: Console) -> int:
    """Download schema for a version."""
    from pathlib import Path

    try:
        import httpx
    except ImportError:
        console.print_error("httpx is required for schema download")
        console.print("Install with: pip install 'dppvalidator[http]'")
        return EXIT_ERROR

    schema_url = f"https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-{version}.json"

    try:
        logger.info("Downloading schema %s from %s", version, schema_url)
        response = httpx.get(schema_url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()

        out_dir = Path(output_dir) if output_dir else Path.cwd()
        out_dir.mkdir(parents=True, exist_ok=True)

        out_file = out_dir / f"untp-dpp-schema-{version}.json"
        out_file.write_text(response.text, encoding="utf-8")

        console.print_success(f"Downloaded: {out_file}")
        return EXIT_VALID

    except Exception as e:
        logger.error("Failed to download schema: %s", e)
        console.print_error(f"Downloading schema: {e}")
        return EXIT_ERROR


def _show_info(version: str, console: Console) -> int:
    """Show schema information."""
    from dppvalidator.exporters.contexts import CONTEXTS

    if version not in CONTEXTS:
        console.print_error(f"Unknown version: {version}")
        console.print(f"Available: {', '.join(CONTEXTS.keys())}")
        return EXIT_ERROR

    ctx = CONTEXTS[version]
    schema_url = f"https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-{version}.json"

    info = f"""[bold]UNTP DPP Schema v{version}[/bold]

Type: {", ".join(ctx.default_type)}

Contexts:
"""
    for url in ctx.contexts:
        info += f"  • {url}\n"
    info += f"\nSchema URL:\n  {schema_url}"

    console.print_panel(info, title=f"Schema v{version}")
    return EXIT_VALID
