"""Migrate command: rewrite a v0.6.x DPP into v0.7.0 shape.

Phase 4 of ``docs/plans/UNTP_0.7.0_MIGRATION.md`` introduces this
command. It runs the compat shim (see
:mod:`dppvalidator.compat.upgrade_0_6_to_0_7`) over a single input file
and writes the upgraded JSON to ``-o`` / ``--in-place``.

By default, the command refuses to write the upgraded file when the
shim emits any ``warning``- or ``error``-severity warnings — the user
must opt in with ``--accept-warnings``. ``info``-severity events are
informational and never block. A sidecar ``<output>.warnings.json``
captures every warning whenever any non-info warning fires, regardless
of whether the write went through.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

logger = get_logger(__name__)

EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_ERROR = 2


def add_parser(subparsers: Any) -> argparse.ArgumentParser:
    """Register the ``migrate`` subcommand."""
    parser = subparsers.add_parser(
        "migrate",
        help="Upgrade a v0.6.x DPP to v0.7.0 shape via the compat shim",
        description=(
            "Run the compat shim over a v0.6.x DPP and write the upgraded "
            "JSON. Refuses to write when warnings fire unless "
            "--accept-warnings is given. A sidecar warnings file is always "
            "produced when warnings fire."
        ),
    )
    parser.add_argument(
        "input",
        help="Input file path, or '-' for stdin",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write the upgraded JSON back to the input path (overwrites).",
    )
    parser.add_argument(
        "--accept-warnings",
        action="store_true",
        help=(
            "Write the upgraded JSON even when the shim emits warnings or "
            "errors. Without this, the command exits with code 1 on any "
            "non-info warning."
        ),
    )
    parser.add_argument(
        "--from",
        dest="source_version",
        default="0.6.x",
        help=(
            "Source UNTP version family (default: 0.6.x). Pass an explicit "
            "X.Y.Z value to pin a specific source version."
        ),
    )
    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute the migrate command."""
    from dppvalidator.compat.upgrade_0_6_to_0_7 import (
        UpgradeSeverity,
        upgrade,
    )

    data = _load_input(args.input, console)
    if data is None:
        return EXIT_ERROR

    if not args.source_version.startswith("0.6"):
        console.print_error(
            f"No upgrade shim registered for source version {args.source_version!r}.",
        )
        return EXIT_ERROR

    try:
        upgraded, warnings = upgrade(data)
    except Exception as exc:
        logger.exception("Upgrade shim crashed")
        console.print_error(f"Upgrade failed: {exc}")
        return EXIT_ERROR

    blocking = [w for w in warnings if w.severity != UpgradeSeverity.INFO]

    output_path = _resolve_output_path(args, console)
    if output_path is None and args.in_place:
        return EXIT_ERROR

    # Always write a sidecar warnings file when *any* blocking-grade
    # warning fired, regardless of whether the main write goes through.
    sidecar_path: Path | None = None
    if blocking and output_path is not None:
        sidecar_path = output_path.with_suffix(output_path.suffix + ".warnings.json")
        _write_warnings_sidecar(sidecar_path, warnings)
        console.print_warning(
            f"{len(warnings)} warning(s) recorded in {sidecar_path}",
        )

    if blocking and not args.accept_warnings:
        console.print_error(
            f"Upgrade emitted {len(blocking)} blocking warning(s); refusing to "
            "write. Re-run with --accept-warnings to override, or fix the "
            "issues listed in the sidecar warnings file.",
        )
        for w in warnings:
            console.print(f"  [{w.code}] ({w.severity.value}) {w.path}: {w.message}")
        return EXIT_BLOCKED

    _write_output(upgraded, output_path, console)

    if warnings:
        console.print(f"Upgraded with {len(warnings)} warning(s).")
        for w in warnings:
            console.print(f"  [{w.code}] ({w.severity.value}) {w.path}: {w.message}")
    else:
        console.print_success("Upgraded with no warnings.")

    return EXIT_OK


def _resolve_output_path(args: argparse.Namespace, console: Console) -> Path | None:
    """Return the resolved output path or ``None`` when stdout is the target."""
    if args.in_place and args.output:
        console.print_error("--in-place and -o/--output are mutually exclusive.")
        return None
    if args.in_place:
        if args.input == "-":
            console.print_error("--in-place is incompatible with stdin input.")
            return None
        return Path(args.input)
    if args.output:
        return Path(args.output)
    return None


def _load_input(input_path: str, console: Console) -> dict[str, Any] | None:
    """Load JSON from a file path or stdin."""
    try:
        if input_path == "-":
            if hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
            content = sys.stdin.read()
        else:
            path = Path(input_path)
            if not path.exists():
                console.print_error(f"File not found: {input_path}")
                return None
            content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as exc:
        console.print_error(f"Invalid JSON: {exc}")
        return None
    except Exception as exc:
        logger.exception("Unexpected error loading input")
        console.print_error(str(exc))
        return None


def _write_output(payload: dict[str, Any], path: Path | None, console: Console) -> None:
    """Write the upgraded JSON to ``path`` (or stdout if ``None``)."""
    serialised = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    if path is None:
        # Stdout — bypass Rich so the output is pipe-friendly.
        print(serialised)
        return
    path.write_text(serialised + "\n", encoding="utf-8")
    console.print(f"Wrote {path}")


def _write_warnings_sidecar(path: Path, warnings: list[Any]) -> None:
    """Persist the full warning list as JSON next to the upgraded payload."""
    from dppvalidator.schemas.registry import SCHEMA_REGISTRY

    target_candidates = [
        v for v in SCHEMA_REGISTRY if v.split(".")[0] == "0" and v.split(".")[1] == "7"
    ]
    target_version = (
        max(target_candidates, key=lambda v: tuple(int(x) for x in v.split(".")))
        if target_candidates
        else "0.7.x"
    )
    payload = {
        "schema_version_from": "0.6.x",
        "schema_version_to": target_version,
        "warnings": [{**asdict(w), "severity": w.severity.value} for w in warnings],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
