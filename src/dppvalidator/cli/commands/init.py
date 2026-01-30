"""Init command for CLI - scaffolds a new DPP project."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

EXIT_SUCCESS = 0
EXIT_ERROR = 2

# Valid project name pattern
PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")

MINIMAL_DPP_TEMPLATE = {
    "type": ["DigitalProductPassport", "VerifiableCredential"],
    "@context": [
        "https://www.w3.org/ns/credentials/v2",
        "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
    ],
    "id": "https://example.com/credentials/dpp-001",
    "issuer": {"id": "https://example.com/issuers/001", "name": "Your Company Name"},
    "validFrom": "2024-01-01T00:00:00Z",
    "validUntil": "2026-01-01T00:00:00Z",
    "credentialSubject": {
        "type": ["ProductPassport"],
        "id": "https://example.com/products/001",
        "granularityLevel": "model",
        "product": {
            "type": ["Product"],
            "id": "https://example.com/products/001",
            "name": "Example Product",
            "description": "A sample product for DPP validation",
        },
    },
}

FULL_DPP_TEMPLATE = {
    "type": ["DigitalProductPassport", "VerifiableCredential"],
    "@context": [
        "https://www.w3.org/ns/credentials/v2",
        "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
    ],
    "id": "https://example.com/credentials/dpp-001",
    "issuer": {"id": "https://example.com/issuers/001", "name": "Your Company Name"},
    "validFrom": "2024-01-01T00:00:00Z",
    "validUntil": "2026-01-01T00:00:00Z",
    "credentialSubject": {
        "type": ["ProductPassport"],
        "id": "https://example.com/products/001",
        "granularityLevel": "model",
        "product": {
            "type": ["Product"],
            "id": "https://example.com/products/001",
            "name": "Example Product",
            "productCategory": ["Textiles"],
            "producedByParty": {
                "type": ["Party"],
                "id": "https://example.com/parties/manufacturer-001",
                "name": "Example Manufacturer",
            },
        },
        "materialsProvenance": [
            {
                "type": ["Material"],
                "name": "Organic Cotton",
                "massFraction": 0.60,
                "recycled": False,
                "hazardous": False,
            },
            {
                "type": ["Material"],
                "name": "Recycled Polyester",
                "massFraction": 0.40,
                "recycled": True,
                "hazardous": False,
            },
        ],
        "circularityScorecard": {
            "type": ["CircularityScorecard"],
            "recycledContent": 0.40,
            "recyclableContent": 0.95,
            "repairabilityScore": 7,
        },
        "conformityClaim": [
            {
                "type": ["Claim"],
                "claimType": "Certification",
                "topic": "sustainability",
                "conformityEvidence": {
                    "type": ["Evidence"],
                    "evidenceType": "Certificate",
                    "linkURL": "https://example.com/certificates/001",
                },
            }
        ],
    },
}

GITIGNORE_CONTENT = """# DPP Validation artifacts
*.log
.dppvalidator/
__pycache__/
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

README_TEMPLATE = """# {project_name}

Digital Product Passport validation project.

## Quick Start

```bash
# Validate a passport
dppvalidator validate data/sample_passport.json

# Check environment
dppvalidator doctor

# Watch for changes during development
dppvalidator watch data/
```

## Project Structure

```
{project_name}/
├── data/
│   └── sample_passport.json  # Sample DPP file
├── .gitignore
└── README.md
```

## Documentation

- [dppvalidator docs](https://artiso-ai.github.io/dppvalidator/)
- [UNTP DPP Schema](https://uncefact.github.io/spec-untp/docs/specification/DigitalProductPassport)
"""

DPPVALIDATOR_CONFIG = {
    "$schema": "https://artiso-ai.github.io/dppvalidator/schemas/config.json",
    "version": "1.0",
    "validation": {
        "strict": False,
        "schema_version": "0.6.1",
        "fail_on_warning": False,
    },
    "paths": {
        "data": "data/",
        "output": "output/",
    },
}

PRE_COMMIT_CONFIG = """repos:
  - repo: local
    hooks:
      - id: dppvalidator
        name: DPP Validation
        entry: dppvalidator validate
        language: system
        files: \\.json$
        types: [json]
"""


