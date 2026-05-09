# EUDPP v1.9.1 / v1.9.4-Maki — consumer changelog

**Status:** Final (Phase 8 finalisation, 2026-05-09). Phase 1 task 1.6
completed the row-by-row audit; this page documents what shipped.

> Looking for the *big picture*? Start at
> [`cirpass-2-alignment.md`](cirpass-2-alignment.md). Looking for
> *how to migrate a UNTP fixture*? See
> [`migrate-untp-to-cirpass.md`](../guides/migrate-untp-to-cirpass.md).

## Audience

Anyone consuming dppvalidator's EU DPP-aligned JSON-LD output, the
`EUDPPNamespace` enum, or the per-module enums under
[`src/dppvalidator/vocabularies/`](https://github.com/artiso-ai/dppvalidator/tree/main/src/dppvalidator/vocabularies).
Read this if your downstream code:

- pinned `http://dpp.taltech.ee/EUDPP#` or `http://dpp.cea.fr/EUDPP/LCA#`
  IRIs as predicate identifiers;
- referenced `EUDPPClass.X` / `EUDPPRoleClass.X` / `HazardCategory.X` /
  `ImpactCategory.X` / `EUDPPObjectProperty.X` constants by name;
- consumed the term-mapping table at
  [`vocabularies/ontology.py::TERM_MAPPINGS`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/vocabularies/ontology.py).

## What changed in Phase 1

### Namespace migration (ADR 0002)

EUDPP IRIs rebased from per-publisher hosts onto the canonical W3ID
prefix. Six bindings affected:

| Before                                | After                           | Note                                      |
| ------------------------------------- | ------------------------------- | ----------------------------------------- |
| `http://dpp.taltech.ee/EUDPP#`        | `https://w3id.org/eudpp/`       | umbrella CORE prefix                      |
| `http://dpp.cea.fr/EUDPP/LCA#`        | `https://w3id.org/eudpp/lca/`   | LCA module                                |
| *(new — was conflated under EUDPP)*   | `https://w3id.org/eudpp/p_dpp/` | Product / DPP module                      |
| *(new)*                               | `https://w3id.org/eudpp/soc/`   | Substances of Concern module              |
| *(new)*                               | `https://w3id.org/eudpp/actor/` | Actors and Roles module                   |
| *(new — module didn't exist pre-1.9)* | `https://w3id.org/eudpp/con/`   | Connector module (cross-module relations) |

**Migration path for downstream consumers:**

- *Reading our JSON-LD output:* update your context resolver to follow
  W3ID redirects. The hub-published context document URL
  (`https://dpp.vocabulary-hub.eu/context/v1`) is unchanged; only the
  predicate IRIs inside it are rebased. Most JSON-LD processors handle
  the redirect transparently.
- *Pinning predicate IRIs in your code:* replace any literal
  `dpp.taltech.ee/EUDPP#` or `dpp.cea.fr/EUDPP/LCA#` substring with
  `w3id.org/eudpp/` (umbrella) or the module-specific sub-prefix.
- *Importing `EUDPPNamespace` from us:* `EUDPPNamespace.EUDPP.value` and
  `EUDPPNamespace.LCA.value` return new strings. Code that compared
  these to the old hosts must be updated. Six new members are added:
  `P_DPP`, `SOC`, `ACTOR`, `CON`, plus the umbrella `EUDPP` (rebased)
  and `LCA` (rebased).
- *Using the deleted aliases:* `CIRPASSNamespace`,
  `compact_cirpass_uri`, `expand_cirpass_uri`, `get_cirpass_context`
  are removed. Use the `_eudpp_` -named functions / classes (existing
  surface) or the new per-module `EUDPPNamespace` members.

### TermMapping schema extension

`TermMapping` gains an optional `cirpass_v1_3: str | None = None`
column alongside the existing `untp_v0_6` / `untp_v0_7`. Defaults
preserve the canonical `untp_term` spelling, so unchanged rows do not
need to repeat themselves. The `OntologyMapper` API gains an optional
keyword-only `family: str = "untp"` parameter on
`find_mapping_for_term`, `_index_for_version`, `mapped_terms_for`, and
`TermMapping.term_for`. Existing call sites are unaffected.

### MANIFEST schema extension

[`src/dppvalidator/schemas/data/MANIFEST.json`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/schemas/data/MANIFEST.json)
gains four optional per-row fields: `family`, `module`,
`vocabulary_hub_guid`, `superseded_by`. Existing rows carry
`family: "untp"` for forward consistency; the required-field set
(`version`, `kind`, `path`, `source_url`, `sha256`, `pulled_at`) is
unchanged, so the integrity test in
[`tests/unit/test_manifest_integrity.py`](https://github.com/artiso-ai/dppvalidator/blob/main/tests/unit/test_manifest_integrity.py)
remains green.

## Per-class diff (populated by Phase 1 tasks 1.6–1.11 audit)

The 6 v1.9.x EUDPP TTLs landed in 2026-05-08; the codegen tool at
[`tools/codegen/cirpass/regenerate_enums.py`](https://github.com/artiso-ai/dppvalidator/blob/main/tools/codegen/cirpass/regenerate_enums.py)
regenerated each enum block. Manual review surfaced these
spec-driven changes:

### Renames (single class moved + IRI changed)

| Module | v1.7.1 IRI                              | v1.9.1 IRI                        | Notes                                                                 |
| ------ | --------------------------------------- | --------------------------------- | --------------------------------------------------------------------- |
| P_DPP  | `eudpp:Document`                        | `eudpp:DocumentFormattedProperty` | P_DPP changelog: "#Document renamed to #DocumentFormattedProperty"    |
| P_DPP  | `eudpp:uniqueProductID` (datatype prop) | `eudpp:uniqueProductIdentifier`   | P_DPP changelog: "Renamed uniqueProductID to uniqueProductIdentifier" |

### Module migrations (IRI unchanged; defining module changed)

The 5 properties below moved from P_DPP v1.7.1 to CON v1.9.1. The IRIs
are unchanged — `EUDPPObjectProperty` keeps them. Downstream consumers
that resolve to the *defining* module (e.g. for SHACL shape-graph
loading) must now query `connector_v1.9.1.ttl`, not
`product_dpp_v1.9.1.ttl`.

| IRI                                | v1.7.1 module | v1.9.1 module |
| ---------------------------------- | ------------- | ------------- |
| `eudpp:containsSubstanceOfConcern` | P_DPP         | CON           |
| `eudpp:hasEconomicOperator`        | P_DPP         | CON           |
| `eudpp:hasBackUpCopyHost`          | P_DPP         | CON           |
| `eudpp:hasIssuer`                  | P_DPP         | CON           |
| `eudpp:hasManufacturer`            | P_DPP         | CON           |

### Removals (no v1.9.1 equivalent)

| IRI                                | Where used pre-1.9                                  | Phase 1 disposition                                                                                                                                       |
| ---------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `eudpp:facilityID` (datatype prop) | `TermMapping.cirpass_uri` for `producedAtFacility`  | Retargeted to `eudpp:Facility` class (in ACTOR module). Predicate removed per P_DPP changelog: "Removed #facilityID. Now described through ACTOR module." |
| `eudpp:hasMaterialProvenance`      | `TermMapping.cirpass_uri` for `materialsProvenance` | Annotated via `TRANSITIONAL_EUDPP_REMOVED_IN_V1_9`; row kept for v0.6↔v0.7 UNTP rename round-trip; resolution test skips it                               |
| `eudpp:hasPerformanceClaim`        | `TermMapping.cirpass_uri` for `conformityClaim`     | Same treatment as above                                                                                                                                   |
| `eudpp:isResponsibleForProduct`    | `EUDPPObjectProperty.IS_RESPONSIBLE_FOR_PRODUCT`    | Annotated `# −1.9.1`; not in v1.9.1 TTL but kept in enum for back-compat                                                                                  |
| `eudpp:isRepresentedBy`            | `EUDPPObjectProperty.IS_REPRESENTED_BY`             | Same treatment                                                                                                                                            |

### Additions (new classes / properties in v1.9.1)

| Module          | Element                                                                                                                 | Notes                                                                                                                                                                                                                                                                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ACTOR           | `eudpp:ActorRoleAssignment` (class)                                                                                     | Models "actor X plays role Y in context Z" as a first-class entity                                                                                                                                                                                                                                                                                  |
| ACTOR           | `eudpp:AuthorisedRepresentationAssignment` (class)                                                                      | Authorised-representative relationship as a first-class entity                                                                                                                                                                                                                                                                                      |
| ACTOR           | `eudpp:CircularEconomyRole` (class)                                                                                     | Super-category for Recycler / Refurbisher / Remanufacturer (which v1.9.1 collapses)                                                                                                                                                                                                                                                                 |
| ACTOR           | `eudpp:ConformityAssessmentRole` (class)                                                                                | Super-category for ConformityAssessmentBody / NotifiedBody (collapsed)                                                                                                                                                                                                                                                                              |
| ACTOR           | `eudpp:hasActor` (object prop)                                                                                          | Replaces a constellation of v1.7.1 inverse relations                                                                                                                                                                                                                                                                                                |
| ACTOR           | `eudpp:hasRepresentativeMandate` (object prop)                                                                          | First-class authorised-representative mandate edge                                                                                                                                                                                                                                                                                                  |
| CON             | `eudpp:isConnectedTo` (object prop)                                                                                     | Generic connector relation                                                                                                                                                                                                                                                                                                                          |
| CON             | `eudpp:inContextOfActivity` (object prop)                                                                               | Disambiguator for activities                                                                                                                                                                                                                                                                                                                        |
| CON             | `eudpp:inContextOfDPP` (object prop)                                                                                    | Disambiguator for DPPs                                                                                                                                                                                                                                                                                                                              |
| CON             | `eudpp:inContextOfProduct` (object prop)                                                                                | Disambiguator for products                                                                                                                                                                                                                                                                                                                          |
| CON             | `eudpp:representsManufacturerForProduct` (object prop)                                                                  | Product-scoped manufacturer-rep edge                                                                                                                                                                                                                                                                                                                |
| LCA v1.9.4-Maki | 33 new classes (e.g. `eudpp:LCIAImpactCategory`, `eudpp:EN15804ImpactIndicator`, `eudpp:EPDDocument`, `eudpp:LCAStudy`) | Major restructuring of the LCA module: EN 15804 + EPD framing replaces the v2.0 `lca:` prefix taxonomy. All 11 v2.0 `lca:Underscore` IRIs are absent from v1.9.4-Maki; the existing `LCAClass` enum retains them as `# −1.9.4-Maki` legacy entries for back-compat with 8 internal dataclasses. The 33 new classes are added under `# +1.9.4-Maki`. |
| LCA v1.9.4-Maki | ~30 new object properties (e.g. `eudpp:hasLCAResult`, `eudpp:hasComplianceDeclaration`)                                 | Not added to `EUDPPObjectProperty` in Phase 1 — Phase 4 wires up LCA validation and is the right place to add them                                                                                                                                                                                                                                  |

### Role consolidation (ACTOR v1.9.1)

The ESPR Annex distinguishes ~24 specific economic-operator role types
(Manufacturer, Importer, Distributor, Dealer, FulfilmentService
Provider, AuthorisedRepresentative, MarketSurveillanceAuthority,
CustomsAuthority, Customer, Consumer, IndependentOperator,
ProfessionalRepairer, Recycler, Refurbisher, Remanufacturer,
DPPServiceProvider, ConformityAssessmentBody, NotifiedBody,
CredentialAgency, IssuingAgency). v1.9.1 of the CIRPASS-2 ACTOR
ontology consolidates these into 6 super-role classes:

- `EconomicOperatorRole` (Manufacturer / Importer / Distributor / Dealer / Fulfilment / AuthorisedRep)
- `AuthorityRole` (MarketSurveillance / Customs)
- `EndUserRole` (Customer / Consumer / EndUser)
- `CircularEconomyRole` (Recycler / Refurbisher / Remanufacturer) — *new in v1.9.1*
- `ConformityAssessmentRole` (DPPServiceProvider / ConformityAssessmentBody / NotifiedBody) — *new in v1.9.1*
- *(Implicit super for IndependentOperator / ProfessionalRepairer)*

The library's existing `EUDPPRoleClass` retains the 24 specific role
IRIs as ESPR-finer-grained labels; they don't dereference against the
v1.9.1 TTL but remain meaningful for downstream LD payloads. The 2
new super-role IRIs were added as `# +1.9.1`.

## See also

- [docs/plans/CIRPASS_2_MIGRATION.md](../plans/CIRPASS_2_MIGRATION.md) —
  Phase 1 task list.
- [docs/adr/0002-canonical-eudpp-iri.md](../adr/0002-canonical-eudpp-iri.md) —
  rebase rationale (D-0.3).
- [docs/concepts/cirpass-2-spec-snapshot.md](cirpass-2-spec-snapshot.md) —
  pinned upstream artefacts.
