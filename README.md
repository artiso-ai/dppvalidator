# dppvalidator

[![PyPI version](https://img.shields.io/pypi/v/dppvalidator.svg)](https://pypi.org/project/dppvalidator/)
[![Python versions](https://img.shields.io/pypi/pyversions/dppvalidator.svg)](https://pypi.org/project/dppvalidator/)
[![License](https://img.shields.io/github/license/artiso-ai/dppvalidator.svg)](https://github.com/artiso-ai/dppvalidator/blob/main/LICENSE)
[![CI](https://github.com/artiso-ai/dppvalidator/actions/workflows/ci.yml/badge.svg)](https://github.com/artiso-ai/dppvalidator/actions/workflows/ci.yml)

**A Python library for validating Digital Product Passports (DPP) according to EU ESPR regulations and UNTP standards.**

## Features

- **Three-Layer Validation** — Schema, Model, and Semantic validation
- **UNTP DPP Schema Support** — Built-in support for UNTP DPP 0.6.1
- **High Performance** — 80,000+ validations per second
- **Plugin System** — Extensible with custom validators and exporters
- **JSON-LD Export** — W3C Verifiable Credentials compliant output
- **CLI & API** — Use from command line or programmatically

## Installation

```bash
# Using uv (recommended)
uv add dppvalidator

# Using pip
pip install dppvalidator
```

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
# Validate a DPP JSON file
dppvalidator validate passport.json

# Export to JSON-LD
dppvalidator export passport.json --format jsonld

# Show schema information
dppvalidator schema --version 0.6.1
```

## Documentation

Full documentation is available at [https://artiso-ai.github.io/dppvalidator/](https://artiso-ai.github.io/dppvalidator/)

- [Installation Guide](https://artiso-ai.github.io/dppvalidator/getting-started/installation/)
- [Quick Start Tutorial](https://artiso-ai.github.io/dppvalidator/getting-started/quickstart/)
- [CLI Usage](https://artiso-ai.github.io/dppvalidator/guides/cli-usage/)
- [API Reference](https://artiso-ai.github.io/dppvalidator/reference/api/validators/)

## Contributing

We welcome contributions! See our [Contributing Guide](https://artiso-ai.github.io/dppvalidator/contributing/development-setup/) to get started.

## License

MIT License - see [LICENSE](LICENSE) for details.
