# ADR 0006 — Canonical validation-layer taxonomy

**Status:** Accepted (Docs Coherence Plan, 2026-05-10).

## Context

By the 0.5.0 (Preview) cut, dppvalidator's documentation surface had
drifted into **four** different taxonomies for the same engine, each
authoritative on its own page:

| Source                                                                                                                                                                                                                                                                      | Layer count | Names                                                                      |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------- |
| [`README.md`](https://github.com/artiso-ai/dppvalidator/blob/main/README.md), [`docs/index.md`](../index.md)                                                                                                                                                                | 7           | Schema, Model, Semantic, JSON-LD, Vocabulary, Plugin, Signature            |
| [`README.md`](https://github.com/artiso-ai/dppvalidator/blob/main/README.md) mermaid + [`docs/concepts/validation-layers.md`](../concepts/validation-layers.md) body                                                                                                        | 6           | Detection, Schema, Model, JSON-LD, Business, Cryptographic                 |
| [`docs/llms-ctx.txt`](../llms-ctx.txt)                                                                                                                                                                                                                                      | 8           | Detection, Schema, Model, Semantic, JSON-LD, Vocabulary, Plugin, Signature |
| [`docs/faq.md`](../faq.md), [`llms.txt`](https://github.com/artiso-ai/dppvalidator/blob/main/llms.txt), [`docs/plans/IMPLEMENTATION_PLAN.md`](../plans/IMPLEMENTATION_PLAN.md), [`README.md`](https://github.com/artiso-ai/dppvalidator/blob/main/README.md) §Documentation | 5           | Schema, Model, Semantic, JSON-LD, Cryptographic                            |

Each downstream phase of the Docs Coherence Plan rewrites layer counts
and error-code prefixes; the rewrites cannot proceed until one
taxonomy is canonical.

## Decision

The engine emits seven non-detection layers today, plus one detection
phase that produces no error codes of its own (it routes — see
[`src/dppvalidator/validators/detection.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/detection.py)).
We adopt the **"seven layers + detection"** framing and pin the table
below as the single canonical taxonomy. Every user-facing source
(README, mkdocs concept pages, FAQ, error-code reference,
`llms*.txt`, `AGENTS.md`) must use these names, this ordering, and
these prefixes verbatim.

| Layer   | Name       | Error-code prefix(es)                                                                                                | Module                                                                                                                                |
| ------- | ---------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Layer 0 | Detection  | _no prefix — routing only_                                                                                           | [`validators/detection.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/detection.py)             |
| Layer 1 | Schema     | `SCH001`–`SCH099`                                                                                                    | [`validators/schema.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/schema.py)                   |
| Layer 2 | Model      | `MDL001`–`MDL099`                                                                                                    | [`validators/model.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/model.py)                     |
| Layer 3 | JSON-LD    | `JLD001`–`JLD099`                                                                                                    | [`validators/jsonld_semantic.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/jsonld_semantic.py) |
| Layer 4 | Semantic   | `SEM001`–`SEM099`                                                                                                    | [`validators/semantic.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/semantic.py)               |
| Layer 5 | Vocabulary | `VOC001`–`VOC099`                                                                                                    | [`vocabularies/`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/vocabularies/)                                 |
| Layer 6 | Plugin     | per-plugin (e.g. `TXT001`–`TXT099` textiles, `CQ001`–`CQ099` CIRPASS quality, `TYR001`–`TYR099` tyres)               | [`plugins/`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/plugins/)                                           |
| Layer 7 | Signature  | _Reserved_ — `SIG001`–`SIG099` reserved; no structured codes shipped (verifier surfaces untyped error strings today) | [`verifier/`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/verifier/)                                         |

### Non-layer (cross-cutting) error codes

Several prefixes do not belong to a layer because they fire outside
the layered pipeline (parsing, version-routing, family-routing,
migration shims, advisory rules). These are documented as **non-layer
codes** so the layer table stays pure:

| Prefix | Surface                                                        | Module                                                                                                                              |
| ------ | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `PRS`  | Input parsing (file IO, JSON syntax) — pre-layer-1             | [`cli/commands/watch.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/cli/commands/watch.py)               |
| `DET`  | Family-mismatch surfaced when `--target` contradicts detection | [`validators/detection.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/detection.py)           |
| `VER`  | Version-mismatch when `--schema-version` contradicts detection | [`validators/`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/)                                   |
| `UPG`  | UNTP 0.6 → 0.7 upgrade-shim warnings                           | [`compat/upgrade_0_6_to_0_7.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/upgrade_0_6_to_0_7.py) |
| `MAP`  | Cross-family migration-shim warnings (UNTP ↔ CIRPASS)          | [`compat/_mapping_codes.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/compat/_mapping_codes.py)         |
| `PRT`  | Advisory rules (e.g. role-enum strictness)                     | [`models/v0_7/identifiers.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/models/v0_7/identifiers.py)     |

`SIG` is **reserved**: an audit during the Docs Coherence Plan
confirmed that the verifier currently returns plain
`errors: list[str]` (see
[`src/dppvalidator/verifier/verifier.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/verifier/verifier.py)).
The prefix is held for the future migration to structured codes; until
that work ships, user-facing docs name the layer as "Signature
(reserved)" and **do not** claim emitted `SIG0xx` codes.

## Why this taxonomy

1. **Every named layer has an emitter in source today.** The five-layer
   framing dropped Vocabulary (real codes — `VOC001`–`VOC005`), Plugin
   (real codes — `TXT*`, `CQ*`, `TYR*`), and Detection (real routing
   path); the six-layer framing dropped Vocabulary and Plugin; the
   eight-layer framing in `llms-ctx.txt` artificially split Schema
   detection from the routing layer. The seven-layer-plus-detection
   shape is the only one where layer count = emitter count.
1. **Backwards compatible with the 0.5.0 mermaid diagram.** The diagram
   in [`README.md`](https://github.com/artiso-ai/dppvalidator/blob/main/README.md) and
   [`docs/concepts/validation-layers.md`](../concepts/validation-layers.md)
   already labels Detection as Layer 0 and Schema/Model/JSON-LD/Business/Crypto
   as Layers 1-5. Phase 2d extends, rather than rewrites, that diagram
   with Vocabulary (5), Plugin (6), Signature (7).
1. **One source of truth for prefixes.** Phase 7 of the Docs Coherence
   Plan adds a CI guard that walks `src/` for every `\b(SCH|MDL|JLD|SEM|VOC|PRS|PRT|VER|UPG|MAP|DET|TXT|CQ|TYR)\d{3}\b`
   literal and asserts coverage in `mkdocs.yml` `nav.Errors`. The guard
   uses *this ADR* as its allow-list source.

## Migration

Phases 1–6 of the Docs Coherence Plan rewrite each user-facing source
to match this ADR. The mechanical replacements are:

| From                                              | To                                                               |
| ------------------------------------------------- | ---------------------------------------------------------------- |
| "five-layer", "Five-Layer", "5 validation layers" | "seven-layer", "Seven-Layer", "7 validation layers"              |
| "six-layer" (concept page mermaid)                | "seven-layer" (extended diagram)                                 |
| `MOD001`-`MOD099`                                 | `MDL001`-`MDL099`                                                |
| `SIG001`-`SIG099` _claimed as emitted_            | `SIG001`-`SIG099` _reserved; verifier emits string errors today_ |
| `MAP` / `DET` _absent from error-code reference_  | `MAP001`-`MAP005` and `DET001` documented as non-layer codes     |

## Consequences

**Pros**

- Single canonical layer count for every audience (humans, agents, CI guards).
- The mermaid diagrams in README and concept pages expand by three
  subgraphs (Vocabulary, Plugin, Signature) but the existing five
  edge labels are unchanged in slot order — `MOD` → `MDL` is the only
  in-place rename.
- Phase 7 CI guards become writable (the test asserts against this ADR).

**Cons**

- "Seven-layer" is a slightly more elaborate marketing line than
  "five-layer". Mitigation: README hero leads with the dual-spec story
  (UNTP + CIRPASS), not the layer count; layer detail lives one click
  deeper, in the concept page.
- "Reserved" status for `SIG` could surprise readers who scanned the
  pre-0.5.0 docs. Mitigation: the concept page calls out the
  reserved-vs-emitted distinction explicitly and links to a tracking
  issue for the future structured-code migration.

## Reversal cost

Low. The ADR is a documentation contract; reversing means another
mechanical pass through the same files. The only persistent cost is
already-published download URLs to `docs/errors/MDL*.md` (which match
source code, so cannot reasonably revert).

## See also

- [Docs Coherence Plan](../plans/DOCS_COHERENCE_PLAN.md) — the rollout
  schedule for this ADR.
- [`.claude/rules/untp-versioning.md`](https://github.com/artiso-ai/dppvalidator/blob/main/.claude/rules/untp-versioning.md) —
  the analogue for UNTP version literals (Phase 1 default-version
  drift uses the same pattern).
- [`docs/concepts/validation-layers.md`](../concepts/validation-layers.md) —
  expanded by Phase 2d to render this taxonomy in detail.
