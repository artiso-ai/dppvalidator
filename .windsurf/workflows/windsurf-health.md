---
description: Maintain coherence across Windsurf agentic capabilities
---

## 1. Inventory Check

Verify all expected Windsurf files exist:

// turbo
1. `ls -la .windsurf/rules/*.md .windsurf/workflows/*.md .windsurf/hooks.json 2>/dev/null | head -30`

// turbo
2. `find .windsurf/skills -name "SKILL.md" 2>/dev/null`

// turbo
3. `find . -maxdepth 3 -name "AGENTS.md" 2>/dev/null`

## 2. Size Validation

Check rules and workflows stay within 12KB limit:

// turbo
4. `wc -c .windsurf/rules/*.md`

// turbo
5. `wc -c .windsurf/workflows/*.md`

## 3. Cross-Reference Audit

6. Review and confirm these alignments:

| Source                | Must Reference             | Check                                        |
| --------------------- | -------------------------- | -------------------------------------------- |
| `python-style.md`     | Pydantic, type hints       | Matches `src/dppvalidator/` patterns         |
| `dpp-domain.md`       | ESPR, CIRPASS, DPP         | Matches domain model structure               |
| `commits.md`          | Conventional commits       | Consistent with gitflow workflows            |
| `validate-dpp` skill  | Validation logic           | References correct validator paths           |
| `pypi-publish` skill  | Publishing steps           | Matches `pyproject.toml` config              |
| Root `AGENTS.md`      | Tech stack, structure      | Reflects current project state               |

## 4. Workflow Consistency

7. Verify workflow descriptions match their content:

// turbo
`head -5 .windsurf/workflows/*.md`

8. Check for workflow cross-references (workflows calling other workflows):
   - `/release` should reference `/lint` and `/test`
   - `/feature` and `/hotfix` follow gitflow
   - `/fix-lint` complements `/lint`

## 5. Hooks Validation

// turbo
9. `cat .windsurf/hooks.json | python -m json.tool > /dev/null && echo "hooks.json valid JSON"`

10. Verify hook commands are valid:
    - Commands use correct tool paths (`uv run ruff`)
    - Working directory variables are valid (`${workspace_root}`)

## 6. AGENTS.md Consistency

11. Verify root `AGENTS.md` covers:
    - [ ] Project overview and purpose
    - [ ] Tech stack (Python 3.10+, Pydantic v2, uv, ruff, ty)
    - [ ] Directory structure
    - [ ] Development workflow (gitflow)
    - [ ] Code principles (SOLID, DRY)

12. Check no conflicts between:
    - Root `AGENTS.md` ↔ `.windsurf/rules/*.md`
    - Skills ↔ Workflows (e.g., pypi-publish skill vs release workflow)

## 7. Report & Fix

13. Document any misalignments found:
    - [ ] Missing files → Create from templates
    - [ ] Size violations (>12KB) → Trim content
    - [ ] Stale references → Update paths
    - [ ] Outdated tech stack → Update AGENTS.md
    - [ ] Conflicting guidance → Resolve in favor of AGENTS.md

14. If changes made, commit:
    `git add .windsurf/ AGENTS.md && git commit -m "chore: align windsurf agentic capabilities"`

**Run this workflow monthly or after major refactors.**
