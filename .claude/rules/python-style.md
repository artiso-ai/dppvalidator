______________________________________________________________________

paths:

- "\*\*/\*.py"

______________________________________________________________________

# Python Code Style

## Coding standards

- Use type hints for all function parameters and return values.
- Follow PEP 8 naming: `snake_case` for functions/variables, `PascalCase` for classes.
- Use Pydantic v2 models for data validation.
- Prefer early returns to reduce nesting.
- Keep functions focused and under ~50 lines.
- Use dataclasses or Pydantic models instead of plain dicts for structured data.

## Imports

- Group imports: stdlib, third-party, local (separated by blank lines).
- Use absolute imports over relative imports.
- Import specific items rather than entire modules when practical.

## Error handling

- Use specific exception types, not bare `except:`.
- Validate input at boundaries using Pydantic.
- Raise descriptive exceptions with context.

## Testing companion

- Each module should have corresponding tests in `tests/`.
- Use pytest fixtures for shared test setup.
- Test both happy path and error cases.
- Use parametrized tests for multiple input variations.
