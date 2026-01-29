# Repository Security Setup Guide

This guide documents the branch protection rules and security settings required for the dppvalidator open-source repository.

## 1. Branch Protection Rules

### Main Branch (`main`)

Navigate to: **Settings → Branches → Add branch protection rule**

| Setting                                                  | Value                          |
| -------------------------------------------------------- | ------------------------------ |
| Branch name pattern                                      | `main`                         |
| **Require a pull request before merging**                | ✅ Enabled                     |
| → Require approvals                                      | ✅ 1 approval minimum          |
| → Dismiss stale PR approvals when new commits are pushed | ✅ Enabled                     |
| → Require review from Code Owners                        | ✅ **Enabled**                 |
| → Restrict who can dismiss PR reviews                    | ✅ Code Owners only            |
| **Require status checks to pass before merging**         | ✅ Enabled                     |
| → Require branches to be up to date                      | ✅ Enabled                     |
| → Status checks:                                         | `test`, `lint`                 |
| **Require conversation resolution before merging**       | ✅ Enabled                     |
| **Require signed commits**                               | ✅ Recommended                 |
| **Require linear history**                               | ✅ Enabled (clean git history) |
| **Do not allow bypassing the above settings**            | ✅ **Enabled**                 |
| **Restrict who can push to matching branches**           | ✅ Enabled                     |
| → Restrict pushes that create matching branches          | ✅ Enabled                     |
| → Allow specified actors:                                | Code Owners only               |
| **Allow force pushes**                                   | ❌ Disabled                    |
| **Allow deletions**                                      | ❌ Disabled                    |

### Develop Branch (`develop`)

Navigate to: **Settings → Branches → Add branch protection rule**

| Setting                                                  | Value                 |
| -------------------------------------------------------- | --------------------- |
| Branch name pattern                                      | `develop`             |
| **Require a pull request before merging**                | ✅ Enabled            |
| → Require approvals                                      | ✅ 1 approval minimum |
| → Dismiss stale PR approvals when new commits are pushed | ✅ Enabled            |
| → Require review from Code Owners                        | ✅ **Enabled**        |
| **Require status checks to pass before merging**         | ✅ Enabled            |
| → Status checks:                                         | `test`, `lint`        |
| **Require conversation resolution before merging**       | ✅ Enabled            |
| **Do not allow bypassing the above settings**            | ✅ **Enabled**        |
| **Restrict who can push to matching branches**           | ✅ Enabled            |
| → Allow specified actors:                                | Code Owners only      |
| **Allow force pushes**                                   | ❌ Disabled           |
| **Allow deletions**                                      | ❌ Disabled           |

### Release Branches (`release/*`)

| Setting                                   | Value               |
| ----------------------------------------- | ------------------- |
| Branch name pattern                       | `release/*`         |
| **Require a pull request before merging** | ✅ Enabled          |
| → Require review from Code Owners         | ✅ **Enabled**      |
| **Require status checks to pass**         | ✅ Enabled          |
| **Restrict who can push**                 | ✅ Code Owners only |
| **Allow force pushes**                    | ❌ Disabled         |
| **Allow deletions**                       | ❌ Disabled         |

______________________________________________________________________

## 2. Tag Protection Rules

Navigate to: **Settings → Tags → Protected tags**

| Pattern | Who can create                 |
| ------- | ------------------------------ |
| `v*`    | Code Owners / Maintainers only |

This ensures only authorized users can create version tags that trigger PyPI releases.

______________________________________________________________________

## 3. Environment Protection (PyPI Publishing)

Your `release.yml` already uses GitHub Environments. Configure protection:

### TestPyPI Environment

Navigate to: **Settings → Environments → testpypi**

| Setting                 | Value                                  |
| ----------------------- | -------------------------------------- |
| **Required reviewers**  | ✅ Add Code Owners                     |
| **Wait timer**          | Optional (0-30 minutes)                |
| **Deployment branches** | Selected branches: `main`, `release/*` |

