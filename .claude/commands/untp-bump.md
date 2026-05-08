---
description: Bootstrap support for a new UNTP version (vendors upstream artefacts, registers the version, scaffolds models, opens a feature branch). Reads the canonical playbook from the untp-migrate skill.
argument-hint: "<X.Y.Z>"
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(curl *) Bash(shasum *) Bash(python3 *) Bash(uv run *) Bash(jq *) Bash(mkdir *) Bash(cp *)
---

# /untp-bump

Bootstrap dppvalidator support for UNTP `$ARGUMENTS`. This is the executable form of the recipe in [.claude/skills/untp-migrate/SKILL.md](../skills/untp-migrate/SKILL.md). Read that skill for the full operating principles before running this; it must be loaded into context.

## Preconditions

- `git status` is clean.
- You're on `develop` (gitflow).
- `$ARGUMENTS` is a valid SemVer (e.g. `0.7.0`, `0.7.1`, `0.8.0`).

## Steps

### 1. Branch

```bash
git checkout develop && git pull origin develop
git checkout -b feature/untp-$ARGUMENTS
```

### 2. Vendor upstream artefacts

```bash
VER="$ARGUMENTS"
mkdir -p tests/fixtures/upstream/v$VER
BASE="https://opensource.unicc.org/un/unece/uncefact/spec-untp/-/raw/v$VER/artefacts"
curl -sL "$BASE/schema/v$VER/dpp/DigitalProductPassport.json" -o tests/fixtures/upstream/v$VER/dpp-schema.json
curl -sL "$BASE/contexts/v$VER/untp-context.jsonld"           -o tests/fixtures/upstream/v$VER/context.jsonld
curl -sL "$BASE/samples/v$VER/dpp/DigitalProductPassport_instance.json" -o tests/fixtures/upstream/v$VER/sample.json
shasum -a 256 tests/fixtures/upstream/v$VER/*
```

If any of those download as zero bytes, the upstream layout has shifted — stop and re-read the [migration plan](../../docs/plans/UNTP_0.7.0_MIGRATION.md) §2.6.

### 3. Drop into bundled paths

```bash
cp tests/fixtures/upstream/v$VER/dpp-schema.json src/dppvalidator/schemas/data/untp-dpp-schema-$VER.json
cp tests/fixtures/upstream/v$VER/context.jsonld   src/dppvalidator/vocabularies/data/untp-context-$VER.jsonld
```

### 4. Diff against the previous version

```bash
PREV=$(python3 -c "from dppvalidator.schemas.registry import SCHEMA_REGISTRY; \
  vs=sorted(SCHEMA_REGISTRY.keys()); print(vs[-1])")
python3 .claude/skills/untp-migrate/scripts/diff_schema.py \
  src/dppvalidator/schemas/data/untp-dpp-schema-$PREV.json \
  src/dppvalidator/schemas/data/untp-dpp-schema-$VER.json
```

Paste the output into a new `docs/plans/UNTP_${VER}_MIGRATION.md` (use the 0.7.0 plan as a template).

### 5. Register the version

You must edit (Claude does this — these aren't shell commands):

- [src/dppvalidator/schemas/registry.py](../../src/dppvalidator/schemas/registry.py) — append a `SchemaVersion` entry with the SHA-256 from step 2.
- [src/dppvalidator/exporters/contexts.py](../../src/dppvalidator/exporters/contexts.py) — append a `ContextDefinition` entry.
- [src/dppvalidator/validators/detection.py](../../src/dppvalidator/validators/detection.py) — extend `_CONTEXT_URL_PATTERN` if the new URL shape isn't already covered.
- `src/dppvalidator/schemas/data/MANIFEST.json` — add the new artefact entries.

### 6. Scaffold models

Create the `src/dppvalidator/models/v<MAJ>_<MIN>/` package with one file per top-level `$def` from the new schema. Stay strictly inside Pydantic v2 patterns (see `.claude/rules/dpp-domain.md`).

### 7. Wire the dispatch

Add the new version to `_MODEL_BY_VERSION` in `src/dppvalidator/validators/model.py`. Do not branch on the version literal anywhere else — the no-version-literals guard test will catch you.

### 8. Verify

```bash
uv run pytest tests/ -q
uv run ruff check src/ tests/
uv run ty check src/
```

### 9. Commit and push

```bash
git add tests/fixtures/upstream/v$VER \
        src/dppvalidator/schemas/data/untp-dpp-schema-$VER.json \
        src/dppvalidator/vocabularies/data/untp-context-$VER.jsonld \
        src/dppvalidator/schemas/data/MANIFEST.json \
        src/dppvalidator/schemas/registry.py \
        src/dppvalidator/exporters/contexts.py \
        src/dppvalidator/validators/detection.py \
        src/dppvalidator/models/v* \
        src/dppvalidator/validators/model.py \
        docs/plans/UNTP_${VER}_MIGRATION.md
git commit -m "feat(untp): vendor and register UNTP $ARGUMENTS"
git push -u origin feature/untp-$ARGUMENTS
```

The shim, version-matrix tests, default-flip, deprecation, and removal happen in **separate PRs** — see the plan's phase split. Do not bundle them into this branch.
