______________________________________________________________________

paths:

- "tests/\*\*/\*.py"
- "\*\*/test\_\*.py"
- "\*\*/\*\_test.py"

______________________________________________________________________

# Testing Guidelines

## Coverage requirements

- Target **≥95% code coverage** for all modules.
- Protocol classes (`typing.Protocol`) may be excluded from coverage as they cannot be tested directly.
- Use `# pragma: no cover` sparingly and only for genuinely untestable code.

## Testing philosophy

- Test **intended behavior**, not literal implementation details.
- Tests should validate what the code is supposed to do, not how it does it.
- Avoid brittle tests that break when refactoring internals.
- Focus on public API contracts and observable outcomes.

## Test types

- **Unit tests**: isolate individual functions/classes, mock external dependencies.
- **Integration tests**: verify components work together correctly.
- **Property-based tests**: use Hypothesis for fuzz testing with generated inputs.
- **Fixtures**: use pytest fixtures for reusable test setup and teardown.

## pytest best practices

- Organize fixtures in `conftest.py` files at appropriate directory levels.
- Use `@pytest.fixture` with appropriate scope (function, class, module, session).
- Use `@pytest.mark.parametrize` for testing multiple inputs.
- Use `@pytest.mark.integration` to tag integration tests.
- Use Hypothesis `@given` decorators for property-based testing.

## Example structure

```python
import pytest
from hypothesis import given, strategies as st


@pytest.fixture
def sample_data():
    """Reusable test fixture."""
    return {...}


def test_behavior_not_implementation(sample_data):
    """Test what it does, not how."""
    result = function_under_test(sample_data)
    assert result.is_valid  # behavior check


@given(st.text(), st.integers())
def test_property_based(text, number):
    """Fuzz test with generated inputs."""
    result = process(text, number)
    assert invariant_holds(result)
```
