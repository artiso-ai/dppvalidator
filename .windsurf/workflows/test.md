---
description: Run test suite
---

1. Run unit tests with coverage:
   // turbo
   `uv run pytest tests/ -v --cov=src/dppvalidator --cov-report=term-missing`

2. Run integration tests (if present):
   // turbo
   `uv run pytest tests/integration/ -v --ignore-glob='**/test_*.py' 2>/dev/null || echo "No integration tests found"`

**On failure**: Check test output for specific failures. Use `uv run pytest tests/path/to/test.py::test_name -v` to run specific tests.
