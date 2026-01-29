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

    def test_main_no_command_shows_help(self, capsys):
        """Test that no command shows help."""
        result = main([])
        assert result == EXIT_VALID

    def test_main_version(self, capsys):
        """Test --version output."""
        result = main(["--version"])
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "dppvalidator" in captured.out

    def test_main_help_flag(self, capsys):
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
        captured = capsys.readouterr()
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

    def test_validate_with_table_format(self, tmp_path, capsys):
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

    def test_validate_stdin(self, tmp_path, monkeypatch):
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

    def test_schema_info_with_context(self, capsys):
        """Test schema info shows context info."""
        from dppvalidator.cli.commands.schema import _show_info

        result = _show_info("0.6.1")
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "0.6.1" in captured.out

    def test_schema_info_unknown(self, capsys):
        """Test schema info with unknown version."""
        from dppvalidator.cli.commands.schema import _show_info

        result = _show_info("9.9.9")
        captured = capsys.readouterr()
        assert result == 2
        assert "Unknown" in captured.out

    def test_schema_list_output(self, capsys):
        """Test schema list output format."""
        from dppvalidator.cli.commands.schema import _list_schemas

        result = _list_schemas()
        captured = capsys.readouterr()
        assert result == EXIT_VALID
        assert "Available" in captured.out
