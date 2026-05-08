# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - _unreleased_

This release adds first-class support for **UNTP DPP 0.7.0** alongside
the existing 0.6.x. Both wire formats coexist and are auto-detected
from `@context` / `$schema` URLs. The plan is captured in
[`docs/plans/UNTP_0.7.0_MIGRATION.md`](docs/plans/UNTP_0.7.0_MIGRATION.md);
each phase has its own implementation log there.

### Added

- **UNTP DPP 0.7.0 schema, context, and Pydantic models**. Vendored
  upstream artefacts under `src/dppvalidator/{schemas,vocabularies}/data/`
  with SHA-256 pins. New version-namespaced model package
  `dppvalidator.models.v0_7.*` (envelope, product, materials, claims,
  identifiers, primitives) covering every required field per the
  upstream schema. The existing top-level `dppvalidator.models.*`
  imports continue to resolve to v0.6 for back-compat.
- **Per-version validator dispatch**. New `_MODEL_BY_VERSION`
  (model layer), `ALL_RULES_BY_VERSION` (semantic-rule layer),
  `LINK_PATHS_BY_VERSION` (deep validator) tables; `ValidationEngine`
  selects the right artefact set per detected version.
- **VER001 version-mismatch fail-fast**. Engine raises `VER001` when
  `schema_version` is pinned and the payload's declared version
  conflicts.
- **Compat shim 0.6.x → 0.7.0**. New `dppvalidator.compat` package
  exporting `upgrade(data, *, country_lookup=None) -> (dict, list[UpgradeWarning])`,
  plus `active_version()` / `is_version()` helpers and four warning
  codes (`UPG001`–`UPG004`). Implements all 17 transformation steps
  from §Phase 4 of the migration plan.
- **`dppvalidator migrate` CLI**. Writes the upgraded JSON to
  `-o` / `--in-place` / stdout; refuses on warnings unless
  `--accept-warnings`; always emits a sidecar
  `<output>.warnings.json` when blocking warnings fire.
- **`dppvalidator validate --upgrade-from <ver>`**. Runs the shim
  before validating; surfaces upgrade + validation issues in one
  report.
- **Per-version EU DPP exporter mapping**. `TermMapping` extended
  with `untp_v0_6` / `untp_v0_7` columns + a `TERM_REMOVED` sentinel;
  `EUDPPJsonLDExporter(schema_version=…)` dispatches per-call;
  auto-detect resolves the source version from the passport's class.
- **Plugin version-awareness**. New
  `BrandNameRuleV07` in the example plugin demonstrates the
  `applies_to_versions` opt-in pattern; the example plugin is now a
  CI-tested target via `tests/integration/test_example_plugin.py`.
- **Manifest integrity test**.
  `tests/unit/test_manifest_integrity.py` SHA-256-verifies every
  vendored `.json` / `.jsonld` artefact and includes a drift-catch
  for un-manifested files.
- **Sample classification test**.
  `tests/unit/test_samples_classification.py` pins
  `detect_schema_version()` per real-world sample under
  `tests/fixtures/samples/`.
- **Production-URL split per artefact**. `SchemaVersion` and
  `MANIFEST.json` now carry both an SHA-pinned `source_url` and a
  human-friendly `production_url` (e.g. `untp.unece.org`).
- **Documentation**. New
  [`docs/concepts/untp-versions.md`](docs/concepts/untp-versions.md)
  and [`docs/guides/migration-0-6-to-0-7.md`](docs/guides/migration-0-6-to-0-7.md);
  refreshed schema, JSON-LD, validation, CLI, FAQ, and index pages
  with both v0.6 and v0.7 examples.

### Changed

- `dppvalidator schema list` reports all three registered versions
  (0.6.0, 0.6.1, 0.7.0).
- `valid_dpp_data` pytest fixture is now parametrised over both
  matrix versions; tests pin to a single version with
  `@pytest.mark.dpp_version("X.Y.Z")`.
- v0.6 model files were relocated to `dppvalidator.models.v0_6/`
  with thin re-export shims at the top level — no callers should
  notice.
- v0.6 semantic rules likewise relocated to
  `dppvalidator.validators.rules.v0_6/`; new
  `dppvalidator.validators.rules.v0_7/` carries the v0.7 ports.
- `EUDPPJsonLDExporter` no longer hardcodes a single mapping table;
  the new auto-detection reads the passport's module path.
- The `Characteristics` `$def` quirk in the upstream UNTP 0.7.0 DPP
  schema (empty `properties`, description copy-pasted from `Claim`)
  is documented in `MANIFEST.json` and
  `docs/concepts/cirpass-implementation.md`.

### Deprecated

