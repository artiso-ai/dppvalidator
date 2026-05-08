---
name: untp-migrate
description: Plan, scaffold, and execute a UNTP DPP version bump (e.g. 0.6.1 → 0.7.0). Use when the user asks about adding a new UNTP version, migrating fixtures or models between versions, drifting away from a hardcoded version, or when working in src/dppvalidator/{schemas,exporters,models,validators}/ during a known migration window.
allowed-tools: Read Edit Write Grep Glob Bash(uv run pytest *) Bash(uv run ruff *) Bash(uv run ty *) Bash(curl *) Bash(python3 *) Bash(shasum *) Bash(jq *)
---

# untp-migrate

Companion skill to [docs/plans/UNTP_0.7.0_MIGRATION.md](../../docs/plans/UNTP_0.7.0_MIGRATION.md). Use it for any UNTP version bump, not only 0.7.0.

## When to invoke

- Adding a new UNTP minor (0.7.0 today, 0.7.x or 0.8.0 next).
- Touching anything under `src/dppvalidator/schemas/`, `src/dppvalidator/exporters/contexts.py`, `src/dppvalidator/validators/detection.py`, `src/dppvalidator/models/v*/`.
- Helping users migrate their own DPP payloads between versions.

## Operating principles (load these into your head before editing)

1. **No bare version literals** outside `schemas/registry.py` and `exporters/contexts.py`. If you find a `"0.6.1"` literal anywhere else, replace it with a registry lookup.
2. **Models are version-namespaced** under `dppvalidator.models.v0_6/`, `…v0_7/`, etc. Never edit a `v0_*` package to "fix" a bug introduced by a different version — branch the version.
3. **Bundled artefacts have a manifest.** Every JSON Schema, JSON-LD context, and ontology lives under `src/dppvalidator/schemas/data/` or `src/dppvalidator/vocabularies/data/`, with SHA-256 in `MANIFEST.json`. Updating an artefact means updating its hash.
4. **Detect, don't guess.** `validators/detection.py` is the only place that decides what version a payload is. Add new URL patterns there.
5. **Coexist before you cut.** Two adjacent versions (N-1 and N) must work simultaneously for one full minor release before N-1 is removed.

## Reference: 0.6.1 → 0.7.0 surface deltas

The migration plan has the full table. The deltas you trip over most often:

- Namespace moved from `test.uncefact.org/vocabulary/untp/dpp/X.Y.Z/` to `vocabulary.uncefact.org/untp/X.Y.Z/context/`.
- `credentialSubject` is now a `Product` directly, not a `ProductPassport` envelope.
- `EmissionsPerformance`, `CircularityPerformance`, `TraceabilityPerformance`, `Metric` collapse into `Claim.claimedPerformance: Performance[]` keyed by `conformityTopic`.
- `serialNumber → itemNumber`; `producedByParty → relatedParty[0]`; `materialsProvenance → materialProvenance`; `Classification.schemeID → schemeId`.
- New required envelope fields: `validFrom`, `name`, `credentialSubject`.

## The bump recipe (mirrors `/untp-bump`)

For each new version `vX.Y.Z`:

### 1. Vendor upstream artefacts

```bash
mkdir -p tests/fixtures/upstream/v$VER
BASE="https://opensource.unicc.org/un/unece/uncefact/spec-untp/-/raw/v$VER/artefacts"
curl -sL $BASE/schema/v$VER/dpp/DigitalProductPassport.json -o tests/fixtures/upstream/v$VER/dpp-schema.json
curl -sL $BASE/contexts/v$VER/untp-context.jsonld           -o tests/fixtures/upstream/v$VER/context.jsonld
curl -sL $BASE/samples/v$VER/dpp/DigitalProductPassport_instance.json -o tests/fixtures/upstream/v$VER/sample.json
shasum -a 256 tests/fixtures/upstream/v$VER/*
```

