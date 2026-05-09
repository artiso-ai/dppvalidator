#!/usr/bin/env python3
"""CI drift gate for code-generated artefacts (Phase 3 task 3.13).

Re-runs every committed code generator under ``tools/codegen/`` and
diffs the output against the bytes on disk. Non-zero exit on drift.

This script is intentionally tiny — the actual generators carry
their own logic; this is just the meta-runner. Add new generators by
appending a row to :data:`_GENERATORS` below.

Usage:

    uv run python tools/codegen/check_drift.py
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class _Generator:
    """One code generator + the artefact it produces."""

    name: str
    command: Sequence[str]
    output: Path

    def expected_bytes(self) -> bytes:
        """Return the bytes currently committed at :attr:`output`."""
        return self.output.read_bytes()

    def regenerate(self) -> bytes:
        """Run the generator and return what it would write.

        Each generator is invoked with ``--stdout`` so the meta-runner
        captures its output without touching the file. This avoids a
        race where the runner *almost* matches the committed bytes
        because the run-and-diff dance overwrites them.
        """
        # S603: command is a hardcoded tuple-of-Path values from the
        # _GENERATORS table immediately below; no untrusted input.
        proc = subprocess.run(  # noqa: S603 — hardcoded generator commands
            [*self.command, "--stdout"],
            capture_output=True,
            check=True,
            cwd=_REPO_ROOT,
        )
        return proc.stdout


_GENERATORS: tuple[_Generator, ...] = (
    _Generator(
        name="cirpass-reference-schema",
        command=(
            sys.executable,
            "tools/codegen/cirpass/derive_schema.py",
        ),
        output=_REPO_ROOT
        / "src"
        / "dppvalidator"
        / "schemas"
        / "data"
        / "cirpass-reference-1.3.0.json",
    ),
)


def _lf_normalised_sha256(content: bytes) -> str:
    """Match the project's manifest-integrity normalisation."""
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def _check_one(generator: _Generator) -> bool:
    """Run one generator and report drift; return True iff committed = generated."""
    expected = generator.expected_bytes()
    actual = generator.regenerate()

    expected_sha = _lf_normalised_sha256(expected)
    actual_sha = _lf_normalised_sha256(actual)

    rel = generator.output.relative_to(_REPO_ROOT)
    if expected_sha == actual_sha:
        print(f"  ✓ {generator.name}: {rel} matches generator output", file=sys.stderr)
        return True

    print(
        f"  ✗ {generator.name}: DRIFT detected at {rel}",
        file=sys.stderr,
    )
    print(f"      committed sha256: {expected_sha}", file=sys.stderr)
    print(f"      generated sha256: {actual_sha}", file=sys.stderr)
    print(
        f"      Re-run the generator and commit the result:\n        {' '.join(generator.command)}",
        file=sys.stderr,
    )
    return False


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001 — argparse-free single-action tool
    print(
        f"# Checking {len(_GENERATORS)} code-generated artefact(s) for drift…",
        file=sys.stderr,
    )
    failures = sum(1 for g in _GENERATORS if not _check_one(g))
    if failures:
        print(
            f"\n# {failures}/{len(_GENERATORS)} generator(s) drifted from committed bytes.",
            file=sys.stderr,
        )
        return 1
    print(f"\n# All {len(_GENERATORS)} generator(s) clean.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
