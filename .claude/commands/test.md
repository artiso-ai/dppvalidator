______________________________________________________________________

## description: Run the test suite with coverage analysis and quality checks argument-hint: "[pytest args]" allowed-tools: Bash(uv run pytest \*) Bash(uv run coverage \*) Bash(uv run mutmut \*)

# /test

Tests must validate **library behavior**, not implementation details:

- Avoid mocking internal components unless testing integration boundaries.
- Test real Pydantic validation, not mocked validators.
- Verify actual JSON-LD output, not mocked exporters.
- Use fixtures with realistic DPP data.
- Coverage target: **95%** (protocols excluded via `pyproject.toml`).

## Quick test (default)

```!
uv run pytest tests/ -v --cov=src/dppvalidator --cov-report=term-missing --cov-fail-under=95 $ARGUMENTS
```

## Comprehensive test suite

```!
uv run pytest tests/unit/ -v --cov=src/dppvalidator --cov-report=term-missing
```

```!
uv run pytest tests/property/ -v --hypothesis-show-statistics
```

```!
uv run pytest tests/fuzz/ -v
```

```!
uv run pytest tests/integration/ -v 2>/dev/null || echo "No integration tests yet"
```

## Coverage analysis

```!
uv run pytest tests/ --cov=src/dppvalidator --cov-report=html --cov-report=term-missing
```

```!
uv run coverage report --show-missing --skip-covered
```

## Mutation testing (verify test quality)

```bash
uv run mutmut run --paths-to-mutate=src/dppvalidator --tests-dir=tests
uv run mutmut results
```

## Debugging specific tests

```bash
# single test file
uv run pytest tests/unit/test_<module>.py -v

# specific test function
uv run pytest tests/unit/test_<module>.py::test_<name> -v -s

# tests matching a pattern
uv run pytest tests/ -v -k "<pattern>"
```

## Test quality checklist

- [ ] Tests validate **behavior**, not mocked internals
- [ ] Edge cases covered (empty inputs, invalid data, boundary values, etc.)
- [ ] Error messages are meaningful and tested
- [ ] Property tests cover model invariants
- [ ] Fixtures use realistic DPP data from `tests/fixtures/`
- [ ] No over-mocking (real Pydantic validation, real exports)

**On failure**:

- Check test output for specific failures.
- Use `uv run pytest tests/path/to/test.py::test_name -v -s` to debug.
- Run `/lint` to check for code issues.
- Review coverage gaps with `uv run coverage html && open htmlcov/index.html`.
