# EU DPP JSON-LD Export Guide

> **Status:** ✅ Available
> **Since:** v0.7.0
> **Source:** CIRPASS-2 Official Ontology v1.7.1

This guide covers exporting Digital Product Passports to EU DPP-aligned JSON-LD
format using the CIRPASS-2 vocabulary.

## Overview

The EU DPP export functionality transforms UNTP DPP models to use the official
EU DPP Core Ontology vocabulary. The key principle is:

> **UNTP models remain unchanged** — the export layer transforms vocabulary
> at export time.

This means you can:

- Use the same UNTP models throughout your application
- Export to EU DPP-aligned format when needed
- Maintain full UNTP compatibility

## Quick Start

```python
from dppvalidator.exporters import EUDPPJsonLDExporter

# Create exporter with term mapping enabled
exporter = EUDPPJsonLDExporter(map_terms=True)

# Export passport to EU DPP JSON-LD
jsonld = exporter.export(passport)
print(jsonld)
```

## Exporter Options

### EUDPPJsonLDExporter

The main exporter class with configurable options:

```python
from dppvalidator.exporters import EUDPPJsonLDExporter

# Full control
exporter = EUDPPJsonLDExporter(
    map_terms=True,  # Map UNTP terms to EU DPP (default: True)
    include_untp_context=False,  # Include UNTP context in output (default: False)
    schema_version=None,  # None = auto-detect from passport class
)

# Export methods
jsonld_str = exporter.export(passport)  # Returns JSON string
jsonld_dict = exporter.export_dict(passport)  # Returns dictionary
exporter.export_to_file(passport, "output.jsonld")  # Writes to file
```

### Per-version dispatch (Phase 3c)

The exporter is **version-aware**. UNTP v0.6 and v0.7 use different
source-side spellings (`serialNumber` vs `itemNumber`,
`producedByParty` vs `relatedParty`, …) but most map to the same EU
DPP target URI. The exporter resolves the right column of
`TermMapping` per call:

- **`schema_version=None` (default)** — auto-detect from the
  passport class's module path. A `dppvalidator.models.v0_7.*`
  passport gets the v0.7 mapper, a v0.6 passport gets the v0.6
  mapper. One exporter instance can serve mixed inputs.
- **`schema_version="0.6.1"` or `"0.7.0"`** — pin explicitly.
  Useful when the passport's source version is known up front
  (e.g. CI pipelines), or when you want to *force* the v0.6 mapping
  on a v0.7 passport for downstream-compat scenarios.

```python
from dppvalidator.exporters import EUDPPJsonLDExporter
from dppvalidator.models.v0_7 import DigitalProductPassport

passport = DigitalProductPassport.model_validate(payload_v07_dict)

# Auto-detect (recommended).
EUDPPJsonLDExporter().export(passport)

# Pin explicitly.
EUDPPJsonLDExporter(schema_version="0.7.0").export(passport)
```

Terms removed in v0.7 (e.g. `gtin`) are skipped from the v0.7
mapper's index — they don't appear in the exported JSON-LD even if
the source class somehow carries them. Renamed terms route to the
correct EU DPP URI regardless of which source spelling was used.

### Convenience Functions

For simple use cases:

```python
from dppvalidator.exporters import (
    export_eudpp_jsonld,
    export_eudpp_jsonld_dict,
    get_term_mapping_summary,
)

# String output (auto-detects version).
jsonld = export_eudpp_jsonld(passport)

# Dictionary output, pinned to v0.7.
data = export_eudpp_jsonld_dict(passport, map_terms=True, schema_version="0.7.0")

# Inspect the mapping table for a given version.
summary_v06 = get_term_mapping_summary("0.6.1")
summary_v07 = get_term_mapping_summary("0.7.0")
```

## Term Mapping

The exporter maps UNTP terms to EU DPP Core Ontology terms. The EU
DPP target URI is the same across UNTP versions; only the source-side
spelling shifts between v0.6 and v0.7.

<!-- markdownlint-disable MD013 MD060 -->

