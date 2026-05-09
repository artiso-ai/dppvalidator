# CIRPASS-2 alignment

> **Status:** Phase 8 reference (2026-05-09). Supersedes the legacy
> [`eudpp-ontology-alignment.md`](eudpp-ontology-alignment.md) — that
> page is now a redirecting stub and is removed in Phase 10 of the
> migration plan.

This page is the single orientation document for *what CIRPASS-2 is,
how dppvalidator implements it, and how it relates to UNTP DPP*. New
readers start here; the deep-dives below are linked rather than
inlined.

## What is CIRPASS-2?

CIRPASS-2 is the EU project that produces the **EU DPP Core
Ontology** (EUDPP) and a hierarchical **reference-structure message
format**. The ontology is a set of OWL modules describing what a
Digital Product Passport *means*; the reference structure is one
concrete wire format that publishers can emit.

The four canonical EUDPP modules dppvalidator bundles:

| Module | Version    | Description                                                   |
| ------ | ---------- | ------------------------------------------------------------- |
| P_DPP  | 1.9.1      | Product / DPP envelope and identifiers.                       |
| ACTOR  | 1.9.1      | Actors and roles (ESPR Art 2(37–55) economic operators).      |
| SOC    | 1.9.1      | Substances of Concern (REACH / SVHC tracking, ESPR Art 7(5)). |
| LCA    | 1.9.4-Maki | Life-Cycle Assessment (PEF 3.1 / EN 15804+A2).                |
| CON    | 1.9.1      | Cross-module connector relations.                             |
| CORE   | 1.9.1      | Integration ontology importing the five modules above.        |

