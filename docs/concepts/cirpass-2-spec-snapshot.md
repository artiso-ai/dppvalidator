# CIRPASS-2 spec snapshot

**Phase 0 deliverable** — task 0.6 of
[`../plans/CIRPASS_2_MIGRATION.md`](../plans/CIRPASS_2_MIGRATION.md).

This page is the authoritative answer to *"what CIRPASS-2 artefacts is
this library bundling, at which versions, with which integrity hashes?"*
It is updated whenever a snapshot row changes (Phase 1 vendor; Phase 10
removal). The `MANIFEST.json` rows under
[`../../src/dppvalidator/schemas/data/MANIFEST.json`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/schemas/data/MANIFEST.json)
are the machine-readable source of truth; this page is the human view.

## How this is maintained

1. The artefact set is defined in
   [`../../tools/snapshot/cirpass2_artefacts.json`](https://github.com/artiso-ai/dppvalidator/blob/main/tools/snapshot/cirpass2_artefacts.json).
1. The fetcher
   [`../../tools/snapshot/fetch_cirpass.py`](https://github.com/artiso-ai/dppvalidator/blob/main/tools/snapshot/fetch_cirpass.py)
   reads that file, downloads each artefact, computes an LF-normalised
   SHA-256, and emits MANIFEST-compatible rows.
1. The MANIFEST rows land in
   [`../../src/dppvalidator/schemas/data/MANIFEST.json`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/schemas/data/MANIFEST.json)
   in Phase 1.
1. This page mirrors the manifest rows for human eyes and adds the
   spec-listing context.

See [`../../tools/snapshot/README.md`](https://github.com/artiso-ai/dppvalidator/blob/main/tools/snapshot/README.md)
for the operator workflow.

## Source of truth

- **Spec listing:** <https://dpp.vocabulary-hub.eu/specifications>
- **Canonical IRI prefix (EUDPP):** `https://w3id.org/eudpp/`
- **CIRPASS-2 project:** <https://cirpass2.eu/>
- **Hub-export endpoints** (GUID-keyed; opaque):
  - `https://dpp.vocabulary-hub.eu/api/ontology/-/version/{guid}/export` — TTL
  - `https://dpp.vocabulary-hub.eu/api/json-schema/-/version/{guid}/export` — JSON Schema

## Snapshot v0 — drafted 2026-05-08

Status legend:

- **planned** — listed in `cirpass2_artefacts.json`; not yet fetched.
  GUID is a `TODO_*` placeholder pending operator pairing.
- **pinned** — fetched, SHA-256 computed, manifest row emitted.
- **vendored** — bundled bytes committed under
  `src/dppvalidator/vocabularies/data/ontologies/` and registered in
  `MANIFEST.json` (Phase 1 outcome).

### EUDPP Core Ontology modules (target Phase 1 vendoring)

| Module | Version    | Date       | Title                                            | Canonical IRI                   | Status  |
| ------ | ---------- | ---------- | ------------------------------------------------ | ------------------------------- | ------- |
| P_DPP  | 1.9.1      | 2026-03-04 | EUDPP CORE ontology Product and DPP module       | `https://w3id.org/eudpp/p_dpp/` | planned |
| SOC    | 1.9.1      | 2026-03-04 | EUDPP CORE ontology Substance of Concerns module | `https://w3id.org/eudpp/soc/`   | planned |
| LCA    | 1.9.4-Maki | 2026-04-27 | EUDPP Core Ontology Life Cycle Assessment module | `https://w3id.org/eudpp/lca/`   | planned |
| ACTOR  | 1.9.1      | 2026-03-04 | EUDPP Core Ontology ACTOR module                 | `https://w3id.org/eudpp/actor/` | planned |
| CON    | 1.9.1      | 2026-03-04 | EUDPP CORE ontology CONNECTOR module             | `https://w3id.org/eudpp/con/`   | planned |
| CORE   | 1.9.1      | 2026-03-04 | EUDPP Core Ontology (umbrella)                   | `https://w3id.org/eudpp/`       | planned |

> **D-0.3 verification gate.** Phase 0 task 0.4 runs
> `python tools/snapshot/fetch_cirpass.py --verify-canonical` to assert
> every IRI in this column dereferences. Failure escalates as Phase 1
> blocker R12.

### CIRPASS message (target Phase 3 derivation)

| Family    | Module | Version | Title                           | Format         | Status  |
| --------- | ------ | ------- | ------------------------------- | -------------- | ------- |
| `cirpass` | —      | 1.3.0   | CIRPASS DPP reference structure | tree-view-json | planned |

> **D-0.1.** The hub does *not* publish a JSON Schema for v1.3.0. Phase 3
> derives one (`tools/codegen/cirpass/derive_schema.py`) from the
> tree-view export and commits the result at
> `src/dppvalidator/schemas/data/cirpass-reference-1.3.0.json`. Drift is
> guarded by `tools/codegen/check_drift.py` (R14).

### CIRPASS-2 Pilot — Textile (target Phase 7)

| Family          | Module | Version | Date       | Title           | Format         | Status  |
| --------------- | ------ | ------- | ---------- | --------------- | -------------- | ------- |
| `textile-pilot` | —      | 2.0     | 2025-12-04 | MVP Textile DPP | tree-view-json | planned |

### CIRPASS-2 Pilot — Tyres (target Phase 7)

| Family       | Module                 | Version | Date       | Title                       | Format         | Status  |
| ------------ | ---------------------- | ------- | ---------- | --------------------------- | -------------- | ------- |
| `tyre-pilot` | GDSO_AMBASSADOR        | 1       | 2025-12-05 | GDSO Ambassador Data Models | json-schema    | planned |
| `tyre-pilot` | TYRE_LIFECYCLE_HISTORY | 1       | 2025-12-05 | Tyre Lifecycle History      | tree-view-json | planned |
| `tyre-pilot` | BIRTH                  | 0.9     | —          | Birth Declaration           | tree-view-json | planned |
| `tyre-pilot` | COLLECTION             | 0.1     | —          | Collection Declaration      | tree-view-json | planned |
| `tyre-pilot` | RETREAD                | 0.1     | —          | Retread Declaration         | tree-view-json | planned |
| `tyre-pilot` | RECYCLING              | 0.1     | —          | Recycling Declaration       | tree-view-json | planned |

> **OA-1.** GDSO Tyre data-model license is to be confirmed. Default
> assumption (until confirmed) is GPL-3.0, matching `plugins/textiles/`.
> Captured as ADR
> [`0003-tyre-license.md`](../adr/0003-tyre-license.md) in `Proposed`
> state until OA-1 closes; then promoted to `Accepted`.

## Reproducing the snapshot from a clean checkout

```bash
# (1) Inspect the planned set
python tools/snapshot/fetch_cirpass.py --list

# (2) Verify canonical IRIs (D-0.3 gate)
python tools/snapshot/fetch_cirpass.py --verify-canonical

# (3) Pair TODO_* GUIDs with hub GUIDs (manual; see tools/snapshot/README.md)

# (4) Re-run --list to confirm zero placeholders remain

# (5) Fetch + emit MANIFEST rows
python tools/snapshot/fetch_cirpass.py --fetch \
    > tools/snapshot/manifest-rows.json

# (6) Phase 1 picks up the rows from manifest-rows.json and folds them
#     into src/dppvalidator/schemas/data/MANIFEST.json, vendoring the
#     bytes into src/dppvalidator/vocabularies/data/ontologies/ along
#     the way.
```

The fetcher is stdlib-only — it runs from a fresh checkout without
`uv sync`. Verbatim downloads land under the gitignored
`tools/snapshot/cirpass-2/` directory; only the emitted MANIFEST rows
and the canonical bundled bytes are committed (in Phase 1).

## Snapshot history

| Snapshot | Drafted    | Vendored          | Notes                                                              |
| -------- | ---------- | ----------------- | ------------------------------------------------------------------ |
| v0       | 2026-05-08 | (pending Phase 1) | Initial draft. 14 artefacts planned, 0 GUIDs paired, 0 SHAs pinned |

This row gets its `Vendored` cell filled when Phase 1 closes. Subsequent
snapshots (v1, v2, …) bump when any artefact changes version or hash.

## Related decisions

- [ADR 0001 — CIRPASS JSON Schema derivation](../adr/0001-cirpass-json-schema-derivation.md)
- [ADR 0002 — Canonical EUDPP IRI prefix](../adr/0002-canonical-eudpp-iri.md)
- [ADR 0003 — GDSO Tyre data-model license](../adr/0003-tyre-license.md)
