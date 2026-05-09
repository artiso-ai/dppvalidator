"""Validate command for CLI."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.cli._io import load_input as _load_input
from dppvalidator.logging import get_logger
from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

logger = get_logger(__name__)

EXIT_VALID = 0
EXIT_INVALID = 1
EXIT_ERROR = 2
# Phase 6 task 6.7 — additional exit codes; see
# docs/reference/cli/exit-codes.md for the full table.
EXIT_FAMILY_MISMATCH = 3
EXIT_IO_ERROR = 5


def add_parser(subparsers: Any) -> argparse.ArgumentParser:
    """Add validate subparser."""
    parser = subparsers.add_parser(
        "validate",
        help="Validate a Digital Product Passport",
        description="Validate a DPP JSON file against UNTP schema",
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Input file path(s), glob pattern(s), or '-' for stdin",
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
        default="auto",
        help=(
            "UNTP DPP schema version to validate against. Defaults to "
            "'auto' — the engine detects the version from the payload's "
            "$schema or @context URLs. Pass an explicit version (e.g. "
            "'0.6.1', '0.7.0') to fail fast with VER001 when the payload "
            f"declares a different version. Default-version fallback when "
            f"detection finds nothing: {DEFAULT_SCHEMA_VERSION}."
        ),
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
    parser.add_argument(
        "--upgrade-from",
        default=None,
        help=(
            "Run the input through the compat shim from the named UNTP version "
            "(e.g. 0.6.1) up to --schema-version before validating. Upgrade "
            "warnings are reported alongside validation issues."
        ),
    )
    parser.add_argument(
        "--target",
        choices=["auto", "untp", "cirpass"],
        default="auto",
        help=(
            "Schema family to validate against. ``auto`` (default) detects "
            "the family from the payload's @context / shape signature. "
            "Explicit ``untp`` or ``cirpass`` overrides detection — when the "
            "override contradicts the payload, the command exits with code 3 "
            "and a DET001 diagnostic instead of silently re-routing."
        ),
    )
    parser.add_argument(
        "--profile",
        choices=["textile-v1", "textile-v2"],
        default=None,
        help=(
            "Optional pilot profile (Phase 7 of CIRPASS_2_MIGRATION). "
            "``textile-v1`` runs the legacy textile rule pack (TXT001…TXT005, "
            "all info/warning); ``textile-v2`` runs the MVP Textile DPP v2 "
            "(2025-12-04) pack with stricter rules (TXT001…TXT007). When "
            "omitted, no textile-specific profile is loaded — the default "
            "rule set still applies."
        ),
    )
    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute validate command."""
    from dppvalidator.validators import ValidationEngine

    # Resolve input patterns to file paths
    files = _resolve_inputs(args.input, console)
    if not files:
        return EXIT_IO_ERROR

    engine = ValidationEngine(
        schema_version=args.schema_version,
        strict_mode=args.strict,
        profile=getattr(args, "profile", None),
    )

    upgrade_from = getattr(args, "upgrade_from", None)
    if upgrade_from is not None:
        _verify_upgrade_path(upgrade_from, args.schema_version, console)

    target = getattr(args, "target", "auto")

    all_valid = True
    has_load_error = False
    has_family_mismatch = False
    results: list[tuple[str, Any]] = []

    for file_path in files:
        data = _load_input(file_path, console)
        if data is None:
            has_load_error = True
            continue

        if upgrade_from is not None:
            data, upgrade_warnings = _apply_upgrade(data, upgrade_from, file_path, console)
            if upgrade_warnings:
                _print_upgrade_warnings(upgrade_warnings, file_path, console)

        # Phase 6 task 6.3: when the user pinned --target explicitly,
        # check it against the detected family before validating. A
        # contradiction emits DET001 + EXIT_FAMILY_MISMATCH; agreement
        # falls through to ordinary validation.
        if target != "auto":
            mismatch = _check_target_family(data, target, file_path, console)
            if mismatch is not None:
                has_family_mismatch = True
                results.append((file_path, mismatch))
                all_valid = False
                continue

        result = engine.validate(
            data,
            fail_fast=args.fail_fast,
            max_errors=args.max_errors,
        )
        results.append((file_path, result))
        if not result.valid:
            all_valid = False

    # If no files were successfully loaded, return IO error
    if not results and has_load_error:
        return EXIT_IO_ERROR

    # Output results
    if len(results) == 1:
        _output_result(results[0][1], args.format, results[0][0], console)
    elif results:
        _output_batch_results(results, args.format, console)

    # Phase 6: family mismatch is a distinct exit code so wrappers
    # can route DET001 differently from regular validation errors.
    if has_family_mismatch:
        return EXIT_FAMILY_MISMATCH
    if has_load_error:
        return EXIT_IO_ERROR
    return EXIT_VALID if all_valid else EXIT_INVALID


