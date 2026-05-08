"""Init command for CLI - scaffolds a new DPP project."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION

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
- [UNTP DPP Schema](https://untp.unece.org/specification/DigitalProductPassport)
"""

DPPVALIDATOR_CONFIG: dict[str, Any] = {
    "$schema": "https://artiso-ai.github.io/dppvalidator/schemas/config.json",
    "version": "1.0",
    "validation": {
        "strict": False,
        # Resolved at template-emission time so a generated project always
        # gets the validator's currently-shipping default UNTP version.
        # Phase 3 will introduce a `--schema-version` flag on `init` so users
        # can pin a specific version (e.g. `0.7.0`) at scaffolding time.
        "schema_version": DEFAULT_SCHEMA_VERSION,
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


@dataclass
class FileSpec:
    """Specification for a file to create (Data-Driven Pattern)."""

    relative_path: str
    content_factory: Callable[[InitContext], str]
    condition: Callable[[argparse.Namespace], bool] = lambda _: True
    display_name: str | None = None

    def get_display_name(self) -> str:
        """Get name for console output."""
        return self.display_name or self.relative_path


@dataclass
class InitContext:
    """Context for file creation."""

    project_path: Path
    project_name: str
    args: argparse.Namespace


def _create_file(
    spec: FileSpec,
    context: InitContext,
    console: Console,
) -> tuple[int, int]:
    """Create a single file from spec. Returns (created, skipped) counts."""
    if not spec.condition(context.args):
        return 0, 0

    filepath = context.project_path / spec.relative_path
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if filepath.exists() and not context.args.force:
        console.print(f"  [yellow]○[/yellow] {spec.get_display_name()} exists (skipped)")
        return 0, 1

    content = spec.content_factory(context)
    filepath.write_text(content, encoding="utf-8")
    console.print(f"  [green]✓[/green] Created {spec.get_display_name()}")
    return 1, 0


def _build_file_specs() -> list[FileSpec]:
    """Build the list of file specifications."""
    return [
        FileSpec(
            relative_path="data/sample_passport.json",
            content_factory=lambda ctx: json.dumps(_get_template(ctx.args.template), indent=2)
            + "\n",
            display_name="data/sample_passport.json",
        ),
        FileSpec(
            relative_path=".gitignore",
            content_factory=lambda _: GITIGNORE_CONTENT,
        ),
        FileSpec(
            relative_path="README.md",
            content_factory=lambda ctx: README_TEMPLATE.format(project_name=ctx.project_name),
            condition=lambda args: args.readme,
        ),
        FileSpec(
            relative_path=".dppvalidator.json",
            content_factory=lambda _: json.dumps(DPPVALIDATOR_CONFIG, indent=2) + "\n",
            condition=lambda args: args.config,
        ),
        FileSpec(
            relative_path=".pre-commit-config.yaml",
            content_factory=lambda _: PRE_COMMIT_CONFIG,
            condition=lambda args: args.pre_commit,
        ),
    ]


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


def _validate_project(args: argparse.Namespace, console: Console) -> tuple[Path, str] | None:
    """Validate project setup. Returns (project_path, project_name) or None on error."""
    project_path = Path(args.path).resolve()
    project_name = args.name or project_path.name

    if not PROJECT_NAME_PATTERN.match(project_name):
        console.print_error(
            f"Invalid project name: '{project_name}'. "
            "Use letters, numbers, hyphens, and underscores only."
        )
        return None

    return project_path, project_name


def _setup_project_directory(
    project_path: Path, args: argparse.Namespace, console: Console
) -> bool:
    """Set up project directory. Returns True on success."""
    if project_path.exists() and any(project_path.iterdir()) and not args.force:
        console.print("  [yellow]⚠[/yellow] Directory not empty. Use --force to overwrite files.")

    project_path.mkdir(parents=True, exist_ok=True)

    try:
        test_file = project_path / ".dppvalidator_init_test"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
    except PermissionError:
        console.print_error(f"No write permission for: {project_path}")
        return False

    return True


def _print_success_message(files_created: int, console: Console) -> None:
    """Print success message with next steps."""
    if files_created > 0:
        console.print("\n[bold green]✓ Project initialized successfully![/bold green]")
        console.print("\nNext steps:")
        console.print("  1. Edit data/sample_passport.json with your product data")
        console.print("  2. Run: dppvalidator validate data/sample_passport.json")
        console.print("  3. Run: dppvalidator doctor (to check your environment)")
    else:
        console.print("\n[yellow]No files created.[/yellow] Use --force to overwrite.")


def run(args: argparse.Namespace, console: Console) -> int:
    """Execute init command."""
    result = _validate_project(args, console)
    if result is None:
        return EXIT_ERROR

    project_path, project_name = result
    console.print(f"\n📦 Initializing DPP project in [bold]{project_path}[/bold]\n")

    try:
        if not _setup_project_directory(project_path, args, console):
            return EXIT_ERROR

        context = InitContext(
            project_path=project_path,
            project_name=project_name,
            args=args,
        )

        files_created = 0
        files_skipped = 0

        for spec in _build_file_specs():
            created, skipped = _create_file(spec, context, console)
            files_created += created
            files_skipped += skipped

        console.print(f"\n  Files created: {files_created}, skipped: {files_skipped}")
        _print_success_message(files_created, console)

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
