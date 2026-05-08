"""Unit tests for watch command - behavior-focused testing."""

import argparse
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from dppvalidator.cli.commands.watch import (
    EXIT_ERROR,
    EXIT_SUCCESS,
    FileWatcher,
    WatchLoop,
    WatchStats,
    _discover_files,
    _find_json_files,
    _is_valid_json_file,
    _print_summary,
    _validate_args,
    _validate_files,
    add_parser,
    run,
)
from dppvalidator.cli.console import Console
from dppvalidator.validators import ValidationEngine


class TestWatchStats:
    """Tests for WatchStats dataclass behavior."""

    def test_default_values(self) -> None:
        """WatchStats has correct defaults."""
        stats = WatchStats()
        assert stats.total_validations == 0
        assert stats.total_valid == 0
        assert stats.total_invalid == 0
        assert stats.total_errors == 0
        assert stats.total_warnings == 0
        assert stats.files_watched == 0

    def test_duration_minutes_calculation(self) -> None:
        """duration_minutes calculates elapsed time correctly."""
        stats = WatchStats()
        stats.start_time = time.time() - 120  # 2 minutes ago
        assert 1.9 <= stats.duration_minutes <= 2.1

    def test_record_validation_valid(self) -> None:
        """record_validation updates counters for valid result."""
        stats = WatchStats()
        stats.record_validation(valid=True, errors=0, warnings=1)

        assert stats.total_validations == 1
        assert stats.total_valid == 1
        assert stats.total_invalid == 0
        assert stats.total_errors == 0
        assert stats.total_warnings == 1

    def test_record_validation_invalid(self) -> None:
        """record_validation updates counters for invalid result."""
        stats = WatchStats()
        stats.record_validation(valid=False, errors=3, warnings=2)

        assert stats.total_validations == 1
        assert stats.total_valid == 0
        assert stats.total_invalid == 1
        assert stats.total_errors == 3
        assert stats.total_warnings == 2


class TestFileWatcher:
    """Tests for FileWatcher behavior."""

    def test_initialize_tracks_file_mtimes(self, tmp_path: Path) -> None:
        """initialize() tracks modification times for given files."""
        f1 = tmp_path / "file1.json"
        f1.write_text("{}")
        f2 = tmp_path / "file2.json"
        f2.write_text("{}")

        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json")
        watcher.initialize([f1, f2])

        assert f1 in watcher._file_mtimes
        assert f2 in watcher._file_mtimes

    def test_initialize_skips_nonexistent_files(self, tmp_path: Path) -> None:
        """initialize() skips files that don't exist."""
        nonexistent = tmp_path / "nonexistent.json"
        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json")
        watcher.initialize([nonexistent])

        assert nonexistent not in watcher._file_mtimes

    def test_get_changed_files_detects_modifications(self, tmp_path: Path) -> None:
        """get_changed_files() detects modified files."""
        f = tmp_path / "test.json"
        f.write_text("{}")

        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json")
        watcher.initialize([f])

        # Simulate file modification
        time.sleep(0.01)
        watcher._file_mtimes[f] = watcher._file_mtimes[f] - 1  # Fake older mtime

        console = MagicMock(spec=Console)
        changed = watcher.get_changed_files(console)

        assert f in changed

    def test_debouncing_prevents_rapid_changes(self, tmp_path: Path) -> None:
        """Rapid changes within debounce window are ignored."""
        f = tmp_path / "test.json"
        f.write_text("{}")

        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json", debounce_ms=1000)
        watcher.initialize([f])

        # Record a recent change
        current_time = time.time()
        watcher._last_change_time[f] = current_time - 0.1  # 100ms ago

        assert watcher._is_debounced(f, current_time) is True

    def test_debouncing_allows_after_threshold(self, tmp_path: Path) -> None:
        """Changes after debounce threshold are allowed."""
        f = tmp_path / "test.json"
        f.write_text("{}")

        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json", debounce_ms=100)
        watcher.initialize([f])

        # Record an old change
        current_time = time.time()
        watcher._last_change_time[f] = current_time - 1.0  # 1 second ago

        assert watcher._is_debounced(f, current_time) is False

    def test_scan_detects_new_files(self, tmp_path: Path) -> None:
        """_scan_for_new_and_removed() detects new files."""
        f1 = tmp_path / "file1.json"
        f1.write_text("{}")

        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json")
        watcher.initialize([f1])

        # Create a new file
        f2 = tmp_path / "file2.json"
        f2.write_text("{}")

        console = MagicMock(spec=Console)
        changed: list[Path] = []
        watcher._scan_for_new_and_removed(changed, console)

        assert f2 in changed
        console.print.assert_called()

    def test_scan_detects_removed_files(self, tmp_path: Path) -> None:
        """_scan_for_new_and_removed() detects removed files."""
        f = tmp_path / "test.json"
        f.write_text("{}")

        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json")
        watcher.initialize([f])

        # Remove the file
        f.unlink()

        console = MagicMock(spec=Console)
        changed: list[Path] = []
        watcher._scan_for_new_and_removed(changed, console)

        assert f not in watcher._file_mtimes
        console.print.assert_called()


