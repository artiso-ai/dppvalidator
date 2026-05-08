# UNTP DPP Schema Files

This directory contains bundled JSON Schema files for the UN
Transparency Protocol (UNTP) Digital Product Passport (DPP)
specification.

## Source

Schemas are sourced from the official UN/CEFACT vocabulary
repositories:

- **v0.6.x**: <https://test.uncefact.org/vocabulary/untp/dpp/>
- **v0.7.0**: <https://untp.unece.org/artefacts/schema/v0.7.0/dpp/>
- **Specification**: <https://untp.unece.org/specification/DigitalProductPassport>

## Included schemas

<!-- markdownlint-disable MD013 -->

| File                         | Version |  Bytes | SHA-256 (LF-normalised)                                            |
| ---------------------------- | ------- | -----: | ------------------------------------------------------------------ |
| `untp-dpp-schema-0.6.1.json` | 0.6.1   | 49 381 | `c0fdd7da5d23b6aec5d1d0ce198ca8d1cd67ca27609395a1b4961b3d1a8549a8` |
| `untp-dpp-schema-0.7.0.json` | 0.7.0   | 50 362 | `42c51943ab23547d5287899fd12b214b19b006c28d105a70ff390f8551b12653` |

<!-- markdownlint-enable MD013 -->

The full provenance + integrity record (source URL, production
mirror URL, upstream commit, pull date, notes) for each file lives
in [`MANIFEST.json`](MANIFEST.json) and is enforced by
[`tests/unit/test_manifest_integrity.py`](../../../../tests/unit/test_manifest_integrity.py).

`v0.6.0` is registered in
[`schemas/registry.py`](../registry.py) but its bytes are **not**
bundled — it shares the wire shape of `v0.6.1` and the engine
defaults v0.6.x callers to the bundled `v0.6.1` schema.

## Manifest

Every artefact under this directory and under
`src/dppvalidator/vocabularies/data/` is required to appear in
[`MANIFEST.json`](MANIFEST.json) with version, source URL,
production URL (when set), SHA-256, and pull date. CI enforces this
contract via the manifest-integrity test; adding a vendored file
without a manifest entry trips the drift catch.

The "two URLs per artefact" pattern records:

- **`source_url`** — the SHA-pinned upstream URL the bundled bytes
  came from. Immutable; used for re-pulling and integrity diffs.
- **`production_url`** — the canonical production hosting (e.g.
  `untp.unece.org` for v0.7.0). Human-friendly; used for
  documentation links. Verified bit-identical to `source_url` at
  vendor time.

## License

The UNTP specification and schemas are published by UN/CEFACT under
open governance. See the [UNTP specification](https://untp.unece.org/)
for licensing details.

## Updates

For routine refreshes (new patch level on an existing version),
re-fetch from the production URL and verify the SHA-256 matches the
manifest pin. If the upstream bytes changed, update the manifest
hash in the same change.

For a new minor/major UNTP version, the recipe lives in
[`.claude/skills/untp-migrate/SKILL.md`](../../../../.claude/skills/untp-migrate/SKILL.md)
(invocable as `/untp-bump <X.Y.Z>` in Claude Code). The minimum
touch list and full versioning rules are in
[`.claude/rules/untp-versioning.md`](../../../../.claude/rules/untp-versioning.md).

```python
from dppvalidator.schemas import SchemaLoader

loader = SchemaLoader()
loader.download_schema("0.7.0", output_dir="./schemas/data")
```
