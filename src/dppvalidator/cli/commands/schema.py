"""Schema command for CLI."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger
from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION

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
        default=DEFAULT_SCHEMA_VERSION,
        help=f"Schema version to download (default: {DEFAULT_SCHEMA_VERSION})",
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
        default=DEFAULT_SCHEMA_VERSION,
        help=f"Schema version (default: {DEFAULT_SCHEMA_VERSION})",
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
    """List available schema versions registered in ``SCHEMA_REGISTRY``.

    Source of truth is ``SCHEMA_REGISTRY``; ``CONTEXTS`` is consulted for the
    JSON-LD context URLs of each version. Both are kept in lock-step — see
    docs/plans/UNTP_0.7.0_MIGRATION.md §Phase 1.
    """
    from dppvalidator.exporters.contexts import CONTEXTS
    from dppvalidator.schemas.registry import SCHEMA_REGISTRY, SchemaRegistry

    default_version = SchemaRegistry().default_version

    table = console.create_table(title="Available UNTP DPP Schema Versions")
    table.add_column("Version")
    table.add_column("Default", justify="center")
    table.add_column("Bundled", justify="center")
    table.add_column("Contexts")

    for version in sorted(SCHEMA_REGISTRY):
        schema = SCHEMA_REGISTRY[version]
        is_default = "✓" if version == default_version else ""
        # ``sha256 is not None`` is the proxy for "we ship this file in-tree";
        # versions without a hash are registered but rely on a custom path
        # being supplied at validate-time.
        is_bundled = "✓" if schema.sha256 is not None else ""
        ctx = CONTEXTS.get(version)
        contexts = ", ".join(ctx.contexts) if ctx else "(no @context registered)"
        table.add_row(version, is_default, is_bundled, contexts)

    console.print_table(table)
    return EXIT_VALID


def _download_schema(version: str, output_dir: str | None, console: Console) -> int:
    """Download a schema by version using the URL recorded in ``SCHEMA_REGISTRY``."""
    from pathlib import Path

    from dppvalidator.schemas.registry import SCHEMA_REGISTRY

    if version not in SCHEMA_REGISTRY:
        console.print_error(f"Unknown version: {version}")
        console.print(f"Available: {', '.join(sorted(SCHEMA_REGISTRY))}")
        return EXIT_ERROR

    try:
        import httpx
    except ImportError:
        console.print_error("httpx is required for schema download")
        console.print("Install with: pip install 'dppvalidator[http]'")
        return EXIT_ERROR

    schema_url = SCHEMA_REGISTRY[version].url

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
    """Show schema information for ``version`` from the registries."""
    from dppvalidator.exporters.contexts import CONTEXTS
    from dppvalidator.schemas.registry import SCHEMA_REGISTRY

    if version not in SCHEMA_REGISTRY:
        console.print_error(f"Unknown version: {version}")
        console.print(f"Available: {', '.join(sorted(SCHEMA_REGISTRY))}")
        return EXIT_ERROR

    schema = SCHEMA_REGISTRY[version]
    ctx = CONTEXTS.get(version)
    type_arr = ctx.default_type if ctx else ()
    sha = schema.sha256 or "(not bundled — fetched on demand)"

    info = f"""[bold]UNTP DPP Schema v{version}[/bold]

Type: {", ".join(type_arr) or "(no @context registered)"}

Contexts:
"""
    for url in ctx.contexts if ctx else ():
        info += f"  • {url}\n"
    info += f"\nSchema URL:\n  {schema.url}\n"
    info += f"\nSHA-256:\n  {sha}"

    console.print_panel(info, title=f"Schema v{version}")
    return EXIT_VALID
