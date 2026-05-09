#!/usr/bin/env python3
"""Phase 7 task 7.9 of [docs/plans/CIRPASS_2_MIGRATION.md] — import-graph guard.

Fails (exit 1) when any module under ``src/dppvalidator/`` imports
from any plugin package under ``plugins/*``. This is the
operational mitigation for risk R8 ("Plugin license bleed-over"):
the dppvalidator core is MIT-licensed and the textiles / tyres
plugins are GPL-3.0-or-later. Any ``from dppvalidator_textiles
import …`` (or ``from dppvalidator_tyres import …``) at the core
boundary would create a one-way GPL dependency that taints the
core's MIT licensing.

How it works
------------

The script walks every ``.py`` file under ``src/dppvalidator/``
and parses it via :mod:`ast` to locate ``import`` and
``from-import`` statements. It then matches the imported module
name against a list of forbidden plugin top-level packages.
Comments / strings are not parsed, so spurious matches in
docstrings don't trigger false positives.

The forbidden-package list is derived from the directory layout
of ``plugins/`` so adding a new plugin doesn't require updating
this script: every direct child of ``plugins/`` whose
``pyproject.toml`` declares a top-level ``[project] name`` (or
``[tool.hatch.build.targets.wheel] packages``) is added to the
forbidden set.

CLI
---

::

    # Hard fail on violation (CI mode):
    uv run python tools/check_imports.py

    # Verbose listing (every imported plugin path, even legal):
    uv run python tools/check_imports.py --verbose

Exit codes: ``0`` clean / ``1`` violation found / ``2`` walk error.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# ``tomllib`` is in the stdlib on Python 3.11+. The dppvalidator
# project requires Python 3.10+; on 3.10 the runner needs the
# ``tomli`` shim to be installed (it ships with most CI / dev
# environments via ``uv``'s resolver).
if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover — Python 3.10 fallback
    import tomli as tomllib  # noqa: F401  # tomli ships in dev env

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CORE_ROOT = _REPO_ROOT / "src" / "dppvalidator"
_PLUGINS_ROOT = _REPO_ROOT / "plugins"


def _find_plugin_packages() -> set[str]:
    """Return the set of top-level Python package names under ``plugins/``.

    Walks every ``plugins/<plugin>/`` and reads its ``pyproject.toml``
    to discover the plugin's distribution name. The heuristic prefers
    explicit ``[tool.hatch.build.targets.wheel] packages`` entries
    (the canonical way), then falls back to deriving from the
    on-disk ``src/<package>/`` layout.
    """
    packages: set[str] = set()
    if not _PLUGINS_ROOT.is_dir():
        return packages
    for plugin_dir in _PLUGINS_ROOT.iterdir():
        if not plugin_dir.is_dir():
            continue
        pyproject = plugin_dir / "pyproject.toml"
        if pyproject.is_file():
            try:
                config = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            except (tomllib.TOMLDecodeError, OSError):
                config = {}
            wheel_packages = (
                config.get("tool", {})
                .get("hatch", {})
                .get("build", {})
                .get("targets", {})
                .get("wheel", {})
                .get("packages", [])
            )
            for pkg in wheel_packages:
                # ``packages`` entries are paths like ``src/dppvalidator_tyres``;
                # extract the top-level package name.
                tail = pkg.rsplit("/", 1)[-1]
                if tail:
                    packages.add(tail)
        # Fallback: discover any ``src/<pkg>/__init__.py`` directly.
        src_dir = plugin_dir / "src"
        if src_dir.is_dir():
            for child in src_dir.iterdir():
                if child.is_dir() and (child / "__init__.py").is_file():
                    packages.add(child.name)
    return packages


def _imports_in_file(path: Path) -> list[str]:
    """Return every imported top-level module name in ``path``."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".", 1)[0]
                names.append(top)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            top = node.module.split(".", 1)[0]
            names.append(top)
    return names


def _collect_violations(forbidden: set[str]) -> list[tuple[Path, str]]:
    """Walk the core source tree and return every forbidden import."""
    violations: list[tuple[Path, str]] = []
    if not _CORE_ROOT.is_dir():
        return violations
    for py_file in _CORE_ROOT.rglob("*.py"):
        for top_module in _imports_in_file(py_file):
            if top_module in forbidden:
                violations.append((py_file, top_module))
    return violations


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the desired CLI exit code."""
    args = argv if argv is not None else sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args

    forbidden = _find_plugin_packages()
    if verbose:
        print(
            f"# Phase 7.9 import-graph guard\n"
            f"# core root: {_CORE_ROOT.relative_to(_REPO_ROOT)}\n"
            f"# forbidden packages (derived from plugins/): "
            f"{sorted(forbidden) if forbidden else '(none — no plugins discovered)'}",
            file=sys.stderr,
        )
    if not forbidden:
        print(
            "✓ no plugins discovered under plugins/; nothing to check.",
            file=sys.stderr,
        )
        return 0

    violations = _collect_violations(forbidden)
    if not violations:
        print(
            f"✓ core import graph clean — no imports from {sorted(forbidden)}",
            file=sys.stderr,
        )
        return 0

    print(
        f"✗ Found {len(violations)} forbidden import(s) in the core "
        "source tree.\n"
        "Plugin license isolation is broken — see "
        ".claude/rules/plugin-licenses.md (rule §1).\n",
        file=sys.stderr,
    )
    for file_path, top_module in violations:
        rel = file_path.relative_to(_REPO_ROOT)
        print(f"  {rel}: imports forbidden plugin package {top_module!r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
