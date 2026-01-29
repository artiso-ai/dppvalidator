---
trigger: glob
globs: ["tests/**/*.py", "**/test_*.py", "**/*_test.py"]
---

# Testing Guidelines

<coverage_requirements>

- Target **≥95% code coverage** for all modules
- Protocol classes (typing.Protocol) may be excluded from coverage as they cannot be tested directly
- Use `# pragma: no cover` sparingly and only for genuinely untestable code

</coverage_requirements>

<testing_philosophy>

- Test **intended behavior**, not literal implementation details
- Tests should validate what the code is supposed to do, not how it does it
- Avoid brittle tests that break when refactoring internals
- Focus on public API contracts and observable outcomes

</testing_philosophy>

<test_types>

- **Unit tests**: Isolate individual functions/classes, mock external dependencies
- **Integration tests**: Verify components work together correctly
- **Property-based tests**: Use Hypothesis for fuzz testing with generated inputs
- **Fixtures**: Use pytest fixtures for reusable test setup and teardown

</test_types>

<pytest_best_practices>

- Organize fixtures in `conftest.py` files at appropriate directory levels
- Use `@pytest.fixture` with appropriate scope (function, class, module, session)
- Use `@pytest.mark.parametrize` for testing multiple inputs
- Use `@pytest.mark.integration` to tag integration tests
- Use Hypothesis `@given` decorators for property-based testing

</pytest_best_practices>

<example_structure>

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

</example_structure>
