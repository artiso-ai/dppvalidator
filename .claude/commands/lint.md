---
description: Run linting and type checking with ruff and ty
allowed-tools: Bash(uv run ruff *) Bash(uv run ty *)
---

# /lint

Run the project's static checks. On any failure, run `/fix-lint` to auto-fix what can be fixed and report the rest.

```!
uv run ruff check src/ tests/
```

```!
uv run ruff format --check src/ tests/
```

```!
uv run ty check src/
```
