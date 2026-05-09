# UNTP DPP 0.7.0 ↔ CIRPASS reference structure v1.3.0 mapping

> **Status:** Final (Phase 8 finalisation, 2026-05-09). The shim
> implementations and warning codes documented here are the public
> contract through Phase 10 of the migration plan.

Phase 5 of [docs/plans/CIRPASS_2_MIGRATION.md] introduces the
two-way compatibility shim between the UNTP DPP envelope and the
CIRPASS-2 reference-structure message. This document is the
**field-by-field lossless-subset reference**: it captures which
fields round-trip cleanly and which transformations are lossy.

> Looking for a *user-facing how-to*? See
> [`migrate-untp-to-cirpass.md`](../guides/migrate-untp-to-cirpass.md)
> for before/after JSON snippets and CLI invocations.

The shims live at:

- [src/dppvalidator/compat/untp_0_7_to_cirpass_1_3.py](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/untp_0_7_to_cirpass_1_3.py)
  — forward (UNTP → CIRPASS).
- [src/dppvalidator/compat/cirpass_1_3_to_untp_0_7.py](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/cirpass_1_3_to_untp_0_7.py)
  — reverse (CIRPASS → UNTP).
- [src/dppvalidator/compat/\_untp_cirpass_map.py](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/_untp_cirpass_map.py)
  — declarative step table (M01…M15) that this document mirrors.

## Warning codes

Five MAP-codes surface during a transformation; consumers may
pattern-match on them to decide whether a transformation is
acceptable for their use case.

| Code     | Meaning                                                             | Default severity |
| -------- | ------------------------------------------------------------------- | ---------------- |
| `MAP001` | Lossy: target shape drops information                               | `warning`        |
| `MAP002` | Synthesised: required field invented from a donor                   | `warning`        |
| `MAP003` | Unmapped: no rule applied; raw passthrough                          | `info`           |
| `MAP004` | Required-field-missing: source can't supply target's required field | `error`          |
| `MAP005` | Temporal collapse: less-expressive target temporal shape            | `warning`        |

`MAP00X` is distinct from `UPG00X` (intra-family upgrade); the two
warning kinds are kept as separate types so call sites can
pattern-match without conflating them.

## Step table

Each row is a single declarative transformation. Step IDs (`M01` …
`M15`) are stable across releases; MAP-warning `details["step"]`
references the ID so consumers can grep for the step that emitted
a warning.

| Step | Description                                       | UNTP path                                | CIRPASS path                            | Lossless? | Codes that may fire        |
| ---- | ------------------------------------------------- | ---------------------------------------- | --------------------------------------- | --------- | -------------------------- |
| M01  | DPP credential identifier ↔ DPP identifier object | `$.id`                                   | `$.dppIdentifier.value`                 | ✓         | `MAP002` `MAP004`          |
| M02  | Product credential subject ↔ root product         | `$.credentialSubject`                    | `$.product`                             | ✓         | `MAP004`                   |
| M03  | Product identifier scheme                         | `$.credentialSubject.idScheme`           | `$.product.productIdentifier.scheme`    | ✓         | `MAP003`                   |
| M04  | DPP envelope name (UNTP only)                     | `$.name`                                 | (not mapped)                            | ✗         | `MAP001`                   |
| M05  | Product name (UNTP scalar ↔ CIRPASS multilingual) | `$.credentialSubject.name`               | `$.product.productName`                 | ✗         | `MAP001` `MAP002`          |
| M06  | Product description (same i18n flatten as M05)    | `$.credentialSubject.description`        | `$.product.description`                 | ✗         | `MAP001` `MAP002`          |
| M07  | Issuance timestamp                                | `$.validFrom`                            | `$.issuedAt.timestamp`                  | ✓         | `MAP004`                   |
| M08  | Effective period                                  | `$.validFrom + $.validUntil`             | `$.effectivePeriod`                     | ✓         | `MAP005`                   |
| M09  | Commodity classification                          | `$.credentialSubject.productCategory`    | `$.product.commodityCode`               | ✗         | `MAP001` `MAP003`          |
| M10  | Material composition                              | `$.credentialSubject.materialProvenance` | `$.composition.materials`               | ✗         | `MAP001` `MAP002`          |
| M11  | Related parties / actors                          | `$.credentialSubject.relatedParty`       | `$.relatedActors`                       | ✗         | `MAP001` `MAP002` `MAP003` |
| M12  | Issuer ↔ manufacturer-role actor                  | `$.issuer`                               | `$.relatedActors[? role==Manufacturer]` | ✗         | `MAP001` `MAP002`          |
| M13  | Performance / LCA results                         | `$.credentialSubject.performanceClaim`   | `$.lca`                                 | ✗         | `MAP001` `MAP003`          |
| M14  | Substances of concern (CIRPASS-only)              | (no source field)                        | `$.substancesOfConcern`                 | ✗         | `MAP001`                   |
| M15  | Connector relations (CIRPASS-only)                | (no source field)                        | `$.connectorRelations`                  | ✗         | `MAP001`                   |

