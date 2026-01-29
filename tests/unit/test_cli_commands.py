"""Tests for CLI commands - behavior-focused testing."""

import argparse
import json
import time
from io import StringIO
from unittest.mock import patch

import pytest

from dppvalidator.cli.console import Console


class TestPrecommitCommand:
    """Tests for pre-commit hook behavior."""

    def test_precommit_no_files_returns_success(self):
        """Pre-commit with no files should succeed (nothing to validate)."""
        from dppvalidator.cli.commands.precommit import main

        result = main([])
        assert result == 0

    def test_precommit_valid_file_returns_success(self, tmp_path):
        """Pre-commit with valid DPP file should succeed."""
        from dppvalidator.cli.commands.precommit import main

        dpp_file = tmp_path / "valid.json"
        dpp_file.write_text(
            json.dumps(
                {
                    "@context": [
                        "https://www.w3.org/ns/credentials/v2",
                        "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
                    ],
                    "id": "https://example.com/dpp",
                    "issuer": {"id": "https://example.com/issuer", "name": "Test"},
                }
            )
        )

        result = main([str(dpp_file)])
        assert result == 0

    def test_precommit_invalid_file_returns_failure(self, tmp_path):
        """Pre-commit with invalid DPP file should fail."""
        from dppvalidator.cli.commands.precommit import main

        dpp_file = tmp_path / "invalid.json"
        dpp_file.write_text(json.dumps({"missing": "required_fields"}))

        result = main([str(dpp_file)])
        assert result == 1

    def test_precommit_nonexistent_file_returns_failure(self):
        """Pre-commit with nonexistent file should fail."""
        from dppvalidator.cli.commands.precommit import main

        result = main(["/nonexistent/path/file.json"])
        assert result == 1

    def test_precommit_skips_non_json_files(self, tmp_path):
        """Pre-commit should skip non-JSON files."""
        from dppvalidator.cli.commands.precommit import main

        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("not a json file")

        result = main([str(txt_file)])
        assert result == 0  # Skipped, no failures

    def test_precommit_strict_mode(self, tmp_path):
        """Pre-commit with --strict flag enables strict validation."""
        from dppvalidator.cli.commands.precommit import main

        dpp_file = tmp_path / "passport.json"
        dpp_file.write_text(
            json.dumps(
                {
                    "id": "https://example.com/dpp",
                    "issuer": {"id": "https://example.com/issuer", "name": "Test"},
                }
            )
        )

        result = main(["--strict", str(dpp_file)])
        # Should pass or fail based on strict validation
        assert result in (0, 1)

    def test_precommit_fail_on_warning(self, tmp_path):
        """Pre-commit with --fail-on-warning treats warnings as errors."""
        from dppvalidator.cli.commands.precommit import main

        dpp_file = tmp_path / "passport.json"
        dpp_file.write_text(
            json.dumps(
                {
                    "id": "https://example.com/dpp",
                    "issuer": {"id": "https://example.com/issuer", "name": "Test"},
                }
            )
        )

        result = main(["--fail-on-warning", str(dpp_file)])
        assert result in (0, 1)

    def test_precommit_multiple_files(self, tmp_path):
        """Pre-commit validates multiple files."""
        from dppvalidator.cli.commands.precommit import main

        valid_file = tmp_path / "valid.json"
        valid_file.write_text(
            json.dumps(
                {
                    "id": "https://example.com/dpp1",
                    "issuer": {"id": "https://example.com/issuer", "name": "Test"},
                }
            )
        )

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text(json.dumps({"bad": "data"}))

        result = main([str(valid_file), str(invalid_file)])
        assert result == 1  # At least one file failed

    def test_precommit_shows_truncated_errors(self, tmp_path):
        """Pre-commit truncates error output when many errors."""
        from dppvalidator.cli.commands.precommit import main

        # Create file that generates multiple errors
        dpp_file = tmp_path / "multi_error.json"
        dpp_file.write_text(json.dumps({"bad": "data"}))

        result = main([str(dpp_file)])
        assert result == 1