- Hardcoded version literals (`"0.6.1"` / `"0.7.0"`) in feature code
  outside `schemas/registry.py` and `exporters/contexts.py`. The
  `tests/unit/test_no_version_literals.py` guard rejects new
  occurrences. Feature code should call
  `dppvalidator.compat.active_version()` instead.

### Tests

- 2019 passing, 13 skipped (by-design via the dpp_version marker),
  1 xfailed; coverage 92.20 % (above the 90 % gate).
- Net new tests added across the migration: ~150+ unit cases, the
  17-case version matrix, the 13-case manifest integrity, the
  27-case samples classification, the 17-case plugin integration,
  the 50-case compat shim, the 10-case CLI migrate, the 4-case
  round-trip integration, and 10 production-URL pins.

## [0.3.2] - 2026-02-01

### Added

- **URDNA2015 RDF Canonicalization**: W3C-compliant signature verification using pyld
- **Module-Level Schema Caching**: Shared cache across ValidationEngine instances
  - `clear_schema_cache()` function to force schema reloading
- **Plugin Registry Singleton**: Optimized plugin discovery with `get_default_registry()`
  - `reset_default_registry()` function for testing scenarios
- **Bundled JSON-LD Contexts**: Pre-bundled W3C VC v2 context for offline validation
- **Async DID Resolution**: Non-blocking `DIDResolver.resolve_async()` method
- **Strict Plugin Mode**: `run_all_validators(strict=True)` raises `PluginError` on failure
- **Migration Guide**: New `docs/migration.md` for version upgrade documentation
- **CI Performance Benchmarks**: Automated benchmark job on main branch pushes
- **SBOM Generation**: CycloneDX Software Bill of Materials in release workflow
- **License Scanning**: Dependency license compliance checking in CI
- **CIRPASS-2 Schema Support (Phase 5)**: Dual-mode validation for UNTP and EU DPP schemas
  - `CIRPASSSchemaLoader` and `CIRPASSSHACLLoader` in `schemas/cirpass_loader.py`
  - `SchemaValidator(schema_type="cirpass")` for CIRPASS-specific validation
  - Bundled CIRPASS-2 v1.3.0 JSON Schema from dpp.vocabulary-hub.eu
- **EU DPP Ontology Vocabularies**: Complete vocabulary modules aligned with CIRPASS-2
  - `eudpp_actors.py`: 24 actor/role classes (Manufacturer, Recycler, etc.)
  - `eudpp_classes.py`: EU DPP Core Ontology class definitions
  - `eudpp_lca.py`: 16 PEF/OEF impact categories per EU 2021/2279
  - `eudpp_relations.py`: EU DPP object property mappings
  - `eudpp_substances.py`: Substances of Concern (SOC) vocabulary
  - `ontology.py`: Ontology alignment utilities
  - `rdf_loader.py`: RDF graph loading with optional rdflib support
- **Bundled Ontology Data Files**: Offline validation without network access
  - `vocabularies/data/ontologies/`: 5 Turtle files (eudpp_core, product_dpp, actors_roles, soc, lca)
  - `vocabularies/data/schemas/`: CIRPASS JSON Schema, SHACL shapes, OpenAPI spec, XSD
- **EU DPP JSON-LD Exporter**: UNTP to EU DPP format conversion
  - `EUDPPJsonLDExporter` class with namespace handling and term mapping
  - `EUDPPTermMapper` for UNTP→EU DPP vocabulary translation
  - `export_eudpp_jsonld()` and `export_eudpp_jsonld_dict()` convenience functions
- **Official SHACL Validation**: RDF-based constraint validation
  - `OfficialSHACLLoader` for CIRPASS SHACL shapes (cirpass_dpp_shacl.ttl)
  - `RDFSHACLValidator` with pyshacl integration
  - `SHACLValidationResult` dataclass with violations/warnings/info
  - `validate_jsonld_with_official_shacl()` convenience function
- **CIRPASS Semantic Rules** (CQ prefix): EU DPP business logic validation
  - CQ001: Mandatory ESPR attributes (issuer, validFrom, product)
  - CQ004: Substances of Concern CAS/EINECS identification per ESPR Art 7(5a)
  - CQ011: Manufacturer unique operator identifier per ESPR Annex III(g)
  - CQ016: DPP validity period per ESPR Art 9(2i)
  - CQ017: Granularity level consistency per SR5423 Annex II Part B
  - CQ020: Product weight/volume declarations per ESPR Annex I(j)
- **Textile-Specific Rules** (TXT prefix): ESPR textile product requirements
  - TXT001: Textile HS code validation (Chapters 50-63)
  - TXT002: Material composition/fiber declaration
  - TXT003: Synthetic fiber microplastic release info
  - TXT004: Durability information per ESPR Annex I
  - TXT005: Care instructions linking
