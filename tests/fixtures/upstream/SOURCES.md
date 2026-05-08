<!-- markdownlint-disable MD013 -->

# Upstream UNTP artefacts (vendored)

This directory holds **read-only, byte-for-byte copies** of UN/CEFACT UNTP artefacts pulled from the upstream GitLab repository. They drive the `tests/fixtures/upstream/` validation matrix and are the source of truth that the bundled `src/dppvalidator/{schemas,vocabularies}/data/` files derive from. Do not edit them — re-vendor when the upstream tag changes.

Each version directory pins the exact upstream commit SHA so that re-pulling against a moved tag is detectable as a hash mismatch.

| Directory            | Vendored from                                                           | Purpose                                                                                                                                      |
| -------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [`v0.7.0/`](v0.7.0/) | <https://opensource.unicc.org/un/unece/uncefact/spec-untp> tag `v0.7.0` | First release supported under the `0.4.0` migration plan ([docs/plans/UNTP_0.7.0_MIGRATION.md](../../../docs/plans/UNTP_0.7.0_MIGRATION.md)) |

______________________________________________________________________

## v0.7.0 — UNTP DPP `0.7.0`

**Upstream:** `https://opensource.unicc.org/un/unece/uncefact/spec-untp.git`
**Tag:** `v0.7.0`
**Pinned commit SHA:** `707cd5267deddede24bb74e453a758561972a109`
**Tag created:** `2026-05-04T10:34:14+00:00`
**Pulled:** `2026-05-07`
**Raw URL prefix:** `https://opensource.unicc.org/un/unece/uncefact/spec-untp/-/raw/707cd5267deddede24bb74e453a758561972a109/artefacts`
**Production mirror prefix:** `https://untp.unece.org/artefacts`