## Lossless subset

The following fields round-trip cleanly — that is,
`to_cirpass_1_3(to_untp_0_7(c))[0] == c` (and symmetrically) over
inputs constructed only from this subset:

- `dppIdentifier.value` ↔ `id`
- `product.productIdentifier.{value, scheme, schemeName}` ↔
  `credentialSubject.{id, idScheme.{id, name}}` *for schemes
  registered in the bundled lookup table*
- `issuedAt.timestamp` ↔ `validFrom`
- `effectivePeriod.{start, end}` ↔ `(validFrom, validUntil)` *when
  both endpoints are populated*
- Single-language `productName[0]` ↔ `name` *when language matches
  the caller's `default_language`*
- Single-language `description[0]` ↔ `description` *same caveat*
- A single related-actor with `ManufacturerRole` ↔ envelope
  `issuer` + a single relatedParty entry with role `manufacturer`

## Lossy transformations (MAP001 / MAP005)

The following transformations *cannot* round-trip without loss:

- **Multilingual labels (M05, M06, M09, M10, M11)** — UNTP carries
  scalar strings for `name` / `description` / `Classification.name`
  / `Material.name` / `Party.name`. The reverse direction picks the
  first list entry (or the entry whose language matches
  `default_language`) and emits one `MAP001` per dropped language.
