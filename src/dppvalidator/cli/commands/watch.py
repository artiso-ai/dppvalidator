"""Watch command for CLI - validates files on change."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.validators import ValidationEngine

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

EXIT_SUCCESS = 0
EXIT_ERROR = 2

# Debounce threshold to avoid validating rapidly changing files
DEBOUNCE_MS = 100


@dataclass
class WatchStats:
    """Statistics for watch session."""

    total_validations: int = 0
    total_valid: int = 0
    total_invalid: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    files_watched: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def duration_minutes(self) -> float:
        return (time.time() - self.start_time) / 60

    def record_validation(self, valid: bool, errors: int, warnings: int) -> None:
        self.total_validations += 1
        if valid:
            self.total_valid += 1
        else:
            self.total_invalid += 1
        self.total_errors += errors
        self.total_warnings += warnings


def add_parser(subparsers: Any) -> argparse.ArgumentParser:
    """Add watch subparser."""
    parser = subparsers.add_parser(
        "watch",
        help="Watch files and validate on change",
        description="Watch DPP JSON files and re-validate when they change",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory or file to watch (default: current directory)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default="*.json",
        help="Glob pattern for files to watch (default: *.json)",
    )
    parser.add_argument(
        "-s",
        "--strict",
        action="store_true",
        help="Enable strict validation",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--schema-version",
        default="0.6.1",
        help="Schema version (default: 0.6.1)",
    )
    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute watch command."""
    watch_path = Path(args.path).resolve()

    if not watch_path.exists():
        console.print_error(f"Path not found: {watch_path}")
        return EXIT_ERROR

    # Validate interval
    if args.interval < 0.1:
        console.print_error("Interval must be at least 0.1 seconds")
        return EXIT_ERROR
    if args.interval > 60:
        console.print_error("Interval cannot exceed 60 seconds")
        return EXIT_ERROR

    try:
        engine = ValidationEngine(
            schema_version=args.schema_version,
            strict_mode=args.strict,
        )
    except Exception as e:
        console.print_error(f"Failed to initialize validation engine: {e}")
        return EXIT_ERROR

    stats = WatchStats()

    # Determine files to watch
    if watch_path.is_file():
        if not _is_valid_json_file(watch_path):
            console.print_error(f"Not a valid JSON file: {watch_path}")
            return EXIT_ERROR
        files_to_watch = [watch_path]
        console.print(f"\n👁️  Watching: {watch_path}")
    else:
        files_to_watch = _find_json_files(watch_path, args.pattern)
        console.print(f"\n👁️  Watching: {watch_path}/{args.pattern}")
        console.print(f"   Found {len(files_to_watch)} file(s)")

    if not files_to_watch:
        console.print_error(f"No files matching pattern: {args.pattern}")
        console.print("   💡 Create some .json files or check your pattern")
        return EXIT_ERROR

    stats.files_watched = len(files_to_watch)
    console.print(f"   Interval: {args.interval}s")
    console.print(f"   Strict: {args.strict}")
    console.print("\nPress Ctrl+C to stop\n")
    console.print("─" * 50)

    # Track file modification times with debouncing
    file_mtimes: dict[Path, float] = {}
    last_change_time: dict[Path, float] = {}

    for f in files_to_watch:
        try:
            if f.exists():
                file_mtimes[f] = f.stat().st_mtime
        except OSError:  # pragma: no cover
            pass  # File may have been deleted

    # Initial validation
    _validate_all(files_to_watch, engine, console, stats)

    try:
        while True:  # pragma: no cover - infinite loop tested via KeyboardInterrupt
            time.sleep(args.interval)

            changed_files: list[Path] = []
            current_time = time.time()

            # Re-scan for new files if watching directory
            if watch_path.is_dir():
                try:
                    current_files = set(_find_json_files(watch_path, args.pattern))
                    watched_files = set(file_mtimes.keys())

                    # New files
                    for f in current_files - watched_files:
                        try:
                            if f.exists():
                                file_mtimes[f] = f.stat().st_mtime
                                changed_files.append(f)
                                console.print(f"\n  [blue]+[/blue] New file: {f.name}")
                        except OSError:
                            pass

                    # Removed files
                    for f in watched_files - current_files:
                        if f in file_mtimes:
                            del file_mtimes[f]
                            console.print(f"\n  [yellow]-[/yellow] Removed: {f.name}")
                except OSError as e:
                    console.print(f"\n  [yellow]⚠[/yellow] Scan error: {e}")

            # Check modification times with debouncing
            for f in list(file_mtimes.keys()):
                try:
                    if not f.exists():
                        del file_mtimes[f]
                        continue

                    current_mtime = f.stat().st_mtime
                    if current_mtime > file_mtimes[f]:
                        # Debounce: wait for file to settle
                        if (
                            f in last_change_time
                            and (current_time - last_change_time[f]) * 1000 < DEBOUNCE_MS
                        ):
                            continue

                        file_mtimes[f] = current_mtime
                        last_change_time[f] = current_time

                        if f not in changed_files:
                            changed_files.append(f)
                except OSError:
                    # File may have been deleted or is inaccessible
                    if f in file_mtimes:
                        del file_mtimes[f]

            # Validate changed files
            if changed_files:
                timestamp = time.strftime("%H:%M:%S")
                console.print(f"\n[{timestamp}] Changes detected:")
                _validate_files(changed_files, engine, console, stats)

    except KeyboardInterrupt:
        _print_summary(console, stats)
        return EXIT_SUCCESS


