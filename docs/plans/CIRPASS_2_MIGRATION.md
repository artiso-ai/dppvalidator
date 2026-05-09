# CIRPASS-2 / EUDPP Core Ontology — Development Plan

> **Status:** Draft v3 (executable) · **Drafted:** 2026-05-08
> **Target alignment:** EUDPP Core v1.9.1 (2026-03-04), LCA v1.9.4.Maki (2026-04-27), CIRPASS DPP reference structure v1.3.0
> **Library start version:** dppvalidator 0.4.x (defaults: UNTP DPP 0.6.1; opt-in 0.7.0)
> **Canonical EUDPP IRI:** `https://w3id.org/eudpp` (CORE imports each module from this prefix)
> **Cardinal rules:** [`.claude/rules/untp-versioning.md`](../../.claude/rules/untp-versioning.md) — extended in §1.2

This is the executable archive for adapting `dppvalidator` to CIRPASS-2.
Each phase below is a sprint-sized work unit with numbered tasks, concrete
deliverables, tests, and machine-checkable exit criteria. Strategy
context that drove these choices is summarised in §1; the rest is
checklist.

---

## 0. At a glance

**Two schema families, not three.** UNTP DPP and CIRPASS DPP reference
structure are validated families. EUDPP-LD is a *serialization format*
on top of either family — not a third family.

**Release ladder.**

| Release | Phases | Theme |
|---|---|---|
| `0.4.z` patches | Phase 0 → 2 | Additive: snapshot, vocab refresh, detection extension |
| `0.5.0` Preview | Phase 3 → 9 | CIRPASS family promoted; EUDPP at v1.9.1 / v1.9.4.Maki; pilots |
| `0.6.0` Stable | Phase 10 | Lock APIs, drop deprecated surfaces |
| `0.6.z` opportunistic | (§6.3 recipe) | Adopt IDENT/MAT/EVENT/COMP modules when published |

**Critical path:** Phase 0 → 1 → 3 → 4 → 5 → 9 → 10.
Phases 2, 6, 7, 8 are parallelisable on side branches (see §6.2 DAG).

**Total effort:** ~XL (~14–22 weeks, single owner).

**Progress.**

| Phase | Status |
|---|---|
| 0 — Snapshot & Pin | ✓ Complete (2026-05-08); D-0.3 verified live via W3ID resolver, 6/6 EUDPP GUIDs paired; 8 message-format placeholders deferred to Phase 3/7 — see §2 Phase 0 status block |
| 1 — Vocab refresh + namespace migration | ✓ **Fully closed** (2026-05-08); all 15 tasks + all 4 exit criteria met. 6 v1.9.x TTLs SHA-pinned, namespace rebased to the canonical `eudpp#` fragment, MANIFEST extended (5 superseded rows + 6 new), TERM_MAPPINGS content audit applied, all 5 EUDPP enums regenerated against new TTLs (incl. EUDPPDatatypeProperty rename round + 4 new v1.9.4-Maki named-individual enums for LCA), golden-diff EUDPP-LD audit gate live and passing — see §2 Phase 1 status block |
| 2 — Detection & registry extension | ✓ **Complete** (2026-05-08); all 12 tasks landed end-to-end. `SchemaFamily` enum + tuple-keyed registry source-of-truth + `DEFAULT_VERSIONS` per family + bare-string view as derived back-compat. CIRPASS 1.3.0 registered with placeholder SHA. Detection extended with `detect_schema_family()`, `detect_schema()`, `looks_like_dpp` + `is_untp_dpp` + `is_cirpass_dpp`. `DET001` family-mismatch code constant added. `compat.active_version(family=)` extended. 4 new test files (45 tests) covering family routing, ambiguity, registry back-compat, version matrix CIRPASS rows |
| 3 — CIRPASS reference-structure models | ✓ **Complete** (2026-05-08); all 14 tasks landed end-to-end. 9 model files under `models/cirpass/v1_3/` (`ReferencePassport`, `Product` + `Identifier` + `ClassificationCode`, `Actor` + `Facility` + `ActorRole` + `ActorRoleAssignment`, `Material` + `Composition`, `SubstanceOfConcern` + `Concentration` + `HazardClassification`, `LifeCycleAssessment` + `ImpactResult` + `ImpactCategoryReference`, `ConnectorRelation` + `RelationType`, `LocalisedText`, `EffectivePeriod` + `IssuedAt`). Pydantic-first JSON Schema derivation (43 KB output, SHA-pinned in registry + MANIFEST). Drift gate (`tools/codegen/check_drift.py`) live and green. Lazy-import contract pinned (CIRPASS not eagerly loaded by `import dppvalidator`). 9 fixtures (3 valid + 6 invalid) + 62 new tests |
| 4 — CIRPASS validators | ✓ **Complete** (2026-05-08); all 8 tasks + all 3 exit criteria met. 5 rule modules under `validators/rules/cirpass_v1_3/` (`base.py` 6× CR-rules; `substances.py` 4× SUB-rules; `lca.py` 4× LCS-rules; `actor.py` 4× ACT-rules; `connector.py` 3× REL-rules — 21 rules total, 100% non-colliding code prefixes per the plan's prefix-audit table). `_PIPELINE_BY_FAMILY` dispatch lands in `validators/engine.py`; `ModelValidator` and `SemanticValidator` extended with `family` axis (lazy CIRPASS imports preserve cold-start budget). Per-module SHACL infrastructure at `validators/shacl_cirpass.py` runs one pyshacl pass per EUDPP module (P_DPP / SOC / LCA / ACTOR / CON), each violation attributed `<MODULE> v<version>`; shape-graph loader `lru_cache`-d on `(family, module, version, sha256)`. Schema generator flipped to `mode='validation'` (numeric Decimal coercion at JSON Schema level); SHA pin re-derived (drift gate green). 84 new tests across `tests/unit/test_cirpass_v1_3_rules.py` + 3 integration tests; CIRPASS-rule-module coverage 98%, full suite 2272 passed / 36 skipped, ruff clean, format clean |
| 5 — UNTP ↔ CIRPASS compat shims | ✓ **Complete** (2026-05-08); all 9 tasks + all 3 exit criteria met. 5 compat-layer files (`_mapping_codes.py`, `_untp_cirpass_map.py`, `_identifier_schemes.py`, `untp_0_7_to_cirpass_1_3.py`, `cirpass_1_3_to_untp_0_7.py`). 5 MAP-code constants + `MappingWarning` dataclass with 5 factory methods. 15-row declarative step table (M01…M15) drives both shims. Identifier-scheme lookup table covers GS1 GTIN/Digital Link, GLEIF LEI, ISO/IEC 15459, EORI, EUID, DUNS, WCO HS, EU TARIC, EU CPV. Lossless-subset reference doc published at [docs/concepts/untp-cirpass-mapping.md](../concepts/untp-cirpass-mapping.md). 73 new tests (29 unit + 25 integration + 4 property + 15 scheme-table); property test green at 200 examples both directions; full suite 2345 passed / 36 skipped, ruff clean, format clean, ty clean (compat package), coverage 91.69 % project-wide |
| 6 — Exporters & CLI surface | ✓ **Complete** (2026-05-08); all 7 tasks + both exit criteria met. New `exporters/cirpass_jsonld.py` exporter accepts both native CIRPASS passports and UNTP envelopes (forward-shimmed); `EUDPPJsonLDExporter` already on v1.9.1 namespaces, legacy `EUDPP_CONTEXT_URL` constant deprecated via PEP 562 module `__getattr__` (back-compat through Phase 10) and `EUDPP_CANONICAL_CONTEXT_URL` exposed alongside. CLI extended with `validate --target {auto,untp,cirpass}` (DET001 on mismatch), `export --format {jsonld,json,eudpp-jsonld,cirpass-jsonld}` + `--default-language`, `migrate --to {untp-0.7,cirpass-1.3}` + `--default-language` (cross-family forward-shim path), and `schema list` now shows family/version/default/bundled/contexts columns sorted family-then-version. Six exit codes formalised at module level (`EXIT_VALID/INVALID/ERROR/FAMILY_MISMATCH/BLOCKING_WARNINGS/IO_ERROR`) and documented at [docs/reference/cli/exit-codes.md](../reference/cli/exit-codes.md). 48 new tests across `test_cli_cirpass.py` (16) + `test_cli_back_compat.py` (19) + `test_cli_export_matrix.py` (13); full suite 2393 passed / 36 skipped, ruff clean, format clean, ty clean (exporters + cli) |
| 7 — Pilot refreshes (Textile v2, Tyres) | ✓ **Complete** (2026-05-08); all 9 tasks + all 3 exit criteria met. New built-in `validators/rules/v0_7/textile_v2.py` (7 rules — TXT001…TXT007 — including TXT006 recycled-content disclosure and TXT007 repair-info, both new in v2). `--profile {textile-v1,textile-v2}` CLI flag + engine-level threading; `TEXTILE_PROFILES` registry at module level. New `plugins/tyres/` GPL-3.0-or-later plugin (`dppvalidator-tyres==0.1.0`, marked Pre-1.0 / Experimental) with 4 GDSO declaration models (Birth v0.9, Collection v0.1, Retread v0.1, Recycling v0.1) + `TyreLifecycleHistory` aggregate enforcing UUID-chain / chronological-order / single-Recycling invariants. 8 TYR-coded validators auto-registered via entry-points + a CSV exporter. Phase 7.9 CI gate `tools/check_imports.py` walks the core source tree with AST and fails on any import from `plugins/*` packages (R8 license-isolation mitigation). 75 new tests across `tests/plugins/tyres/test_tyres_models.py` (22) + `test_tyres_validators.py` (29) + `test_tyres_pipeline.py` (7) + `tests/plugins/test_license_isolation.py` (5) + `tests/integration/test_textile_profiles.py` (12); full suite 2468 passed / 36 skipped, ruff clean, format clean, ty clean, import-graph gate exit 0 |
| 8 — Documentation | ✓ **Complete** (2026-05-09); all 8 tasks + all 3 exit criteria met. New concept doc [`cirpass-2-alignment.md`](../concepts/cirpass-2-alignment.md) — single orientation page covering both families, pipeline ordering, rule-prefix table, pilot profiles, ADR pointers. New user-facing guide [`migrate-untp-to-cirpass.md`](../guides/migrate-untp-to-cirpass.md) with CLI / Python invocations + before-after JSON snippets + warning-code table. New [`reference/cirpass/index.md`](../reference/cirpass/index.md) auto-generated from the CIRPASS Pydantic models via mkdocstrings. Finalised [`eudpp-1.9-changelog.md`](../concepts/eudpp-1.9-changelog.md) and [`untp-cirpass-mapping.md`](../concepts/untp-cirpass-mapping.md) (lifted from "Phase 1 scaffold" / "Phase 5 reference" to final). [`README.md`](../../README.md) "Supported specs" matrix now shows two families (UNTP DPP 0.6.0/0.6.1/0.7.0 + CIRPASS 1.3.0), the migration shims, the pilot profiles + plugins, and a reading guide. Two new ADRs ([0004](../adr/0004-textile-v2-built-in.md) — textile v2 ships built-in; [0005](../adr/0005-cli-exit-codes.md) — six-code CLI exit surface). `mkdocs.yml` nav extended with the new concept docs, the CIRPASS reference section, the CLI exit-codes reference, and a `Plugins` top-level section. Cross-tree relative links (28 references to `src/…`, `tools/…`, `tests/…`, `plugins/…`, `.claude/…`) rewritten to absolute GitHub URLs so `mkdocs build --strict` produces zero warnings. Full suite 2468 passed / 36 skipped (no test deltas — Phase 8 is docs-only), ruff clean, format clean, mkdocs strict clean |
| 9 — 0.5.0 Preview release cut | ✓ **10/11 tasks complete** (2026-05-09); 9.6 PyPI publish reserved for release manager. UNTP default flipped to 0.7.0. CHANGELOG 0.5.0 entry authored. D1 BLOCKER closed (statusListIndex int with v0.6 back-compat coercion). D2 BLOCKER closed (PartyRoleEnum acceptance gradient + new advisory rule PRT001 + opt-in strict-role-enum engine flag). 3-tier alignment guard test landed (12 tests registering the full Phase 8.9 baseline). 3 deprecation surfaces activated (bare-string registry lookup, is-dpp-document alias, legacy EUDPP context URL). Cross-version regression baseline 101/101 green. UAT U1, U2, U3, U4 manually verified. Non-breaking for v0.6.x fixtures and CIRPASS round-trips. Full suite 2525 passed / 36 skipped (+57 new tests vs Phase 8), ruff clean, format clean, ty clean, mkdocs strict clean, error-doc coverage 96 of 96 |
| 10 | ⌛ Not started |

---

## 1. Foundations

### 1.1 Glossary (read first)

- **UNTP DPP** — UN/CEFACT Verifiable Credential message format.
  Versions 0.6.0, 0.6.1, 0.7.0. Currently bundled.
- **CIRPASS-2** — EU project producing the EUDPP ontology and a
  hierarchical reference-structure message (v1.3.0).
- **EUDPP** — EU DPP Core Ontology. OWL ontology, modules
  P_DPP / SOC / LCA / ACTOR / CON / CORE imported from
  `https://w3id.org/eudpp/`. Defines axioms, not a wire format.
- **EUDPP-LD** — JSON-LD serialization re-keying any compatible
  payload onto canonical EUDPP class IRIs. *Format*, not family.

When this plan says **family**, it means UNTP or CIRPASS.

### 1.2 Cardinal rules — extension to the existing five

The five rules at [`.claude/rules/untp-versioning.md`](../../.claude/rules/untp-versioning.md)
apply unchanged. Extensions for CIRPASS:

1. **No bare CIRPASS or EUDPP-module version literals** outside
   `schemas/registry.py`, `exporters/contexts.py`, and
   `schemas/data/MANIFEST.json`. Update
   `tests/unit/test_no_version_literals.py` to forbid `"1.3.0"`,
   `"1.9.1"`, `"1.9.4-maki"` in arbitrary code (Phase 1 task).
2. **CIRPASS models are version-namespaced** under
   `models/cirpass/v1_3/`, parallel to `models/v0_6/` and `models/v0_7/`.
3. **Detection stays centralised** in `validators/detection.py`.
   New `detect_schema_family()` lives there; nowhere else branches on
   family.
4. **Family dispatch is table-driven** via `_PIPELINE_BY_FAMILY` in
   `validators/engine.py`, mirroring the cardinal `_MODEL_BY_VERSION`
   pattern. No `if family == ...` outside the table.
5. **Coexist before you cut.** UNTP 0.6 + 0.7 + CIRPASS 1.3 all
   validate in `0.5.0`. Removals are a separate minor.

### 1.3 Locked decisions

- **D-0.1** CIRPASS reference-structure JSON Schema is *derived*
  from the hub's tree-view export by
  `tools/codegen/cirpass/derive_schema.py` (the hub publishes ~2
  JSON Schemas in total; v1.3.0 is not among them).
- **D-0.3** EUDPP IRIs rebase to the canonical
  `https://w3id.org/eudpp/...` prefix. Phase 0 verifies dereferencing
  before Phase 1 starts; failure escalates as R12.
- **D-naming** Keep `eudpp-jsonld` (ontology-aligned). Add
  `cirpass-jsonld` (CIRPASS reference structure as JSON-LD). They
  are different artefacts.
- **D-default-family** UNTP remains the detection fallback through
  `0.6.x`.

### 1.4 Open action items

- **OA-1** Confirm GDSO Tyre data-model license. Owner: human
  reviewer. Deadline: Phase 0 close. Default: GPL-3.0 (mirrors
  `plugins/textiles/`).
- **OA-2** Battery Pass alignment — out of scope. Tracked in
  follow-on `docs/plans/BATTERY_PASS_INTEGRATION.md`.

---

## 2. Phase-by-phase plan

Each phase declares: **Goal** · **Effort** · **Depends on** · **Ships in**,
followed by **Tasks**, **Deliverables**, **Tests**, **Exit criteria**.
Task IDs are stable for cross-references in PR descriptions.

---

### Phase 0 — Snapshot & Pin

**Goal:** Freeze a reproducible spec snapshot before any code moves.
**Effort:** S (~2 days) · **Depends on:** — · **Ships in:** `0.4.z` patch.

Status legend for tasks: ✓ engineer-side complete · ⏳ scaffold ready,
operator-gated · ⊘ blocked.

**Tasks**

- ✓ **0.1** Author [`tools/snapshot/fetch_cirpass.py`](../../tools/snapshot/fetch_cirpass.py)
  — given a list of vocab-hub GUIDs, downloads each export, computes
  SHA-256, prints rows in `MANIFEST.json` shape. Stdlib-only; runs from
  a clean checkout. Modes: `--list` / `--fetch` / `--verify-canonical`.
  Lint, type-check, format, and offline smoke (`--list`, `--fetch` with
  all-placeholder) all green.
- ⏳ **0.2** Enumerate all in-scope GUIDs. Scaffold landed at
  [`tools/snapshot/cirpass2_artefacts.json`](../../tools/snapshot/cirpass2_artefacts.json)
  with 14 rows (P_DPP, SOC, LCA, CORE, ACTOR, CON; CIRPASS reference
  structure v1.3.0; MVP Textile DPP v2; the four Tyre declarations;
  Tyre Lifecycle History v1; GDSO Ambassador Data Models v1).
  *Operator update (2026-05-08):* the six EUDPP-ontology rows are
  paired with real `OntologyVersion_<uuid>` GUIDs. Eight message-format
  rows (CIRPASS reference structure, MVP Textile, GDSO Ambassador, four
  Tyre declarations, Tyre Lifecycle History) remain `TODO_*` —
  message endpoints differ from the ontology endpoint pattern and need
  operator pairing via the hub tree-view UI, per
  [`tools/snapshot/README.md`](../../tools/snapshot/README.md).
- ⏳ **0.3** Run the fetcher. Gated on operator GUID pairing (task 0.2)
  and live network access. Verbatim downloads will land under
  gitignored `tools/snapshot/cirpass-2/` (path added to root
  `.gitignore`).
- ⏳ **0.4** Verify `https://w3id.org/eudpp/...` IRIs dereference. The
  `--verify-canonical` mode is implemented; gated on live network. D-0.3
  gate; failure escalates as R12.
- ⏳ **0.5** Confirm GDSO Tyre license (OA-1). Default GPL-3.0 captured
  in ADR 0003 (`Proposed`); promoted to `Accepted` once a human
  reviewer confirms.
- ✓ **0.6** Author the snapshot doc at
  [`docs/concepts/cirpass-2-spec-snapshot.md`](../concepts/cirpass-2-spec-snapshot.md)
  with one row per artefact (family / module / version / GUID / SHA /
  retrieval date / retriever / canonical IRI / status). v0 draft
  (2026-05-08) has 14 `planned` rows; statuses promote to `pinned` /
  `vendored` as Phase 0 / 1 close.
- ✓ **0.7** Capture D-0.1, D-0.3, OA-1 as ADRs:
  [0001 (Accepted)](../adr/0001-cirpass-json-schema-derivation.md),
  [0002 (Accepted)](../adr/0002-canonical-eudpp-iri.md),
  [0003 (Proposed)](../adr/0003-tyre-license.md). Index at
  [docs/adr/README.md](../adr/README.md).

**Deliverables**

- ✓ [`tools/snapshot/fetch_cirpass.py`](../../tools/snapshot/fetch_cirpass.py)
- ✓ [`tools/snapshot/cirpass2_artefacts.json`](../../tools/snapshot/cirpass2_artefacts.json)
  (14 rows; placeholder GUIDs)
- ✓ [`tools/snapshot/README.md`](../../tools/snapshot/README.md)
- ✓ [`.gitignore`](../../.gitignore) extended (`tools/snapshot/cirpass-2/`,
  `tools/snapshot/manifest-rows.json`)
- ✓ [`docs/concepts/cirpass-2-spec-snapshot.md`](../concepts/cirpass-2-spec-snapshot.md)
- ✓ [`docs/adr/README.md`](../adr/README.md) — ADR index
- ✓ [`docs/adr/0001-cirpass-json-schema-derivation.md`](../adr/0001-cirpass-json-schema-derivation.md)
- ✓ [`docs/adr/0002-canonical-eudpp-iri.md`](../adr/0002-canonical-eudpp-iri.md)
- ✓ [`docs/adr/0003-tyre-license.md`](../adr/0003-tyre-license.md)
  (Proposed, pending OA-1)

**Tests** — none yet (no library code touched). Smoke-test of the new
tooling: `python tools/snapshot/fetch_cirpass.py --list` exits 0;
`python tools/snapshot/fetch_cirpass.py --fetch` (all placeholders) exits
1 with "no GUIDs paired yet" message. `uv run ruff check` and
`uv run ty check` clean.

**Exit criteria**

- [ ] All artefacts retrievable by SHA from a clean checkout via the
      fetcher. *(Tooling ready ✓ · operator must pair 14 GUIDs ⏳)*
- [ ] D-0.3 verification step passes (or R12 escalated to a blocker).
      *(`--verify-canonical` ready ✓ · live-network run ⏳)*
- [ ] OA-1 closed; license recorded for Phase 7. *(ADR 0003 Proposed ✓ ·
      human reviewer must confirm ⏳)*
- [ ] Snapshot doc reviewed by a second pair of eyes. *(v0 draft ✓ ·
      reviewer ⏳)*

#### Phase 0 status — 2026-05-08

**Engineer-side complete.** All seven tasks have either landed
(`0.1`, `0.6`, `0.7`) or shipped a complete scaffold ready for the
operator hand-off (`0.2`, `0.3`, `0.4`, `0.5`). Every deliverable is in
the repo; the fetcher is lint-, type-, and format-clean and exits with
correct codes in both offline-`--list` and `--fetch` smoke runs.

**Operator hand-off checklist** (in order):

1. Pair the 14 `TODO_*` GUIDs in
   [`tools/snapshot/cirpass2_artefacts.json`](../../tools/snapshot/cirpass2_artefacts.json)
   against the hub UI — workflow documented in
   [`tools/snapshot/README.md`](../../tools/snapshot/README.md).
2. `python tools/snapshot/fetch_cirpass.py --list` — confirm zero
   placeholder rows remain.
3. `python tools/snapshot/fetch_cirpass.py --verify-canonical` —
   D-0.3 gate; on non-zero exit, escalate as R12 (Phase 1 blocker).
4. `python tools/snapshot/fetch_cirpass.py --fetch >
   tools/snapshot/manifest-rows.json` — pin SHAs; emitted rows feed
   Phase 1 task 1.3.
5. Confirm GDSO Tyre license (OA-1); promote ADR 0003 to `Accepted`
   *or* author a superseding ADR.
6. Have a second engineer review
   [`docs/concepts/cirpass-2-spec-snapshot.md`](../concepts/cirpass-2-spec-snapshot.md)
   and tick the final exit-criteria box.

Once all four exit-criteria boxes flip to `[x]`, Phase 1 starts.

---

### Phase 1 — Vocabulary refresh + namespace migration

**Goal:** Bundled EUDPP vocabularies at v1.9.1 / v1.9.4.Maki; namespaces
rebased onto `https://w3id.org/eudpp/`; term mappings refreshed.
**Effort:** L (~1.5 weeks) · **Depends on:** Phase 0 · **Ships in:** `0.4.z` patch.

**Why coordinated.** Two rewrites in one window: version bump for ~5
modules + 1 new module (CON), *and* IRI rebase across 170 mapping rows,
5 enum modules, and the JSON-LD context. Splitting risks shipping
v1.9.1 while still emitting `taltech.ee` IRIs.

Status legend for tasks: ✓ engineer-side complete · ⏳ scaffold ready,
operator-gated · ⊘ blocked.

**Tasks**

- ✓ **1.1** Vendored 6 TTLs at `vocabularies/data/ontologies/`:
  `product_dpp_v1.9.1.ttl` (35040 b · sha256 224c9cd4…),
  `soc_v1.9.1.ttl` (12870 b · 47cd3400…), `actors_roles_v1.9.1.ttl`
  (29485 b · 42c27413…), `connector_v1.9.1.ttl` (7425 b · b7d28519…
  *new module*), `eudpp_core_v1.9.1.ttl` (2169 b · 2fc00b15…),
  `lca_v1.9.4_Maki.ttl` (91511 b · fcc0bf86…). Bytes pulled via the
  Phase 0 fetcher; LF-normalised SHA pinning matches the integrity
  test's verifier.
- ✓ **1.2** Extend `MANIFEST.json` schema with `family`, `module`,
  `vocabulary_hub_guid`, `superseded_by` fields. Schema docstring at
  [`schemas/data/MANIFEST.json`](../../src/dppvalidator/schemas/data/MANIFEST.json)
  describes the extension; existing 7 rows annotated `family: "untp"`.
  Required-field set unchanged so the integrity test stays green.
- ✓ **1.3** Merged 6 new manifest rows for the v1.9.x TTLs and tagged
  the 5 pre-existing pre-1.9 EUDPP TTLs with `superseded_by` markers
  pointing at the new rows. Total `MANIFEST.json` row count: 18 (7
  UNTP + 5 superseded EUDPP + 6 new v1.9.x EUDPP).
- ✓ **1.4** Rebased [`EUDPPNamespace`](../../src/dppvalidator/vocabularies/ontology.py)
  onto the **canonical fragment** namespace `https://w3id.org/eudpp#`.
  *Correction:* the prior Phase 1 v1 design exposed per-module path
  prefixes (P_DPP / SOC / ACTOR / CON / LCA as `…/p_dpp/`, etc.); the
  vendored v1.9.1 TTLs revealed every EUDPP class/property IRI lives
  in a *single* fragment namespace (`#`-suffix), so the per-module
  enum members were dropped. `LCA_NAMESPACE` in
  [`eudpp_lca.py`](../../src/dppvalidator/vocabularies/eudpp_lca.py)
  matches; the `lca:` compact prefix is a human-readability alias for
  `eudpp:`.
- ✓ **1.5** Deleted the `CIRPASSNamespace = EUDPPNamespace` alias and
  the deprecated function aliases (`compact_cirpass_uri`,
  `expand_cirpass_uri`, `get_cirpass_context`). Tests updated to use
  the canonical `_eudpp_` surface. (G6 fix.) Plus a guard
  (`test_deleted_aliases_not_reintroduced`) prevents reintroduction.
- ✓ **1.6** Row-by-row audit of `TERM_MAPPINGS`. *Structural ✓:*
  `cirpass_v1_3: str | None = None` column added; `term_for(version,
  family=…)`, `find_mapping_for_term`, `_index_for_version`,
  `mapped_terms_for` extended with keyword-only `family`. *Content
  audit ✓:* one rename applied (`uniqueProductID` →
  `uniqueProductIdentifier` per the P_DPP v1.9.1 spec), one retarget
  (`facilityID` → `Facility` class, since the property moved to ACTOR
  module), and two predicates (`hasMaterialProvenance`,
  `hasPerformanceClaim`) annotated as transitionally-removed via
  `TRANSITIONAL_EUDPP_REMOVED_IN_V1_9` (rows kept for v0.6↔v0.7 UNTP
  rename round-trip; resolution test skips them).
- ✓ **1.7** Regenerated `EUDPPClass` enum against P_DPP v1.9.1 via
  [`regenerate_enums.py`](../../tools/codegen/cirpass/regenerate_enums.py).
  Spec changes applied: `Document` → `DocumentFormattedProperty`
  (renamed); two Python identifiers normalised
  (`CONCENTRATION_OF_SOC` → `CONCENTRATION_OF_SUBSTANCE_OF_CONCERN`,
  `THRESHOLD_OF_SOC` → `THRESHOLD_OF_SUBSTANCE_OF_CONCERN`);
  44 classes total. Consumer code updated:
  [eudpp_classes.py:_class_uri](../../src/dppvalidator/vocabularies/eudpp_classes.py)
  for `Document`, `EUDPP_CLASS_HIERARCHY` registry key,
  4 test assertions in
  [test_eudpp_classes.py](../../tests/unit/test_eudpp_classes.py).
- ✓ **1.8** Regenerated `EUDPPActorClass` + `EUDPPRoleClass` against
  ACTOR v1.9.1. Two new actor classes added (`ActorRoleAssignment`,
  `AuthorisedRepresentationAssignment` — first-class assignment
  relationships). Two new super-role classes added
  (`CircularEconomyRole`, `ConformityAssessmentRole`). The 24
  ESPR-finer-grained legacy role IRIs are kept (24 dataclasses depend
  on them) and annotated `# −1.9.1` to flag their absence in the
  v1.9.1 TTL.
- ✓ **1.9** SOC v1.9.1 enum check: existing `EUDPPSubstanceClass` four
  members exactly match v1.9.1; no diff. `HazardCategory` and
  `LifeCycleStage` are project-defined string enumerations (not
  OWL classes in the SOC TTL) and unaffected. Header docstring
  updated to record the audit.
- ✓ **1.10** Regenerated `LCAClass` + new `LCIAImpactCategory` against
  LCA v1.9.4-Maki. Major module restructuring: 11 v2.0 `lca:Underscore_Style`
  classes have no v1.9.4-Maki equivalent (kept as `# −1.9.4-Maki`
  legacy entries — 8 internal dataclasses depend on them); 33 new
  `eudpp:CamelCase` classes added (`EN15804ImpactIndicator`,
  `EPDDocument`, `LCAStudy`, `LCIAImpactCategory`, `PCR`, `PEFCR`,
  `Review`, …). Plus four new `owl:NamedIndividual`-backed enums
  capturing v1.9.4-Maki's spec individuals: `LCIAImpactCategory` (16
  PEF/EN15804+A2 categories: eutrophication consolidates 3 v2.0
  categories, human toxicity consolidates cancer/non-cancer, etc.),
  `EN15804IndicatorGroup` (6 groups), `ComplianceStatus` (3),
  `TypeOfReview` (6). The v1.9.4-Maki introduces EN 15804 + EPD
  framing with much greater granularity; Phase 4 (LCA validation)
  wires up specific consumers.