- **Error Documentation**: Comprehensive error code reference
  - 74 new error documentation pages (SCH, PRS, MDL, VOC, CQ, TXT codes)
  - `scripts/check_error_docs.py` for documentation coverage verification
  - CI workflow step for error documentation completeness
- **Optional Dependency Extras**: Modular installation
  - `[rdf]` extra: rdflib>=7.0.0, pyshacl>=0.25.0 for SHACL validation
  - `[all]` extra: combined cli + rdf features
- **Test Suite Expansion**: CIRPASS/EU DPP coverage
  - `test_cirpass_loader.py`, `test_cirpass_rules.py`, `test_cirpass_vocabulary.py`
  - `test_eudpp_actors.py`, `test_eudpp_classes.py`, `test_eudpp_lca.py`
  - `test_eudpp_relations.py`, `test_eudpp_substances.py`, `test_eudpp_export.py`
  - `test_rdf_loader.py`, `test_ontology_alignment.py`, `test_shacl_official.py`
  - `test_schema_dual_mode.py`, `test_textile_rules.py`
  - `test_cirpass_shacl_integration.py` (integration)
  - `test_fuzz_cirpass.py`, `test_property_cirpass.py` (fuzz/property)
  - Shared fixtures in `tests/conftest.py` (`valid_dpp_data`, `minimal_dpp_data`)
- **Validation Layer Architecture**: New `validators/layers.py` module with Strategy Pattern
  - `ValidationContext` dataclass for shared validation state
  - `ValidationLayer` abstract base class with 7 implementations
  - `SchemaLayer`, `ModelLayer`, `SemanticLayer`, `JsonLdLayer`,
    `VocabularyLayer`, `PluginLayer`, `SignatureLayer`
- **Schema Auto-Detection (Phase 0)**: `ValidationEngine` now defaults to `schema_version="auto"`
  - Detects version from `$schema`, `@context`, or `type` array
  - New `detect_schema_version()` and `is_dpp_document()` functions in `validators/detection.py`
- **JSON-LD Semantic Validation (Phase 1)**: PyLD-based expansion validation
  - `JSONLDValidator` class with `CachingDocumentLoader` for remote contexts
  - New error codes: JLD001-JLD004 for context and term validation
  - Enable with `ValidationEngine(validate_jsonld=True)`
- **Extended Code Lists (Phase 2)**: UNECE Rec 46, HS codes, GTIN validation
  - `validate_gtin()`, `is_valid_material_code()`, `is_valid_hs_code()` functions
  - GS1 Digital Link URL parsing and validation
  - 85 UNECE Rec 46 material codes, 156 textile HS codes (Chapters 50-63)
  - New rules: VOC003 (material codes), VOC004 (HS codes), VOC005 (GTIN checksum)
- **Verifiable Credential Verification (Phase 3)**: DID resolution and signature verification
  - `CredentialVerifier`, `DIDResolver`, `SignatureVerifier` classes in `verifier/` module
  - Support for `did:web` and `did:key` resolution
  - Ed25519, ES256, ES384 signature algorithms
  - Ed25519Signature2020, DataIntegrityProof, JsonWebSignature2020 proof types
  - New `ValidationResult` fields: `signature_valid`, `issuer_did`, `verification_method`
  - Enable with `ValidationEngine(verify_signatures=True)`
- **Deep/Recursive Validation (Phase 4)**: Supply chain traversal
  - `DeepValidator` class with async crawling, rate limiting, retry logic
  - Cycle detection for circular references
  - Configurable depth limits and link following paths
  - New `ValidationEngine.validate_deep()` async method
- `CredentialStatus` model for W3C VC v2 revocation checking
- `credentialStatus` field on `DigitalProductPassport`
- `Scope1`, `Scope2`, `Scope3` values to `OperationalScope` enum (GHG Protocol)
- SHA-256 integrity hash for schema v0.6.1
- `pytest-asyncio` for native async test support
- `CONTRIBUTING.md` with development guidelines
- Stable error code mapping (`PYDANTIC_ERROR_CODES`) for model validation

### Changed

- **Signature Verification**: Uses URDNA2015 RDF canonicalization (W3C compliant)
- **Error Codes**: Plugin errors standardized from `PLG_ERROR` to `PLG001` format
- **validate_deep()**: Now returns typed `DeepValidationResult` instead of `Any`
- **Layer Type Hints**: All validators use `Validator | None` protocol type hints
- **Docstrings**: Engine docstring updated to document seven validation layers
- **Async Pattern**: `validate_async()` docstring documents sync/async relationship
- **Mutation Testing**: CI scope expanded to validators, verifier, and models
- **File Size Check**: Path inputs now validated for size before reading (DoS protection)
- **base58 Library**: Uses `base58>=2.1.0` instead of custom implementation
- **Documentation**: README expanded with EU DPP/CIRPASS-2 sections
  - Optional features installation guide (RDF, JSON-LD, signatures)
  - EU DPP & CIRPASS-2 support section with examples
  - CIRPASS-2 Integration documentation link
