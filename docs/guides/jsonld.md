# JSON-LD Export Guide

dppvalidator can export Digital Product Passports to JSON-LD format, compliant with W3C Verifiable Credentials.

## Basic Export

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
jsonld_string = exporter.export(passport)
print(jsonld_string)
```

## Output Format

The JSON-LD output includes the W3C VC context:

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://vocabulary.uncefact.org/untp/dpp/0.6.1"
  ],
  "type": ["DigitalProductPassport", "VerifiableCredential"],
  "id": "https://example.com/dpp/001",
  "issuer": {
    "id": "https://example.com/issuer",
    "name": "Acme Corp"
  }
}
```

## Export Options

### Custom Context

```python
exporter = JSONLDExporter(
    context=[
        "https://www.w3.org/ns/credentials/v2",
        "https://custom.context.example.com",
    ]
)
```

### Pretty Print

```python
jsonld = exporter.export(passport, indent=2)
```

## CLI Export

```
# Export to JSON-LD
dppvalidator export passport.json --format jsonld

# Save to file
dppvalidator export passport.json --format jsonld -o output.jsonld
```

## Verifiable Credentials

The exported JSON-LD is structured as a W3C Verifiable Credential:

- `@context` — Links to VC and UNTP vocabularies
- `type` — Includes "VerifiableCredential" and "DigitalProductPassport"
- `issuer` — The credential issuer
- `credentialSubject` — The product passport data
- `validFrom` / `validUntil` — Credential validity period

## Next Steps

- [Plugin Development](plugins.md) — Create custom exporters
- [API Reference](../reference/api/exporters.md) — Full Exporter API
