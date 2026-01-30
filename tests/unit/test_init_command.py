"""Tests for CLI init command."""

import argparse
import json
from unittest.mock import MagicMock

from dppvalidator.cli.commands.init import (
    EXIT_ERROR,
    EXIT_SUCCESS,
    FULL_DPP_TEMPLATE,
    GITIGNORE_CONTENT,
    MINIMAL_DPP_TEMPLATE,
    PRE_COMMIT_CONFIG,
    add_parser,
    run,
)


def make_args(
    path=".",
    template="minimal",
    pre_commit=False,
    force=False,
    name=None,
    config=False,
    readme=True,
):
    """Create argparse.Namespace with all required init command args."""
    return argparse.Namespace(
        path=path,
        template=template,
        pre_commit=pre_commit,
        force=force,
        name=name,
        config=config,
        readme=readme,
    )


class TestAddParser:
    """Tests for init parser setup."""

    def test_adds_init_subcommand(self):
        """Parser adds init subcommand."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        init_parser = add_parser(subparsers)

        assert init_parser is not None

    def test_parser_has_path_argument(self):
        """Parser accepts optional path argument."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_parser(subparsers)

        args = parser.parse_args(["init", "/some/path"])
        assert args.path == "/some/path"

    def test_parser_default_path_is_current_dir(self):
        """Parser defaults to current directory."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_parser(subparsers)

        args = parser.parse_args(["init"])
        assert args.path == "."

    def test_parser_has_template_option(self):
        """Parser accepts --template option."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_parser(subparsers)

        args = parser.parse_args(["init", "--template", "full"])
        assert args.template == "full"

    def test_parser_has_pre_commit_flag(self):
        """Parser accepts --pre-commit flag."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_parser(subparsers)

        args = parser.parse_args(["init", "--pre-commit"])
        assert args.pre_commit is True

    def test_parser_has_force_flag(self):
        """Parser accepts --force flag."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_parser(subparsers)

        args = parser.parse_args(["init", "--force"])
        assert args.force is True


