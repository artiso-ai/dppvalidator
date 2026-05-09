# `tools/codegen/cirpass/` — CIRPASS-2 codegen tooling

Workstream X1 of [`docs/plans/CIRPASS_2_MIGRATION.md`](../../../docs/plans/CIRPASS_2_MIGRATION.md).

This directory holds **pure code generators** that produce Python
artefacts from vendored CIRPASS-2 TTL ontologies. Each tool emits a
deterministic, hash-pinned output so a second run on the same input
reproduces byte-identical Python.

## Files

| File                  | Purpose                                                                                                                                                                    |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `regenerate_enums.py` | Phase 1 tasks 1.7–1.11 — regenerate `EUDPPClass` / `EUDPPActorClass` / `EUDPPRoleClass` / `LCAClass` / `EUDPPObjectProperty` / `EUDPPDatatypeProperty` from a vendored TTL |
| `derive_schema.py`    | Phase 3 task 3.1 — derive `cirpass-reference-1.3.0.json` from the hub's tree-view export *(scaffold lands when Phase 1.1 unblocks)*                                        |
| `README.md`           | This file                                                                                                                                                                  |

The drift gate `tools/codegen/check_drift.py` (Phase 3 task 3.13) wraps
all generators so CI fails when a regenerated artefact differs from the
committed source.

## `regenerate_enums.py`

```bash
uv run --extra rdf python tools/codegen/cirpass/regenerate_enums.py \
    --ttl <TTL_PATH> \
    --target {class|object-property|datatype-property} \
    --namespace <IRI_PREFIX> \
    --prefix <COMPACT_PREFIX> \
    --enum-name <PYTHON_CLASS_NAME> \
    --enum-doc "<DOCSTRING>"
```

Output: a complete `class Foo(str, Enum)` block on stdout, with a
`# generated-from: <ttl-path>@<sha256>` header. Paste-replace the
existing class body in `src/dppvalidator/vocabularies/eudpp_*.py`.

### Canonical invocations for Phase 1 tasks 1.7–1.11

Once Phase 1 task 1.1 vendors the v1.9.1 TTLs, the operator runs each of:

```bash
# Task 1.7 — EUDPPClass against P_DPP v1.9.1
uv run --extra rdf python tools/codegen/cirpass/regenerate_enums.py \
    --ttl src/dppvalidator/vocabularies/data/ontologies/product_dpp_v1.9.1.ttl \
    --target class \
    --namespace https://w3id.org/eudpp/p_dpp/ \
    --prefix p_dpp \
    --enum-name EUDPPClass \
    --enum-doc "EU DPP Core Ontology class URIs (P_DPP module v1.9.1)."

# Task 1.8 — EUDPPActorClass + EUDPPRoleClass against ACTOR v1.9.1
# (run twice with different --enum-name; the file lifts both)
uv run --extra rdf python tools/codegen/cirpass/regenerate_enums.py \
    --ttl src/dppvalidator/vocabularies/data/ontologies/actors_roles_v1.9.1.ttl \
    --target class \
    --namespace https://w3id.org/eudpp/actor/ \
    --prefix actor \
    --enum-name EUDPPActorClass \
    --enum-doc "EU DPP ACTOR module class URIs (v1.9.1)."

# Task 1.9 — substance enums against SOC v1.9.1
# (HazardCategory and LifeCycleStage are *value enums* not IRI enums,
#  so they are NOT regenerated — only EUDPPSubstanceClass is.)
uv run --extra rdf python tools/codegen/cirpass/regenerate_enums.py \
    --ttl src/dppvalidator/vocabularies/data/ontologies/soc_v1.9.1.ttl \
    --target class \
    --namespace https://w3id.org/eudpp/soc/ \
    --prefix soc \
    --enum-name EUDPPSubstanceClass \
    --enum-doc "EU DPP SOC module class URIs (v1.9.1)."

# Task 1.10 — LCAClass against LCA v1.9.4-Maki
uv run --extra rdf python tools/codegen/cirpass/regenerate_enums.py \
    --ttl src/dppvalidator/vocabularies/data/ontologies/lca_v1.9.4_Maki.ttl \
    --target class \
    --namespace https://w3id.org/eudpp/lca/ \
    --prefix lca \
    --enum-name LCAClass \
    --enum-doc "EU DPP LCA module class URIs (v1.9.4-Maki)."

# Task 1.11 — EUDPPObjectProperty + EUDPPDatatypeProperty against CORE + CON
# (run twice per file; concatenate output if a single class spans modules)
uv run --extra rdf python tools/codegen/cirpass/regenerate_enums.py \
    --ttl src/dppvalidator/vocabularies/data/ontologies/eudpp_core_v1.9.1.ttl \
    --target object-property \
    --namespace https://w3id.org/eudpp/ \
    --prefix eudpp \
    --enum-name EUDPPObjectProperty \
    --enum-doc "EU DPP CORE object properties (v1.9.1)."

uv run --extra rdf python tools/codegen/cirpass/regenerate_enums.py \
    --ttl src/dppvalidator/vocabularies/data/ontologies/connector_v1.9.1.ttl \
    --target object-property \
    --namespace https://w3id.org/eudpp/con/ \
    --prefix con \
    --enum-name CONObjectProperty \
    --enum-doc "EU DPP CON module object properties (v1.9.1)."
```

### Annotation step (manual, after regeneration)

The plan calls for `# +1.9.1` / `# −1.9.1` markers on members
added/removed since the previous TTL version. Since the codegen output
is already sorted alphabetically, this is a one-shot `git diff` task:

```bash
git diff --no-index <(git show HEAD:src/.../eudpp_classes.py) \
    src/dppvalidator/vocabularies/eudpp_classes.py
```

Members in the `+` lines that don't exist in HEAD get `# +1.9.1`;
members in `-` lines that don't exist in the new file get a tombstone
comment `# −1.9.1 (was: <local_name>)` adjacent to the closest
remaining alphabetical neighbour, or are simply dropped if the
deprecation has already played out.

### Determinism guarantees

- TTL parsed by `rdflib`; member iteration order is *not* the TTL
  source order. We sort by Python identifier so output is independent
  of `rdflib`'s internal hash seed.
- Hashes are LF-normalised before SHA-256 (matches the project's
  manifest scheme).
- `rdfs:label` (English-tagged, falling back to untagged) is appended
  as a Python-comment trailer for human readability; only used as a
  hint, never as part of the enum value.

## Why this lives outside `src/`

The cardinal rule from
[`.claude/rules/untp-versioning.md`](../../../.claude/rules/untp-versioning.md)
is that vendored data and the validator source are separately
hashed-and-pinned. Generators are *production tooling* but not part of
the runtime wheel — they run at TTL-vendor time and at CI-drift-check
time. Keeping them in `tools/codegen/` mirrors the existing
`tools/snapshot/` discipline (Phase 0).
