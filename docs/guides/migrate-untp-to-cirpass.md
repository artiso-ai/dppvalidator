<!-- markdownlint-disable MD013 MD060 -->

# Migrating from UNTP DPP 0.7.0 to CIRPASS reference structure v1.3.0

UNTP DPP and the CIRPASS-2 reference-structure message are two
different *families* of DPP payload, not two versions of the same
format. dppvalidator ships **two-way compat shims** that project
between them:

- `dppvalidator.compat.to_cirpass_1_3` — forward (UNTP → CIRPASS).
- `dppvalidator.compat.to_untp_0_7` — reverse (CIRPASS → UNTP).

The shims are *lossy outside a documented subset*. This guide:

1. Shows how to run them from the CLI and Python.
1. Walks through a before/after JSON example.
1. Lists the five `MAP00X` warning codes and what they mean.
1. Captures the round-trip identity (lossless subset) so you know
   what survives a forward+reverse cycle.

The conceptual overview lives at
[`cirpass-2-alignment.md`](../concepts/cirpass-2-alignment.md); the
complete field-by-field mapping table is at
[`untp-cirpass-mapping.md`](../concepts/untp-cirpass-mapping.md).

## When you need this

- You have UNTP 0.7.0 DPPs in production and a downstream consumer
  asks for CIRPASS-shaped output.
- You're publishing CIRPASS reference-structure messages and want
  to convert them to UNTP 0.7.0 for a UN/CEFACT-side workflow.
- You want to add a CIRPASS-side validation pass to an existing
  UNTP pipeline without re-authoring fixtures.

## Quick start

### CLI — UNTP → CIRPASS

```bash
# Project a UNTP 0.7.0 payload onto CIRPASS reference structure v1.3.0.
# Default refuses to write when warnings fire.
dppvalidator migrate untp-passport.json --to cirpass-1.3 -o cirpass.json

# Accept lossy/synthesis warnings and proceed. The sidecar
# cirpass.json.warnings.json captures every MAP00X warning.
dppvalidator migrate untp-passport.json \
    --to cirpass-1.3 \
    -o cirpass.json \
    --accept-warnings

# Override the synthesised default language for multilingual labels:
dppvalidator migrate untp-passport.json --to cirpass-1.3 \
    -o cirpass.json --default-language de --accept-warnings
```

### CLI — CIRPASS → UNTP

```bash
# Project a CIRPASS payload onto UNTP 0.7.0 envelope.
dppvalidator migrate cirpass.json --to untp-0.7 -o untp.json --accept-warnings
```

> **Note:** The reverse direction (`--to untp-0.7`) is only available
> for CIRPASS *inputs* in Phase 5+. For UNTP 0.6 → 0.7 intra-family
> upgrades, the same `--to untp-0.7` flag still routes through the
> legacy v0.6 → v0.7 shim — see
> [migration-0-6-to-0-7.md](migration-0-6-to-0-7.md).

### CLI — JSON-LD export shortcut

If you don't need a sidecar JSON file but just want a CIRPASS-
shaped JSON-LD document, the export command does both the projection
and the JSON-LD wrapping in one step:

```bash
dppvalidator export untp-passport.json --format cirpass-jsonld > cirpass.jsonld
```

The exporter forwards mapping warnings to **stderr** so stdout stays
pipe-clean for `... | jq` consumers.

### Python

```python
import json
from dppvalidator.compat import to_cirpass_1_3, to_untp_0_7, MAP_CODE_LOSSY

untp_dict = json.load(open("untp-passport.json"))

# Forward
cirpass_dict, warnings = to_cirpass_1_3(
    untp_dict,
    default_language="en",
)

# Inspect warnings
for w in warnings:
    print(f"[{w.code}] {w.severity.value} {w.path}: {w.message}")

# Validate the projected output
from dppvalidator.models.cirpass.v1_3 import ReferencePassport

ReferencePassport.model_validate(cirpass_dict)

# Reverse
back, rev_warnings = to_untp_0_7(cirpass_dict, default_language="en")
```

## Before / after — minimal example

