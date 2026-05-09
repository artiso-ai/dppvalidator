# CIRPASS reference structure v1.3.0 — API reference

> **Status:** Final (Phase 8 finalisation, 2026-05-09). Generated
> from the Pydantic models at
> [`src/dppvalidator/models/cirpass/v1_3/`](https://github.com/artiso-ai/dppvalidator/tree/main/src/dppvalidator/models/cirpass/v1_3).

The CIRPASS reference structure v1.3.0 is the message-level wire
format that the CIRPASS-2 project publishes alongside the EUDPP
ontology. dppvalidator's Pydantic models are the source of truth;
the JSON Schema bundled at
[`schemas/data/cirpass-reference-1.3.0.json`](https://github.com/artiso-ai/dppvalidator/tree/main/src/dppvalidator/schemas/data/cirpass-reference-1.3.0.json)
is *derived* from them via
[`tools/codegen/cirpass/derive_schema.py`](https://github.com/artiso-ai/dppvalidator/tree/main/tools/codegen/cirpass/derive_schema.py).

## Reading guide

| Topic                   | Page                                                                    |
| ----------------------- | ----------------------------------------------------------------------- |
| Big-picture orientation | [`cirpass-2-alignment.md`](../../concepts/cirpass-2-alignment.md)       |
| EUDPP module changelog  | [`eudpp-1.9-changelog.md`](../../concepts/eudpp-1.9-changelog.md)       |
| UNTP ↔ CIRPASS mapping  | [`untp-cirpass-mapping.md`](../../concepts/untp-cirpass-mapping.md)     |
| Migration how-to        | [`migrate-untp-to-cirpass.md`](../../guides/migrate-untp-to-cirpass.md) |

## Root: `ReferencePassport`

The CIRPASS DPP reference structure root. Maps to `eudpp:DPP`
(P_DPP v1.9.1). Mirrors the v1.3.0 message tree-view shape: a
`Product` at the root + sibling fields for the DPP-level metadata.

::: dppvalidator.models.cirpass.v1_3.ReferencePassport
options:
show_source: false
show_bases: false

## Product / Identifier / Classification

::: dppvalidator.models.cirpass.v1_3.Product
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.Identifier
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.ClassificationCode
options:
show_source: false
show_bases: false

## Actor / Role

::: dppvalidator.models.cirpass.v1_3.Actor
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.Facility
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.ActorRole
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.ActorRoleAssignment
options:
show_source: false
show_bases: false

## Material / Composition

::: dppvalidator.models.cirpass.v1_3.Material
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.Composition
options:
show_source: false
show_bases: false

## Substances of Concern

::: dppvalidator.models.cirpass.v1_3.SubstanceOfConcern
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.Concentration
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.HazardClassification
options:
show_source: false
show_bases: false

## Life-Cycle Assessment

::: dppvalidator.models.cirpass.v1_3.LifeCycleAssessment
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.ImpactResult
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.ImpactCategoryReference
options:
show_source: false
show_bases: false

## Connector relations

::: dppvalidator.models.cirpass.v1_3.ConnectorRelation
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.RelationType
options:
show_source: false
show_bases: false

## Multilingual labels

::: dppvalidator.models.cirpass.v1_3.LocalisedText
options:
show_source: false
show_bases: false

## Temporal

::: dppvalidator.models.cirpass.v1_3.EffectivePeriod
options:
show_source: false
show_bases: false

::: dppvalidator.models.cirpass.v1_3.IssuedAt
options:
show_source: false
show_bases: false
