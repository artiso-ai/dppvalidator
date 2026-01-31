# Frequently Asked Questions

Common questions about dppvalidator, Digital Product Passports, and EU compliance.

______________________________________________________________________

## What is dppvalidator?

### What does dppvalidator do?

dppvalidator is a Python library that validates Digital Product Passports (DPP) against EU ESPR regulations and UNTP standards. It ensures your DPP data is structurally correct, semantically meaningful, and optionally cryptographically verifiable before production deployment.

**Core capabilities:**

- **Validate** DPP JSON data through five validation layers
- **Parse** DPP data into type-safe Pydantic models
- **Export** validated passports to JSON-LD format for W3C Verifiable Credentials
- **Verify** cryptographic signatures on signed credentials
- **Crawl** supply chains by following linked documents

### What dppvalidator is NOT

- **Not a DPP generator** — It validates existing data, not creates it from scratch
- **Not a database** — It doesn't store passports; use it as validation middleware
- **Not a blockchain** — Signature verification supports DIDs, but doesn't require blockchain
- **Not a UI framework** — It's a backend library; build your own frontend

______________________________________________________________________

## Who Should Use dppvalidator?

### Primary Users

| Role                       | Use Case                                             |
| -------------------------- | ---------------------------------------------------- |
| **Fashion/Textile Brands** | Validate DPP data before QR code generation          |
| **Backend Developers**     | Integrate DPP validation into APIs and microservices |
| **DevOps Engineers**       | Add compliance gates to CI/CD pipelines              |
| **Sustainability Teams**   | Validate supplier DPP submissions                    |
| **System Integrators**     | Migrate legacy product data to DPP format            |

### Industry Applications

- **Textiles & Apparel** — EU ESPR compliance starting 2027
- **Electronics & Batteries** — Battery passport requirements
- **Construction Materials** — Building product passports
- **Packaging** — Recyclability and material traceability

______________________________________________________________________

## Technical Questions

### What Python versions are supported?

Python **3.10+** is required. We recommend Python 3.12 for best performance.

### What are the core dependencies?

All included by default:

- **Pydantic v2** — Data validation and parsing
- **jsonschema** — JSON Schema validation
- **pyld** — JSON-LD expansion and context resolution
- **httpx** — HTTP client for deep validation
- **cryptography** — Signature verification
- **PyJWT** — JWT token handling

Optional extras:

- **rich** — CLI formatting (install with `pip install dppvalidator[cli]`)

### How fast is validation?

| Validation Type   | Throughput                          |
| ----------------- | ----------------------------------- |
| Schema only       | ~200,000 ops/sec                    |
| Model only        | ~85,000 ops/sec                     |
| Full (all layers) | ~60,000 ops/sec                     |
| With JSON-LD      | ~10,000 ops/sec (network-dependent) |

*Benchmarked on Apple M2, Python 3.12*

### What schema versions are supported?

Currently supported:

- **UNTP DPP 0.6.1** (default)

Schema version is auto-detected from `@context` or `$schema` fields. You can also specify it explicitly:

```python
engine = ValidationEngine(schema_version="0.6.1")
```

______________________________________________________________________

## Validation Questions

### What are the five validation layers?

1. **Layer 0: Schema Detection** — Auto-detects DPP schema version
1. **Layer 1: Schema Validation** — JSON Schema structure validation
1. **Layer 2: Model Validation** — Pydantic type validation
1. **Layer 3: JSON-LD Semantic** — Context expansion and term resolution
1. **Layer 4: Business Logic** — Vocabulary codes, date logic, GTIN checksums
1. **Layer 5: Cryptographic** — VC signature verification (optional)

### Can I run only specific layers?

Yes, use the `layers` parameter:

```python
# Schema validation only (fastest)
engine = ValidationEngine(layers=["schema"])

# Model + Semantic only
engine = ValidationEngine(layers=["model", "semantic"])

# Full validation with JSON-LD
engine = ValidationEngine(layers=["schema", "model", "semantic", "jsonld"])
```

### What error codes does dppvalidator use?

| Prefix | Layer      | Description                    |
| ------ | ---------- | ------------------------------ |
| `SCH`  | Schema     | JSON Schema validation errors  |
| `MOD`  | Model      | Pydantic validation errors     |
| `JLD`  | JSON-LD    | Context/term resolution errors |
| `SEM`  | Semantic   | Business rule violations       |
| `VOC`  | Vocabulary | Code list validation errors    |
| `SIG`  | Signature  | Credential verification errors |
| `PRS`  | Parse      | Input parsing errors           |

### How do I handle validation errors?

```python
result = engine.validate(dpp_data)

if not result.valid:
    for error in result.errors:
        print(f"[{error.code}] {error.path}: {error.message}")
        if error.suggestion:
            print(f"  Suggestion: {error.suggestion}")
```

Each error includes:

- `code` — Error identifier (e.g., `SEM001`)
- `path` — JSON path to the error (e.g., `$.credentialSubject.materials[0].massFraction`)
- `message` — Human-readable description
- `suggestion` — How to fix the error (optional)
- `docs_url` — Link to detailed documentation (optional)

