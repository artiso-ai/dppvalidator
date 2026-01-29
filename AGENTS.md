# dppvalidator Development Guidelines

## Project Overview

**dppvalidator** is a Python library for validating Digital Product Passports (DPP) according to EU ESPR regulations and CIRPASS/UNECE ontologies.

## Tech Stack

- **Python 3.10+** with type hints
- **Pydantic v2** for validation models
- **uv** for package management and versioning
- **ruff** for linting and formatting
- **ty** (Astral) for type checking
- **pytest** for testing
- **GitHub Actions** for CI/CD

## Directory Structure

```text
src/dppvalidator/      # Main package
├── models/            # Pydantic models for DPP entities
├── validators/        # Validation logic
├── exporters/         # JSON-LD and other export formats
├── schemas/           # JSON Schema loading and caching
├── vocabularies/      # Controlled vocabulary loading
├── cli/               # Command-line interface
├── plugins/           # Plugin system
└── __init__.py

tests/                 # Test suite
├── unit/             # Unit tests
├── integration/      # Integration tests
├── property/         # Property-based tests (Hypothesis)
├── fuzz/             # Fuzz tests
└── fixtures/         # Test data
```

## Development Workflow

1. Use **gitflow**: `develop` → `feature/*` → PR → `develop` → `release/*` → `main`
1. Run `/lint` before committing
1. Run `/test` to verify changes
1. Use conventional commits

## Code Principles

- Follow SOLID and DRY principles
- Validate at boundaries with Pydantic
- Type hint all public APIs
- Document public functions with docstrings
