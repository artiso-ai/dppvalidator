"""Guard test: forbid bare ``"X.Y.Z"`` version literals in source code.

This test enforces the contract documented in
``docs/plans/UNTP_0.7.0_MIGRATION.md`` §Phase 1 / §7.1 (rule 1) and
``.claude/rules/untp-versioning.md`` (cardinal rule 1), extended in
Phase 1 of ``docs/plans/CIRPASS_2_MIGRATION.md`` to cover CIRPASS
message and EUDPP module versions:

> No bare UNTP / CIRPASS / EUDPP-module version literals. A string like
> ``"0.6.1"``, ``"0.7.0"``, ``"1.3.0"``, or ``"1.9.1"`` may only appear
> in ``schemas/registry.py``, ``exporters/contexts.py``, and
> ``schemas/cirpass_loader.py``. Everywhere else: look it up via
> ``SchemaRegistry``, ``ContextManager``, or
> ``dppvalidator.compat.active_version()``.

The regex matches any ``"\\d+\\.\\d+\\.\\d+"`` triple-dotted SemVer
literal, so the CIRPASS-2 migration's new versions are caught
automatically by the existing pattern. Pre-release suffixes such as
``"1.9.4-Maki"`` are intentionally not matched — those literals appear
only in registry rows where the four-part shape is unambiguous.

When this test fails, the right fix is almost always to import
``DEFAULT_SCHEMA_VERSION`` (or ``DEFAULT_VERSIONS[…]`` post-Phase 2)
from ``dppvalidator.schemas.registry`` and use it as the constructor
default / dataclass default / argparse default — not to add the new
file to ``ALLOWED``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Pattern: a "double-quoted" SemVer-shaped literal anywhere in a Python source
# line. We intentionally do NOT match version-like substrings that appear
# inside longer URLs (e.g. "https://.../0.6.1/..."), because the version is
# not the entire content between the surrounding quotes there.
_VERSION_LITERAL_PATTERN = re.compile(r'"\d+\.\d+\.\d+"')

# Files allowed to contain bare version literals. These are all *registries*
# in the strict §7.1 sense ("source of truth per surface"): each one defines
# a single dispatch table whose entries MUST be literal version strings
# keyed to :data:`SCHEMA_REGISTRY`. Adding a new UNTP version is a one-line
# change in each.
#
# - ``schemas/registry.py``       : the ``SchemaVersion`` registry itself.
# - ``exporters/contexts.py``     : the JSON-LD ``ContextDefinition`` registry.
# - ``schemas/cirpass_loader.py`` : the CIRPASS-2 ``CIRPASS_SCHEMA_VERSION``
#                                   constant (separate version axis).
# - ``validators/model.py``       : the ``_MODEL_BY_VERSION`` Pydantic-class
#                                   dispatch (Phase 3.3).
# - ``validators/deep.py``        : the ``LINK_PATHS_BY_VERSION`` deep-crawl
#                                   path dispatch (Phase 3b).
# - ``validators/rules/__init__`` : the ``ALL_RULES_BY_VERSION`` semantic-rule
#                                   dispatch (Phase 3b).
_ALLOWED_FILES = frozenset(
    {
        Path("src/dppvalidator/schemas/registry.py"),
        Path("src/dppvalidator/exporters/contexts.py"),
        Path("src/dppvalidator/schemas/cirpass_loader.py"),
        Path("src/dppvalidator/validators/model.py"),
        Path("src/dppvalidator/validators/deep.py"),
        Path("src/dppvalidator/validators/rules/__init__.py"),
        # Added the
        # CIRPASS-family rule dispatch table — analogous to the UNTP
        # ``ALL_RULES_BY_VERSION`` dispatch in the parent ``rules``
        # package. Single dispatch table; literal CIRPASS version
        # keys are intentional.
        Path("src/dppvalidator/validators/rules/cirpass_v1_3/__init__.py"),
    }
)


def _project_root() -> Path:
    """Locate the repo root by walking up from this test file."""
    return Path(__file__).resolve().parents[2]


def _violations() -> list[tuple[Path, int, str, str]]:
    """Collect every bare version-literal occurrence outside the allow-list.

    Returns:
        Tuples of ``(relative_path, line_number, matched_literal, line_excerpt)``.
    """
    root = _project_root()
    src = root / "src" / "dppvalidator"
    if not src.is_dir():
        # If the layout ever changes, fail loudly instead of silently passing.
        raise RuntimeError(f"Expected source tree at {src}")

    out: list[tuple[Path, int, str, str]] = []
    for path in sorted(src.rglob("*.py")):
        rel = path.relative_to(root)
        if rel in _ALLOWED_FILES:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in _VERSION_LITERAL_PATTERN.findall(line):
                out.append((rel, lineno, match, line.strip()))
    return out


def test_no_bare_version_literals_in_src() -> None:
    """Every UNTP/CIRPASS version literal must live in one of the registries.

    See module docstring for the rationale and the fix.
    """
    violations = _violations()
    if not violations:
        return

    pretty = "\n".join(
        f"  {rel}:{lineno}: {literal}\n      {excerpt[:120]}"
        for rel, lineno, literal, excerpt in violations
    )
    allowed = "\n".join(f"  - {p}" for p in sorted(_ALLOWED_FILES))
    pytest.fail(
        f"\n{len(violations)} bare version literal(s) found outside the registry "
        f"allow-list.\n\nViolations:\n{pretty}\n\nAllowed files:\n{allowed}\n\n"
        "Fix: import DEFAULT_SCHEMA_VERSION from dppvalidator.schemas.registry "
        "and reference that constant instead of hardcoding the string. "
        "See docs/plans/UNTP_0.7.0_MIGRATION.md §Phase 1.\n",
    )


def test_allow_list_files_exist() -> None:
    """Every allow-listed path must exist; otherwise the guard is a tautology."""
    root = _project_root()
    missing = [p for p in _ALLOWED_FILES if not (root / p).is_file()]
    assert not missing, (
        f"Allow-list references non-existent file(s): {missing}. "
        "Update _ALLOWED_FILES to match the current source layout."
    )


def test_pattern_matches_expected_strings() -> None:
    """Self-test: confirm the regex catches the kinds of literal we care about."""
    assert _VERSION_LITERAL_PATTERN.search('default = "0.6.1"')
    assert _VERSION_LITERAL_PATTERN.search('schema_version: str = "0.7.0"')
    # URL-embedded versions must NOT match — they're inside longer strings.
    assert not _VERSION_LITERAL_PATTERN.search('"https://example.com/0.6.1/schema.json"')
    # Two-part versions are not matched.
    assert not _VERSION_LITERAL_PATTERN.search('python_requires = "3.10"')
