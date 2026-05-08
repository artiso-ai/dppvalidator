<!-- markdownlint-disable MD013 MD060 -->

# Migrating UNTP DPP payloads from 0.6.x to 0.7.0

UNTP DPP **0.7.0** restructures several core fields. dppvalidator
ships a **compat shim** (`dppvalidator.compat.upgrade_0_6_to_0_7`)
that rewrites a 0.6.x payload into 0.7.0 shape and emits structured
warnings for anything it can't fully translate.

This guide covers:

1. How to run the shim from the CLI and Python.
1. The complete field rename / shape-change table.
1. The four warning codes and what they mean.
1. The documented limitations (fields that need manual intervention).

The conceptual overview of UNTP version handling lives in
[UNTP DPP versions](../concepts/untp-versions.md).

## When you need this

You need this guide if you:

- have v0.6.x payloads and want to publish them as v0.7.0,
- have a pipeline that validates v0.6.x today and want to switch the
  validation target without re-issuing every passport, or
- are authoring a new v0.7.0 payload and want a quick reference for
  what changed.

If you're authoring fresh v0.7.0 payloads, skip to the
[field rename table](#field-rename-and-shape-change-table) and the
[`untp-versions`](../concepts/untp-versions.md) page.

## Quick start

### CLI: rewrite a single file

```bash
# Default — write to stdout, refuse if any warning fires.
dppvalidator migrate passport.json

# Write to an explicit output path.
dppvalidator migrate passport.json -o passport-v07.json

# Overwrite the input. Refuses on warnings unless --accept-warnings.
dppvalidator migrate passport.json --in-place

# Accept the upgrade even if warnings fire. Produces a sidecar
# passport-v07.json.warnings.json with the full warning list.
dppvalidator migrate passport.json -o passport-v07.json --accept-warnings
```

### CLI: validate-then-upgrade in one shot

```bash
# Run the shim, then validate the result against v0.7.0.
dppvalidator validate passport.json \
    --upgrade-from 0.6.1 \
    --schema-version 0.7.0
```

### Python API

```python
from dppvalidator.compat import upgrade

with open("passport.json") as f:
    src = json.load(f)

upgraded, warnings = upgrade(src, country_lookup={"DE": "Germany"})

for w in warnings:
    print(f"[{w.code}] ({w.severity.value}) {w.path}: {w.message}")
```

`upgrade()` is pure — it deep-copies its input, never mutates it.
The optional `country_lookup` populates `Country.countryName` for
ISO-3166-1 alpha-2 codes; codes outside the map fall back to
`{countryCode: …}` only.

## Field rename and shape-change table

The shim performs 17 transformation steps in a fixed order. The
most user-visible changes are summarised here; the full step-by-step
specification lives in
[`upgrade_0_6_to_0_7.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/upgrade_0_6_to_0_7.py).

### Envelope-level changes

| v0.6.x                                                                 | v0.7.0                                                        | Note                                                                                                             |
| ---------------------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `@context: ".../test.uncefact.org/vocabulary/untp/dpp/0.6.x/"`         | `@context: ".../vocabulary.uncefact.org/untp/0.7.0/context/"` | The W3C VC v2 context is preserved; only the UNTP entry is rewritten.                                            |
| `name`: optional                                                       | `name`: **required**                                          | Synthesised from `credentialSubject.product.name` when missing → `UPG002`.                                       |
| `validFrom`: optional                                                  | `validFrom`: **required**                                     | Cannot be synthesised — `UPG004` fires when missing.                                                             |
| `credentialSubject` is `ProductPassport` (envelope wrapping `Product`) | `credentialSubject` IS the `Product` directly                 | All `ProductPassport` siblings (claims, scorecards, materials, due-diligence) are folded onto the new `Product`. |

### Product-level renames

| v0.6.x                                             | v0.7.0                                                                  | Note                                                                                                            |
| -------------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `Product.serialNumber`                             | `Product.itemNumber`                                                    | Pure rename.                                                                                                    |
| `ProductPassport.granularityLevel`                 | `Product.idGranularity`                                                 | Carried up to the new `credentialSubject`.                                                                      |
| `ProductPassport.materialsProvenance[]`            | `Product.materialProvenance[]`                                          | Singular noun in v0.7.                                                                                          |
| `ProductPassport.dueDiligenceDeclaration: Link`    | `Product.relatedDocument[Link{name: "Due diligence declaration"}]`      | Folded into the unified `relatedDocument` array.                                                                |
| `Product.furtherInformation: Link[]`               | `Product.relatedDocument[]`                                             | Same target; existing `relatedDocument` entries are preserved and the legacy ones are appended.                 |
| `Product.producedByParty: Party`                   | `Product.relatedParty[PartyRole{role: "manufacturer", party: <party>}]` | Wrapped as a typed PartyRole. v0.7's `relatedParty` carries every supply-chain role, not just the manufacturer. |
| `Product.productCategory: Classification` (scalar) | `Product.productCategory: Classification[]`                             | Single-element array even when only one category is set.                                                        |
| `Product.registeredId`                             | _dropped_ — moves to `Party.registeredId`                               | The shim emits `UPG001`. Re-attach manually to the appropriate `relatedParty[*].party.registeredId` if needed.  |

### Per-claim changes

| v0.6.x                                                                | v0.7.0                                                                                                                     | Note                                                                                                              |
| --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `ProductPassport.conformityClaim[]`                                   | `Product.performanceClaim[]`                                                                                               | Plus the three v0.6 scorecards (emissions, circularity, traceability) are also folded here.                       |
| `Claim.assessmentDate`                                                | `Claim.claimDate`                                                                                                          | Field rename.                                                                                                     |
| `Claim.assessmentCriteria: Criterion[]`                               | `Claim.referenceCriteria: list[dict]`                                                                                      | The Criterion type is gone; entries are passed through as free-form objects.                                      |
| `Claim.declaredValue: Metric[]`                                       | `Claim.claimedPerformance: Performance[]`                                                                                  | Each `Metric` is split: `metricName` → `metric.name`, `metricValue` → `measure`, `score` → `score.code`.          |
| `Claim.conformityTopic: string`                                       | `Claim.conformityTopic: ConformityTopic[]`                                                                                 | Wrapped as a single-element list with `id`/`name` set to the original string.                                     |
| `Claim.conformityEvidence: SecureLink`                                | `Claim.evidence: Link[]`                                                                                                   | The dedicated `SecureLink` type is gone in v0.7; v0.7 `Link` absorbs `digestMultibase` + `mediaType`.             |
| `Claim.referenceStandard: Standard`                                   | `Claim.referenceStandard: list[dict]`                                                                                      | Scalar wrapped to a single-element list.                                                                          |
| `Claim.referenceRegulation: Regulation`                               | `Claim.referenceRegulation: list[dict]`                                                                                    | Same wrapping.                                                                                                    |
| `Claim.conformance: bool`                                             | _dropped_                                                                                                                  | No v0.7 equivalent at the top level.                                                                              |
| `EmissionsScorecard / CircularityScorecard / TraceabilityPerformance` | folded into `Claim` entries on `performanceClaim[]` with `conformityTopic` set to `Emissions`/`Circularity`/`Traceability` | Numeric scorecard fields become `claimedPerformance[].measure` entries; embedded Link fields become `evidence[]`. |

### Country / Material / Classification

| v0.6.x                                                                           | v0.7.0                                                              | Note                                                                                                                                                                             |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Product.countryOfProduction: "DE"`                                              | `Product.countryOfProduction: {countryCode: "DE", countryName?: …}` | `countryName` is optional; populate via `country_lookup={"DE": "Germany"}` when invoking the shim.                                                                               |
| `Material.originCountry: "DE"`                                                   | `Material.originCountry: Country`                                   | Same wrapping as above.                                                                                                                                                          |
| `Material.symbol: "<base64>"`                                                    | `Material.symbol: Image{name, imageData, mediaType}`                | Sentinel placeholders (`"undefined"`, etc.) are dropped with `UPG001`. Real base64 is upgraded with synthesised `name="Material symbol"` and `mediaType="image/png"` (`UPG002`). |
| `Material.materialType: Classification` (optional)                               | `Material.materialType: Classification` (**required**)              | When missing, the shim emits `UPG004`; provide manually.                                                                                                                         |
| `Material.massFraction: float` (optional)                                        | `Material.massFraction: float` (**required**)                       | Same: `UPG004` fires when missing.                                                                                                                                               |
| `Classification.schemeID`                                                        | `Classification.schemeId`                                           | camelCase fix; renamed everywhere recursively.                                                                                                                                   |
| Embedded `type: [...]` arrays on `Dimension`, `Characteristics`, `Measure`, etc. | _stripped_                                                          | v0.7 schema dropped these discriminators; the shim removes them.                                                                                                                 |

## Warning codes

Every transformation that can't translate cleanly emits a structured
`UpgradeWarning` with one of four codes:

| Code     | Severity       | Meaning                                                                                                                                                                                                                                                                                                                                |
| -------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `UPG001` | warning        | **Lossy** — a v0.6 field has no v0.7 equivalent. Examples: `Product.registeredId` dropped; sentinel `Material.symbol` strings dropped.                                                                                                                                                                                                 |
| `UPG002` | info / warning | **Synthesised** — the shim filled a missing field from another source. Examples: `name` synthesised from `Product.name`; `Material.symbol` upgraded to a v0.7 `Image` with synthesised `name` and `mediaType`. `INFO` severity for "country name not synthesised because no `country_lookup`"; `WARNING` for envelope-level synthesis. |
| `UPG003` | warning        | **Unmapped country** — a country code is not in the bundled ISO-3166-1 list. The shim still wraps the value structurally, but it will fail v0.7 validation.                                                                                                                                                                            |
| `UPG004` | error          | **Required field missing** — a field that v0.7 requires is missing from the v0.6 source and the shim cannot synthesise it. The caller MUST provide the value before the upgraded payload validates. Examples: `validFrom`, `Material.materialType`, `Material.massFraction`.                                                           |

The `migrate` CLI refuses to write the output file when any
warning- or error-severity event fires; pass `--accept-warnings` to
override. INFO-severity events never block. A sidecar
`<output>.warnings.json` is always written alongside any blocking-warning
output (whether or not the main file is written) so the caller has a
machine-readable record.

## Documented limitations

These v0.6.x payloads cannot fully round-trip through the shim; each
case is intentional and surfaces as one of the warnings above:

| Limitation                                                        | Code             | What to do                                                                                                                                                                                    |
| ----------------------------------------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Product.registeredId` set                                        | `UPG001`         | Move the value to `Product.relatedParty[*].party.registeredId` on the appropriate party (typically the manufacturer). The shim drops it because the field's home moved from Product to Party. |
| `Material.materialType` missing                                   | `UPG004`         | v0.7 makes `materialType` required. Supply a `Classification` (e.g. `{schemeId: ".../cpc/", schemeName: "UN CPC", code: "12345", name: "..."}`).                                              |
| `Material.massFraction` missing                                   | `UPG004`         | v0.7 makes `massFraction` required. Supply a numeric value in `[0, 1]`.                                                                                                                       |
| Top-level `name` missing AND `Product.name` missing               | `UPG004`         | Provide a top-level `name` manually. The shim only synthesises from the inner `Product.name`.                                                                                                 |
| Top-level `validFrom` missing                                     | `UPG004`         | Add a real `validFrom` timestamp; the shim cannot fabricate a date.                                                                                                                           |
| `Material.symbol` is a non-base64 string                          | `UPG001`         | Provide a v0.7 `Image` object with `name`, `imageData` (base64), and `mediaType`. The shim drops anything that doesn't decode as base64.                                                      |
| Country code not in bundled ISO-3166-1 list                       | `UPG003`         | The shim wraps it structurally as `{countryCode: "XX"}`, but v0.7 model validation rejects non-ISO codes. Fix the source data.                                                                |
| Bare `ProductPassport` payload (no W3C VC envelope)               | _shim no-ops_    | The shim is defined for full DPP envelopes; bare `ProductPassport` payloads were never valid v0.6 wire format. Wrap in a VC envelope first.                                                   |
| Domain-specific industry extensions (e.g. textiles plugin fields) | _passes through_ | Extension fields under `Characteristics` flow through (`extra="allow"`) but their internal shape isn't migrated. Verify against your plugin's v0.7 documentation.                             |

## Round-trip verification

The repository includes
[`tests/integration/test_compat_roundtrip.py`](https://github.com/artiso-ai/dppvalidator/blob/main/tests/integration/test_compat_roundtrip.py),
which upgrades every enveloped 0.6.x fixture under
`tests/fixtures/valid/` and asserts the result either validates
cleanly against the v0.7 model or surfaces an explanatory warning.
A silent failure (no warning, no validation pass) trips the assertion
immediately.

If you build a CI check around the shim, mirror that contract:
**fail loudly when an upgrade produces an invalid payload AND no
warning explains why.**

## See also

- [UNTP DPP versions](../concepts/untp-versions.md) — overall version
  handling, default version, detection rules.
- [Five-layer validation](../concepts/validation-layers.md) — how the
  upgraded payload then flows through validation.
- [`upgrade_0_6_to_0_7.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/upgrade_0_6_to_0_7.py)
  — full implementation of the 17 transformation steps.
- [Migration plan archive](https://github.com/artiso-ai/dppvalidator/blob/main/docs/plans/UNTP_0.7.0_MIGRATION.md) — Phase 4
  (compat shim) is the canonical engineering record.
