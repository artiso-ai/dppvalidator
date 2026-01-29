"""Unit tests for CLI init command."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from dppvalidator.cli.commands.init import (
    PROJECT_NAME_PATTERN,
    _get_template,
    run,
)


class TestProjectNamePattern:
    """Tests for project name validation pattern."""

    def test_valid_names(self) -> None:
        """Valid project names should match."""
        valid_names = [
            "myproject",
            "MyProject",
            "my-project",
            "my_project",
            "project123",
            "A",
        ]
        for name in valid_names:
            assert PROJECT_NAME_PATTERN.match(name), f"{name} should be valid"

    def test_invalid_names(self) -> None:
        """Invalid project names should not match."""
        invalid_names = [
            "123project",  # starts with number
            "-project",  # starts with hyphen
            "_project",  # starts with underscore
            "project.name",  # contains dot
            "project name",  # contains space
            "",  # empty
        ]
        for name in invalid_names:
            assert not PROJECT_NAME_PATTERN.match(name), f"{name} should be invalid"


class TestGetTemplate:
    """Tests for template generation."""

    def test_minimal_template(self) -> None:
        """Minimal template should have required fields."""
        template = _get_template("minimal")

        assert "type" in template
        assert "DigitalProductPassport" in template["type"]
        assert "@context" in template
        assert "id" in template
        assert "issuer" in template
        assert "validFrom" in template
        assert "validUntil" in template

    def test_full_template(self) -> None:
        """Full template should have additional fields."""
        template = _get_template("full")

        assert "credentialSubject" in template
        subject = template["credentialSubject"]
        assert "materialsProvenance" in subject
        assert "circularityScorecard" in subject

    def test_template_dates_are_updated(self) -> None:
        """Template dates should be current, not hardcoded."""
        template = _get_template("minimal")

        # validFrom should not be the hardcoded 2024 date
        assert "2024-01-01" not in template["validFrom"]


class TestInitCommand:
    """Tests for init command execution."""

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        """Init should create project directory."""
        project_dir = tmp_path / "new_project"
        console = MagicMock()

        args = MagicMock()
        args.path = str(project_dir)
        args.template = "minimal"
        args.force = False
        args.pre_commit = False
        args.name = None
        args.config = False
        args.readme = True

        result = run(args, console)

        assert result == 0
        assert project_dir.exists()
        assert (project_dir / "data").exists()

    def test_init_creates_sample_dpp(self, tmp_path: Path) -> None:
        """Init should create sample DPP file."""
        console = MagicMock()

        args = MagicMock()
        args.path = str(tmp_path)
        args.template = "minimal"
        args.force = False
        args.pre_commit = False
        args.name = None
        args.config = False
        args.readme = True

        run(args, console)

        dpp_file = tmp_path / "data" / "sample_passport.json"
        assert dpp_file.exists()

        content = json.loads(dpp_file.read_text())
        assert "type" in content
        assert "DigitalProductPassport" in content["type"]

    def test_init_creates_gitignore(self, tmp_path: Path) -> None:
        """Init should create .gitignore."""
        console = MagicMock()

        args = MagicMock()
        args.path = str(tmp_path)
        args.template = "minimal"
        args.force = False
        args.pre_commit = False
        args.name = None
        args.config = False
        args.readme = True

        run(args, console)

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".dppvalidator/" in gitignore.read_text()

    def test_init_creates_readme(self, tmp_path: Path) -> None:
        """Init should create README.md."""
        console = MagicMock()

        args = MagicMock()
        args.path = str(tmp_path)
        args.template = "minimal"
        args.force = False
        args.pre_commit = False
        args.name = "TestProject"
        args.config = False
        args.readme = True

        run(args, console)

        readme = tmp_path / "README.md"
        assert readme.exists()
        assert "TestProject" in readme.read_text()

    def test_init_creates_config(self, tmp_path: Path) -> None:
        """Init should create config file when requested."""
        console = MagicMock()

        args = MagicMock()
        args.path = str(tmp_path)
        args.template = "minimal"
        args.force = False
        args.pre_commit = False
        args.name = None
        args.config = True
        args.readme = False

        run(args, console)

        config_file = tmp_path / ".dppvalidator.json"
        assert config_file.exists()

        content = json.loads(config_file.read_text())
        assert "validation" in content

    def test_init_creates_precommit(self, tmp_path: Path) -> None:
        """Init should create pre-commit config when requested."""
        console = MagicMock()

        args = MagicMock()
        args.path = str(tmp_path)
        args.template = "minimal"
        args.force = False
        args.pre_commit = True
        args.name = None
        args.config = False
        args.readme = False

        run(args, console)

        precommit = tmp_path / ".pre-commit-config.yaml"
        assert precommit.exists()
        assert "dppvalidator" in precommit.read_text()

    def test_init_skips_existing_files(self, tmp_path: Path) -> None:
        """Init should skip existing files without --force."""
        console = MagicMock()

        # Create existing file
        (tmp_path / "data").mkdir()
        existing = tmp_path / "data" / "sample_passport.json"
        existing.write_text('{"existing": true}')

        args = MagicMock()
        args.path = str(tmp_path)
        args.template = "minimal"
        args.force = False
        args.pre_commit = False
        args.name = None
        args.config = False
        args.readme = False

        run(args, console)

        # Should not overwrite
        content = json.loads(existing.read_text())
        assert content == {"existing": True}

    def test_init_overwrites_with_force(self, tmp_path: Path) -> None:
        """Init should overwrite existing files with --force."""
        console = MagicMock()

        # Create existing file
        (tmp_path / "data").mkdir()
        existing = tmp_path / "data" / "sample_passport.json"
        existing.write_text('{"existing": true}')

        args = MagicMock()
        args.path = str(tmp_path)
        args.template = "minimal"
        args.force = True
        args.pre_commit = False
        args.name = None
        args.config = False
        args.readme = False

        run(args, console)

        # Should be overwritten
        content = json.loads(existing.read_text())
        assert "type" in content

    def test_init_invalid_project_name(self, tmp_path: Path) -> None:
        """Init should reject invalid project names."""
        console = MagicMock()

        args = MagicMock()
        args.path = str(tmp_path)
        args.template = "minimal"
        args.force = False
        args.pre_commit = False
        args.name = "123-invalid"  # starts with number
        args.config = False
        args.readme = True

        result = run(args, console)

        assert result == 2  # EXIT_ERROR
        console.print_error.assert_called()
