# `tools/snapshot/` — CIRPASS-2 spec snapshot tooling

Phase 0 of [`docs/plans/CIRPASS_2_MIGRATION.md`](../../docs/plans/CIRPASS_2_MIGRATION.md).

This directory holds the discovery + pinning tooling that lets us
reproduce the bundled CIRPASS-2 vocabulary and message artefacts from a
clean checkout. The verbatim downloads land under `cirpass-2/`
(gitignored); only the `MANIFEST.json` rows emitted by the fetcher
are committed (in Phase 1, into
[`src/dppvalidator/schemas/data/MANIFEST.json`](../../src/dppvalidator/schemas/data/MANIFEST.json)).

## Files

| File                      | Purpose                                                                  |
| ------------------------- | ------------------------------------------------------------------------ |
| `fetch_cirpass.py`        | The fetcher. Stdlib-only; runs from a clean checkout                     |
| `cirpass2_artefacts.json` | Manifest of in-scope artefacts (14 rows) with `TODO_*` GUID placeholders |
| `cirpass-2/`              | Gitignored. Verbatim downloads land here                                 |
| `README.md`               | This file                                                                |

## Quick reference

```bash
# Show what is planned (offline; no I/O)
python tools/snapshot/fetch_cirpass.py --list

# Verify that w3id.org/eudpp/<module>/ canonical IRIs dereference (D-0.3 gate)
python tools/snapshot/fetch_cirpass.py --verify-canonical

# Fetch every artefact whose GUID is paired; emit MANIFEST rows on stdout
python tools/snapshot/fetch_cirpass.py --fetch \
    > tools/snapshot/manifest-rows.json
```

Exit codes: `0` success · `1` operator error · `2` network/integrity
failure · `3` D-0.3 verification failed (R12 escalation).

## Operator workflow

The artefacts manifest ships with **placeholder GUIDs**. The DPP
Vocabulary Hub renders its listing client-side, so the static spec
URL ([`https://dpp.vocabulary-hub.eu/specifications`](https://dpp.vocabulary-hub.eu/specifications))
does not surface stable title→GUID pairings. The operator pairs them
once, by hand, before invoking `--fetch`:

1. Open [`https://dpp.vocabulary-hub.eu/specifications`](https://dpp.vocabulary-hub.eu/specifications).
1. For each row in `cirpass2_artefacts.json` whose GUID begins with
   `TODO_`:
   1. Locate the matching artefact card in the hub UI (titles in the
      manifest match the hub's display titles verbatim).
   1. Click `Export ttl` (ontology) or `Tree view` → `Export schema`
      (message). The browser will resolve a URL of the form
      `https://dpp.vocabulary-hub.eu/api/{ontology|json-schema|...}/-/version/<GUID>/export`.
   1. Copy the GUID portion (the segment between `version/` and
      `/export`) and paste it over the `TODO_*` placeholder in
      `cirpass2_artefacts.json`.
   1. For message-tree artefacts (CIRPASS reference structure, MVP
      Textile, the tyre declarations), if the hub uses an endpoint
      pattern other than `ontology` / `json-schema`, set the explicit
      `source_url` field on the row instead of the GUID.
1. Run `--list` again to confirm zero placeholders remain.
1. Run `--verify-canonical` to confirm all `https://w3id.org/eudpp/<module>/`
   IRIs dereference (D-0.3 gate; failure escalates as Phase 1 blocker
   R12).
1. Run `--fetch > tools/snapshot/manifest-rows.json` to download bytes
   and emit MANIFEST rows for Phase 1 to merge.
1. Verify the snapshot doc
   ([`docs/concepts/cirpass-2-spec-snapshot.md`](../../docs/concepts/cirpass-2-spec-snapshot.md))
   reflects the pinned SHAs.

## Schema of `cirpass2_artefacts.json`

```jsonc
{
  "schema_version": 1,
  "spec_listing_url": "...",
  "drafted_at": "YYYY-MM-DD",
  "artefacts": [
    {
      "family": "eudpp-ontology" | "cirpass" | "textile-pilot" | "tyre-pilot",
      "module": "P_DPP" | ... | null,           // null for non-modular families
      "version": "1.9.1",
      "date": "2026-03-04" | null,              // hub-printed publish date
      "title": "<verbatim hub title>",
      "guid": "OntologyVersion_<uuid>"          // or TODO_* placeholder
              | "JsonSchemaVersion_<uuid>"
              | "TODO_<slug>",
      "canonical_iri": "https://w3id.org/eudpp/<module>/" | null,
      "format": "ttl" | "jsonld" | "json-schema" | "tree-view-json",
      "scope": "phase-1-vendor"                 // when this artefact lands
              | "phase-3-derive-schema"
              | "phase-7-pilot",
      "source_url": "..." | null,               // explicit override for message URLs
      "notes": "..."                            // free-form
    }
  ]
}
```

The fetcher validates this shape and fails fast with a helpful message
on missing keys. New families / formats can be added without code
changes if they fit the existing `OntologyVersion_*` /
`JsonSchemaVersion_*` GUID conventions; non-conforming endpoints
require setting `source_url` explicitly.

## Why stdlib-only

The fetcher must run from a fresh checkout *before* `uv sync`, so it
deliberately uses `urllib.request` rather than the project's `httpx`
dependency. The fetcher is also the only Python in this directory —
no `__init__.py`, because `tools/` is a script directory, not a
package.
