---
description: Review and address PR comments
---

1. Fetch and checkout the PR branch:
   `gh pr checkout [PR_NUMBER]`

2. Get PR comments:
   `gh pr view [PR_NUMBER] --comments`

3. Run tests to ensure current state:
   // turbo
   `uv run pytest tests/ -v`

4. For EACH comment:
   a. Read and understand the feedback
   b. Implement the requested change
   c. Run relevant tests
   d. Commit with reference: `git commit -m "fix: address PR feedback - DESCRIPTION"`

5. Push changes:
   `git push`

6. Reply to comments on GitHub indicating addressed items

**Note**: Use `gh pr comment [PR_NUMBER] --body "Addressed in latest push"` to notify reviewers.
