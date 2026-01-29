# dppvalidator-example-plugin

Example plugin for [dppvalidator](https://github.com/artiso-ai/dppvalidator) demonstrating how to create custom validators and exporters.

## Installation

```
# Using uv (recommended)
uv pip install dppvalidator-example-plugin

# Or using pip
pip install dppvalidator-example-plugin
```

Or for development:

```
cd examples/dppvalidator_example_plugin

# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Features

### Custom Validators

This plugin provides two example validators:

- **BrandNameRule** (`SEM_BRAND`) - Validates that products have a brand name
- **MinMaterialsRule** (`SEM_MINMAT`) - Warns if products have fewer than 2 materials declared

### Custom Exporter

- **CSVExporter** - Exports passport data to CSV format

## Usage

Once installed, validators are automatically discovered and used by dppvalidator:

```python
from dppvalidator import ValidationEngine

engine = ValidationEngine()
result = engine.validate({"id": "...", "issuer": {...}})

# Plugin validators are automatically included!
```

### Manual Registration

For testing or custom setups:

```python
from dppvalidator.plugins import PluginRegistry
from dppvalidator_example_plugin.validators import BrandNameRule

registry = PluginRegistry(auto_discover=False)
registry.register_validator("brand_check", BrandNameRule())
```

### Using the CSV Exporter

```python
from dppvalidator_example_plugin.exporters import CSVExporter

exporter = CSVExporter()
csv_content = exporter.export(passport)
```

## Creating Your Own Plugin

See the source code in `src/` for examples of how to:

1. Implement the `SemanticRule` protocol for validators
1. Create custom exporters
1. Register plugins via entry points

## License

MIT