- **Package Metadata**: `pyproject.toml` classifiers and keywords updated
  - New keywords: eu-regulation, sustainability, circular-economy, textile, battery-passport,
    untp, verifiable-credentials, json-ld, w3c, supply-chain, traceability
  - Added `Environment :: Console` classifier
  - Build includes bundled `.json`, `.ttl`, `.xsd`, `.yaml` data files
- **MkDocs Navigation**: Expanded error reference structure
  - Full error code hierarchy (SCH, PRS, MDL, JLD, SEM, VOC, CQ, TXT)
  - EU DPP Ontology Alignment and CIRPASS-2 Implementation concept pages
  - EU DPP Export guide added
- **CLI Output**: JSON format uses plain print to avoid Rich ANSI codes
- **Console Fallback**: Panel output respects `_file` parameter for testability
- **Breaking**: `ValidationEngine()` now defaults to `schema_version="auto"`
- **Architecture**: Validation uses Strategy Pattern with pluggable layers
  - `validate()` refactored from 88 lines to 32 lines
  - Complexity reduced: C901 (15→0), PLR0912 (14→0)
- **CLI Refactoring**: Watch, init, and validate commands restructured
  - `watch.py`: Extracted `FileWatcher` and `WatchLoop` classes
  - `init.py`: Data-driven `FileSpec` pattern for scaffolding
  - `validate.py`: Extracted `_format_issue()` helper
- **Vocabulary Loader**: `_extract_values()` uses dispatch pattern
- Core dependencies simplified: `httpx`, `jsonschema`, `pyld`, `cryptography`, `PyJWT` now required
- Removed all `HAS_*` conditional checks from source code
- `has_vc_support()` now always returns `True`
- `operational_scope` is now optional in `EmissionsPerformance` (enables SEM007 rule)
- Replaced bare `except Exception` catches with specific exception types
- Consolidated error system: removed unused `EnhancedValidationError` class
- Version now read from `pyproject.toml` via `importlib.metadata`
- Async validation uses `asyncio.to_thread()` instead of deprecated API

### Security

- **URDNA2015 Canonicalization**: Signature verification now uses W3C-compliant
  RDF canonicalization instead of simplified JSON sorting
- **File Size Validation**: Path inputs checked for size before reading (DoS protection)
- **base58 Library**: Replaced custom implementation with audited `base58>=2.1.0`
- **JWT Verification**: Proper algorithm validation for ES256, ES384, EdDSA
- **Async DID Resolution**: Non-blocking network I/O prevents thread exhaustion

### Fixed

- README plugin API example now matches actual `SemanticRule` protocol
- Model error codes are now deterministic (based on Pydantic error type)
- Unused imports and arguments cleaned up across verifier module
- Flaky `test_engine_never_crashes_on_binary` deadline increased to 500ms
- Redundant exception handling in `verifier.py` simplified
- Test assertions updated for URDNA2015 N-Quads output format
- Cache eviction tests fixed for pre-populated bundled contexts

## [0.2.0] - 2026-01-30

### Added

- **Deep/Recursive Validation**: Supply chain traversal with `DeepValidator`
  - Async crawling, rate limiting, cycle detection
  - `ValidationEngine.validate_deep()` async method
- **Verifiable Credential Verification**: DID resolution and signatures
  - `CredentialVerifier`, `DIDResolver`, `SignatureVerifier` classes
  - Support for `did:web` and `did:key` resolution
  - Ed25519, ES256, ES384 signature algorithms
- **JSON-LD Semantic Validation**: PyLD-based expansion validation
  - `JSONLDValidator` with `CachingDocumentLoader`
  - Error codes JLD001-JLD004
- **Extended Code Lists**: UNECE Rec 46, HS codes, GTIN validation
  - `validate_gtin()`, `is_valid_material_code()`, `is_valid_hs_code()`
  - GS1 Digital Link URL parsing
- **Schema Auto-Detection**: `schema_version="auto"` default
- **Validation Layer Architecture**: Strategy Pattern in `validators/layers.py`
- Bundled JSON-LD contexts for offline validation
- Async DID resolution with `DIDResolver.resolve_async()`

### Changed

- Signature verification uses URDNA2015 RDF canonicalization (W3C compliant)
- Core dependencies: `httpx`, `jsonschema`, `pyld`, `cryptography`, `PyJWT` now required
- `ValidationEngine()` defaults to `schema_version="auto"`

### Security

- URDNA2015 canonicalization for signature verification
- File size validation for DoS protection
- Uses audited `base58>=2.1.0` library

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