def _resolve_inputs(inputs: list[str], console: Console) -> list[str]:
    """Resolve input patterns to file paths, expanding globs.

    Cross-platform considerations:
    - Windows: shell doesn't expand globs, so patterns arrive as-is
    - Unix: shell may expand globs before reaching Python (if unquoted)
    - Path separators are normalized for consistent output
    """
    files: list[str] = []

    for pattern in inputs:
        if pattern == "-":
            files.append("-")
            continue

        # Normalize path separators for cross-platform glob matching
        # Windows accepts forward slashes, and glob works better with them
        normalized_pattern = pattern.replace("\\", "/")

        # Try glob expansion (works on all platforms)
        expanded = glob.glob(normalized_pattern, recursive=True)
        if expanded:
            # Normalize output paths for consistent cross-platform display
            files.extend(sorted(str(Path(f)) for f in expanded))
        elif Path(pattern).exists():
            # Pattern didn't match glob but file exists (exact path)
            files.append(str(Path(pattern)))
        else:
            console.print_error(f"No files match pattern: {pattern}")

    return files


def _check_target_family(
    data: dict[str, Any],
    target: str,
    file_path: str,
    console: Console,
) -> Any | None:
    """Validate that ``--target`` agrees with the payload's detected family.

    Phase 6 task 6.3 of [docs/plans/CIRPASS_2_MIGRATION.md]. Returns
    ``None`` when there's no contradiction; returns a synthetic
    :class:`ValidationResult` carrying ``DET001`` when the user-
    supplied target overrides what the engine would have picked.
    """
    from dppvalidator.schemas.registry import SchemaFamily
    from dppvalidator.validators.detection import (
        DET_CODE_FAMILY_MISMATCH,
        detect_schema_family,
    )
    from dppvalidator.validators.results import ValidationError, ValidationResult

    detected = detect_schema_family(data)
    target_family = SchemaFamily.UNTP if target == "untp" else SchemaFamily.CIRPASS
    if detected is None:
        # No detection signal — caller's --target wins silently.
        return None
    if detected is target_family:
        # Detection agrees with --target. Continue.
        return None
    # Mismatch — fail fast with DET001.
    error = ValidationError(
        path="$",
        message=(
            f"--target={target!r} contradicts the payload's detected "
            f"family ({detected.value!r}). Re-run with --target=auto "
            f"or --target={detected.value!r} (or fix the payload)."
        ),
        code=DET_CODE_FAMILY_MISMATCH,
        layer="engine",
        severity="error",
        context={
            "detected_family": detected.value,
            "configured_target": target,
        },
    )
    console.print_error(
        f"DET001: {file_path} — payload looks like {detected.value!r} "
        f"but --target={target!r} pins the other family."
    )
    return ValidationResult(
        valid=False,
        errors=[error],
        schema_version=target_family.value,
    )


def _verify_upgrade_path(source: str, target: str, console: Console) -> None:
    """Confirm we have a registered shim for ``source → target``.

    The current matrix is just ``0.6.x → 0.7.0`` (Phase 4). Anything else
    is reported as a warning so the caller knows their flag had no effect;
    we don't raise so the rest of the validation still runs.
    """
    from dppvalidator.compat.upgrade_0_6_to_0_7 import upgrade as _u  # noqa: F401

    if not (source.startswith("0.6") and target.startswith("0.7")):
        console.print_warning(
            f"No upgrade shim registered for {source!r} → {target!r}; "
            "input will be validated without transformation.",
        )


def _apply_upgrade(
    data: dict[str, Any], source: str, path: str, console: Console
) -> tuple[dict[str, Any], list[Any]]:
    """Run the v0.6 → v0.7 shim on ``data`` and return ``(upgraded, warnings)``."""
    if source.startswith("0.6"):
        from dppvalidator.compat.upgrade_0_6_to_0_7 import upgrade

        try:
            return upgrade(data)
        except Exception as exc:  # pragma: no cover — defensive
            logger.exception("Upgrade shim crashed on %s", path)
            console.print_error(f"Upgrade shim failed for {path}: {exc}")
            return data, []
    return data, []