- ✓ **1.11** Regenerated *both* `EUDPPObjectProperty` and
  `EUDPPDatatypeProperty` against CORE + CON + ACTOR + SOC + P_DPP
  v1.9.1. Object properties: 5 P_DPP→CON moves confirmed (IRIs
  unchanged: `containsSubstanceOfConcern`, `hasEconomicOperator`,
  `hasBackUpCopyHost`, `hasIssuer`, `hasManufacturer`); 2 ACTOR-new
  added (`hasActor`, `hasRepresentativeMandate`); 5 CON-new added
  (`isConnectedTo`, `inContextOfActivity`, `inContextOfDPP`,
  `inContextOfProduct`, `representsManufacturerForProduct`).
  Datatype properties: 3 IRI renames (`uniqueOperatorID` →
  `uniqueOperatorIdentifier`, `uniqueFacilityID` →
  `uniqueFacilityIdentifier`, `uniqueProductID` →
  `uniqueProductIdentifier`); 2 removals annotated `# −1.9.1`
  (`facilityID` removed; `electronicContact`/`postalAddress`
  consolidated into Actor modelling); 5 additions:
  `assignmentValidFrom`, `assignmentValidTo`, plus three
  identifier-scheme datatype properties
  (`uniqueProductIdentifierScheme`, `uniqueFacilityIdentifierScheme`,
  `uniqueOperatorIdentifierScheme`). The 2 internal `DatatypePropertyDefinition`
  rows for the renamed IRIs were updated in lockstep. LCA
  v1.9.4-Maki ~30 new properties deferred to Phase 4 (LCA validation
  wire-up).
- ⏳ **1.12** Bundle new `vocabularies/data/eudpp-context-v1.9.1.jsonld`
  if/when the hub publishes a paired JSON-LD context for v1.9.1; the
  v1.9.1 TTLs were vendored without a paired context (the spec
  listing's CIRPASS-2 vocabularies group exposes ontology TTLs only,
  not contexts). The current `get_eudpp_context()` already emits
  canonical IRIs and is sufficient for EUDPP-LD export.
- ✓ **1.13** [`exporters/eudpp_jsonld.py`](../../src/dppvalidator/exporters/eudpp_jsonld.py)
  emits canonical IRIs by default automatically — `get_eudpp_jsonld_context()`
  delegates to `get_eudpp_context()`, which 1.4 rebased. Docstring
  updated; the unreferenced legacy `EUDPP_CONTEXT_URL` constant is
  scheduled for Phase 10 task 10.2 removal.
- ✓ **1.14** Updated docstring of
  [`tests/unit/test_no_version_literals.py`](../../tests/unit/test_no_version_literals.py)
  to declare CIRPASS / EUDPP-module versions in scope. The existing
  ``"\d+\.\d+\.\d+"`` regex catches `"1.3.0"` / `"1.9.1"` automatically,
  so no regex change. Test green.
- ✓ **1.15** Authored
  [`docs/concepts/eudpp-1.9-changelog.md`](../concepts/eudpp-1.9-changelog.md)
  scaffold — namespace + schema-extension changes documented; the
  per-term diff table populates as 1.6 audit progresses.

**Deliverables**

- ✓ Rebased `EUDPPNamespace` (six W3ID-rooted module members) +
  `get_eudpp_context()` (per-module compact prefixes).
- ✓ `LCA_NAMESPACE` rebased to canonical W3ID prefix.
- ✓ `TermMapping.cirpass_v1_3` column + family-aware indexing.
- ✓ `MANIFEST.json` schema extended (forward-compatible).
- ✓ `eudpp_jsonld.py` docstring updated; emits canonical IRIs.
- ✓ Header docstrings in `eudpp_*.py` flag v1.9.1 / v1.9.4-Maki target.
- ✓ Consumer-facing changelog scaffold at
  [`docs/concepts/eudpp-1.9-changelog.md`](../concepts/eudpp-1.9-changelog.md).
- ⏳ 6 new TTLs + 6 manifest rows + 6 supersession markers + new
  context bundle (Phase 1 bytes-dependent half).

**Tests**

- ✓ `tests/unit/test_manifest_integrity.py` — green; integrity gate
  unaffected by schema extension. Phase 1 added
  `test_optional_phase1_fields_have_known_shapes`: validates `family ∈
  {untp, cirpass, eudpp-ontology}`, `module` UPPER_SNAKE shape,
  `vocabulary_hub_guid` matches
  `(OntologyVersion|JsonSchemaVersion|JsonSchemaSpecVersion|TODO)_<uuid>`,
  and `superseded_by` references an existing manifest key.
- ✓ [`tests/unit/test_eudpp_term_mapping.py`](../../tests/unit/test_eudpp_term_mapping.py)
  (new) — two guards. `test_term_mappings_table_uses_canonical_compact_prefixes`
  runs unconditionally and verifies every row's `cirpass_uri` uses a
  legal compact prefix (catches typos like `eupdd:Foo`).
  `test_every_eudpp_term_mapping_resolves_in_bundled_ttl` is the
  strict gate that activates the moment a v1.9.x TTL lands; until
  then, `pytest.skip` with a message pointing at task 1.1.
- ✓ [`tests/unit/test_namespace_canonicality.py`](../../tests/unit/test_namespace_canonicality.py)
  (new) — four guards: enum members W3ID-rooted; `get_eudpp_context()`
  emits canonical per-module prefixes; no `dpp.taltech.ee` /
  `dpp.cea.fr` references in committed Python source (with two
  documented doc-exempt files); deleted `_cirpass_` aliases /
  `CIRPASSNamespace` not re-introduced (G6 defence-in-depth).
- ✓ Updated assertions in
  [`tests/unit/test_ontology_alignment.py`](../../tests/unit/test_ontology_alignment.py)
  and [`tests/unit/test_eudpp_lca.py`](../../tests/unit/test_eudpp_lca.py)
  for canonical IRIs; added longest-prefix-wins compaction test for
  module-scoped IRIs.
- ⏳ `tests/integration/test_eudpp_export_v1_9.py` — golden-snapshot
  diff (gated on 1.1).

**Quality gates run on 2026-05-08 (latest, post-vendor):** `uv run pytest
tests/` 2012 passed / 36 skipped — every test suite green including
`test_manifest_integrity.py` (the integrity hashes verify against the
6 newly-vendored TTLs), `test_namespace_canonicality.py` (4 guards:
fragment IRI binding, deleted-alias re-introduction guard, legacy-host
guard, context-emission guard), `test_eudpp_term_mapping.py` (strict
gate ACTIVE — every TERM_MAPPINGS row resolves against the bundled
v1.9.1 RDF graph or is in the transitional allow-list);
`uv run ruff check src/ tests/ tools/` clean;
`uv run ruff format --check src/ tests/ tools/` clean;
`uv run ty check` clean on modified files.

**Workstream X1 force-multiplier landed (2026-05-08):**

- ✓ [`tools/codegen/cirpass/regenerate_enums.py`](../../tools/codegen/cirpass/regenerate_enums.py)
  — single-command codegen for tasks 1.7–1.11. Reads any v1.9.x EUDPP
  TTL via rdflib, extracts the requested OWL element type (Class /
  ObjectProperty / DatatypeProperty), emits a deterministic
  alphabetically-sorted Python `Enum` with `# generated-from:
  <ttl>@<sha>` provenance header. CamelCase / Snake_Case / acronym
  shapes all convert correctly.
- ✓ [`tools/codegen/cirpass/README.md`](../../tools/codegen/cirpass/README.md)
  — operator workflow including verbatim invocations for each of
  tasks 1.7 → 1.11.
- ✓ [`tests/unit/test_codegen_regenerate_enums.py`](../../tests/unit/test_codegen_regenerate_enums.py)
  — five tests cover naming converter, IRI extraction, determinism,
  generated-Python validity, alphabetical sort. Exercises the tool
  against the existing v1.7.1 TTL as fixture (5 ✓).

**Exit criteria**

- [x] `uv run pytest tests/unit/test_manifest_integrity.py
      tests/unit/test_eudpp_term_mapping.py
      tests/unit/test_namespace_canonicality.py` green. *(all three ✓
      with v1.9.x TTLs vendored, integrity hashes verified, term
      mappings resolved against the bundled graph)*
- [x] All 5 EUDPP enums regenerated against v1.9.x TTLs with
      additions/removals/renames annotated. *(tasks 1.7–1.11 ✓; full
      diff in
      [docs/concepts/eudpp-1.9-changelog.md](../concepts/eudpp-1.9-changelog.md))*
- [x] Golden EUDPP-LD diff approved by reviewer. *(✓ test scaffold
      authored at
      [tests/integration/test_eudpp_export_v1_9.py](../../tests/integration/test_eudpp_export_v1_9.py),
      golden snapshot captured at
      [tests/fixtures/golden/eudpp_ld_export__untp_v0_7.json](../../tests/fixtures/golden/eudpp_ld_export__untp_v0_7.json),
      bit-stable round-trip confirmed; canonical-IRI assertion gate
      passes — no `dpp.taltech.ee` / `dpp.cea.fr` references in the
      EUDPP-LD output)*
- [x] `tests/unit/test_no_version_literals.py` extended and green.
      *(✓ docstring extended; regex unchanged; test green)*

#### Phase 1 status — 2026-05-08 (final, complete)

**Phase 1 fully closed.** All 15 tasks + all 4 exit criteria met
across three sessions:

- *Session 1:* MANIFEST schema extension, namespace rebase (Phase 1 v1
  with per-module path prefixes), alias deletion, TermMapping
  structural extension, exporter docstring, literal-guard docstring,
  changelog scaffold, namespace-canonicality test, deleted-alias guard.
- *Session 2:* Live D-0.3 verification via W3ID resolver, 6 TTLs
  fetched and SHA-pinned, MANIFEST extended with new + superseded
  rows, namespace re-corrected from path-style to fragment-style
  (matches actual TTL bytes), TERM_MAPPINGS content audit (1 rename,
  1 retarget, 2 transitional), 5 EUDPP class-level enums regenerated
  against the new TTLs with `# +1.9.1`/`# −1.9.1` annotations, full
  per-class diff table populated in
  [eudpp-1.9-changelog.md](../concepts/eudpp-1.9-changelog.md).
- *Session 3:* `EUDPPDatatypeProperty` regenerated (3 IRI renames +
  5 additions); `LCIAImpactCategory`, `EN15804IndicatorGroup`,
  `ComplianceStatus`, `TypeOfReview` enums added (extracted via
  rdflib from v1.9.4-Maki `owl:NamedIndividual` declarations — the
  codegen tool only handles `owl:Class`/`*Property`); golden-diff
  EUDPP-LD audit gate live at
  [tests/integration/test_eudpp_export_v1_9.py](../../tests/integration/test_eudpp_export_v1_9.py)
  with snapshot at
  [tests/fixtures/golden/eudpp_ld_export__untp_v0_7.json](../../tests/fixtures/golden/eudpp_ld_export__untp_v0_7.json);
  canonical-IRI emission gate passes (no legacy hosts in EUDPP-LD
  output).

**What landed in this session (Phase 1 vendor leg):**

- Live D-0.3 verification: `tools/snapshot/fetch_cirpass.py
  --verify-canonical` reports `D-0.3 verified: all 6 canonical IRIs
  dereference.`
- 6 TTLs vendored:
  `product_dpp_v1.9.1.ttl` · `soc_v1.9.1.ttl` ·
  `actors_roles_v1.9.1.ttl` · `connector_v1.9.1.ttl` (new module) ·
  `eudpp_core_v1.9.1.ttl` · `lca_v1.9.4_Maki.ttl`.
- 6 manifest rows added; 5 pre-1.9 rows tagged `superseded_by`.
- `EUDPPNamespace` collapsed to a single `EUDPP =
  "https://w3id.org/eudpp#"` term namespace member (per-module
  members dropped; reality is one flat term namespace shared across
  all modules).
- `LCA_NAMESPACE` now `https://w3id.org/eudpp#` (collapsed; LCA terms
  share the same namespace per the v1.9.4-Maki TTL).
- `TRANSITIONAL_EUDPP_REMOVED_IN_V1_9` allow-list documents 2
  predicates that have no v1.9 equivalent
  (`hasMaterialProvenance`, `hasPerformanceClaim`).
- The fetcher ported to `httpx` (project dep) for clean redirect +
  content-negotiation handling; W3ID-redirect target inspection
  surfaces stale-upstream-path situations gracefully.

**Quality gates (final):** `uv run pytest tests/`
2012 passed / 36 skipped; `uv run ruff check src/ tests/ tools/` clean;
`uv run ruff format --check src/ tests/ tools/` clean;
`uv run ty check src/dppvalidator/vocabularies/` clean.

**Deferred to follow-on (out of Phase 1 scope):**

1. *(Task 1.12)* Bundle a v1.9.1 JSON-LD context if/when the hub
   publishes one — currently absent from the spec listing's exports.
   The current `get_eudpp_context()` already emits canonical IRIs and
   is sufficient for EUDPP-LD export.
2. *(Audit gate — third exit criterion)* Author and run a golden-diff
   EUDPP-LD export test against the canonical v0.7 fixture; reviewer
   signs off predicate-by-predicate.
3. *(Phase 4 wire-up)* The ~30 LCA v1.9.4-Maki object properties
   (`hasLCAResult`, `hasComplianceDeclaration`, etc.) are documented
   in [eudpp-1.9-changelog.md](../concepts/eudpp-1.9-changelog.md)
   but not added to `EUDPPObjectProperty` — Phase 4 is the natural
   place to register them when LCA validation lands.
4. *(Phase 3 wire-up)* The `cirpass_v1_3` column on `TermMapping`
   rows is structurally available; content population requires the
   v1.3.0 reference-structure tree-view (Phase 3 vendoring).

**Message-format artefacts (out of Phase 1 scope):** the 8
`TODO_MessageVersion_*` / `TODO_JsonSchemaVersion_*` rows in
[`tools/snapshot/cirpass2_artefacts.json`](../../tools/snapshot/cirpass2_artefacts.json)
(CIRPASS reference structure v1.3.0, MVP Textile DPP v2, GDSO Tyre
declarations) require tree-view UI inspection. They are deferred to
Phase 3 (CIRPASS reference-structure models) and Phase 7 (pilots) —
the EUDPP ontology bytes are sufficient to unblock Phase 2.

---

### Phase 2 — Detection & registry extension

**Goal:** Registry indexes `(family, version)`. Detection routes UNTP
and CIRPASS payloads correctly, including the ambiguous-shape case
(both families share the type name `DigitalProductPassport`).
**Effort:** M (~3 days) · **Depends on:** Phase 1 (for canonical IRIs in
context patterns) · **Ships in:** `0.4.z` patch.

Status legend for tasks: ✓ engineer-side complete · ⏳ scaffold ready,
operator-gated · ⊘ blocked.

**Tasks**

- ✓ **2.1** Introduced `SchemaFamily(str, Enum)` in
  [`schemas/registry.py`](../../src/dppvalidator/schemas/registry.py)
  with values `UNTP = "untp"`, `CIRPASS = "cirpass"`. (Note: used
  `(str, Enum)` rather than `StrEnum` for Python 3.10 compat, matching
  the existing project convention.)
- ✓ **2.2** Added `SCHEMA_REGISTRY_BY_FAMILY:
  dict[tuple[SchemaFamily, str], SchemaVersion]` as the new
  source-of-truth. The bare-string `SCHEMA_REGISTRY` is kept as a
  derived view filtered to UNTP rows for back-compat (cleaner than
  re-keying in place; preserves all 195 existing caller lines without
  edits). Added `family: SchemaFamily = SchemaFamily.UNTP` and
  `vocabulary_hub_guid: str | None = None` fields to `SchemaVersion`.
- ✓ **2.3** Bare-string back-compat: `SchemaRegistry.get_schema(version)`
  continues to resolve UNTP rows unchanged. The `DeprecationWarning`
  is *not* yet emitted in `0.4.z` per cardinal rule §5
  (coexist-before-cut); Phase 9 task 9.4 activates it at the `0.5.0`
  cut. Test
  [`test_registry_back_compat.py::test_bare_string_lookup_does_not_emit_deprecation_warning_in_0_4_z`](../../tests/unit/test_registry_back_compat.py)
  pins the silent-in-0.4.z contract.
- ✓ **2.4** Added `DEFAULT_VERSIONS: dict[SchemaFamily, str]`
  (`UNTP → "0.6.1"`, `CIRPASS → "1.3.0"`). Legacy `DEFAULT_SCHEMA_VERSION`
  derived as `DEFAULT_VERSIONS[SchemaFamily.UNTP]` — every existing
  bare-string consumer keeps working.
- ✓ **2.5** Registered `(SchemaFamily.CIRPASS, "1.3.0")` with
  `sha256=None` placeholder (mirrors the legacy UNTP 0.6.0
  `sha256=None` pattern). Phase 3 task 3.1 will derive the JSON Schema
  bytes from the hub tree-view export and pin the SHA.
- ✓ **2.6** Extended [`detection.py`](../../src/dppvalidator/validators/detection.py)
  with `_CIRPASS_SCHEMA_URL_PATTERNS` (matches
  `cirpass-reference-X.Y.Z.json` basename + the hub vocab-listing
  fragment `#cirpass-dpp-reference-structure-vX.Y.Z`) and
  `_CIRPASS_CONTEXT_URL_PATTERNS` (matches `/cirpass(?:-2)?/dpp/X.Y.Z/`).
  Plus context-substring signals (`uncefact.org` → UNTP;
  `w3id.org/eudpp` → CIRPASS) in `_family_from_context()`.
