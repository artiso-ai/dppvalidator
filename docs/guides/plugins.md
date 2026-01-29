# Plugin Development

dppvalidator supports custom validators and exporters through a plugin system.

## Plugin Architecture

Plugins are discovered via Python entry points. You can create:

- **Validators** — Custom validation rules
- **Exporters** — Custom export formats

## Creating a Validator Plugin

### 1. Define the Validator

```python
# my_validator.py
from dppvalidator.validators.protocols import ValidatorProtocol
from dppvalidator.validators.results import ValidationResult, ValidationError


class MyCustomValidator:
    """Custom validator for business-specific rules."""

    def validate(self, data: dict) -> ValidationResult:
        errors = []

        # Custom validation logic
        if "customField" not in data:
            errors.append(
                ValidationError(
                    path="$.customField",
                    message="Custom field is required",
                    code="CUSTOM001",
                    layer="plugin",
                    severity="error",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### 2. Register via Entry Point

In your `pyproject.toml`:

```toml
[project.entry-points."dppvalidator.validators"]
my_validator = "my_package.my_validator:MyCustomValidator"
```

### 3. Use the Plugin

```python
from dppvalidator.plugins import PluginRegistry

registry = PluginRegistry()
validator = registry.get_validator("my_validator")
result = validator.validate(data)
```

## Creating an Exporter Plugin

### 1. Define the Exporter

```python
# my_exporter.py
from dppvalidator.exporters.protocols import ExporterProtocol
from dppvalidator.models import DigitalProductPassport


class XMLExporter:
    """Export DPP to XML format."""

    def export(self, passport: DigitalProductPassport) -> str:
        # Convert to XML
        return f"<dpp id='{passport.id}'></dpp>"
```

### 2. Register via Entry Point

```toml
[project.entry-points."dppvalidator.exporters"]
xml = "my_package.my_exporter:XMLExporter"
```

## Manual Registration

For testing or custom setups:

```python
from dppvalidator.plugins import PluginRegistry

registry = PluginRegistry(auto_discover=False)
registry.register_validator("my_validator", MyCustomValidator)
registry.register_exporter("xml", XMLExporter)
```

## Plugin Discovery

```python
# List all discovered plugins
registry = PluginRegistry()

print("Validators:", registry.list_validators())
print("Exporters:", registry.list_exporters())
```

## Next Steps

- [API Reference](../reference/api/plugins.md) — Plugin Registry API
- [Validation Guide](validation.md) — Understanding validation layers
