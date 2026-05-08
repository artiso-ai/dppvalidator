---
description: Start a new feature branch following gitflow
argument-hint: "<feature-name>"
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(uv run pytest *) Bash(uv run ruff *) Bash(gh *)
---

# /feature

Create a feature branch for `$ARGUMENTS` and walk through the gitflow loop.

1. Ensure `develop` is up to date:

   ```bash
   git checkout develop && git pull origin develop
   ```

1. Create the feature branch:

   ```bash
   git checkout -b feature/$ARGUMENTS
   ```

1. **Implement the feature** — write code and tests.

1. Run tests:

   ```bash
   uv run pytest tests/ -v
   ```

1. Run lint:

   ```bash
   uv run ruff check src/ tests/
   ```

1. Commit changes (conventional commits — see `.claude/rules/commits.md`):

   ```bash
   git add . && git commit -m "feat: $ARGUMENTS"
   ```

1. Push the feature branch:

   ```bash
   git push -u origin feature/$ARGUMENTS
   ```

1. Open the PR against `develop` via `gh pr create` or the GitHub UI.
