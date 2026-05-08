@AGENTS.md

## Working with Claude Code in this repo

This repository is configured for Claude Code under `.claude/`:

- `.claude/CLAUDE.md` — extra project instructions (this file imports it implicitly via `./CLAUDE.md`)
- `.claude/rules/` — path-scoped rules that load when Claude reads matching files
- `.claude/skills/` — invocable skills (`/validate-dpp`, `/pypi-publish`)
- `.claude/commands/` — slash commands for workflows (`/lint`, `/test`, `/feature`, `/release`, `/hotfix`, `/pr-review`, `/code-health`, `/docs-health`, `/dev-setup`, `/fix-lint`, `/claude-health`)
- `.claude/settings.json` — hooks and other shared settings (committed)
- `.claude/settings.local.json` — personal overrides (gitignored)

## Conventions specific to Claude Code sessions

- Always use `uv run <tool>` (not bare `pytest`/`ruff`/`ty`); the project pins versions through `uv`.
- Prefer the `Edit` tool for changes to existing files; reserve `Write` for new files.
- When editing Python under `src/dppvalidator/` or `tests/`, the `PostToolUse` hook auto-runs `uv run ruff check --fix` on the touched file. If a fix is applied, re-read the file before subsequent edits.
- Follow conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`, `perf:`). See `.claude/rules/commits.md`.
- Do not import plugin code from `src/dppvalidator/` (one-way dependency only). See `.claude/rules/plugin-licenses.md`.

## Quick orientation

- Public package: `src/dppvalidator/` (MIT)
- Plugin packages: `plugins/*/` (separately licensed; e.g. `plugins/textiles/` is GPL-3.0)
- Tests: `tests/{unit,integration,property,fuzz}/` with shared fixtures in `tests/fixtures/`
- Docs site: `mkdocs.yml` + `docs/`
- CLI entry: defined in `pyproject.toml`
- Versioned models: `src/dppvalidator/models/v0_6/`, `…/v0_7/`.
  Top-level imports re-export v0.6 for back-compat.
- Compat shim 0.6 → 0.7:
  `src/dppvalidator/compat/upgrade_0_6_to_0_7.py` (CLI:
  `dppvalidator migrate` and `validate --upgrade-from`).
- Versioning cardinal rules: `.claude/rules/untp-versioning.md`.
  Adding a UNTP version: `/untp-bump <X.Y.Z>`.
  Migration plan archive: `docs/plans/UNTP_0.7.0_MIGRATION.md`.
