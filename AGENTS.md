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
│   ├── v0_6/          # UNTP 0.6.x models (ProductPassport envelope)
│   ├── v0_7/          # UNTP 0.7.0 models (Product as credentialSubject)
│   └── …              # Top-level shims re-export v0.6 for back-compat
├── validators/        # Validation logic (per-version dispatch)
│   ├── rules/v0_6/    # Semantic rules — v0.6
│   ├── rules/v0_7/    # Semantic rules — v0.7
│   └── …
├── compat/            # Cross-version compat shims (Phase 4)
├── verifier/          # Signature and credential verification
├── exporters/         # JSON-LD and EU DPP export formats
├── schemas/           # JSON Schema loading + version registry
├── vocabularies/      # Controlled vocabulary loading + EU DPP ontology mapping
├── cli/               # Command-line interface (validate, migrate, schema, …)
├── plugins/           # Plugin system (entry-points discovery)
└── __init__.py

tests/                 # Test suite
├── unit/             # Unit tests
├── integration/      # Integration tests (incl. version matrix, plugin)
├── property/         # Property-based tests (Hypothesis)
├── fuzz/             # Fuzz tests
└── fixtures/         # Test data
    ├── valid/        # Per-version happy-path fixtures
    ├── invalid/0.7.0/ # v0.7-specific failure fixtures
    └── upstream/     # SHA-pinned upstream samples
```

## UNTP version handling

dppvalidator supports **UNTP DPP 0.6.x and 0.7.0** in the same release.

- Version detection: `validators/detection.py` is the only place that
  decides the version of a payload.
- Default version: `schemas.registry.DEFAULT_SCHEMA_VERSION` (currently
  `0.6.1`); call `dppvalidator.compat.active_version()` from feature
  code instead of hardcoding the literal.
- Adding a new version: see
  [`.claude/rules/untp-versioning.md`](.claude/rules/untp-versioning.md)
  for the cardinal rules and the minimum touch list. Use
  `/untp-bump <X.Y.Z>` (Claude Code).
- v0.6 → v0.7 upgrade: `dppvalidator.compat.upgrade_0_6_to_0_7.upgrade`
  ships the 17-step shim with structured warnings; CLI surface is
  `dppvalidator migrate` and `dppvalidator validate --upgrade-from`.
- Documentation: [`docs/concepts/untp-versions.md`](docs/concepts/untp-versions.md)
  and [`docs/guides/migration-0-6-to-0-7.md`](docs/guides/migration-0-6-to-0-7.md).

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
- **Cardinal versioning rules** in
  [`.claude/rules/untp-versioning.md`](.claude/rules/untp-versioning.md)
  apply to every change in `src/dppvalidator/{schemas,exporters,models,validators,compat}/`.
