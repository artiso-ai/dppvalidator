______________________________________________________________________

## name: pypi-publish description: Guide publishing dppvalidator to PyPI with proper versioning, smoke checks, and GitHub release. Use when the user asks to release, publish, or cut a version of the package. disable-model-invocation: true argument-hint: "[patch|minor|major]" allowed-tools: Bash(uv run pytest \*) Bash(uv run ruff \*) Bash(uv run ty \*) Bash(uv build \*) Bash(uv publish \*) Bash(uv version \*) Bash(git \*)

# pypi-publish

Publish a release of `dppvalidator` to PyPI. Bump type defaults to `patch` if `$ARGUMENTS` is empty.

## 1. Pre-publishing checklist

```bash
uv run pytest tests/ -v
uv run ruff check src/
uv run ty check src/
```

- [ ] All tests pass
- [ ] Lint clean
- [ ] Type check clean
- [ ] Version bumped in `pyproject.toml`
- [ ] `CHANGELOG.md` updated

## 2. Bump the version

```bash
# patch (0.1.0 -> 0.1.1)
uv version patch

# minor (0.1.0 -> 0.2.0)
uv version minor

# major (0.1.0 -> 1.0.0)
uv version major
```

## 3. Build and publish

```bash
# Build distribution
uv build

# Publish to TestPyPI first
uv publish --repository testpypi

# Verify install from TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ dppvalidator

# Publish to PyPI
uv publish
```

## 4. Authentication

Set `PYPI_API_TOKEN` in the environment or configure `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN
```

## 5. Post-publish

1. Create a GitHub release with the tag.
1. Update documentation.
1. Announce the release.

If anything fails after publish, use the `/hotfix` workflow for the PyPI release-failure runbook.