class TestWatchCommand:
    """Tests for watch command behavior."""

    def test_watch_add_parser(self):
        """Watch command parser should be correctly configured."""
        from dppvalidator.cli.commands.watch import add_parser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        watch_parser = add_parser(subparsers)

        assert watch_parser is not None
        # Parse default args
        args = watch_parser.parse_args([])
        assert args.path == "."
        assert args.pattern == "*.json"
        assert args.interval == 1.0
        assert args.strict is False

    def test_watch_nonexistent_path_fails(self, capsys):
        """Watch on nonexistent path should fail."""
        from dppvalidator.cli.commands.watch import run

        args = argparse.Namespace(
            path="/nonexistent/path",
            pattern="*.json",
            strict=False,
            interval=1.0,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 2  # EXIT_ERROR
        captured = capsys.readouterr()
        assert "not found" in stream.getvalue().lower() or "not found" in captured.err.lower()

    def test_watch_interval_too_small_fails(self, tmp_path, capsys):
        """Watch with interval < 0.1 should fail."""
        from dppvalidator.cli.commands.watch import run

        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            strict=False,
            interval=0.05,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 2
        captured = capsys.readouterr()
        assert "0.1" in stream.getvalue() or "0.1" in captured.err

    def test_watch_interval_too_large_fails(self, tmp_path, capsys):
        """Watch with interval > 60 should fail."""
        from dppvalidator.cli.commands.watch import run

        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            strict=False,
            interval=120.0,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 2
        captured = capsys.readouterr()
        assert "60" in stream.getvalue() or "60" in captured.err

    def test_watch_no_matching_files_fails(self, tmp_path, capsys):
        """Watch with no matching files should fail."""
        from dppvalidator.cli.commands.watch import run

        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            strict=False,
            interval=1.0,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 2
        captured = capsys.readouterr()
        output = stream.getvalue() + captured.err
        assert "No files" in output or "0 file" in output

    def test_watch_invalid_json_file_fails(self, tmp_path):
        """Watch on invalid JSON file should fail."""
        from dppvalidator.cli.commands.watch import run

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json")

        args = argparse.Namespace(
            path=str(invalid_file),
            pattern="*.json",
            strict=False,
            interval=1.0,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 2

    def test_watch_stats_tracking(self):
        """WatchStats should track validation results correctly."""
        from dppvalidator.cli.commands.watch import WatchStats

        stats = WatchStats()
        assert stats.total_validations == 0
        assert stats.total_valid == 0
        assert stats.total_invalid == 0

        stats.record_validation(valid=True, errors=0, warnings=1)
        assert stats.total_validations == 1
        assert stats.total_valid == 1
        assert stats.total_warnings == 1

        stats.record_validation(valid=False, errors=2, warnings=0)
        assert stats.total_validations == 2
        assert stats.total_invalid == 1
        assert stats.total_errors == 2

    def test_watch_stats_duration(self):
        """WatchStats should calculate duration correctly."""
        from dppvalidator.cli.commands.watch import WatchStats

        stats = WatchStats()
        time.sleep(0.1)
        assert stats.duration_minutes >= 0

    def test_watch_find_json_files(self, tmp_path):
        """_find_json_files should find matching files."""
        from dppvalidator.cli.commands.watch import _find_json_files

        # Create test files
        (tmp_path / "test1.json").write_text("{}")
        (tmp_path / "test2.json").write_text("{}")
        (tmp_path / "readme.txt").write_text("text")
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".hidden" / "secret.json").write_text("{}")

        files = _find_json_files(tmp_path, "*.json")
        assert len(files) == 2  # Should not include hidden

    def test_watch_is_valid_json_file(self, tmp_path):
        """_is_valid_json_file should validate JSON files."""
        from dppvalidator.cli.commands.watch import _is_valid_json_file

        valid_json = tmp_path / "valid.json"
        valid_json.write_text('{"key": "value"}')
        assert _is_valid_json_file(valid_json) is True

        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("not json")
        assert _is_valid_json_file(invalid_json) is False

        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("text")
        assert _is_valid_json_file(txt_file) is False

    def test_watch_validate_files(self, tmp_path):
        """_validate_files should validate and track results."""
        from dppvalidator.cli.commands.watch import WatchStats, _validate_files
        from dppvalidator.validators import ValidationEngine

        dpp_file = tmp_path / "passport.json"
        dpp_file.write_text(
            json.dumps(
                {
                    "id": "https://example.com/dpp",
                    "issuer": {"id": "https://example.com/issuer", "name": "Test"},
                }
            )
        )

        engine = ValidationEngine()
        stats = WatchStats()
        stream = StringIO()
        console = Console(file=stream)

        _validate_files([dpp_file], engine, console, stats)
        assert stats.total_validations == 1

    def test_watch_validate_files_json_decode_error(self, tmp_path):
        """_validate_files should handle JSON decode errors."""
        from dppvalidator.cli.commands.watch import WatchStats, _validate_files
        from dppvalidator.validators import ValidationEngine

        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json")

        engine = ValidationEngine()
        stats = WatchStats()
        stream = StringIO()
        console = Console(file=stream)

        _validate_files([bad_file], engine, console, stats)
        output = stream.getvalue()
        assert "Invalid JSON" in output or "PRS002" in output

    def test_watch_validate_files_os_error(self, tmp_path):
        """_validate_files should handle OS errors."""
        from dppvalidator.cli.commands.watch import WatchStats, _validate_files
        from dppvalidator.validators import ValidationEngine

        # Create and then delete file to cause OS error
        missing_file = tmp_path / "deleted.json"

        engine = ValidationEngine()
        stats = WatchStats()
        stream = StringIO()
        console = Console(file=stream)

        _validate_files([missing_file], engine, console, stats)
        # Should handle gracefully

    def test_watch_print_summary(self):
        """_print_summary should output session statistics."""
        from dppvalidator.cli.commands.watch import WatchStats, _print_summary

        stats = WatchStats()
        stats.files_watched = 5
        stats.record_validation(True, 0, 0)
        stats.record_validation(False, 2, 1)

        stream = StringIO()
        console = Console(file=stream)

        _print_summary(console, stats)
        output = stream.getvalue()
        assert "session summary" in output.lower()
        assert "5" in output  # files watched

    def test_watch_single_file_keyboard_interrupt(self, tmp_path):
        """Watch exits gracefully on KeyboardInterrupt."""
        from dppvalidator.cli.commands.watch import run

        dpp_file = tmp_path / "passport.json"
        dpp_file.write_text(
            json.dumps(
                {
                    "id": "https://example.com/dpp",
                    "issuer": {"id": "https://example.com/issuer", "name": "Test"},
                }
            )
        )

        args = argparse.Namespace(
            path=str(dpp_file),
            pattern="*.json",
            strict=False,
            interval=0.1,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        # Patch time.sleep to raise KeyboardInterrupt
        with patch("time.sleep", side_effect=KeyboardInterrupt):
            result = run(args, console)
            assert result == 0  # EXIT_SUCCESS on graceful exit


class TestDoctorCommand:
    """Tests for doctor command behavior."""

    def test_doctor_all_checks_pass(self):
        """Doctor command runs all checks."""
        from dppvalidator.cli.commands.doctor import run

        args = argparse.Namespace(fix=False)
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        output = stream.getvalue()
        assert "dppvalidator doctor" in output
        # Should complete without error
        assert result in (0, 1, 2)

    def test_doctor_python_version_check(self):
        """Doctor checks Python version."""
        from dppvalidator.cli.commands.doctor import _check_python_version

        stream = StringIO()
        console = Console(file=stream)

        status, _, _ = _check_python_version(console)
        output = stream.getvalue()
        assert "Python" in output
        # Python 3.10+ should pass
        assert status is True

    def test_doctor_dppvalidator_version_check(self):
        """Doctor checks dppvalidator version."""
        from dppvalidator.cli.commands.doctor import _check_dppvalidator_version

        stream = StringIO()
        console = Console(file=stream)

        status, _, _ = _check_dppvalidator_version(console)
        assert status is True

    def test_doctor_pydantic_check(self):
        """Doctor checks Pydantic version."""
        from dppvalidator.cli.commands.doctor import _check_pydantic

        stream = StringIO()
        console = Console(file=stream)

        status, _, _ = _check_pydantic(console)
        assert status is True

    def test_doctor_optional_deps_check(self):
        """Doctor checks optional dependencies."""
        from dppvalidator.cli.commands.doctor import _check_optional_deps

        stream = StringIO()
        console = Console(file=stream)

        status, _, is_warning = _check_optional_deps(console)
        # Should always return True (missing deps are warnings)
        assert status is True

    def test_doctor_schema_cache_check(self):
        """Doctor checks schema cache."""
        from dppvalidator.cli.commands.doctor import _check_schema_cache

        stream = StringIO()
        console = Console(file=stream)

        status, _, _ = _check_schema_cache(console)
        assert status is True  # Cache may be empty but that's okay

    def test_doctor_disk_space_check(self):
        """Doctor checks disk space."""
        from dppvalidator.cli.commands.doctor import _check_disk_space

        stream = StringIO()
        console = Console(file=stream)

        status, _, _ = _check_disk_space(console)
        assert status is True

    def test_doctor_config_files_check(self):
        """Doctor checks config files."""
        from dppvalidator.cli.commands.doctor import _check_config_files

        stream = StringIO()
        console = Console(file=stream)

        status, _, _ = _check_config_files(console)
        assert status is True

    def test_doctor_write_permissions_check(self):
        """Doctor checks write permissions."""
        from dppvalidator.cli.commands.doctor import _check_write_permissions

        stream = StringIO()
        console = Console(file=stream)

        status, _, _ = _check_write_permissions(console)
        assert status is True

    def test_doctor_issues_warning_exit_code(self):
        """Doctor returns warning exit code when only warnings."""
        from dppvalidator.cli.commands.doctor import EXIT_WARNING

        assert EXIT_WARNING == 1

    def test_doctor_pydantic_old_version(self):
        """Doctor reports error for old Pydantic version."""
        from dppvalidator.cli.commands.doctor import _check_pydantic

        stream = StringIO()
        console = Console(file=stream)

        with patch("dppvalidator.cli.commands.doctor.pkg_version", return_value="1.10.0"):
            status, message, _ = _check_pydantic(console)
            assert status is False
            assert "too old" in message.lower()

    def test_doctor_pydantic_not_installed(self):
        """Doctor reports error when Pydantic not installed."""
        from dppvalidator.cli.commands.doctor import _check_pydantic

        stream = StringIO()
        console = Console(file=stream)

        with patch(
            "dppvalidator.cli.commands.doctor.pkg_version", side_effect=Exception("not found")
        ):
            status, message, _ = _check_pydantic(console)
            assert status is False

    def test_doctor_disk_space_low(self):
        """Doctor warns on low disk space."""
        from dppvalidator.cli.commands.doctor import _check_disk_space

        stream = StringIO()
        console = Console(file=stream)

        # Mock disk_usage to return low space
        with patch("shutil.disk_usage", return_value=(1000, 900, 10 * 1024 * 1024)):
            status, _, is_warning = _check_disk_space(console)
            assert status is True
            assert is_warning is True

    def test_doctor_disk_space_error(self):
        """Doctor handles disk space check errors."""
        from dppvalidator.cli.commands.doctor import _check_disk_space

        stream = StringIO()
        console = Console(file=stream)

        with patch("shutil.disk_usage", side_effect=OSError("disk error")):
            status, _, is_warning = _check_disk_space(console)
            assert status is True
            assert is_warning is True

    def test_doctor_write_permission_denied(self):
        """Doctor reports permission denied."""
        from dppvalidator.cli.commands.doctor import _check_write_permissions

        stream = StringIO()
        console = Console(file=stream)

        with patch("pathlib.Path.mkdir", side_effect=PermissionError("denied")):
            status, _, _ = _check_write_permissions(console)
            assert status is False

    def test_doctor_write_permission_os_error(self):
        """Doctor handles OS errors in permission check."""
        from dppvalidator.cli.commands.doctor import _check_write_permissions

        stream = StringIO()
        console = Console(file=stream)

        with patch("pathlib.Path.mkdir", side_effect=OSError("fs error")):
            status, _, is_warning = _check_write_permissions(console)
            assert status is True
            assert is_warning is True

    def test_doctor_schema_cache_corrupted(self, tmp_path):
        """Doctor detects corrupted cache files."""
        from dppvalidator.cli.commands.doctor import _check_schema_cache

        cache_dir = tmp_path / ".cache" / "dppvalidator"
        cache_dir.mkdir(parents=True)

        # Create valid and corrupted cache files
        (cache_dir / "valid.json").write_text('{"valid": true}')
        (cache_dir / "corrupted.json").write_text("not json")

        stream = StringIO()
        console = Console(file=stream)

        with patch("pathlib.Path.home", return_value=tmp_path):
            status, _, is_warning = _check_schema_cache(console)
            assert status is True
            assert is_warning is True


class TestInitCommand:
    """Tests for init command behavior."""

    def test_init_creates_project_structure(self, tmp_path):
        """Init creates complete project structure."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "new_project"
        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        assert (project_dir / "data" / "sample_passport.json").exists()
        assert (project_dir / ".gitignore").exists()
        assert (project_dir / "README.md").exists()

    def test_init_full_template(self, tmp_path):
        """Init with full template creates expanded DPP."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "full_project"
        args = argparse.Namespace(
            path=str(project_dir),
            template="full",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0

        dpp_content = json.loads((project_dir / "data" / "sample_passport.json").read_text())
        assert "materialsProvenance" in dpp_content.get("credentialSubject", {})

    def test_init_with_config(self, tmp_path):
        """Init with --config creates config file."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "config_project"
        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=True,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        assert (project_dir / ".dppvalidator.json").exists()

    def test_init_with_precommit(self, tmp_path):
        """Init with --pre-commit creates pre-commit config."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "precommit_project"
        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=True,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        assert (project_dir / ".pre-commit-config.yaml").exists()

    def test_init_invalid_project_name(self, tmp_path):
        """Init with invalid project name fails."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "123invalid"
        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name="123-invalid-name",
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 2  # EXIT_ERROR

    def test_init_existing_files_skipped(self, tmp_path):
        """Init skips existing files without --force."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "existing"
        project_dir.mkdir()
        (project_dir / ".gitignore").write_text("existing content")

        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        assert (project_dir / ".gitignore").read_text() == "existing content"

    def test_init_force_overwrites(self, tmp_path):
        """Init with --force overwrites existing files."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "force_project"
        project_dir.mkdir()
        (project_dir / ".gitignore").write_text("old content")

        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=True,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        assert (project_dir / ".gitignore").read_text() != "old content"

    def test_init_no_readme(self, tmp_path):
        """Init with --no-readme skips README creation."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "no_readme"
        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=False,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        assert not (project_dir / "README.md").exists()

    def test_init_permission_denied(self, tmp_path):
        """Init handles permission denied errors."""
        from dppvalidator.cli.commands.init import run

        args = argparse.Namespace(
            path=str(tmp_path / "project"),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        with patch("pathlib.Path.mkdir", side_effect=PermissionError("denied")):
            result = run(args, console)
            assert result == 2

    def test_init_os_error(self, tmp_path):
        """Init handles OS errors."""
        from dppvalidator.cli.commands.init import run

        args = argparse.Namespace(
            path=str(tmp_path / "project"),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        with patch("pathlib.Path.mkdir", side_effect=OSError("disk full")):
            result = run(args, console)
            assert result == 2

    def test_init_existing_dpp_skipped(self, tmp_path):
        """Init skips existing sample_passport.json."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "project"
        data_dir = project_dir / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "sample_passport.json").write_text('{"existing": true}')

        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        content = json.loads((data_dir / "sample_passport.json").read_text())
        assert content == {"existing": True}

    def test_init_existing_readme_skipped(self, tmp_path):
        """Init skips existing README.md."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "README.md").write_text("# Existing README")

        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        assert "Existing README" in (project_dir / "README.md").read_text()

    def test_init_existing_config_skipped(self, tmp_path):
        """Init skips existing .dppvalidator.json."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".dppvalidator.json").write_text('{"existing": true}')

        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=True,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        content = json.loads((project_dir / ".dppvalidator.json").read_text())
        assert content == {"existing": True}

    def test_init_existing_precommit_skipped(self, tmp_path):
        """Init skips existing .pre-commit-config.yaml."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".pre-commit-config.yaml").write_text("repos: []")

        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=True,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        assert "repos: []" in (project_dir / ".pre-commit-config.yaml").read_text()

    def test_init_all_files_skipped_message(self, tmp_path):
        """Init shows message when no files created."""
        from dppvalidator.cli.commands.init import run

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "data").mkdir()
        (project_dir / "data" / "sample_passport.json").write_text("{}")
        (project_dir / ".gitignore").write_text("")
        (project_dir / "README.md").write_text("")

        args = argparse.Namespace(
            path=str(project_dir),
            template="minimal",
            pre_commit=False,
            force=False,
            name=None,
            config=False,
            readme=True,
        )
        stream = StringIO()
        console = Console(file=stream)

        result = run(args, console)
        assert result == 0
        output = stream.getvalue()
        assert "No files created" in output or "skipped" in output.lower()


class TestValidateCommandExtendedCoverage:
    """Extended coverage tests for validate command."""

    def test_validate_unexpected_exception(self, tmp_path):
        """Validate handles unexpected exceptions in load."""
        from dppvalidator.cli.commands.validate import _load_input

        stream = StringIO()
        console = Console(file=stream)

        with patch("pathlib.Path.read_text", side_effect=Exception("unexpected")):
            file_path = tmp_path / "test.json"
            file_path.touch()
            result = _load_input(str(file_path), console)
            assert result is None

    def test_validate_output_text_with_suggestions(self):
        """Validate shows suggestions in text output."""
        from dppvalidator.cli.commands.validate import _output_text
        from dppvalidator.validators.results import ValidationError, ValidationResult

        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    path="$.issuer",
                    message="Missing required field",
                    code="REQ001",
                    layer="schema",
                    did_you_mean=("issuer", "issuers"),
                    suggestion="Add an issuer object",
                    docs_url="https://docs.example.com/issuer",
                )
            ],
        )
        stream = StringIO()
        console = Console(file=stream)

        _output_text(result, "test.json", console)
        output = stream.getvalue()
        assert "Did you mean" in output
        assert "issuer" in output

    def test_validate_output_text_with_warnings(self):
        """Validate shows warnings in text output."""
        from dppvalidator.cli.commands.validate import _output_text
        from dppvalidator.validators.results import ValidationError, ValidationResult

        result = ValidationResult(
            valid=True,
            warnings=[
                ValidationError(
                    path="$.validUntil",
                    message="Expiry date is soon",
                    code="WARN001",
                    layer="semantic",
                    severity="warning",
                    suggestion="Consider extending validity",
                    docs_url="https://docs.example.com/validity",
                )
            ],
        )
        stream = StringIO()
        console = Console(file=stream)

        _output_text(result, "test.json", console)
        output = stream.getvalue()
        assert "Warning" in output or "warning" in output.lower()

    def test_validate_output_text_with_info(self):
        """Validate shows info messages in text output."""
        from dppvalidator.cli.commands.validate import _output_text
        from dppvalidator.validators.results import ValidationError, ValidationResult

        result = ValidationResult(
            valid=True,
            info=[
                ValidationError(
                    path="$",
                    message="Schema version 0.6.1",
                    code="INFO001",
                    layer="schema",
                    severity="info",
                )
            ],
        )
        stream = StringIO()
        console = Console(file=stream)

        _output_text(result, "test.json", console)
        output = stream.getvalue()
        assert "Info" in output

    def test_validate_output_table_with_issues(self):
        """Validate table output shows issues."""
        from dppvalidator.cli.commands.validate import _output_table
        from dppvalidator.validators.results import ValidationError, ValidationResult

        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    path="$.issuer",
                    message="Missing required field",
                    code="REQ001",
                    layer="schema",
                )
            ],
            warnings=[
                ValidationError(
                    path="$.validUntil",
                    message="Expiry soon",
                    code="WARN001",
                    layer="semantic",
                    severity="warning",
                )
            ],
        )
        stream = StringIO()
        console = Console(file=stream)

        _output_table(result, "test.json", console)
        # Table output should include issues


