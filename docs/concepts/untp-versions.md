<!-- markdownlint-disable MD013 MD060 -->

# UNTP DPP versions

dppvalidator supports more than one UNTP DPP wire format. This page is the
single authoritative explanation of how versions are detected, which one
is the default, how to pick one explicitly, and how a new one would be
added.

For a side-by-side migration walkthrough between specific versions,
see the [migration guide](../guides/migration-0-6-to-0-7.md).

## Supported versions

| UNTP DPP version | Default? | Status                                                                  | Wire shape highlight                                                          |
| ---------------- | -------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **0.6.0**        | no       | Supported (legacy)                                                      | Same envelope as 0.6.1; minor schema-only fixes only.                         |
| **0.6.1**        | no       | Supported (legacy)                                                      | `credentialSubject` is a `ProductPassport` envelope wrapping `Product`.       |
| **0.7.0**        | **yes**  | Default — set in `dppvalidator.schemas.registry.DEFAULT_SCHEMA_VERSION` | `credentialSubject` IS the `Product` directly. No `ProductPassport` envelope. |

Future releases may flip the default. The flip is a separate minor
release with deprecation warnings — see *Adding a new version* below.

## How a payload's version is detected

`dppvalidator.validators.detection.detect_schema_version(data)` is the
**only** place where this decision is made. The detection rules apply
in order:

1. **`$schema` URL** — if the payload carries a `$schema` field whose
   URL matches a vendored schema basename
   (`untp-dpp-schema-X.Y.Z.json` or `…/vX.Y.Z/.../DigitalProductPassport.json`),
   that wins.
1. **`@context` URLs** — if a context entry matches a registered
   pattern, the version is read from there. Two URL conventions are
   recognised:
   - Legacy (0.6.x): `https://test.uncefact.org/vocabulary/untp/dpp/X.Y.Z/`
   - Modern (0.7.0+): `https://vocabulary.uncefact.org/untp/X.Y.Z/context/`
1. **Type marker** — if `"DigitalProductPassport"` appears in the
   `type` array, the payload is recognised as a DPP and the
   `DEFAULT_SCHEMA_VERSION` is used.
1. **Fallback** — `DEFAULT_SCHEMA_VERSION`.

False positives are guarded by a registry-membership check at the call
sites: a `/X.Y.Z/` URL segment that doesn't appear in
`SCHEMA_REGISTRY` is rejected. Adding a new URL convention means
appending a pattern in [validators/detection.py](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/detection.py),
not anywhere else.

## Picking a version explicitly

Three layers can pin a version. Pick the one that matches your
intent.

### Engine-wide pin

```python
from dppvalidator.validators import ValidationEngine

# Pin the engine; auto-detection is bypassed.
engine = ValidationEngine(schema_version="0.7.0")
result = engine.validate(payload)
```

When `schema_version` and the payload's declared version disagree,
the engine emits a **VER001 version mismatch** error and refuses to
validate. This fail-fast behaviour catches accidental version
mixing in pipelines.

### CLI pin

```bash
# Validate as 0.7.0 (current default; the flag is optional).
dppvalidator validate passport.json --schema-version 0.7.0

# Validate as 0.6.1 (legacy) regardless of the payload's declared version.
dppvalidator validate passport.json --schema-version 0.6.1

# List every version the registry knows about.
dppvalidator schema list
```

### Programmatic registry lookup

```python
from dppvalidator.schemas.registry import SCHEMA_REGISTRY, SchemaRegistry

reg = SchemaRegistry()
print(reg.available_versions)  # ['0.6.0', '0.6.1', '0.7.0']
print(reg.default_version)  # '0.7.0'

# The SHA-pinned upstream URL the bundled bytes came from.
print(reg.get_schema_url("0.7.0"))

# The canonical production URL (when set; e.g. untp.unece.org for v0.7).
print(reg.get_production_url("0.7.0"))

# JSON-LD context URLs paired with this version.
print(reg.get_context_urls("0.7.0"))
```

## Default version

`dppvalidator.schemas.registry.DEFAULT_SCHEMA_VERSION` is the single
source of truth. Application code that needs to refer to "the active
default" version SHOULD use
`dppvalidator.compat.active_version()` instead of importing the
constant directly — both return the same string, but
`active_version()` keeps your call site outside the
no-version-literals guard's allow-list.

```python
from dppvalidator.compat import active_version, is_version

if is_version("0.7.0"):
    # we're on a build whose default is v0.7.0
    ...
```

## Coexistence with v0.6.x

v0.6.x and v0.7.0 coexist in the same release. Every validator layer,
every exporter, and every model package is version-aware:

