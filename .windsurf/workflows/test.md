---
description: Run test suite with coverage analysis and quality checks
---

<test_philosophy>

Tests must validate **library behavior**, not implementation details:

- Avoid mocking internal components unless testing integration boundaries
- Test real Pydantic validation, not mocked validators
- Verify actual JSON-LD output, not mocked exporters
- Use fixtures with realistic DPP data
- Coverage target: **95%** (protocols excluded via pyproject.toml)

</test_philosophy>

## Quick Test (default)

1. Run full test suite with coverage:
   // turbo
   `uv run pytest tests/ -v --cov=src/dppvalidator --cov-report=term-missing --cov-fail-under=95`

## Comprehensive Test Suite

2. Run unit tests (behavior-focused):
   // turbo
   `uv run pytest tests/unit/ -v --cov=src/dppvalidator --cov-report=term-missing`

3. Run property-based tests (Hypothesis):
   // turbo
   `uv run pytest tests/property/ -v --hypothesis-show-statistics`

4. Run fuzz tests:
   // turbo
   `uv run pytest tests/fuzz/ -v`

5. Run integration tests:
   // turbo
   `uv run pytest tests/integration/ -v 2>/dev/null || echo "No integration tests yet"`

## Coverage Analysis

6. Generate HTML coverage report:
   // turbo
   `uv run pytest tests/ --cov=src/dppvalidator --cov-report=html --cov-report=term-missing`

7. View uncovered lines:
   // turbo
   `uv run coverage report --show-missing --skip-covered`

## Mutation Testing (verify test quality)

8. Run mutation tests to ensure tests catch real bugs:
   `uv run mutmut run --paths-to-mutate=src/dppvalidator --tests-dir=tests`

9. View mutation test results:
   // turbo
   `uv run mutmut results`

## Debugging Specific Tests

10. Run a single test file:
    `uv run pytest tests/unit/test_<module>.py -v`

11. Run a specific test function:
    `uv run pytest tests/unit/test_<module>.py::test_<name> -v -s`

12. Run tests matching a pattern:
    // turbo
    `uv run pytest tests/ -v -k "<pattern>"`

## Test Quality Checklist

Before considering tests complete, verify the following:

- [ ] Tests validate **behavior**, not mocked internals
- [ ] Edge cases covered (empty inputs, invalid data, boundary values, etc.)
- [ ] Error messages are meaningful and tested
- [ ] Property tests cover model invariants
- [ ] Fixtures use realistic DPP data from `tests/fixtures/`
- [ ] No over-mocking (real Pydantic validation, real exports)

**On failure**:
- Check test output for specific failures
- Use `uv run pytest tests/path/to/test.py::test_name -v -s` to debug
- Run `/lint` to check for code issues
- Review coverage gaps with `uv run coverage html && open htmlcov/index.html`
