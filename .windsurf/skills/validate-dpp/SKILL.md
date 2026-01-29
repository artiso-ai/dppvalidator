---
name: validate-dpp
description: Guides implementation of DPP validation features following ESPR/CIRPASS standards
---

## Overview

This skill helps implement Digital Product Passport validation features following EU ESPR regulations and CIRPASS ontologies.

## Implementation Steps

### 1. Define Pydantic Model

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional

class YourModel(BaseModel):
    field_name: str = Field(..., description="Description for docs")

    @field_validator('field_name')
    @classmethod
    def validate_field(cls, v: str) -> str:
        # validation logic
        return v
```

### 2. Add to Validation Engine

- Add model to `src/dppvalidator/models/`
- Register in validation engine
- Add JSON-LD export support

### 3. Write Tests

```python
import pytest
from dppvalidator.models import YourModel

def test_valid_model():
    model = YourModel(field_name="value")
    assert model.field_name == "value"

def test_invalid_model():
    with pytest.raises(ValueError):
        YourModel(field_name="invalid")
```

## Reference Standards

- **ISO 2076**: Textile fiber codes
- **ISO 3166-1**: Country codes
- **GS1 GTIN-13**: Product identifiers
- **JSON-LD**: Linked data format