class TestInitRun:
    """Tests for init run command."""

    def test_creates_project_structure(self, tmp_path):
        """Init creates expected project structure."""
        console = MagicMock()
        project_dir = tmp_path / "new_project"
        args = make_args(path=str(project_dir))

        result = run(args, console)

        assert result == EXIT_SUCCESS
        assert project_dir.exists()
        assert (project_dir / "data").exists()
        assert (project_dir / "data" / "sample_passport.json").exists()
        assert (project_dir / ".gitignore").exists()

    def test_creates_minimal_template(self, tmp_path):
        """Init creates minimal DPP template by default."""
        console = MagicMock()
        args = make_args(path=str(tmp_path))

        run(args, console)

        dpp_file = tmp_path / "data" / "sample_passport.json"
        content = json.loads(dpp_file.read_text())

        assert content["type"] == MINIMAL_DPP_TEMPLATE["type"]
        assert "credentialSubject" in content

    def test_creates_full_template(self, tmp_path):
        """Init creates full DPP template when requested."""
        console = MagicMock()
        args = make_args(path=str(tmp_path), template="full")

        run(args, console)

        dpp_file = tmp_path / "data" / "sample_passport.json"
        content = json.loads(dpp_file.read_text())

        assert "materialsProvenance" in content["credentialSubject"]
        assert "circularityScorecard" in content["credentialSubject"]

    def test_creates_gitignore(self, tmp_path):
        """Init creates .gitignore with expected content."""
        console = MagicMock()
        args = make_args(path=str(tmp_path))

        run(args, console)

        gitignore = tmp_path / ".gitignore"
        content = gitignore.read_text()

        assert ".dppvalidator/" in content
        assert "__pycache__/" in content

    def test_creates_pre_commit_config_when_requested(self, tmp_path):
        """Init creates pre-commit config when --pre-commit flag used."""
        console = MagicMock()
        args = make_args(path=str(tmp_path), pre_commit=True)

        run(args, console)

        precommit = tmp_path / ".pre-commit-config.yaml"
        assert precommit.exists()
        content = precommit.read_text()
        assert "dppvalidator" in content

    def test_does_not_create_pre_commit_by_default(self, tmp_path):
        """Init does not create pre-commit config by default."""
        console = MagicMock()
        args = make_args(path=str(tmp_path))

        run(args, console)

        precommit = tmp_path / ".pre-commit-config.yaml"
        assert not precommit.exists()

    def test_does_not_overwrite_existing_files(self, tmp_path):
        """Init does not overwrite existing files without --force."""
        console = MagicMock()

        # Create existing file
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        existing_file = data_dir / "sample_passport.json"
        existing_file.write_text('{"existing": "data"}')

        args = make_args(path=str(tmp_path))

        run(args, console)

        # Original content preserved
        content = json.loads(existing_file.read_text())
        assert content == {"existing": "data"}

    def test_overwrites_files_with_force_flag(self, tmp_path):
        """Init overwrites existing files with --force flag."""
        console = MagicMock()

        # Create existing file
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        existing_file = data_dir / "sample_passport.json"
        existing_file.write_text('{"existing": "data"}')

        args = make_args(path=str(tmp_path), force=True)

        run(args, console)

        # Content replaced
        content = json.loads(existing_file.read_text())
        assert "type" in content
        assert "existing" not in content

    def test_handles_permission_error(self, tmp_path, monkeypatch):
        """Init handles permission errors gracefully."""
        console = MagicMock()
        args = make_args(path=str(tmp_path / "test_project"))

        # Mock Path.mkdir to raise PermissionError (works cross-platform)
        from pathlib import Path

        def mock_mkdir(_self, *_args, **_kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(Path, "mkdir", mock_mkdir)

        result = run(args, console)

        # Should return error, not crash
        assert result == EXIT_ERROR
        console.print_error.assert_called()


class TestTemplates:
    """Tests for DPP templates."""

    def test_minimal_template_is_valid_dpp(self):
        """Minimal template is a valid DPP structure."""
        assert "type" in MINIMAL_DPP_TEMPLATE
        assert "DigitalProductPassport" in MINIMAL_DPP_TEMPLATE["type"]
        assert "@context" in MINIMAL_DPP_TEMPLATE
        assert "id" in MINIMAL_DPP_TEMPLATE
        assert "issuer" in MINIMAL_DPP_TEMPLATE
        assert "credentialSubject" in MINIMAL_DPP_TEMPLATE

    def test_full_template_has_materials(self):
        """Full template includes materials provenance."""
        assert "materialsProvenance" in FULL_DPP_TEMPLATE["credentialSubject"]
        materials = FULL_DPP_TEMPLATE["credentialSubject"]["materialsProvenance"]
        assert len(materials) >= 2

    def test_full_template_has_circularity(self):
        """Full template includes circularity scorecard."""
        assert "circularityScorecard" in FULL_DPP_TEMPLATE["credentialSubject"]
        scorecard = FULL_DPP_TEMPLATE["credentialSubject"]["circularityScorecard"]
        assert "recycledContent" in scorecard

    def test_full_template_has_conformity_claims(self):
        """Full template includes conformity claims."""
        assert "conformityClaim" in FULL_DPP_TEMPLATE["credentialSubject"]

    def test_templates_mass_fractions_sum_to_one(self):
        """Full template materials have valid mass fractions."""
        materials = FULL_DPP_TEMPLATE["credentialSubject"]["materialsProvenance"]
        total = sum(m["massFraction"] for m in materials)
        assert abs(total - 1.0) < 0.01


class TestGitignoreContent:
    """Tests for .gitignore template."""

    def test_ignores_dppvalidator_cache(self):
        """Gitignore includes .dppvalidator directory."""
        assert ".dppvalidator/" in GITIGNORE_CONTENT

    def test_ignores_python_cache(self):
        """Gitignore includes Python cache directories."""
        assert "__pycache__/" in GITIGNORE_CONTENT


class TestPreCommitConfig:
    """Tests for pre-commit config template."""

    def test_includes_dppvalidator_hook(self):
        """Pre-commit config includes dppvalidator hook."""
        assert "dppvalidator" in PRE_COMMIT_CONFIG
        assert "entry: dppvalidator validate" in PRE_COMMIT_CONFIG

    def test_targets_json_files(self):
        """Pre-commit hook targets JSON files."""
        assert ".json$" in PRE_COMMIT_CONFIG or "json" in PRE_COMMIT_CONFIG.lower()
