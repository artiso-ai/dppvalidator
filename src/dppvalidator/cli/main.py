"""Command-line interface for dppvalidator."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import NoReturn

from dppvalidator.cli.commands import completions, doctor, export, init, schema, validate, watch
from dppvalidator.cli.console import Console
from dppvalidator.logging import configure_logging

EXIT_VALID = 0
EXIT_INVALID = 1
EXIT_ERROR = 2

# Command handler type: (args, console) -> exit_code
CommandHandler = Callable[[argparse.Namespace, Console], int]

# Command dispatch table
COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "validate": validate.run,
    "export": export.run,
    "schema": schema.run,
    "init": init.run,
    "doctor": doctor.run,
    "watch": watch.run,
    "completions": lambda args, _: completions.run(args),
}


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="dppvalidator",
        description="Validate and export Digital Product Passports (UNTP DPP)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dppvalidator validate passport.json
  dppvalidator validate passport.json --strict --format json
  cat passport.json | dppvalidator validate -
  dppvalidator export passport.json -o output.jsonld
  dppvalidator schema list
        """,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Show version and exit",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-essential output",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    validate.add_parser(subparsers)
    export.add_parser(subparsers)
    schema.add_parser(subparsers)
    init.add_parser(subparsers)
    doctor.add_parser(subparsers)
    watch.add_parser(subparsers)
    completions.add_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code: 0=valid, 1=invalid, 2=error
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    configure_logging(quiet=args.quiet, verbose=args.verbose)
    console = Console(quiet=args.quiet)

    if args.version:
        from dppvalidator import __version__

        console.print(f"dppvalidator {__version__}")
        return EXIT_VALID

    if args.command is None:
        parser.print_help()
        return EXIT_VALID

    try:
        handler = COMMAND_HANDLERS.get(args.command)
        if handler:
            return handler(args, console)
        parser.print_help()
        return EXIT_ERROR

    except KeyboardInterrupt:
        console.print_error("Interrupted")
        return EXIT_ERROR
    except Exception as e:
        if args.verbose:
            import traceback

            traceback.print_exc()
        else:
            console.print_error(str(e))
        return EXIT_ERROR


def cli() -> NoReturn:
    """CLI entry point that exits with proper code."""
    sys.exit(main())


if __name__ == "__main__":
    cli()