Bundled TTLs live under
[`src/dppvalidator/vocabularies/data/ontologies/`](https://github.com/artiso-ai/dppvalidator/tree/main/src/dppvalidator/vocabularies/data/ontologies);
SHA-256 pins are recorded in
[`src/dppvalidator/schemas/data/MANIFEST.json`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/schemas/data/MANIFEST.json).

## Two families, one engine

dppvalidator validates **two parallel families**:

- **UNTP DPP** — the UN/CEFACT Verifiable-Credential message format.
  Versions 0.6.0, 0.6.1, 0.7.0 are bundled.
- **CIRPASS DPP reference structure v1.3.0** — the CIRPASS-2 message
  format. Pydantic-first JSON Schema derived in Phase 3.

EUDPP-LD is *not* a third family — it's a serialization layer that
re-keys either family's payload onto canonical EUDPP class IRIs.

The engine routes payloads through family-specific pipelines:

```
UNTP    : schema → model → semantic → JSON-LD → vocabulary → plugin → signature
CIRPASS : schema → model → semantic → SHACL    → vocabulary → plugin
```

Detection is **automatic by default** but explicit override is
supported via `--target {auto,untp,cirpass}` (Phase 6). Mismatch
between the user's target and the detected family fails fast with
`DET001` and exit code 3.

## Validator surface

Each family ships its own rule tree with non-colliding code prefixes:

| Family          | Prefix | Owns                                                                                |
| --------------- | ------ | ----------------------------------------------------------------------------------- |
| UNTP            | `SEM`  | Base semantic rules (mass-fraction sum, validity dates, hazardous-material safety). |
| UNTP            | `VOC`  | Vocabulary-driven rules (country codes, units, HS codes, GTIN).                     |
| UNTP            | `CQ`   | CIRPASS Quality rules — pre-CIRPASS-2 ESPR-compliance heuristics.                   |
| UNTP            | `JLD`  | JSON-LD shape rules.                                                                |
| UNTP            | `MDL`  | Pydantic model failures.                                                            |
| UNTP            | `VER`  | Version-mismatch errors.                                                            |
| UNTP            | `UPG`  | 0.6 → 0.7 upgrade-shim warnings.                                                    |
| CIRPASS         | `CR`   | Reference-structure base rules.                                                     |
| CIRPASS         | `SUB`  | SOC v1.9.1 axioms.                                                                  |
| CIRPASS         | `LCS`  | LCA v1.9.4-Maki axioms.                                                             |
| CIRPASS         | `ACT`  | ACTOR v1.9.1 axioms.                                                                |
| CIRPASS         | `REL`  | Connector / relation axioms.                                                        |
| Cross-family    | `MAP`  | UNTP ↔ CIRPASS mapping warnings.                                                    |
| Cross-family    | `DET`  | Family-detection diagnostics.                                                       |
| Pilot (textile) | `TXT`  | Textile DPP rules — v1 (legacy) / v2 (MVP Textile DPP 2025-12-04).                  |
| Pilot (tyres)   | `TYR`  | GDSO declaration rules.                                                             |

Per-rule documentation lives under [`docs/errors/`](../errors/index.md).

## Pilot profiles

Phase 7 introduced *profile-keyed dispatch* so pilot-specific rule
packs swap in via `validate --profile <name>`:

- `textile-v1` — legacy TXT001…TXT005 rules (info / warning).
- `textile-v2` — MVP Textile DPP v2 (2025-12-04) pack: TXT001…TXT007
  with stricter severity (TXT006 recycled-content, TXT007 repair
  info). See
  [`src/dppvalidator/validators/rules/v0_7/textile_v2.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/rules/v0_7/textile_v2.py).

The tyres pilot ships out-of-tree as the
[`dppvalidator-tyres`](../plugins/tyres.md) plugin (GPL-3.0-or-later;
Pre-1.0 / Experimental); install separately to activate.

## Cross-family mapping

UNTP and CIRPASS messages can be projected onto each other via the
[Phase 5 compat shims](untp-cirpass-mapping.md):

- `dppvalidator.compat.to_cirpass_1_3(untp_dict)` — forward.
- `dppvalidator.compat.to_untp_0_7(cirpass_dict)` — reverse.

The lossless subset (round-trip identity-preserving) is documented
inline in the mapping doc; transformations outside the subset emit
`MAP00X` warnings:

| Code     | Meaning                                            |
| -------- | -------------------------------------------------- |
| `MAP001` | Lossy: target shape drops information.             |
| `MAP002` | Synthesised: required field invented from a donor. |
| `MAP003` | Unmapped: passthrough (no rule applied).           |
| `MAP004` | Required-field-missing.                            |
| `MAP005` | Temporal collapse (less-expressive target).        |

## Reading path

| You want…                           | Read this                                                                                |
| ----------------------------------- | ---------------------------------------------------------------------------------------- |
| The big picture                     | this page                                                                                |
| The migration story                 | [`docs/plans/CIRPASS_2_MIGRATION.md`](../plans/CIRPASS_2_MIGRATION.md) (engineering log) |
| EUDPP module changelog              | [eudpp-1.9-changelog.md](eudpp-1.9-changelog.md)                                         |
| Field-by-field UNTP↔CIRPASS mapping | [untp-cirpass-mapping.md](untp-cirpass-mapping.md)                                       |
| Migrate a UNTP fixture to CIRPASS   | [migrate-untp-to-cirpass.md](../guides/migrate-untp-to-cirpass.md)                       |
| CIRPASS Pydantic model API          | [reference/cirpass/](../reference/cirpass/index.md)                                      |
| CLI exit codes                      | [reference/cli/exit-codes.md](../reference/cli/exit-codes.md)                            |
| Per-rule errors                     | [errors/](../errors/index.md)                                                            |
| Tyres pilot plugin                  | [plugins/tyres.md](../plugins/tyres.md)                                                  |

## Architecture decisions

The Phase 0 decision log captures the load-bearing choices:

- [ADR 0001](../adr/0001-cirpass-json-schema-derivation.md) — JSON
  Schema derivation strategy (Pydantic-first vs hub tree-view).
- [ADR 0002](../adr/0002-canonical-eudpp-iri.md) — Canonical EUDPP
  IRI rebase to W3ID.
- [ADR 0003](../adr/0003-tyre-license.md) — Tyre plugin licensing
  (GPL-3.0-or-later).
- [ADR 0004](../adr/0004-textile-v2-built-in.md) — Textile v2 ships
  as a built-in profile rather than an out-of-tree plugin.
- [ADR 0005](../adr/0005-cli-exit-codes.md) — Six-code CLI exit
  surface (Phase 6 §6.7).

## Spec snapshot

Phase 0 of the migration plan vendored a frozen snapshot of the
CIRPASS-2 hub artefacts. See
[cirpass-2-spec-snapshot.md](cirpass-2-spec-snapshot.md) for the
provenance of every bundled file (URL + SHA-256 + pull date).
