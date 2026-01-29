---
name: pypi-publish
description: Guides publishing dppvalidator to PyPI with proper versioning
---

## Pre-Publishing Checklist

1. **All tests pass**: `uv run pytest tests/ -v`
2. **Lint clean**: `uv run ruff check src/`
3. **Type check clean**: `uv run ty check src/`
4. **Version bumped**: Check `pyproject.toml`
5. **CHANGELOG updated**: Document changes

## Version Bump Commands

```
# Patch release (0.1.0 -> 0.1.1)
uv version patch

# Minor release (0.1.0 -> 0.2.0)
uv version minor

# Major release (0.1.0 -> 1.0.0)
uv version major
```

## Build and Publish

```
# Build distribution
uv build

# Publish to TestPyPI first
uv publish --repository testpypi

# Verify installation from TestPyPI (using uv)
uv pip install --index-url https://test.pypi.org/simple/ dppvalidator

# Or using pip
# pip install --index-url https://test.pypi.org/simple/ dppvalidator

# Publish to PyPI
uv publish
```

## Authentication

Set `PYPI_API_TOKEN` environment variable or configure `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN
```

## Post-Publish

1. Create GitHub release with tag
2. Update documentation
3. Announce release
