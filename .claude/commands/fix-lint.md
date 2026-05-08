---
description: Auto-fix linting and formatting issues with ruff
allowed-tools: Bash(uv run ruff *)
---

# /fix-lint

Auto-fix what can be fixed, then re-verify. Commit only after issues are resolved.

```!
uv run ruff check --fix src/ tests/
```

```!
uv run ruff format src/ tests/
```

```!
uv run ruff check src/ tests/
```
