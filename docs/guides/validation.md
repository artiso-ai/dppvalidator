# Validation Guide

dppvalidator uses a seven-layer validation architecture to ensure Digital Product
Passports are valid, semantically meaningful, and cryptographically verifiable.

## Quick Start

```python
from dppvalidator import ValidationEngine

# Create engine with auto-detection (default)
engine = ValidationEngine()

# Validate a DPP
result = engine.validate(dpp_data)

if result.valid:
    print("Passport is valid!")
else:
    for error in result.errors:
        print(f"[{error.code}] {error.path}: {error.message}")
```

## Schema Auto-Detection

The engine automatically detects the schema version from your document:

```python
# Auto-detection — engine reads $schema / @context / type from the payload.
engine = ValidationEngine()

# Pin v0.6.1 explicitly. A v0.7.0 payload through this engine fails fast
# with VER001 (version mismatch).
engine = ValidationEngine(schema_version="0.6.1")

# Pin v0.7.0 explicitly.
engine = ValidationEngine(schema_version="0.7.0")
```

Detection checks (in order):

1. `$schema` URL pattern
1. `@context` URLs (`https://test.uncefact.org/vocabulary/untp/dpp/0.6.x/`
   for v0.6.x; `https://vocabulary.uncefact.org/untp/0.7.0/context/` for
   v0.7.0)
1. `type` array presence
1. Fallback to `dppvalidator.schemas.registry.DEFAULT_SCHEMA_VERSION`

The full version-handling story is in
[UNTP DPP versions](../concepts/untp-versions.md).

### Validating v0.6.x payloads against v0.7.0

If you have v0.6.x payloads but want to validate them against the
v0.7.0 schema (because your downstream consumers have moved to
v0.7.0), use the **compat shim** via `--upgrade-from`:

```bash
# Run the v0.6 → v0.7 shim, then validate against v0.7.0.
dppvalidator validate passport.json \
    --upgrade-from 0.6.1 \
    --schema-version 0.7.0
```

```python
from dppvalidator.compat import upgrade
from dppvalidator import ValidationEngine

upgraded, warnings = upgrade(payload_v06)
result = ValidationEngine(schema_version="0.7.0").validate(upgraded)
```

The shim emits structured warnings (`UPG001`–`UPG004`) for fields it
can't fully translate. See the
[migration guide](migration-0-6-to-0-7.md) for the warning codes,
field rename table, and known limitations.

## Validation Layers

### Layer 1: Schema Validation

Validates JSON structure against the UNTP DPP JSON Schema.

```python
engine = ValidationEngine(layers=["schema"])
result = engine.validate(data)
```

### Layer 2: Model Validation

Validates data against Pydantic models with stricter type checking.

```python
engine = ValidationEngine(layers=["model"])
result = engine.validate(data)
```

### Layer 3: JSON-LD Semantic Validation

Validates JSON-LD semantics using PyLD expansion algorithm.

```python
engine = ValidationEngine(validate_jsonld=True)
result = engine.validate(data)
```

**What it checks:**

- `@context` is present and valid
- All terms resolve during expansion
- Custom terms use proper namespacing

### Layer 4: Business Logic Validation

Validates business rules and vocabulary references.

```python
engine = ValidationEngine(layers=["semantic"])
result = engine.validate(data)
```

**What it checks:**

- Vocabulary values (ISO country codes, UN/CEFACT unit codes)
- Material codes (UNECE Rec 46)
- GTIN checksums (GS1 standard)
- Date relationships

### Layer 5: Signature Verification

Verifies Verifiable Credential signatures.

```python
engine = ValidationEngine(verify_signatures=True)
result = engine.validate(data)

if result.signature_valid:
    print(f"Signed by: {result.issuer_did}")
    print(f"Method: {result.verification_method}")
```

**Supported:**

- DID methods: `did:web`, `did:key`
- Algorithms: Ed25519, ES256, ES384
- Proof types: Ed25519Signature2020, DataIntegrityProof, JsonWebSignature2020

## Deep Validation

Validate entire supply chains by crawling linked documents:

```python
result = await engine.validate_deep(
    dpp_data,
    max_depth=3,
    follow_links=["credentialSubject.traceabilityEvents"],
    timeout=30.0,
    auth_header={"Authorization": "Bearer token..."},
)

print(f"Total documents: {result.total_documents}")
print(f"Max depth reached: {result.max_depth_reached}")
print(f"Cycle detected: {result.cycle_detected}")
print(f"All valid: {result.valid}")
```

## Validation Results

```python
result = engine.validate(data)

# Check if valid
if result.valid:
    print("Passport is valid!")

# Access errors
for error in result.errors:
    print(f"[{error.code}] {error.path}: {error.message}")

# Access warnings
for warning in result.warnings:
    print(f"Warning: {warning.message}")

# Signature status (when verify_signatures=True)
if result.signature_valid is not None:
    print(f"Signature valid: {result.signature_valid}")
    print(f"Issuer: {result.issuer_did}")

# Validation time
print(f"Validated in {result.validation_time_ms:.2f}ms")
```

## Error Codes

| Prefix | Layer      | Description                    |
| ------ | ---------- | ------------------------------ |
| SCH    | Schema     | JSON Schema validation errors  |
| MOD    | Model      | Pydantic validation errors     |
| JLD    | JSON-LD    | Context/term resolution errors |
| SEM    | Semantic   | Business rule violations       |
| VOC    | Vocabulary | Code list validation errors    |
| SIG    | Signature  | Credential verification errors |

## Code List Validation

Validate identifiers and codes:

```python
from dppvalidator.vocabularies import (
    validate_gtin,
    is_valid_material_code,
    is_valid_hs_code,
    is_valid_gs1_digital_link,
)

# GTIN checksum validation
validate_gtin("5901234123457")  # True

# Material codes (UNECE Rec 46)
is_valid_material_code("COTTON")  # True
is_valid_material_code("RECYCLED_POLYESTER")  # True

# GS1 Digital Link
is_valid_gs1_digital_link("https://id.gs1.org/01/5901234123457")  # True
```

## Full Validation Example

```python
from dppvalidator import ValidationEngine

# Enable all validation features
engine = ValidationEngine(
    validate_jsonld=True,
    verify_signatures=True,
    strict_mode=True,
)

result = engine.validate(dpp_data)

print(f"Valid: {result.valid}")
print(f"Errors: {len(result.errors)}")
print(f"Warnings: {len(result.warnings)}")
print(f"Signature valid: {result.signature_valid}")
```

## Next Steps

- [JSON-LD Export](jsonld.md) — Export validated passports
- [Validation Layers](../concepts/validation-layers.md) — Architecture deep dive
- [API Reference](../reference/api/validators.md) — Full ValidationEngine API
