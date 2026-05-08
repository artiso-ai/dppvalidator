---
description: Create a new release following gitflow and publish to PyPI
argument-hint: "[patch|minor|major]"
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(uv *) Bash(uv run *) Bash(gh *)
---

# /release

Cut a release. Bump kind defaults to `patch` if `$ARGUMENTS` is empty.

1. Ensure you're on `develop`:

   ```bash
   git checkout develop && git pull origin develop
   ```

1. Run linting:

   ```bash
   uv run ruff check src/ tests/
   ```

1. Run the full test suite:

   ```bash
   uv run pytest tests/ -v
   ```

1. Bump the version:

   ```bash
   uv version $ARGUMENTS  # patch | minor | major
   ```

1. Create the release branch:

   ```bash
   git checkout -b release/v$(uv version --short)
   ```

1. Update `CHANGELOG.md` with release notes.

1. Commit the version bump:

   ```bash
   git add pyproject.toml CHANGELOG.md \
     && git commit -m "chore: bump version to $(uv version --short)"
   ```

1. Merge to `main`:

   ```bash
   git checkout main && git pull \
     && git merge --no-ff release/v$(uv version --short)
   ```

1. Tag the release:

   ```bash
   git tag -a v$(uv version --short) -m "Release v$(uv version --short)"
   ```

1. Merge back to `develop`:

   ```bash
   git checkout develop && git merge --no-ff main
   ```

1. Push all branches and tags:

   ```bash
   git push origin main develop --tags
   ```

1. Build and publish to PyPI (the `/pypi-publish` skill walks through this in detail):

   ```bash
   uv build && uv publish
   ```

Ensure `PYPI_API_TOKEN` is configured in environment or `.pypirc`.
