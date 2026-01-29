---
trigger: glob
globs: ["**/*.py"]
---

# Python Code Style

<coding_standards>
- Use type hints for all function parameters and return values
- Follow PEP 8 naming conventions (snake_case for functions/variables, PascalCase for classes)
- Use Pydantic v2 models for data validation
- Prefer early returns to reduce nesting
- Keep functions focused and under 50 lines
- Use dataclasses or Pydantic models instead of plain dicts for structured data
</coding_standards>

<imports>
- Group imports: stdlib, third-party, local (separated by blank lines)
- Use absolute imports over relative imports
- Import specific items rather than entire modules when practical
</imports>

<error_handling>
- Use specific exception types, not bare `except:`
- Validate input at boundaries using Pydantic
- Raise descriptive exceptions with context
</error_handling>

<testing>
- Each module should have corresponding tests in `tests/`
- Use pytest fixtures for shared test setup
- Test both happy path and error cases
- Use parametrized tests for multiple input variations
</testing>
