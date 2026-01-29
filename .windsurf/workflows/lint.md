---
description: Run linting and type checking with ruff and ty
---

1. Run ruff linter:
   // turbo
   `uv run ruff check src/ tests/`

2. Run ruff formatter check:
   // turbo
   `uv run ruff format --check src/ tests/`

3. Run ty type checker:
   // turbo
   `uv run ty check src/`

**On failure**: Run `/fix-lint` to auto-fix issues.
