# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `CredentialStatus` model for W3C VC v2 revocation checking
- `credentialStatus` field on `DigitalProductPassport`
- `Scope1`, `Scope2`, `Scope3` values to `OperationalScope` enum (GHG Protocol)
- SHA-256 integrity hash for schema v0.6.1
- `pytest-asyncio` for native async test support
- `CONTRIBUTING.md` with development guidelines
- Stable error code mapping (`PYDANTIC_ERROR_CODES`) for model validation

### Changed

- `operational_scope` is now optional in `EmissionsPerformance` (enables SEM007 rule)
- Replaced bare `except Exception` catches with specific exception types
- Consolidated error system: removed unused `EnhancedValidationError` class
- Version now read from `pyproject.toml` via `importlib.metadata`
- Async validation uses `asyncio.to_thread()` instead of deprecated API

### Fixed

- README plugin API example now matches actual `SemanticRule` protocol
- Model error codes are now deterministic (based on Pydantic error type)

## [0.1.0] - 2026-01-29

### Added

- Initial release
- `Material` model for fiber composition with ISO 2076 codes
- `SupplyChainNode` model for traceability
- `DigitalProductPassport` model following EU ESPR regulations
- JSON-LD export for Semantic Web compatibility
- Unit tests for all models and validators
- GitHub Actions CI/CD pipeline
- Pre-commit hooks with ruff
