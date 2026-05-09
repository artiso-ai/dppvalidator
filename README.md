<p align="center">
  <img src="docs/assets/logo.png" alt="dppvalidator logo" width="120">
  <h1 align="center">dppvalidator</h1>
  <p align="center">
    <strong>The open-source compliance engine for EU Digital Product Passports</strong>
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/dppvalidator/" style="text-decoration: none;"><img src="https://img.shields.io/pypi/v/dppvalidator?style=flat&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/dppvalidator/" style="text-decoration: none;"><img src="https://img.shields.io/pypi/pyversions/dppvalidator?style=flat&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://pypi.org/project/dppvalidator/" style="text-decoration: none;"><img src="https://img.shields.io/pypi/dm/dppvalidator?style=flat&logo=pypi&logoColor=white" alt="Downloads"></a>
  <a href="https://github.com/artiso-ai/dppvalidator/blob/main/LICENSE" style="text-decoration: none;"><img src="https://img.shields.io/github/license/artiso-ai/dppvalidator?style=flat" alt="License"></a>
  <a href="https://github.com/artiso-ai/dppvalidator/actions/workflows/ci.yml" style="text-decoration: none;"><img src="https://github.com/artiso-ai/dppvalidator/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <a href="https://artiso-ai.github.io/dppvalidator/" style="text-decoration: none;"><img src="https://img.shields.io/badge/docs-mkdocs-blue?style=flat&logo=materialformkdocs&logoColor=white" alt="Documentation"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue?style=flat" alt="Platform">
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

______________________________________________________________________

