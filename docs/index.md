______________________________________________________________________

## description: Validate EU Digital Product Passports with Python. 80k ops/sec.

# dppvalidator

[![PyPI version](https://img.shields.io/pypi/v/dppvalidator?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/dppvalidator/)
[![Python versions](https://img.shields.io/pypi/pyversions/dppvalidator?style=flat&logo=python&logoColor=white)](https://pypi.org/project/dppvalidator/)
[![Downloads](https://img.shields.io/pypi/dm/dppvalidator?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/dppvalidator/)
[![License](https://img.shields.io/github/license/artiso-ai/dppvalidator?style=flat)](https://github.com/artiso-ai/dppvalidator/blob/main/LICENSE)
[![CI](https://github.com/artiso-ai/dppvalidator/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/artiso-ai/dppvalidator/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/artiso-ai/dppvalidator?style=flat&logo=codecov&logoColor=white)](https://codecov.io/gh/artiso-ai/dppvalidator)

**A Python library for validating Digital Product Passports (DPP) according to EU ESPR regulations and UNTP standards.**

______________________________________________________________________

## Features

- :octicons-check-circle-16:{ .text-green } **Three-Layer Validation** — Schema, Model, and Semantic validation
- :octicons-package-16: **UNTP DPP Schema Support** — Built-in support for UNTP DPP 0.6.1
- :octicons-rocket-16: **High Performance** — 80,000+ validations per second
- :octicons-plug-16: **Plugin System** — Extensible with custom validators and exporters
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

```
# Validate a DPP JSON file
dppvalidator validate passport.json

# Export to JSON-LD
dppvalidator export passport.json --format jsonld

# Show schema information
dppvalidator schema --version 0.6.1
```

## Documentation

- [Installation Guide](getting-started/installation.md) — Detailed installation instructions
- [Quick Start Tutorial](getting-started/quickstart.md) — Get started in 5 minutes
- [CLI Usage](guides/cli-usage.md) — Command line reference
- [Validation Guide](guides/validation.md) — Understanding validation layers
- [API Reference](reference/api/validators.md) — Full API documentation

## For AI Assistants

- [llms.txt](llms.txt) — Quick context for LLMs
- [llms-ctx.txt](llms-ctx.txt) — Extended context with API details

## Contributing

We welcome contributions! See our [Contributing Guide](contributing/development-setup.md) to get started.

## License

MIT License - see [LICENSE](https://github.com/artiso-ai/dppvalidator/blob/main/LICENSE) for details.
