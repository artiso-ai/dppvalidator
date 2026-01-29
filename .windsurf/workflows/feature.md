---
description: Start a new feature branch following gitflow
---

1. Ensure develop is up to date:
   `git checkout develop && git pull origin develop`

2. Create feature branch (replace FEATURE_NAME):
   `git checkout -b feature/FEATURE_NAME`

3. **Implement the feature** - write code and tests

4. Run tests:
   // turbo
   `uv run pytest tests/ -v`

5. Run lint:
   // turbo
   `uv run ruff check src/ tests/`

6. Commit changes:
   `git add . && git commit -m "feat: FEATURE_DESCRIPTION"`

7. Push feature branch:
   `git push -u origin feature/FEATURE_NAME`

8. Create PR to develop branch via GitHub

**Commit convention**: Use conventional commits (feat:, fix:, docs:, chore:, refactor:, test:)