______________________________________________________________________

## Use Case Questions

### Can I use dppvalidator for CI/CD compliance gates?

Yes! Add validation to your pipeline:

```yaml
# .github/workflows/validate-dpp.yml
- name: Validate DPP files
  run: |
    pip install dppvalidator
    dppvalidator validate data/passports/*.json --strict --format json
```

Exit codes:

- `0` — All validations passed
- `1` — Validation failed
- `2` — System error (file not found, invalid JSON)

### Can I validate supplier submissions via API?

Yes, integrate into your backend:

```python
from fastapi import FastAPI, HTTPException
from dppvalidator import ValidationEngine

app = FastAPI()
engine = ValidationEngine(strict_mode=True)


@app.post("/api/v1/dpp/validate")
async def validate_dpp(dpp: dict):
    result = engine.validate(dpp)
    if not result.valid:
        raise HTTPException(status_code=422, detail=result.to_dict())
    return {"valid": True, "passport_id": dpp.get("id")}
```

### Can I validate entire supply chains?

Yes, use deep validation to crawl linked documents:

```python
result = await engine.validate_deep(
    dpp_data,
    max_depth=3,
    follow_links=["credentialSubject.traceabilityEvents"],
    timeout=30.0,
    auth_header={"Authorization": "Bearer token..."},
)

print(f"Total documents validated: {result.total_documents}")
print(f"All valid: {result.valid}")
```

### Can I batch validate thousands of passports?

Yes, use async batch validation:

```python
results = await engine.validate_batch(
    list_of_dpps,
    concurrency=20,
)

valid_count = sum(1 for r in results if r.valid)
print(f"Valid: {valid_count}/{len(results)}")
```

### Can I add custom validation rules?

Yes, use the plugin system:

```python
from dppvalidator.plugins import PluginRegistry


class TextileFiberRule:
    rule_id = "TEX001"
    description = "Fiber composition must sum to 100%"
    severity = "error"

    def check(self, passport):
        violations = []
        # Your validation logic here
        return violations


registry = PluginRegistry()
registry.register_validator("textile", TextileFiberRule)
```

______________________________________________________________________

## Export Questions

### What export formats are supported?

- **JSON** — Standard JSON output
- **JSON-LD** — W3C Verifiable Credentials format

```python
from dppvalidator.exporters import JSONLDExporter

exporter = JSONLDExporter()
jsonld = exporter.export(passport)
```

### Is the JSON-LD output compatible with VC wallets?

Yes, exported JSON-LD follows the W3C Verifiable Credentials Data Model v2 and includes proper `@context` for UNTP DPP vocabularies.

______________________________________________________________________

## Compliance Questions

### Does dppvalidator ensure EU ESPR compliance?

dppvalidator validates the **technical structure** of DPP data against UNTP standards. However, **compliance is your responsibility** — you must ensure your product data accurately reflects:

- Material composition
- Manufacturing processes
- Environmental indicators
- Chemical compliance (REACH)
- Traceability information

dppvalidator catches data errors; it doesn't verify the truthfulness of claims.

### What standards does dppvalidator support?

- **UNTP DPP** — UN/CEFACT Digital Product Passport specification
- **W3C VC** — Verifiable Credentials Data Model v2
- **JSON Schema Draft 2020-12** — For structure validation
- **GS1** — GTIN checksum validation
- **ISO** — Country codes, unit codes via UNECE vocabularies

### When will EU DPP requirements take effect?

- **2027** — Textiles and apparel
- **2027** — Batteries (separate regulation)
- **TBD** — Other product categories under ESPR

Start preparing now to avoid last-minute compliance failures.

______________________________________________________________________

## Troubleshooting

### Why is JSON-LD validation slow?

JSON-LD validation requires fetching context documents from remote URLs. Enable caching:

```python
# Contexts are cached after first request
# Subsequent validations will be faster
engine = ValidationEngine(validate_jsonld=True)
```

For offline environments, context resolution may fail.

### Why do I get "pyld not installed" warnings?

This shouldn't happen with a standard installation since `pyld` is a core
dependency. Try reinstalling:

```bash
pip install --force-reinstall dppvalidator
# or
uv sync --reinstall-package dppvalidator
```

### How do I enable signature verification?

Signature verification is available out of the box since `cryptography` is
a core dependency:

```python
engine = ValidationEngine(verify_signatures=True)
result = engine.validate(signed_dpp)

if result.signature_valid:
    print(f"Signed by: {result.issuer_did}")
```

______________________________________________________________________

## Getting Help

- **Documentation** — [artiso-ai.github.io/dppvalidator](https://artiso-ai.github.io/dppvalidator)
- **GitHub Issues** — [github.com/artiso-ai/dppvalidator/issues](https://github.com/artiso-ai/dppvalidator/issues)
- **PyPI** — [pypi.org/project/dppvalidator](https://pypi.org/project/dppvalidator)

For AI assistants, see [llms.txt](llms.txt) and [llms-ctx.txt](llms-ctx.txt).
