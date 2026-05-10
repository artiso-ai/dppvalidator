"""Docs guard: pin user-facing default-version literals to the registry.

Scans the user-facing documentation surface for assertions of the form
``default ... 0.X.Y`` (with ``current``, ``current default``,
``currently``, etc.) and asserts the literal matches
``DEFAULT_VERSIONS[SchemaFamily.UNTP]`` from
``src/dppvalidator/schemas/registry.py``.

This is the docs-side analogue of
``tests/unit/test_no_version_literals.py`` (which guards source files
under ``src/dppvalidator/`` from drifting). Phase 1 of the
[Docs Coherence Plan](docs/plans/DOCS_COHERENCE_PLAN.md) flipped every
known reference from ``0.6.1`` to ``0.7.0``; Phase 7 prevents the same
drift from recurring on the next default-version flip.

Wired into ``.pre-commit-config.yaml`` and the ``ci.yml`` lint job.

Exit codes
----------
0 - All user-facing docs agree with the registry.
1 - At least one drift hit was found; offending lines printed to stderr.
2 - Could not import / parse the registry (configuration error).
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files that are docs-shaped but explicitly exempt from this guard:
# - ADR 0006 documents the migration *from* the old default; it
#   intentionally cites ``0.6.1`` as the legacy literal.
# - The Docs Coherence Plan and other plan docs in ``docs/plans/``
#   describe the rollout; they intentionally cite both the source and
#   target literals during the migration.
# - The CHANGELOG records the historical flip; ``0.6.1`` lives there
#   forever as part of the release history.
EXEMPT = (
    "docs/adr/0006-validation-layer-taxonomy.md",
    "docs/plans/",
    "CHANGELOG.md",
    "docs/changelog.md",  # snippet include of CHANGELOG.md
)

# Files that the guard reads. These are the user-facing surfaces that
# Phase 1 of the Docs Coherence Plan rewrote.
TARGETS = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "docs/index.md",
    "docs/faq.md",
    "docs/llms.txt",
    "docs/llms-ctx.txt",
    "docs/concepts/untp-versions.md",
    "docs/concepts/validation-layers.md",
    "docs/guides/cli-usage.md",
    "docs/guides/migration-0-6-to-0-7.md",
)

# Pattern: a trigger word ("default", "currently", "current default")
# followed within ~80 characters by one *or more* version literals on
# the same line. We only flag when NO literal in the window matches the
# expected default — that lets enumerations like "currently 0.6.0,
# 0.6.1, 0.7.0" pass (the expected version is present) while still
# catching "current default = 0.6.1" (no expected version in window).
_TRIGGER = re.compile(r"\b(default|currently|current default)\b", re.IGNORECASE)
_VERSION = re.compile(r"\b0\.\d+\.\d+\b")
_WINDOW = 80


def _read_default_version() -> str:
    """Parse the canonical default UNTP version from ``registry.py``.

    The registry uses ``DEFAULT_VERSIONS[SchemaFamily.UNTP]`` as the
    single source of truth. We avoid importing ``dppvalidator`` here
    so the guard runs in a minimal pre-commit environment.
    """
    registry = REPO_ROOT / "src" / "dppvalidator" / "schemas" / "registry.py"
    text = registry.read_text(encoding="utf-8")
    # Match: SchemaFamily.UNTP: "0.X.Y"  (with optional whitespace).
    match = re.search(
        r"SchemaFamily\.UNTP\s*:\s*[\"'](?P<ver>0\.\d+\.\d+)[\"']",
        text,
    )
    if not match:
        msg = f"could not locate DEFAULT_VERSIONS[SchemaFamily.UNTP] in {registry}"
        raise RuntimeError(msg)
    return match.group("ver")


def _is_exempt(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    return any(rel == ex or rel.startswith(ex) for ex in EXEMPT)


def _scan(path: Path, expected: str) -> Iterable[tuple[int, str, str]]:
    if _is_exempt(path):
        return
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for trigger in _TRIGGER.finditer(line):
            window = line[trigger.end() : trigger.end() + _WINDOW]
            versions = [m.group(0) for m in _VERSION.finditer(window)]
            if not versions:
                continue
            # If the expected default is anywhere in the trigger window,
            # the line is fine — even if other versions are listed too.
            if expected in versions:
                continue
            # Otherwise, the trigger asserts a default that doesn't
            # match the registry. Report the first off-default literal.
            yield line_no, line, versions[0]


def main() -> int:
    try:
        expected = _read_default_version()
    except (OSError, RuntimeError) as exc:
        print(f"check_doc_default_version: {exc}", file=sys.stderr)
        return 2

    drift: list[tuple[Path, int, str, str]] = []
    for rel in TARGETS:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        for line_no, line, ver in _scan(path, expected):
            drift.append((path, line_no, line, ver))

    if drift:
        print(
            "check_doc_default_version: docs cite a default UNTP version "
            f"that no longer matches the registry "
            f"(DEFAULT_VERSIONS[SchemaFamily.UNTP] = {expected!r}).",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for path, line_no, line, ver in drift:
            rel = path.relative_to(REPO_ROOT).as_posix()
            print(f"  {rel}:{line_no}: cites {ver!r}", file=sys.stderr)
            print(f"    > {line.strip()}", file=sys.stderr)
        print(file=sys.stderr)
        print(
            "Update the cited literal to match the registry, or add the "
            "file to EXEMPT in tools/check_doc_default_version.py if the "
            "mention is genuinely historical (e.g. an ADR documenting "
            "the migration).",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
