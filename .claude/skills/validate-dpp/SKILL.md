______________________________________________________________________

## name: validate-dpp description: Implement Digital Product Passport validation features following EU ESPR/CIRPASS standards. Use when adding a new validator, Pydantic model for a DPP entity, JSON-LD export, or any work that touches src/dppvalidator/models/ or src/dppvalidator/validators/. allowed-tools: Read Edit Write Grep Glob Bash(uv run pytest \*) Bash(uv run ruff \*) Bash(uv run ty \*)

# validate-dpp

Implement DPP validation features following EU ESPR regulations and CIRPASS ontologies.

## Implementation steps

### 1. Define the Pydantic v2 model

```python
from pydantic import BaseModel, Field, field_validator, model_validator


class YourModel(BaseModel):
    field_name: str = Field(..., description="Description for docs")
    optional_field: str | None = None  # use X | None, not Optional[X]

    @field_validator("field_name")
    @classmethod
    def validate_field(cls, v: str) -> str:
        # validation logic
        return v
```

Anchor decisions to `.claude/rules/dpp-domain.md` (Pydantic v2 patterns, ESPR/CIRPASS reference data).

### 2. Wire it into the validation engine

- Add the model under `src/dppvalidator/models/`.
- Register it in the validation engine.
- Add JSON-LD export support (`@context`, `@type`).

### 3. Write tests

```python
import pytest
from dppvalidator.models import YourModel


def test_valid_model() -> None:
    model = YourModel(field_name="value")
    assert model.field_name == "value"


def test_invalid_model() -> None:
    with pytest.raises(ValueError):
        YourModel(field_name="invalid")
```

### 4. Verify

```bash
uv run pytest tests/ -q
uv run ruff check src/ tests/
uv run ty check src/
```

## Reference standards

- **ISO 2076**: textile fiber codes
- **ISO 3166-1**: country codes
- **GS1 GTIN-13**: product identifiers
- **JSON-LD**: linked data format
- **CIRPASS / UNECE**: DPP ontologies