def add_parser(subparsers: Any) -> argparse.ArgumentParser:
    """Add init subparser."""
    parser = subparsers.add_parser(
        "init",
        help="Initialize a new DPP project",
        description="Scaffold a new DPP validation project with templates",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "-t",
        "--template",
        choices=["minimal", "full"],
        default="minimal",
        help="DPP template to use (default: minimal)",
    )
    parser.add_argument(
        "--pre-commit",
        action="store_true",
        help="Add pre-commit hook configuration",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    parser.add_argument(
        "--name",
        help="Project name (for README, defaults to directory name)",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Create .dppvalidator.json config file",
    )
    parser.add_argument(
        "--readme",
        action="store_true",
        default=True,
        help="Create README.md (default: true)",
    )
    parser.add_argument(
        "--no-readme",
        action="store_false",
        dest="readme",
        help="Skip README.md creation",
    )
    return parser


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute init command."""
    project_path = Path(args.path).resolve()
    project_name = args.name or project_path.name

    # Validate project name
    if not PROJECT_NAME_PATTERN.match(project_name):
        console.print_error(
            f"Invalid project name: '{project_name}'. "
            "Use letters, numbers, hyphens, and underscores only."
        )
        return EXIT_ERROR

    console.print(f"\n📦 Initializing DPP project in [bold]{project_path}[/bold]\n")

    try:
        # Check if path exists and is not empty
        if project_path.exists() and any(project_path.iterdir()) and not args.force:
            console.print(
                "  [yellow]⚠[/yellow] Directory not empty. Use --force to overwrite files."
            )

        project_path.mkdir(parents=True, exist_ok=True)

        # Verify write permissions
        try:
            test_file = project_path / ".dppvalidator_init_test"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
        except PermissionError:
            console.print_error(f"No write permission for: {project_path}")
            return EXIT_ERROR

        files_created = 0
        files_skipped = 0

        # Create data directory
        data_dir = project_path / "data"
        data_dir.mkdir(exist_ok=True)

        # Create sample DPP file with current dates
        template = _get_template(args.template)
        dpp_file = data_dir / "sample_passport.json"

        if dpp_file.exists() and not args.force:
            console.print(f"  [yellow]○[/yellow] {dpp_file.name} exists (skipped)")
            files_skipped += 1
        else:
            dpp_file.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
            console.print(f"  [green]✓[/green] Created {dpp_file.relative_to(project_path)}")
            files_created += 1

        # Create .gitignore
        gitignore = project_path / ".gitignore"
        if gitignore.exists() and not args.force:
            console.print("  [yellow]○[/yellow] .gitignore exists (skipped)")
            files_skipped += 1
        else:
            gitignore.write_text(GITIGNORE_CONTENT, encoding="utf-8")
            console.print("  [green]✓[/green] Created .gitignore")
            files_created += 1

        # Create README.md
        if args.readme:
            readme = project_path / "README.md"
            if readme.exists() and not args.force:
                console.print("  [yellow]○[/yellow] README.md exists (skipped)")
                files_skipped += 1
            else:
                readme.write_text(
                    README_TEMPLATE.format(project_name=project_name), encoding="utf-8"
                )
                console.print("  [green]✓[/green] Created README.md")
                files_created += 1

        # Create config file if requested
        if args.config:
            config_file = project_path / ".dppvalidator.json"
            if config_file.exists() and not args.force:
                console.print("  [yellow]○[/yellow] .dppvalidator.json exists (skipped)")
                files_skipped += 1
            else:
                config_file.write_text(
                    json.dumps(DPPVALIDATOR_CONFIG, indent=2) + "\n", encoding="utf-8"
                )
                console.print("  [green]✓[/green] Created .dppvalidator.json")
                files_created += 1

        # Create pre-commit config if requested
        if args.pre_commit:
            precommit = project_path / ".pre-commit-config.yaml"
            if precommit.exists() and not args.force:
                console.print(f"  [yellow]○[/yellow] {precommit.name} exists (skipped)")
                files_skipped += 1
            else:
                precommit.write_text(PRE_COMMIT_CONFIG, encoding="utf-8")
                console.print("  [green]✓[/green] Created .pre-commit-config.yaml")
                files_created += 1

        # Summary
        console.print(f"\n  Files created: {files_created}, skipped: {files_skipped}")

        if files_created > 0:
            console.print("\n[bold green]✓ Project initialized successfully![/bold green]")
            console.print("\nNext steps:")
            console.print("  1. Edit data/sample_passport.json with your product data")
            console.print("  2. Run: dppvalidator validate data/sample_passport.json")
            console.print("  3. Run: dppvalidator doctor (to check your environment)")
        else:
            console.print("\n[yellow]No files created.[/yellow] Use --force to overwrite.")

        return EXIT_SUCCESS

    except PermissionError as e:
        console.print_error(f"Permission denied: {e}")
        return EXIT_ERROR
    except OSError as e:
        console.print_error(f"OS error: {e}")
        return EXIT_ERROR
    except Exception as e:
        console.print_error(f"Unexpected error: {e}")
        return EXIT_ERROR


def _get_template(template_type: str) -> dict[str, Any]:
    """Get DPP template with current dates."""
    template = FULL_DPP_TEMPLATE if template_type == "full" else MINIMAL_DPP_TEMPLATE
    template = template.copy()

    # Update dates to current + 2 years
    now = datetime.now(timezone.utc)
    valid_until = now.replace(year=now.year + 2)

    template["validFrom"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    template["validUntil"] = valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")

    return template
