# ADR 0002 — EUDPP IRIs rebase to canonical `https://w3id.org/eudpp/`

**Status:** Accepted
**Date:** 2026-05-08
**Deciders:** dppvalidator maintainers (drafted during CIRPASS-2 migration planning)
**Migration-plan label:** D-0.3
**Related phases:** Phase 0 (verification), Phase 1 (rebase)

## Context

The EUDPP namespace constants in
[`src/dppvalidator/vocabularies/ontology.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/vocabularies/ontology.py)
bind EUDPP class IRIs to the *publishing host* of each module:

```python
class EUDPPNamespace(str, Enum):
    EUDPP = "http://dpp.taltech.ee/EUDPP#"  # TalTech publishes P_DPP / SOC / ACTOR / CON / CORE
    LCA = "http://dpp.cea.fr/EUDPP/LCA#"  # CEA France publishes LCA
    ...
```

These IRIs are accurate as *origin URLs* for the historic v1.7.1 / v2.0
TTL bytes — the bytes literally lived under those hosts.

The CIRPASS-2 v1.9.1 / v1.9.4.Maki release on the DPP Vocabulary Hub
declares a different identifier basis. The CORE umbrella module's
metadata (per <https://dpp.vocabulary-hub.eu/specifications>, 2026-05-08)
states:

> EUDPP CORE ontology maps the ontology modules by importing them.
> The imports are from `https://w3id.org/eudpp`.

`https://w3id.org/eudpp` is a *permanent identifier* (W3ID) that
redirects to whichever publisher hosts the bytes today. As of v1.9.1,
the canonical IRIs of the EUDPP modules are:

- `https://w3id.org/eudpp/` (CORE)
- `https://w3id.org/eudpp/p_dpp/`
- `https://w3id.org/eudpp/soc/`
- `https://w3id.org/eudpp/lca/`
- `https://w3id.org/eudpp/actor/`
- `https://w3id.org/eudpp/con/`

Continuing to emit `dpp.taltech.ee` / `dpp.cea.fr` IRIs from
`EUDPPJsonLDExporter` produces JSON-LD that downstream consumers cannot
dereference: the predicates point at non-canonical hosts. Linked-data
unification breaks.

## Decision

All EUDPP namespace bindings rebase onto the canonical
`https://w3id.org/eudpp/` prefix in Phase 1.

Specifically:

- `EUDPPNamespace.EUDPP` → `"https://w3id.org/eudpp/"`.
- `EUDPPNamespace.LCA` → `"https://w3id.org/eudpp/lca/"`.
- New per-module bindings added: `P_DPP`, `SOC`, `ACTOR`, `CON`.
- All 170 rows of `TERM_MAPPINGS` rebase predicate IRIs.
- The bundled `eudpp-context-v1.9.1.jsonld` carries the canonical IRIs.
- The legacy `CIRPASSNamespace = EUDPPNamespace` alias at
  [`vocabularies/ontology.py:59`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/vocabularies/ontology.py)
  is **deleted**: it conflated *messages* (CIRPASS) with *axioms*
  (EUDPP). Phase 3 introduces a distinct
  `CIRPASSMessageNamespace` if needed for the message-tree shape.
- Old IRIs remain registered in `exporters/contexts.py` for one release
  with a `DeprecationWarning`; removed in Phase 10.

A precondition gate runs in Phase 0:
`python tools/snapshot/fetch_cirpass.py --verify-canonical` HEAD-pings
each canonical IRI. Non-zero exit (R12 in the plan) blocks Phase 1
until the IRIs resolve, with two escalation paths:

1. The IRIs are not yet wired up by W3ID; coordinate upstream and
   wait. Phase 1 is paused.
1. The IRIs are intentionally different from what the spec page
   states; update this ADR with the corrected basis and re-run the
   gate.

## Consequences

**Positive**

- EUDPP-LD output is canonically dereferenceable.
- `MANIFEST.json` rows can carry a meaningful `canonical_iri` field
  separately from the (mutable) host URL the bytes were vendored from.
- Future re-publishings (TalTech → some new publisher; CEA → some new
  publisher) leave canonical IRIs unchanged.

**Negative**

- This is a coordinated rewrite, not a version bump. Phase 1's scope
  is larger than "refresh the TTLs"; it includes the IRI rebase across
  170 mapping rows, 5 enum modules, and the JSON-LD context.
- Downstream consumers that pinned the old `taltech.ee` / `cea.fr`
  IRIs break. We mitigate with a one-release deprecation window
  (`0.5.0` → `0.6.0`) and call out the change in
  [`docs/concepts/eudpp-1.9-changelog.md`](../concepts/eudpp-1.9-changelog.md).
- W3ID is a redirector, not a host. If the redirector is briefly down,
  consumers that follow the IRI lose the dereferencing path. This is a
  reliability concern for downstream code, not for our emission.

## Alternatives considered

- **Keep per-publisher IRIs.** Rejected: non-canonical; the spec
  declares a different basis; LD consumers fail.
- **Dual-emit both IRI sets** (legacy + canonical). Rejected: an LD
  document with two predicates for the same property is semantically
  ambiguous.
- **Defer the rebase to a later phase**, ship v1.9.1 axioms with old
  IRIs first. Rejected: produces a broken-by-design intermediate
  release; users would update and immediately get non-canonical
  emissions.

## Validation hooks

- `tools/snapshot/fetch_cirpass.py --verify-canonical` — Phase 0 task 0.4.
- `tests/unit/test_namespace_canonicality.py` (Phase 1) — every emitted
  EUDPP IRI starts with `https://w3id.org/eudpp/`; no `taltech.ee` /
  `cea.fr` references remain in the codebase.
- `tests/integration/test_eudpp_export_v1_9.py` (Phase 1) — golden-diff
  audit of EUDPP-LD output for the canonical v0.7 fixture.

## References

- [Migration plan §1.3 D-0.3](../plans/CIRPASS_2_MIGRATION.md)
- [Spec snapshot doc](../concepts/cirpass-2-spec-snapshot.md)
- W3ID: <https://w3id.org/>
- DPP Vocabulary Hub: <https://dpp.vocabulary-hub.eu/specifications>