def _find_json_files(directory: Path, pattern: str) -> list[Path]:
    """Find JSON files matching pattern, excluding hidden directories."""
    files = []
    try:
        for f in directory.glob(f"**/{pattern}"):
            # Skip hidden directories and files
            if any(part.startswith(".") for part in f.parts):
                continue
            if f.is_file():
                files.append(f)
    except OSError:  # pragma: no cover
        pass
    return files


def _is_valid_json_file(filepath: Path) -> bool:
    """Check if file is a valid JSON file."""
    if filepath.suffix.lower() != ".json":
        return False
    try:
        json.loads(filepath.read_text())
        return True
    except (json.JSONDecodeError, OSError):
        return False


def _validate_all(
    files: list[Path],
    engine: ValidationEngine,
    console: Console,
    stats: WatchStats,
) -> None:
    """Validate all files."""
    console.print("\nInitial validation:")
    _validate_files(files, engine, console, stats)


def _validate_files(
    files: list[Path],
    engine: ValidationEngine,
    console: Console,
    stats: WatchStats,
) -> None:
    """Validate a list of files."""
    valid_count = 0
    invalid_count = 0

    for filepath in files:
        try:
            result = engine.validate_file(filepath)
            stats.record_validation(result.valid, result.error_count, result.warning_count)

            if result.valid:
                valid_count += 1
                status = "[green]✓[/green]"
            else:
                invalid_count += 1
                status = "[red]✗[/red]"

            console.print(f"  {status} {filepath.name}")

            if not result.valid:
                for err in result.errors[:3]:
                    msg = err.message[:55] + "..." if len(err.message) > 55 else err.message
                    console.print(f"      [{err.code}] {msg}")
                if result.error_count > 3:
                    console.print(f"      ... +{result.error_count - 3} more")

            if result.warning_count > 0:
                console.print(f"      ⚠️  {result.warning_count} warning(s)")

        except json.JSONDecodeError as e:
            invalid_count += 1
            console.print(f"  [red]✗[/red] {filepath.name}")
            console.print(f"      [PRS002] Invalid JSON: {e.msg} at line {e.lineno}")
        except OSError as e:  # pragma: no cover
            invalid_count += 1
            console.print(f"  [red]✗[/red] {filepath.name}")
            console.print(f"      [PRS001] File error: {e}")
        except Exception as e:  # pragma: no cover
            invalid_count += 1
            console.print(f"  [red]✗[/red] {filepath.name}")
            console.print(f"      Error: {e}")

    console.print(f"\n  Summary: {valid_count} valid, {invalid_count} invalid")


def _print_summary(console: Console, stats: WatchStats) -> None:
    """Print session summary."""
    console.print("\n" + "─" * 50)
    console.print("\n👋 Watch session summary:")
    console.print(f"   Duration: {stats.duration_minutes:.1f} minutes")
    console.print(f"   Files watched: {stats.files_watched}")
    console.print(f"   Total validations: {stats.total_validations}")
    console.print(f"   Valid: {stats.total_valid}, Invalid: {stats.total_invalid}")
    console.print(f"   Total errors: {stats.total_errors}, warnings: {stats.total_warnings}")
    console.print("")
