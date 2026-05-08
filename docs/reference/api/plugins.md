# Plugins API

Plugin registry and discovery for custom validators and exporters.

## PluginRegistry

Central registry for validator and exporter plugins.

::: dppvalidator.plugins.PluginRegistry
options:
show_source: false

## Plugin Discovery

Plugins are discovered via Python entry points.

### Entry Points

```toml
# pyproject.toml
[project.entry-points."dppvalidator.validators"]
my_validator = "my_package:MyValidator"

[project.entry-points."dppvalidator.exporters"]
my_exporter = "my_package:MyExporter"
```

## Usage Example

```python
from dppvalidator.plugins import PluginRegistry
from dppvalidator.plugins.registry import get_default_registry

# Use singleton registry (recommended)
registry = get_default_registry()

# List available plugins
print("Validators:", registry.validator_names)
print("Exporters:", registry.exporter_names)

# Get a specific plugin
validator = registry.get_validator("my_validator")
exporter = registry.get_exporter("my_exporter")

# Manual registration (for testing)
registry = PluginRegistry(auto_discover=False)
registry.register_validator("custom", MyCustomValidator)
```

## Strict Mode

For CI/CD pipelines, use strict mode to raise exceptions on plugin failures:

```python
from dppvalidator.plugins.registry import get_default_registry, PluginError

registry = get_default_registry()

try:
    errors = registry.run_all_validators(passport, strict=True)
except PluginError as e:
    print(f"Plugin failed: {e}")
    sys.exit(1)
```

## Creating Plugins

See the [Plugin Development Guide](../../guides/plugins.md) for detailed instructions.