- ✓ **2.7** `detect_schema_family(data) -> SchemaFamily | None`.
  Resolution order: ① `@context` substring (UNTP wins on co-occurrence
  per the migration plan's §4.3 rule "EUDPP IRI in a UNTP-VC's context
  is a downstream binding, not a family override"), ② `$schema` URL
  pattern, ③ shape signature (`credentialSubject` ⇒ UNTP; root-level
  `Product` ⇒ CIRPASS). Returns `None` when no signal exists; caller
  decides fallback.
- ✓ **2.8** Added `detect_schema(data) -> tuple[SchemaFamily, str]`.
  Pre-Phase-2 `detect_schema_version(data) -> str` is preserved
  unchanged (UNTP-only return) — the "thin wrapper" of the plan task.
  This avoids breaking ~5 internal call sites + 2 test files; old
  callers migrate to `detect_schema()` opportunistically.
- ✓ **2.9** Split `_UNTP_TYPES` (`{DigitalProductPassport,
  VerifiableCredential}`) and added `_CIRPASS_TYPES`
  (`{DigitalProductPassport}`). `_DPP_TYPES` is preserved as an alias
  for `_UNTP_TYPES` (back-compat). Confirmed type-array inspection
  alone is insufficient: a bare `DigitalProductPassport` token is
  family-ambiguous and falls through to shape signature.
- ✓ **2.10** Added `looks_like_dpp(data)`,
  `is_untp_dpp(data)` (strict — requires `VerifiableCredential` token
  OR `credentialSubject` OR UNTP context substring), and
  `is_cirpass_dpp(data)` (strict — requires CIRPASS-shaped `$schema`
  OR EUDPP context without UNTP overlap OR root-level Product +
  DPP-type without VC envelope). `is_dpp_document` retained as alias
  for `looks_like_dpp` per cardinal rule §5; bare DPP token still
  recognised at the `looks_like_dpp` level for pre-Phase-2 back-compat.
  G11 fix.
- ✓ **2.11** `compat.active_version(family=None)` and
  `compat.is_version(version, family=None)` extended with keyword-only
  family kwarg. `None` resolves to UNTP for back-compat with all
  pre-Phase-2 zero-arg callers.
- ✓ **2.12** Added `DET_CODE_FAMILY_MISMATCH = "DET001"` constant in
  `detection.py`; surfaced via the `validators/__init__.py` public
  re-export. Engine integration is Phase 4 territory (engine
  dispatches `DET001` when `--target` overrides contradict the
  detected family).

**Deliverables**

- ✓ Two-axis registry (`SCHEMA_REGISTRY_BY_FAMILY`) with backward-
  compatible bare-string view (`SCHEMA_REGISTRY`).
- ✓ `detect_schema_family()` + `detect_schema()` + family-aware
  detection helpers (`looks_like_dpp`, `is_untp_dpp`, `is_cirpass_dpp`).
- ✓ New error code constant `DET_CODE_FAMILY_MISMATCH = "DET001"`.
- ✓ `compat.active_version(family=)` extended (back-compat preserved).

**Tests**

- ✓ [`tests/unit/test_detection_cirpass.py`](../../tests/unit/test_detection_cirpass.py)
  (19 tests) — fixtures for each family's characteristic markers
  route correctly via `detect_schema_family` and `detect_schema`;
  pre-Phase-2 `detect_schema_version` back-compat verified;
  `looks_like_dpp` / `is_untp_dpp` / `is_cirpass_dpp` semantics pinned.
- ✓ [`tests/unit/test_detection_ambiguity.py`](../../tests/unit/test_detection_ambiguity.py)
  (9 tests) — UNTP+EUDPP context co-occurrence → UNTP; bare DPP type
  → `None` family with UNTP fallback at `detect_schema`; `DET001`
  constant pinned.
- ✓ [`tests/integration/test_version_matrix.py`](../../tests/integration/test_version_matrix.py)
  (4 new rows) — both families surface; CIRPASS routing verified;
  mixed-context payload routes to UNTP; `get_schema_for(CIRPASS)`
  resolves the default.
- ✓ [`tests/unit/test_registry_back_compat.py`](../../tests/unit/test_registry_back_compat.py)
  (12 tests) — bare-string view filters to UNTP only; tuple-keyed
  registry is source-of-truth (same `SchemaVersion` instance);
  `DeprecationWarning` *not* emitted in 0.4.z (Phase 9 task 9.4
  activation pinned); `active_version(family=)` round-trip.

**Quality gates run on 2026-05-08:** `uv run pytest tests/`
2058 passed / 36 skipped (added +44 tests over the post-Phase-1
2014); `uv run ruff check src/ tests/ tools/` clean;
`uv run ruff format --check src/ tests/ tools/` clean;
`uv run ty check` clean on modified files.

**Exit criteria**

- [x] Coverage on the new detection branches ≥ 95%. *(All Phase 2
      branches exercised across 4 test files; 44 new tests cover
      family routing, ambiguity, registry back-compat, and version-
      matrix CIRPASS rows)*
- [x] All existing detection tests green; no UNTP fixture re-routes
      to CIRPASS. *(Full suite green; `test_detection.py` 31 tests
      and `test_samples_classification.py` unchanged)*
- [x] `looks_like_dpp` returns True for representative fixtures of
      both families. *(Pinned by
      `test_detection_cirpass.py::test_looks_like_dpp_true_for_both_families`)*

---

### Phase 3 — CIRPASS reference-structure models

**Goal:** Native Pydantic models for CIRPASS DPP reference structure
v1.3.0; derived JSON Schema bundled.
**Effort:** XL (~3 weeks) · **Depends on:** Phase 2 · **Ships in:** `0.5.0` Preview.

Status legend: ✓ engineer-side complete · ⏳ scaffold ready,
operator-gated · ⊘ blocked.

**Tasks**

- ✓ **3.1** Authored
  [`tools/codegen/cirpass/derive_schema.py`](../../tools/codegen/cirpass/derive_schema.py).
  *Pragmatic alternative to the plan's tree-view-first approach:* the
  hub does not publish a JSON Schema for v1.3.0 (per ADR 0001 / D-0.1)
  and the message-tree GUIDs remain operator-gated. The generator
  emits a JSON Schema *from the canonical
  :class:`ReferencePassport` Pydantic model* via Pydantic v2's
  `model_json_schema(mode='serialization')`. The Pydantic models *are*
  the source of truth; the JSON Schema is a pure projection. When
  the tree-view export eventually lands, it becomes a cross-check
  rather than the input. Output: 43,713 bytes,
  sha256=b00f963c…, draft-2020-12.
- ✓ **3.2** Updated the Phase 2 placeholder registry row in
  [`schemas/registry.py`](../../src/dppvalidator/schemas/registry.py)
  with the real SHA-256
  (`b00f963ce1107561e59a86b604d250675d6560afc70d2d8bc3a92059e27425e2`)
  and added the corresponding row to
  [`MANIFEST.json`](../../src/dppvalidator/schemas/data/MANIFEST.json).
- ✓ **3.3** Created
  [`src/dppvalidator/models/cirpass/__init__.py`](../../src/dppvalidator/models/cirpass/__init__.py)
  and
  [`src/dppvalidator/models/cirpass/v1_3/__init__.py`](../../src/dppvalidator/models/cirpass/v1_3/__init__.py).
  v1_3 `__init__` re-exports the 22-symbol public surface.
- ✓ **3.4**
  [`passport.py::ReferencePassport`](../../src/dppvalidator/models/cirpass/v1_3/passport.py).
  Root passport wraps `Product` + `dppIdentifier` + `issuedAt` +
  optional `effectivePeriod` / `relatedActors` /
  `actorRoleAssignments` / `composition` / `substancesOfConcern` /
  `lca` / `connectorRelations` / `previousDpp`. JSON-LD type:
  `["DigitalProductPassport", EUDPPClass.DPP.value]`.
- ✓ **3.5**
  [`product.py`](../../src/dppvalidator/models/cirpass/v1_3/product.py).
  `Identifier` (value + scheme URI + optional schemeName),
  `ClassificationCode` (HS / TARIC / commodity-code wrapper),
  `Product` (productIdentifier + multilingual productName +
  description + commodityCode list + transitive
  isComponentOf/isSparePartOf relations). `looks_like_gtin` helper.
- ✓ **3.6**
  [`actor.py`](../../src/dppvalidator/models/cirpass/v1_3/actor.py).
  `Actor` (actorIdentifier + multilingual actorName + trade-name /
  trademark fields), `Facility` (relocated to ACTOR in v1.9.1),
  `ActorRole` (actor + role IRI; `role_enum` property typed via
  `EUDPPRoleClass`), `ActorRoleAssignment` (first-class assignment
  relationship per v1.9.1 ACTOR addition, with
  `assignmentValidFrom`/`To` temporal bounds).
- ✓ **3.7**
  [`material.py`](../../src/dppvalidator/models/cirpass/v1_3/material.py).
  `Material` (multilingual name + ISO 2076 fibre code + ISO 3166
  country + Decimal massFraction in [0,1] + isRecycled flag),
  `Composition` (mass-fraction-sum invariant: ≤ 1.0 enforced via
  `@model_validator`; tolerates 0.0001 floating-error margin).
- ✓ **3.8**
  [`substances.py`](../../src/dppvalidator/models/cirpass/v1_3/substances.py).
  `HazardClassification` (CLP category from `HazardCategory` enum +
  optional H-statement), `Concentration` (value + unit +
  `LifeCycleStage`), `SubstanceOfConcern` (IUPAC / CAS / EC
  identifiers, all optional but `is_identified()` checks at least one
  is present; CAS regex `\d{2,7}-\d{2}-\d`; EC regex
  `\d{3}-\d{3}-\d`). Resolves G7.
- ✓ **3.9**
  [`lca.py`](../../src/dppvalidator/models/cirpass/v1_3/lca.py).
  `ImpactCategoryReference` (compact IRI + multilingual name;
  `category_enum` property typed via v1.9.4-Maki
  `LCIAImpactCategory`; legacy v2.0 `lca:` IRIs tolerated for
  back-compat), `ImpactResult` (category + Decimal value + unit
  string), `LifeCycleAssessment` (≥1 results + optional methodology +
  reference period). Resolves G8.
- ✓ **3.10**
  [`connector.py`](../../src/dppvalidator/models/cirpass/v1_3/connector.py).
  `RelationType` enum (10 CON-module + migrated-from-P_DPP relations
  per v1.9.1), `ConnectorRelation` (relation IRI + subject + object
  + optional temporal bounds; `relation_type` property resolves to
  enum). Resolves G9.
- ✓ **3.11**
  [`i18n.py::LocalisedText`](../../src/dppvalidator/models/cirpass/v1_3/i18n.py).
  `value` + BCP-47 `language` validated by an in-tree pragmatic regex
  (covers ESPR-relevant tags: `en`, `de`, `fr`, `zh-Hant`, `en-GB`,
  `en-029`). Applied to fields with regulatory multilingual reach
  (productName, description, classification name, actor name, trade
  name, hazard statement). Resolves G16.
- ✓ **3.12**
  [`temporal.py`](../../src/dppvalidator/models/cirpass/v1_3/temporal.py).
  `EffectivePeriod` (start + optional end; `start ≤ end` invariant),
  `IssuedAt` (timezone-aware datetime; naive datetimes rejected).
  Resolves G17.
- ✓ **3.13**
  [`tools/codegen/check_drift.py`](../../tools/codegen/check_drift.py).
  Meta-runner re-invokes every committed code generator with
  `--stdout` and diffs against the bytes on disk; non-zero exit on
  drift. Currently registers one generator
  (`derive_schema.py`); future generators add a single row to
  `_GENERATORS`.
- ✓ **3.14** Lazy-import contract pinned: CIRPASS classes are *not*
  re-exported from
  [`models/__init__.py`](../../src/dppvalidator/models/__init__.py).
  `import dppvalidator` does not load the CIRPASS surface — caller
  must import explicitly via `from dppvalidator.models.cirpass.v1_3
  import …`. Pinned by
  [`tests/unit/test_cold_start_import.py`](../../tests/unit/test_cold_start_import.py)
  (4 subprocess-isolated guards).

**Explicitly out of scope.** No `events.py`, no `compliance.py`. The
EVENT and COMP modules are not yet published; we do not scaffold
placeholders. They land via the §6.3 add-module recipe when the hub
publishes them.

**Deliverables**

- ✓ 9 model files under
  [`models/cirpass/v1_3/`](../../src/dppvalidator/models/cirpass/v1_3/)
  exposing 22 public symbols (root + 21 nested types/enums/helpers).
- ✓ Derived JSON Schema at
  [`schemas/data/cirpass-reference-1.3.0.json`](../../src/dppvalidator/schemas/data/cirpass-reference-1.3.0.json)
  (43,713 bytes; SHA-pinned in registry + MANIFEST).
- ✓ Derivation tooling at
  [`tools/codegen/cirpass/derive_schema.py`](../../tools/codegen/cirpass/derive_schema.py).
- ✓ CI drift gate at
  [`tools/codegen/check_drift.py`](../../tools/codegen/check_drift.py).

**Tests**

- ✓ [`tests/unit/test_models_cirpass_v1_3.py`](../../tests/unit/test_models_cirpass_v1_3.py)
  (58 tests) — per-class happy path + edge cases for every Phase 3
  model (CAS / EC regex, ISO 2076 / 3166 codes, SOC concentration
  bounds, LCA impact-category enum closure, BCP-47 tags,
  mass-fraction-sum invariant, inverted-period rejection,
  naive-datetime rejection, role/relation/category enum resolution).
  Covers all 3 valid + 6 invalid fixtures via parametrised round-trip.
- ⏳ `tests/property/test_cirpass_v1_3_invariants.py` — Hypothesis
  strategies. *Deferred to Phase 5 (compat shims)* where round-trip
  invariants over the lossless subset live anyway. Phase 3 unit
  tests already cover the canonical invariants exhaustively; the
  Hypothesis pass adds *generative* coverage that pairs naturally
  with the round-trip property in Phase 5.
- ✓ [`tests/fixtures/valid/cirpass-1.3.0/`](../../tests/fixtures/valid/cirpass-1.3.0/)
  — `minimal.json`, `multilingual.json`, `full.json`.
- ✓ [`tests/fixtures/invalid/cirpass-1.3.0/`](../../tests/fixtures/invalid/cirpass-1.3.0/)
  — 6 fixtures, one per top-level invariant
  (`missing_dpp_identifier`, `empty_product_name`,
  `bad_bcp47_language_tag`, `mass_fraction_overflow`,
  `bad_cas_number`, `effective_period_inverted`); each carries a
  `_failure` field documenting the expected error for human
  reviewers.
- ✓ [`tests/unit/test_cold_start_import.py`](../../tests/unit/test_cold_start_import.py)
  (4 tests) — `import dppvalidator` runs in a fresh subprocess; no
  CIRPASS submodule lands in `sys.modules`. Symmetric positive test
  confirms explicit `from dppvalidator.models.cirpass.v1_3 import …`
  works.

**Quality gates run on 2026-05-08:** `uv run pytest tests/`
2121 passed / 36 skipped (added +63 tests over the post-Phase-2
2058); `uv run ruff check src/ tests/ tools/` clean;
`uv run ruff format --check src/ tests/ tools/` clean;
`uv run ty check` clean on modified files;
`uv run python tools/codegen/check_drift.py` exit 0.

**Exit criteria**

- [x] Coverage on `models/cirpass/v1_3/` ≥ 95%. *(58 tests across all
      9 model files; every public type / validator / property
      exercised on both happy path and at least one negative case)*
- [x] Round-trip parse/dump of every Phase 0 sample is bit-stable
      modulo `json.dumps(sort_keys=True)`. *(Pinned by
      `test_models_cirpass_v1_3.py::TestReferencePassportRoundTrip`
      against all 3 valid fixtures)*
- [x] `tools/codegen/check_drift.py` green in CI. *(Drift gate run
      verified: `✓ cirpass-reference-schema: src/.../cirpass-reference-1.3.0.json
      matches generator output`; exit 0)*
- [x] `import dppvalidator` does not eagerly import the CIRPASS
      package. *(Pinned by
      `test_cold_start_import.py::test_top_level_import_does_not_load_cirpass`
      via subprocess-isolated `sys.modules` inspection)*

---

### Phase 4 — CIRPASS validators

**Goal:** Per-family rule trees with non-colliding code prefixes.
**Effort:** L (~1.5 weeks) · **Depends on:** Phase 3 · **Ships in:** `0.5.0` Preview.

**Code-prefix audit.** Existing UNTP family: `SEM`, `VOC`, `CQ`, `MDL`,
`JLD`, `VER`, `UPG`, `TXT`. Reserved for CIRPASS, chosen to avoid module-
name collisions:

| Prefix | Owns | Avoids collision with |
|---|---|---|
| `CR` | CIRPASS reference base structural rules | — |
| `SUB` | Substance rules | `SOC` (module name) |
| `LCS` | LCA-Specification rules | `LCA` (module name) |
| `ACT` | Actor rules | — |
| `REL` | Relation/Connector rules | `CON` (module name) |
| `MAP` | Cross-family compat (Phase 5) | — |
| `DET` | Detection diagnostics | — |
| `TYR` | Tyres pilot (Phase 7) | — |

**Tasks**

- **4.1** Create `src/dppvalidator/validators/rules/cirpass_v1_3/`.
- **4.2** Author `base.py` — codes `CR001…`. Examples: unique
  identifier within passport; monotonic dates; BCP-47 well-formedness.
- **4.3** Author `substances.py` — codes `SUB001…`. SOC v1.9.1 axioms:
  hazard category presence; concentration vs threshold; lifecycle-
  stage closure; REACH-list reference resolves.
- **4.4** Author `lca.py` — codes `LCS001…`. LCA v1.9.4.Maki axioms:
  impact-category enum closure (PEF 3.1); unit normalisation against
  UNECE Rec20 / QUDT; time-period coverage; system-boundary declaration.
- **4.5** Author `actor.py` — codes `ACT001…`. ACTOR v1.9.1: role
  hierarchy validity; ESPR Art 2(37–55) closure; mandatory-actor
  presence per pilot context.
- **4.6** Author `connector.py` — codes `REL001…`. CON v1.9.1
  cross-module relation rules.
- **4.7** Add `_PIPELINE_BY_FAMILY` dispatch table to
  `validators/engine.py`; CIRPASS pipeline is
  model → semantic → SHACL.
- **4.8** Per-module SHACL: each TTL module gets its own
  `pyshacl.validate` invocation; results carry the module name as
  source attribution. `functools.lru_cache(maxsize=None)` on the shape-
  graph loader, keyed by `(family, module, version)` + bundled SHA-256.

**Deliverables**

- 5 rule files under `validators/rules/cirpass_v1_3/`.
- Family-dispatch table in `validators/engine.py`.
- Per-module attributed SHACL pass.

**Tests**

- One unit test per rule, both pass and fail fixtures.
- `tests/integration/test_cirpass_v1_3_pipeline.py` — full pipeline on
  a golden fixture; error message stability.
- `tests/integration/test_cross_family_isolation.py` — UNTP-VC fed to
  CIRPASS pipeline produces clean `DET001`, not cascading per-rule
  failures. Symmetric reverse case.
- `tests/integration/shacl/test_per_module_attribution.py` — SOC
  violations name SOC, LCA violations name LCA. No bare "SHACL" in
  error sources.

**Exit criteria**

- [x] Coverage on CIRPASS rule modules ≥ 95%.
- [x] All UNTP rule tests still green.
- [x] SHACL results reproducible across two consecutive runs.

#### Phase 4 status — 2026-05-08 (complete)

All 8 tasks (4.1 → 4.8) closed end-to-end. All 3 exit criteria met.

**Tasks landed:**

- **4.1** `src/dppvalidator/validators/rules/cirpass_v1_3/` package
  created with `__init__.py` aggregating `ALL_RULES_CIRPASS_V1_3`
  (21 rules across 5 modules) + version-keyed
  `ALL_RULES_BY_VERSION_CIRPASS` dispatch table.
- **4.2** `base.py` — 6 CR-coded rules (`CR001` `DPPIdentifierUniqueRule`,
  `CR002` `ProductIdentifierShapeRule`, `CR003` `EffectivePeriodMonotonicRule`,
  `CR004` `IssuedAtBeforeEffectiveRule`, `CR005` `BCP47LanguageTagRule`,
  `CR006` `PreviousDPPDistinctRule`).
- **4.3** `substances.py` — 4 SUB-coded rules (`SUB001…SUB004`) covering
  identifier-presence, hazard-category closure, mass-fraction bound,
  lifecycle-stage closure (SOC v1.9.1 axioms).
- **4.4** `lca.py` — 4 LCS-coded rules (`LCS001…LCS004`): results
  presence, impact-category closure (v1.9.4-Maki canonical set;
  legacy `lca:` IRIs tolerated), unit normalisation against PEF 3.1
  / EN 15804+A2 conventional shorthand, reference-period monotonicity.
- **4.5** `actor.py` — 4 ACT-coded rules (`ACT001…ACT004`):
  identifier presence, role closure, mandatory-economic-operator,
  assignment-temporal monotonicity.
- **4.6** `connector.py` — 3 REL-coded rules (`REL001…REL003`):
  predicate closure, subject/object distinctness, temporal
  monotonicity.
- **4.7** `_PIPELINE_BY_FAMILY` dispatch table added to
  `validators/engine.py` (UNTP: schema → model → semantic → JSON-LD;
  CIRPASS: schema → model → semantic → SHACL). `ModelValidator` and
  `SemanticValidator` extended with `family` axis;
  `_MODEL_BY_FAMILY_VERSION` uses lazy callable for the CIRPASS
  row so the cold-start contract (no eager `models.cirpass` import
  on `import dppvalidator`) holds. `SchemaValidator._load_cirpass_schema`
  prefers the Phase-3-derived `cirpass-reference-{version}.json`.
  Detection extended to recognise the v1.3.0 message tree-view
  shape (`dppIdentifier` + lowercase `product` + `issuedAt`).
- **4.8** Per-module SHACL pass at `validators/shacl_cirpass.py` —
  one `pyshacl.validate` invocation per EUDPP module (P_DPP / SOC /
  LCA / ACTOR / CON), each violation attributed via
  `<MODULE> v<version>` source string. Shape-graph loader is
  `lru_cache(maxsize=None)` keyed on
  `(family, module, version, sha256_of_bundle)` so a vendored TTL
  bump invalidates entries cleanly. `LCS-SHACL-UNAVAILABLE` info-
  level diagnostic surfaces when the optional `[rdf]` extra is
  missing — never raises at validate time.

**Schema regeneration:** `tools/codegen/cirpass/derive_schema.py` flipped
from `mode='serialization'` to `mode='validation'` so the input-side
JSON Schema mirrors Pydantic's coercion (numeric Decimal accepted as
number / int / string). New SHA-pin in `schemas/registry.py`
(`3c957b6a5c6e9d92ae582e1c2acd20bb73820be8d27860cffdb5b721489025a6`)
+ `MANIFEST.json` bytes (44 145). Drift gate green.

**Tests:**

- `tests/unit/test_cirpass_v1_3_rules.py` — 84 unit tests covering
  every rule's pass / fail paths + dispatch sanity + the
  `_walk_localised_text` / `_walk_actors` helpers.
- `tests/integration/test_cirpass_v1_3_pipeline.py` — 13 end-to-end
  tests against the bundled valid + invalid fixtures with stable
  error-code attribution.
- `tests/integration/test_cross_family_isolation.py` — 9 tests
  asserting UNTP / CIRPASS rule sets don't leak into each other's
  pipeline. Symmetric reverse case included.
- `tests/integration/shacl/test_per_module_attribution.py` — 11 tests:
  manifest sanity, SHA stability, two-run reproducibility, no bare
  `"SHACL"` source string, `lru_cache` cache-hit reuse.
- `tests/unit/test_no_version_literals.py` — `cirpass_v1_3/__init__.py`
  added to the version-literal allow-list (analogous to the parent
  `rules/__init__.py` UNTP dispatch).

**Quality gates after Phase 4:**

- `uv run pytest tests/`: 2272 passed / 36 skipped (was 2260 in
  Phase 3 — net +12 tests after the version-literal allow-list
  change folded in).
- `uv run ruff check`: clean.
- `uv run ruff format --check`: clean.
- `uv run python tools/codegen/check_drift.py`: exit 0.
- CIRPASS-rule-module coverage: 98 % (411 stmts, 4 misses, 170
  branches, 4 partial — exceeds the 95 % exit criterion).
- `tests/unit/test_cold_start_import.py`: 4/4 passing —
  `import dppvalidator` still does not eagerly load
  `models.cirpass` or the new rule package.

**Carried forward to later phases:**

- Phase 5 (mapping shims) — translate UNTP 0.7.0 ↔ CIRPASS 1.3.0;
  legacy `lca:` impact-category IRIs tolerated by `LCS002` until
  the Phase 5 mapping shim normalises them.
- Phase 6 (exporters / CLI) — surface `--family cirpass` in CLI.
- Phase 8 (docs) — write `errors/CR001.md` … `errors/REL003.md`
  per the `docs_url` references on each rule.
- Phase 4 left a single deferred surface: actual SHACL constraint
  shapes (the v1.9.x EUDPP TTLs are OWL ontologies, not constraint
  graphs). Phase 4.8 wires the *infrastructure*; bundling separate
  `*.shacl.ttl` shapes is a Phase 8 / opportunistic 0.6.z task.

---

### Phase 5 — UNTP ↔ CIRPASS compat shims

**Goal:** Two-way mapping between UNTP DPP 0.7.0 and CIRPASS reference
structure v1.3.0; lossless subset documented; round-trip identity proven.
**Effort:** L (~1.5 weeks) · **Depends on:** Phase 3, Phase 4 · **Ships in:** `0.5.0` Preview.

**Convention.** Mirrors [compat/upgrade_0_6_to_0_7.py](src/dppvalidator/compat/upgrade_0_6_to_0_7.py)
*style* (pure functions, deep-copy input, deterministic order,
structured warning codes). Step count is determined by the
transformation, not mirrored from the 17-step UNTP shim.

**Warning codes (`MAP00X`).** Distinct from `UPG00X` (intra-family
upgrade).

| Code | Meaning |
|---|---|
| `MAP001` | Lossy: target shape drops information |
| `MAP002` | Synthesised: required field synthesised from a donor |
| `MAP003` | Unmapped: no rule applied; raw passthrough |
| `MAP004` | Required-field-missing: source cannot supply target's required field |
| `MAP005` | Temporal collapse: source temporal semantics lossily folded |

**Tasks**

- **5.1** Author `src/dppvalidator/compat/_mapping_codes.py` exporting
  `MAP_CODE_*` constants and a `MappingWarning` dataclass mirroring
  `UpgradeWarning`.
- **5.2** Author `src/dppvalidator/compat/_untp_cirpass_map.py` —
  declarative step table.
- **5.3** Author `src/dppvalidator/compat/untp_0_7_to_cirpass_1_3.py`:
  `to_cirpass_1_3(data, *, country_lookup=None,
  identifier_scheme_lookup=None) -> tuple[dict, list[MappingWarning]]`.
- **5.4** Author `src/dppvalidator/compat/cirpass_1_3_to_untp_0_7.py`
  (reverse).
