---
description: Check documentation consistency; ensure README.md and mkdocs are aligned with the codebase
allowed-tools: Bash(grep *) Bash(head *) Bash(ls *) Bash(test *) Bash(find *)
---

# /docs-health

## 1. Verify mkdocs nav files exist

```!
for f in $(grep -oE '[a-z/-]+\.md' mkdocs.yml); do [ -f "docs/$f" ] || echo "MISSING: docs/$f"; done
```

## 2. Core documentation consistency

Compare key information across documentation sources:

| Source           | Check                                              |
| ---------------- | -------------------------------------------------- |
| `README.md`      | Accurate project description, install instructions |
| `docs/index.md`  | Matches README features and quick start            |
| `AGENTS.md`      | Tech stack reflects current dependencies           |
| `pyproject.toml` | Version, description matches docs                  |

```!
head -20 README.md
```

```!
grep -E "^(name|version|description)" pyproject.toml | head -5
```

## 3. Validate public API documentation

```!
grep -r "^from dppvalidator" docs/reference/ 2>/dev/null || echo "Check API docs manually"
```

```!
grep -E "^(class|def) " src/dppvalidator/__init__.py 2>/dev/null | head -10
```

## 4. Check code examples

Verify code examples in docs use current API patterns:

- Import paths match actual module structure.
- Class/function names exist in codebase.
- Examples use Pydantic v2 syntax (not v1).

```!
grep -rh "from dppvalidator" docs/*.md docs/**/*.md 2>/dev/null | sort -u | head -10
```

```!
grep -rh "import dppvalidator" docs/*.md docs/**/*.md 2>/dev/null | sort -u | head -5
```

## 5. Version consistency

```!
grep -E "version|0\.[0-9]" pyproject.toml docs/index.md mkdocs.yml CHANGELOG.md 2>/dev/null | head -15
```

Verify version numbers are consistent across:

- [ ] `pyproject.toml` → package version
- [ ] `docs/index.md` → schema version references
- [ ] `CHANGELOG.md` → latest release matches `pyproject.toml`

## 6. Changelog sync

```!
head -30 CHANGELOG.md
```

```!
[ -f docs/changelog.md ] && head -5 docs/changelog.md || echo "docs/changelog.md missing"
```

Ensure `docs/changelog.md` references or includes root `CHANGELOG.md`.

## 7. Links validation

```!
grep -rohE '\[.*\]\([^)]+\.md[^)]*\)' docs/*.md docs/**/*.md 2>/dev/null | head -20
```

Spot-check external links manually:

- PyPI badge links
- GitHub repo links
- UNTP / ESPR reference links

## 8. Schema reference accuracy

```!
ls -la src/dppvalidator/schemas/*.json 2>/dev/null || echo "Check schema location"
```

```!
grep -r "0\.6\." docs/ src/ 2>/dev/null | head -10
```

## 9. Report and fix

Document any inconsistencies found:

- [ ] Missing nav files → create placeholder or remove from nav
- [ ] Stale code examples → update to current API
- [ ] Version mismatch → sync versions
- [ ] Broken links → fix paths
- [ ] Missing API docs → document public exports

If changes were made, commit:

```bash
git add README.md docs/ CHANGELOG.md \
  && git commit -m "docs: sync documentation with codebase"
```

Run this workflow before releases and after major API changes.
