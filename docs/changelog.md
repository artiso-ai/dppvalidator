# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Schema Auto-Detection (Phase 0)**: `ValidationEngine` now defaults to
  `schema_version="auto"`
  - Detects version from `$schema`, `@context`, or `type` array
  - New `detect_schema_version()` and `is_dpp_document()` functions
- **JSON-LD Semantic Validation (Phase 1)**: PyLD-based expansion validation
  - `JSONLDValidator` class with `CachingDocumentLoader` for remote contexts
  - New error codes: JLD001-JLD004 for context and term validation
  - Enable with `ValidationEngine(validate_jsonld=True)`
- **Extended Code Lists (Phase 2)**: UNECE Rec 46, HS codes, GTIN validation
  - `validate_gtin()`, `is_valid_material_code()`, `is_valid_hs_code()`
  - GS1 Digital Link URL parsing and validation
  - 85 UNECE Rec 46 material codes, 156 textile HS codes (Chapters 50-63)
  - New rules: VOC003, VOC004, VOC005
- **Verifiable Credential Verification (Phase 3)**: DID resolution and signatures
  - `CredentialVerifier`, `DIDResolver`, `SignatureVerifier` in `verifier/`
  - Support for `did:web` and `did:key` resolution
  - Ed25519, ES256, ES384 signature algorithms
  - New `ValidationResult` fields: `signature_valid`, `issuer_did`
  - Enable with `ValidationEngine(verify_signatures=True)`
- **Deep/Recursive Validation (Phase 4)**: Supply chain traversal
  - `DeepValidator` with async crawling, rate limiting, retry logic
  - Cycle detection for circular references
  - New `ValidationEngine.validate_deep()` async method
- `CredentialStatus` model for W3C VC v2 revocation checking
- `credentialStatus` field on `DigitalProductPassport`
- `Scope1`, `Scope2`, `Scope3` values to `OperationalScope` enum (GHG Protocol)
- SHA-256 integrity hash for schema v0.6.1
- `pytest-asyncio` for native async test support
- `CONTRIBUTING.md` with development guidelines
- Stable error code mapping (`PYDANTIC_ERROR_CODES`) for model validation

### Changed

- **Breaking**: `ValidationEngine()` defaults to `schema_version="auto"`
- **Architecture**: Validation expanded from 3 to 5 layers
- Core dependencies: `httpx`, `jsonschema`, `pyld`, `cryptography` now required
- Removed all `HAS_*` conditional checks from source code
- `has_vc_support()` now always returns `True`
- `operational_scope` is now optional in `EmissionsPerformance`
- Replaced bare `except Exception` catches with specific exception types
- Consolidated error system: removed unused `EnhancedValidationError` class
- Version now read from `pyproject.toml` via `importlib.metadata`
- Async validation uses `asyncio.to_thread()` instead of deprecated API

### Fixed

- README plugin API example now matches actual `SemanticRule` protocol
- Model error codes are now deterministic (based on Pydantic error type)
- Unused imports and arguments cleaned up across verifier module
- Flaky `test_engine_never_crashes_on_binary` deadline increased to 500ms

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

[0.1.0]: https://github.com/artiso-ai/dppvalidator/releases/tag/v0.1.0
[unreleased]: https://github.com/artiso-ai/dppvalidator/compare/v0.1.0...HEAD
