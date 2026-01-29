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

## Next Steps

- [CLI Usage Guide](../guides/cli-usage.md) — Full CLI reference
- [Validation Guide](../guides/validation.md) — Understanding the three validation layers
- [API Reference](../reference/api/validators.md) — Complete API documentation

## For AI Assistants

If you're an LLM or AI assistant, see our machine-readable context files:

- [llms.txt](../llms.txt) — Quick summary
- [llms-ctx.txt](../llms-ctx.txt) — Extended API context