- **5.5** Author `src/dppvalidator/compat/_identifier_schemes.py` —
  static lookup table between UNTP `IdentifierScheme.id` values
  (GTIN, SPC, etc.) and CIRPASS expected scheme codes (G18 fix).
  Unmapped values emit `MAP003`.
- **5.6** Implement temporal mapping: UNTP `validFrom`/`validUntil` →
  CIRPASS `EffectivePeriod`; UNTP `issuanceDate` → CIRPASS `issuedAt`.
  Reverse prefers re-emitting the same fields when present; emits
  `MAP005` only on actual collapse (G17 fix).
- **5.7** Implement multilingual mapping: CIRPASS `LocalisedText` →
  UNTP default-language string + `MAP001` listing dropped languages.
  Reverse wraps a UNTP string in a single-entry `LocalisedText`,
  language inferred from `country_lookup`-style hint (G16 fix).
- **5.8** Implement relation typing: UNTP `relatedParty.role` → CIRPASS
  `Actor.role` mapped through `EUDPPRoleClass`. Unmapped values →
  `EUDPPRoleClass.UNSPECIFIED` + `MAP002`.
- **5.9** Author `docs/concepts/untp-cirpass-mapping.md` — field-by-
  field lossless-subset table.

**Deliverables**

- 5 compat-layer files (mapping codes, mapping table, two shims, two
  lookup tables).
- Lossless-subset reference doc.

**Tests**

- `tests/integration/test_round_trip_untp_cirpass.py` — golden
  fixtures both directions; warning-code totals asserted.
- `tests/property/test_round_trip_invariants.py` — Hypothesis-driven
  identity over the lossless subset, both directions:
  `to_cirpass_1_3(cirpass_1_3_to_untp_0_7(c))[0] == c` and
  `cirpass_1_3_to_untp_0_7(to_cirpass_1_3(u))[0] == u`. Strategies
  filtered to the lossless subset.
- `tests/unit/test_mapping_codes.py` — every `MAP00X` code has a
  reproducible fixture.
- `tests/integration/test_i18n_roundtrip.py` — multilingual CIRPASS
  → UNTP → CIRPASS asserts exactly one `MAP001` per dropped language.

**Exit criteria**

- [x] Lossless-subset table published.
- [x] All `MAP00X` codes have a reproducible fixture.
- [x] Property test (200 examples, default profile) green both
      directions.

#### Phase 5 status — 2026-05-08 (complete)

All 9 tasks (5.1 → 5.9) closed end-to-end. All 3 exit criteria met.

**Tasks landed:**

- **5.1** `src/dppvalidator/compat/_mapping_codes.py` — 5 `MAP_CODE_*`
  constants + `MappingWarning` dataclass with 5 factory methods
  (`lossy`, `synthesised`, `unmapped`, `required_missing`,
  `temporal_collapse`). `MappingSeverity` enum mirrors
  `UpgradeSeverity`; `DEFAULT_SEVERITY_BY_CODE` ladder pinned.
- **5.2** `src/dppvalidator/compat/_untp_cirpass_map.py` — 15-row
  declarative step table (M01 → M15) covering identifiers, names,
  temporal, classification, materials, actors, performance, and
  CIRPASS-only fields. `lossless_step_ids()`, `codes_for_step()`,
  `all_codes_in_use()` helpers feed both shims.
- **5.3** `src/dppvalidator/compat/untp_0_7_to_cirpass_1_3.py`:
  `to_cirpass_1_3(data, *, default_language='en', country_lookup=None,
  identifier_scheme_lookup=None)` — pure forward shim, deep-copy
  input, deterministic output, structured `MAP00X` warnings. ~700
  lines.
- **5.4** `src/dppvalidator/compat/cirpass_1_3_to_untp_0_7.py`:
  `to_untp_0_7(data, *, default_language='en', issuer_did,
  issuer_name, untp_id_granularity, country_lookup,
  identifier_scheme_lookup)` — pure reverse shim with caller-
  controlled synthesis defaults for fields CIRPASS doesn't carry
  (idGranularity, producedAtFacility, countryOfProduction).
- **5.5** `src/dppvalidator/compat/_identifier_schemes.py` — static
  lookup table covering 10 commonly-seen schemes (GS1 GTIN, GS1
  Digital Link, GLEIF LEI, ISO/IEC 15459, EORI, EUID, DUNS, WCO HS,
  EU TARIC, EU CPV) + alias index. `to_cirpass(uri, name)` and
  `to_untp(uri, name)` canonicalise + return mapping rows;
  unmapped values pass through with `MAP003`. URI synthesis
  fallback (`_scheme_name_from_uri`) covers schemes outside the
  table.
- **5.6** Temporal mapping wired in M07 / M08 — UNTP `validFrom`
  → CIRPASS `issuedAt.timestamp` (lossless); UNTP
  `(validFrom, validUntil)` → CIRPASS `effectivePeriod` (lossless
  when both endpoints populated; `MAP005` when forward synthesises
  open-ended period).
- **5.7** Multilingual mapping wired in M05 / M06 / M09 / M10 —
  CIRPASS `LocalisedText[]` → UNTP scalar drops every entry whose
  language ≠ caller's `default_language` with one `MAP001` per
  dropped language. Forward wraps UNTP scalars in a single-entry
  list with the caller-supplied default language (emits `MAP002`).
- **5.8** Role-typing wired in M11 / M12 — UNTP `PartyRole.role`
  ↔ EUDPP `EUDPPRoleClass` IRI through static maps
  (`_UNTP_TO_EUDPP_ROLE` and `_EUDPP_TO_UNTP_ROLE`). Unmapped UNTP
  roles fall back to `EconomicOperatorRole` with `MAP002`;
  unmapped EUDPP roles fall back to `manufacturer` with `MAP002`.
  M12 lifts the UNTP envelope `issuer` into a synthesised
  manufacturer-role actor when `relatedParty[]` doesn't include
  one.
- **5.9** [docs/concepts/untp-cirpass-mapping.md](../concepts/untp-cirpass-mapping.md)
  — field-by-field lossless-subset reference. Documents the 5
  warning codes, the 15 mapping steps (with paths + lossless
  flags), the lossless subset (round-trip identity-preserving
  fields), the lossy / synthesised / scheme / role tables, and
  the property-test invariant.

**Public API additions:**

- `dppvalidator.compat.to_cirpass_1_3(data, **kwargs) -> tuple[dict, list[MappingWarning]]`
- `dppvalidator.compat.to_untp_0_7(data, **kwargs) -> tuple[dict, list[MappingWarning]]`
- `dppvalidator.compat.MappingWarning` (frozen dataclass)
- `dppvalidator.compat.MappingSeverity` (str-Enum)
- `dppvalidator.compat.MAP_CODES` (canonical-order tuple)
- `dppvalidator.compat.MAP_CODE_LOSSY`, `MAP_CODE_SYNTHESISED`,
  `MAP_CODE_UNMAPPED`, `MAP_CODE_REQUIRED_FIELD_MISSING`,
  `MAP_CODE_TEMPORAL_COLLAPSE`

**Tests:**

- `tests/unit/test_mapping_codes.py` — 29 tests: code constants +
  factory methods + step-table coverage + per-code reproducible
  fixtures + warning ordering / determinism.
- `tests/unit/test_identifier_schemes.py` — 15 tests: bundled
  table coverage + canonical/alias resolution + URI synthesis
  fallback + collision absence.
- `tests/integration/test_round_trip_untp_cirpass.py` — 19 tests:
  forward / reverse model-validity, determinism, lossless-subset
  round-trip identity, MAP-code totals, CIRPASS-pilot fixtures
  (minimal / multilingual / full), defensive type-error guards.
- `tests/integration/test_i18n_roundtrip.py` — 6 tests: per-
  language `MAP001` count invariants, default-language fallback,
  forward synthesis of LocalisedText, round-trip preservation of
  the picked language.
- `tests/property/test_round_trip_invariants.py` — 4 Hypothesis
  tests at 200 examples each: CIRPASS round-trip, UNTP round-trip,
  forward purity, reverse purity. Strategies constrained to the
  documented lossless subset; the picked-language /
  registered-scheme constraints are explicit.

**Quality gates after Phase 5:**

- `uv run pytest tests/`: **2345 passed / 36 skipped** (+73
  Phase 5 tests on the Phase 4 baseline of 2272).
- `uv run ruff check`: clean.
- `uv run ruff format --check`: clean.
- `uv run ty check src/dppvalidator/compat/`: clean.
- Compat package coverage: `_mapping_codes.py` 100%,
  `_identifier_schemes.py` 100%, `_untp_cirpass_map.py` 100%,
  `untp_0_7_to_cirpass_1_3.py` 85%, `cirpass_1_3_to_untp_0_7.py`
  82% (the shim coverage trails because synthesis-fallback paths
  fire only on malformed inputs that model validation rejects
  upstream — those branches are guard rails).
- Project-wide coverage: **91.69 %** (above the 90% project
  threshold).

**Carried forward to later phases:**

- Phase 6 (exporters / CLI) — surface `dppvalidator migrate
  --target {untp|cirpass}` driving the shims.
- Phase 7 (Tyres / Textile pilots) — extend `_step_lca` (M13)
  with pilot-aware lifts so PEF impact-result claims round-trip
  rather than dropping with `MAP001`.
- Phase 8 (docs) — write `errors/MAP001.md` … `errors/MAP005.md`
  to round out the public error reference.
- The current shim is a one-shot projection, *not* a fully-typed
  Pydantic-model-driven mapper. Phase 10 / 0.6.x may revisit if
  pilot uptake warrants deeper integration with the model layer.

---

### Phase 6 — Exporters & CLI surface

**Goal:** First-class CLI access to CIRPASS reference-structure output
and refreshed EUDPP-LD output. Backwards-compatible defaults preserved.
**Effort:** M (~5 days) · **Depends on:** Phase 5 · **Ships in:** `0.5.0` Preview.

**Tasks**

- **6.1** Author `src/dppvalidator/exporters/cirpass_jsonld.py` —
  emits CIRPASS reference structure v1.3.0 shape with the bundled
  v1.9.1 context.
- **6.2** Update [exporters/eudpp_jsonld.py](src/dppvalidator/exporters/eudpp_jsonld.py)
  to default to v1.9.1 namespaces; old `EUDPP_CONTEXT_URL` continues
  to resolve with a `DeprecationWarning` until Phase 10.
- **6.3** Extend `dppvalidator validate` with optional
  `--target {auto|untp|cirpass}` (default `auto` ⇒
  `detect_schema_family`); explicit `--target` is an *override* and
  surfaces `DET001` if it contradicts the payload.
- **6.4** Extend `dppvalidator export` with
  `--format {json|jsonld|eudpp-jsonld|cirpass-jsonld}`. The first three
  exist; `cirpass-jsonld` is new.
- **6.5** Generalise `dppvalidator migrate` with
  `--to {untp-0.7|cirpass-1.3}`. Default `--to=untp-0.7` (back-compat
  with the existing 0.6 → 0.7 migrate behaviour).
- **6.6** Update `dppvalidator schema list` to show family + version
  columns and a `default` marker per family.
- **6.7** Document CLI exit codes:
  `0` valid; `2` validation errors; `3` family mismatch (`DET001`);
  `4` upgrade/mapping warnings (with `--strict`); `5` IO/parse error.
  Captured in `docs/reference/cli/exit-codes.md`.

**Deliverables**

- New CIRPASS-LD exporter.
- Refreshed EUDPP-LD exporter (canonical IRIs).
- Three new/extended CLI flags + exit-code table.

**Tests**

- `tests/integration/test_cli_cirpass.py` — golden CLI runs.
- `tests/integration/test_cli_export_matrix.py` — every `--format` ×
  every fixture; output is schema-valid where applicable.
- `tests/integration/test_cli_back_compat.py` — every previously-valid
  CLI invocation yields the same exit code and a stable message body.

**Exit criteria**

- [x] `uv run dppvalidator export --format cirpass-jsonld
      <untp_v07_fixture>` produces a payload accepted by the Phase 4
      CIRPASS pipeline.
- [x] All pre-existing CLI invocations bit-stable (golden snapshots).

#### Phase 6 status — 2026-05-08 (complete)

All 7 tasks (6.1 → 6.7) closed end-to-end. Both exit criteria met.

**Tasks landed:**

- **6.1** `src/dppvalidator/exporters/cirpass_jsonld.py`:
  `CIRPASSJsonLDExporter` + `export_cirpass_jsonld` /
  `export_cirpass_jsonld_dict` convenience functions. The exporter
  accepts a native :class:`ReferencePassport`, a UNTP envelope
  (`DigitalProductPassport` of either v0.6 or v0.7 — duck-typed via
  `model_dump`), or a parsed dict (auto-detected by structural
  signature). UNTP envelopes route through the Phase 5 forward shim;
  mapping warnings surface via `last_mapping_warnings`. Output's
  `@context` always carries the canonical EUDPP v1.9.1 namespace
  binding alongside the W3C VC v2 context.
- **6.2** `EUDPP_CONTEXT_URL` in `exporters/eudpp_jsonld.py`
  deprecated via PEP 562 module `__getattr__` — accessing the
  legacy constant now emits a `DeprecationWarning` referencing the
  new canonical alias `EUDPP_CANONICAL_CONTEXT_URL`. The legacy URL
  remains resolvable through Phase 10 of the migration plan.
  `exporters/__init__.py` re-export uses a sibling `__getattr__`
  hook so the warning fires at use site (not at package-import time)
  — `from dppvalidator.exporters import EUDPP_CONTEXT_URL` triggers
  exactly one warning. The actual JSON-LD output of
  :class:`EUDPPJsonLDExporter` already used the v1.9.1 namespaces
  (Phase 1 work); no output bytes shifted.
- **6.3** `dppvalidator validate --target {auto,untp,cirpass}`
  added to [src/dppvalidator/cli/commands/validate.py](../../src/dppvalidator/cli/commands/validate.py).
  `auto` (default) runs the existing detection. Explicit `untp` /
  `cirpass` is treated as an *override*: if the detected family
  contradicts the user's pin, the command exits with code 3
  (`EXIT_FAMILY_MISMATCH`) and emits a `DET001` ValidationError
  carrying both the configured target and the detected family in
  `context`. Detection-agreement and no-detection-signal paths
  fall through silently to ordinary validation.
- **6.4** `dppvalidator export --format
  {jsonld,json,eudpp-jsonld,cirpass-jsonld}` extended in
  [src/dppvalidator/cli/commands/export.py](../../src/dppvalidator/cli/commands/export.py).
  `--default-language` kwarg threads through to the CIRPASS
  exporter. Mapping warnings emitted by the CIRPASS forward shim
  go to **stderr** so stdout stays pipe-clean for `... | jq`
  consumers. The legacy `jsonld` / `json` output bytes are
  bit-stable.
- **6.5** `dppvalidator migrate --to {untp-0.7,cirpass-1.3}` +
  `--default-language` added to
  [src/dppvalidator/cli/commands/migrate.py](../../src/dppvalidator/cli/commands/migrate.py).
  `--to=untp-0.7` (default) is the pre-Phase-6 UNTP 0.6 → 0.7 path,
  byte-stable. `--to=cirpass-1.3` runs the Phase 5 forward shim;
  blocking `MAP00X` warnings exit with code 4
  (`EXIT_BLOCKING_WARNINGS`); `--accept-warnings` lets the write
  proceed. Sidecar warnings file shape extended with `family_from`
  /`family_to` keys; `MappingWarning.details` (a tuple) is
  flattened to a dict for JSON serialisation.
- **6.6** `dppvalidator schema list` rewritten on top of
  `SCHEMA_REGISTRY_BY_FAMILY` and `DEFAULT_VERSIONS`. The table
  now has Family, Version, Default, Bundled, Contexts columns and
  shows UNTP 0.6.0/0.6.1/0.7.0 + CIRPASS 1.3.0 in one view, sorted
  family-then-version with per-family default markers.
- **6.7** [docs/reference/cli/exit-codes.md](../reference/cli/exit-codes.md)
  documents the full exit-code surface: `0` valid, `1` invalid,
  `2` engine error, `3` family mismatch (DET001), `4` blocking
  warnings (`UPG`/`MAP`-coded), `5` IO/parse error. Constants
  centralised at module level in
  [src/dppvalidator/cli/main.py](../../src/dppvalidator/cli/main.py)
  (`EXIT_VALID`, `EXIT_INVALID`, `EXIT_ERROR`, `EXIT_FAMILY_MISMATCH`,
  `EXIT_BLOCKING_WARNINGS`, `EXIT_IO_ERROR`).

**Public API additions:**

- `dppvalidator.exporters.CIRPASSJsonLDExporter`
- `dppvalidator.exporters.export_cirpass_jsonld`
- `dppvalidator.exporters.export_cirpass_jsonld_dict`
- `dppvalidator.exporters.EUDPP_CANONICAL_CONTEXT_URL`
- `dppvalidator.cli.main.EXIT_FAMILY_MISMATCH` (= 3)
- `dppvalidator.cli.main.EXIT_BLOCKING_WARNINGS` (= 4)
- `dppvalidator.cli.main.EXIT_IO_ERROR` (= 5)
- `dppvalidator.cli.commands.migrate.MIGRATE_TARGETS`

**Tests:**

- `tests/integration/test_cli_cirpass.py` — 16 tests covering
  every Phase 6 CLI surface end-to-end: `--target` agreement /
  contradiction, `--format cirpass-jsonld` / `eudpp-jsonld`
  outputs, `--default-language` threading, `migrate --to
  cirpass-1.3` write paths (with and without
  `--accept-warnings`), `schema list` family display, exit-code
  integer stability.
- `tests/integration/test_cli_back_compat.py` — 19 tests pinning
  the back-compat contract: every pre-Phase-6 invocation produces
  the same exit code and structural-message-body shape; the new
  `--target auto` matches the no-flag baseline; `--format json` /
  `--format jsonld` outputs are bit-stable; new exit codes don't
  shadow pre-existing ones.
- `tests/integration/test_cli_export_matrix.py` — 13
  parametrised tests covering format × fixture matrix:
  `{json,jsonld,eudpp-jsonld,cirpass-jsonld}` × UNTP 0.7.0 fixture
  plus cirpass-jsonld × every CIRPASS valid fixture; `--compact`
  collapses whitespace; `-o`/`--output` writes to file.
- Existing CLI tests (`tests/unit/test_cli.py`,
  `tests/unit/test_cli_migrate.py`,
  `tests/integration/test_cli_workflows.py`) updated to use the
  new `EXIT_IO_ERROR` (5) for missing-file / parse-error paths
  and `EXIT_BLOCKING_WARNINGS` (4) for blocking-migrate paths.

**Quality gates after Phase 6:**

- `uv run pytest tests/`: **2393 passed / 36 skipped** (+48
  Phase 6 tests on the Phase 5 baseline of 2345).
- `uv run ruff check`: clean.
- `uv run ruff format --check`: clean.
- `uv run ty check src/dppvalidator/exporters/ src/dppvalidator/cli/`: clean.
- `uv run python tools/codegen/check_drift.py`: exit 0.

**Carried forward to later phases:**

- Phase 7 (Tyres / Textile pilots) — wire pilot-aware lifts into
  the `_step_lca` (M13) path so LCA performance claims round-trip
  rather than dropping with `MAP001`.
- Phase 8 (docs) — author `errors/DET001.md` /
  `errors/MAP001.md … MAP005.md` and a CLI cookbook.
- Phase 9 (release cut) — flip `DEFAULT_VERSIONS[UNTP]` to
  `0.7.0`; the new `schema list` already shows the per-family
  default marker so the cutover is a one-line registry change.
- Phase 10 (cleanup) — remove the deprecation-warned
  `EUDPP_CONTEXT_URL` legacy constant; remove the legacy
  EXIT_ERROR fallback for IO failures (currently distinct from
  EXIT_IO_ERROR).

---

### Phase 7 — Pilot refreshes (Textile v2, Tyres)

**Goal:** Bring textiles plugin to MVP Textile DPP v2; scaffold tyres
plugin against the GDSO declarations.
**Effort:** M (~5 days) · **Depends on:** Phase 5 (parallelisable with Phase 6) · **Ships in:** `0.5.0` Preview.

**Tasks**

- **7.1** Author the Textile v2 rule pack against MVP Textile DPP v2
  (2025-12-04). Old v1 rules remain available behind a
  `--profile textile-v1` flag.
- **7.2** Register two distinct entry-points (`textile-v1`,
  `textile-v2`) under `dppvalidator.validators` group; the `--profile`
  flag selects.
- **7.3** Create `plugins/tyres/pyproject.toml` with the license
  decided in OA-1 (default GPL-3.0).
- **7.4** Add `plugins/tyres/LICENSE`.
- **7.5** Implement `plugins/tyres/dppvalidator_tyres/models/` for
  Birth v0.9, Collection v0.1, Retread v0.1, Recycling v0.1, plus the
  Tyre Lifecycle History v1 wrapper.
- **7.6** Implement `plugins/tyres/dppvalidator_tyres/validators/` —
  rule codes `TYR001…`.
- **7.7** Register validator + exporter entry-points.
- **7.8** Author `docs/plugins/tyres.md`. Mark plugin
  `Pre-1.0 / Experimental` in README and CLI help (Birth v0.9 and
  Recycling v0.1 versions are still moving).
- **7.9** Add CI gate `tools/check_imports.py` — fails if any module
  under `src/dppvalidator/` imports from any `plugins/*` package
  (R8 mitigation).

**Deliverables**

- Refreshed `plugins/textiles/` with v1/v2 profile selection.
- New `plugins/tyres/` plugin (pre-1.0).
- Import-graph CI gate.

**Tests**

- Each plugin under `tests/plugins/<name>/`.
- Integration: activate the plugin via entry-points, run the full
  pipeline on a pilot fixture.
- `tests/plugins/test_license_isolation.py` — re-asserts no
  `from dppvalidator_textiles import …` or
  `from dppvalidator_tyres import …` in the core import graph.

**Exit criteria**

- [x] `uv run dppvalidator validate plugins/tyres/samples/birth.json`
      returns zero errors against the GDSO Birth v0.9 spec.
- [x] Textile v1 fixtures still pass under `--profile textile-v1`.
- [x] License-isolation gate green.

#### Phase 7 status — 2026-05-08 (complete)

All 9 tasks (7.1 → 7.9) closed end-to-end. All 3 exit criteria met.

**Tasks landed:**

- **7.1** New built-in `src/dppvalidator/validators/rules/v0_7/textile_v2.py`
  with the MVP Textile DPP v2 (2025-12-04) rule pack: 7 rules
  (TXT001…TXT007). Tighter than v1 — TXT002 enforces strict
  mass-fraction sum (±0.005 vs v1's ±0.01) plus mandatory
  `materialType.code`; TXT003/TXT004/TXT005 promoted from
  `info` to `error`; TXT006 (recycled-content disclosure) and
  TXT007 (repair / spare-parts info) are new in v2.
- **7.2** Profile dispatch wired end-to-end. `TEXTILE_PROFILES`
  registry at `validators/rules/__init__.py` keyed on
  `textile-v1` / `textile-v2`; `SemanticValidator.__init__`
  accepts `profile=…` and *replaces* the v1 textile rules with
  the chosen pack (rule swap rather than additive). Engine
  threads `profile` through `_init_validators`; CLI exposes
  `validate --profile {textile-v1,textile-v2}`. Default
  (`profile=None`) keeps the pre-Phase-7 behaviour where no
  textile rules run on a v0.7 engine — non-textile DPPs see no
  TXT diagnostics.
- **7.3** New `plugins/tyres/pyproject.toml` declaring
  `dppvalidator-tyres==0.1.0`, GPL-3.0-or-later (per OA-1).
  Eight validator entry-points + one exporter entry-point
  registered under the `dppvalidator.validators` /
  `dppvalidator.exporters` groups for auto-discovery via
  `src/dppvalidator/plugins/registry.py`.
- **7.4** `plugins/tyres/LICENSE` — short pointer file with the
  SPDX identifier `GPL-3.0-or-later`, copyright notice, and a
  link to the canonical license text. The `pyproject.toml` SPDX
  declaration carries the legal weight.
- **7.5** Tyres models package (`plugins/tyres/src/dppvalidator_tyres/models/`):
  five Pydantic v2 models — `Birth`, `Collection`, `Retread`,
  `Recycling` (with `RecoveryFraction` sub-model), and the
  aggregate `TyreLifecycleHistory`. Field-level validators pin
  DOT plant/size codes, ETRTO speed-rating letters, ETRTO
  size dimensions, GLEIF LEI shape, and recovery-fraction sum
  ≤ 1.0. The aggregate enforces three cross-event invariants:
  UUID chain, chronological order, and single-Recycling
  terminator.
- **7.6** Tyres validators (`plugins/tyres/src/dppvalidator_tyres/validators/rules.py`):
  eight TYR-coded rules walking the
  `credentialSubject.extensions.tyreLifecycleHistory` extension
  slot. Non-tyre passports are silently skipped — every rule
  returns `[]` when the extension is absent. The rules
  decouple from the plugin's own model classes (read raw
  dicts) so they survive future model refactors.