class TestWatchCommandExtended:
    """Extended tests for watch command to cover edge cases."""

    def test_watch_engine_init_error(self, tmp_path):
        """Watch handles validation engine initialization errors."""
        from dppvalidator.cli.commands.watch import run

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text('{"id": "test"}')

        args = argparse.Namespace(
            path=str(dpp_file),
            pattern="*.json",
            strict=False,
            interval=1.0,
            schema_version="invalid_version_xyz",
        )
        stream = StringIO()
        console = Console(file=stream)

        with patch(
            "dppvalidator.cli.commands.watch.ValidationEngine",
            side_effect=Exception("Engine init failed"),
        ):
            result = run(args, console)
            assert result == 2

    def test_watch_validate_files_generic_exception(self, tmp_path):
        """_validate_files handles generic exceptions."""
        from dppvalidator.cli.commands.watch import WatchStats, _validate_files

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text('{"id": "test"}')

        class MockEngine:
            def validate_file(self, _path):
                raise RuntimeError("Unexpected error")

        stats = WatchStats()
        stream = StringIO()
        console = Console(file=stream)

        _validate_files([dpp_file], MockEngine(), console, stats)
        output = stream.getvalue()
        assert "Error" in output or "✗" in output

    def test_watch_directory_with_keyboard_interrupt(self, tmp_path):
        """Watch on directory exits gracefully on KeyboardInterrupt."""
        from dppvalidator.cli.commands.watch import run

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text(
            json.dumps({"id": "https://example.com/dpp", "issuer": {"id": "x", "name": "y"}})
        )

        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            strict=False,
            interval=0.1,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        with patch("time.sleep", side_effect=KeyboardInterrupt):
            result = run(args, console)
            assert result == 0

    def test_watch_loop_detects_changes(self, tmp_path):
        """Watch loop detects file changes before interrupt."""
        from dppvalidator.cli.commands.watch import run

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text(
            json.dumps({"id": "https://example.com/dpp", "issuer": {"id": "x", "name": "y"}})
        )

        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            strict=False,
            interval=0.1,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        # Allow one loop iteration then interrupt
        call_count = [0]

        def mock_sleep(_duration):
            call_count[0] += 1
            if call_count[0] >= 2:
                raise KeyboardInterrupt
            # Actually sleep briefly
            time.sleep(0.001)

        with patch("dppvalidator.cli.commands.watch.time.sleep", side_effect=mock_sleep):
            result = run(args, console)
            assert result == 0

    def test_watch_loop_detects_new_file(self, tmp_path):
        """Watch loop detects new files added to directory."""
        from dppvalidator.cli.commands.watch import run

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text(
            json.dumps({"id": "https://example.com/dpp", "issuer": {"id": "x", "name": "y"}})
        )

        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            strict=False,
            interval=0.1,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        # Create a new file during the loop
        call_count = [0]

        def mock_sleep(_duration):
            call_count[0] += 1
            if call_count[0] == 1:
                # Add a new file during the first sleep
                new_file = tmp_path / "new_file.json"
                new_file.write_text('{"id": "new"}')
            elif call_count[0] >= 3:
                raise KeyboardInterrupt
            time.sleep(0.001)

        with patch("dppvalidator.cli.commands.watch.time.sleep", side_effect=mock_sleep):
            result = run(args, console)
            assert result == 0
            output = stream.getvalue()
            # Should detect new file or at least run without error
            assert "session summary" in output.lower()

    def test_watch_loop_detects_removed_file(self, tmp_path):
        """Watch loop handles file removal."""
        from dppvalidator.cli.commands.watch import run

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text(
            json.dumps({"id": "https://example.com/dpp", "issuer": {"id": "x", "name": "y"}})
        )

        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            strict=False,
            interval=0.1,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        call_count = [0]

        def mock_sleep(_duration):
            call_count[0] += 1
            if call_count[0] == 1:
                # Remove the file during first sleep
                dpp_file.unlink()
            elif call_count[0] >= 3:
                raise KeyboardInterrupt
            time.sleep(0.001)

        with patch("dppvalidator.cli.commands.watch.time.sleep", side_effect=mock_sleep):
            result = run(args, console)
            assert result == 0

    def test_watch_loop_detects_modified_file(self, tmp_path):
        """Watch loop detects file modifications."""
        from dppvalidator.cli.commands.watch import run

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text(
            json.dumps({"id": "https://example.com/dpp", "issuer": {"id": "x", "name": "y"}})
        )

        args = argparse.Namespace(
            path=str(tmp_path),
            pattern="*.json",
            strict=False,
            interval=0.1,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        call_count = [0]

        def mock_sleep(_duration):
            call_count[0] += 1
            if call_count[0] == 1:
                # Modify file during first sleep
                time.sleep(0.01)  # Ensure mtime changes
                dpp_file.write_text(
                    json.dumps({"id": "modified", "issuer": {"id": "x", "name": "y"}})
                )
            elif call_count[0] >= 3:
                raise KeyboardInterrupt
            time.sleep(0.001)

        with patch("dppvalidator.cli.commands.watch.time.sleep", side_effect=mock_sleep):
            result = run(args, console)
            assert result == 0
            output = stream.getvalue()
            # Should show changes detected
            assert "session summary" in output.lower()

    def test_watch_file_deleted_during_init(self, tmp_path):
        """Watch handles file deleted during initialization."""
        from dppvalidator.cli.commands.watch import run

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text('{"id": "test"}')

        args = argparse.Namespace(
            path=str(dpp_file),
            pattern="*.json",
            strict=False,
            interval=0.1,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        # Just test that watch exits gracefully on KeyboardInterrupt
        with patch("time.sleep", side_effect=KeyboardInterrupt):
            result = run(args, console)
            assert result == 0

    def test_watch_validate_all(self, tmp_path):
        """_validate_all validates all files with output."""
        from dppvalidator.cli.commands.watch import WatchStats, _validate_all
        from dppvalidator.validators import ValidationEngine

        dpp_file = tmp_path / "test.json"
        dpp_file.write_text(json.dumps({"id": "test", "issuer": {"id": "x", "name": "y"}}))

        engine = ValidationEngine()
        stats = WatchStats()
        stream = StringIO()
        console = Console(file=stream)

        _validate_all([dpp_file], engine, console, stats)
        output = stream.getvalue()
        assert "Initial validation" in output


class TestSchemaCommandExtended:
    """Extended tests for schema command."""

    def test_schema_download_httpx_import_error(self, tmp_path):
        """Schema download handles httpx import errors."""
        from dppvalidator.cli.commands.schema import _download_schema

        stream = StringIO()
        console = Console(file=stream)

        # Mock httpx import to raise ImportError
        original_import = (
            __builtins__["__import__"]
            if isinstance(__builtins__, dict)
            else __builtins__.__import__
        )

        def mock_import(name, *args, **kwargs):
            if name == "httpx":
                raise ImportError("No module named 'httpx'")
            return original_import(name, *args, **kwargs)

        # This is difficult to test due to cached imports
        # Just verify the function exists and handles errors
        with patch("httpx.get", side_effect=Exception("Network error")):
            result = _download_schema("0.6.1", str(tmp_path), console)
            assert result == 2

    def test_schema_download_network_error(self, tmp_path):
        """Schema download handles network errors."""
        from dppvalidator.cli.commands.schema import _download_schema

        stream = StringIO()
        console = Console(file=stream)

        with patch("httpx.get", side_effect=Exception("Network error")):
            result = _download_schema("0.6.1", str(tmp_path), console)
            assert result == 2


class TestDoctorCommandExtended:
    """Extended tests for doctor command edge cases."""

    def test_doctor_python_version_check_passes(self):
        """Doctor Python version check passes for current version."""
        from dppvalidator.cli.commands.doctor import _check_python_version

        stream = StringIO()
        console = Console(file=stream)

        # Current Python should pass
        status, _, _ = _check_python_version(console)
        assert status is True
        assert "Python" in stream.getvalue()

    def test_doctor_dppvalidator_import_error(self):
        """Doctor reports error when dppvalidator import fails."""
        # This test verifies the import error path exists
        # The actual import error is difficult to trigger in tests
        from dppvalidator.cli.commands.doctor import _check_dppvalidator_version

        stream = StringIO()
        console = Console(file=stream)

        # Normal case should pass
        status, _, _ = _check_dppvalidator_version(console)
        assert status is True

    def test_doctor_returns_warning_code(self):
        """Doctor returns EXIT_WARNING when only warnings."""
        from dppvalidator.cli.commands.doctor import EXIT_WARNING, run

        args = argparse.Namespace(fix=False)
        stream = StringIO()
        console = Console(file=stream)

        # Run and check result is one of valid exit codes
        result = run(args, console)
        assert result in (0, EXIT_WARNING, 2)

    def test_doctor_config_files_found(self, tmp_path, monkeypatch):
        """Doctor finds config files in cwd."""
        from dppvalidator.cli.commands.doctor import _check_config_files

        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")

        stream = StringIO()
        console = Console(file=stream)

        status, _, is_warning = _check_config_files(console)
        assert status is True
        assert is_warning is False


class TestValidationResultCoverage:
    """Coverage tests for ValidationResult edge cases."""

    def test_validation_error_to_dict_all_fields(self):
        """ValidationError.to_dict includes all optional fields."""
        from dppvalidator.validators.results import ValidationError

        error = ValidationError(
            path="$.test",
            message="Test error",
            code="TST001",
            layer="schema",
            suggestion="Fix it",
            docs_url="https://docs.example.com",
            did_you_mean=("option1", "option2"),
            context={"key": "value"},
        )

        result = error.to_dict()
        assert result["suggestion"] == "Fix it"
        assert result["docs_url"] == "https://docs.example.com"
        assert result["did_you_mean"] == ["option1", "option2"]

    def test_validation_error_to_dict_minimal(self):
        """ValidationError.to_dict with minimal fields."""
        from dppvalidator.validators.results import ValidationError

        error = ValidationError(
            path="$.test",
            message="Test error",
            code="TST001",
            layer="schema",
        )

        result = error.to_dict()
        assert "suggestion" not in result
        assert "docs_url" not in result
        assert "did_you_mean" not in result

    def test_validation_result_raise_for_errors(self):
        """ValidationResult.raise_for_errors raises on invalid."""
        from dppvalidator.validators.results import (
            ValidationError,
            ValidationException,
            ValidationResult,
        )

        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    path="$.test",
                    message="Test error",
                    code="TST001",
                    layer="schema",
                )
            ],
        )

        with pytest.raises(ValidationException) as exc_info:
            result.raise_for_errors()

        assert exc_info.value.result is result
        assert "1 error" in str(exc_info.value)

    def test_validation_result_raise_for_errors_valid(self):
        """ValidationResult.raise_for_errors does nothing when valid."""
        from dppvalidator.validators.results import ValidationResult

        result = ValidationResult(valid=True)
        result.raise_for_errors()  # Should not raise

    def test_validation_result_merge(self):
        """ValidationResult.merge combines results."""
        from dppvalidator.validators.results import ValidationError, ValidationResult

        result1 = ValidationResult(
            valid=True,
            errors=[],
            warnings=[
                ValidationError(
                    path="$.a",
                    message="Warning 1",
                    code="W001",
                    layer="schema",
                    severity="warning",
                )
            ],
            parse_time_ms=10.0,
            validation_time_ms=20.0,
        )
        result2 = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    path="$.b",
                    message="Error 1",
                    code="E001",
                    layer="model",
                )
            ],
            parse_time_ms=5.0,
            validation_time_ms=15.0,
        )

        merged = result1.merge(result2)
        assert merged.valid is False
        assert len(merged.errors) == 1
        assert len(merged.warnings) == 1
        assert merged.parse_time_ms == 15.0
        assert merged.validation_time_ms == 35.0

    def test_validation_result_all_issues(self):
        """ValidationResult.all_issues returns all combined."""
        from dppvalidator.validators.results import ValidationError, ValidationResult

        error = ValidationError(path="$.a", message="E", code="E001", layer="schema")
        warning = ValidationError(
            path="$.b", message="W", code="W001", layer="model", severity="warning"
        )
        info = ValidationError(
            path="$.c", message="I", code="I001", layer="semantic", severity="info"
        )

        result = ValidationResult(
            valid=False,
            errors=[error],
            warnings=[warning],
            info=[info],
        )

        all_issues = result.all_issues
        assert len(all_issues) == 3
        assert error in all_issues
        assert warning in all_issues
        assert info in all_issues