**dppvalidator** is a Python library for validating [Digital Product Passports (DPP)](https://untp.unece.org/docs/specification/DigitalProductPassport/) according to EU ESPR regulations and [UNTP](https://uncefact.unece.org/) standards.

**Starting 2027, every textile and apparel product sold in the EU must have a Digital Product Passport.** This library ensures your DPP data is compliant *before* it hits production — saving fashion brands from costly compliance failures and enabling seamless integration with the circular economy.

## Why dppvalidator?

<!-- markdownlint-disable MD013 MD060 -->

| Challenge                         | Solution                                                                                                                |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Complex JSON Schema validation    | **Seven-layer validation** catches errors at schema, model, semantic, JSON-LD, vocabulary, plugin, and signature levels |
| Evolving UNTP specifications      | **Both UNTP DPP 0.6.x and 0.7.0** — auto-detected; `dppvalidator migrate` upgrades 0.6 → 0.7                            |
| Integration with existing systems | **CLI + Python API** for pipelines, CI/CD, and application integration                                                  |
| Custom business rules             | **Plugin system** for domain-specific validators and exporters                                                          |
| Interoperability requirements     | **JSON-LD export** for W3C Verifiable Credentials compliance                                                            |

<!-- markdownlint-enable MD013 MD060 -->

## Installation

```
# Using uv (recommended)
uv add dppvalidator

# With CLI extras (rich formatting)
uv add "dppvalidator[cli]"

# Or using pip
pip install dppvalidator
pip install "dppvalidator[cli]"  # with CLI extras
```

### Optional Features

#### RDF/SHACL Validation

For SHACL validation against official CIRPASS-2 shapes:

```bash
# Using uv (recommended)
uv add "dppvalidator[rdf]"

# Or using pip
pip install "dppvalidator[rdf]"
```

```python
from dppvalidator.validators import ValidationEngine

# Enable SHACL validation (requires [rdf] extra)
engine = ValidationEngine(enable_shacl=True)
result = engine.validate(dpp_data)
```

#### JSON-LD Semantic Validation

JSON-LD validation is included by default (via `pyld`):

```python
engine = ValidationEngine(validate_jsonld=True)
result = engine.validate(dpp_data)
```

#### Signature Verification

Signature verification is included by default (via `cryptography`):

```python
engine = ValidationEngine(verify_signatures=True)
result = engine.validate(dpp_data)
```

> **Note:** `pyld` and `cryptography` are core dependencies installed automatically.
> Only `[rdf]` (for SHACL via rdflib/pyshacl) and `[cli]` (for rich formatting)
> are true optional extras.

**Requirements:** Python 3.10+

## Quick Start

### Validate a DPP

```python
from dppvalidator.validators import ValidationEngine

engine = ValidationEngine()

result = engine.validate(
    {
        "id": "https://example.com/dpp/battery-001",
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "issuer": {
            "id": "https://example.com/manufacturer",
            "name": "Acme Battery Co.",
        },
        "credentialSubject": {
            "id": "https://example.com/product/battery-001",
            "product": {
                "name": "EV Battery Pack",
                "description": "High-capacity lithium-ion battery",
            },
        },
    }
)

if result.valid:
    print(f"✓ Valid in {result.validation_time_ms:.2f}ms")
else:
    for error in result.errors:
        print(f"✗ [{error.code}] {error.path}: {error.message}")
```

### Command Line

```
# Validate a DPP file
dppvalidator validate passport.json

# Strict mode - warnings become errors
dppvalidator validate passport.json --strict

# Export to JSON-LD (W3C Verifiable Credential format)
dppvalidator export passport.json --format jsonld --output passport.jsonld

# Display schema information
dppvalidator schema --version 0.6.1
```

### Export to JSON-LD

```python
from dppvalidator.models import DigitalProductPassport, CredentialIssuer
from dppvalidator.exporters import JSONLDExporter

passport = DigitalProductPassport(
    id="https://example.com/dpp/product-001",
    issuer=CredentialIssuer(
        id="https://example.com/issuer", name="Sustainable Textiles Ltd."
    ),
)

exporter = JSONLDExporter()
jsonld_output = exporter.export(passport)
# Ready for W3C Verifiable Credentials ecosystem
```

## Supported specs

dppvalidator validates **two parallel families** in the same
release: UNTP DPP (UN/CEFACT Verifiable Credential format) and the
CIRPASS DPP reference structure (CIRPASS-2 hierarchical message).
Family + version are auto-detected from the payload's `@context` /
shape; pin explicitly with `--target` (family) and `--schema-version`
(version), or `target=` / `schema_version=` in Python.

<!-- markdownlint-disable MD013 MD060 -->

### UNTP DPP

| Version   | Status             | Default? | Wire shape                                                                                                                                                                          |
| --------- | ------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0.6.0** | Supported (legacy) | no       | `credentialSubject` is `ProductPassport` wrapping `Product`.                                                                                                                        |
| **0.6.1** | Default            | **yes**  | Same shape as 0.6.0; current `DEFAULT_SCHEMA_VERSION`.                                                                                                                              |
| **0.7.0** | Fully supported    | no       | `credentialSubject` IS the `Product` directly. New required fields: `name` (envelope), `idScheme`, `idGranularity`, `productCategory`, `producedAtFacility`, `countryOfProduction`. |

### CIRPASS DPP reference structure

| Version   | Status          | Default? | Wire shape                                                                                                                                                                        |
| --------- | --------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1.3.0** | Fully supported | **yes**  | Hierarchical message: root carries `dppIdentifier`, `product`, `issuedAt`, `effectivePeriod`, `relatedActors`, `composition`, `substancesOfConcern`, `lca`, `connectorRelations`. |

EUDPP modules bundled: P_DPP / ACTOR / SOC / CON v1.9.1, LCA
v1.9.4-Maki. Per-module SHACL pass with attributed source (Phase 4).

<!-- markdownlint-enable MD013 MD060 -->

### Migration shims

Two shims project between families and across UNTP versions:

```bash
# UNTP 0.6 → 0.7 (intra-family upgrade)
dppvalidator migrate passport-v06.json -o passport-v07.json

# UNTP 0.7 → CIRPASS reference structure 1.3 (cross-family forward)
dppvalidator migrate passport-v07.json --to cirpass-1.3 -o cirpass.json --accept-warnings

# CIRPASS 1.3 → UNTP 0.7 (cross-family reverse)
dppvalidator migrate cirpass.json --to untp-0.7 -o untp.json --accept-warnings
```

### Pilot profiles + plugins

<!-- markdownlint-disable MD013 MD060 -->

| Pilot                                           | Activation                       | Source                                                              |
| ----------------------------------------------- | -------------------------------- | ------------------------------------------------------------------- |
| Textile DPP v1 (legacy)                         | `--profile textile-v1`           | built-in                                                            |
| Textile DPP v2 (MVP 2025-12-04)                 | `--profile textile-v2`           | built-in                                                            |
| Tyres (GDSO Birth/Collection/Retread/Recycling) | `pip install dppvalidator-tyres` | [`plugins/tyres/`](plugins/tyres) — Pre-1.0 / Experimental, GPL-3.0 |

<!-- markdownlint-enable MD013 MD060 -->

### Reading guide

<!-- markdownlint-disable MD013 MD060 -->

| You want…                         | See                                                                                |
| --------------------------------- | ---------------------------------------------------------------------------------- |
| Big-picture orientation           | [`docs/concepts/cirpass-2-alignment.md`](docs/concepts/cirpass-2-alignment.md)     |
| Migrate a UNTP fixture to CIRPASS | [`docs/guides/migrate-untp-to-cirpass.md`](docs/guides/migrate-untp-to-cirpass.md) |
| UNTP version handling             | [`docs/concepts/untp-versions.md`](docs/concepts/untp-versions.md)                 |
| 0.6 → 0.7 upgrade                 | [`docs/guides/migration-0-6-to-0-7.md`](docs/guides/migration-0-6-to-0-7.md)       |
| Field-by-field UNTP↔CIRPASS map   | [`docs/concepts/untp-cirpass-mapping.md`](docs/concepts/untp-cirpass-mapping.md)   |
| CLI exit codes                    | [`docs/reference/cli/exit-codes.md`](docs/reference/cli/exit-codes.md)             |
| CIRPASS Pydantic API              | [`docs/reference/cirpass/index.md`](docs/reference/cirpass/index.md)               |

<!-- markdownlint-enable MD013 MD060 -->

## Features

### Seven-Layer Validation Architecture

```mermaid
flowchart TD
    subgraph Input
        A[/"📄 Input Data (JSON)"/]
    end

    subgraph Layer0["Layer 0: Schema Detection"]
        A0["Auto-detect schema version<br/>from $schema, @context, type"]
    end

    subgraph Layer1["Layer 1: Schema Validation"]
        B["JSON Schema Draft 2020-12<br/>Required fields, types, formats"]
    end

    subgraph Layer2["Layer 2: Model Validation"]
        C["Pydantic v2 Models<br/>Type coercion, URL validation"]
    end

    subgraph Layer3["Layer 3: JSON-LD Semantic"]
        C2["PyLD Expansion<br/>Context resolution, term validation"]
    end

    subgraph Layer4["Layer 4: Business Logic"]
        D["Business Rules & Vocabularies<br/>ISO codes, date logic, GTIN checksums"]
    end

    subgraph Layer5["Layer 5: Cryptographic"]
        E["VC Signature Verification<br/>DID resolution, Ed25519/ECDSA"]
    end

    subgraph Output
        F[/"✅ ValidationResult<br/>.valid | .errors | .signature_valid"/]
    end

    A --> A0
    A0 --> B
    B -->|"SCH001-SCH099"| C
    C -->|"MOD001-MOD099"| C2
    C2 -->|"JLD001-JLD099"| D
    D -->|"SEM001-SEM099"| E
    E -->|"SIG001-SIG099"| F
```

### Selective Layer Validation

```python
from dppvalidator.validators import ValidationEngine

# Run all layers (default)
engine = ValidationEngine()

# Schema validation only (fastest)
engine = ValidationEngine(layers=["schema"])

# Skip schema, run model + semantic
engine = ValidationEngine(layers=["model", "semantic"])

# Enable JSON-LD validation
engine = ValidationEngine(validate_jsonld=True)

# Enable signature verification
engine = ValidationEngine(verify_signatures=True)
result = engine.validate(dpp_data)
if result.signature_valid:
    print(f"Signed by: {result.issuer_did}")
```

### Performance

| Layer            | Mean Time | Throughput        |
| ---------------- | --------- | ----------------- |
| Model (minimal)  | 0.012ms   | 84,387 ops/sec    |
| Model (full)     | 0.016ms   | 63,945 ops/sec    |
| Semantic         | 0.005ms   | 200,889 ops/sec   |
| Full (Model+Sem) | 0.022ms   | 45,735 ops/sec    |
| Engine Creation  | 0.001ms   | 1,524,868 ops/sec |

*Benchmarked on Apple Silicon (M-series). JSON-LD and signature verification depend on network latency (cached after first request).*

### Plugin System

Extend dppvalidator with custom validators following the `SemanticRule` protocol:

```python
from dppvalidator.plugins import PluginRegistry


# Create a custom validator implementing SemanticRule protocol
class TextileFiberRule:
    """Custom rule to validate textile fiber composition."""

    rule_id = "TEX001"
    description = "Fiber composition must sum to 100%"
    severity = "error"
    suggestion = "Ensure all fiber percentages add up to 100"
    docs_url = "https://example.com/textile-rules"

    def check(self, passport):
        """Return list of (json_path, error_message) tuples."""
        violations = []
        # Add your validation logic here
        return violations


# Register with the plugin registry
registry = PluginRegistry(auto_discover=False)
registry.register_validator("textile", TextileFiberRule)

# ValidationEngine auto-discovers plugins via entry points by default
engine = ValidationEngine(load_plugins=True)
```

## EU DPP & CIRPASS-2 Support

dppvalidator includes full support for the **EU DPP Core Ontology** from CIRPASS-2:

```python
from dppvalidator.validators import SchemaValidator
from dppvalidator.exporters import EUDPPJsonLDExporter

# Dual-mode validation: UNTP (default) or EU DPP
validator = SchemaValidator(schema_type="cirpass")
result = validator.validate(dpp_data)

# Export to EU DPP-aligned JSON-LD
exporter = EUDPPJsonLDExporter(map_terms=True)
jsonld = exporter.export(passport)
```

| Feature                  | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| **Dual-mode validation** | Switch between UNTP and CIRPASS schemas                                  |
| **EU DPP vocabulary**    | 24 actor/role classes, 16 PEF categories                                 |
| **JSON-LD export**       | EU DPP-aligned output with term mapping                                  |
| **SHACL validation**     | Optional RDF-based validation (requires `pip install dppvalidator[rdf]`) |

> 🏆 **Aligned with [dpp.vocabulary-hub.eu/specifications](https://dpp.vocabulary-hub.eu/specifications)** as of 2025-02-01. To our knowledge, dppvalidator is the most comprehensive open-source Python package for EU DPP vocabulary compliance.

## Documentation

📚 **Full documentation:** [artiso-ai.github.io/dppvalidator](https://artiso-ai.github.io/dppvalidator/)

| Guide                                                                                              | Description                               |
| -------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| [Installation](https://artiso-ai.github.io/dppvalidator/getting-started/installation/)             | Setup and CLI extras                      |
| [Quick Start](https://artiso-ai.github.io/dppvalidator/getting-started/quickstart/)                | Get started in 5 minutes                  |
| [CLI Reference](https://artiso-ai.github.io/dppvalidator/guides/cli-usage/)                        | Command-line interface                    |
| [Validation Layers](https://artiso-ai.github.io/dppvalidator/concepts/validation-layers/)          | Understanding the five-layer architecture |
| [CIRPASS-2 Integration](https://artiso-ai.github.io/dppvalidator/concepts/cirpass-implementation/) | EU DPP ontology alignment                 |
| [API Reference](https://artiso-ai.github.io/dppvalidator/reference/api/validators/)                | Complete Python API                       |

## Built for Fashion & Textiles

The EU's [Ecodesign for Sustainable Products Regulation (ESPR)](https://commission.europa.eu/energy-climate-change-environment/standards-tools-and-labels/products-labelling-rules-and-requirements/ecodesign-sustainable-products-regulation_en) mandates Digital Product Passports for textiles starting 2027. dppvalidator helps fashion brands prepare now:

| DPP Requirement                | How dppvalidator Helps                       |
| ------------------------------ | -------------------------------------------- |
| Material composition & weights | Validates fiber percentages sum to 100%      |
| Manufacturing processes        | Validates supply chain node structure        |
| Environmental indicators       | Supports LCA data validation                 |
| Chemical compliance (REACH)    | Semantic validation for substance references |
| Traceability information       | Validates production stage URIs              |
| Durability & recyclability     | Custom validators via plugin system          |

### Use Cases

dppvalidator serves diverse stakeholders across the product lifecycle:

| Use Case                      | Target User         | Value Proposition                          |
| ----------------------------- | ------------------- | ------------------------------------------ |
| **Pre-production validation** | Brand product teams | Catch errors before QR code generation     |
| **Supplier onboarding**       | Procurement teams   | Validate supplier DPP submissions          |
| **CI/CD compliance gates**    | DevOps teams        | Automated compliance checks in pipelines   |
| **Data migration**            | IT teams            | Validate legacy data exports to DPP format |
| **Consumer apps**             | App developers      | DPP scanning, parsing, and display         |
| **Recycling facilities**      | Waste management    | Material identification for sorting        |
| **Resale platforms**          | Recommerce          | Product authentication and history         |
| **Customs & compliance**      | Border control      | Import compliance verification             |

**Example: CI/CD Integration**

```yaml
# .github/workflows/validate-dpp.yml
- name: Validate DPP files
  run: dppvalidator validate data/passports/*.json --strict
```

**Example: Supplier Validation API**

```python
from dppvalidator.validators import ValidationEngine

engine = ValidationEngine(strict_mode=True)


def validate_supplier_submission(dpp_json: dict) -> bool:
    result = engine.validate(dpp_json)
    if not result.valid:
        raise ValueError(f"Invalid DPP: {result.errors}")
    return True
```

## Related Standards

- [UNTP Digital Product Passport](https://untp.unece.org/docs/specification/DigitalProductPassport/) — UN/CEFACT specification
- [EU ESPR Regulation](https://commission.europa.eu/energy-climate-change-environment/standards-tools-and-labels/products-labelling-rules-and-requirements/ecodesign-sustainable-products-regulation_en) — Ecodesign for Sustainable Products
- [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model/) — Credential format standard

> ⚠️ **Note on UNTP Specification:** The UNTP Digital Product Passport specification is under active development and not yet ready for production implementation. We track the latest maintained releases and will update dppvalidator as the specification stabilizes. See the [UNTP releases page](https://untp.unece.org/docs/specification/DigitalProductPassport/) for current status.

## Known Limitations

### Signature Verification

| Feature               | Status       | Recommendation                          |
| --------------------- | ------------ | --------------------------------------- |
| Data Integrity Proofs | ✅ Supported | Use for production                      |
| JWS Proofs            | ✅ Supported | Use for production                      |
| JWT Credentials       | ✅ Supported | Full verification (ES256, ES384, EdDSA) |

**JWT Credentials:** JWT-encoded Verifiable Credentials are fully verified via DID resolution and cryptographic signature verification. Supported algorithms include ES256, ES384, and EdDSA (Ed25519). For maximum interoperability, Data Integrity Proofs are recommended.

### Canonicalization

The signature verification uses **simplified JSON canonicalization** (sorted keys) rather than full [URDNA2015](https://www.w3.org/TR/rdf-canon/) RDF canonicalization. This may cause verification failures for credentials signed with strict W3C Data Integrity canonicalization.

For production deployments requiring full W3C VC compliance:

```python
# Future: Use pyld for URDNA2015 canonicalization
from pyld import jsonld

normalized = jsonld.normalize(credential, {"algorithm": "URDNA2015"})
```

## Contributing

We welcome contributions! Here's how to get started:

```
# Clone the repository
git clone https://github.com/artiso-ai/dppvalidator.git
cd dppvalidator

# Install dependencies with uv
uv sync --all-extras

# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

See our [Contributing Guide](https://artiso-ai.github.io/dppvalidator/contributing/development-setup/) for more details.

## About ARTISO

<table border="0" cellspacing="0" cellpadding="0" style="border: none;"><tr><td style="border: none;">

**dppvalidator** is developed and maintained by [ARTISO](https://www.artiso.ai), a Barcelona-based fashion technology company.

</td><td align="right" valign="top">
<a href="https://www.artiso.ai"><img src="https://www.artiso.ai/ARTISO.svg" alt="ARTISO" height="40"></a>
</td></tr></table>

We believe the fashion industry's transition to sustainability requires **open, accessible tools**. By open-sourcing dppvalidator, we're enabling brands of all sizes - from emerging designers to global retailers - to meet EU compliance requirements without proprietary solutions.

**Our commitment:**

- **Open Source First** - Core validation engine will always be free and MIT-licensed
- **Fashion Expertise** - Built by a team with deep industry experience at major brands
- **Circular Economy** - Enabling the data infrastructure for textile recycling and resale
- **Community Driven** - We welcome contributions from brands, sustainability experts, and developers

> *"The circular economy can only work if recyclers can read the tags. dppvalidator ensures interoperability across the entire fashion supply chain."*

## License

MIT License — see [LICENSE](LICENSE) for details.

______________________________________________________________________

<p align="center">
  <a href="https://www.artiso.ai">artiso.ai</a> ·
  <a href="https://artiso-ai.github.io/dppvalidator/">Documentation</a> ·
  <a href="https://github.com/artiso-ai/dppvalidator/issues">Issues</a>
</p>

<p align="center">
  <sub>Built with ❤️ in Barcelona for a more sustainable fashion industry</sub>
</p>