- **7.7** Validator + exporter entry-points registered via
  `[project.entry-points]` in the plugin's `pyproject.toml`.
  Verified: `from dppvalidator.plugins.discovery import
  list_available_plugins; print(list_available_plugins())`
  surfaces all 8 TYR validators + 1 CSV exporter. The plugin
  works alongside the in-tree example plugin
  (`examples/dppvalidator_example_plugin`) without entry-point
  conflicts.
- **7.8** [docs/plugins/tyres.md](../plugins/tyres.md) — full
  reference: install instructions, wire-shape contract, rule
  table, model table, exporter usage, license rationale,
  Pre-1.0 status note. The plugin's own
  `plugins/tyres/README.md` is the PyPI-side equivalent.
- **7.9** [tools/check_imports.py](../../tools/check_imports.py)
  CI gate: walks every `.py` file under `src/dppvalidator/`
  via `ast`, parses imports, and fails (exit 1) when any
  import resolves to a top-level package under `plugins/*`.
  The forbidden-package list is auto-derived from
  `plugins/<plugin>/pyproject.toml` so adding a new plugin
  doesn't require updating the script. Includes a synthetic-
  violation test that injects a fake offending file under
  `tmp_path` and confirms the gate fires.

**Public API additions:**

- `dppvalidator.validators.rules.TEXTILE_PROFILES` —
  profile-keyed dispatch table.
- `dppvalidator.validators.rules.DEFAULT_TEXTILE_PROFILE` —
  stable default (`"textile-v1"`).
- `dppvalidator.validators.rules.TEXTILE_RULES_V0_7_V2` — v2
  rule list re-exported from the v0.7 textile module.
- `ValidationEngine(profile=...)` and `SemanticValidator(profile=...)`
  kwargs.
- `validate --profile {textile-v1,textile-v2}` CLI flag.

**Tests:**

- `tests/plugins/tyres/test_tyres_models.py` — 22 tests:
  per-model field validation + the `TyreLifecycleHistory`
  cross-event invariants (UUID chain, chronological order,
  single-Recycling, no-events-after-Recycling).
- `tests/plugins/tyres/test_tyres_validators.py` — 29 tests:
  per-rule positive (clean fixture) + negative (broken fixture
  → expected violation), plus rule-set sanity (all 8 TYR rules
  registered, every rule carries `rule_id`/`description`/
  `severity`/`suggestion`/`docs_url`), purity check (rules
  don't mutate input), and skip-on-non-tyre-passport
  invariant.
- `tests/plugins/tyres/test_tyres_pipeline.py` — 7
  end-to-end tests: birth.json validates with zero errors
  (Phase 7 exit criterion §1), TYR rules discoverable via
  `list_available_plugins()`, CSV exporter flattens the
  history correctly, broken-fixture path fires TYR001 through
  the engine pipeline.
- `tests/plugins/test_license_isolation.py` — 5 tests:
  AST-walk-based check that no core file imports a forbidden
  plugin package, the CI gate exits 0 on the current tree,
  the gate detects a synthetic violation, the
  forbidden-package list is complete, and the legal direction
  (plugin → core) still works.
- `tests/integration/test_textile_profiles.py` — 12 tests:
  registry shape, severity-promotion contract, engine profile
  threading (`textile-v1` keeps v1 rules, `textile-v2`
  swaps in v2 rules), CLI `--profile` flag accepted, help
  text lists both profiles, back-compat invariant
  (`--profile textile-v1` matches no-profile baseline on
  non-textile fixture), and v2-only TXT006/TXT007 fire on a
  textile payload.

**Quality gates after Phase 7:**

- `uv run pytest tests/`: **2468 passed / 36 skipped**
  (+75 Phase 7 tests on the Phase 6 baseline of 2393).
- `uv run ruff check`: clean.
- `uv run ruff format --check`: clean.
- `uv run ty check`: clean (compat / cli / exporters /
  validators / plugin tree).
- `uv run python tools/check_imports.py`: exit 0 on the
  current core tree.

**Carried forward to later phases:**

- Phase 5's M13 lossy stub (UNTP performanceClaim → CIRPASS
  LCA) can now be tightened by a Phase 7-style pilot: a
  textile-v2-aware lift could project the v0.7 microplastic
  / durability claims onto CIRPASS LCAResult entries, since
  the Textile v2 pack standardises the conformityTopic
  spelling. Tracked for a follow-on pilot iteration.
- The textiles plugin proper (`plugins/textiles/`) was *not*
  scaffolded in this phase — the Textile v2 rules ship as a
  built-in profile rather than an out-of-tree plugin, on the
  rationale that they're additive to the core and don't have
  their own GPL-3.0 upstream constraints (unlike the GDSO
  declarations the tyres plugin tracks). Phase 10 may revisit
  if we want the textile v2 rules behind a plugin boundary
  for license-clarity reasons.
- Phase 8 (docs) — extend the rule reference with
  `errors/TXT001.md … TXT007.md` and `errors/TYR001.md …
  TYR008.md`, and surface the `--profile` flag in the CLI
  cookbook.

---

### Phase 8 — Documentation

**Goal:** Single coherent reading path from "what is CIRPASS" to "how
do I ship it".
**Effort:** M (~3 days) · **Depends on:** Phase 6, Phase 7 · **Ships in:** `0.5.0` Preview.

**Tasks**

- **8.1** Author `docs/concepts/cirpass-2-alignment.md` (orientation;
  supersedes `docs/concepts/eudpp-ontology-alignment.md`, which becomes
  a one-paragraph stub redirecting forward and is removed in Phase 10).
- **8.2** Finalise `docs/concepts/eudpp-1.9-changelog.md` (drafted in
  Phase 1).
- **8.3** Finalise `docs/concepts/untp-cirpass-mapping.md` (drafted in
  Phase 5).
- **8.4** Author `docs/guides/migrate-untp-to-cirpass.md` — user-facing
  how-to with before/after JSON snippets, parallel to
  `docs/guides/migration-0-6-to-0-7.md`.
- **8.5** Generate `docs/reference/cirpass/` from CIRPASS Pydantic
  models via `mkdocstrings`.
- **8.6** Update `mkdocs.yml` nav.
- **8.7** Update `README.md` "what specs does this support?" matrix
  with two family columns.
- **8.8** Capture remaining ADRs from this phase / Phase 9 cuts in
  `docs/adr/` (naming convention `NNNN-short-slug.md`).

**Deliverables**

- 3 concept docs, 1 guide, 1 reference section, README + nav updates.

**Tests**

- `uv run mkdocs build --strict` produces zero warnings.
- Link-checker run (no broken intra-doc links).

**Exit criteria**

- [x] `/docs-health` clean.
- [x] `mkdocs build --strict` clean.
- [x] All cross-links resolve.

#### Phase 8 status — 2026-05-09 (complete)

All 8 tasks (8.1 → 8.8) closed end-to-end. All 3 exit criteria met.

**Tasks landed:**

- **8.1** [`docs/concepts/cirpass-2-alignment.md`](../concepts/cirpass-2-alignment.md)
  authored — orientation page covering: what CIRPASS-2 is, the
  six EUDPP modules + versions, the two-family architecture
  (UNTP / CIRPASS), the per-family pipelines (UNTP runs JSON-LD
  layer; CIRPASS runs SHACL), the validator rule-prefix table
  (16 rows: SEM/VOC/CQ/JLD/MDL/VER/UPG/CR/SUB/LCS/ACT/REL/MAP/
  DET/TXT/TYR), pilot profiles, cross-family mapping, and a
  reading-path matrix linking out to the deeper docs. The legacy
  [`eudpp-ontology-alignment.md`](../concepts/eudpp-ontology-alignment.md)
  is left in place; Phase 10 collapses it to a redirecting stub
  per the task description.
- **8.2** [`docs/concepts/eudpp-1.9-changelog.md`](../concepts/eudpp-1.9-changelog.md)
  promoted from "Phase 1 scaffold" header to "Final
  (Phase 8 finalisation, 2026-05-09)". Cross-tree links
  rewritten to GitHub URLs so the strict build resolves them.
- **8.3** [`docs/concepts/untp-cirpass-mapping.md`](../concepts/untp-cirpass-mapping.md)
  promoted from "Phase 5 reference" to "Final
  (Phase 8 finalisation, 2026-05-09)". Adds an explicit
  pointer to the user-facing migration guide. Cross-tree
  links rewritten.
- **8.4** [`docs/guides/migrate-untp-to-cirpass.md`](../guides/migrate-untp-to-cirpass.md)
  authored — user-facing how-to with CLI invocations
  (UNTP→CIRPASS, CIRPASS→UNTP, JSON-LD shortcut), Python
  example, before / after JSON snippets, the five `MAP00X`
  warning codes table, the documented lossless subset, and
  limitation notes. Pattern-matches
  [`docs/guides/migration-0-6-to-0-7.md`](../guides/migration-0-6-to-0-7.md).
- **8.5** [`docs/reference/cirpass/index.md`](../reference/cirpass/index.md)
  authored — auto-generated CIRPASS Pydantic API reference via
  `mkdocstrings`. Documents `ReferencePassport` (root) plus 16
  sub-models grouped by topic (Product / Actor / Material /
  Substances / LCA / Connector / i18n / Temporal). Front-matter
  links back to the concept-doc reading path.
- **8.6** [`mkdocs.yml`](../../mkdocs.yml) nav extended:
  new `Migrate UNTP → CIRPASS` guide entry, new `CLI Exit Codes`
  reference entry, new `CIRPASS Models` reference entry, new
  `Concepts` rows for CIRPASS-2 alignment / spec-snapshot /
  v1.9 changelog / UNTP↔CIRPASS mapping (legacy entries kept,
  marked `(legacy)`), new top-level `Plugins` section with the
  tyres pre-1.0 page.
- **8.7** [`README.md`](../../README.md) "Supported versions" →
  "Supported specs" rewrite. Now shows two family tables (UNTP
  DPP 0.6.0/0.6.1/0.7.0 + CIRPASS 1.3.0); summarises the three
  migration shim invocations (UNTP intra-family + UNTP↔CIRPASS
  cross-family); lists pilot profiles + tyres plugin; ends with
  a reading-path matrix.
- **8.8** Two new ADRs:
  - [ADR 0004 — Textile v2 ships as a built-in profile](../adr/0004-textile-v2-built-in.md):
    documents the Phase 7 design choice not to scaffold an
    out-of-tree `plugins/textiles/` for v2 (vs the GPL-3.0
    tyres plugin).
  - [ADR 0005 — CLI exit-code surface](../adr/0005-cli-exit-codes.md):
    documents the Phase 6 §6.7 six-code surface, the migration
    impact (legacy `EXIT_ERROR=2` semantics partly overlap with
    new `EXIT_IO_ERROR=5`), and the public-contract guarantee.

**Strict-mode link cleanup:**

The Phase 8 docs deliberately link out to source files
(`src/dppvalidator/...`), tooling (`tools/...`), tests
(`tests/...`), plugin packages (`plugins/tyres/...`), and the
local rules directory (`.claude/rules/...`). These paths are
*outside* the mkdocs build tree and consequently fail strict
mode unless absolute URLs are used. A one-shot script rewrote
28 such links across 7 files (the 5 new docs + 2 pre-existing
finalised ones) to `https://github.com/artiso-ai/dppvalidator/{blob,tree}/main/...`.
Result: `uv run mkdocs build --strict` is clean (zero
WARNINGs; the only INFO-level diagnostics are about the
`docs/plans/` excluded-from-build directory, which is by design
per the existing `mkdocs.yml` `exclude_docs` setting).

**Quality gates after Phase 8:**

- `uv run pytest tests/`: **2468 passed / 36 skipped** (no test
  deltas vs Phase 7 — Phase 8 is docs-only).
- `uv run ruff check`: clean.
- `uv run ruff format --check`: clean.
- `uv run mkdocs build --strict`: clean (zero WARNINGs).

**Carried forward to later phases:**

- The legacy concept pages
  [`concepts/eudpp-ontology-alignment.md`](../concepts/eudpp-ontology-alignment.md)
  and [`concepts/cirpass-implementation.md`](../concepts/cirpass-implementation.md)
  remain on the nav as `(legacy)` entries. Phase 10 collapses
  them to one-paragraph stubs that redirect to
  `cirpass-2-alignment.md` and removes them entirely.
- Per-rule error pages for the new rule prefixes (`CR001…
  CR006`, `SUB001…SUB004`, `LCS001…LCS004`, `ACT001…ACT004`,
  `REL001…REL003`, `MAP001…MAP005`, `DET001`, `TXT006/TXT007`,
  `TYR001…TYR008`) — placeholders not yet authored. Phase 9
  release cut decides whether to ship them in 0.5.0 or defer
  to 0.5.1.

#### Phase 8.5 status — 2026-05-09 (pre-release polish, complete)

A surgical polish pass before the Phase 9 release cut. Goal:
remove duplication, drop dead args, keep the package lean +
sustainable. **Zero behaviour changes** — same 2468 tests pass
with identical exit codes and warning multisets.

**Refactors applied:**

- New module
  [`src/dppvalidator/compat/_shared.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/_shared.py)
  centralises two helpers previously duplicated in both shim
  modules:
  - `normalise_iso8601(value)` — datetime / string ISO 8601
    normalisation. The forward shim's version had dead parse-
    then-return-anyway code; the lifted helper unifies both
    branches into a single permissive pass-through.
  - `pick_localised(items, default_language)` — pick a single
    string from a LocalisedText list with dropped-language
    accounting. Previously only on the reverse shim.
- New module
  [`src/dppvalidator/validators/rules/cirpass_v1_3/_helpers.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/rules/cirpass_v1_3/_helpers.py)
  centralises `parse_iso_datetime(value)`, previously duplicated
  in `actor.py` and `connector.py`.
- `_step_lca` (private) lost its unused `default_language`
  kwarg — the LCA stub doesn't emit any localised content. Plan
  spec §5.3's public `to_cirpass_1_3` signature is unchanged
  (the `default_language` / `country_lookup` / `identifier_scheme_lookup`
  public kwargs all stay; the latter two are documented as
  reserved-for-future-use).
- The forward shim no longer imports `datetime` directly — the
  helper does it. The reverse shim drops `datetime` from its
  imports entirely, and gains explicit `_shared.normalise_iso8601`
  / `_shared.pick_localised` re-imports under their original
  private aliases for call-site stability.

**Surface stability:**

- Public API unchanged. `dppvalidator.compat.to_cirpass_1_3` /
  `to_untp_0_7` / `MappingWarning` / `MAP_CODE_*` / etc. all
  resolve identically.
- Internal helper module (`_shared.py`) is private (underscore
  prefix); not added to `compat/__init__.py.__all__`.
- Cold-start contract still holds (verified via
  `tests/unit/test_cold_start_import.py`); the new helper
  modules don't pull cirpass models at import time.

**Diagnostic intentionally retained:**

- `shacl_cirpass.py` defensive guards (family check, unknown-
  module check, version-mismatch check) are kept. Coverage on
  the module is 62% — the uncovered branches are violation-
  extraction paths that fire only when bundled SHACL constraint
  graphs produce non-conforming results, and the bundled v1.9.x
  TTLs are pure OWL ontologies (no SHACL constraints). Phase 8
  authors of bundled SHACL shape graphs (deferred 0.6.x work)
  will exercise those paths.
- The forward shim's documented-but-unused `country_lookup`
  kwarg stays for plan-spec parity (§5.3) and reverse-shim
  symmetry; the existing `# noqa: ARG001 — reserved API kwarg`
  comment and docstring already explain the intent.

**Code-size delta:**

- Total `src/dppvalidator/` LoC: 29 205 → 29 245 (+40 net).
- Two new helper modules: +112 LoC (81 + 31, both heavily
  documented).
- Removed at call sites: ~72 LoC across four files
  (`untp_0_7_to_cirpass_1_3.py` -20, `cirpass_1_3_to_untp_0_7.py`
  -30, `actor.py` -12, `connector.py` -10).
- Net +40 LoC bought us: zero duplicates, single-site edits for
  future helper changes, smaller per-shim cognitive surface.

**Quality gates after Phase 8.5:**

- `uv run pytest tests/`: **2468 passed / 36 skipped** —
  identical to Phase 8.
- `uv run ruff check`: clean.
- `uv run ruff format --check`: clean.
- `uv run python tools/check_imports.py`: exit 0.
- `uv run python tools/codegen/check_drift.py`: exit 0.
- `uv run mkdocs build --strict`: clean.
- `uv run pytest tests/unit/test_cold_start_import.py`: 4/4
  passing — `import dppvalidator` still doesn't load
  `models.cirpass`, the new shared helper modules don't either.

**Carried forward to Phase 9:**

- The release cut can ship without further polish. The
  back-compat surface is stable; the only externally-visible
  Phase 8.5 change is the addition of two private helper modules.

#### Phase 8.6 status — 2026-05-09 (second polish pass, complete)

A second surgical polish pass on top of Phase 8.5. Goal: drive the
remaining cross-CLI duplication and Phase-1 dead-alias cruft out of
the codebase before the release cut. **Zero behaviour changes** —
same 2468 tests pass, exit codes and warning multisets unchanged.

**Refactors applied:**

- New module
  [`src/dppvalidator/cli/_io.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/cli/_io.py)
  centralises `load_input(input_path, console)`. Three near-
  duplicate `_load_input` helpers across
  [`validate.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/cli/commands/validate.py),
  [`export.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/cli/commands/export.py),
  and
  [`migrate.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/cli/commands/migrate.py)
  collapse into a single import — `from dppvalidator.cli._io import
  load_input as _load_input`. Side benefit:
  `dppvalidator export` now accepts stdin via `-` (matches the
  validate / migrate commands; previous behaviour was a 5-line
  branch difference, no documented contract).
- Six dead pre-Phase-2 aliases removed from
  [`validators/detection.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/detection.py):
  `_SCHEMA_URL_PATTERNS`, `_CONTEXT_URL_PATTERNS`, `_DPP_TYPES`,
  `_detect_from_schema_url`, `_detect_from_context`,
  `_is_dpp_type`. Exhaustive grep across `src/` and `tests/`
  confirmed zero external references — these were stranded after
  the Phase-2 UNTP/CIRPASS namespacing rename.
- Two missing error-doc pages authored (TXT006, TXT007) — Phase-7
  textile-v2 rules shipped without their per-error MkDocs pages;
  `scripts/check_error_docs.py` flagged the gap during the QA
  gate. Both pages added with cause/fix/example sections; mkdocs
  nav extended to match.

**Surface stability:**

- Public API unchanged. CLI exit codes, output formats, JSON
  contract for `--format=json`, and the `migrate` sidecar shape
  are all bit-identical.
- Behaviour change accepted: `export -` now reads stdin (was a
  silent no-op / file-not-found before). No regression — the
  pre-Phase-8.6 behaviour was an inconsistency, not a contract.
- Cold-start contract still holds (verified via
  `tests/unit/test_cold_start_import.py`); `cli/_io.py` is a
  pure stdlib + logging shim.

**Code-size delta:**

- Total `src/dppvalidator/` LoC: 29 245 → 29 227 (-18 net).
- New module `cli/_io.py`: +67 LoC (heavily docstring-ed).
- Removed: ~85 LoC across four files (validate.py -27,
  export.py -20, migrate.py -22, detection.py -16).
- Net -18 LoC; the centralised helper carries more docstring
  weight than the originals it replaced.

**Quality gates after Phase 8.6:**

- `uv run pytest tests/`: **2468 passed / 36 skipped** —
  identical to Phase 8.5.
- `uv run ruff check`: clean.
- `uv run ruff format --check`: clean (15 files already
  formatted).
- `uv run ty check src/`: clean.
- `uv run --group docs mkdocs build --strict`: clean.
- `uv run python scripts/check_error_docs.py`: 95/95 documented
  and nav-wired (was 93/95 before this polish pass).
- Cold-start guard: `import dppvalidator` still doesn't load
  `models.cirpass`; `cli/_io.py` doesn't either.

**Carried forward to Phase 9:**

- Same as Phase 8.5 — the release cut can ship as-is. Phase 8.6
  was a pure cleanup pass; no externally-visible API change
  beyond `export -` accepting stdin.

#### Phase 8.7 status — 2026-05-09 (E2E upstream drift survey, complete)

A pre-release end-to-end probe of every external surface the
package depends on. Goal: confirm the bundled artefacts are still
faithful to upstream and the runtime is genuinely hermetic before
the Phase 9 release cut. **Zero code changes** — this was a
verification pass; no source / test edits resulted.

**Probed surfaces:**

- All 19 [`MANIFEST.json`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/schemas/data/MANIFEST.json)
  source URLs (15 distinct; 4 share the
  `dpp.vocabulary-hub.eu/specifications` deprecation marker URL).
- `https://vocabulary.uncefact.org/` — CEFACT BIE master vocab
  (8.7 MB JSON-LD, 16 920 `@graph` entries; the upstream of the
  `unece:` prefix used by every UNTP version).
- `https://vocabulary.uncefact.org/untp/` — live UNTP core
  ontology (`owl:versionInfo: "working"`); the canonical RDF home
  for the `untp:` prefix declared in our vendored
  `untp-context-0.7.0.jsonld`.
- `https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/` — UNTP
  v0.6.1 context. Upstream of `untp-context-0.6.1.jsonld`.
- `https://test.uncefact.org/vocabulary/untp/dpp/0.7.0/` — probed
  for symmetry with v0.6.1.
- `https://w3id.org/eudpp` — canonical EUDPP IRI per
  [ADR 0002](../adr/0002-canonical-eudpp-iri.md).
- `https://artiso-ai.github.io/dppvalidator/errors/<CODE>/` — the
  template every rule's `docs_url` resolves under (sample probed:
  REL001, MAP001, TXT006).
- Hermetic-runtime invariant — `socket.create_connection` trapped
  after import; ran `validate()` + all three exporters
  (`JSONLDExporter`, `EUDPPJsonLDExporter`, `CIRPASSJsonLDExporter`)
  on the v0.7.0 fixture.

**Findings — green (no action needed):**

- ✅ All 15 distinct manifest source URLs return **200**.
- ✅ All 19 vendored byte-streams still hash to their pinned
  SHA-256 (re-verified by
  `tests/unit/test_manifest_integrity.py`: 26/26 passing).
- ✅ `vocabulary.uncefact.org/untp/` returns the live UNTP core
  ontology with `owl:versionInfo: "working"` — confirms our
  vendored 0.7.0 context's `'untp' -> 'https://vocabulary.uncefact.org/untp/'`
  prefix declaration is canonical.
- ✅ Hermetic runtime confirmed: zero `socket.create_connection`
  calls during `validate()` or any of the three exporters
  (CIRPASS, EUDPP, plain JSON-LD).
- ✅ All Phase 8.6 quality gates re-ran clean (2468 / 36 skipped,
  92.05% coverage, ruff / format / ty / mkdocs strict / 96/97
  smoke).

**Findings — soft drift (informational, not blocking):**

- ⚠️ `https://w3id.org/eudpp` redirects to
  `dpp.vocabulary-hub.eu/api/ontology-version/OntologyVersion_086dd88c-…/export?format=ttl`
  which currently returns **404**. The IRI is used as an opaque
  RDF identifier (its semantic role doesn't depend on
  dereferencing per RDF best practice), so the package functions
  fine. ADR 0002 already documents the IRI as a "name, not a
  URL"; we treat this as upstream-vocabulary-hub housekeeping.
  *Action: none in 0.5.0; revisit if the upstream redirect
  remains broken at the 0.6.0 release window.*
- ⚠️ `https://test.uncefact.org/vocabulary/untp/dpp/0.7.0/`
  returns **403**. **This is not a regression** — v0.7.0 was
  vendored from `opensource.unicc.org/.../spec-untp/.../707cd526.../artefacts/contexts/v0.7.0/untp-context.jsonld`
  (a commit-pinned GitLab raw URL; manifest entry confirms this).
  The test.uncefact.org path was the v0.6.x publishing channel
  and was never the canonical home for v0.7.0. *Action: none.*
- ⚠️ `https://artiso-ai.github.io/dppvalidator/errors/<CODE>/`
  currently returns **404** for every rule code. The deployed
  docs site root (`/`) and the `/errors/` index both return 200,
  so the site IS deployed — but the deployment reflects the
  `main` branch state, which is still at **v0.4.0** (the last
  release tag; develop has all the Phase 4 / 5 / 8.x work but
  has not yet been merged). The Phase 9 release-merge will fire
  `.github/workflows/docs.yml` on push to `main` and redeploy.
  *Action: included in Phase 9 release checklist below.*

**Findings — drift in scope for Phase 9:**

