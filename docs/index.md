______________________________________________________________________

## Validate EU Digital Product Passports with Python - 80k ops/sec.

# dppvalidator

[![PyPI version](https://img.shields.io/pypi/v/dppvalidator?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/dppvalidator/)
[![Python versions](https://img.shields.io/pypi/pyversions/dppvalidator?style=flat&logo=python&logoColor=white)](https://pypi.org/project/dppvalidator/)
[![Downloads](https://img.shields.io/pypi/dm/dppvalidator?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/dppvalidator/)
[![License](https://img.shields.io/github/license/artiso-ai/dppvalidator?style=flat)](https://github.com/artiso-ai/dppvalidator/blob/main/LICENSE)
[![CI](https://github.com/artiso-ai/dppvalidator/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/artiso-ai/dppvalidator/actions/workflows/ci.yml)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue?style=flat)

**A Python library for validating Digital Product Passports (DPP) according to EU ESPR regulations and UNTP standards.**

______________________________________________________________________

## Features

- :octicons-check-circle-16:{ .text-green } **Seven-Layer Validation** — Schema, Model, Semantic, JSON-LD, Vocabulary, Plugin, and Signature validation
- :octicons-package-16: **UNTP DPP Schema Support** — Both **0.6.x**
  and **0.7.0** (default) wire formats; auto-detected from
  `@context` / `$schema` URLs. See
  [UNTP DPP versions](concepts/untp-versions.md).
- :octicons-arrow-switch-16: **Compat shim 0.6 → 0.7** —
  `dppvalidator migrate` upgrades v0.6.x payloads to v0.7.0 shape
  with structured warnings. See the
  [migration guide](guides/migration-0-6-to-0-7.md).
- :octicons-rocket-16: **High Performance** — 80,000+ validations per second
- :octicons-plug-16: **Plugin System** — Extensible with custom
  validators and exporters; version-aware rules with
  `applies_to_versions` opt-in.
- :octicons-file-code-16: **JSON-LD Export** — W3C Verifiable Credentials compliant output
- :octicons-terminal-16: **CLI & API** — Use from command line or programmatically

## Quick Install

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

## Quick Start

### Validate a DPP file

```python
from dppvalidator.validators import ValidationEngine

engine = ValidationEngine()
result = engine.validate(
    {
        "id": "https://example.com/dpp/12345",
        "issuer": {"id": "https://example.com/issuer", "name": "Acme Corp"},
    }
)

if result.valid:
    print("DPP is valid!")
else:
    for error in result.errors:
        print(f"{error.path}: {error.message}")
```

### Command Line

```bash
# Validate a DPP JSON file (auto-detects version from the payload)
dppvalidator validate passport.json

# Pin a specific UNTP version
dppvalidator validate passport.json --schema-version 0.7.0

# Upgrade a v0.6.x payload to v0.7.0 shape
dppvalidator migrate passport.json -o passport-v07.json

# Validate-after-upgrade in one shot
dppvalidator validate passport.json --upgrade-from 0.6.1 --schema-version 0.7.0

# Export to JSON-LD
dppvalidator export passport.json --format jsonld

# List every registered UNTP version
dppvalidator schema list
```

## Documentation

- [Installation Guide](getting-started/installation.md) — Detailed installation instructions
- [Quick Start Tutorial](getting-started/quickstart.md) — Get started in 5 minutes
- [CLI Usage](guides/cli-usage.md) — Command line reference
- [Validation Guide](guides/validation.md) — Understanding validation layers
- [UNTP DPP versions](concepts/untp-versions.md) — Version handling,
  detection, defaults, adding a new version
- [Migration guide: 0.6.x → 0.7.0](guides/migration-0-6-to-0-7.md) —
  The compat shim, field rename table, warning codes
- [API Reference](reference/api/validators.md) — Full API documentation

## For AI Assistants

- [llms.txt](llms.txt) — Quick context for LLMs
- [llms-ctx.txt](llms-ctx.txt) — Extended context with API details

## Contributing

We welcome contributions! See our [Contributing Guide](contributing/development-setup.md) to get started.

## License

MIT License - see [LICENSE](https://github.com/artiso-ai/dppvalidator/blob/main/LICENSE) for details.
