---
description: Auto-fix linting and formatting issues
---

1. Fix ruff lint issues:
   // turbo
   `uv run ruff check --fix src/ tests/`

2. Format code with ruff:
   // turbo
   `uv run ruff format src/ tests/`

3. Re-run lint to verify:
   // turbo
   `uv run ruff check src/ tests/`

**Post-fix**: Commit the changes if all issues are resolved.
