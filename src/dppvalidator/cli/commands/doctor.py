"""Doctor command for CLI - diagnoses environment issues."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

EXIT_SUCCESS = 0
EXIT_WARNING = 1
EXIT_ERROR = 2

# Minimum disk space required (in MB)
MIN_DISK_SPACE_MB = 50


def add_parser(subparsers: Any) -> argparse.ArgumentParser:
    """Add doctor subparser."""
    parser = subparsers.add_parser(
        "doctor",
        help="Diagnose environment and configuration issues",
        description="Check dppvalidator installation and environment",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix detected issues",
    )
    return parser


def run(_args: argparse.Namespace, console: Console) -> int:
    """Execute doctor command."""
    console.print("\n🩺 [bold]dppvalidator doctor[/bold]\n")
    console.print("Checking your environment...\n")

    checks = [
        _check_python_version,
        _check_dppvalidator_version,
        _check_pydantic,
        _check_optional_deps,
        _check_schema_cache,
        _check_disk_space,
        _check_config_files,
        _check_write_permissions,
    ]

    issues = 0
    warnings = 0

    for check in checks:
        status, message, is_warning = check(console)
        if not status:
            if is_warning:
                warnings += 1
            else:
                issues += 1

    console.print("\n" + "─" * 50)

    if issues == 0 and warnings == 0:
        console.print(
            "\n[bold green]✓ All checks passed![/bold green] "
            "Your environment is ready for DPP validation.\n"
        )
        return EXIT_SUCCESS
    elif issues == 0:
        console.print(
            f"\n[bold yellow]⚠ {warnings} warning(s)[/bold yellow] "
            "Environment is functional but could be improved.\n"
        )
        return EXIT_WARNING
    else:
        console.print(
            f"\n[bold red]✗ {issues} issue(s) found[/bold red] "
            f"({warnings} warnings). Please address the issues above.\n"
        )
        return EXIT_ERROR


def _check_python_version(console: Console) -> tuple[bool, str, bool]:
    """Check Python version compatibility."""
    py_version = sys.version_info
    version_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"

    if py_version >= (3, 10):
        console.print(f"  [green]✓[/green] Python {version_str}")
        return True, "", False
    else:
        console.print(
            f"  [red]✗[/red] Python {version_str} - requires Python 3.10+",
            style="red",
        )
        console.print("    💡 Install Python 3.10+ from https://python.org")
        return False, "Python version too old", False


def _check_dppvalidator_version(console: Console) -> tuple[bool, str, bool]:
    """Check dppvalidator installation."""
    try:
        from dppvalidator import __version__

        console.print(f"  [green]✓[/green] dppvalidator {__version__}")
        return True, "", False
    except ImportError:
        console.print("  [red]✗[/red] dppvalidator not installed properly", style="red")
        console.print("    💡 Run: pip install dppvalidator")
        return False, "dppvalidator not installed", False


def _check_pydantic(console: Console) -> tuple[bool, str, bool]:
    """Check Pydantic v2 installation."""
    try:
        pydantic_ver = pkg_version("pydantic")
        major = int(pydantic_ver.split(".")[0])

        if major >= 2:
            console.print(f"  [green]✓[/green] Pydantic {pydantic_ver}")
            return True, "", False
        else:
            console.print(
                f"  [red]✗[/red] Pydantic {pydantic_ver} - requires Pydantic v2+",
                style="red",
            )
            console.print("    💡 Run: pip install 'pydantic>=2.0'")
            return False, "Pydantic version too old", False
    except Exception:
        console.print("  [red]✗[/red] Pydantic not installed", style="red")
        console.print("    💡 Run: pip install pydantic")
        return False, "Pydantic not installed", False


def _check_optional_deps(console: Console) -> tuple[bool, str, bool]:
    """Check optional dependencies."""
    optional_deps = {
        "rich": ("CLI formatting", "pip install 'dppvalidator[cli]'"),
        "httpx": ("HTTP schema fetching", "pip install 'dppvalidator[http]'"),
        "jsonschema": ("JSON Schema validation", "pip install 'dppvalidator[jsonschema]'"),
    }

    missing = []
    for dep, (purpose, install_cmd) in optional_deps.items():
        try:
            dep_ver = pkg_version(dep)
            console.print(f"  [green]✓[/green] {dep} {dep_ver} ({purpose})")
        except Exception:
            missing.append((dep, purpose, install_cmd))

    if missing:
        for dep, purpose, install_cmd in missing:
            console.print(f"  [yellow]○[/yellow] {dep} not installed ({purpose})")
            console.print(f"    💡 Run: {install_cmd}")
        return True, "Some optional dependencies missing", True

    return True, "", False


def _check_schema_cache(console: Console) -> tuple[bool, str, bool]:
    """Check schema cache status."""
    cache_dirs = [
        Path.home() / ".cache" / "dppvalidator",
        Path.home() / ".dppvalidator" / "cache",
    ]

    for cache_dir in cache_dirs:
        if cache_dir.exists():
            schema_files = list(cache_dir.glob("*.json"))
            if schema_files:
                # Verify cache files are valid JSON
                valid_count = 0
                for sf in schema_files:
                    try:
                        json.loads(sf.read_text())
                        valid_count += 1
                    except (json.JSONDecodeError, OSError):
                        pass
                console.print(
                    f"  [green]✓[/green] Schema cache: {valid_count}/{len(schema_files)} valid in {cache_dir}"
                )
                if valid_count < len(schema_files):
                    console.print("    💡 Some cache files are corrupted, consider clearing cache")
                    return True, "Some cache files corrupted", True
                return True, "", False

    console.print("  [yellow]○[/yellow] Schema cache not populated")
    console.print("    💡 Schemas will be fetched on first validation")
    return True, "Schema cache empty", True


def _check_disk_space(console: Console) -> tuple[bool, str, bool]:
    """Check available disk space."""
    try:
        home = Path.home()
        total, used, free = shutil.disk_usage(home)
        free_mb = free // (1024 * 1024)
        free_gb = free_mb / 1024

        if free_mb >= MIN_DISK_SPACE_MB:
            console.print(f"  [green]✓[/green] Disk space: {free_gb:.1f} GB available")
            return True, "", False
        else:
            console.print(
                f"  [yellow]⚠[/yellow] Low disk space: {free_mb} MB available",
            )
            console.print(f"    💡 Recommended: at least {MIN_DISK_SPACE_MB} MB free")
            return True, "Low disk space", True
    except OSError as e:
        console.print(f"  [yellow]○[/yellow] Could not check disk space: {e}")
        return True, "Disk check failed", True


def _check_config_files(console: Console) -> tuple[bool, str, bool]:
    """Check for config files in current directory."""
    cwd = Path.cwd()
    config_files = [
        (".pre-commit-config.yaml", "pre-commit hooks"),
        ("pyproject.toml", "project config"),
        (".dppvalidator.json", "dppvalidator config"),
    ]

    found = []
    for filename, description in config_files:
        config_path = cwd / filename
        if config_path.exists():
            found.append((filename, description))

    if found:
        for filename, description in found:
            console.print(f"  [green]✓[/green] Found {filename} ({description})")
        return True, "", False
    else:
        console.print("  [yellow]○[/yellow] No config files found in current directory")
        console.print("    💡 Run 'dppvalidator init' to create project structure")
        return True, "No config files", True


def _check_write_permissions(console: Console) -> tuple[bool, str, bool]:
    """Check write permissions for cache directory."""
    cache_dir = Path.home() / ".cache" / "dppvalidator"

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        test_file = cache_dir / ".write_test"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        console.print(f"  [green]✓[/green] Write permissions OK for {cache_dir}")
        return True, "", False
    except PermissionError:
        console.print(f"  [red]✗[/red] No write permission for {cache_dir}")
        console.print("    💡 Check directory permissions or use a different cache location")
        return False, "No write permission", False
    except OSError as e:
        console.print(f"  [yellow]○[/yellow] Could not verify write permissions: {e}")
        return True, "Permission check failed", True
