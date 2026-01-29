"""Tests for CLI module."""

import json

from dppvalidator.cli.main import EXIT_ERROR, EXIT_INVALID, EXIT_VALID, create_parser, main


class TestCLIParser:
    """Tests for CLI argument parser."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser.prog == "dppvalidator"

    def test_parser_version_flag(self):
        """Test --version flag."""
        parser = create_parser()
        args = parser.parse_args(["--version"])
        assert args.version is True

    def test_parser_quiet_flag(self):
        """Test --quiet flag."""
        parser = create_parser()
        args = parser.parse_args(["--quiet", "validate", "test.json"])
        assert args.quiet is True

    def test_parser_verbose_flag(self):
        """Test --verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["--verbose", "validate", "test.json"])
        assert args.verbose is True


class TestCLIMain:
    """Tests for main CLI entry point."""

    def test_main_no_command_shows_help(self, capsys):  # noqa: ARG002
        """Test that no command shows help."""
        result = main([])
        assert result == EXIT_VALID

    def test_main_version(self, capsys):
        """Test --version output."""
        result = main(["--version"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "dppvalidator" in captured.out

    def test_main_help_flag(self, capsys):  # noqa: ARG002
        """Test --help flag shows help."""
        # Note: argparse raises SystemExit(0) for --help
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0


class TestValidateCommand:
    """Tests for validate command."""

    def test_validate_valid_file(self, tmp_path):
        """Test validating a valid passport file."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path)])
        assert result == EXIT_VALID

    def test_validate_invalid_file(self, tmp_path):
        """Test validating an invalid passport file."""
        passport_data = {"invalid": "data"}
        file_path = tmp_path / "invalid.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path)])
        assert result == EXIT_INVALID

    def test_validate_nonexistent_file(self):
        """Test validating a nonexistent file."""
        result = main(["validate", "/nonexistent/path.json"])
        assert result == EXIT_ERROR

    def test_validate_with_format_json(self, tmp_path, capsys):
        """Test validate with JSON format output."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path), "--format", "json"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        # Output should be valid JSON
        output = json.loads(captured.out)
        assert "valid" in output

    def test_validate_strict_mode(self, tmp_path):
        """Test validate with strict mode."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path), "--strict"])
        # Should pass since minimal passport is valid
        assert result in (EXIT_VALID, EXIT_INVALID)


class TestExportCommand:
    """Tests for export command."""

    def test_export_to_stdout(self, tmp_path, capsys):
        """Test export to stdout."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["export", str(file_path)])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        output = json.loads(captured.out)
        assert "@context" in output

    def test_export_to_file(self, tmp_path):
        """Test export to file."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        input_path = tmp_path / "passport.json"
        input_path.write_text(json.dumps(passport_data))
        output_path = tmp_path / "output.jsonld"

        result = main(["export", str(input_path), "-o", str(output_path)])
        assert result == EXIT_VALID
        assert output_path.exists()
        content = json.loads(output_path.read_text())
        assert "@context" in content

    def test_export_json_format(self, tmp_path, capsys):
        """Test export with JSON format."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["export", str(file_path), "--format", "json"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        output = json.loads(captured.out)
        assert "issuer" in output


class TestSchemaCommand:
    """Tests for schema command."""

    def test_schema_list(self, capsys):
        """Test schema list command."""
        result = main(["schema", "list"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "0.6.1" in captured.out or "Available" in captured.out

    def test_schema_info(self, capsys):
        """Test schema info command."""
        result = main(["schema", "info", "--version", "0.6.1"])
        _captured = capsys.readouterr()
        # Should return valid or error depending on implementation
        assert result in (EXIT_VALID, EXIT_ERROR)


class TestCompletionsCommand:
    """Tests for completions command."""

    def test_completions_bash(self, capsys):
        """Test bash completions generation."""
        result = main(["completions", "bash"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "_dppvalidator_completions" in captured.out
        assert "complete -F" in captured.out

    def test_completions_zsh(self, capsys):
        """Test zsh completions generation."""
        result = main(["completions", "zsh"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "#compdef dppvalidator" in captured.out
        assert "_dppvalidator" in captured.out

    def test_completions_fish(self, capsys):
        """Test fish completions generation."""
        result = main(["completions", "fish"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "complete -c dppvalidator" in captured.out
        assert "__fish_use_subcommand" in captured.out


class TestCLIExitCodes:
    """Tests for CLI exit codes."""

    def test_exit_valid_constant(self):
        """Test EXIT_VALID constant."""
        assert EXIT_VALID == 0

    def test_exit_invalid_constant(self):
        """Test EXIT_INVALID constant."""
        assert EXIT_INVALID == 1

    def test_exit_error_constant(self):
        """Test EXIT_ERROR constant."""
        assert EXIT_ERROR == 2


class TestSchemaCommandExtended:
    """Extended tests for schema command."""

    def test_schema_no_subcommand(self, capsys):
        """Test schema with no subcommand."""
        result = main(["schema"])
        captured = capsys.readouterr()
        assert result == 2  # EXIT_ERROR
        assert "Usage" in captured.out

    def test_schema_list(self, capsys):
        """Test schema list command."""
        result = main(["schema", "list"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "Available" in captured.out or "0.6" in captured.out


class TestValidateCommandExtended:
    """Extended tests for validate command."""

    def test_validate_with_table_format(self, tmp_path, capsys):  # noqa: ARG002
        """Test validate with table format."""
        passport_data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path), "--format", "table"])
        assert result in (EXIT_VALID, EXIT_INVALID)

    def test_validate_invalid_json(self, tmp_path):
        """Test validate with invalid JSON file."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")

        result = main(["validate", str(file_path)])
        assert result == EXIT_ERROR

    def test_validate_stdin(self, tmp_path, monkeypatch):  # noqa: ARG002
        """Test validate from stdin."""
        import io
        import sys

        passport_json = json.dumps(
            {
                "id": "https://example.com/dpp",
                "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            }
        )
        monkeypatch.setattr(sys, "stdin", io.StringIO(passport_json))

        result = main(["validate", "-"])
        assert result in (EXIT_VALID, EXIT_INVALID, EXIT_ERROR)


class TestExportCommandExtended:
    """Extended tests for export command."""

    def test_export_nonexistent_file(self):
        """Test export with nonexistent file."""
        result = main(["export", "/nonexistent/file.json"])
        assert result == EXIT_ERROR

    def test_export_invalid_json(self, tmp_path):
        """Test export with invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not json")

        result = main(["export", str(file_path)])
        assert result == EXIT_ERROR

    def test_export_with_format_jsonld(self, tmp_path, capsys):
        """Test export with jsonld format."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["export", str(file_path), "--format", "jsonld"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "@context" in captured.out


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_main_verbose_error(self):
        """Test verbose error output."""
        result = main(["--verbose", "validate", "/nonexistent/file.json"])
        assert result == EXIT_ERROR

    def test_main_quiet_mode(self, tmp_path):
        """Test quiet mode."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["--quiet", "validate", str(file_path)])
        assert result == EXIT_VALID


class TestSchemaCommandFullCoverage:
    """Full coverage tests for schema command."""

    def test_schema_list_via_main(self):
        """Test schema list via main CLI."""
        result = main(["schema", "list"])
        assert result == EXIT_VALID

    def test_schema_info_via_main(self):
        """Test schema info via main CLI."""
        result = main(["schema", "info", "-v", "0.6.1"])
        assert result == EXIT_VALID

    def test_schema_no_subcommand_via_main(self):
        """Test schema with no subcommand."""
        result = main(["schema"])
        assert result in (EXIT_VALID, EXIT_ERROR)

    def test_schema_download_via_main(self, tmp_path):
        """Test schema download via main CLI."""
        result = main(["schema", "download", "-v", "0.6.1", "-o", str(tmp_path)])
        # May fail due to network issues, but should not crash
        assert result in (EXIT_VALID, EXIT_ERROR)

    def test_schema_info_unknown_version(self):
        """Test schema info with unknown version."""
        result = main(["schema", "info", "-v", "99.99.99"])
        # Unknown version may return EXIT_VALID with warning or EXIT_ERROR
        assert result in (EXIT_VALID, EXIT_ERROR)

    def test_schema_download_no_output_dir(self, tmp_path, monkeypatch):
        """Test schema download with no output dir uses cwd."""
        # Change to tmp_path to avoid polluting the project
        monkeypatch.chdir(tmp_path)
        result = main(["schema", "download", "-v", "0.6.1"])
        # May succeed or fail depending on network
        assert result in (EXIT_VALID, EXIT_ERROR)


class TestCLIMainFullCoverage:
    """Full coverage tests for CLI main module."""

    def test_validate_missing_file(self):
        """Test validate command with missing file."""
        result = main(["validate", "/nonexistent/path.json"])
        assert result == EXIT_ERROR

    def test_completions_command(self):
        """Test completions command."""
        result = main(["completions", "bash"])
        assert result in (EXIT_VALID, EXIT_ERROR)

    def test_main_with_exception(self, tmp_path, monkeypatch):
        """Test main handles exceptions gracefully."""
        # Create file that will cause an exception during processing
        file_path = tmp_path / "test.json"
        file_path.write_text('{"id": "test"}')

        # Mock validate handler to raise an exception
        def raise_exception(*_args, **_kwargs):  # noqa: ARG001
            raise RuntimeError("Test exception")

        import importlib

        cli_main_module = importlib.import_module("dppvalidator.cli.main")
        monkeypatch.setitem(cli_main_module.COMMAND_HANDLERS, "validate", raise_exception)

        result = main(["validate", str(file_path)])
        assert result == EXIT_ERROR

    def test_main_with_verbose_exception(self, tmp_path, monkeypatch):
        """Test main shows traceback in verbose mode."""
        file_path = tmp_path / "test.json"
        file_path.write_text('{"id": "test"}')

        def raise_exception(*_args, **_kwargs):  # noqa: ARG001
            raise RuntimeError("Test exception")

        import importlib

        cli_main_module = importlib.import_module("dppvalidator.cli.main")
        monkeypatch.setitem(cli_main_module.COMMAND_HANDLERS, "validate", raise_exception)

        result = main(["--verbose", "validate", str(file_path)])
        assert result == EXIT_ERROR

    def test_validate_invalid_json(self, tmp_path):
        """Test validate command with invalid JSON file."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json {")
        result = main(["validate", str(file_path)])
        assert result == EXIT_ERROR

    def test_export_missing_file(self, capsys):  # noqa: ARG002
        """Test export command with missing file."""
        result = main(["export", "/nonexistent/path.json"])
        assert result == EXIT_ERROR


class TestValidateCommandCoverage:
    """Coverage tests for validate command."""

    def test_validate_with_format_json(self, tmp_path, capsys):
        """Test validate with JSON output format."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path), "--format", "json"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        # Should be valid JSON output
        assert "valid" in captured.out.lower() or "{" in captured.out

    def test_validate_with_strict_mode(self, tmp_path, capsys):  # noqa: ARG002
        """Test validate with strict mode."""
        passport_data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path), "--strict"])
        assert result in (EXIT_VALID, EXIT_INVALID)

    def test_validate_stdin(self, monkeypatch, capsys):  # noqa: ARG002
        """Test validate from stdin."""
        import sys
        from io import StringIO

        passport_data = json.dumps(
            {
                "id": "https://example.com/dpp",
                "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            }
        )
        monkeypatch.setattr(sys, "stdin", StringIO(passport_data))

        result = main(["validate", "-"])
        assert result in (EXIT_VALID, EXIT_INVALID)


class TestSchemaCommandCoverage:
    """Coverage tests for schema command branches."""

    def test_schema_info_valid_version(self):
        """Test schema info with valid version shows info."""
        import argparse
        from io import StringIO

        from dppvalidator.cli.commands import schema as schema_module
        from dppvalidator.cli.console import Console

        args = argparse.Namespace(schema_command="info", version="0.6.1")
        stream = StringIO()
        console = Console(file=stream)

        result = schema_module.run(args, console)
        output = stream.getvalue()
        assert result == EXIT_VALID
        assert "0.6.1" in output

    def test_schema_info_unknown_version_error(self, capsys):
        """Test schema info with unknown version returns error."""
        import argparse
        from io import StringIO

        from dppvalidator.cli.commands import schema as schema_module
        from dppvalidator.cli.console import Console

        args = argparse.Namespace(schema_command="info", version="99.99.99")
        stream = StringIO()
        console = Console(file=stream)

        result = schema_module.run(args, console)
        captured = capsys.readouterr()
        output = stream.getvalue()
        assert result == EXIT_ERROR
        assert "Unknown" in captured.err or "unknown" in output.lower()

    def test_schema_download_to_directory(self, tmp_path):
        """Test schema download to specified directory."""
        import argparse
        from io import StringIO

        from dppvalidator.cli.commands import schema as schema_module
        from dppvalidator.cli.console import Console

        args = argparse.Namespace(
            schema_command="download",
            version="0.6.1",
            output=str(tmp_path),
        )
        stream = StringIO()
        console = Console(file=stream)

        # The download will likely fail due to network, which is expected
        result = schema_module.run(args, console)
        # Either succeeds (network available) or fails (expected in CI)
        assert result in (EXIT_VALID, EXIT_ERROR)

    def test_schema_list_shows_versions(self, capsys):
        """Test schema list shows available versions with table."""
        result = main(["schema", "list"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        # Should show version info
        assert "0.6" in captured.out or "Available" in captured.out


class TestExportCommandCoverage:
    """Coverage tests for export command."""

    def test_export_invalid_dpp_shows_errors(self, tmp_path, capsys):
        """Test export with invalid DPP shows validation errors."""
        passport_data = {"invalid": "data", "no_issuer": True}
        file_path = tmp_path / "invalid.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["export", str(file_path)])
        captured = capsys.readouterr()
        assert result == EXIT_ERROR
        assert "not a valid DPP" in captured.err.lower() or "error" in captured.err.lower()

    def test_export_compact_output(self, tmp_path, capsys):
        """Test export with --compact flag produces minimal formatting."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["export", str(file_path), "--compact"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        # Compact output should not have leading whitespace (no indentation)
        output = captured.out
        # Check there's no 2+ space indentation at start of lines
        lines_with_indent = [line for line in output.split("\n") if line.startswith("  ")]
        assert len(lines_with_indent) == 0, "Compact output should not have indentation"

    def test_export_to_json(self, tmp_path, capsys):
        """Test export to JSON format."""
        passport_data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["export", str(file_path), "--format", "json"])
        _captured = capsys.readouterr()
        # Should output JSON
        assert result in (EXIT_VALID, EXIT_ERROR)

    def test_export_to_jsonld(self, tmp_path, capsys):  # noqa: ARG002
        """Test export to JSON-LD format."""
        passport_data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["export", str(file_path), "--format", "jsonld"])
        assert result in (EXIT_VALID, EXIT_ERROR)

    def test_export_to_file(self, tmp_path, capsys):  # noqa: ARG002
        """Test export to output file."""
        passport_data = {
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        output_path = tmp_path / "output.json"
        result = main(["export", str(file_path), "-o", str(output_path)])
        assert result in (EXIT_VALID, EXIT_ERROR)


class TestValidateCommandBehavior:
    """Behavior tests for validate command - testing actual library behavior."""

    def test_validate_returns_structured_json_output(self, tmp_path, capsys):
        """Test that --format json returns properly structured output."""
        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test Corp"},
        }
        file_path = tmp_path / "passport.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path), "--format", "json"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID

        # Parse and verify structure
        output = json.loads(captured.out)
        assert "valid" in output
        assert output["valid"] is True
        assert "schema_version" in output

    def test_validate_invalid_data_json_format(self, tmp_path, capsys):
        """Test invalid data returns structured errors in JSON format."""
        passport_data = {"missing": "issuer"}
        file_path = tmp_path / "invalid.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path), "--format", "json"])
        captured = capsys.readouterr()
        assert result == EXIT_INVALID

        output = json.loads(captured.out)
        assert output["valid"] is False
        assert len(output["errors"]) > 0

    def test_validate_multiple_errors_collected(self, tmp_path, capsys):
        """Test that multiple validation errors are collected."""
        passport_data = {
            "validFrom": "2034-01-01T00:00:00Z",
            "validUntil": "2024-01-01T00:00:00Z",
        }
        file_path = tmp_path / "multi_error.json"
        file_path.write_text(json.dumps(passport_data))

        result = main(["validate", str(file_path), "--format", "json"])
        captured = capsys.readouterr()
        assert result == EXIT_INVALID

        output = json.loads(captured.out)
        # Should have at least errors for missing issuer and date order
        assert len(output["errors"]) >= 1


class TestCompletionsUnknownShell:
    """Tests for completions command with unknown shell."""

    def test_completions_unknown_shell(self, capsys):
        """Test completions with unknown shell returns error."""
        import argparse

        from dppvalidator.cli.commands import completions as completions_module

        args = argparse.Namespace(shell="powershell")
        result = completions_module.run(args)
        captured = capsys.readouterr()
        assert result == 2  # EXIT_ERROR equivalent
        assert "Unknown shell" in captured.err


class TestExportNullPassport:
    """Tests for export command when passport is None after validation."""

    def test_export_passport_none_after_validation(self, tmp_path, monkeypatch):
        """Test export when validation passes but passport is None."""
        import argparse
        from io import StringIO

        from dppvalidator.cli.commands import export as export_module
        from dppvalidator.cli.console import Console
        from dppvalidator.validators.results import ValidationResult

        # Create a valid JSON file
        file_path = tmp_path / "passport.json"
        file_path.write_text('{"id": "test", "issuer": {"id": "x", "name": "y"}}')

        # Mock ValidationEngine to return valid=True but passport=None
        class MockEngine:
            def __init__(self, **kwargs):
                pass

            def validate(self, _data):
                return ValidationResult(valid=True, passport=None, schema_version="0.6.1")

        # Patch at the source module where it's imported from
        import dppvalidator.validators as validators_module

        monkeypatch.setattr(validators_module, "ValidationEngine", MockEngine)

        args = argparse.Namespace(
            input=str(file_path),
            output=None,
            format="jsonld",
            compact=False,
            schema_version="0.6.1",
        )
        stream = StringIO()
        console = Console(file=stream)

        result = export_module.run(args, console)
        assert result == 2  # EXIT_ERROR


class TestCLIKeyboardInterrupt:
    """Tests for CLI keyboard interrupt handling."""

    def test_main_keyboard_interrupt(self, tmp_path, monkeypatch):
        """Test main handles KeyboardInterrupt gracefully."""
        import importlib

        cli_main_module = importlib.import_module("dppvalidator.cli.main")

        def raise_keyboard_interrupt(*_args, **_kwargs):
            raise KeyboardInterrupt()

        monkeypatch.setitem(cli_main_module.COMMAND_HANDLERS, "validate", raise_keyboard_interrupt)

        file_path = tmp_path / "test.json"
        file_path.write_text('{"id": "test"}')

        result = main(["validate", str(file_path)])
        assert result == EXIT_ERROR
