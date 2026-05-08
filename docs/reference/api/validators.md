# Validators API

Validation engine and result types for DPP validation.

## ValidationEngine

The main validation engine supporting seven-layer validation.

::: dppvalidator.validators.ValidationEngine
options:
show_source: false
members:
\- __init__
\- validate

## ValidationResult

Result of a validation operation.

::: dppvalidator.validators.ValidationResult
options:
show_source: false

## ValidationError

A single validation error or warning.

::: dppvalidator.validators.ValidationError
options:
show_source: false

## Usage Example

```python
from dppvalidator.validators import ValidationEngine, ValidationResult

# Create engine with specific layers
engine = ValidationEngine(layers=["model", "semantic"])

# Validate data
result = engine.validate(
    {
        "id": "https://example.com/dpp/001",
        "issuer": {"id": "https://example.com/issuer", "name": "Acme Corp"},
    }
)

# Check result
if result.valid:
    print("Passport is valid!")
else:
    for error in result.errors:
        print(f"[{error.code}] {error.path}: {error.message}")

# Access validation metadata
print(f"Schema version: {result.schema_version}")
print(f"Validation time: {result.validation_time_ms:.2f}ms")
```

## Validation Layers

The engine supports seven validation layers:

| Layer      | Description                              |
| ---------- | ---------------------------------------- |
| schema     | JSON Schema validation (Draft 2020-12)   |
| model      | Pydantic model validation                |
| semantic   | Business rule validation                 |
| jsonld     | JSON-LD context expansion and validation |
| vocabulary | External vocabulary validation           |
| plugin     | Custom plugin validators                 |
| signature  | Verifiable Credential signatures         |

## Performance Features

### Module-Level Schema Caching

Schemas are cached at the module level for better performance:

```python
from dppvalidator.schemas.loader import clear_schema_cache

# Clear cache if needed (e.g., after updating schema files)
clear_schema_cache()
```

### Plugin Registry Singleton

The plugin registry uses a singleton pattern:

```python
from dppvalidator.plugins.registry import get_default_registry, reset_default_registry

# Get the shared registry
registry = get_default_registry()

# Reset for testing
reset_default_registry()
```

## Error Codes

| Code   | Layer    | Description              |
| ------ | -------- | ------------------------ |
| SCH001 | schema   | Required field missing   |
| SCH002 | schema   | Invalid type             |
| MOD001 | model    | Model validation error   |
| JLD001 | jsonld   | Invalid context          |
| SEM001 | semantic | Invalid vocabulary value |
| SEM002 | semantic | Invalid date range       |
| SIG001 | crypto   | Invalid signature        |

> **Note:** This table shows common examples. See [Error Reference](../errors/) for the complete list of 70+ error codes.