Record the GitLab tag SHA and pull date in `tests/fixtures/upstream/SOURCES.md`.

### 2. Drop them under the bundled paths

```bash
cp tests/fixtures/upstream/v$VER/dpp-schema.json src/dppvalidator/schemas/data/untp-dpp-schema-$VER.json
cp tests/fixtures/upstream/v$VER/context.jsonld   src/dppvalidator/vocabularies/data/untp-context-$VER.jsonld
```

Then update `src/dppvalidator/schemas/data/MANIFEST.json` with version, source URL, SHA-256, and pull date.

### 3. Register the version

Add entries to:

- [src/dppvalidator/schemas/registry.py](../../src/dppvalidator/schemas/registry.py) — `SCHEMA_REGISTRY[VER] = SchemaVersion(...)`
- [src/dppvalidator/exporters/contexts.py](../../src/dppvalidator/exporters/contexts.py) — `CONTEXTS[VER] = ContextDefinition(...)`
- [src/dppvalidator/validators/detection.py](../../src/dppvalidator/validators/detection.py) — extend `_CONTEXT_URL_PATTERN` if the namespace shape changed

### 4. Diff against the previous version

Run the bundled helper to print a deltas table you can paste into the migration plan:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/diff_schema.py \
  src/dppvalidator/schemas/data/untp-dpp-schema-<PREV>.json \
  src/dppvalidator/schemas/data/untp-dpp-schema-<NEW>.json
```

### 5. Scaffold the model package

Create `src/dppvalidator/models/v<MAJ_MIN>/` with one file per top-level `$def`. Use Pydantic v2 patterns from `.claude/rules/dpp-domain.md`. Cross-field invariants live in `@model_validator(mode="after")`. Re-export the new models from `src/dppvalidator/models/__init__.py` only after the default version flips.

### 6. Wire the model dispatch

In [src/dppvalidator/validators/model.py](../../src/dppvalidator/validators/model.py), add the new version to `_MODEL_BY_VERSION`. Do not branch on version anywhere else.

### 7. Write the upgrade shim

Add `dppvalidator/compat/upgrade_<PREV>_to_<NEW>.py`. The shim takes a dict and returns a dict; lossy mappings emit warnings, never silently drop. Property-based tests round-trip every previous-version fixture through it.

### 8. Tests and fixtures

- Add `tests/fixtures/valid/untp-dpp-instance-$VER.json`.
- Parametrise version-relevant tests with `@pytest.mark.parametrize("version", [...])`.
- Add `tests/integration/test_version_matrix.py` cases for the new pair.

### 9. Verify

```bash
uv run pytest tests/ -q
uv run ruff check src/ tests/
uv run ty check src/
```

The `tests/unit/test_no_version_literals.py` regex guard must stay green.

### 10. Docs

- Add `docs/guides/migration-<PREV>-to-<NEW>.md` (use the 0.6→0.7 doc as the template).
- Update `docs/concepts/untp-versions.md` table.
- Refresh CHANGELOG.

## Anti-patterns to refuse

- "Just bump the default to the new version" without writing the upgrade shim — breaks every pinned downstream user.
- "Edit the existing model class in place" — produces an Either-typed schema and unstable JSON-LD output.
- "Fetch the schema from the network at validate time" — destroys offline-first behaviour and supply-chain integrity.
- "Bypass the registry with a one-off literal because it's a test fixture" — defeats the no-literals guard test.

## Pointers

- Migration plan: [docs/plans/UNTP_0.7.0_MIGRATION.md](../../docs/plans/UNTP_0.7.0_MIGRATION.md)
- Upstream source: <https://opensource.unicc.org/un/unece/uncefact/spec-untp> (tag `v0.7.0`)
- Hosted context: <https://vocabulary.uncefact.org/untp/0.7.0/context/>
- Versioning rule: [.claude/rules/untp-versioning.md](../../.claude/rules/untp-versioning.md)
