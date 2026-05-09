"""Export command for CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.cli._io import load_input as _load_input
from dppvalidator.logging import get_logger
from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

logger = get_logger(__name__)

EXIT_VALID = 0
EXIT_ERROR = 2
# Phase 6 task 6.7 — additional exit codes; see
# docs/reference/cli/exit-codes.md for the full table.
EXIT_IO_ERROR = 5


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
        choices=["jsonld", "json", "eudpp-jsonld", "cirpass-jsonld"],
        default="jsonld",
        help=(
            "Output format. ``json`` and ``jsonld`` are pre-Phase-6 "
            "and emit the UNTP shape. ``eudpp-jsonld`` re-keys the "
            "UNTP payload onto canonical EUDPP v1.9.1 IRIs. "
            "``cirpass-jsonld`` projects onto the CIRPASS reference-"
            "structure v1.3.0 shape (Phase 5 forward shim runs "
            "automatically when the input is a UNTP envelope)."
        ),
    )
    parser.add_argument(
        "--default-language",
        default="en",
        help=(
            "BCP-47 tag used by ``--format=cirpass-jsonld`` when "
            "wrapping UNTP scalar names as CIRPASS LocalisedText "
            "entries. Default: en."
        ),
    )
    parser.add_argument(
        "--schema-version",
        default="auto",
        help=(
            "UNTP DPP schema version. Defaults to 'auto' — detected "
            "from the payload's $schema or @context. Default-version "
            f"fallback when detection finds nothing: {DEFAULT_SCHEMA_VERSION}."
        ),
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact output (no indentation)",
    )
    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute export command."""
    from dppvalidator.exporters import (
        CIRPASSJsonLDExporter,
        EUDPPJsonLDExporter,
        JSONExporter,
        JSONLDExporter,
    )
    from dppvalidator.validators import ValidationEngine

    data = _load_input(args.input, console)
    if data is None:
        return EXIT_IO_ERROR

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

    # When the user passed --schema-version=auto (the default), the
    # validator resolved a concrete version into ``result.schema_version``.
    # Use that for the exporter so the output's @context URL matches the
    # payload's actual version, not the literal 'auto' sentinel.
    resolved_version = result.schema_version or args.schema_version
    default_language = getattr(args, "default_language", "en")

    if args.format == "jsonld":
        jsonld_exporter = JSONLDExporter(version=resolved_version)
        output = jsonld_exporter.export(result.passport, indent=indent)
    elif args.format == "eudpp-jsonld":
        eudpp_exporter = EUDPPJsonLDExporter(schema_version=resolved_version)
        output = eudpp_exporter.export(result.passport, indent=indent)
    elif args.format == "cirpass-jsonld":
        # The CIRPASS exporter accepts both UNTP envelopes (forward-
        # shimmed) and native CIRPASS passports. Either way the
        # output is a CIRPASS reference-structure v1.3.0 message
        # with the EUDPP v1.9.1 context attached.
        cirpass_exporter = CIRPASSJsonLDExporter()
        output = cirpass_exporter.export(
            result.passport,
            indent=indent,
            default_language=default_language,
        )
        # Surface mapping warnings on stderr so the user knows what
        # was lossy / synthesised on the projection. Stderr (rather
        # than the Console object, which targets stdout) keeps the
        # JSON output on stdout pipe-clean for ``... | jq`` consumers.
        for w in cirpass_exporter.last_mapping_warnings:
            print(
                f"  [{w.code}] ({w.severity.value}) {w.path}: {w.message}",
                file=sys.stderr,
            )
    else:
        json_exporter = JSONExporter()
        output = json_exporter.export(result.passport, indent=indent)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        console.print_success(f"Exported to: {args.output}")
    else:
        # Use plain print for stdout to keep pipes clean (Rich would
        # inject ANSI escapes that break JSON consumers).
        print(output)

    return EXIT_VALID
