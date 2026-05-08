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

This plugin provides three example validators:

- **BrandNameRule** (`SEM_BRAND`) - Validates that v0.6 products have a
  brand name. Reads `passport.credential_subject.product.name`.
- **BrandNameRuleV07** (`SEM_BRAND_V07`) - v0.7 variant; reads
  `passport.credential_subject.name` directly and accepts a
  `brandOwner` `relatedParty` as an alternative attribution.
- **MinMaterialsRule** (`SEM_MINMAT`) - Warns if v0.6 products have
  fewer than 2 materials declared.

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

## Writing a version-aware rule

UNTP DPP introduced a wire-shape change in v0.7.0: the
`ProductPassport` envelope is gone, so `credentialSubject` is now a
`Product` directly (no inner `.product` attribute). A rule written
against the v0.6 shape will silently no-op on v0.7 payloads — and
vice-versa. Phase 4 of the migration (`compat/upgrade_0_6_to_0_7.py`)
helps callers upgrade payloads, but plugins still need to declare
which shape they target.

This plugin demonstrates the version-aware-rule pattern with two
sibling rules:

- `BrandNameRule` (in `validators.py`) — v0.6 shape; reads
  `passport.credential_subject.product.name`.
- `BrandNameRuleV07` (in `brand_name_v07.py`) — v0.7 shape; reads
  `passport.credential_subject.name` directly and also accepts a
  `relatedParty` with `role="brandOwner"` as a brand attribution.

The v0.7 rule advertises an `applies_to_versions = ("0.7.0",)` class
attribute. The engine's per-version rule dispatch consults that
attribute to decide whether to run the rule for a given payload's
detected version. As an extra safety net, `BrandNameRuleV07.check()`
**ducks on attribute presence**: if a v0.6 passport ever flows
through (e.g. a caller bypassed dispatch), the rule no-ops cleanly
because `credential_subject.product` exists — it never raises.

### Recipe

To author a version-aware rule for a UNTP version `X.Y.Z`:

1. Create `your_rule_X_Y.py` in your plugin package.
1. Import the version-specific model:
   `from dppvalidator.models.vX_Y.envelope import DigitalProductPassport`.
1. Set `applies_to_versions = ("X.Y.Z",)` on the rule class.
1. In `check()`, validate the shape with `hasattr` / `getattr` on the
   passport before reading version-specific attributes; return `[]`
   when the shape doesn't match. This makes the rule co-exist
   gracefully with rules for other versions in the same registry.
1. Register the rule in `pyproject.toml` under
   `[project.entry-points."dppvalidator.validators"]` with a unique
   name (e.g. `brand_name_v07`).

## License

MIT
