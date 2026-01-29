# Plugin Development Guide

This guide explains how to create plugins for dppvalidator to extend its validation and export capabilities.

## Overview

dppvalidator uses Python's entry point system for plugin discovery. Plugins can provide:

- **Custom Validators** - Additional semantic validation rules
- **Custom Exporters** - New export formats (CSV, XML, etc.)

## Quick Start

### 1. Create Your Package

```
my-dppvalidator-plugin/
├── pyproject.toml
├── README.md
└── src/
    └── my_plugin/
        ├── __init__.py
        ├── validators.py
        └── exporters.py
```

### 2. Configure Entry Points

In your `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-dppvalidator-plugin"
version = "0.1.0"
dependencies = ["dppvalidator>=0.1.0"]

[project.entry-points."dppvalidator.validators"]
my_rule = "my_plugin.validators:MyCustomRule"

[project.entry-points."dppvalidator.exporters"]
xml = "my_plugin.exporters:XMLExporter"
```

### 3. Implement the SemanticRule Protocol

```python
from typing import Literal


class MyCustomRule:
    """Custom validation rule for DPP."""

    # Required attributes
    rule_id: str = "MY_RULE"
    description: str = "Description of what this rule checks"
    severity: Literal["error", "warning", "info"] = "warning"

    def check(self, passport) -> list[tuple[str, str]]:
        """Check the passport and return violations.

        Args:
            passport: DigitalProductPassport instance

        Returns:
            List of (json_path, message) tuples for violations
        """
        violations = []

        # Your validation logic here
        if some_condition:
            violations.append(("$.credentialSubject.field", "Description of the issue"))

        return violations
```

### 4. Install and Test

```
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .

# Your plugin is now automatically discovered!
python -c "from dppvalidator.plugins import list_available_plugins; print(list_available_plugins())"
```

## Validator Protocol

All validators must implement the `SemanticRule` protocol:

### Required Attributes

| Attribute     | Type                                  | Description                           |
| ------------- | ------------------------------------- | ------------------------------------- |
| `rule_id`     | `str`                                 | Unique identifier (e.g., `"MY_RULE"`) |
| `description` | `str`                                 | Human-readable description            |
| `severity`    | `Literal["error", "warning", "info"]` | Default severity level                |

### Required Methods

```python
def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
    """
    Check the passport for violations.

    Args:
        passport: The parsed DigitalProductPassport model

    Returns:
        List of tuples: (json_path, error_message)
        Return empty list if no violations.
    """
```

### Example Validator

```python
from typing import Literal


class ProductImageRequiredRule:
    """Require products to have an image URL."""

    rule_id = "PLG_IMG"
    description = "Products should have an image for consumer identification"
    severity: Literal["error", "warning", "info"] = "warning"

    def check(self, passport) -> list[tuple[str, str]]:
        violations = []

        if not passport.credential_subject:
            return violations

        product = passport.credential_subject.product
        if product and not product.product_image:
            violations.append(
                (
                    "$.credentialSubject.product.productImage",
                    "Product image is recommended for consumer identification",
                )
            )

        return violations
```

## Exporter Protocol

Exporters should provide these methods:

```python
class CustomExporter:
    """Export DPP to custom format."""

    def export(self, passport: DigitalProductPassport) -> str:
        """Export to string format."""
        ...

    def export_to_file(self, passport: DigitalProductPassport, path: Path) -> None:
        """Export to file."""
        ...
```

### Example Exporter

```python
import xml.etree.ElementTree as ET
from pathlib import Path


class XMLExporter:
    """Export DPP to XML format."""

    def export(self, passport) -> str:
        root = ET.Element("DigitalProductPassport")

        id_elem = ET.SubElement(root, "id")
        id_elem.text = str(passport.id)

        issuer = ET.SubElement(root, "issuer")
        issuer_name = ET.SubElement(issuer, "name")
        issuer_name.text = passport.issuer.name

        return ET.tostring(root, encoding="unicode")

    def export_to_file(self, passport, path: Path | str) -> None:
        content = self.export(passport)
        Path(path).write_text(content, encoding="utf-8")
```

## Entry Point Groups

| Group                     | Description             |
| ------------------------- | ----------------------- |
| `dppvalidator.validators` | Custom validation rules |
| `dppvalidator.exporters`  | Custom export formats   |

## Manual Registration

For testing or special cases, register plugins manually:

```python
from dppvalidator.plugins import PluginRegistry

registry = PluginRegistry(auto_discover=False)
registry.register_validator("my_rule", MyCustomRule())
registry.register_exporter("xml", XMLExporter())

# Use the registry
errors = registry.run_all_validators(passport)
```

## Using the Default Registry

```python
from dppvalidator.plugins import get_default_registry

# Get singleton registry (auto-discovers plugins)
registry = get_default_registry()

# List available plugins
print(registry.validator_names)
print(registry.exporter_names)

# Run all plugin validators
errors = registry.run_all_validators(passport)
```

## Error Handling

The plugin system handles errors gracefully:

- Failed plugin loads are logged as warnings
- Plugin exceptions during validation are caught and reported
- Other plugins continue to run even if one fails

## Best Practices

1. **Unique Rule IDs** - Use a prefix like `PLG_` or your package name
1. **Clear Messages** - Provide actionable error messages
1. **Appropriate Severity** - Use `error` for blockers, `warning` for recommendations, `info` for suggestions
1. **JSON Paths** - Use valid JSON path syntax (e.g., `$.credentialSubject.field`)
1. **Null Safety** - Always check for `None` values before accessing nested fields
1. **Testing** - Test your validators with various passport configurations

## Example Plugin Package

See the complete example in `examples/dppvalidator_example_plugin/` for:

- Full `pyproject.toml` configuration
- Two example validators (BrandNameRule, MinMaterialsRule)
- Example CSV exporter
- README with usage instructions

## Troubleshooting

### Plugin Not Discovered

1. Ensure the package is installed (`uv pip install -e .` or `pip install -e .`)
1. Check entry point syntax in `pyproject.toml`
1. Verify the module path is correct
1. Check for import errors in your plugin code

### Plugin Errors

Enable debug logging to see plugin discovery:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Testing Without Installation

```python
from dppvalidator.plugins import PluginRegistry
from my_plugin.validators import MyRule

registry = PluginRegistry(auto_discover=False)
registry.register_validator("test", MyRule())
```
