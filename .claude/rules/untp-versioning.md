---
paths:
  - "src/dppvalidator/schemas/**"
  - "src/dppvalidator/exporters/contexts.py"
  - "src/dppvalidator/exporters/jsonld.py"
  - "src/dppvalidator/exporters/eudpp_jsonld.py"
  - "src/dppvalidator/validators/detection.py"
  - "src/dppvalidator/validators/model.py"
  - "src/dppvalidator/validators/jsonld_semantic.py"
  - "src/dppvalidator/validators/semantic.py"
  - "src/dppvalidator/models/**"
  - "src/dppvalidator/cli/commands/**"
  - "src/dppvalidator/compat/**"
---

# UNTP Versioning Rules

These files form the version-aware spine of the validator. Read carefully before editing — they have stricter rules than the rest of the codebase.

## Cardinal rules

1. **No bare UNTP version literals.** A string like `"0.6.1"` or `"0.7.0"` may only appear in `src/dppvalidator/schemas/registry.py` and `src/dppvalidator/exporters/contexts.py`. Everywhere else: look it up via `SchemaRegistry`, `ContextManager`, or `dppvalidator.compat.active_version()`. The `tests/unit/test_no_version_literals.py` guard will fail your PR otherwise.

2. **Models are version-namespaced.** Pydantic classes for UNTP data live in `src/dppvalidator/models/v0_6/`, `…v0_7/`, etc. Never edit a `v0_X` package to absorb behaviour from a different version. To support a new version, add a `v0_Y/` package — do not graft fields onto the previous one.

3. **Detection is centralised.** `validators/detection.py` is the only place that decides what version a payload is. New URL/namespace shapes get added to `_CONTEXT_URL_PATTERN` and `_SCHEMA_URL_PATTERN` there, nowhere else.

4. **Bundled artefacts have a manifest.** Every JSON Schema and JSON-LD context vendored under `src/dppvalidator/schemas/data/` or `src/dppvalidator/vocabularies/data/` MUST appear in `src/dppvalidator/schemas/data/MANIFEST.json` with version, source URL, SHA-256, and pull date. CI verifies the hashes.

5. **Coexist before you cut.** When a new version lands, the previous version must keep working in the same release. Removing a version is its own minor release with its own deprecation warning lead-time.

## Adding a UNTP version: short version

Use the `/untp-bump <X.Y.Z>` slash command. It runs the recipe documented in [`.claude/skills/untp-migrate/SKILL.md`](../skills/untp-migrate/SKILL.md). Read that skill in full before improvising.

## Adding a UNTP version: minimum touch list

When you add `vX.Y.Z`, you must touch:

- `src/dppvalidator/schemas/registry.py` — one `SchemaVersion` entry.
- `src/dppvalidator/exporters/contexts.py` — one `ContextDefinition` entry.
- `src/dppvalidator/schemas/data/MANIFEST.json` — manifest entries for the new schema and context files.
- `src/dppvalidator/schemas/data/untp-dpp-schema-X.Y.Z.json` — vendored schema.
- `src/dppvalidator/vocabularies/data/untp-context-X.Y.Z.jsonld` — vendored context.
- `src/dppvalidator/models/vX_Y/` — new Pydantic model package.
- `src/dppvalidator/validators/model.py` — add to `_MODEL_BY_VERSION`.
- `src/dppvalidator/validators/detection.py` — extend URL pattern if the namespace shape changed.
- `src/dppvalidator/compat/upgrade_<PREV>_to_<NEW>.py` — input shim.
- `tests/fixtures/upstream/vX.Y.Z/` — vendored upstream samples + schema.
- `tests/integration/test_version_matrix.py` — add the new version to the matrix.
- `docs/plans/UNTP_X.Y.Z_MIGRATION.md` — full migration doc.

If you touched more than this list, you're either fixing an unrelated bug (split the PR) or going around the version-aware spine (don't).

## Anti-patterns

- Hardcoding `"0.6.1"` or `"0.7.0"` as a default in a function signature.
- Branching on `if version == "0.7.0":` outside `validators/model.py`'s `_MODEL_BY_VERSION` table.
- Adding a `Optional[Union[Old, New]]` typed field to a model to "support both".
- Fetching a schema or context from the network during validation.
- Editing a vendored schema or context to "fix" something — that breaks the SHA-256 manifest. Either upgrade to a new upstream version or open an upstream issue.
