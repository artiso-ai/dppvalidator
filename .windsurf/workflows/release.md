---
description: Create a new release following gitflow and publish to PyPI
---

1. Ensure you're on develop branch:
   `git checkout develop && git pull origin develop`

2. Run full test suite:
   // turbo
   `uv run pytest tests/ -v`

3. Bump version (patch/minor/major):
   `uv version patch`  # or: uv version minor | uv version major

4. Create release branch:
   `git checkout -b release/v$(uv version --short)`

5. Update CHANGELOG.md with release notes

6. Commit version bump:
   `git add pyproject.toml CHANGELOG.md && git commit -m "chore: bump version to $(uv version --short)"`

7. Merge to main:
   `git checkout main && git pull && git merge --no-ff release/v$(uv version --short)`

8. Tag the release:
   `git tag -a v$(uv version --short) -m "Release v$(uv version --short)"`

9. Merge back to develop:
   `git checkout develop && git merge --no-ff main`

10. Push all branches and tags:
    `git push origin main develop --tags`

11. Build and publish to PyPI:
    // turbo
    `uv build && uv publish`

**Note**: Ensure PYPI_API_TOKEN is configured in environment or `.pypirc`.
