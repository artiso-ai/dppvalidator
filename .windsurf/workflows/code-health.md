---
description: Maintain code coherence, remove inconsistencies, improve readability (DRY, SOLID, SOTA)
---

## 1. Run Static Analysis

// turbo
`uv run ruff check src/dppvalidator/ tests/ --fix`

// turbo
`uv run ruff format src/dppvalidator/ tests/`

## 2. Type Check

// turbo
`uv run ty check src/dppvalidator/`

## 3. Review Checklist

Manually verify the following:

### DRY (Don't Repeat Yourself)

- [ ] No duplicate code blocks across modules
- [ ] Shared logic extracted to utility functions
- [ ] Constants defined centrally (e.g., in config or constants module)
- [ ] Common test fixtures in `tests/conftest.py`

### SOLID Principles

- [ ] **S**ingle Responsibility: Each validator/model has one purpose
- [ ] **O**pen/Closed: New validators extend patterns, don't modify base
- [ ] **L**iskov Substitution: Subclasses honor parent contracts
- [ ] **I**nterface Segregation: No forced unused dependencies
- [ ] **D**ependency Inversion: Use protocols/ABCs for abstractions

### Consistency (Codebase-Specific)

- [ ] All modules use Pydantic v2 patterns
- [ ] All public functions have type hints (ty enforced)
- [ ] All models inherit from appropriate Pydantic base
- [ ] Import order: stdlib → third-party → local

### Readability

- [ ] Function names describe what they do
- [ ] Variables have meaningful names (no `x`, `temp`, `data`)
- [ ] Complex logic has inline comments explaining *why*
- [ ] Max function length ~50 lines; split if larger

## 4. Find Code Smells

// turbo
`uv run ruff check src/dppvalidator/ --select=C901,PLR0912,PLR0915 --statistics`

This checks for:
- `C901`: Complex functions (cyclomatic complexity)
- `PLR0912`: Too many branches
- `PLR0915`: Too many statements

## 5. Check Test Coverage

// turbo
`uv run pytest tests/ --cov=src/dppvalidator --cov-report=term-missing --cov-fail-under=80`

## 6. Final Verification

// turbo
`uv run pytest tests/ -q`

---

## Quick Reference: Common Refactorings

| Smell               | Refactoring                                           |
| ------------------- | ----------------------------------------------------- |
| Duplicate code      | Extract to shared utility module                      |
| Long function       | Split into smaller functions                          |
| God class           | Decompose into focused classes                        |
| Primitive obsession | Create Pydantic models in `models/`                   |
| Long parameter list | Use Pydantic config or dataclass                      |
| Magic strings       | Use `Literal` types or `Enum`                         |
| Nested validation   | Use Pydantic validators and `model_validator`         |
| Repeated schemas    | Extract base models, use inheritance                  |