The "Raw URL prefix" is the SHA-pinned source we vendored from (immutable; safe to diff against). The "Production mirror prefix" is the human-friendly hosting at `untp.unece.org` — verified bit-identical to the SHA-pinned source on 2026-05-08 (every artefact's SHA-256 matched). Use the production mirror for documentation links; use the SHA-pinned URL for integrity checks.

### Files

| Local path                                                    | Upstream path                                                               |   Bytes | SHA-256                                                            |
| ------------------------------------------------------------- | --------------------------------------------------------------------------- | ------: | ------------------------------------------------------------------ |
| `v0.7.0/schema/DigitalProductPassport.json`                   | `artefacts/schema/v0.7.0/dpp/DigitalProductPassport.json`                   |  50 362 | `42c51943ab23547d5287899fd12b214b19b006c28d105a70ff390f8551b12653` |
| `v0.7.0/schema/Product.json`                                  | `artefacts/schema/v0.7.0/dpp/Product.json`                                  |  38 990 | `fde2e1f11b0bbebd8fc209675c0575f1ff8359a9b52e5557f01d41c11f9ef23f` |
| `v0.7.0/contexts/untp-context.jsonld`                         | `artefacts/contexts/v0.7.0/untp-context.jsonld`                             | 105 396 | `fbd4824e30d3cfc5cba949e1efe19b4c9ebaee056abe7aaf1c6b139a7bf91b0c` |
| `v0.7.0/samples/DigitalProductPassport_instance.json`         | `artefacts/samples/v0.7.0/dpp/DigitalProductPassport_instance.json`         |   8 749 | `4c8df24357651169a90242b3f779842573104ed5f755d8fbe817f3129e8f0f91` |
| `v0.7.0/samples/DigitalProductPassport_battery_instance.json` | `artefacts/samples/v0.7.0/dpp/DigitalProductPassport_battery_instance.json` |  23 268 | `462264fcc6a4dc5ebcdc69cfbe238f76d2efa75534b71d5e1195d33139c7e599` |
| `v0.7.0/samples/DigitalProductPassport_cathode_instance.json` | `artefacts/samples/v0.7.0/dpp/DigitalProductPassport_cathode_instance.json` |   9 628 | `65841b5f60aa0b11e8b5c19656525023c2d62be8e40a3757c08e36426c8c79f4` |
| `v0.7.0/vocabularies/untp-ontology.jsonld`                    | `artefacts/vocabularies/untp-core/untp-ontology.jsonld`                     | 147 724 | `752060cc15c6c77bfcea8b170f173239a705e9da389314c1cb2dacc8a69d93bc` |
| `v0.7.0/vocabularies/untp-metrics.jsonld`                     | `artefacts/vocabularies/untp-metrics/untp-metrics.jsonld`                   |  53 765 | `77900ce1138be124976d138750bea24bacb6c8ba327672fe8598b85db99a0a36` |
| `v0.7.0/vocabularies/untp-topics.jsonld`                      | `artefacts/vocabularies/untp-topics/untp-topics.jsonld`                     |  61 045 | `49affcb265bdf2a7a92d1b171c49a27543bfb4915bcbd11dd6e571252a57bb12` |

### Quick-look facts

- **DPP schema** — required: `[@context, id, issuer, validFrom, name, credentialSubject]`; 22 `$defs`; `credentialSubject` is `Product` (no `ProductPassport` envelope).
- **Context** — single unified `@context` covering DPP/DCC/DFR/DIA/DTE; 36 top-level term keys; `untp` prefix is `https://vocabulary.uncefact.org/untp/`; JSON-LD `@version: 1.1`.
- **Samples** — all three samples validate cleanly against the bundled DPP schema (verified at vendor time).

### Verifying integrity

The snippet below extracts the `(local-path, sha256)` pairs from the table above and re-checks them with `shasum`. It is robust to Markdown table reformatting because it pattern-matches on the literal backticks around the path and the 64-char hex SHA, not on byte positions:

```bash
python3 - <<'PY' | shasum -a 256 -c
import re, pathlib
src = pathlib.Path("tests/fixtures/upstream/SOURCES.md").read_text()
# Match a path-in-backticks (`v0.X.Y/...`) followed within the same row by
# a 64-char hex SHA-256 in backticks. `.*?` is non-greedy so adjacent rows
# don't bleed into each other.
pat = r"`(v0\.\d+\.\d+/[^`]+)`.*?`([0-9a-f]{64})`"
for path, sha in re.findall(pat, src):
    print(f"{sha}  tests/fixtures/upstream/{path}")
PY
```

Or, equivalently, re-pull and diff:

```bash
sha=707cd5267deddede24bb74e453a758561972a109
base=https://opensource.unicc.org/un/unece/uncefact/spec-untp/-/raw/$sha/artefacts
diff <(curl -sL $base/schema/v0.7.0/dpp/DigitalProductPassport.json) tests/fixtures/upstream/v0.7.0/schema/DigitalProductPassport.json
```

### Production mirror cross-check

The production mirror at `untp.unece.org` is verified bit-identical to the SHA-pinned `opensource.unicc.org` source on each re-vendor pull. To re-run the cross-check against the current bundled bytes:

```bash
prod=https://untp.unece.org/artefacts
diff <(curl -sL $prod/schema/v0.7.0/dpp/DigitalProductPassport.json) tests/fixtures/upstream/v0.7.0/schema/DigitalProductPassport.json
diff <(curl -sL $prod/schema/v0.7.0/dpp/Product.json) tests/fixtures/upstream/v0.7.0/schema/Product.json
diff <(curl -sL $prod/samples/v0.7.0/dpp/DigitalProductPassport_instance.json) tests/fixtures/upstream/v0.7.0/samples/DigitalProductPassport_instance.json
diff <(curl -sL $prod/samples/v0.7.0/dpp/DigitalProductPassport_battery_instance.json) tests/fixtures/upstream/v0.7.0/samples/DigitalProductPassport_battery_instance.json
diff <(curl -sL $prod/samples/v0.7.0/dpp/DigitalProductPassport_cathode_instance.json) tests/fixtures/upstream/v0.7.0/samples/DigitalProductPassport_cathode_instance.json
```

Each `diff` should produce no output. A non-empty diff means upstream republished the artefact at the production mirror without re-tagging — open an issue with UN/CEFACT and re-pin the registry against the new bytes.

### Re-vendoring (when a new upstream tag lands)

1. Resolve the new tag's commit SHA (`curl -sL "https://opensource.unicc.org/api/v4/projects/62/repository/tags/<TAG>" | jq -r .commit.id`).
1. Run the fetch helper (or use the `/untp-bump <X.Y.Z>` Claude Code slash command, which scripts steps 2–4 of [docs/plans/UNTP_0.7.0_MIGRATION.md](../../../docs/plans/UNTP_0.7.0_MIGRATION.md) §7.2).
1. Re-compute SHA-256s and append a new section to this file.
1. Open a tracking PR linking back to the upstream tag.

### License

The UNTP specification artefacts are published by UN/CEFACT under [GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0.html) per the upstream repository. They are vendored here for **test fixture use only** under that licence — they are not redistributed inside the `dppvalidator` Python wheel. The vendored copies are read-only; modifications to the upstream content must happen upstream.
