---
description: Review and address PR comments
argument-hint: "<pr-number>"
disable-model-invocation: true
allowed-tools: Bash(gh *) Bash(git *) Bash(uv run pytest *)
---

# /pr-review

Address feedback on PR `#$ARGUMENTS`.

1. Fetch and check out the PR branch:

   ```bash
   gh pr checkout $ARGUMENTS
   ```

1. Get PR comments:

   ```bash
   gh pr view $ARGUMENTS --comments
   ```

1. Run tests to ensure current state is green:

   ```bash
   uv run pytest tests/ -v
   ```

1. For **each comment**:

   1. Read and understand the feedback.
   1. Implement the requested change.
   1. Run relevant tests.
   1. Commit with reference: `git commit -m "fix: address PR feedback - <description>"`.

1. Push changes:

   ```bash
   git push
   ```

1. Reply to comments on GitHub indicating addressed items.

Use `gh pr comment $ARGUMENTS --body "Addressed in latest push"` to notify reviewers.
