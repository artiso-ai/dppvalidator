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
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.cli._io import load_input as _load_input
from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

logger = get_logger(__name__)

EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_ERROR = 2
# Phase 6 task 6.7 — additional exit codes; see
# docs/reference/cli/exit-codes.md for the full table.
EXIT_FAMILY_MISMATCH = 3
EXIT_BLOCKING_WARNINGS = 4
EXIT_IO_ERROR = 5

# Migration target tokens (Phase 6 task 6.5). Stable across releases.
_MIGRATE_TARGET_UNTP_07 = "untp-0.7"
_MIGRATE_TARGET_CIRPASS_13 = "cirpass-1.3"
MIGRATE_TARGETS: tuple[str, ...] = (_MIGRATE_TARGET_UNTP_07, _MIGRATE_TARGET_CIRPASS_13)


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
            "X.Y.Z value to pin a specific source version. For "
            "``--to=cirpass-1.3``, ``--from`` accepts ``0.7.0`` and "
            "is otherwise unused (the CIRPASS forward shim only reads "
            "UNTP 0.7.0 input)."
        ),
    )
    parser.add_argument(
        "--to",
        dest="target",
        choices=list(MIGRATE_TARGETS),
        default=_MIGRATE_TARGET_UNTP_07,
        help=(
            "Migration target. ``untp-0.7`` (default) runs the v0.6 → v0.7 "
            "intra-family upgrade shim (back-compat with the pre-Phase-6 "
            "behaviour). ``cirpass-1.3`` runs the Phase 5 cross-family "
            "forward shim onto the CIRPASS reference structure v1.3.0."
        ),
    )
    parser.add_argument(
        "--default-language",
        default="en",
        help=(
            "BCP-47 tag passed to the CIRPASS forward shim when "
            "wrapping UNTP scalar names as LocalisedText entries. "
            "Used only by ``--to=cirpass-1.3`` (default: en)."
        ),
    )
    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute the migrate command.

    Phase 6 task 6.5 of [docs/plans/CIRPASS_2_MIGRATION.md] generalised
    this command from the single 0.6 → 0.7 path to a family-aware
    dispatch on ``--to``. The 0.6 → 0.7 path is the default for
    back-compat with the pre-Phase-6 behaviour.
    """
    data = _load_input(args.input, console)
    if data is None:
        return EXIT_IO_ERROR

    target = getattr(args, "target", _MIGRATE_TARGET_UNTP_07)
    try:
        if target == _MIGRATE_TARGET_UNTP_07:
            return _run_untp_upgrade(args, data, console)
        if target == _MIGRATE_TARGET_CIRPASS_13:
            return _run_cirpass_forward(args, data, console)
        # argparse should have rejected anything else; defensive
        # fallback only.
        console.print_error(f"Unknown migration target: {target!r}")
        return EXIT_ERROR
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("Migrate dispatch crashed")
        console.print_error(f"Migrate failed: {exc}")
        return EXIT_ERROR


def _run_untp_upgrade(args: argparse.Namespace, data: dict[str, Any], console: Console) -> int:
    """0.6 → 0.7 intra-family upgrade (pre-Phase-6 behaviour)."""
    from dppvalidator.compat.upgrade_0_6_to_0_7 import (
        UpgradeSeverity,
        upgrade,
    )

    if not args.source_version.startswith("0.6"):
        console.print_error(
            f"No upgrade shim registered for source version "
            f"{args.source_version!r}. ``--to=untp-0.7`` only reads "
            f"v0.6.x input; for cross-family migration use "
            f"``--to=cirpass-1.3``.",
        )
        return EXIT_FAMILY_MISMATCH

    try:
        upgraded, warnings = upgrade(data)
    except Exception as exc:
        logger.exception("Upgrade shim crashed")
        console.print_error(f"Upgrade failed: {exc}")
        return EXIT_ERROR

    blocking = [w for w in warnings if w.severity != UpgradeSeverity.INFO]
    return _finalise_migration(
        args=args,
        payload=upgraded,
        warnings=warnings,
        blocking=blocking,
        target_label="UNTP 0.7.0",
        sidecar_meta={
            "schema_version_from": "0.6.x",
            "schema_version_to": _resolve_v07_target_version(),
        },
        console=console,
    )


def _run_cirpass_forward(args: argparse.Namespace, data: dict[str, Any], console: Console) -> int:
    """UNTP 0.7.0 → CIRPASS reference structure v1.3.0 forward shim
    (Phase 6 task 6.5).
    """
    from dppvalidator.compat import MappingSeverity, to_cirpass_1_3

    default_language = getattr(args, "default_language", "en")
    try:
        cirpass_dict, mapping_warnings = to_cirpass_1_3(data, default_language=default_language)
    except Exception as exc:
        logger.exception("CIRPASS forward shim crashed")
        console.print_error(f"Mapping failed: {exc}")
        return EXIT_ERROR

    blocking = [w for w in mapping_warnings if w.severity != MappingSeverity.INFO]
    # ``schema_version_from`` defaults to the current UNTP default
    # (sourced from the registry, not a literal) when --from is left
    # at its catch-all "0.6.x" value. Pulling the version literals
    # from the registry keeps the no-version-literals guard happy.
    from dppvalidator.compat import active_version
    from dppvalidator.schemas.registry import DEFAULT_VERSIONS, SchemaFamily

    untp_default = active_version(SchemaFamily.UNTP)
    source_version = (
        args.source_version if args.source_version not in (None, "0.6.x") else untp_default
    )
    return _finalise_migration(
        args=args,
        payload=cirpass_dict,
        warnings=mapping_warnings,
        blocking=blocking,
        target_label=(f"CIRPASS reference structure v{DEFAULT_VERSIONS[SchemaFamily.CIRPASS]}"),
        sidecar_meta={
            "schema_version_from": source_version,
            "schema_version_to": DEFAULT_VERSIONS[SchemaFamily.CIRPASS],
            "family_from": "untp",
            "family_to": "cirpass",
        },
        console=console,
    )


def _finalise_migration(
    *,
    args: argparse.Namespace,
    payload: dict[str, Any],
    warnings: list[Any],
    blocking: list[Any],
    target_label: str,
    sidecar_meta: dict[str, Any],
    console: Console,
) -> int:
    """Shared post-migration handling: sidecar + accept-warnings gate + write.

    Both the UNTP-upgrade and CIRPASS-forward paths converge here so
    sidecar / blocking-warning semantics are identical.
    """
    output_path = _resolve_output_path(args, console)
    if output_path is None and args.in_place:
        return EXIT_ERROR

    sidecar_path: Path | None = None
    if blocking and output_path is not None:
        sidecar_path = output_path.with_suffix(output_path.suffix + ".warnings.json")
        _write_warnings_sidecar(sidecar_path, warnings, sidecar_meta)
        console.print_warning(
            f"{len(warnings)} warning(s) recorded in {sidecar_path}",
        )

    if blocking and not args.accept_warnings:
        console.print_error(
            f"Migration to {target_label} emitted {len(blocking)} "
            "blocking warning(s); refusing to write. Re-run with "
            "--accept-warnings to override, or fix the issues listed "
            "in the sidecar warnings file.",
        )
        for w in warnings:
            console.print(f"  [{w.code}] ({w.severity.value}) {w.path}: {w.message}")
        return EXIT_BLOCKING_WARNINGS

    _write_output(payload, output_path, console)

    if warnings:
        console.print(f"Migrated to {target_label} with {len(warnings)} warning(s).")
        for w in warnings:
            console.print(f"  [{w.code}] ({w.severity.value}) {w.path}: {w.message}")
    else:
        console.print_success(f"Migrated to {target_label} with no warnings.")

    return EXIT_OK


def _resolve_v07_target_version() -> str:
    """Resolve the highest 0.7.x version registered in SCHEMA_REGISTRY."""
    from dppvalidator.schemas.registry import SCHEMA_REGISTRY

    target_candidates = [
        v for v in SCHEMA_REGISTRY if v.split(".")[0] == "0" and v.split(".")[1] == "7"
    ]
    if target_candidates:
        return max(target_candidates, key=lambda v: tuple(int(x) for x in v.split(".")))
    return "0.7.x"


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


def _write_output(payload: dict[str, Any], path: Path | None, console: Console) -> None:
    """Write the upgraded JSON to ``path`` (or stdout if ``None``)."""
    serialised = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    if path is None:
        # Stdout — bypass Rich so the output is pipe-friendly.
        print(serialised)
        return
    path.write_text(serialised + "\n", encoding="utf-8")
    console.print(f"Wrote {path}")


def _write_warnings_sidecar(
    path: Path,
    warnings: list[Any],
    meta: dict[str, Any] | None = None,
) -> None:
    """Persist the full warning list as JSON next to the upgraded payload.

    Accepts both :class:`UpgradeWarning` (UNTP 0.6 → 0.7) and
    :class:`MappingWarning` (cross-family) entries; both expose the
    same dataclass shape, but MappingWarning's ``details`` field is a
    tuple of ``(key, value)`` pairs that needs flattening for JSON
    serialisation.
    """
    payload: dict[str, Any] = {
        "schema_version_from": "0.6.x",
        "schema_version_to": _resolve_v07_target_version(),
    }
    if meta:
        payload.update(meta)
    payload["warnings"] = [_warning_to_dict(w) for w in warnings]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _warning_to_dict(warning: Any) -> dict[str, Any]:
    """Convert UpgradeWarning / MappingWarning to a JSON-serialisable dict."""
    raw = asdict(warning)
    raw["severity"] = warning.severity.value
    # MappingWarning.details is a ``tuple[tuple[str, str], ...]``; turn
    # it into a dict for ergonomic JSON output.
    details = raw.get("details")
    if isinstance(details, (list, tuple)):
        raw["details"] = dict(details)
    return raw
