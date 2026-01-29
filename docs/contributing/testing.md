# Testing

dppvalidator maintains high test coverage with multiple testing strategies.

## Running Tests

```
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=dppvalidator

# Run specific test file
uv run pytest tests/unit/test_validators.py

# Run tests matching pattern
uv run pytest -k "test_validate"

# Verbose output
uv run pytest -v
```

## Test Structure

```text
tests/
├── unit/                  # Unit tests
│   ├── test_models.py
│   ├── test_validators.py
│   └── test_exporters.py
├── integration/           # Integration tests
├── property/              # Property-based tests
│   ├── test_property_models.py
│   └── test_property_validators.py
└── fuzz/                  # Fuzzing tests
    └── test_fuzz_engine.py
```

## Writing Tests

### Unit Tests

Test individual functions and classes in isolation:

```python
import pytest
from dppvalidator.validators import ValidationEngine


class TestValidationEngine:
    def test_valid_passport(self):
        engine = ValidationEngine()
        result = engine.validate(
            {
                "id": "https://example.com/dpp",
                "issuer": {"id": "https://issuer.com", "name": "Test"},
            }
        )
        assert result.valid

    def test_invalid_passport_missing_id(self):
        engine = ValidationEngine()
        result = engine.validate({"issuer": {"name": "Test"}})
        assert not result.valid
```

### Property-Based Tests

Use Hypothesis for fuzz testing with generated inputs:

```python
from hypothesis import given, strategies as st
from dppvalidator.validators import ValidationEngine


@given(st.binary())
def test_engine_never_crashes(data):
    engine = ValidationEngine()
    try:
        result = engine.validate(data.decode("utf-8", errors="replace"))
        assert result is not None
    except Exception:
        pass  # Exceptions are acceptable, crashes are not
```

### Fixtures

Use pytest fixtures for reusable setup:

```python
import pytest


@pytest.fixture
def valid_passport_data():
    return {
        "id": "https://example.com/dpp",
        "issuer": {"id": "https://issuer.com", "name": "Test"},
    }


def test_with_fixture(valid_passport_data):
    engine = ValidationEngine()
    result = engine.validate(valid_passport_data)
    assert result.valid
```

## Coverage

Target: **85%** coverage

```
# Generate coverage report
uv run pytest --cov=dppvalidator --cov-report=html

# View report
open htmlcov/index.html
```

## Benchmarks

Run performance benchmarks:

```
uv run python -m benchmarks.run_benchmarks
```

## Next Steps

- [Code Style](code-style.md) — Coding conventions
- [Development Setup](development-setup.md) — Environment setup