def _print_upgrade_warnings(warnings: list[Any], input_path: str, console: Console) -> None:
    """Print upgrade-shim warnings inline with validation output."""
    if not warnings:
        return
    console.print(
        f"\n[bold yellow]Upgrade warnings ({len(warnings)})[/bold yellow] — {input_path}",
        style="yellow",
    )
    for w in warnings:
        console.print(f"  [{w.code}] ({w.severity.value}) {w.path}: {w.message}")


def _output_result(result: Any, fmt: str, input_path: str, console: Console) -> None:
    """Output validation result in specified format."""
    if fmt == "json":
        # Use plain print for JSON to avoid Rich formatting/ANSI codes
        print(result.to_json())
        return

    if fmt == "table":
        _output_table(result, input_path, console)
        return

    _output_text(result, input_path, console)


def _format_issue(issue: Any, console: Console) -> None:
    """Format and print a single validation issue with optional fields."""
    console.print(f"  [{issue.code}] {issue.path}: {issue.message}")

    if getattr(issue, "did_you_mean", None):
        suggestions = ", ".join(f'"{v}"' for v in issue.did_you_mean)
        console.print(f"    Did you mean: {suggestions}?", style="cyan")

    if issue.suggestion:
        console.print(f"    💡 {issue.suggestion}", style="dim")

    if issue.docs_url:
        console.print(f"    📖 {issue.docs_url}", style="dim blue")


def _print_issues(issues: list[Any], label: str, style: str, console: Console) -> None:
    """Print a section of issues with header."""
    if not issues:
        return
    console.print(f"\n[bold {style}]{label} ({len(issues)}):[/bold {style}]", style=style)
    for issue in issues:
        _format_issue(issue, console)


def _output_text(result: Any, input_path: str, console: Console) -> None:
    """Output result as text."""
    if result.valid:
        console.print(f"\n[bold green]✓ VALID[/bold green]: {input_path}", style="green")
    else:
        console.print(f"\n[bold red]✗ INVALID[/bold red]: {input_path}", style="red")

    console.print(f"Schema version: {result.schema_version}")

    _print_issues(result.errors, "Errors", "red", console)
    _print_issues(result.warnings, "Warnings", "yellow", console)

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


def _output_batch_results(results: list[tuple[str, Any]], fmt: str, console: Console) -> None:
    """Output results for multiple files."""
    if fmt == "json":
        batch_output = {
            "files": [{"path": path, "result": result.to_dict()} for path, result in results],
            "summary": {
                "total": len(results),
                "valid": sum(1 for _, r in results if r.valid),
                "invalid": sum(1 for _, r in results if not r.valid),
            },
        }
        print(json.dumps(batch_output, indent=2, default=str))
        return

    if fmt == "table":
        _output_batch_table(results, console)
        return

    # Text format - output each result
    for path, result in results:
        _output_text(result, path, console)

    # Summary (use ASCII hyphen for cross-platform compatibility)
    valid_count = sum(1 for _, r in results if r.valid)
    invalid_count = len(results) - valid_count
    console.print(f"\n{'-' * 40}")
    console.print(f"[bold]Summary:[/bold] {len(results)} files processed")
    console.print(f"  [green]✓ Valid:[/green] {valid_count}")
    console.print(f"  [red]✗ Invalid:[/red] {invalid_count}")


def _output_batch_table(results: list[tuple[str, Any]], console: Console) -> None:
    """Output batch results as table."""
    summary = console.create_table(title="Batch Validation Results")
    summary.add_column("Status", style="bold")
    summary.add_column("Path")
    summary.add_column("Errors", justify="right")
    summary.add_column("Warnings", justify="right")

    for path, result in results:
        status = "[green]✓[/green]" if result.valid else "[red]✗[/red]"
        summary.add_row(
            status,
            path,
            str(result.error_count),
            str(result.warning_count),
        )

    console.print_table(summary)

    valid_count = sum(1 for _, r in results if r.valid)
    console.print(
        f"\n[bold]Total:[/bold] {len(results)} files | "
        f"[green]{valid_count} valid[/green] | "
        f"[red]{len(results) - valid_count} invalid[/red]"
    )
