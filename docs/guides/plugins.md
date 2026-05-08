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

## Writing a version-aware rule

UNTP DPP introduced a wire-shape change in **v0.7.0**: the
`ProductPassport` envelope is gone, so `credentialSubject` is now a
`Product` directly (no inner `.product` attribute). A rule written
against the v0.6 shape will silently no-op on v0.7 payloads — and
vice-versa. Plugins that target a specific version should declare
which shape they target.

The contract: set
`applies_to_versions: tuple[str, ...] = ("0.7.0",)` on the rule
class, and **duck on attribute presence** so the rule no-ops
cleanly when the wrong-version passport flows through.

```python
# brand_name_v07.py
from typing import Any, Literal


class BrandNameRuleV07:
    """v0.7-shape brand-name check.

    Reads ``passport.credential_subject.name`` directly (v0.7 has
    Product as credentialSubject) and accepts a brandOwner
    relatedParty as an alternative attribution.
    """

    rule_id: str = "SEM_BRAND_V07"
    description: str = "Products should attribute brand identity (v0.7)."
    severity: Literal["error", "warning", "info"] = "warning"

    # Tells the engine's per-version rule dispatch which version this
    # rule targets. If omitted, the rule runs for every version.
    applies_to_versions: tuple[str, ...] = ("0.7.0",)

    def check(self, passport: Any) -> list[tuple[str, str]]:
        cs = getattr(passport, "credential_subject", None)
        if cs is None or hasattr(cs, "product"):
            # v0.6 shape (or no cs) — skip cleanly.
            return []

        if getattr(cs, "name", None):
            return []

        # Fall back to a brandOwner relatedParty.
        for entry in getattr(cs, "related_party", None) or []:
            role = getattr(entry, "role", None)
            if getattr(role, "value", role) == "brandOwner":
                return []

        return [
            (
                "$.credentialSubject",
                "Product should attribute brand identity via Product.name "
                "or a relatedParty with role 'brandOwner'.",
            )
        ]
```

Register it as a separate entry point alongside the v0.6 sibling:

```toml
[project.entry-points."dppvalidator.validators"]
brand_name      = "my_package.brand_name:BrandNameRule"        # v0.6
brand_name_v07  = "my_package.brand_name_v07:BrandNameRuleV07" # v0.7
```

Both rules co-exist in the registry; the engine picks the one
whose `applies_to_versions` matches the detected payload version.
A worked v0.6/v0.7 sibling pair lives in the
[`dppvalidator-example-plugin`](https://github.com/artiso-ai/dppvalidator/tree/main/examples/dppvalidator_example_plugin)
under `examples/`, with integration tests in
[`tests/integration/test_example_plugin.py`](https://github.com/artiso-ai/dppvalidator/blob/main/tests/integration/test_example_plugin.py).

### Public-API stability for plugins

The plugin's import path
(`from dppvalidator.models.passport import DigitalProductPassport`)
resolves to the **v0.6** model via the top-level shim, even after
the Phase 3 model relocation. v0.7 plugins should import from
`dppvalidator.models.v0_7.envelope` explicitly. The CI test
`tests/integration/test_example_plugin.py` pins this contract.

## Next Steps

- [API Reference](../reference/api/plugins.md) — Plugin Registry API
- [UNTP DPP versions](../concepts/untp-versions.md) — version detection
  and the coexistence matrix.
- [Validation Guide](validation.md) — Understanding validation layers
