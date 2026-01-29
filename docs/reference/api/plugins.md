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

# Auto-discover plugins
registry = PluginRegistry()

# List available plugins
print("Validators:", registry.list_validators())
print("Exporters:", registry.list_exporters())

# Get a specific plugin
validator = registry.get_validator("my_validator")
exporter = registry.get_exporter("my_exporter")

# Manual registration (for testing)
registry = PluginRegistry(auto_discover=False)
registry.register_validator("custom", MyCustomValidator)
```

## Creating Plugins

See the [Plugin Development Guide](../../guides/plugins.md) for detailed instructions.
