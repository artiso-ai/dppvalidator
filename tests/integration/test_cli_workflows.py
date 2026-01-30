"""Integration tests for CLI workflows.

Tests complete user workflows through the CLI interface.
"""

import json
from pathlib import Path

from dppvalidator.cli.main import EXIT_ERROR, EXIT_INVALID, EXIT_VALID, main

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestValidateWorkflow:
    """Integration tests for validate command workflow."""

    def test_validate_valid_fixture_succeeds(self):
        """Validating a valid fixture returns success."""
        fixture = FIXTURES_DIR / "valid" / "minimal_dpp.json"

        exit_code = main(["validate", str(fixture)])

        assert exit_code == EXIT_VALID

    def test_validate_invalid_fixture_fails(self):
        """Validating an invalid fixture returns invalid code."""
        fixture = FIXTURES_DIR / "invalid" / "missing_issuer.json"

        exit_code = main(["validate", str(fixture)])

        assert exit_code == EXIT_INVALID

    def test_validate_nonexistent_file_errors(self):
        """Validating nonexistent file returns error code."""
        exit_code = main(["validate", "/does/not/exist.json"])

        assert exit_code == EXIT_ERROR

    def test_validate_with_json_output(self, capsys):
        """Validate with --format json produces JSON output."""
        fixture = FIXTURES_DIR / "valid" / "minimal_dpp.json"

        exit_code = main(["validate", str(fixture), "--format", "json"])
        captured = capsys.readouterr()

        assert exit_code == EXIT_VALID
        # Output should be valid JSON
        result = json.loads(captured.out)
        assert "valid" in result
        assert result["valid"] is True

    def test_validate_single_file_workflow(self, tmp_path):
        """Validating a single file through the CLI."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "dpp.json"
        file_path.write_text(json.dumps(data))

        exit_code = main(["validate", str(file_path)])

        assert exit_code == EXIT_VALID


class TestExportWorkflow:
    """Integration tests for export command workflow."""

    def test_export_to_jsonld(self, tmp_path):
        """Export command produces JSON-LD output."""
        fixture = FIXTURES_DIR / "valid" / "minimal_dpp.json"
        output = tmp_path / "output.jsonld"

        exit_code = main(["export", str(fixture), "--output", str(output)])

        assert exit_code == EXIT_VALID
        assert output.exists()
        content = json.loads(output.read_text())
        assert "@context" in content

    def test_export_to_json(self, tmp_path):
        """Export command produces plain JSON output."""
        fixture = FIXTURES_DIR / "valid" / "minimal_dpp.json"
        output = tmp_path / "output.json"

        exit_code = main(
            [
                "export",
                str(fixture),
                "--output",
                str(output),
                "--format",
                "json",
            ]
        )

        assert exit_code == EXIT_VALID
        assert output.exists()


class TestInitWorkflow:
    """Integration tests for init command workflow."""

    def test_init_creates_project(self, tmp_path):
        """Init command creates project structure."""
        project_dir = tmp_path / "my_project"

        exit_code = main(["init", str(project_dir)])

        assert exit_code == EXIT_VALID
        assert project_dir.exists()
        assert (project_dir / "data" / "sample_passport.json").exists()
        assert (project_dir / ".gitignore").exists()

    def test_init_with_full_template(self, tmp_path):
        """Init with full template creates complete DPP."""
        project_dir = tmp_path / "my_project"

        exit_code = main(["init", str(project_dir), "--template", "full"])

        assert exit_code == EXIT_VALID
        dpp_file = project_dir / "data" / "sample_passport.json"
        content = json.loads(dpp_file.read_text())
        assert "materialsProvenance" in content.get("credentialSubject", {})

    def test_init_then_validate_workflow(self, tmp_path):
        """Full workflow: init project then validate created DPP."""
        project_dir = tmp_path / "my_project"

        # Initialize project
        init_code = main(["init", str(project_dir)])
        assert init_code == EXIT_VALID

        # Validate the created sample
        dpp_file = project_dir / "data" / "sample_passport.json"
        validate_code = main(["validate", str(dpp_file)])

        assert validate_code == EXIT_VALID


class TestSchemaWorkflow:
    """Integration tests for schema command workflow."""

    def test_schema_show_version(self, capsys):
        """Schema command shows available versions."""
        exit_code = main(["schema", "list"])

        captured = capsys.readouterr()
        assert exit_code == EXIT_VALID
        # Should mention schema versions
        assert "0.6.1" in captured.out or "schema" in captured.out.lower()


class TestDoctorWorkflow:
    """Integration tests for doctor command workflow."""

    def test_doctor_runs_diagnostics(self, capsys):
        """Doctor command runs environment diagnostics."""
        exit_code = main(["doctor"])

        captured = capsys.readouterr()
        # Should run without crashing
        assert exit_code in (EXIT_VALID, 1)  # Success or warning
        # Should show diagnostic output
        assert "dppvalidator" in captured.out.lower() or "python" in captured.out.lower()


class TestQuietAndVerboseFlags:
    """Tests for quiet and verbose output modes."""

    def test_quiet_mode_minimal_output(self, tmp_path, capsys):
        """Quiet mode produces minimal output."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "dpp.json"
        file_path.write_text(json.dumps(data))

        main(["--quiet", "validate", str(file_path)])
        captured = capsys.readouterr()

        # Output should be minimal in quiet mode
        assert len(captured.out) < 200 or captured.out == ""

    def test_verbose_mode_detailed_output(self, tmp_path, capsys):
        """Verbose mode produces detailed output."""
        data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
        }
        file_path = tmp_path / "dpp.json"
        file_path.write_text(json.dumps(data))

        main(["--verbose", "validate", str(file_path)])
        captured = capsys.readouterr()

        # Verbose output should include more detail
        assert len(captured.out) > 0


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_malformed_json_graceful_error(self, tmp_path, capsys):
        """Malformed JSON produces helpful error message."""
        file_path = tmp_path / "bad.json"
        file_path.write_text("{not valid json")

        exit_code = main(["validate", str(file_path)])

        assert exit_code == EXIT_ERROR
        captured = capsys.readouterr()
        # Should mention JSON or parse error
        output = captured.out + captured.err
        assert "json" in output.lower() or "parse" in output.lower() or "invalid" in output.lower()

    def test_permission_denied_graceful_error(self, tmp_path, monkeypatch):
        """Permission denied produces helpful error message."""

        # Mock Path.mkdir to raise PermissionError (works cross-platform)
        def mock_mkdir(_self, *_args, **_kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(Path, "mkdir", mock_mkdir)

        exit_code = main(["init", str(tmp_path / "protected_location")])

        assert exit_code == EXIT_ERROR


class TestEndToEndWorkflows:
    """Full end-to-end workflow tests."""

    def test_complete_validation_workflow(self, tmp_path):
        """Complete workflow: create, validate, export."""
        # Step 1: Initialize project with minimal template (validates cleanly)
        project_dir = tmp_path / "project"
        assert main(["init", str(project_dir), "--template", "minimal"]) == EXIT_VALID

        # Step 2: Validate the created DPP
        dpp_file = project_dir / "data" / "sample_passport.json"
        assert main(["validate", str(dpp_file)]) == EXIT_VALID

        # Step 3: Export to JSON-LD
        output_file = tmp_path / "exported.jsonld"
        assert main(["export", str(dpp_file), "--output", str(output_file)]) == EXIT_VALID

        # Step 4: Validate the exported file
        assert main(["validate", str(output_file)]) == EXIT_VALID

    def test_sequential_validation_workflow(self, tmp_path):
        """Sequential validation of multiple files."""
        ctx = [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ]
        # Create multiple DPP files and validate each
        for i in range(3):
            data = {
                "@context": ctx,
                "id": f"https://example.com/dpp-{i}",
                "issuer": {"id": "https://example.com/issuer", "name": f"Issuer {i}"},
            }
            file_path = tmp_path / f"dpp-{i}.json"
            file_path.write_text(json.dumps(data))

            # Validate each file individually
            exit_code = main(["validate", str(file_path)])
            assert exit_code == EXIT_VALID