class TestValidateArgs:
    """Tests for argument validation."""

    def test_valid_path_returns_path(self, tmp_path: Path) -> None:
        """Valid path returns resolved Path object."""
        args = argparse.Namespace(path=str(tmp_path), interval=1.0)
        console = MagicMock(spec=Console)

        result = _validate_args(args, console)
        assert result == tmp_path.resolve()

    def test_nonexistent_path_returns_none(self) -> None:
        """Nonexistent path returns None with error."""
        args = argparse.Namespace(path="/nonexistent/path", interval=1.0)
        console = MagicMock(spec=Console)

        result = _validate_args(args, console)
        assert result is None
        console.print_error.assert_called()

    def test_interval_too_small_returns_none(self, tmp_path: Path) -> None:
        """Interval < 0.1 returns None with error."""
        args = argparse.Namespace(path=str(tmp_path), interval=0.05)
        console = MagicMock(spec=Console)

        result = _validate_args(args, console)
        assert result is None
        console.print_error.assert_called_with("Interval must be at least 0.1 seconds")

    def test_interval_too_large_returns_none(self, tmp_path: Path) -> None:
        """Interval > 60 returns None with error."""
        args = argparse.Namespace(path=str(tmp_path), interval=61.0)
        console = MagicMock(spec=Console)

        result = _validate_args(args, console)
        assert result is None
        console.print_error.assert_called_with("Interval cannot exceed 60 seconds")


class TestDiscoverFiles:
    """Tests for file discovery."""

    def test_single_file_returns_list(self, tmp_path: Path) -> None:
        """Single valid JSON file returns list with one file."""
        f = tmp_path / "test.json"
        f.write_text("{}")

        console = MagicMock(spec=Console)
        result = _discover_files(f, "*.json", console)

        assert result == [f]

    def test_invalid_json_file_returns_none(self, tmp_path: Path) -> None:
        """Invalid JSON file returns None."""
        f = tmp_path / "test.txt"
        f.write_text("not json")

        console = MagicMock(spec=Console)
        result = _discover_files(f, "*.json", console)

        assert result is None

    def test_directory_finds_matching_files(self, tmp_path: Path) -> None:
        """Directory discovers files matching pattern."""
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        (tmp_path / "c.txt").write_text("text")

        console = MagicMock(spec=Console)
        result = _discover_files(tmp_path, "*.json", console)

        assert result is not None
        assert len(result) == 2

    def test_empty_directory_returns_none(self, tmp_path: Path) -> None:
        """Empty directory returns None with error."""
        console = MagicMock(spec=Console)
        result = _discover_files(tmp_path, "*.json", console)

        assert result is None
        console.print_error.assert_called()


class TestFindJsonFiles:
    """Tests for JSON file discovery."""

    def test_finds_nested_json_files(self, tmp_path: Path) -> None:
        """Finds JSON files in subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.json").write_text("{}")
        (tmp_path / "root.json").write_text("{}")

        files = _find_json_files(tmp_path, "*.json")

        assert len(files) == 2

    def test_excludes_hidden_directories(self, tmp_path: Path) -> None:
        """Excludes files in hidden directories."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.json").write_text("{}")
        (tmp_path / "visible.json").write_text("{}")

        files = _find_json_files(tmp_path, "*.json")

        assert len(files) == 1
        assert files[0].name == "visible.json"


class TestIsValidJsonFile:
    """Tests for JSON file validation."""

    def test_valid_json_returns_true(self, tmp_path: Path) -> None:
        """Valid JSON file returns True."""
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}')
        assert _is_valid_json_file(f) is True

    def test_invalid_json_returns_false(self, tmp_path: Path) -> None:
        """Invalid JSON content returns False."""
        f = tmp_path / "test.json"
        f.write_text("not json")
        assert _is_valid_json_file(f) is False

    def test_non_json_extension_returns_false(self, tmp_path: Path) -> None:
        """Non-.json extension returns False."""
        f = tmp_path / "test.txt"
        f.write_text("{}")
        assert _is_valid_json_file(f) is False


