# Installation

## Requirements

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended), pip, or poetry

## Install from PyPI

=== "uv (recommended)"

```

uv add dppvalidator

```

=== "pip"

```

pip install dppvalidator

```

=== "poetry"

```

poetry add dppvalidator

```

## Optional Dependencies

### CLI Extras

For enhanced CLI output with rich formatting:

=== "uv"

```
uv add "dppvalidator[cli]"
```

=== "pip"

```
pip install "dppvalidator[cli]"
```

This installs `rich` for colored terminal output.

!!! note "Core dependencies included by default"
    The core package already includes `httpx`, `jsonschema`, `pyld`, and `cryptography` — no extras needed for full validation functionality.

## Verify Installation

```
# Check version
dppvalidator --version

# Run a quick test
echo '{"id": "https://example.com/dpp"}' | dppvalidator validate -
```

## Development Installation

For contributing to dppvalidator:

```
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