### PyPI Environment (Production)

Navigate to: **Settings → Environments → pypi**

| Setting                 | Value                          |
| ----------------------- | ------------------------------ |
| **Required reviewers**  | ✅ Add Code Owners (mandatory) |
| **Wait timer**          | ✅ 5-10 minutes recommended    |
| **Deployment branches** | Selected branches: `main` only |

______________________________________________________________________

## 4. Repository Settings

Navigate to: **Settings → General**

### Pull Requests

- ✅ **Allow squash merging** (recommended for clean history)
- ❌ Disable merge commits (optional)
- ❌ Disable rebase merging (optional)
- ✅ **Always suggest updating pull request branches**
- ✅ **Automatically delete head branches**

### Pushes

- ✅ **Limit how many branches and tags can be updated in a single push**: 5

______________________________________________________________________

## 5. Actions Permissions

Navigate to: **Settings → Actions → General**

| Setting                                          | Value                                        |
| ------------------------------------------------ | -------------------------------------------- |
| **Actions permissions**                          | Allow all actions and reusable workflows     |
| **Fork pull request workflows**                  | Require approval for first-time contributors |
| **Workflow permissions**                         | Read repository contents only                |
| → Allow GitHub Actions to create and approve PRs | ❌ Disabled                                  |

______________________________________________________________________

## 6. Code Security

Navigate to: **Settings → Code security and analysis**

| Feature                             | Status     |
| ----------------------------------- | ---------- |
| **Dependency graph**                | ✅ Enabled |
| **Dependabot alerts**               | ✅ Enabled |
| **Dependabot security updates**     | ✅ Enabled |
| **Secret scanning**                 | ✅ Enabled |
| **Secret scanning push protection** | ✅ Enabled |

______________________________________________________________________

## 7. CODEOWNERS File

The `.github/CODEOWNERS` file defines who must review PRs:

```text
# Default owners for everything
*                           @matbmeijer

# Critical paths
/src/                       @matbmeijer
/.github/                   @matbmeijer
/pyproject.toml             @matbmeijer
```

**Important**: CODEOWNERS only works when:

1. The file is in `.github/CODEOWNERS`, `CODEOWNERS`, or `docs/CODEOWNERS`
1. Branch protection has "Require review from Code Owners" enabled
1. The repository is public OR on a paid GitHub plan

______________________________________________________________________

## 8. Quick Setup Checklist

```
□ Push CODEOWNERS file to repository
□ Configure main branch protection
□ Configure develop branch protection
□ Configure release/* branch protection
□ Add tag protection for v* tags
□ Create and configure 'testpypi' environment
□ Create and configure 'pypi' environment with required reviewers
□ Enable Dependabot alerts and security updates
□ Enable secret scanning
□ Review Actions permissions
```

______________________________________________________________________

## 9. Trusted Publishers (PyPI)

For additional security, configure PyPI Trusted Publishers:

1. Go to https://pypi.org/manage/account/publishing/
1. Add a new pending publisher:
   - **PyPI project name**: `dppvalidator`
   - **Owner**: `artiso-ai` (your GitHub org/user)
   - **Repository**: `dppvalidator`
   - **Workflow name**: `release.yml`
   - **Environment**: `pypi`

This eliminates the need for API tokens and ties publishing directly to your GitHub repository.

______________________________________________________________________

## Summary of Protection Layers

| Layer                 | Protection                                     |
| --------------------- | ---------------------------------------------- |
| **Code Changes**      | PRs required, Code Owner approval mandatory    |
| **Branch Tampering**  | No direct push, no force push, no deletion     |
| **Release Tags**      | Only Code Owners can create `v*` tags          |
| **TestPyPI**          | Environment protection with reviewer           |
| **PyPI (Production)** | Environment protection + wait timer + reviewer |
| **Secrets**           | Secret scanning + push protection              |
| **Dependencies**      | Dependabot alerts and security updates         |
