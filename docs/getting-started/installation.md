# Installation

## Requirements

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended), pip, or poetry

## Install from PyPI

=== "uv (recommended)"

````
[uv](https://docs.astral.sh/uv/) is a fast Python package manager:

```bash
uv add dppvalidator
```
````

=== "pip"

````
```bash
pip install dppvalidator
```
````

=== "poetry"

````
```bash
poetry add dppvalidator
```
````

## Optional Dependencies

### HTTP Support

For fetching remote schemas and vocabularies:

=== "uv"

````
```bash
uv add "dppvalidator[http]"
```
````

=== "pip"

````
```bash
pip install "dppvalidator[http]"
```
````

This installs `httpx` for async HTTP requests.

### JSON Schema Validation

For strict JSON Schema validation:

=== "uv"

````
```bash
uv add "dppvalidator[jsonschema]"
```
````

=== "pip"

````
```bash
pip install "dppvalidator[jsonschema]"
```
````

### All Optional Dependencies

=== "uv"

````
```bash
uv add "dppvalidator[all]"
```
````

=== "pip"

````
```bash
pip install "dppvalidator[all]"
```
````

## Verify Installation

```bash
# Check version
dppvalidator --version

# Run a quick test
echo '{"id": "https://example.com/dpp"}' | dppvalidator validate -
```

## Development Installation

For contributing to dppvalidator:

```bash
# Clone the repository
git clone https://github.com/artiso-ai/dppvalidator.git
cd dppvalidator

# Install with dev dependencies
uv sync

# Run tests
uv run pytest
```

## Next Steps

- [Quick Start Tutorial](quickstart.md) — Validate your first DPP
- [CLI Usage](../guides/cli-usage.md) — Learn the command line interface
