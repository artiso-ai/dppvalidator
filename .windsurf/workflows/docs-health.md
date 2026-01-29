---
description: Check documentation consistency and ensure README.md and mkdocs are up-to-date with the codebase
---

## 1. Verify mkdocs Navigation Files Exist

Check all files referenced in `mkdocs.yml` nav exist:

// turbo
1. `for f in $(grep -oE '[a-z/-]+\.md' mkdocs.yml); do [ -f "docs/$f" ] || echo "MISSING: docs/$f"; done`

## 2. Check Core Documentation Consistency

2. Compare key information across documentation sources for alignment:

| Source            | Check                                                |
| ----------------- | ---------------------------------------------------- |
| `README.md`       | Accurate project description, install instructions   |
| `docs/index.md`   | Matches README features and quick start              |
| `AGENTS.md`       | Tech stack reflects current dependencies             |
| `pyproject.toml`  | Version, description matches docs                    |

// turbo
3. `head -20 README.md`

// turbo
4. `grep -E "^(name|version|description)" pyproject.toml | head -5`

## 3. Validate Public API Documentation

5. Check that public exports are documented in API reference:

// turbo
`grep -r "^from dppvalidator" docs/reference/ 2>/dev/null || echo "Check API docs manually"`

// turbo
6. `grep -E "^(class|def) " src/dppvalidator/__init__.py 2>/dev/null | head -10`

## 4. Check Code Examples

7. Verify code examples in docs use current API patterns:
   - Import paths match actual module structure
   - Class/function names exist in codebase
   - Examples use Pydantic v2 syntax (not v1)

// turbo
8. `grep -rh "from dppvalidator" docs/*.md docs/**/*.md 2>/dev/null | sort -u | head -10`

// turbo
9. `grep -rh "import dppvalidator" docs/*.md docs/**/*.md 2>/dev/null | sort -u | head -5`

## 5. Version Consistency

// turbo
10. `grep -E "version|0\.[0-9]" pyproject.toml docs/index.md mkdocs.yml CHANGELOG.md 2>/dev/null | head -15`

11. Verify version numbers are consistent across:
    - [ ] `pyproject.toml` → package version
    - [ ] `docs/index.md` → schema version references
    - [ ] `CHANGELOG.md` → latest release matches pyproject

## 6. Changelog Sync

// turbo
12. `head -30 CHANGELOG.md`

// turbo
13. `[ -f docs/changelog.md ] && head -5 docs/changelog.md || echo "docs/changelog.md missing"`

14. Ensure `docs/changelog.md` references or includes root `CHANGELOG.md`

## 7. Links Validation

15. Check for broken internal links in documentation:

// turbo
`grep -rohE '\[.*\]\([^)]+\.md[^)]*\)' docs/*.md docs/**/*.md 2>/dev/null | head -20`

16. Verify external links (manual spot check):
    - PyPI badge links
    - GitHub repo links
    - UNTP/ESPR reference links

## 8. Schema Reference Accuracy

17. Verify schema version references match bundled schemas:

// turbo
`ls -la src/dppvalidator/schemas/*.json 2>/dev/null || echo "Check schema location"`

// turbo
18. `grep -r "0\\.6\\." docs/ src/ 2>/dev/null | head -10`

## 9. Report & Fix

19. Document any inconsistencies found:
    - [ ] Missing nav files → Create placeholder or remove from nav
    - [ ] Stale code examples → Update to current API
    - [ ] Version mismatch → Sync versions
    - [ ] Broken links → Fix paths
    - [ ] Missing API docs → Document public exports

20. If changes made, commit:
    `git add README.md docs/ CHANGELOG.md && git commit -m "docs: sync documentation with codebase"`

**Run this workflow before releases and after major API changes.**
