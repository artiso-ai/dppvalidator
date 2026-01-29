# Validation Guide

dppvalidator uses a three-layer validation approach to ensure Digital Product Passports are valid and meaningful.

## Three-Layer Validation

### Layer 1: Schema Validation

The first layer validates the JSON structure against the UNTP DPP JSON Schema.

```python
from dppvalidator.validators import ValidationEngine

engine = ValidationEngine(layers=["schema"])
result = engine.validate(data)
```

**What it checks:**

- Required fields are present
- Field types are correct
- String formats (URIs, dates)
- Enum values

### Layer 2: Model Validation

The second layer validates data against Pydantic models, providing stricter type checking and coercion.

```python
engine = ValidationEngine(layers=["model"])
result = engine.validate(data)
```

**What it checks:**

- Pydantic model constraints
- URL validation
- Date parsing
- Custom validators

### Layer 3: Semantic Validation

The third layer checks business rules and cross-field relationships.

```python
engine = ValidationEngine(layers=["semantic"])
result = engine.validate(data)
```

**What it checks:**

- Vocabulary values (country codes, unit codes)
- Date relationships (valid_from < valid_until)
- Identifier formats
- Cross-reference consistency

## Using All Layers

By default, all layers are enabled:

```python
engine = ValidationEngine()  # All layers enabled
result = engine.validate(data)

# Or explicitly:
engine = ValidationEngine(layers=["schema", "model", "semantic"])
```

## Validation Results

```python
result = engine.validate(data)

# Check if valid
if result.valid:
    print("Passport is valid!")

# Access errors
for error in result.errors:
    print(f"[{error.code}] {error.path}: {error.message}")

# Access warnings
for warning in result.warnings:
    print(f"Warning: {warning.message}")

# Get validation time
print(f"Validated in {result.validation_time_ms:.2f}ms")
```

## Error Codes

| Code   | Layer    | Description               |
| ------ | -------- | ------------------------- |
| SCH001 | Schema   | Required field missing    |
| SCH002 | Schema   | Invalid type              |
| MOD001 | Model    | Pydantic validation error |
| SEM001 | Semantic | Invalid vocabulary value  |
| SEM002 | Semantic | Invalid date relationship |

## Strict Mode

Enable strict mode for additional schema checks:

```python
engine = ValidationEngine(strict_mode=True)
```

## Next Steps

- [JSON-LD Export](jsonld.md) — Export validated passports
- [API Reference](../reference/api/validators.md) — Full ValidationEngine API
