"""Watch command for CLI - validates files on change."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION
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


@dataclass
class FileWatcher:
    """Handles file change detection with debouncing (Single Responsibility)."""

    watch_path: Path
    pattern: str
    debounce_ms: int = DEBOUNCE_MS

    _file_mtimes: dict[Path, float] = field(default_factory=dict)
    _last_change_time: dict[Path, float] = field(default_factory=dict)

    def initialize(self, files: list[Path]) -> None:
        """Initialize tracking for given files."""
        for f in files:
            try:
                if f.exists():
                    self._file_mtimes[f] = f.stat().st_mtime
            except OSError:
                pass

    def get_changed_files(self, console: Console) -> list[Path]:
        """Detect changed files since last check."""
        changed: list[Path] = []
        current_time = time.time()

        if self.watch_path.is_dir():
            self._scan_for_new_and_removed(changed, console)

        self._check_modifications(changed, current_time)
        return changed

    def _scan_for_new_and_removed(self, changed: list[Path], console: Console) -> None:
        """Scan directory for new and removed files."""
        try:
            current_files = set(_find_json_files(self.watch_path, self.pattern))
            watched_files = set(self._file_mtimes.keys())

            for f in current_files - watched_files:
                self._track_new_file(f, changed, console)

            for f in watched_files - current_files:
                self._handle_removed(f, console)
        except OSError as e:
            console.print(f"\n  [yellow]⚠[/yellow] Scan error: {e}")

    def _track_new_file(self, f: Path, changed: list[Path], console: Console) -> None:
        """Track a newly discovered file."""
        try:
            if f.exists():
                self._file_mtimes[f] = f.stat().st_mtime
                changed.append(f)
                console.print(f"\n  [blue]+[/blue] New file: {f.name}")
        except OSError:
            pass

    def _handle_removed(self, f: Path, console: Console) -> None:
        """Handle a removed file."""
        if f in self._file_mtimes:
            del self._file_mtimes[f]
            console.print(f"\n  [yellow]-[/yellow] Removed: {f.name}")

    def _check_modifications(self, changed: list[Path], current_time: float) -> None:
        """Check for modified files with debouncing."""
        for f in list(self._file_mtimes.keys()):
            try:
                if not f.exists():
                    del self._file_mtimes[f]
                    continue

                current_mtime = f.stat().st_mtime
                if current_mtime > self._file_mtimes[f]:
                    if self._is_debounced(f, current_time):
                        continue

                    self._file_mtimes[f] = current_mtime
                    self._last_change_time[f] = current_time

                    if f not in changed:
                        changed.append(f)
            except OSError:
                if f in self._file_mtimes:
                    del self._file_mtimes[f]

    def _is_debounced(self, f: Path, current_time: float) -> bool:
        """Check if file change should be debounced."""
        if f not in self._last_change_time:
            return False
        return (current_time - self._last_change_time[f]) * 1000 < self.debounce_ms


@dataclass
class WatchLoop:
    """Orchestrates the watch loop lifecycle (Single Responsibility)."""

    watcher: FileWatcher
    engine: ValidationEngine
    console: Console
    stats: WatchStats
    interval: float

    def run(self, initial_files: list[Path]) -> int:
        """Execute the main watch loop."""
        self._print_header(initial_files)
        self.watcher.initialize(initial_files)
        _validate_all(initial_files, self.engine, self.console, self.stats)

        try:
            self._loop()
        except KeyboardInterrupt:
            _print_summary(self.console, self.stats)
            return EXIT_SUCCESS
        return EXIT_SUCCESS  # pragma: no cover

    def _print_header(self, files: list[Path]) -> None:
        """Print watch session header."""
        self.stats.files_watched = len(files)
        self.console.print(f"   Interval: {self.interval}s")
        self.console.print(f"   Strict: {self.engine.strict_mode}")
        self.console.print("\nPress Ctrl+C to stop\n")
        self.console.print("─" * 50)

    def _loop(self) -> None:
        """Main polling loop."""
        while True:  # pragma: no cover - infinite loop tested via KeyboardInterrupt
            time.sleep(self.interval)
            changed = self.watcher.get_changed_files(self.console)
            if changed:
                self._on_change(changed)

    def _on_change(self, files: list[Path]) -> None:
        """Handle detected file changes."""
        timestamp = time.strftime("%H:%M:%S")
        self.console.print(f"\n[{timestamp}] Changes detected:")
        _validate_files(files, self.engine, self.console, self.stats)


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
        default="auto",
        help=(
            "UNTP DPP schema version. Defaults to 'auto' — detected "
            "from each watched payload's $schema or @context. Pass an "
            "explicit version to fail-fast on payloads that declare a "
            f"different one. Default-version fallback: {DEFAULT_SCHEMA_VERSION}."
        ),
    )
    return parser


def _validate_args(args: argparse.Namespace, console: Console) -> Path | None:
    """Validate command arguments. Returns watch_path or None on error."""
    watch_path = Path(args.path).resolve()

    if not watch_path.exists():
        console.print_error(f"Path not found: {watch_path}")
        return None

    if args.interval < 0.1:
        console.print_error("Interval must be at least 0.1 seconds")
        return None

    if args.interval > 60:
        console.print_error("Interval cannot exceed 60 seconds")
        return None

    return watch_path


def _discover_files(watch_path: Path, pattern: str, console: Console) -> list[Path] | None:
    """Discover files to watch. Returns file list or None on error."""
    if watch_path.is_file():
        if not _is_valid_json_file(watch_path):
            console.print_error(f"Not a valid JSON file: {watch_path}")
            return None
        console.print(f"\n👁️  Watching: {watch_path}")
        return [watch_path]

    files = _find_json_files(watch_path, pattern)
    console.print(f"\n👁️  Watching: {watch_path}/{pattern}")
    console.print(f"   Found {len(files)} file(s)")

    if not files:
        console.print_error(f"No files matching pattern: {pattern}")
        console.print("   💡 Create some .json files or check your pattern")
        return None

    return files


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute watch command."""
    watch_path = _validate_args(args, console)
    if watch_path is None:
        return EXIT_ERROR

    try:
        engine = ValidationEngine(
            schema_version=args.schema_version,
            strict_mode=args.strict,
        )
    except Exception as e:
        console.print_error(f"Failed to initialize validation engine: {e}")
        return EXIT_ERROR

    files_to_watch = _discover_files(watch_path, args.pattern, console)
    if files_to_watch is None:
        return EXIT_ERROR

    watcher = FileWatcher(watch_path=watch_path, pattern=args.pattern)
    stats = WatchStats()
    loop = WatchLoop(
        watcher=watcher,
        engine=engine,
        console=console,
        stats=stats,
        interval=args.interval,
    )

    return loop.run(files_to_watch)


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
        json.loads(filepath.read_text(encoding="utf-8"))
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
