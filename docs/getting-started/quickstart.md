______________________________________________________________________

## description: Get started with dppvalidator in 5 minutes.

# Quick Start

Get started with dppvalidator in 5 minutes.

## 1. Install dppvalidator

=== "uv (recommended)"

````
```
uv add dppvalidator
```
````

=== "pip"

````
```
pip install dppvalidator
```
````

## 2. Create a Sample DPP

Create a file called `passport.json`:

```json
{
  "id": "https://example.com/dpp/battery-001",
  "type": ["DigitalProductPassport", "VerifiableCredential"],
  "issuer": {
    "id": "https://example.com/manufacturer",
    "name": "Acme Battery Co."
  },
  "credentialSubject": {
    "id": "https://example.com/product/battery-001",
    "product": {
      "id": "https://example.com/product/battery-001",
      "name": "EV Battery Pack",
      "description": "High-capacity lithium-ion battery for electric vehicles"
    }
  }
}
```

## 3. Validate from Command Line

```
dppvalidator validate passport.json
```

Output:

```
✓ VALID: passport.json
Schema version: 0.6.1
Validation time: 1.23ms
```

## 4. Validate Programmatically

```python
from dppvalidator.validators import ValidationEngine

# Create validation engine
engine = ValidationEngine()

# Load and validate
with open("passport.json") as f:
    import json

    data = json.load(f)

result = engine.validate(data)

# Check result
print(f"Valid: {result.valid}")
print(f"Errors: {len(result.errors)}")
print(f"Warnings: {len(result.warnings)}")
```

## 5. Handle Validation Errors

```python
result = engine.validate({"id": "invalid"})

if not result.valid:
    for error in result.errors:
        print(f"[{error.code}] {error.path}: {error.message}")
```

## 6. Export to JSON-LD

```python
from dppvalidator.exporters import JSONLDExporter
from dppvalidator.models import DigitalProductPassport, CredentialIssuer

# Create a passport
passport = DigitalProductPassport(
    id="https://example.com/dpp/001",
    issuer=CredentialIssuer(id="https://example.com/issuer", name="Acme Corp"),
)

# Export to JSON-LD
exporter = JSONLDExporter()
jsonld = exporter.export(passport)
print(jsonld)
```

## 7. Working with UNTP v0.7.0

dppvalidator supports both UNTP DPP **v0.6.x** (the wire shape used
above — `credentialSubject` wraps a `Product`) and **v0.7.0**
(`credentialSubject` IS the `Product` directly, with new required
fields). The engine auto-detects the version from the payload's
`@context` URL.

### Validate a v0.7.0 payload

```bash
# Auto-detected from the payload's @context URL.
dppvalidator validate passport-v07.json

# Pin explicitly when you want VER001 fail-fast on mismatched payloads.
dppvalidator validate passport-v07.json --schema-version 0.7.0
```

### Upgrade a v0.6.x payload to v0.7.0

```bash
# Write the upgraded payload to a new file.
dppvalidator migrate passport.json -o passport-v07.json

# Validate-after-upgrade in one shot.
dppvalidator validate passport.json \
    --upgrade-from 0.6.1 \
    --schema-version 0.7.0
```

The shim emits structured warnings (`UPG001`–`UPG004`) for fields
it can't fully translate. See the
[migration guide](../guides/migration-0-6-to-0-7.md) for the field
rename table and warning codes, and
[UNTP DPP versions](../concepts/untp-versions.md) for the full
version-handling story.

## Next Steps

- [CLI Usage Guide](../guides/cli-usage.md) — Full CLI reference
  (validate, migrate, schema, …)
- [Validation Guide](../guides/validation.md) — Understanding the five
  validation layers
- [UNTP DPP versions](../concepts/untp-versions.md) — Version detection,
  defaults, adding a new version
- [Migration guide: 0.6 → 0.7](../guides/migration-0-6-to-0-7.md) —
  The compat shim, field rename table, warning codes
- [API Reference](../reference/api/validators.md) — Complete API documentation

## For AI Assistants

If you're an LLM or AI assistant, see our machine-readable context files:

- [llms.txt](../llms.txt) — Quick summary
- [llms-ctx.txt](../llms-ctx.txt) — Extended API context
