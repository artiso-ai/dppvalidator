---
description: Create a hotfix for production following gitflow
---

1. Create hotfix branch from main:
   `git checkout main && git pull && git checkout -b hotfix/ISSUE_NAME`

2. **Fix the issue** - implement minimal fix

3. Add regression test for the fix

4. Run tests:
   // turbo
   `uv run pytest tests/ -v`

5. Bump patch version:
   `uv version patch`

6. Commit the fix:
   `git add . && git commit -m "fix: ISSUE_DESCRIPTION"`

7. Merge to main:
   `git checkout main && git merge --no-ff hotfix/ISSUE_NAME`

8. Tag the release:
   `git tag -a v$(uv version --short) -m "Hotfix v$(uv version --short)"`

9. Merge to develop:
   `git checkout develop && git merge --no-ff hotfix/ISSUE_NAME`

10. Push and publish:
    `git push origin main develop --tags`

11. Delete hotfix branch:
    `git branch -d hotfix/ISSUE_NAME`