class TestValidateFiles:
    """Tests for file validation behavior."""

    def test_validates_files_and_updates_stats(self, tmp_path: Path) -> None:
        """_validate_files processes files and updates stats."""
        f = tmp_path / "test.json"
        f.write_text(
            json.dumps(
                {
                    "@context": [
                        "https://www.w3.org/ns/credentials/v2",
                        "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
                    ],
                    "id": "https://example.com/dpp",
                    "issuer": {"id": "https://example.com/issuer"},
                }
            )
        )

        engine = ValidationEngine(layers=["model"])
        console = MagicMock(spec=Console)
        stats = WatchStats()

        _validate_files([f], engine, console, stats)

        assert stats.total_validations == 1
        console.print.assert_called()

    def test_handles_json_decode_error(self, tmp_path: Path) -> None:
        """_validate_files handles invalid JSON gracefully."""
        f = tmp_path / "bad.json"
        f.write_text("{invalid json")

        engine = ValidationEngine(layers=["model"])
        console = MagicMock(spec=Console)
        stats = WatchStats()

        _validate_files([f], engine, console, stats)

        # Should print error but not crash
        assert any("PRS002" in str(call) for call in console.print.call_args_list)


class TestPrintSummary:
    """Tests for summary printing."""

    def test_prints_session_summary(self) -> None:
        """_print_summary outputs session statistics."""
        stats = WatchStats()
        stats.total_validations = 10
        stats.total_valid = 8
        stats.total_invalid = 2
        stats.total_errors = 5
        stats.total_warnings = 3
        stats.files_watched = 4

        console = MagicMock(spec=Console)
        _print_summary(console, stats)

        calls = [str(call) for call in console.print.call_args_list]
        assert any("10" in c for c in calls)
        assert any("8" in c for c in calls)


class TestAddParser:
    """Tests for argument parser setup."""

    def test_adds_watch_subparser(self) -> None:
        """add_parser creates watch subparser with expected arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        watch_parser = add_parser(subparsers)

        assert watch_parser is not None
        # Parse with defaults
        args = watch_parser.parse_args([])
        assert args.path == "."
        assert args.pattern == "*.json"
        assert args.interval == 1.0


class TestRunCommand:
    """Tests for the main run command."""

    def test_run_with_nonexistent_path_returns_error(self) -> None:
        """run() with nonexistent path returns EXIT_ERROR."""
        args = argparse.Namespace(
            path="/nonexistent/path",
            pattern="*.json",
            interval=1.0,
            strict=False,
            schema_version="0.6.1",
        )
        console = MagicMock(spec=Console)

        result = run(args, console)
        assert result == EXIT_ERROR

    def test_run_with_no_matching_files_returns_error(self, tmp_path: Path) -> None:
        """run() with no matching files returns EXIT_ERROR."""
        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            interval=1.0,
            strict=False,
            schema_version="0.6.1",
        )
        console = MagicMock(spec=Console)

        result = run(args, console)
        assert result == EXIT_ERROR


class TestWatchLoop:
    """Tests for WatchLoop behavior."""

    def test_run_handles_keyboard_interrupt(self, tmp_path: Path) -> None:
        """WatchLoop.run() handles KeyboardInterrupt gracefully."""
        f = tmp_path / "test.json"
        f.write_text("{}")

        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json")
        engine = ValidationEngine(layers=["model"])
        console = MagicMock(spec=Console)
        stats = WatchStats()

        loop = WatchLoop(
            watcher=watcher,
            engine=engine,
            console=console,
            stats=stats,
            interval=0.1,
        )

        # Patch _loop to raise KeyboardInterrupt
        with patch.object(loop, "_loop", side_effect=KeyboardInterrupt):
            result = loop.run([f])

        assert result == EXIT_SUCCESS

    def test_print_header_sets_files_watched(self, tmp_path: Path) -> None:
        """_print_header sets files_watched in stats."""
        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json")
        engine = ValidationEngine(layers=["model"])
        console = MagicMock(spec=Console)
        stats = WatchStats()

        loop = WatchLoop(
            watcher=watcher,
            engine=engine,
            console=console,
            stats=stats,
            interval=1.0,
        )

        files = [tmp_path / "a.json", tmp_path / "b.json"]
        loop._print_header(files)

        assert stats.files_watched == 2

    def test_on_change_validates_changed_files(self, tmp_path: Path) -> None:
        """_on_change validates the provided files."""
        f = tmp_path / "test.json"
        f.write_text('{"id": "test"}')

        watcher = FileWatcher(watch_path=tmp_path, pattern="*.json")
        engine = ValidationEngine(layers=["model"])
        console = MagicMock(spec=Console)
        stats = WatchStats()

        loop = WatchLoop(
            watcher=watcher,
            engine=engine,
            console=console,
            stats=stats,
            interval=1.0,
        )

        loop._on_change([f])

        assert stats.total_validations == 1