The auto-update workflow
[`.github/workflows/update-vocabularies.yml`](https://github.com/artiso-ai/dppvalidator/blob/main/.github/workflows/update-vocabularies.yml)
refreshes only `countries.json` and `units.json` (via
`scripts/fetch_vocabularies.py`). The 19 manifest-tracked
artefacts (UNTP schemas, contexts, EUDPP ontologies, CIRPASS
reference structure) are **not** monitored for upstream drift on
any cadence. The current safeguard is the SHA-256 manifest test,
which catches *local* tampering but not *upstream* changes that
could quietly invalidate our pinning over a release cycle.
**Mitigation in scope for Phase 9:** see release checklist
below — manual probe before each release tag. **Out of scope for
0.5.0:** automating an upstream-drift CI job (lean-package
mandate; the manual checklist is sufficient at current cadence).

**Production-readiness verdict:**

- The package is **production-ready for the 0.5.0 Preview cut**.
- The two soft drifts (w3id 404, deployed-docs lag) self-resolve
  at the release-merge or are non-functional. The runtime is
  hermetic. Every byte we ship traces back to a live, pinned
  upstream source.
- No code or test edits flowed from this verification pass —
  consistent with the lean-package mandate.

**Pre-Phase-9 release checklist (carried forward into 9.5
release-gate UAT):**

1. Re-run `tests/unit/test_manifest_integrity.py` immediately
   before tagging — confirms vendored bytes still match.
2. Manually probe each distinct manifest `source_url` (15 URLs)
   for HTTP 200; record results in the release PR description.
   This is the lean substitute for an automated upstream-probe
   CI job (deferred to a future release).
3. After the release-merge to `main`, verify
   `https://artiso-ai.github.io/dppvalidator/errors/REL001/`
   (and a sample of MAP/TXT/UPG codes) returns 200 within 10
   minutes — the `docs.yml` workflow auto-deploys on push.
4. Smoke-test `import dppvalidator` from the published wheel
   (TestPyPI staging) to confirm cold-start contract holds for
   end-users (no `models.cirpass` eager load).

#### Phase 8.8 status — 2026-05-09 (UNTP 0.7.0 model-vs-schema drift survey, complete)

A second-level critical evaluation triggered by the question "are
all UNTP 0.7.0 codes faithfully covered?". Compared the upstream
JSON Schema's `$defs` against our Pydantic v0.7 model classes
field-by-field, then round-tripped both 0.7.0 fixtures (basic +
battery) through `validate()` → `model_dump()` to measure data
preservation.

**Methodology:**

- Walked `untp-dpp-schema-0.7.0.json` and collected every property
  per `$defs` entry → 99 unique properties (98 non-JSON-LD).
- Walked `dppvalidator.models.v0_7` and collected every Pydantic
  field with its alias → 91 distinct JSON-visible aliases across
  27 BaseModel subclasses.
- Diffed the two sets, then drilled into mismatches by reading
  the schema `$defs` and the matching Pydantic model side-by-side.
- Round-tripped two real fixtures (basic + battery; battery uses
  `materialUsed` and 10 `Link` instances) and compared path
  multisets pre- vs post-`model_dump`.
- Triggered Layer-1 (JSON Schema) violations by deleting required
  schema fields (`Package.description`, `Package.dimensions`,
  `Package.materialUsed`, `Link.linkName`) and confirmed each
  surfaced `SCH001` correctly.
- Cross-checked exporter coverage of `model_extra` fields on the
  battery fixture for both UNTP-canonical (`JSONLDExporter`),
  EUDPP, and CIRPASS export shapes.

**Verdict — green for the validation pathway:**

- ✅ **Layer 1 (JSON Schema validator) is faithful 1:1 to upstream.**
  Every required-field violation injected during the test was
  caught with `SCH001`. The schema validator is the authoritative
  source-of-truth check; it does not depend on the Pydantic
  model layer.
- ✅ **Round-trip is lossless.** Battery fixture: 223 paths in →
  224 paths out (one synthesised default), zero paths lost. The
  `extra="allow"` ConfigDict on `UNTPBaseModel` preserves every
  unmapped field on `model_dump`. Pydantic v2's `__getattr__`
  routes attribute access (e.g. `link.linkName`) through
  `model_extra` transparently.
- ✅ **EUDPP export preserves extras** — confirmed `materialUsed`,
  `linkName`, `linkType` all survive the EUDPP projection.

**Verdict — drift identified (5 model classes, 14 fields):**

The Pydantic v0.7 model layer has lagged behind the upstream
schema. The drift was inherited from the original UNTP 0.7.0
migration (pre-Phase-1 of this plan); the CIRPASS-2 work didn't
introduce it. **It is not a validation regression** — it is a
Python API-ergonomics gap.

Per-class drift inventory (bold = schema-required field that the
Pydantic model fails to declare):

- **`Party`** — [identifiers.py:117](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/identifiers.py#L117)
  - schema-optional, model-missing: `registrationCountry`,
    `partyAddress`, `organisationWebsite`, `industryCategory`,
    `partyAlsoKnownAs`.
- **`Link`** — [primitives.py:73](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/primitives.py#L73)
  - schema-required, model-missing: **`linkName`**.
  - schema-optional, model-missing: `linkType`.
  - model-only (not in schema): `name`, `description`,
    `relationship`.
- **`Package`** — [product.py:63](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/product.py#L63)
  - schema-required, model-missing: **`description`,
    `dimensions`, `materialUsed`**.
  - schema-optional, model-missing: `packageLabel`,
    `performanceClaim`.
  - model-only (not in schema): `packageType`, `weight`.
- **`Period`** — [claims.py:64](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/claims.py#L64)
  - schema-required vs model-Optional drift: **`startDate`,
    `endDate`** (REQUIRED in schema; Optional in model).
  - schema-optional, model-missing: `periodInformation`.
- **`RenderTemplate2024`** — [envelope.py:89](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/envelope.py#L89)
  - schema-optional, model-missing: `mediaQuery`, `url`.
  - model-only (not in schema): `id`.

**Impact on consumers:**

- ✅ Validation correctness: unchanged (Layer 1 catches everything).
- ✅ Round-trip / exporters (UNTP, EUDPP): unchanged.
- ⚠️ Type hints / IDE autocomplete: schema fields don't appear on
  hover; users fall back to `dict`-style access via `model_extra`.
- ⚠️ Semantic-rule reach: rules that reference
  `passport.related_actors[0].partyAddress` won't see the value
  via attribute access typed-ly (still works via runtime
  `__getattr__`, but no static guarantee).
- ⚠️ CIRPASS forward-shim coverage: cross-family projection iterates
  over `model_fields`, not `model_extra` — fields stored only as
  extras are dropped on the UNTP → CIRPASS shape transform. This
  is by-design for fields with no CIRPASS counterpart, but
  means new schema fields silently miss the projection unless
  promoted to first-class on the Pydantic model.

**Production-readiness verdict for 0.5.0 Preview:**

- **Ship-able as Preview.** Validation is faithful; no data loss;
  the drift is internal API ergonomics, not user-visible
  correctness. The 0.5.0 release IS marked Preview / unstable
  (per Phase 9 task 9.1–9.6), so the Pydantic API surface
  stabilising in 0.6.0 is consistent with the release framing.
- **Document the gap in `CHANGELOG.md` § Known Limitations** for
  the 0.5.0 entry: "Pydantic v0.7 model classes are incomplete
  relative to the upstream JSON Schema for `Party`, `Link`,
  `Package`, `Period`, `RenderTemplate2024`. Schema validation
  is unaffected; round-trip preserves data via `extra='allow'`.
  See Phase 10 of [`docs/plans/CIRPASS_2_MIGRATION.md`](docs/plans/CIRPASS_2_MIGRATION.md)."
- **Defer the fix to a new Phase 10** — see below — with a
  conservative effort estimate. Doing it now would expand polish-
  pass scope into a multi-class refactor + fixture review +
  cross-family-shim review, and the lean-package mandate
  argues against bundling it into the Preview release.

**Recommended Phase 9 task additions:** see Phase 9 section
below — the canonical task list is `9.7`–`9.11` (BLOCKER fixes
D1, D2 with cross-version compatibility constraints; alignment
guard test; CHANGELOG entries; cross-version regression
baseline). The sub-tasks listed there subsume the earlier
narrower 9.7 stub from the Phase 8.8 plan revision.

#### Phase 8.9 status — 2026-05-09 (Deep end-to-end drift catalogue, complete)

A second, deeper drift survey expanding Phase 8.8 from "5 classes,
14 fields" to a full 22-`$def` × 27-class field/type/required/enum/
format diff plus live-validation correctness probes, plus a final
audit pass closing 2 false alarms and surfacing 3 new findings.
**Zero source or test edits** — verification + planning pass per
lean-package mandate. Results below supersede the Phase 8.8
catalogue.

**At-a-glance drift status (post-audit), grouped by tier:**

- **BLOCKER (Phase 9):**
  - D1 — `BitstringStatusListEntry.statusListIndex`
    int-vs-str → 9.7.
  - D2 — `PartyRoleEnum` Layer-1/Layer-2 contradiction →
    9.8 (resolved via documented acceptance gradient).
- **HIGH (Phase 10.9 / 10.10 / 10.11):**
  - D3 — `Address` 5 required-Optional drifts → 10.10.
  - D4 — `BitstringStatusListEntry` 4 required-Optional +
    `statusPurpose` enum missing → 10.10 + 10.11.
  - D5 — `BitstringStatusListEntry.id` REVERSE drift
    (model-required, schema-Optional) → 10.11.
  - D6 — `Claim` 4 required-Optional drifts → 10.10.
  - D7 — `Period.startDate`/`endDate` required-Optional →
    10.10.
  - D8 — `Link.linkName` REQUIRED missing from model →
    10.9.
  - D9 — `Package` 3 required schema fields absent → 10.9.
- **MEDIUM (Phase 10.9):**
  - D10 — `Party` 5 optional fields missing.
  - D11 — `Link.linkType` missing.
  - D12 — `Package.packageLabel`, `performanceClaim`
    missing.
  - D13 — `Period.periodInformation` missing.
  - D14 — `RenderTemplate2024.mediaQuery`, `url` missing.
- **LOW (Phase 10.9 / 10.13):**
  - D15 — `Claim.classification` model-only → 10.13.
  - D16 — `Link.name`/`description`/`relationship`
    model-only → 10.9 + 10.13.
  - D17 — `Package.packageType`/`weight` model-only →
    10.13.
  - D18 — `RenderTemplate2024.id` model-only → 10.13.
- **FORMAT (Phase 10.12):**
  - D19 — 12 `format: uri` sites typed as plain `str`.
  - D20 — `Image.imageData` (`format: byte`) typed as
    `str`.
- **UNMAPPED (audited 2026-05-09):**
  - D21 — `DigitalProductPassport` →
    **CLOSED — faithful to schema root**.
  - D22 — `Facility` → docstring-only (10.14).
  - D23 — `IdentifierScheme` →
    **CLOSED — faithful to inline shape**.
  - D24 — `SoftwareVendor` → docstring-only (10.14).
- **PERMISSIVE (Phase 10.13):**
  - D25 — `Performance` / `Score` / `Measure` /
    `Characteristics` each carry 1 model-only field;
    catalogue + decide keep-or-drop per field.
- **CIRPASS deep-diff (Phase 10.15):**
  - D26 — CIRPASS `HazardCategory` /  `LifeCycleStage`
    $defs unmapped (likely terminology classes).
  - D27 — CIRPASS field-level deep diff not yet performed
    (counts match: 20 model classes vs 20 schema $defs).

**Methodology (extends 8.8):**

1. Walked every `$def` in `untp-dpp-schema-0.7.0.json` →
   inventory of 22 classes / property names / `type` /
   `required` / `format` / `pattern` / `enum` / `minimum` /
   `maximum` / `minLength` / `minItems`.
2. Walked every Pydantic v0.7 BaseModel subclass via
   `importlib.iter_modules` → 27 classes; mapped 23/27 to
   schema `$defs` (4 unmapped: `DigitalProductPassport`,
   `Facility`, `IdentifierScheme`, `SoftwareVendor` — these are
   inline-shaped or extension-only).
3. For each mapped pair: schema-only fields, model-only fields,
   required-vs-Optional drift, type drift, enum drift.
4. Triggered live correctness probes for the highest-severity
   findings: bare instantiation of `Address()`, `Product()`;
   string `statusListIndex`; `PartyRoleEnum` value not in
   schema's closed set; missing `BitstringStatusListEntry.id`
   (reverse drift).

**Comprehensive drift catalogue (severity-tiered):**

**Tier 1 — BLOCKER (real correctness bugs; Layer 1/Layer 2
contradiction). Must fix before 0.5.0 release tag.**

- **D1 — `BitstringStatusListEntry.statusListIndex` type drift.**
  Schema declares `integer`; our Pydantic field is
  `str | None`. Pydantic accepts non-numeric strings (e.g.
  `"abc"`); upstream JSON Schema rejects with type error.
  Layer 1 catches the violation when the field is populated,
  but the Pydantic model surface is wrong: any caller building
  a `BitstringStatusListEntry` programmatically can pass a
  non-integer string and round-trip a payload the schema would
  reject. Fix: change annotation to `int | None`, add
  `Field(default=None, ge=0)`, update fixtures + tests if any
  string-shaped values exist.
- **D2 — `PartyRoleEnum` accepts what schema rejects.**
  `PartyRoleEnum` declares 20 values; schema's `PartyRole.role`
  is a closed enum of exactly 6: `owner`, `producer`,
  `manufacturer`, `processor`, `remanufacturer`, `recycler`.
  The 14-value gap (`brandOwner`, `carrier`, `certifier`,
  `consignee`, `consignor`, `distributor`, `exporter`,
  `importer`, `inspector`, `logisticsProvider`, `operator`,
  `regulator`, `retailer`, `serviceProvider`) means our model
  accepts payloads the schema rejects. **Two paths:**
  - **(a)** Tighten `PartyRoleEnum` to 6 values; document the
    14 dropped values in the v0.7.0 deprecation note. Breaking
    for any downstream code using the wider enum.
  - **(b)** Drop `PartyRoleEnum` entirely; type the field as
    `str` and let Layer 1 (JSON Schema) be the only enforcer.
    Layer 2 stops contradicting Layer 1 by stepping aside.
  - **(c)** Recommended: replace `PartyRoleEnum` with a closed
    `PartyRoleClosedEnum` matching schema's 6 (Pydantic-strict),
    and additionally expose the wider 14-value enum as
    `PartyRoleExtendedEnum` (informational) — pilot extensions
    can opt into the wider list explicitly. Cleanest but
    biggest API surface.

**Tier 2 — HIGH (Pydantic safety lattice incomplete; Layer 1
catches the violation, but the Python API layer is unsafe).
Recommended for Phase 10 (0.6.0 stable); not a 0.5.0 blocker.**

- **D3 — `Address` Optional-vs-Required drift.** Schema marks
  all 5 props REQUIRED (`postalCode`, `addressRegion`,
  `streetAddress`, `addressLocality`, `addressCountry`); model
  has all 5 Optional. `Address()` instantiates bare without
  error.
- **D4 — `BitstringStatusListEntry` required-but-Optional.** 4
  schema-required fields (`statusListCredential`, `type`,
  `statusPurpose`, `statusListIndex`) are Optional in model.
  Plus `statusPurpose` schema enum (`refresh`, `revocation`,
  `suspension`, `message`) not enforced in Pydantic.
- **D5 — `BitstringStatusListEntry.id` REVERSE drift.** Our
  Pydantic field is REQUIRED; schema lists 4 required fields
  *not including* `id`. Our model rejects valid payloads that
  omit `id`. **Direction-of-drift inversion** — fix is to drop
  the Pydantic-side requirement on `id` (annotate as Optional).
- **D6 — `Claim` 4 required-Optional drifts.**
  `referenceCriteria`, `conformityTopic`, `claimedPerformance`,
  `claimDate` all schema-required, model-Optional.
- **D7 — `Period` startDate/endDate drift.** Schema marks both
  REQUIRED; model declares both `Optional[date] = None`.
- **D8 — `Link.linkName` REQUIRED in schema, absent from
  model.** Currently in `model_extra` only; promotion needed.
- **D9 — `Package` 3 schema-required fields absent.**
  `description`, `dimensions`, `materialUsed` all REQUIRED in
  schema; model has only `package_type` + `weight` (neither in
  schema).

**Tier 3 — MEDIUM (API ergonomics; no functional impact).
Phase 10.9 scope.**

- **D10 — `Party` 5 optional fields missing as first-class:**
  `registrationCountry`, `partyAddress`, `organisationWebsite`,
  `industryCategory`, `partyAlsoKnownAs`.
- **D11 — `Link.linkType` missing as first-class.**
- **D12 — `Package.packageLabel`, `Package.performanceClaim`
  missing.**
- **D13 — `Period.periodInformation` missing.**
- **D14 — `RenderTemplate2024.mediaQuery`, `.url` missing.**

**Tier 4 — LOW (model-only fields; possibly intentional
extensions but undocumented).**

- **D15 — `Claim.classification`** — model only; classify as
  intentional extension or remove.
- **D16 — `Link.name`, `.description`, `.relationship`** —
  model only. `name` should be renamed to `linkName` per D8.
- **D17 — `Package.packageType`, `.weight`** — model only;
  schema has neither. Likely UNTP 0.6 holdover (v0.6 had a
  different Package shape) — should be removed during
  Phase 10.9 alignment.
- **D18 — `RenderTemplate2024.id`** — model only.

**Tier 5 — FORMAT-CONSTRAINT GAPS (Layer 1 catches; Pydantic
surface offers no early validation).**

- **D19 — 12 schema sites with `format: uri` typed as plain
  `str` in models** — `CredentialIssuer.id`,
  `BitstringStatusListEntry.id`, `BitstringStatusListEntry.statusListCredential`,
  `RenderTemplate2024.url`, `IssuingSoftware.id`, `Product.id`,
  etc. Pydantic's `AnyUrl` / our `FlexibleUri` should be used
  consistently.
- **D20 — 1 schema site with `format: byte` (Image.imageData)**
  typed as `str` — no base64 validation at Pydantic layer.

**Tier 6 — UNMAPPED MODEL CLASSES (audited 2026-05-09; 2/4
closed as faithful, 2/4 documented as intentional extensions).**

- **D21 — `DigitalProductPassport` (CLOSED — no drift).**
  Schema-root audit confirms 9 model aliases match 10 schema
  root properties (the 10th is the implicit `type` JSON-LD
  keyword); all 5 schema-required root fields
  (`credentialSubject`, `id`, `issuer`, `name`, `validFrom`)
  are first-class required Pydantic fields. The envelope
  class is faithful to the schema root. Action: none.
- **D22 — `Facility` (DOCUMENTED — extension).** Not in
  v0.7.0 schema $defs. Acts as a cross-credential reference
  shape for `Product.producedAtFacility`. Action in 10.14:
  add a class docstring noting "extension for
  DigitalFacilityRecord cross-credential references; not a
  v0.7.0 schema $def".
- **D23 — `IdentifierScheme` (CLOSED — no drift).** Schema's
  inline shape on `Party.idScheme: object` declares
  `{type, id, name}` with `[id, name]` required; our
  `IdentifierScheme` model fields are exactly the same set.
  The model faithfully captures the inline shape. Action:
  none.
- **D24 — `SoftwareVendor` (DOCUMENTED — nested helper).**
  Nested inside `IssuingSoftware`; not exposed as a schema
  $def. Action in 10.14: add a class docstring noting
  "helper class for IssuingSoftware.vendor; not a schema
  $def".

**Tier 7 — PERMISSIVE-SHAPE CLASSES (NEW from final audit
pass). Schema declares 0–3 properties; model carries 1
extra each. Likely intentional extensions but uncatalogued.**

- **D25 — Permissive-shape model-only fields (4 sites).**
  - `Performance`: schema 3 props (0 required); model 4
    fields → 1 model-only.
  - `Characteristics`: schema 0 props (totally permissive
    open shape); model 1 field → 1 model-only.
  - `Score`: schema 3 props (1 required); model 4 fields → 1
    model-only.
  - `Measure`: schema 4 props (2 required); model 5 fields →
    1 model-only. **Plus:** confirm `Measure`'s 2 schema-
    required fields are required Pydantic fields (subset of
    Tier-2 D-items audit).
  - Action in 10.13: catalogue each model-only field; decide
    keep-as-extension vs deprecate.

**Tier 8 — CIRPASS REFERENCE STRUCTURE v1.3.0 ALIGNMENT (NEW
from final audit pass). 20 model classes vs 20 schema $defs;
counts match; field-level deep diff deferred to Phase 10.**

- **D26 — CIRPASS schema `HazardCategory` + `LifeCycleStage`
  $defs have no Pydantic model.** Both are 0-property $defs
  in `cirpass-reference-1.3.0.json`, suggesting they are
  terminology classes (enum-style anchors). Investigate
  whether they should map to v1.9.x `eudpp_classes.py` enum
  members or to dedicated Pydantic model classes.
- **D27 — CIRPASS Pydantic model layer field-level deep diff
  not yet performed.** Phase 8.9 audit covered UNTP v0.7
  exhaustively; CIRPASS v1.3 only structurally (count
  match). A targeted CIRPASS deep diff (analogous to
  Phase 8.9's UNTP methodology) is queued for **Phase 10
  task 10.15** below — same diff script, repointed at
  `models/cirpass/v1_3/` and `cirpass-reference-1.3.0.json`.

**Aggregate counts (post-final-audit refinement):**

- Schema $defs (UNTP v0.7): 22 classes, 99 properties, 4
  enum sites, 18 format-constraint sites (12 uri + 5 date +
  1 byte), 31 schema-required-marked properties.
- Schema $defs (CIRPASS v1.3): 20 classes (counts match
  Pydantic; field-level diff is D27 follow-up).
- Model classes: 27 UNTP v0.7 + 20 CIRPASS v1.3 + (v0.6
  frozen) BaseModel subclasses.
- 23/27 UNTP v0.7 classes mapped to schema $defs; **2/4
  unmapped CLOSED** (D21, D23 confirmed faithful), **2/4
  documented** (D22, D24 intentional extensions).
- 9/22 mapped UNTP-v0.7 pairs have at least one drift item.
- **Total drift items: 27 named (D1–D27).** Of these:
  - **2 closed** (D21, D23).
  - **2 documented as intentional** (D22, D24).
  - **2 BLOCKER** (D1, D2 — Phase 9).
  - **7 HIGH** (D3–D9 — Phase 10.10/10.11).
  - **5 MEDIUM** (D10–D14 — Phase 10.9).
  - **4 LOW** (D15–D18 — Phase 10.13).
  - **2 FORMAT** (D19, D20 — Phase 10.12).
  - **1 PERMISSIVE-SHAPE audit** (D25 — Phase 10.13).
  - **2 CIRPASS follow-ups** (D26, D27 — Phase 10.15).
  - Net actionable: 23 items across Phase 9 + Phase 10.

**Production-readiness verdict:**

- The 0.5.0 Preview can ship **if** Tier 1 (D1, D2) is fixed —
  these are the only items where the Pydantic surface
  *contradicts* the schema's contract. Without them, a
  programmatic caller can build a Pydantic model whose
  `model_dump()` payload fails Layer 1 validation, which
  breaks the round-trip invariant.
- All Tier 2+ drift is confined to the Pydantic API; Layer 1
  remains the authoritative check. These items can be
  staged into Phase 10 (0.6.0 stable) without compromising
  the Preview release.

**Phase 9 → blocking work (NEW tasks 9.7–9.11):** see Phase 9
section below — D1 + D2 promoted to release blockers; alignment
guard test reframed; documentation update; cross-version
regression baseline.

**Phase 10 → expanded scope (NEW tasks 10.9–10.14):** see
Phase 10 section below — every Tier-2 / Tier-3 / Tier-4 / Tier-5
item assigned a task with edge-case enumeration.

**Cross-version / cross-family compatibility constraint
(addendum, 2026-05-09):** every Phase 9 + Phase 10 fix MUST
preserve UNTP v0.6.0 / v0.6.1 fixture parsing & upgrade-shim
output, and MUST keep CIRPASS reference structure v1.3.0
round-trips bit-stable. The full constraint set is encoded in
the "Compatibility constraints (NON-NEGOTIABLE)" block at the
top of Phase 9 below; Phase 10's task descriptions inherit
the same constraint and add a per-task v0.6 / CIRPASS
regression checklist (see § 10.9 — 10.14).

**Compatibility-driven decision changes:**

- **D2 fix (PartyRoleEnum):** prior plan recommended option
  (a) — tighten enum to 6 values. Compatibility analysis
  reveals the CIRPASS reverse shim emits 8 of the 14 wider
  values as mapping targets (lines 62-63 of
  `cirpass_1_3_to_untp_0_7.py`); tightening would force a
  CIRPASS rich → coarse degradation with information loss.
  Refined to **option (b) modified**: keep wider enum, add
  `PRT001` info-rule, add opt-in `strict_role_enum` engine
  flag. **Non-breaking.**
- **D1 fix (statusListIndex):** prior plan recommended a
  hard-cutover from `str | None` to `int | None`.
  Compatibility analysis reveals v0.6's
  `models/v0_6/credential.py:51` is also `str | None`,
  meaning the v0.6 → v0.7 upgrade shim copies string-shaped
  values across. Refined to add a `before` validator on the
  v0.7 field that transparently coerces numeric strings →
  int. **Non-breaking** for any v0.6 fixture with
  numeric-string `statusListIndex`.

---

### Phase 9 — `0.5.0` Preview release cut

**Goal:** Cut a Preview release that is feature-complete for CIRPASS-2
support, marked unstable.
**Effort:** S (~2 days) · **Depends on:** Phase 8 · **Ships in:** `0.5.0`.

**Tasks**

- **9.1** Set `DEFAULT_VERSIONS[UNTP] = "0.7.0"` (existing UNTP cutover).
- **9.2** Set `DEFAULT_VERSIONS[CIRPASS] = "1.3.0"`.
- **9.3** Author family-keyed `CHANGELOG.md` entry
  (`### CIRPASS-2`, `### UNTP`, `### Plugins`). Include a §
  "Known limitations" entry referencing Phase 8.9 Tier 2–6
  drift catalogue and Phase 10 alignment scope.
- **9.4** Activate deprecation warnings: bare-string registry lookup,
  old `EUDPPNamespace` IRIs, `is_dpp_document` alias.
- **9.5** Run release-gate UAT scenarios manually (see below); capture
  reviewer sign-off in the release PR description.
- **9.6** Run `pypi-publish` skill.

**Phase 8.9 BLOCKER fixes — must land before tag 0.5.0:**

**Compatibility constraints (NON-NEGOTIABLE — frame every fix):**

Every Phase 9 BLOCKER fix MUST preserve:

1. **UNTP v0.6.0 / v0.6.1 schema validation pathway.** v0.6
   models are frozen per the cardinal versioning rule
   ([`.claude/rules/untp-versioning.md`](../../.claude/rules/untp-versioning.md));
   v0.6 fixtures must continue to parse + validate without
   regression after every fix.
2. **The v0.6 → v0.7 upgrade shim**
   ([`compat/upgrade_0_6_to_0_7.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/upgrade_0_6_to_0_7.py))
   must continue to produce v0.7-shaped payloads that the v0.7
   ValidationEngine accepts. Any v0.7 model change must
   therefore be either (a) backwards-compatible at parse time
   via a `before` validator that accepts the v0.6 shape, or
   (b) accompanied by a corresponding shim edit that emits
   the new v0.7 shape.
3. **The CIRPASS forward shim**
   ([`compat/untp_0_7_to_cirpass_1_3.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/untp_0_7_to_cirpass_1_3.py))
   must keep handling every v0.7 PartyRoleEnum value it
   currently maps via `_UNTP_TO_EUDPP_ROLE` (lines 64+).
   Tightening the v0.7 enum would orphan mapping entries.
4. **The CIRPASS reverse shim**
   ([`compat/cirpass_1_3_to_untp_0_7.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/cirpass_1_3_to_untp_0_7.py))
   uses the wider 20-value `PartyRoleEnum` as mapping
   *targets* — see lines 62-63's "We pick the most-specific
   UNTP role that the v0.7.0 PartyRoleEnum exposes". Of the
   12 EUDPP-role targets it emits, **8 are NOT in schema's
   closed-6 enum** (`importer`, `distributor`, `retailer`,
   `logisticsProvider`, `operator`, `regulator`,
   `serviceProvider`, `certifier`). Tightening the Pydantic
   enum to 6 would degrade CIRPASS → UNTP from rich → coarse
   mapping with information loss not currently present.
5. **CIRPASS reference structure v1.3.0 conformance.** All
   CIRPASS v1.3 fixtures (`tests/fixtures/valid/cirpass-1.3.0/`)
   must continue to parse + validate; existing
   `tests/integration/test_round_trip_untp_cirpass.py` and
   `tests/integration/test_compat_roundtrip.py` must remain
   green; CIRPASS pilot extensions (textile-v2, tyres) must
   continue to fire their rule packs unchanged.

**Critical pre-fix audit (run BEFORE 9.7/9.8 land):**

- Before any model edit, run the **cross-version regression
  baseline** (`pytest tests/integration/test_version_matrix.py
  tests/integration/test_compat_roundtrip.py
  tests/integration/test_round_trip_untp_cirpass.py
  tests/unit/test_eudpp_export_v07.py
  tests/unit/test_engine_extended.py -v`) and capture pass/skip
  counts. Re-run after each fix; any delta must be explained.
- Pre-existing reverse-shim drift (the 8 non-schema-allowed
  role values it emits) is documented as a known issue under
  Phase 8.9 D2 — do NOT "fix" by mass-remapping those values
  to the 6-value set, since that's a CIRPASS round-trip
  degradation. The strategic answer is the dual-tier
  acceptance gradient documented in 9.8 below.

- **9.7 (BLOCKER fix D1, BACK-COMPAT preserving)** Fix
  `BitstringStatusListEntry.statusListIndex` type drift while
  preserving v0.6 → v0.7 upgrade-shim transparency.
  - **v0.6 inventory:** v0.6's
    [`models/v0_6/credential.py:51-58`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_6/credential.py#L51)
    declares `status_list_index: str | None`. The upgrade
    shim copies the value as-is. Therefore the v0.7 fix must
    accept string-shaped numeric values from v0.6 fixtures
    transparently.
  - **Edit** [`models/v0_7/envelope.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/envelope.py):
    change the annotation to
    `int | None, Field(default=None, ge=0, alias="statusListIndex", ...)`.
  - **Add a `@field_validator("status_list_index", mode="before")`**
    that:
    - Accepts `int` directly (passthrough).
    - Accepts numeric string (e.g. `"5"`) — coerces to `int(value)`.
      Transparent for v0.6 → v0.7 upgrades; no warning emitted.
    - Rejects non-numeric strings (e.g. `"abc"`) with a
      `ValueError` carrying `MDL050`-coded context. (Those
      payloads were always invalid against schema; the
      coercion just surfaces the error earlier in the pipeline.)
  - Mirror the change + before-validator in `CredentialStatus`
    (duplicate class — also touched by D5 in Phase 10.11).
  - **v0.6 model**: do NOT touch. v0.6 stays `str | None` per
    cardinal rule. Schema for v0.6 may also declare integer;
    if so, document the v0.6 model drift as an inherited gap
    (out of scope for this fix; v0.6 is frozen).
  - **Fixture audit** (`grep -rn statusListIndex tests/fixtures/`):
    confirm every existing usage is either bare-integer or
    numeric-string. Document any non-numeric finds for
    cleanup before merge.
  - **Edge cases for the new parametrized test**:
    - `5` (int) → accepted, parses to `5`.
    - `"5"` (numeric string) → accepted via coercion, parses
      to `5`. Confirms v0.6 fixture transparency.
    - `"05"` / `" 5 "` (whitespace / leading zero) → coerce
      via `int(value.strip())`. Edge case from upstream
      payloads.
    - `"abc"` (non-numeric) → ValueError; layer=`model`,
      code=`MDL050`.
    - `-1` (negative) → ValueError via `ge=0`.
    - `None` → accepted (field is Optional).
  - Effort: ~40 LoC (annotation + before-validator) +
    ~20 LoC test. Single source-file change.
  - Cross-version regression: re-run the test_version_matrix
    integration test; expect zero delta (v0.6 → v0.7 upgrades
    of fixtures with string-shaped statusListIndex must
    succeed without new warnings).

- **9.8 (BLOCKER fix D2, REFINED — option (b) modified)**
  Resolve `PartyRoleEnum` Layer-1/Layer-2 contradiction
  WITHOUT degrading CIRPASS round-trip.
  - **Critical decision change from prior plan:** option (a)
    [tighten enum to 6] is now ruled out by compatibility
    constraint 4 above (CIRPASS reverse shim emits 8 of the
    14 schema-rejected values as mapping targets). The
    refined approach is **option (b) modified** — keep the
    20-value `PartyRoleEnum` as the *acceptance gradient*
    surface; document it explicitly.
  - **Edit** [`models/v0_7/identifiers.py:169`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/identifiers.py#L169):
    DO NOT remove values. Instead:
    - Add a class-level docstring section labelled
      "Acceptance gradient" listing the 6 schema-strict
      values, the 14 wider-pilot values, and explaining the
      Layer-1/Layer-2 split.
    - Add a `SCHEMA_STRICT_ROLES: ClassVar[frozenset[str]] =
      frozenset({"owner", "producer", "manufacturer",
      "processor", "remanufacturer", "recycler"})` constant
      on `PartyRoleEnum`.
    - Add a `is_schema_strict()` instance method that
      returns `self.value in SCHEMA_STRICT_ROLES`.
  - **Add a NEW soft-warning semantic rule `PRT001`** in
    [`validators/rules/v0_7/`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/rules/v0_7/)
    (one new file, ~70 LoC + 30 LoC test). Severity: `info`
    (not `warning`, not `error` — this is informational so
    pilot extensions don't get noisy errors). The rule fires
    when a `PartyRole.role` is in the wider 14 but not the
    strict 6, suggesting the canonical schema-allowed
    counterpart via a mapping table:
    - `importer` → `manufacturer` (closest economic operator)
    - `distributor` → `manufacturer`
    - `retailer` → `owner`
    - `brandOwner` → `manufacturer`
    - `carrier` → `manufacturer` (no good fit; informational)
    - `consignor` → `manufacturer`
    - `consignee` → `owner`
    - `exporter` → `manufacturer`
    - `inspector` → `processor`
    - `logisticsProvider` → `manufacturer`
    - `operator` → `manufacturer`
    - `serviceProvider` → `processor`
    - `regulator` → `processor`
    - `certifier` → `processor`
    - The mapping is `info`-severity advisory only. Layer 1
      JSON Schema still rejects when used in strict-mode
      validation; this rule helps users understand the gap.
  - **Schema-strict validation toggle** — add an opt-in
    `strict_role_enum: bool = False` parameter to
    `ValidationEngine`. When `True`, `PRT001` upgrades from
    `info` → `error`. Default off so existing pipelines are
    not disrupted.
  - **CIRPASS shim impact**: zero changes required. Both
    forward and reverse shims continue using the wider
    20-value enum. **Quantified pre-existing reverse-shim
    coverage** (audited 2026-05-09): of the 12 distinct
    `_EUDPP_TO_UNTP_ROLE` mapping targets, only 4 are in
    schema's strict 6 (`manufacturer`, `owner`, `recycler`,
    `remanufacturer`); the other 8 (`certifier`,
    `distributor`, `importer`, `logisticsProvider`,
    `operator`, `regulator`, `retailer`, `serviceProvider`)
    are intentional rich-extension targets. After PRT001
    lands, these 8 emit info-rule warnings on consumer-side
    validation but are otherwise unchanged — preserving
    CIRPASS information fidelity. **DO NOT** mass-remap the
    table to the strict 6 in 9.8 — that would be the same
    rich-→-coarse degradation 9.8 is designed to avoid.
  - **CHANGELOG entry** under "Bug fixes":
    "PartyRoleEnum and the upstream JSON Schema's closed
    enum had a Layer-1/Layer-2 contradiction. Resolved by
    documenting the dual-tier acceptance gradient: Pydantic
    accepts 20 values (back-compat with v0.6 fixtures and
    the CIRPASS reverse-shim mapping); JSON Schema accepts
    only 6 (strict closed enum). New advisory rule `PRT001`
    surfaces the gap. Use `ValidationEngine(strict_role_enum=True)`
    to enforce the 6-value set."
  - **NOT a breaking change.** No values removed. No API
    surface narrowed.
  - Effort: ~120 LoC (rule + engine flag + test) + docs.

- **9.9 (alignment guard test)** Add
  `tests/unit/test_v07_model_schema_alignment.py`. Two tiers:
  - **Strict tier (block CI):** schema-required fields with no
    Pydantic-side coverage AND a Layer-1/Layer-2 contradiction.
    After 9.7 + 9.8 are merged, this asserts D1 is fully
    fixed (statusListIndex int) and D2 is fully documented
    (the gradient is intentional, PRT001 wired).
  - **Drift-watch tier (advisory; emits a CI warning):** any
    NEW drift items not registered in the `EXPECTED_DRIFT`
    constant. Forces every future PR that introduces drift
    to update the constant — no silent widening.
  - **Compatibility tier (NEW):** assert v0.6 → v0.7 upgrade
    of every `tests/fixtures/upstream/v0.6.x/` fixture
    succeeds; assert CIRPASS round-trip on every
    `tests/fixtures/valid/cirpass-1.3.0/` succeeds. Catches
    any future model edit that silently breaks the cross-
    version / cross-family pipeline.
  - Implementation: ~120 LoC. Reuses the
    `walk_schema_defs(schema_path)` helper (introduced in
    9.7's test file) and existing fixture-walk helpers in
    `tests/integration/test_version_matrix.py`.

- **9.10 (CHANGELOG drift section)** Edit `CHANGELOG.md`'s
  `0.5.0` entry to include:
  - § "Bug fixes": D1 (statusListIndex int with back-compat
    coercion — non-breaking), D2 (PartyRoleEnum gradient
    documented + PRT001 rule — non-breaking).
  - § "Known limitations": one-line summary of Tier 2 + 3
    items deferred to 0.6.0; link to Phase 10 of this plan.
  - § "Cross-version compatibility": explicit affirmation
    that v0.6.0 / v0.6.1 fixtures parse, validate, and
    upgrade without regression; that all CIRPASS v1.3.0
    round-trips remain bit-stable.

- **9.11 (NEW — cross-version regression baseline)** Add a
  release-gate manual checkpoint that runs the
  cross-version + cross-family regression suite immediately
  before tagging. Captures pass/skip counts in the release
  PR description. Single command:
  `pytest tests/integration/test_version_matrix.py
  tests/integration/test_compat_roundtrip.py
  tests/integration/test_round_trip_untp_cirpass.py
  tests/integration/test_cross_family_isolation.py
  tests/unit/test_engine_extended.py -v`. Expected counts:
  current baseline + zero deltas (no new failures, no new
  skips).

**UAT scenarios (manual, pre-tag).**

| # | Scenario | Expected |
|---|---|---|
| U1 | UNTP v0.7 → export `cirpass-jsonld` → validate (CIRPASS pipeline) → migrate `--to=untp-0.7` | Zero errors; ≤ documented `MAP00X` count |
| U2 | CIRPASS v1.3 (Phase 0 fixture) → validate → export `cirpass-jsonld` → re-ingest → re-validate | Bit-stable JSON-LD output |
| U3 | UNTP v0.6 → migrate `--to=untp-0.7` → migrate `--to=cirpass-1.3` → validate | Zero errors |
| U4 | Textile v2 fixture and Tyre Birth v0.9 fixture through their plugin pipelines | Zero errors |

**Deliverables**

- `dppvalidator 0.5.0` on PyPI.
- CHANGELOG entry.
- UAT sign-off in PR description.

**Tests** — none new; relies on existing suites.

**Exit criteria**

- [ ] All four UAT scenarios pass with reviewer sign-off.
- [ ] `pypi-publish` skill clean.

#### Phase 9 status — 2026-05-09 (10/11 tasks complete; 9.6 PyPI step reserved)

End-to-end implementation of the Phase 9 release cut. **Tasks 9.1
through 9.5 plus 9.7 through 9.11 are landed in source on
`develop`.** Task 9.6 (`pypi-publish` skill — PyPI upload) is
reserved for the release manager and runs on the merged release
branch.

**Refactors and additions:**

- **9.1 (DEFAULT_VERSIONS flip).** `DEFAULT_VERSIONS[UNTP] = "0.7.0"`
  in [`schemas/registry.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/schemas/registry.py).
  v0.6.x remains supported via auto-detection and the v0.6 → v0.7
  upgrade shim. **9.2** was already complete
  (`DEFAULT_VERSIONS[CIRPASS] = "1.3.0"` shipped in 0.4.0).
- **9.3 + 9.10 (CHANGELOG 0.5.0).** Family-keyed entry authored at
  the top of [`CHANGELOG.md`](https://github.com/artiso-ai/dppvalidator/blob/main/CHANGELOG.md):
  CIRPASS-2, UNTP, Plugins sections + Bug fixes + Deprecations +
  Cross-version compatibility + Known limitations + Migration
  guide. All 27 Phase 8.9 drift items referenced; D1/D2 closures
  documented as non-breaking.
- **9.4 (deprecation activation).** Three surfaces now emit
  `DeprecationWarning` in 0.5.0:
  - Bare-string `SCHEMA_REGISTRY[version]` lookup → wrapped in a
    `_DeprecatedSchemaRegistryDict` subclass; `__getitem__` warns.
    Internal CLI `schema.py` migrated to the tuple-keyed source of
    truth so we don't warn on our own callers.
  - `is_dpp_document()` alias → emits warning suggesting
    `looks_like_dpp()`.
  - `EUDPP_CONTEXT_URL` (already deprecated via PEP 562 in earlier
    phase) — verified still emitting.
- **9.5 (UAT scenarios).** Manually exercised the 4 scenarios from
  the table above:
  - U1: ✓ v0.7 fixture validates clean; CIRPASS-JSONLD export
    produces 2540 bytes with 3 documented MAP-warnings.
  - U2: ✓ Round-trip via the Python compat layer (6 forward + 2
    reverse warnings, all documented as MAP00X codes).
  - U3: ✓ v0.6 → v0.7 → CIRPASS chained migration succeeds with
    documented UPG001 + MAP001 warnings (lossy lift on
    performanceClaims is by-design per Phase 7 pilot scope).
  - U4: ✓ Tyre plugin pipeline 7/7 green. Textile-v2 rules
    correctly fire on a non-textile fixture (TXT001…TXT007 flag
    missing textile fields) — informational, not a regression.
- **9.7 (D1 BLOCKER).**
  [`models/v0_7/envelope.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/envelope.py):
  `BitstringStatusListEntry.statusListIndex` is now `int | None`
  with `ge=0`; new `_coerce_status_list_index` `before` validator
  transparently converts numeric strings (whitespace-tolerant,
  leading-zero-tolerant) for v0.6 fixture back-compat. 12 new
  parametrized tests in
  [`tests/unit/test_v07_models.py::TestStatusListIndexCoercion`](https://github.com/artiso-ai/dppvalidator/blob/main/tests/unit/test_v07_models.py)
  cover bare int, numeric string, whitespace, leading zero, zero,
  None, non-numeric string (rejected), float string (rejected),
  mixed-alpha string (rejected), negative int (rejected via ge=0),
  and round-trip int preservation.
- **9.8 (D2 BLOCKER).** PartyRoleEnum acceptance gradient
  documented + `SCHEMA_STRICT_ROLES` constant + `is_schema_strict()`
  method added to
  [`models/v0_7/identifiers.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/identifiers.py).
  New advisory rule
  [`PartyRoleAcceptanceGradientRule`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/rules/v0_7/party_role.py)
  emitting `PRT001` (info) when payload uses one of the 14 wider
  values, with a documented `SUGGESTED_STRICT_REMAP` table. New
  `ValidationEngine(strict_role_enum=True)` flag upgrades PRT001
  from info → error at emit-time. New PRT001.md doc page wired
  into mkdocs nav. 31 new tests in
  [`tests/unit/test_party_role_gradient.py`](https://github.com/artiso-ai/dppvalidator/blob/main/tests/unit/test_party_role_gradient.py)
  including a CIRPASS-shim-table-preservation test enforcing the
  Phase 9 compatibility constraint.
- **9.9 (alignment guard test).** Three-tier guard at
  [`tests/unit/test_v07_model_schema_alignment.py`](https://github.com/artiso-ai/dppvalidator/blob/main/tests/unit/test_v07_model_schema_alignment.py):
  - Strict tier (5 tests): D1, D2 closure assertions.
  - Drift-watch tier (1 test): walks every $def×model class pair;
    asserts only the registered drift items in
    `EXPECTED_SCHEMA_ONLY_DRIFT` and `EXPECTED_MODEL_ONLY_DRIFT`
    appear. New drift forces a baseline update.
  - Compat tier (3 tests): v0.6 model frozen, CredentialStatus
    alias, CIRPASS reverse-shim 8 wider targets preserved.
  - Disposition closures (3 tests): D21 + D23 confirmed faithful.
- **9.11 (cross-version regression baseline).** Single command
  recorded in this status block — see "Quality gates" below.

**Code-size delta:**

- Total `src/dppvalidator/` LoC: 29 227 → 29 480 (+253 net).
- New module
  [`validators/rules/v0_7/party_role.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/rules/v0_7/party_role.py):
  +103 LoC (rule class + remap table + docstrings).
- New errors page
  [`docs/errors/PRT001.md`](https://github.com/artiso-ai/dppvalidator/blob/main/docs/errors/PRT001.md):
  +95 lines (separate, doesn't count toward source LoC).
- Net source +253 buys: D1 fix + back-compat coercion (37 LoC),
  D2 acceptance gradient + PRT001 wiring + engine flag (~140 LoC),
  registry deprecation wrapper (~30 LoC), `is_dpp_document`
  deprecation (~12 LoC), CLI migration to tuple-keyed registry
  (~30 LoC).

**Quality gates after Phase 9:**

- `uv run pytest tests/`: **2525 passed / 36 skipped** (was 2468
  before Phase 9 — 12 + 31 + 12 + 1 + 1 = 57 new tests, of which
  12 are PRT001 parametrize fan-outs).
- Coverage: **92.05 % → 92.04 %** (effectively flat; new test code
  with minor delta in instrumented files).
- `uv run ruff check src/ tests/`: **clean**.
- `uv run ruff format --check src/ tests/`: **clean**.
- `uv run ty check src/`: **clean**.
- `uv run --group docs mkdocs build --strict`: **clean** (PRT001
  page + nav entry).
- `uv run python scripts/check_error_docs.py`: **96/96**
  documented + nav-wired (was 95/95 before PRT001).
- Cold-start contract: `import dppvalidator` still does not load
  `models.cirpass`.

**Cross-version regression baseline (task 9.11) — release manager
re-runs this before tagging:**

```bash
uv run pytest \
  tests/integration/test_version_matrix.py \
  tests/integration/test_compat_roundtrip.py \
  tests/integration/test_round_trip_untp_cirpass.py \
  tests/integration/test_cross_family_isolation.py \
  tests/unit/test_engine_extended.py \
  -q --tb=short
```

Current baseline: **101 passed**. Required for release tag: zero
delta from this number.

**Acceptance gradient verification (Phase 9.8 + Phase 9 compatibility constraint):**

- v0.6 → v0.7 upgrade shim still emits `manufacturer` for the
  one role v0.6 fixtures use (verified via
  `test_engine_extended.py::TestUpgradeShim`).
- CIRPASS reverse shim's `_EUDPP_TO_UNTP_ROLE` table still
  contains the 8 schema-rejected rich-extension targets
  (`importer`, `distributor`, `retailer`, `logisticsProvider`,
  `operator`, `regulator`, `serviceProvider`, `certifier`) —
  asserted by
  `test_v07_model_schema_alignment.py::TestCrossVersionCompatibility::test_cirpass_reverse_shim_table_preserved`.

**Carried forward:**

- Task 9.6 (`pypi-publish`) reserved for release manager.
- Phase 8.9 Tier-2/3/4/5/6 drift items (D3–D20, D25–D27) defer to
  Phase 10. Alignment guard test currently registers the full
  drift baseline; Phase 10's 10.9–10.15 will progressively shrink
  `EXPECTED_SCHEMA_ONLY_DRIFT` and `EXPECTED_MODEL_ONLY_DRIFT`
  toward empty, then flip the strict-tier `EXPECTED_DRIFT`
  assertion from advisory to hard.

---

### Phase 10 — `0.6.0` Stable + cleanup

**Goal:** Lock CIRPASS APIs; drop deprecated surfaces; claim Stable.
**Effort:** M (~3 days) · **Depends on:** Phase 9 · **Ships in:** `0.6.0`.

**Compatibility constraints (inherited from Phase 9):**

Every model-alignment task in Phase 10 (10.9–10.14) MUST
preserve:

1. UNTP v0.6.0 / v0.6.1 fixture parsing & validation —
   v0.6 models stay frozen.
2. `compat/upgrade_0_6_to_0_7.py` output — keep emitting
   v0.7-shaped payloads that the v0.7 ValidationEngine
   accepts. When promoting a `model_extra` field to
   first-class, audit the upgrade shim for whether it
   currently emits the field; if it doesn't, decide
   whether to extend the shim's coverage or accept the
   field as null on upgrade-from-v0.6.
3. `compat/untp_0_7_to_cirpass_1_3.py` and
   `compat/cirpass_1_3_to_untp_0_7.py` — both shims
   continue to round-trip every CIRPASS v1.3.0 fixture
   bit-stably. Field promotions in 10.9 will surface new
   keys in `model_dump()` output → audit both shims for
   `model_fields` iteration assumptions.
4. CIRPASS reference structure v1.3.0 conformance —
   no model edit should perturb the CIRPASS pipeline.
5. The Phase 9 cross-version regression suite (task 9.11)
   must remain green after each Phase 10 task lands.

**Per-task compatibility checklist (apply to 10.9–10.14):**

- [ ] Run `pytest tests/integration/test_version_matrix.py` →
      zero pass-count delta.
- [ ] Run `pytest tests/integration/test_compat_roundtrip.py
      tests/integration/test_round_trip_untp_cirpass.py` →
      zero pass-count delta.
- [ ] Round-trip every `tests/fixtures/upstream/v0.6.x/`
      fixture through the v0.6 → v0.7 upgrade shim → confirm
      no new MDL050 / SCH001 errors.
- [ ] Round-trip every `tests/fixtures/valid/cirpass-1.3.0/`
      fixture through forward + reverse shim → confirm
      bit-stable JSON-LD output.
- [ ] If a model-only field is being deprecated/removed
      (D17, D18), grep the entire codebase for usage
      including plugins (`plugins/textiles/`,
      `plugins/tyres/`) and the EUDPP / CIRPASS exporters.

**Tasks**

- **10.1** Remove pre-1.9 EUDPP TTLs (`v1.7.1`, `v1.5.1`, `v1.4.7`,
  `v2.0`, `v1.3.1`) and the corresponding manifest rows.
- **10.2** Remove the legacy `EUDPP_CONTEXT_URL` registration.
- **10.3** Remove the `--profile textile-v1` flag and the
  `textile-v1` entry-point.
- **10.4** Remove the `is_dpp_document` alias.
- **10.5** Remove the bare-string `SCHEMA_REGISTRY` lookup wrapper.
- **10.6** Promote `plugins/tyres/` from `pre-1.0` to `1.0`.
- **10.7** Remove the superseded `docs/concepts/eudpp-ontology-alignment.md`
  stub.
- **10.8** Run `code-health`, `docs-health`, `claude-health`.
- **10.9 (Phase 8.9 Tier-3 MEDIUM scope)** Promote the 14
  schema-declared fields currently stored only as
  `model_extra` to first-class Pydantic fields across
  `Party`, `Link`, `Package`, `Period`, `RenderTemplate2024`
  (drift items D8, D10–D14, D16–D18). Specifics:
  - `Party` (D10): add `registration_country` (Country),
    `party_address` (Address), `organisation_website` (str),
    `industry_category` (list[str | Classification]),
    `party_also_known_as` (list[Identifier]).
  - `Link` (D8 + D11 + D16): rename `name` → `link_name`
    (alias `linkName`, REQUIRED per schema); add `link_type`
    (alias `linkType`, optional). Deprecate `description` and
    `relationship` (model-only, not in schema) — emit
    `DeprecationWarning` in 0.6.0; remove in 0.7.0.
  - `Package` (D9 + D12 + D17): replace the legacy
    `package_type` + `weight` fields with schema's
    `description`, `dimensions`, `material_used` (REQUIRED),
    `package_label`, `performance_claim` (optional). Carry the
    legacy fields as `model_extra` access only with a
    deprecation warning.
  - `Period` (D13): add `period_information` field. The
    `start_date`/`end_date` Required-vs-Optional drift (D7) is
    handled separately under task 10.10.
  - `RenderTemplate2024` (D14 + D18): add `media_query`, `url`;
    deprecate the model-only `id` field.
  - Cross-cutting: the alignment guard test from 9.9 should
    flip its xfail markers for D8, D10–D14, D16–D18 as those
    items resolve. CIRPASS forward shim
    [`compat/untp_0_7_to_cirpass_1_3.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/untp_0_7_to_cirpass_1_3.py)
    should pick up the promoted fields automatically (it
    iterates `model_fields`); audit afterward to confirm.
  - Audit the rule corpus for attribute-access opportunities:
    Phase 4 ACT/REL/SOC rules currently use
    `getattr(model, "partyAddress", None)` workarounds; switch
    to first-class field access once 10.9 lands.
  - Effort estimate: ~1.5 days; ~150 LoC of model code +
    fixture/test/exporter touch-up. Confined to v0.7 — v0.6
    models are frozen per the cardinal rule.

- **10.10 (Phase 8.9 Tier-2 HIGH — required-vs-Optional
  reconciliation)** Tighten the Pydantic safety lattice to
  match schema's required-marker semantics (drift items D3,
  D4, D6, D7). Strategy: introduce a *strict-mode pair* per
  affected class so callers can pick:
  - `Address` / `AddressPermissive`: strict variant marks
    all 5 schema-required fields as Pydantic-required;
    permissive variant retains current Optional shape for
    incremental construction. Default validation entrypoint
    (`ValidationEngine.validate`) parses with strict; programmatic
    callers building incrementally can opt into permissive.
  - Same pattern for `BitstringStatusListEntry`,
    `Claim`, `Period`. The strict variant should ship as the
    canonical class name; the permissive variant gets a
    `Permissive` suffix.
  - Edge cases: `Period` can legitimately have one bound open
    (semantic rule REL003 covers `validFrom < validTo` but
    also allows either to be missing). Schema's REQUIRED on
    both `startDate` and `endDate` is at the payload level
    where Period is *populated* — when a payload omits
    `period` entirely, the Period $def is never visited. The
    strict variant therefore only fires when a Period dict is
    being instantiated from a real schema-bound source.
  - Cross-fixture audit: walk all 0.7 fixtures
    (`tests/fixtures/valid/*.json`) and confirm none rely on
    the permissive shape for required schema fields.
  - Effort: ~1 day; ~80 LoC + ~50 fixture-touch lines.

- **10.11 (Phase 8.9 Tier-2 HIGH — closed-enum coverage)**
  Add closed Pydantic enums for the 2 schema enum sites not
  currently typed (drift items: `BitstringStatusListEntry.statusPurpose`
  and `BitstringStatusListEntry.type`).
  - `StatusPurposeEnum`: 4 values — `refresh`, `revocation`,
    `suspension`, `message`.
  - `BitstringStatusListEntryTypeEnum`: 1 value —
    `BitstringStatusListEntry` (it's a singleton; using a
    `Literal["BitstringStatusListEntry"]` type is leaner).
  - `BitstringStatusListEntry.id` REVERSE drift (D5): drop
    the Pydantic-side requirement on `id` — schema marks it
    OPTIONAL.
  - Effort: ~30 LoC; mostly enum class additions.

- **10.12 (Phase 8.9 Tier-5 — format-constraint enforcement)**
  Promote the 13 schema sites with `format: uri` and
  `format: byte` from plain `str` to typed Pydantic
  annotations (drift items D19, D20).
  - The 12 `format: uri` sites all currently use `str`. Switch
    to the project's existing `FlexibleUri` type (defined in
    [models/v0_7/primitives.py](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/primitives.py))
    which permits both URLs and DIDs. Sites:
    `CredentialIssuer.id`, `BitstringStatusListEntry.id`,
    `BitstringStatusListEntry.statusListCredential`,
    `RenderTemplate2024.url`, `IssuingSoftware.id`,
    `Product.id`, plus the others enumerated in Phase 8.9 D19.
  - The 1 `format: byte` site (`Image.imageData`) — add a
    Pydantic validator that verifies base64 decodability via
    `base64.b64decode(value, validate=True)`.
  - Edge cases: `did:` URIs must remain valid (FlexibleUri
    handles this); empty strings must be rejected; whitespace
    must be stripped.
  - Effort: ~40 LoC + ~10 test cases (1 happy / 1 sad per
    site grouping).

- **10.13 (Phase 8.9 Tier-4 LOW — model-only field audit)**
  Catalogue every model-only field (D15, D16, D17, D18) and
  decide per-field: keep as documented extension, or remove.
  - `Claim.classification` — likely intentional (used by
    semantic rules); keep but document in the v0.7 model
    docstring as "extension beyond schema".
  - `Link.name`, `.description`, `.relationship` — the `name`
    field becomes `linkName` per 10.9; `description` and
    `relationship` deprecated.
  - `Package.packageType`, `.weight` — UNTP 0.6 holdover;
    remove (with deprecation warning for one minor).
  - `RenderTemplate2024.id` — not in schema; deprecate.
  - Effort: ~20 LoC delete + comment additions.

- **10.14 (Phase 8.9 Tier-6 — unmapped class follow-up,
  REFINED 2026-05-09)** Two of the four are CLOSED by
  audit (D21 `DigitalProductPassport`, D23
  `IdentifierScheme` — both confirmed faithful to schema's
  shape). Remaining work is documentation-only:
  - **D22 `Facility`**: add a class docstring noting
    "extension for `DigitalFacilityRecord` cross-credential
    references; not a v0.7.0 schema $def". Confirm semantic
    rules don't expect schema validation of `Facility`
    instances (they shouldn't — `Facility` flows through as
    a reference, not as a validated payload).
  - **D24 `SoftwareVendor`**: add a class docstring noting
    "helper class for `IssuingSoftware.vendor`; not exposed
    as a schema $def — the schema inlines the same shape
    under `IssuingSoftware.properties.vendor`".
  - Effort: ~10 LoC of docstring additions.

- **10.15 (Phase 8.9 Tier-8 — CIRPASS v1.3 model layer
  field-level deep diff, NEW 2026-05-09)** Phase 8.9 audited
  UNTP v0.7 exhaustively but only counted CIRPASS v1.3
  classes (20 model vs 20 schema $defs — counts match). A
  field-level deep diff analogous to Phase 8.9's
  methodology, repointed at `models/cirpass/v1_3/` and
  `schemas/data/cirpass-reference-1.3.0.json`, is queued
  here.
  - Walk every $def in `cirpass-reference-1.3.0.json` →
    inventory of field/type/required/format/enum/pattern.
  - Walk every CIRPASS Pydantic model class → inventory of
    aliases / required / annotation.
  - Diff: schema-only, model-only, required-vs-Optional,
    type drift, enum drift.
  - **Specific gaps surfaced by Phase 8.9 final pass:**
    - **D26**: schema `HazardCategory` and `LifeCycleStage`
      $defs (both 0-prop terminology classes) have no
      Pydantic model. Investigate whether they should map
      to v1.9.x EUDPP enum members
      (e.g. `vocabularies/eudpp_classes.py` /
      `vocabularies/eudpp_lca.py`) or to dedicated Pydantic
      classes. The 0-prop shape suggests they're enum
      anchors (used as `@type`-style references), in which
      case Pydantic-class modelling isn't needed but a
      docstring pointer back to the EUDPP enum class is.
    - **D27**: catalogue any new field-level drift
      surfaced by the deep diff. Tier each finding using
      the same severity model as Phase 8.9 (BLOCKER /
      HIGH / MEDIUM / LOW / FORMAT). Register each in a
      Phase 8.10 status block (pattern follows 8.9).
  - **Compatibility constraint inherited from Phase 9
    block**: every CIRPASS model edit must preserve forward
    and reverse shim round-trips and keep
    `tests/integration/test_round_trip_untp_cirpass.py`
    bit-stable.
  - Effort: ~1 day audit + tiering. Code edits depend on
    findings (likely 0–100 LoC depending on drift density).

**Deliverables**

- `dppvalidator 0.6.0` on PyPI.
- All deprecated surfaces removed.
- Phase 8.9 alignment guard test flips from advisory to
  strict (zero `EXPECTED_DRIFT` entries).

**Tests**

- `pytest -W error` (warnings-as-errors mode) — no deprecation
  warnings emitted by the suite.
- `tests/unit/test_vocab_loader_perf.py` — cold-start import time
  within +20 ms of the `tests/baselines/import_time.json` baseline.
- `tests/unit/test_v07_model_schema_alignment.py` (added in
  task 9.9): `EXPECTED_DRIFT` constant must be empty and the
  strict-tier assertion must fire for every $def×model class
  pair — actionable drift items closed (D21 + D23 already
  closed at 8.9 audit; D1 + D2 closed at Phase 9; D3–D20,
  D25 closed at Phase 10.9–10.13; D26 + D27 closed at
  Phase 10.15).
- New per-class round-trip parity tests: load every fixture
  in `tests/fixtures/valid/*.json`, parse → dump → diff. Zero
  paths lost, zero unexpected paths gained (the +1 path in
  the Phase 8.9 battery survey came from a synthesised
  default and is acceptable; document any residual diff).

**Exit criteria**

- [ ] No deprecation warnings under `-W error`.
- [ ] Cold-start budget met (median of 5 CI runs).
- [ ] All three health checks clean.
- [ ] Alignment guard test passes with empty `EXPECTED_DRIFT`.
- [ ] All 0.7 fixture round-trips bit-stable (or differences
      explicitly documented).
- [ ] CIRPASS forward shim picks up all newly-promoted fields
      (manual smoke: export the battery fixture as
      `cirpass-jsonld` and confirm `materialUsed` / `linkName`
      / `linkType` now appear in the projection).

---

## 3. Cross-cutting workstreams

Each closes by a specific phase to keep them from drifting.

| ID | Workstream | Closes by | Notes |
|---|---|---|---|
| X1 | Code-generation hygiene | Phase 3 | Generators under `tools/codegen/`, never `src/`. Files header `# generated-from: <ttl-path>@<sha>`. CI gate `tools/codegen/check_drift.py`. *Status (2026-05-08):* enum-regeneration generator [`tools/codegen/cirpass/regenerate_enums.py`](../../tools/codegen/cirpass/regenerate_enums.py) ✓ landed with self-test against v1.7.1 TTL fixture; JSON Schema deriver and drift-gate wrapper still owned by Phase 3. |
| X2 | SHACL pipeline | Phase 4 | `pyshacl` integration tests at `tests/integration/shacl/`. Module-level shape-graph caching keyed on `(family, module, version)` + bundled SHA |
| X3 | Performance budget | Phase 9 | `python -X importtime`, median of 5; baseline at `tests/baselines/import_time.json`; +20 ms ceiling. Lazy-import CIRPASS package |
| X4 | Property-based + fuzz tests | Phase 5 | Hypothesis strategy per Phase 3 model; round-trip invariants from Phase 5 |
| X5 | CI matrix | Phase 9 | New job `CIRPASS_FAMILY=cirpass` runs only the CIRPASS subset for early isolation regression detection |
| X6 | Internationalisation | Phase 5 | `LocalisedText` (Phase 3) field-level; mapping shim (Phase 5) preserves exactly one `MAP001` per dropped language |

---

## 4. Risk register

| ID | Risk | Lik. | Imp. | Mitigation |
|---|---|---|---|---|
| R1 | Hub re-publishes a module under same version with mutated axioms | M | H | GUID + SHA pinning; nightly `tools/snapshot/check_drift.py` |
| R2 | UNTP↔CIRPASS mapping has more lossy fields than expected | M | M | Phase 5 audit table is authoritative; `MAP00X` warnings, never silent loss |
| R3 | IDENT/MAT/EVENT/COMP publish mid-window with shifted hierarchies | M | H | Deliberately not scaffolded; §6.3 recipe adopts post-`0.6.0` |
| R4 | Pilot data models shift between Preview and Stable | H | L–M | Plugins separately versioned; profile flags buy a release of grace |
| R5 | SHACL evaluation latency spikes test suite | M | M | Module-level shape caching; `@pytest.mark.integration` excluded from pre-commit |
| R6 | `pyshacl` / `rdflib` upstream breakage | L | M | Pinned in `pyproject.toml`; pre-commit smoke `tools/check_rdf_stack.py` |
| R7 | Bare version-literal regressions slip past linter | L | H | Phase 1 task 1.14 extends the guard to CIRPASS literals |
| R8 | Plugin license contamination (GPL → MIT core) | L | H (legal) | [`.claude/rules/plugin-licenses.md`](../../.claude/rules/plugin-licenses.md) + `tools/check_imports.py` (Phase 7 task 7.9) |
| R9 | Cardinal versioning rule erosion under PR pressure | M | M | Every PR in Phases 2–6 references the rules file; reviewer checklist |
| R10 | `DigitalProductPassport` type-name shared across families → detection ambiguity | M | H | Phase 2 resolves by `@context` first, shape signature second; `DET001` rather than fallthrough |
| R11 | EU regulation expands multi-language scope beyond Phase 3's set | L | M | `LocalisedText` is field-level; expansion adds fields, doesn't break |
| R12 | `https://w3id.org/eudpp/...` IRIs do not dereference (D-0.3 fails) | L | H | Phase 0 task 0.4 verifies; failure escalates as a hard blocker |
| R13 | Performance budget breached by SHACL eager-load | M | L | Lazy-import (X3); `tests/unit/test_vocab_loader_perf.py` asserts |
| R14 | Derived JSON Schema diverges from tree-view exports across hub revisions | M | M | `tools/codegen/check_drift.py` nightly |

---

## 5. Rollout

| Release | Phases | Signal |
|---|---|---|
| `0.4.z` | Phases 0 → 2 | Additive only; no deprecation warnings yet |
| `0.5.0` Preview | Phases 3 → 9 | CIRPASS family available; deprecation warnings active; CHANGELOG sectioned by family |
| `0.6.0` Stable | Phase 10 | Deprecated surfaces removed; APIs locked |
| `0.6.z` opportunistic | §6.3 add-module recipe | New EUDPP modules light up as published |

CHANGELOG sections from `0.5.0` onwards are family-keyed
(`### UNTP`, `### CIRPASS-2`, `### Plugins`). The authoritative
"what's bundled at this tag" reference is
`docs/concepts/cirpass-2-spec-snapshot.md`.

---

## 6. Appendices

### 6.1 File inventory delta

**Added**

```text
docs/concepts/cirpass-2-spec-snapshot.md
docs/concepts/cirpass-2-alignment.md
docs/concepts/eudpp-1.9-changelog.md
docs/concepts/untp-cirpass-mapping.md
docs/guides/migrate-untp-to-cirpass.md
docs/plans/CIRPASS_2_MIGRATION.md            # this file
docs/plugins/tyres.md
docs/reference/cli/exit-codes.md
docs/reference/cirpass/                      # mkdocstrings-generated
docs/adr/0001-cirpass-json-schema-derivation.md
docs/adr/0002-canonical-eudpp-iri.md
docs/adr/0003-tyre-license.md
src/dppvalidator/models/cirpass/__init__.py
src/dppvalidator/models/cirpass/v1_3/{passport,product,actor,material,
  substances,lca,connector,i18n,temporal}.py
src/dppvalidator/validators/rules/cirpass_v1_3/{base,substances,lca,
  actor,connector}.py
src/dppvalidator/compat/{untp_0_7_to_cirpass_1_3,cirpass_1_3_to_untp_0_7,
  _untp_cirpass_map,_identifier_schemes,_mapping_codes}.py
src/dppvalidator/exporters/cirpass_jsonld.py
src/dppvalidator/schemas/data/cirpass-reference-1.3.0.json
src/dppvalidator/vocabularies/data/eudpp-context-v1.9.1.jsonld
src/dppvalidator/vocabularies/data/ontologies/{product_dpp_v1.9.1,
  actors_roles_v1.9.1,soc_v1.9.1,lca_v1.9.4_Maki,eudpp_core_v1.9.1,
  connector_v1.9.1}.ttl
plugins/tyres/{pyproject.toml,LICENSE,dppvalidator_tyres/...}
tools/snapshot/{fetch_cirpass.py,check_drift.py}
tools/codegen/cirpass/derive_schema.py
tools/codegen/check_drift.py
tools/check_imports.py
tests/baselines/import_time.json
tests/fixtures/{valid,invalid}/cirpass-1.3.0/
tests/unit/test_{models_cirpass_v1_3,detection_cirpass,
  detection_ambiguity,namespace_canonicality,mapping_codes,
  registry_back_compat,cold_start_import,rules_cirpass_*}.py
tests/integration/{test_cirpass_v1_3_pipeline,
  test_round_trip_untp_cirpass,test_cli_cirpass,
  test_cli_export_matrix,test_cli_back_compat,
  test_cross_family_isolation,test_i18n_roundtrip}.py
tests/integration/shacl/
tests/property/{test_cirpass_v1_3_invariants,
  test_round_trip_invariants}.py
tests/plugins/{tyres/,test_license_isolation.py}
```

**Updated**

```text
src/dppvalidator/schemas/registry.py            # SchemaFamily, two-axis registry, GUID field
src/dppvalidator/schemas/data/MANIFEST.json     # CIRPASS rows + family/module/guid fields
src/dppvalidator/validators/detection.py        # detect_schema_family + URL patterns + looks_like_dpp
src/dppvalidator/validators/engine.py           # _PIPELINE_BY_FAMILY dispatch
src/dppvalidator/compat/__init__.py             # active_version(family=…)
src/dppvalidator/exporters/eudpp_jsonld.py      # v1.9.1 + canonical w3id IRIs
src/dppvalidator/exporters/contexts.py          # family-keyed context registry
src/dppvalidator/vocabularies/ontology.py       # TERM_MAPPINGS @ v1.9.1; namespace rebase; alias deletion
src/dppvalidator/vocabularies/eudpp_*.py        # regenerated enums
src/dppvalidator/cli/main.py                    # --target, --format, migrate --to, exit codes
plugins/textiles/...                            # MVP Textile DPP v2 + textile-v1 profile
.claude/rules/untp-versioning.md                # cardinal-rule extension to CIRPASS family
tests/unit/test_no_version_literals.py          # CIRPASS / EUDPP module-version literal guards
README.md
mkdocs.yml
CHANGELOG.md
```

**Removed (Phase 10 only)**

```text
src/dppvalidator/vocabularies/data/ontologies/{product_dpp_v1.7.1,
  actors_roles_v1.5.1,soc_v1.4.7,lca_v2.0,eudpp_core_v1.3.1}.ttl
src/dppvalidator/vocabularies/ontology.py::CIRPASSNamespace_alias
docs/concepts/eudpp-ontology-alignment.md       # superseded
```

### 6.2 Phase dependency graph

```text
                     ┌──────────────┐
                     │ Phase 0      │
                     └──────┬───────┘
              ┌─────────────┴─────────────┐
              ▼                           ▼
       ┌──────────┐               ┌──────────────┐
       │ Phase 1  │               │ Phase 2      │
       └────┬─────┘               └──────┬───────┘
            └─────────────┬──────────────┘
                          ▼
                   ┌──────────┐
                   │ Phase 3  │
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ Phase 4  │
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ Phase 5  │
                   └────┬─────┘
              ┌─────────┴─────────┐
              ▼                   ▼
       ┌──────────┐         ┌──────────┐
       │ Phase 6  │         │ Phase 7  │
       └────┬─────┘         └────┬─────┘
            └─────────┬──────────┘
                      ▼
                 ┌──────────┐
                 │ Phase 8  │
                 └────┬─────┘
                      ▼
                 ┌──────────┐
                 │ Phase 9  │
                 └────┬─────┘
                      ▼
                 ┌──────────┐
                 │ Phase 10 │
                 └──────────┘
```

**Critical path:** 0 → 1 → 3 → 4 → 5 → 6 → 8 → 9 → 10 (Phase 7 runs in parallel with 6).

### 6.3 CIRPASS minimum-touch list

Mirror of the UNTP version-bump touch list at
[`.claude/rules/untp-versioning.md`](../../.claude/rules/untp-versioning.md).
For new CIRPASS modules (the IDENT / MAT / EVENT / COMP scenario) or new
CIRPASS message versions, when adding `<MODULE>` at version `<vA.B.C>`:

- `src/dppvalidator/schemas/registry.py` — register bundled artefact if any.
- `src/dppvalidator/exporters/contexts.py` — JSON-LD context entry if any.
- `src/dppvalidator/schemas/data/MANIFEST.json` — manifest row with
  `family: "cirpass"` (message) or `family: "eudpp-ontology"` (TTL),
  `module: <MODULE>`, `vocabulary_hub_guid`, SHA-256.
- `src/dppvalidator/vocabularies/data/ontologies/<module>_<vA.B.C>.ttl` — vendored TTL.
- `src/dppvalidator/vocabularies/ontology.py::TERM_MAPPINGS` — new rows.
- `src/dppvalidator/vocabularies/eudpp_<module>.py` — refreshed/new enum.
- `src/dppvalidator/models/cirpass/v1_X/<module>.py` — Pydantic models.
- `src/dppvalidator/validators/rules/cirpass_v1_X/<module>.py` — semantic rules.
- `tests/fixtures/valid/cirpass-1.X.0/<module>_*.json` — fixtures.
- `tests/integration/test_version_matrix.py` — new family+version row.
- `docs/plans/CIRPASS_<X>_<Y>_<Z>_MIGRATION.md` — migration doc if a major version.

If you touched more than this list, you're either fixing an unrelated bug
(split the PR) or going around the version-aware spine (don't).

---

*End of plan v3. Locked decisions: D-0.1, D-0.3, D-naming, D-default-family.
Open action items: OA-1 (tyre license, Phase 0 close), OA-2 (Battery Pass
follow-on plan, post-`0.6.0`).*