### UNTP 0.7.0 input

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://vocabulary.uncefact.org/untp/0.7.0/context/"
  ],
  "type": ["DigitalProductPassport", "VerifiableCredential"],
  "id": "https://example.com/dpp/CR-001",
  "name": "Cotton T-shirt DPP",
  "issuer": {
    "id": "https://example.com/lei/529900T8BM49AURSDO55",
    "name": "Example Apparel Ltd.",
    "type": ["CredentialIssuer"]
  },
  "validFrom": "2026-05-08T00:00:00+00:00",
  "validUntil": "2031-05-08T00:00:00+00:00",
  "credentialSubject": {
    "type": ["Product"],
    "id": "01234567890128",
    "name": "Cotton T-shirt",
    "idScheme": {"id": "https://gs1.org/voc/", "name": "GS1 GTIN"},
    "idGranularity": "model",
    "productCategory": [
      {
        "schemeId": "https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition.aspx",
        "schemeName": "WCO HS",
        "code": "61091000",
        "name": "T-shirts"
      }
    ],
    "producedAtFacility": {"id": "https://example.com/f", "name": "F", "type": ["Facility"]},
    "countryOfProduction": {"countryCode": "DE", "countryName": "Germany"},
    "materialProvenance": [
      {
        "name": "Cotton",
        "originCountry": {"countryCode": "DE"},
        "materialType": {
          "schemeId": "https://w3id.org/eudpp#MaterialType",
          "schemeName": "ISO 2076",
          "code": "CO",
          "name": "Cotton"
        },
        "massFraction": 1.0
      }
    ]
  }
}
```

### CIRPASS reference structure v1.3.0 output (after `to_cirpass_1_3`)

```json
{
  "dppIdentifier": {
    "value": "https://example.com/dpp/CR-001",
    "scheme": "https://example.com/dpp-register/",
    "schemeName": "DPP register"
  },
  "product": {
    "productIdentifier": {
      "value": "01234567890128",
      "scheme": "https://gs1.org/voc/",
      "schemeName": "GS1 GTIN"
    },
    "productName": [
      {"value": "Cotton T-shirt", "language": "en"}
    ],
    "commodityCode": [
      {
        "code": "61091000",
        "scheme": "https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition.aspx",
        "name": [{"value": "T-shirts", "language": "en"}]
      }
    ]
  },
  "issuedAt": {"timestamp": "2026-05-08T00:00:00+00:00"},
  "effectivePeriod": {
    "start": "2026-05-08T00:00:00+00:00",
    "end": "2031-05-08T00:00:00+00:00"
  },
  "composition": {
    "materials": [
      {
        "materialName": [{"value": "Cotton", "language": "en"}],
        "materialType": "CO",
        "originCountry": "DE",
        "massFraction": "1.0"
      }
    ]
  },
  "relatedActors": [
    {
      "actor": {
        "actorIdentifier": {
          "value": "https://example.com/lei/529900T8BM49AURSDO55",
          "scheme": "https://www.gleif.org/lei/",
          "schemeName": "GLEIF LEI"
        },
        "actorName": [{"value": "Example Apparel Ltd.", "language": "en"}]
      },
      "role": "eudpp:ManufacturerRole"
    }
  ]
}
```

### Warnings emitted on the projection

The forward shim emits five `MAP002` warnings on this payload — one
for each synthesised value (DPP-register scheme URI; the language
tag on every LocalisedText entry the shim wraps; a manufacturer
actor lifted from `issuer`).

```text
[MAP002] (warning) $.dppIdentifier.scheme: DPP-register scheme synthesised — UNTP carries the credential id but no register URI; using a placeholder.
[MAP002] (warning) $.product.productName[0].language: UNTP credentialSubject.name is a scalar string; synthesised a single CIRPASS LocalisedText entry with language='en'.
[MAP002] (warning) $.product.commodityCode[0].name[0].language: UNTP Classification.name is a scalar string; projected onto a single LocalisedText with language='en'.
[MAP002] (warning) $.composition.materials[0].materialName[0].language: UNTP Material.name is a scalar string; projected onto a single LocalisedText with language='en'.
```

The shim does **not** synthesise content (e.g. the recycled-mass
fraction is absent on the input, so it's absent on the output).

## Warning codes

The five `MAP00X` codes the shim may emit:

| Code     | Meaning                                                                                                                                                                                                          | Default severity |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| `MAP001` | **Lossy** — target shape drops information. Examples: dropping a non-default-language LocalisedText entry; dropping CIRPASS-only fields (`substancesOfConcern`, `connectorRelations`, `lca`) on the reverse leg. | `warning`        |
| `MAP002` | **Synthesised** — required field invented from a donor (e.g. wrapping a UNTP scalar name in a single-entry LocalisedText).                                                                                       | `warning`        |
| `MAP003` | **Unmapped** — passthrough (no rule applied). Fires when the input carries a scheme URI / role IRI / etc. that's not in the bundled lookup table.                                                                | `info`           |
| `MAP004` | **Required-field-missing** — the source cannot supply a field the target requires. The output will *not* validate against the target Pydantic model until you fill the field in.                                 | `error`          |
| `MAP005` | **Temporal collapse** — less-expressive target temporal shape (e.g. `validUntil` absent ⇒ `effectivePeriod.end` left empty).                                                                                     | `warning`        |

## Lossless subset

The following fields round-trip identity-preserving — pass through
both shims unchanged when the input only contains them:

- `dppIdentifier.value` ↔ `id`
- `product.productIdentifier.{value, scheme, schemeName}` ↔
  `credentialSubject.{id, idScheme.{id, name}}` *for schemes
  registered in the bundled lookup table*
- `issuedAt.timestamp` ↔ `validFrom`
- `effectivePeriod.{start, end}` ↔ `(validFrom, validUntil)` *when
  both endpoints populate*
- Single-language `productName[0]` ↔ `name` *when language matches
  the caller's `default_language`*
- A single related-actor with `ManufacturerRole` ↔ envelope
  `issuer` + a single `relatedParty` entry with role
  `manufacturer`

The Hypothesis property test at
[`tests/property/test_round_trip_invariants.py`](https://github.com/artiso-ai/dppvalidator/tree/main/tests/property/test_round_trip_invariants.py)
exercises this invariant against 200 generated examples per direction.

## Limitations

The shim *will not*:

- Synthesise content the input doesn't carry. Missing
  `producedAtFacility` becomes a placeholder; missing
  `materialType.code` becomes `"unspecified"`.
- Translate UNTP `performanceClaim` entries into CIRPASS LCA
  results. The Phase 7 textile-v2 pilot extends this for the
  microplastic / durability / recycled-content topics, but the
  base shim drops every claim with a single `MAP001`.
- Translate CIRPASS `substancesOfConcern` into a UNTP base
  representation — there isn't one. Use the `dppvalidator-textiles`
  plugin (when published) for textile-side substance tracking.

## Round-trip identity check

The forward shim is *idempotent* over the lossless subset, but a
forward+reverse cycle on a non-subset payload will not recover the
original. If you want to verify round-trip behaviour for your
specific input shape, run:

```python
import json
from dppvalidator.compat import to_cirpass_1_3, to_untp_0_7

untp = json.load(open("untp.json"))
cirpass, _ = to_cirpass_1_3(untp)
recovered, _ = to_untp_0_7(cirpass)

# Compare the lossless-subset fields
assert recovered["id"] == untp["id"]
assert recovered["validFrom"] == untp["validFrom"]
assert recovered.get("validUntil") == untp.get("validUntil")
assert recovered["credentialSubject"]["id"] == untp["credentialSubject"]["id"]
```

## See also

- [`untp-cirpass-mapping.md`](../concepts/untp-cirpass-mapping.md) —
  field-by-field mapping table.
- [`cirpass-2-alignment.md`](../concepts/cirpass-2-alignment.md) —
  big-picture orientation.
- [`migration-0-6-to-0-7.md`](migration-0-6-to-0-7.md) — UNTP
  intra-family upgrade (0.6 → 0.7).
- [CLI exit codes](../reference/cli/exit-codes.md).
