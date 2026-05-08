---
description: Maintain code coherence, remove inconsistencies, improve readability (DRY, SOLID, SOTA)
allowed-tools: Bash(uv run ruff *) Bash(uv run ty *) Bash(uv run pytest *) Bash(uv run coverage *)
---

# /code-health

## 1. Static analysis

```!
uv run ruff check src/dppvalidator/ tests/ --fix
```

```!
uv run ruff format src/dppvalidator/ tests/
```

## 2. Type check

```!
uv run ty check src/dppvalidator/
```

## 3. Review checklist

### DRY (don't repeat yourself)

- [ ] No duplicate code blocks across modules.
- [ ] Shared logic extracted to utility functions.
- [ ] Constants defined centrally (e.g. in config or constants module).
- [ ] Common test fixtures in `tests/conftest.py`.

### SOLID principles

- [ ] **S**ingle responsibility: each validator/model has one purpose.
- [ ] **O**pen/closed: new validators extend patterns, don't modify base.
- [ ] **L**iskov substitution: subclasses honor parent contracts.
- [ ] **I**nterface segregation: no forced unused dependencies.
- [ ] **D**ependency inversion: use protocols/ABCs for abstractions.

### Consistency (codebase-specific)

- [ ] All modules use Pydantic v2 patterns.
- [ ] All public functions have type hints (ty enforced).
- [ ] All models inherit from appropriate Pydantic base.
- [ ] Import order: stdlib → third-party → local.

### Readability

- [ ] Function names describe what they do.
- [ ] Variables have meaningful names (no `x`, `temp`, `data`).
- [ ] Complex logic has inline comments explaining *why*.
- [ ] Max function length ~50 lines; split if larger.

## 4. Find code smells

```!
uv run ruff check src/dppvalidator/ --select=C901,PLR0912,PLR0915 --statistics
```

This checks for:

- `C901`: complex functions (cyclomatic complexity)
- `PLR0912`: too many branches
- `PLR0915`: too many statements

## 5. Test coverage

```!
uv run pytest tests/ --cov=src/dppvalidator --cov-report=term-missing --cov-fail-under=80
```

## 6. Final verification

```!
uv run pytest tests/ -q
```

______________________________________________________________________

## Quick reference: common refactorings

| Smell               | Refactoring                                   |
| ------------------- | --------------------------------------------- |
| Duplicate code      | Extract to shared utility module              |
| Long function       | Split into smaller functions                  |
| God class           | Decompose into focused classes                |
| Primitive obsession | Create Pydantic models in `models/`           |
| Long parameter list | Use Pydantic config or dataclass              |
| Magic strings       | Use `Literal` types or `Enum`                 |
| Nested validation   | Use Pydantic validators and `model_validator` |
| Repeated schemas    | Extract base models, use inheritance          |
