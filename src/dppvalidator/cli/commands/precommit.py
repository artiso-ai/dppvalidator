"""Pre-commit hook entry point for dppvalidator."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from dppvalidator.cli.console import Console
from dppvalidator.logging import get_logger
from dppvalidator.validators import ValidationEngine

logger = get_logger(__name__)
console = Console()


def main(argv: Sequence[str] | None = None) -> int:
    """Pre-commit hook entry point.

    Validates DPP JSON files passed as arguments.
    Returns 0 if all files are valid, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Pre-commit hook for DPP validation",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to validate",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args(argv)

    if not args.files:
        return 0

    engine = ValidationEngine(strict_mode=args.strict)
    failed = False

    for filepath in args.files:
        path = Path(filepath)
        if not path.exists():
            logger.error("File not found: %s", filepath)
            failed = True
            continue

        if path.suffix.lower() != ".json":
            continue

        result = engine.validate_file(path)

        if not result.valid:
            console.print_error(f"{filepath}: {result.error_count} error(s)")
            for err in result.errors[:5]:
                console.print(f"  [{err.code}] {err.path}: {err.message}")
            if result.error_count > 5:
                console.print(f"  ... and {result.error_count - 5} more errors")
            failed = True
        elif args.fail_on_warning and result.warning_count > 0:
            console.print_warning(f"{filepath}: {result.warning_count} warning(s)")
            for warn in result.warnings[:3]:
                console.print(f"  [{warn.code}] {warn.path}: {warn.message}")
            failed = True
        else:
            console.print_success(filepath)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