- **Open-ended effective period (M08)** — UNTP `validUntil` may be
  absent; CIRPASS `effectivePeriod.end` is also optional, so this
  is reversible *if* the forward shim leaves end empty. When the
  forward shim *synthesises* an end (it doesn't currently), `MAP005`
  fires.
- **Performance claims (M13)** — UNTP `performanceClaim[]` carries
  rich claim structure (assessor, evidence, claimedBenchmark) that
  the CIRPASS `LifeCycleAssessment` does not model. The current
  shim drops claims wholesale with a single `MAP001`; Phase 7 pilot
  lifts cover the supported subset (PEF / EN 15804 LCA results).
- **Substances of concern (M14)** — CIRPASS-only; no UNTP base
  equivalent. The textile pilot extends UNTP with substance
  metadata (Phase 7 territory); the base shim drops with `MAP001`.
- **Connector relations (M15)** — CIRPASS-only construct. Drops
  with `MAP001`.

## Synthesised values (MAP002)

The forward shim synthesises values for fields CIRPASS requires
that the UNTP envelope can't supply directly. Each synthesised
value emits a `MAP002`; the caller can override by passing
keyword arguments to the shim:

- `dppIdentifier.scheme` — CIRPASS requires an http(s) URI; UNTP
  carries the credential id without a register URI. Default:
  `https://example.com/dpp-register/`.
- LocalisedText languages — UNTP scalar strings get wrapped as
  `[{value, language}]`; the language is the caller-supplied
  `default_language` (defaults to `"en"`).
- Manufacturer actor — when UNTP `relatedParty[]` doesn't include
  a manufacturer role, the forward shim lifts the envelope `issuer`
  into a synthesised actor with `eudpp:ManufacturerRole`.

The reverse shim synthesises values for fields UNTP requires that
CIRPASS doesn't carry directly:

- `idGranularity` — CIRPASS doesn't carry granularity; defaults to
  `"model"`. Caller can override via the `untp_id_granularity` kwarg.
- `producedAtFacility` — CIRPASS has no root-level facility; the
  reverse shim emits a placeholder.
- `countryOfProduction` — best-effort lift from the first
  material's `originCountry`; falls back to ISO `"ZZ"` (unknown)
  with a `MAP002` warning.
- `Material.materialType` — UNTP requires a Classification; CIRPASS
  carries a bare ISO 2076 code. Synthesised with scheme
  `https://w3id.org/eudpp#MaterialType`.
- `Material.massFraction` — UNTP requires a number; CIRPASS may
  omit it. Synthesised as `0.0` (caller must supply real values).

## Identifier scheme map

The bundled scheme map at
[src/dppvalidator/compat/\_identifier_schemes.py](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/_identifier_schemes.py)
covers commonly-seen identifier schemes for products, parties,
and facilities:

| UNTP `idScheme.id`                                                                                              | UNTP `idScheme.name` | CIRPASS `scheme` | Aliases recognised                                  |
| --------------------------------------------------------------------------------------------------------------- | -------------------- | ---------------- | --------------------------------------------------- |
| `https://gs1.org/voc/`                                                                                          | `GS1 GTIN`           | same             | `https://www.gs1.org/voc/`                          |
| `https://id.gs1.org/01/`                                                                                        | `GS1 Digital Link`   | same             | `https://gs1.org/dl/`                               |
| `https://www.gleif.org/lei/`                                                                                    | `GLEIF LEI`          | same             | `https://gleif.org/lei/`                            |
| `https://www.iso.org/standard/82220.html`                                                                       | `ISO/IEC 15459`      | same             | —                                                   |
| `https://ec.europa.eu/taxation_customs/dds2/eos/eori_home.jsp`                                                  | `EORI`               | same             | `https://ec.europa.eu/eori/`                        |
| `https://e-justice.europa.eu/topics/registers-business-insolvency-land/business-registers-search-company-eu_en` | `EUID`               | same             | `https://e-justice.europa.eu/euid/`                 |
| `https://www.dnb.com/duns-number.html`                                                                          | `DUNS`               | same             | `https://duns.com/`, `https://www.dnb.com/`         |
| `https://www.wcoomd.org/.../hs-nomenclature-2022-edition.aspx`                                                  | `WCO HS`             | same             | `https://www.wcoomd.org/`, `https://hs.wcoomd.org/` |
| `https://ec.europa.eu/taxation_customs/dds2/taric/`                                                             | `EU TARIC`           | same             | `https://ec.europa.eu/taric/`                       |
| `https://simap.ted.europa.eu/cpv`                                                                               | `EU CPV`             | same             | —                                                   |

Schemes outside this table pass through verbatim and surface as
`MAP003` (unmapped). Consumers can extend by passing the
`identifier_scheme_lookup` kwarg to either shim.

## Role enum mapping

UNTP `PartyRoleEnum` (20 members) ↔ EUDPP `EUDPPRoleClass`. The
forward map is many-to-one (e.g. UNTP `producer` and `manufacturer`
both project to `eudpp:ManufacturerRole`); the reverse map picks
the most-specific UNTP role.

| UNTP role                                                 | EUDPP role IRI                                     |
| --------------------------------------------------------- | -------------------------------------------------- |
| `manufacturer`, `producer`, `processor`, `brandOwner`     | `eudpp:ManufacturerRole`                           |
| `remanufacturer`                                          | `eudpp:RemanufacturerRole`                         |
| `recycler`                                                | `eudpp:RecyclerRole`                               |
| `importer`                                                | `eudpp:ImporterRole`                               |
| `distributor`                                             | `eudpp:DistributorRole`                            |
| `retailer`                                                | `eudpp:DealerRole`                                 |
| `logisticsProvider`, `carrier`                            | `eudpp:FulfilmentServiceProviderRole`              |
| `serviceProvider`                                         | `eudpp:DPPServiceProviderRole`                     |
| `inspector`, `certifier`                                  | `eudpp:ConformityAssessmentBodyRole`               |
| `regulator`                                               | `eudpp:AuthorityRole`                              |
| `owner`, `exporter`, `operator`, `consignor`, `consignee` | `eudpp:EconomicOperatorRole` (super-role fallback) |

EUDPP roles outside this table emit `MAP002` and fall back to
`eudpp:EconomicOperatorRole` (forward) / `manufacturer` (reverse).

## Property-test invariant

The Phase 5 property test
[tests/property/test_round_trip_invariants.py](https://github.com/artiso-ai/dppvalidator/blob/main/tests/property/test_round_trip_invariants.py)
exercises Hypothesis-generated payloads constrained to the
documented lossless subset. The invariant:

```text
to_cirpass_1_3(to_untp_0_7(c))[0] == c     # CIRPASS round-trip
to_untp_0_7(to_cirpass_1_3(u))[0] == u     # UNTP round-trip
```

200 examples per direction (Hypothesis default profile). Failures
surface as a counterexample showing the smallest input where the
identity breaks.
