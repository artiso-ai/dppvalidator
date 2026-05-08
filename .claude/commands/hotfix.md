---
description: Create a hotfix for production following gitflow; includes PyPI release-failure runbook
argument-hint: "<issue-name>"
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(uv *) Bash(uv run *) Bash(gh *)
---

# /hotfix

## Standard hotfix workflow

1. Create the hotfix branch from `main`:

   ```bash
   git checkout main && git pull && git checkout -b hotfix/$ARGUMENTS
   ```

1. **Fix the issue** — implement the minimal fix.

1. Add a regression test for the fix.

1. Run tests:

   ```bash
   uv run pytest tests/ -v
   ```

1. Bump the patch version:

   ```bash
   uv version patch
   ```

1. Commit the fix:

   ```bash
   git add . && git commit -m "fix: $ARGUMENTS"
   ```

1. Merge to `main`:

   ```bash
   git checkout main && git merge --no-ff hotfix/$ARGUMENTS
   ```

1. Tag the release:

   ```bash
   git tag -a v$(uv version --short) -m "Hotfix v$(uv version --short)"
   ```

1. Merge to `develop`:

   ```bash
   git checkout develop && git merge --no-ff hotfix/$ARGUMENTS
   ```

1. Push and publish:

   ```bash
   git push origin main develop --tags
   ```

1. Delete the hotfix branch:

   ```bash
   git branch -d hotfix/$ARGUMENTS
   ```

______________________________________________________________________

## PyPI release-failure runbook

Use this runbook when `verify-pypi` fails or users report installation issues.

### Step 1: assess the failure

Check the GitHub Actions workflow run to identify the issue:

- **Import failure**: missing module or dependency issue.
- **CLI failure**: entry-point misconfiguration.
- **Validation failure**: core functionality broken.

### Step 2: yank the release (only if necessary)

Yank only if the release causes installation failures or breaks functionality.

1. Open <https://pypi.org/manage/project/dppvalidator/releases/>.
1. Find the affected version.
1. Click **Options → Yank release**.
1. Reason: "Installation/functionality issue - hotfix pending".

Yanked releases remain downloadable via explicit version, but won't be installed by default. Reversible.

### Step 3: cut a hotfix release

1. Branch:

   ```bash
   git checkout main && git pull && git checkout -b hotfix/v<NEXT_PATCH>
   ```

1. Fix the identified issue.

1. Add a regression test.

1. Full test suite:

   ```bash
   uv run pytest tests/ -v
   ```

1. Bump the patch version: `uv version patch`.

1. Update `CHANGELOG.md`:

   ```text
   ## [X.Y.Z] - YYYY-MM-DD

   ### Fixed
   - Fixed [description] that caused [symptom]
   ```

1. Commit, merge, tag:

   ```bash
   git add .
   git commit -m "fix: [description]"
   git checkout main && git merge --no-ff hotfix/v<VERSION>
   git tag -a v$(uv version --short) -m "Hotfix v$(uv version --short)"
   ```

1. Merge to `develop` and push:

   ```bash
   git checkout develop && git merge --no-ff main
   git push origin main develop --tags
   ```

### Step 4: verify the hotfix

1. Wait for CI/CD to complete.
1. Confirm `smoke-test` passes.
1. Confirm `verify-pypi` passes.
1. Test installation manually: `pip install dppvalidator==<NEW_VERSION>`.

### Step 5: communicate (if public release)

- Update the GitHub Release notes with hotfix information.
- If users were affected, consider a brief announcement.