| UNTP v0.6 term           | UNTP v0.7 term                      | EU DPP target URI             |
| ------------------------ | ----------------------------------- | ----------------------------- |
| `id`                     | `id`                                | `eudpp:uniqueDPPID`           |
| `DigitalProductPassport` | `DigitalProductPassport`            | `eudpp:DPP`                   |
| `Product`                | `Product`                           | `eudpp:Product`               |
| `serialNumber`           | `itemNumber`                        | `eudpp:uniqueProductID`       |
| `producedByParty`        | `relatedParty[role="manufacturer"]` | `eudpp:hasManufacturer`       |
| `granularityLevel`       | `idGranularity`                     | `eudpp:granularity`           |
| `materialsProvenance`    | `materialProvenance`                | `eudpp:hasMaterialProvenance` |
| `conformityClaim`        | `performanceClaim`                  | `eudpp:hasPerformanceClaim`   |
| `gtin`                   | *removed*                           | `eudpp:GTIN` (v0.6 only)      |
| `validFrom`              | `validFrom`                         | `eudpp:validFrom`             |
| `issuer`                 | `issuer`                            | `eudpp:hasIssuer`             |

<!-- markdownlint-enable MD013 MD060 -->

The full table lives in
[`vocabularies/ontology.py:TERM_MAPPINGS`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/vocabularies/ontology.py).
The `TERM_REMOVED` sentinel marks v0.6 fields with no v0.7 equivalent
(`gtin` today) — those rows drop out of the v0.7 mapper's index.

### Viewing Term Mappings

```python
from dppvalidator.exporters import get_term_mapping_summary

mappings = get_term_mapping_summary()
for untp_term, eudpp_term in mappings.items():
    print(f"{untp_term} → {eudpp_term}")
```

## JSON-LD Context

The exported JSON-LD includes the proper EU DPP context:

```python
from dppvalidator.exporters import get_eudpp_jsonld_context

context = get_eudpp_jsonld_context()
# Returns:
# [
#   "https://www.w3.org/ns/credentials/v2",
#   {"eudpp": "http://dpp.taltech.ee/EUDPP#", ...}
# ]
```

## Validating Exports

Validate that an export has the required EU DPP structure:

```python
from dppvalidator.exporters import validate_eudpp_export

data = exporter.export_dict(passport)
issues = validate_eudpp_export(data)

if issues:
    print("Export validation issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ Valid EU DPP export")
```

## Example Output

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    {
      "eudpp": "http://dpp.taltech.ee/EUDPP#",
      "schema": "https://schema.org/",
      "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
  ],
  "type": ["eudpp:DPP", "VerifiableCredential"],
  "uniqueDPPID": "urn:uuid:12345-abcde",
  "schemaVersion": "CIRPASS-2 v1.3.0",
  "granularity": "model",
  "credentialSubject": {
    "product": {
      "type": "eudpp:Product",
      "productName": "Sustainable T-Shirt",
      "uniqueProductID": "urn:gtin:1234567890123"
    }
  }
}
```

## Dual-Mode Validation

Combine EU DPP export with CIRPASS schema validation:

```python
from dppvalidator.validators import SchemaValidator
from dppvalidator.exporters import EUDPPJsonLDExporter

# Validate with CIRPASS schema
validator = SchemaValidator(schema_type="cirpass")
result = validator.validate(dpp_data)

if result.valid:
    # Export to EU DPP format
    exporter = EUDPPJsonLDExporter()
    jsonld = exporter.export(passport)
```

## SHACL Validation (Optional)

For full RDF-based SHACL validation, install the RDF extras:

```bash
pip install dppvalidator[rdf]
```

Then validate against official SHACL shapes:

```python
from dppvalidator.validators import (
    RDFSHACLValidator,
    is_shacl_validation_available,
)

if is_shacl_validation_available():
    validator = RDFSHACLValidator(use_official_shapes=True)
    result = validator.validate_jsonld(jsonld_data)

    if result.conforms:
        print("✅ Valid against SHACL shapes")
    else:
        for violation in result.violations:
            print(f"✗ {violation['path']}: {violation['message']}")
```

## API Reference

### Classes

| Class                 | Description          |
| --------------------- | -------------------- |
| `EUDPPJsonLDExporter` | Main exporter class  |
| `EUDPPTermMapper`     | Term mapping utility |

### Functions

| Function                     | Description               |
| ---------------------------- | ------------------------- |
| `export_eudpp_jsonld()`      | Export to JSON-LD string  |
| `export_eudpp_jsonld_dict()` | Export to dictionary      |
| `get_eudpp_jsonld_context()` | Get JSON-LD @context      |
| `get_term_mapping_summary()` | Get term mapping dict     |
| `validate_eudpp_export()`    | Validate export structure |

## See Also

- [CIRPASS-2 Integration](../concepts/cirpass-implementation.md)
- [EU DPP Ontology Alignment](../concepts/eudpp-ontology-alignment.md)
- [JSON-LD Export](jsonld.md)
