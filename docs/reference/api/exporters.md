# Exporters API

Export Digital Product Passports to various formats.

## JSONExporter

Export passports to JSON format.

::: dppvalidator.exporters.JSONExporter
options:
show_source: false

## JSONLDExporter

Export passports to JSON-LD format with W3C VC context.

::: dppvalidator.exporters.JSONLDExporter
options:
show_source: false

## Usage Example

```python
from dppvalidator.exporters import JSONExporter, JSONLDExporter
from dppvalidator.models import DigitalProductPassport, CredentialIssuer

# Create a passport
passport = DigitalProductPassport(
    id="https://example.com/dpp/001",
    issuer=CredentialIssuer(id="https://example.com/issuer", name="Acme Corp"),
)

# Export to JSON
json_exporter = JSONExporter()
json_output = json_exporter.export(passport)
print(json_output)

# Export to JSON-LD
jsonld_exporter = JSONLDExporter()
jsonld_output = jsonld_exporter.export(passport)
print(jsonld_output)
```

## JSON-LD Context

The JSON-LD exporter adds W3C Verifiable Credentials context:

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://vocabulary.uncefact.org/untp/dpp/0.6.1"
  ],
  "type": ["DigitalProductPassport", "VerifiableCredential"],
  ...
}
```
