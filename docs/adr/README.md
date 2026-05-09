# Architecture Decision Records

This directory holds Architecture Decision Records (ADRs) — short
documents capturing single, durable decisions and the reasoning behind
them. The audience is the next engineer who has to extend this code in
six months without the meeting context.

## Conventions

- File naming: `NNNN-short-slug.md`, four-digit zero-padded sequential.
- Frontmatter fields: `Status`, `Date`, `Deciders` (when known),
  `Context`, `Decision`, `Consequences`, `Alternatives considered`.
- States: `Proposed` → `Accepted` → optionally `Superseded by ADR-NNNN`.
- One decision per ADR. If you find yourself making more than one
  decision, split it.
- Don't update an ADR's *content* once it's `Accepted`; instead, write a
  new ADR that supersedes it. ADRs are append-only history, not living
  docs.

When an ADR ships into a migration plan as a locked decision, the plan
references it (e.g. `D-0.1` in
[`../plans/CIRPASS_2_MIGRATION.md`](../plans/CIRPASS_2_MIGRATION.md)
points at [`0001-cirpass-json-schema-derivation.md`](0001-cirpass-json-schema-derivation.md)).

## Index

| #                                              | Title                                                                                | Status   | Related             |
| ---------------------------------------------- | ------------------------------------------------------------------------------------ | -------- | ------------------- |
| [0001](0001-cirpass-json-schema-derivation.md) | CIRPASS reference-structure JSON Schema is *derived* from the hub's tree-view export | Accepted | Plan D-0.1, Phase 3 |
| [0002](0002-canonical-eudpp-iri.md)            | EUDPP IRIs rebase to canonical `https://w3id.org/eudpp/`                             | Accepted | Plan D-0.3, Phase 1 |
| [0003](0003-tyre-license.md)                   | GDSO Tyre data-model license — provisional GPL-3.0                                   | Proposed | Plan OA-1, Phase 7  |
