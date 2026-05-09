"""Phase 7 — re-asserts the plugin license-isolation contract.

> tests/plugins/test_license_isolation.py — re-asserts no
> ``from dppvalidator_textiles import …`` or
> ``from dppvalidator_tyres import …`` in the core import graph.

The dppvalidator core (``src/dppvalidator/``) is MIT-licensed; the
textiles plugin (when published) and the tyres plugin (Phase 7)
are GPL-3.0-or-later. A reverse import would create a one-way
GPL dependency that taints the core's MIT licensing — the
mitigation for risk R8.

This test mirrors what ``tools/check_imports.py`` does at CI time,
but as a pytest unit so it runs alongside every developer-side
``uv run pytest`` invocation.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CORE_ROOT = _REPO_ROOT / "src" / "dppvalidator"

# Forbidden top-level package names. Adding a new plugin: register
# its top-level distribution package here.
_FORBIDDEN_PLUGIN_PACKAGES: frozenset[str] = frozenset(
    {
        "dppvalidator_textiles",
        "dppvalidator_tyres",
    }
)


def _collect_imports(path: Path) -> list[str]:
    """Return every imported top-level module in ``path`` via AST walk."""
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
                names.append(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module.split(".", 1)[0])
    return names


def test_core_does_not_import_any_plugin_package() -> None:
    """No file under src/dppvalidator/ may import a plugin top-level package."""
    if not _CORE_ROOT.is_dir():
        pytest.skip("source layout not available")
    violations: list[tuple[Path, str]] = []
    for py_file in _CORE_ROOT.rglob("*.py"):
        for top_module in _collect_imports(py_file):
            if top_module in _FORBIDDEN_PLUGIN_PACKAGES:
                violations.append((py_file, top_module))
    if violations:
        details = "\n".join(f"  {p.relative_to(_REPO_ROOT)}: imports {m!r}" for p, m in violations)
        msg = (
            f"Plugin license isolation broken — {len(violations)} forbidden "
            f"import(s) in src/dppvalidator/:\n{details}\n\n"
            "See .claude/rules/plugin-licenses.md (rule §1, no reverse imports)."
        )
        pytest.fail(msg)


def test_check_imports_tool_runs_clean() -> None:
    """The CI gate at ``tools/check_imports.py`` exits 0 on the current tree."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "tools" / "check_imports.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"check_imports.py exited {result.returncode}; stderr:\n{result.stderr}"
    )


def test_check_imports_tool_detects_simulated_violation(tmp_path: Path) -> None:
    """The gate fires when a synthetic violation is introduced.

    We synthesise a fake ``src/dppvalidator/`` tree under tmp with a
    forbidden import, then point ``check_imports.py`` at it via a
    monkeypatched repo root. Validates the gate's positive path.
    """
    import importlib.util
    import sys

    # Load the module fresh (don't pollute the global import graph).
    spec = importlib.util.spec_from_file_location(
        "_check_imports_under_test",
        _REPO_ROOT / "tools" / "check_imports.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Inject a synthetic violation by patching the module's
    # internal core/plugins roots.
    fake_core = tmp_path / "src" / "dppvalidator"
    fake_core.mkdir(parents=True)
    (fake_core / "naughty.py").write_text(
        "from dppvalidator_tyres.models import Birth\n",
        encoding="utf-8",
    )
    # ``_find_plugin_packages`` iterates the children of
    # ``_PLUGINS_ROOT``; the root needs to be the parent ``plugins/``
    # directory, not a specific plugin.
    fake_plugins_root = tmp_path / "plugins"
    fake_plugins_root.mkdir(parents=True)
    fake_plugin_dir = fake_plugins_root / "tyres"
    fake_plugin_dir.mkdir(parents=True)
    (fake_plugin_dir / "pyproject.toml").write_text(
        "[tool.hatch.build.targets.wheel]\npackages = ['src/dppvalidator_tyres']\n",
        encoding="utf-8",
    )
    module._CORE_ROOT = fake_core
    module._PLUGINS_ROOT = fake_plugins_root
    module._REPO_ROOT = tmp_path
    exit_code = module.main([])
    assert exit_code == 1
    # Restore in case sys.modules already imported the module.
    sys.modules.pop("_check_imports_under_test", None)


def test_forbidden_packages_set_is_complete() -> None:
    """Pin the forbidden-packages list against accidental thinning."""
    assert "dppvalidator_textiles" in _FORBIDDEN_PLUGIN_PACKAGES
    assert "dppvalidator_tyres" in _FORBIDDEN_PLUGIN_PACKAGES


def test_plugin_can_import_core() -> None:
    """The dependency direction is *one-way*: plugin → core is fine.

    This test demonstrates the legal direction by re-importing the
    core's ``SemanticRule`` protocol from the tyres plugin's test
    surface. The reverse direction is blocked by the test above.
    """
    pytest.importorskip("dppvalidator_tyres")
    # The plugin's models import from dppvalidator-core implicitly
    # via its own dependency. This test would fail at collection if
    # that didn't work.
    from dppvalidator_tyres.validators import TYR_RULES

    from dppvalidator.validators.protocols import SemanticRule  # noqa: F401

    assert TYR_RULES
