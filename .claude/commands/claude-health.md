---
description: Maintain coherence across Claude Code agentic capabilities (CLAUDE.md, rules, skills, commands, hooks)
allowed-tools: Bash(ls *) Bash(find *) Bash(wc *) Bash(head *) Bash(cat *) Bash(jq *) Bash(python3 *)
---

# /claude-health

Audit the project's Claude Code configuration and surface inconsistencies.

## 1. Inventory check

Verify all expected Claude Code files exist:

```!
ls -la .claude/rules/*.md .claude/commands/*.md .claude/settings.json 2>/dev/null | head -40
```

```!
find .claude/skills -name "SKILL.md" 2>/dev/null
```

```!
ls -la CLAUDE.md AGENTS.md 2>/dev/null
```

## 2. Size validation

Keep individual rules and commands tight. CLAUDE.md should stay under ~200 lines for best adherence.

```!
wc -l CLAUDE.md AGENTS.md 2>/dev/null
```

```!
wc -c .claude/rules/*.md
```

```!
wc -c .claude/commands/*.md
```

```!
wc -c .claude/skills/*/SKILL.md
```

## 3. Cross-reference audit

Confirm these alignments:

| Source                                | Must reference        | Check                                |
| ------------------------------------- | --------------------- | ------------------------------------ |
| `.claude/rules/python-style.md`       | Pydantic, type hints  | Matches `src/dppvalidator/` patterns |
| `.claude/rules/dpp-domain.md`         | ESPR, CIRPASS, DPP    | Matches domain model structure       |
| `.claude/rules/commits.md`            | Conventional commits  | Consistent with gitflow workflows    |
| `.claude/skills/validate-dpp/`        | Validation logic      | References correct validator paths   |
| `.claude/skills/pypi-publish/`        | Publishing steps      | Matches `pyproject.toml` config      |
| Root `AGENTS.md` (imported by CLAUDE) | Tech stack, structure | Reflects current project state       |

## 4. Command consistency

Verify command descriptions match their content:

```!
head -5 .claude/commands/*.md
```

Check cross-references between commands:

- `/release` should reference `/lint` and `/test`.
- `/feature` and `/hotfix` follow gitflow.
- `/fix-lint` complements `/lint`.

## 5. Hooks validation

```!
cat .claude/settings.json | python3 -m json.tool > /dev/null && echo ".claude/settings.json valid JSON"
```

Verify hook commands are valid:

- Commands use correct tool paths (`uv run ruff`, etc.).
- Hook scripts under `.claude/hooks/` are executable.
- Use the `$CLAUDE_PROJECT_DIR` env var for project-relative script paths.

```!
ls -l .claude/hooks/ 2>/dev/null
```

## 6. CLAUDE.md / AGENTS.md consistency

Verify root context covers:

- [ ] Project overview and purpose
- [ ] Tech stack (Python 3.10+, Pydantic v2, uv, ruff, ty)
- [ ] Directory structure
- [ ] Development workflow (gitflow)
- [ ] Code principles (SOLID, DRY)

Check for conflicts between:

- Root `AGENTS.md` ↔ `.claude/rules/*.md`
- Skills ↔ Commands (e.g. `/pypi-publish` skill vs `/release` command)
- `CLAUDE.md` ↔ `AGENTS.md` (CLAUDE.md should `@AGENTS.md`, not duplicate)

```!
head -3 CLAUDE.md
```

## 7. Skill / command frontmatter

Spot-check that skill frontmatter is well-formed:

```!
for f in .claude/skills/*/SKILL.md; do echo "=== $f ==="; awk '/^---$/{c++; if(c==2) exit} c==1' "$f"; done
```

```!
for f in .claude/commands/*.md; do echo "=== $f ==="; awk '/^---$/{c++; if(c==2) exit} c==1' "$f"; done
```

## 8. Report and fix

Document any misalignments found:

- [ ] Missing files → create from templates.
- [ ] Oversized files → trim or split into path-scoped rules / supporting files.
- [ ] Stale references → update paths.
- [ ] Outdated tech stack → update `AGENTS.md`.
- [ ] Conflicting guidance → resolve in favor of `AGENTS.md` and `CLAUDE.md`.

If changes were made, commit:

```bash
git add .claude/ CLAUDE.md AGENTS.md \
  && git commit -m "chore: align claude-code agentic capabilities"
```

**Run this workflow monthly or after major refactors.**
