# Code Style

dppvalidator follows consistent coding standards enforced by automated tools.

## Tools

- **Ruff** — Linting and formatting
- **ty** — Type checking

## Running Checks

```
# Lint check
uv run ruff check .

# Format check
uv run ruff format --check .

# Type check
uv run ty check src/
```

## Auto-fix

```
# Fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Style Guidelines

### Imports

- Group imports: stdlib, third-party, local
- Use absolute imports
- Sort alphabetically within groups

```python
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from dppvalidator.logging import get_logger
```

### Type Hints

- Type hint all public functions
- Use `from __future__ import annotations` for forward references
- Use `typing.TYPE_CHECKING` for import-only types

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dppvalidator.models import DigitalProductPassport


def validate(passport: DigitalProductPassport) -> bool: ...
```

### Docstrings

Use Google-style docstrings:

```python
def validate(data: dict) -> ValidationResult:
    """Validate a Digital Product Passport.

    Args:
        data: The passport data as a dictionary.

    Returns:
        A ValidationResult with errors and warnings.

    Raises:
        ValueError: If data is not a valid dictionary.
    """
```

### Line Length

Maximum 100 characters per line.

### Naming Conventions

- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_CASE` for constants

## Pre-commit

Pre-commit hooks run automatically on commit:

```
uv run pre-commit install
```

## Next Steps

- [Testing](testing.md) — Writing tests
- [Development Setup](development-setup.md) — Environment setup