| Surface                       | v0.6 entry point                                               | v0.7 entry point                                           |
| ----------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| Pydantic model package        | `dppvalidator.models.v0_6.*`                                   | `dppvalidator.models.v0_7.*`                               |
| Top-level shim (back-compat)  | `dppvalidator.models.passport.DigitalProductPassport` (= v0.6) | `dppvalidator.models.v0_7.envelope.DigitalProductPassport` |
| Semantic-rule registry        | `dppvalidator.validators.rules.v0_6`                           | `dppvalidator.validators.rules.v0_7`                       |
| Deep-link path table          | `LINK_PATHS_BY_VERSION["0.6.1"]`                               | `LINK_PATHS_BY_VERSION["0.7.0"]`                           |
| EU DPP exporter mapping table | `TermMapping.untp_v0_6`                                        | `TermMapping.untp_v0_7`                                    |
| Engine model dispatch         | `_MODEL_BY_VERSION["0.6.1"]`                                   | `_MODEL_BY_VERSION["0.7.0"]`                               |
| Compat shim (input upgrade)   | n/a                                                            | `dppvalidator.compat.upgrade_0_6_to_0_7.upgrade(data)`     |

Plugin authors targeting a specific version should set
`applies_to_versions: tuple[str, ...] = ("0.7.0",)` on their rule
class and gate their attribute access on the wire shape they expect.
See the [example plugin](https://github.com/artiso-ai/dppvalidator/tree/main/examples/dppvalidator_example_plugin)
for a worked v0.6 vs v0.7 sibling pair.

## Migrating between versions

v0.6.x payloads can be upgraded to v0.7.0 shape via the bundled
compat shim:

```bash
# Upgrade a single payload, write to stdout.
dppvalidator migrate passport.json

# Upgrade in place, accepting any warnings.
dppvalidator migrate passport.json --in-place --accept-warnings

# Validate the v0.6 payload against v0.7 (runs the shim, then validates).
dppvalidator validate passport.json --upgrade-from 0.6.1 --schema-version 0.7.0
```

The shim emits structured warnings (`UPG001`–`UPG004`) for lossy or
synthesised values; a sidecar `<output>.warnings.json` is always
written when blocking warnings fire. See the
[migration guide](../guides/migration-0-6-to-0-7.md) for the field
rename table and known shim limitations.

## Adding a new UNTP version

The full recipe lives in
[`.claude/skills/untp-migrate/SKILL.md`](https://github.com/artiso-ai/dppvalidator/blob/main/.claude/skills/untp-migrate/SKILL.md)
(invocable as `/untp-bump <X.Y.Z>` in Claude Code) and the
authoritative cardinal-rules document is
[`.claude/rules/untp-versioning.md`](https://github.com/artiso-ai/dppvalidator/blob/main/.claude/rules/untp-versioning.md).
The minimum touch list:

1. `src/dppvalidator/schemas/registry.py` — one new `SchemaVersion` entry.
1. `src/dppvalidator/exporters/contexts.py` — one new `ContextDefinition` entry.
1. `src/dppvalidator/schemas/data/MANIFEST.json` — manifest entries for the new schema and context (with SHA-256, source URL, production URL).
1. `src/dppvalidator/schemas/data/untp-dpp-schema-X.Y.Z.json` — vendored schema bytes.
1. `src/dppvalidator/vocabularies/data/untp-context-X.Y.Z.jsonld` — vendored context bytes.
1. `src/dppvalidator/models/vX_Y/` — new Pydantic model package.
1. `src/dppvalidator/validators/model.py` — add to `_MODEL_BY_VERSION`.
1. `src/dppvalidator/validators/detection.py` — extend URL pattern if the namespace shape changed.
1. `src/dppvalidator/compat/upgrade_<PREV>_to_<NEW>.py` — input shim from the previous version.
1. `tests/fixtures/upstream/vX.Y.Z/` — vendored upstream samples + schema.
1. `tests/integration/test_version_matrix.py` — add the new version to the matrix.
1. `docs/plans/UNTP_X.Y.Z_MIGRATION.md` — full migration doc.

If your change touches more than this list, you're either fixing an
unrelated bug (split the PR) or going around the version-aware
spine (don't).

## See also

- [Migration guide: 0.6.x → 0.7.0](../guides/migration-0-6-to-0-7.md)
- [Validation pipeline](validation-layers.md) — how the version flows through the validator layers.
- [EU DPP ontology alignment](eudpp-ontology-alignment.md) — how UNTP versions map onto EU DPP / CIRPASS-2 ontology terms.
- [Migration plan archive](https://github.com/artiso-ai/dppvalidator/blob/main/docs/plans/UNTP_0.7.0_MIGRATION.md) — phased history of the v0.7.0 migration.
