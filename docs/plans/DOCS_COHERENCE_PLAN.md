# Documentation Coherence Plan

**Status**: Draft — 2026-05-10
**Scope**: surgical fixes for cross-source documentation drift surfaced after
the 0.5.0 (Preview) cut.
**Out of scope**: rewriting concept pages, adding new guides, regenerating
benchmarks, plugin docs.

This plan is mechanical wherever possible. Each phase has a scoped touch
list, an exit gate, and a verification step. Phases 0–2 are blocking
(they encode decisions every later phase consults); 3–7 can land in
parallel once 0–2 are merged.

______________________________________________________________________

## Audit summary

Eight independent drift classes were found. The first three are
load-bearing for everything else:

| ID | Class                                        | Severity | Phase |
| -- | -------------------------------------------- | -------- | ----- |
| A  | Default UNTP version: docs say `0.6.1`, code says `0.7.0` since 0.5.0 | High | 1 |
| B  | Validation-layer taxonomy split (`five` vs `seven`; 5/6/7/8 numberings) | High | 0 + 2 |
| C  | Error-code prefix drift (`MOD` in docs, `MDL` in code; missing `MAP`/`DET`; phantom `SIG`) | High | 2 |
| D  | `docs/changelog.md` last entry is `0.1.0`; root `CHANGELOG.md` is at `0.5.0` | Medium | 3 |
| E  | mkdocs orphan files in `docs/` not in nav and not in `exclude_docs:` | Medium | 4 |
| F  | Project framing omits CIRPASS-2 (`mkdocs.yml site_description`, `llms*.txt`, README hero) | Medium | 5 |
| G  | `llms.txt` (root) and `docs/llms.txt` are out of sync with each other | Medium | 5 |
| H  | `AGENTS.md` / `CLAUDE.md` claim default `0.6.1` and omit CIRPASS family | Low | 6 |

No CI guard catches any of these today. Phase 7 closes that gap.

______________________________________________________________________

## Phase 0 — Pick a canonical layer taxonomy (decision-only)

**Why blocking**: Phases 2, 3, 5, 6 all rewrite layer counts and error-code
prefixes. They cannot proceed until one taxonomy is canonical.

The current state mixes four taxonomies:

| Source | Count | Names |
| ------ | ----- | ----- |
| [README.md:20](../../README.md#L20), [docs/index.md:20](../index.md#L20) | 7 | Schema, Model, Semantic, JSON-LD, Vocabulary, Plugin, Signature |
| [README.md:253](../../README.md#L253) mermaid + [docs/concepts/validation-layers.md](../concepts/validation-layers.md) body | 6 | Detection, Schema, Model, JSON-LD, Business, Cryptographic |
| [docs/llms-ctx.txt:30–39](../llms-ctx.txt) | 8 | Detection, Schema, Model, Semantic, JSON-LD, Vocabulary, Plugin, Signature |
| [docs/faq.md:15, :134](../faq.md), [llms.txt](../../llms.txt), [docs/IMPLEMENTATION_PLAN.md:352](../IMPLEMENTATION_PLAN.md#L352), [README.md:402](../../README.md#L402) | 5 | Schema, Model, Semantic, JSON-LD, Cryptographic |

### Action

Open an ADR — `docs/adr/0006-validation-layer-taxonomy.md` — recording
the decision. Recommended canonical taxonomy (matches what the engine
code actually emits today):

```
Layer 0  Detection         (no error prefix; routing only)
Layer 1  Schema            SCH001–SCH099
Layer 2  Model             MDL001–MDL099   ← NOT MOD
Layer 3  JSON-LD           JLD001–JLD099
Layer 4  Semantic          SEM001–SEM099
Layer 5  Vocabulary        VOC001–VOC099
Layer 6  Plugin            (per-plugin; e.g. TXT001–TXT099, CQ001–CQ099, TYR001–TYR099)
Layer 7  Signature         (verifier/, no prefix registered yet — see Phase 2)
```

This is the "seven layers + detection" framing, and it's the only one
where every layer has an emitter in the codebase today. Cross-cutting
codes (`PRS`, `VER`, `UPG`, `PRT`, `MAP`, `DET`) are documented as
"non-layer" codes in the same ADR.

### Exit gate

- ADR merged.
- Single sentence in [docs/concepts/validation-layers.md](../concepts/validation-layers.md)
  intro pins the chosen count and links the ADR.

______________________________________________________________________

## Phase 1 — Default UNTP version drift (`0.6.1` → `0.7.0`)

The 0.5.0 changelog records the flip
(`DEFAULT_VERSIONS[UNTP]: "0.6.1" → "0.7.0"` at
[src/dppvalidator/schemas/registry.py:191](../../src/dppvalidator/schemas/registry.py#L191)),
but the public docs still tell users the default is `0.6.1`.

### Touch list

Mechanical edits — every occurrence of "default 0.6.1", "current default
= 0.6.1", or `default_version → '0.6.1'` flips to `0.7.0` and the
example payloads should follow:

- [docs/index.md:21–22](../index.md#L21) — `(default)` annotation moves from `0.6.x` to `0.7.0`.
- [docs/faq.md:88, :95, :114](../faq.md) — version table marker; `# current default` comment; `--upgrade-from` example unchanged but reframe.
- [docs/concepts/untp-versions.md:18, :77, :90](../concepts/untp-versions.md) — table marker, comment in CLI block, `print(reg.default_version)`.
- [docs/concepts/validation-layers.md:71, :79–81](../concepts/validation-layers.md) — `(currently 0.6.1)` and pin example.
- [docs/guides/cli-usage.md:27–30, :37, :42, :124, :134, :165](../guides/cli-usage.md) — every `default: 0.6.1` and the comment-only examples.
- [docs/llms-ctx.txt:128](../llms-ctx.txt) — `dppvalidator schema --version 0.6.1` example flips.
- [docs/llms.txt:10](../llms.txt), [llms.txt:10](../../llms.txt) — "Built-in UNTP DPP 0.6.1 schema support" → "UNTP DPP 0.6.x + 0.7.0 + CIRPASS-2 v1.3.0" (handled fully in Phase 5; Phase 1 just removes the false `0.6.1`-only claim).
- [AGENTS.md](../../AGENTS.md) — "Default version: ... (currently 0.6.1)" → `0.7.0` with a note that `compat.active_version()` is the runtime accessor (already mandated by [.claude/rules/untp-versioning.md](../../.claude/rules/untp-versioning.md)).

### Verification

```bash
# Should return zero hits in user-facing docs after Phase 1.
rg -n '(default|currently)\s*[:=]?\s*[`"]?0\.6\.1' \
   README.md docs/ AGENTS.md CLAUDE.md llms.txt \
   --glob '!docs/plans/**' --glob '!docs/IMPLEMENTATION_PLAN.md'
```

### Exit gate

- Grep above is clean.
- Cardinal rule §1 (no bare UNTP version literals outside `registry.py` /
  `contexts.py`) is unaffected — these are docs, not code.

______________________________________________________________________

## Phase 2 — Error-code prefix and layer-numbering rewrite

Driven by Phase 0. Rewrite every place that names error prefixes or layer
numbers.

### 2a · `MOD` → `MDL` (concrete bug)

The actual code emits `MDL001`–`MDL099`
([src/dppvalidator/validators/model.py:93](../../src/dppvalidator/validators/model.py#L93),
[src/dppvalidator/validators/errors.py:61](../../src/dppvalidator/validators/errors.py#L61)),
and every `docs/errors/MDL*.md` file uses that prefix. The docs' `MOD`
references are dead links.

Touch list:

- [README.md:292](../../README.md#L292) — mermaid edge label.
- [docs/concepts/validation-layers.md:44, :138](../concepts/validation-layers.md) — mermaid + body.
- [docs/llms-ctx.txt:34](../llms-ctx.txt).
- [docs/reference/api/validators.md:107](../reference/api/validators.md#L107).
- [docs/faq.md:160–168](../faq.md) error-code prefix table.

### 2b · Add `MAP` and `DET` to the public error catalogue

`MAP001`–`MAP005` are emitted by the cross-family compat shims
([src/dppvalidator/compat/_untp_cirpass_map.py](../../src/dppvalidator/compat/_untp_cirpass_map.py),
[src/dppvalidator/compat/cirpass_1_3_to_untp_0_7.py](../../src/dppvalidator/compat/cirpass_1_3_to_untp_0_7.py)),
and `DET001` by family detection
([src/dppvalidator/validators/detection.py:36](../../src/dppvalidator/validators/detection.py#L36)).
Neither has a `docs/errors/*.md` page or a [mkdocs.yml](../../mkdocs.yml)
nav entry.

Add:

- `docs/errors/DET001.md` (Family Mismatch).
- `docs/errors/MAP001.md`–`MAP005.md` (one per code; bodies can be
  short — title, when-emitted, fix suggestion, link to the relevant
  shim).
- Two new sections in [mkdocs.yml](../../mkdocs.yml) `nav.Errors`:
  `Detection Errors` (`DET001`) and `Mapping Errors` (`MAP001`–`MAP005`).
- A row each in [docs/faq.md:160–168](../faq.md) error-code prefix table.

### 2c · `SIG` prefix audit

Multiple docs claim `SIG001`–`SIG099`
([README.md:295](../../README.md#L295),
[docs/concepts/validation-layers.md:46, :188](../concepts/validation-layers.md),
[docs/llms-ctx.txt:39](../llms-ctx.txt)),
but `rg "SIG0\d{2}" src/` returns nothing. Either:

- the verifier emits codes under a different prefix (`MDL010` family
  covers issuer errors; signature failures may currently surface as
  `MDL` or untyped exceptions) — in which case the docs are wrong, or
- the prefix is reserved for a planned phase and should be marked
  *Reserved* until codes ship.

**Action**: confirm by reading
[src/dppvalidator/verifier/](../../src/dppvalidator/verifier/) and
[src/dppvalidator/validators/results.py](../../src/dppvalidator/validators/results.py).
Fix whichever side is wrong; do not invent codes to satisfy docs.

### 2d · Layer-numbering rewrite

Rewrite all four off-canon framings to match the Phase 0 ADR. Highest-
churn files:

- [README.md:253–296](../../README.md#L253) — mermaid + table; rename
  the section "Seven-Layer Validation Architecture" and add Vocabulary
  / Plugin / Signature subgraphs (or document why mermaid only renders
  the dispatch path).
- [README.md:402](../../README.md#L402) — "five-layer architecture"
  → "seven-layer architecture".
- [docs/concepts/validation-layers.md](../concepts/validation-layers.md) —
  expand body to match title; either add Vocabulary / Plugin /
  Signature sections or rename to "Six-Layer". (Recommendation: add
  the missing sections — they exist in code, just not in prose.)
- [docs/faq.md:15, :134–141](../faq.md) — flip "five" → "seven";
  rewrite the numbered list.
- [docs/IMPLEMENTATION_PLAN.md:352, :957](../IMPLEMENTATION_PLAN.md) —
  internal plan; quickest fix is to mark it historical (this file
  becomes Phase 4 candidate for `exclude_docs:`).
- [llms.txt:9](../../llms.txt), [docs/llms.txt:9](../llms.txt) — flip
  to canonical seven-layer phrasing (Phase 5 regenerates these
  fully).

### Exit gate

```bash
# After Phase 2 these should all return zero hits in user-facing docs:
rg -n 'MOD0\d{2}' README.md docs/ --glob '!docs/plans/**'
rg -n '(five|5)[\s-]?(layer|validation layer)' README.md docs/ llms.txt --glob '!docs/plans/**'
```

______________________________________________________________________

## Phase 3 — Changelog reconciliation

[docs/changelog.md](../changelog.md) stops at `[0.1.0] - 2026-01-29`.
The root [CHANGELOG.md](../../CHANGELOG.md) is at `[0.5.0] - 2026-05-09 (Preview)`.

### Action

Pick one of two patterns; both are common:

1. **Mirror via include** — replace [docs/changelog.md](../changelog.md)
   contents with a one-line snippet:

   ```markdown
   --8<-- "CHANGELOG.md"
   ```

   `pymdownx.snippets` (already loaded in [mkdocs.yml:84](../../mkdocs.yml#L84))
   will inline it at build time. Add `CHANGELOG.md` to the snippets
   `base_path`.

2. **Symlink** — `ln -s ../../CHANGELOG.md docs/changelog.md`. Simpler,
   but breaks `edit_uri` links.

Recommended: option 1.

### Exit gate

`docs/changelog.md` rendered output equals root `CHANGELOG.md` content
on every build. Add a CI assertion (Phase 7).

______________________________________________________________________

## Phase 4 — mkdocs build hygiene

Today [.github/workflows/docs.yml:24](../../.github/workflows/docs.yml#L24)
runs `mkdocs gh-deploy --force` without `--strict`, so orphan files in
`docs/` silently ship to the deployed site without nav placement.

### Inventory of orphans

Files / directories in `docs/` that are neither in `nav:` nor matched by
`exclude_docs:`:

- `docs/IMPLEMENTATION_PLAN.md`
- `docs/IMPROVEMENT_ROADMAP.md`
- `docs/REFACTORING_PLAN.md`
- `docs/STRATEGIC_ROADMAP.md`
- `docs/UNTTP_PLUGIN_PLAN.md`
- `docs/VC_WALLET_ROADMAP.md`
- `docs/dpp_validator_description.md`
- `docs/plugins.md` (note: `docs/plugins/tyres.md` *is* in nav)
- `docs/contributing/SECURITY_SETUP.md`
- `docs/dpp/` (raw schema fixtures: `dpp.json`, `jsonschema.json`)
- `docs/uv/uv.md`
- `docs/windsurf/cascade-reference.md`

### Action

Decide per file (one of three):

1. **Keep + add to nav** — only for files that are user-facing (e.g.
   `docs/plugins.md` may merit a top-level Plugins overview; promote it
   into nav above the per-plugin pages).
2. **Move to `docs/plans/`** — internal plans / roadmaps. `plans/` is
   already in `exclude_docs:`, so nothing else to do.
3. **Delete** — if superseded (e.g.
   `docs/dpp_validator_description.md`, `docs/dpp/*.json`,
   `docs/uv/uv.md`, `docs/windsurf/cascade-reference.md` look like
   scratch artefacts; verify with `git log` first).

Recommended split:

- → `docs/plans/`: `IMPLEMENTATION_PLAN.md`, `IMPROVEMENT_ROADMAP.md`,
  `REFACTORING_PLAN.md`, `STRATEGIC_ROADMAP.md`, `UNTTP_PLUGIN_PLAN.md`,
  `VC_WALLET_ROADMAP.md`.
- → `nav:` (Contributing tab): `contributing/SECURITY_SETUP.md`.
- → `nav:` (Plugins overview, above tyres): `docs/plugins.md` if it's
  the canonical overview; otherwise delete.
- → delete (after `git log` review): `docs/dpp/`, `docs/uv/`,
  `docs/windsurf/`, `docs/dpp_validator_description.md`.

### Then

Add `--strict` to [.github/workflows/docs.yml](../../.github/workflows/docs.yml):

```yaml
- name: Build docs (strict)
  run: uv run mkdocs build --strict
- name: Deploy docs
  if: github.ref == 'refs/heads/main'
  run: uv run mkdocs gh-deploy --force
```

`--strict` will additionally catch broken cross-doc links from Phase 1/2
and any new orphans.

### Exit gate

`uv run mkdocs build --strict` exits 0.

______________________________________________________________________

## Phase 5 — `llms*.txt` and project framing

### 5a · Single-source `llms.txt`

There are two copies — [llms.txt](../../llms.txt) (repo root) and
[docs/llms.txt](../llms.txt) — and they disagree (root says
"Five-layer", docs/ says "Seven-layer", both claim `UNTP DPP 0.6.1`
support without `0.7.0` or CIRPASS-2).

Action: make root `llms.txt` a symlink to `docs/llms.txt` (or vice
versa) and rewrite once. Same for [llms-ctx.txt](../../llms-ctx.txt) ↔
[docs/llms-ctx.txt](../llms-ctx.txt).

Update content (post-Phase 0/1/2):

- "Seven-layer validation: schema, model, semantic, JSON-LD, vocabulary,
  plugin, signature".
- "Schema support: UNTP DPP 0.6.0 / 0.6.1 / 0.7.0 (default) and CIRPASS
  v1.3.0".
- Add `[rdf]` extra to the install snippet
  ([docs/llms-ctx.txt:25](../llms-ctx.txt) currently omits it).
- Add the `MDL` / `MAP` / `DET` prefixes wherever `MOD` / `SIG` were
  cited.

### 5b · `mkdocs.yml site_description` and README hero

- [mkdocs.yml:2](../../mkdocs.yml#L2): currently
  `Python library for validating Digital Product Passports (UNTP DPP)`.
  Sync to `pyproject.toml` description (which already names CIRPASS):
  `Python library for validating Digital Product Passports (DPP)
  according to EU ESPR regulations and CIRPASS/UNECE ontologies`.
- [README.md:14](../../README.md#L14): "according to EU ESPR
  regulations and UNTP standards" — extend to mention CIRPASS-2 and
  UNTP, since 0.5.0 ships both as first-class families.

### Exit gate

`pyproject.toml` description, `mkdocs.yml site_description`,
`README.md` hero, and `llms*.txt` Overview lines describe the same
scope using CIRPASS + UNTP + ESPR phrasing.

______________________________________________________________________

## Phase 6 — `AGENTS.md` / `CLAUDE.md` repo-instruction sync

[AGENTS.md](../../AGENTS.md) is imported by
[CLAUDE.md](../../CLAUDE.md), so one edit covers both.

Touch list:

- "Default version: ... (currently `0.6.1`)" → `0.7.0`. (Already in
  Phase 1 grep, listed here for completeness.)
- "dppvalidator supports **UNTP DPP 0.6.x and 0.7.0** in the same
  release" → extend with "and CIRPASS DPP reference structure 1.3.0
  (`SchemaFamily.CIRPASS`)".
- Tech-stack block: add `[rdf]` extra and the SHACL story; mention
  `dppvalidator.compat.active_version()` (already mentioned but worth
  surfacing in the version-handling section).
- Directory tree: add `models/cirpass/v1_3/` and
  `validators/rules/cirpass_v1_3/` (both shipped in 0.5.0).

### Exit gate

`AGENTS.md` factually matches `src/dppvalidator/` tree and the 0.5.0
changelog.

______________________________________________________________________

## Phase 7 — CI guards (regression prevention)

Without guards, the same drift will recur on every release. Add three:

### 7a · Strict mkdocs build (covered in Phase 4)

```yaml
# .github/workflows/docs.yml
- run: uv run mkdocs build --strict
```

Catches: orphan files, broken intra-doc links, undefined nav targets.

### 7b · Pre-commit "no stale default-version literal" guard

A small `tools/check_doc_default_version.py` script that greps user-
facing docs for `default.*0\.\d+\.\d+` and asserts the version matches
`DEFAULT_VERSIONS[SchemaFamily.UNTP]` from
[src/dppvalidator/schemas/registry.py](../../src/dppvalidator/schemas/registry.py).
Wire it into `.pre-commit-config.yaml` and the `ci.yml` lint job.

This is the docs-side analogue of the existing
[tests/unit/test_no_version_literals.py](../../tests/unit/test_no_version_literals.py)
guard for source code.

### 7c · Error-code-prefix coverage test

`tests/unit/test_doc_error_code_coverage.py`:

- Walk `src/` for every `\b(SCH|MDL|JLD|SEM|VOC|PRS|PRT|VER|UPG|MAP|DET|TXT|CQ|TYR)\d{3}\b` literal.
- Assert each appears in `mkdocs.yml` `nav.Errors` AND has a
  corresponding `docs/errors/<CODE>.md`.
- Inverse: every `docs/errors/<CODE>.md` file maps back to a code
  emitted by `src/`.

This catches both the `MOD`/`MDL` class of typos *and* future
unmaintained docs/errors entries.

### Exit gate

All three guards green on `develop` after Phases 0–6 land.

______________________________________________________________________

## Sequencing and PR boundaries

| Phase | Depends on | Suggested PR |
| ----- | ---------- | ------------ |
| 0     | —          | `docs(adr): canonical validation-layer taxonomy` |
| 1     | 0          | `docs: flip default UNTP version to 0.7.0` |
| 2a    | 0          | `docs: rename MOD error-code prefix to MDL` |
| 2b    | 0          | `docs(errors): add DET and MAP error pages` |
| 2c    | 0          | `docs(errors): audit SIG prefix` (may be a code-side fix) |
| 2d    | 0, 2a      | `docs: align validation-layer taxonomy across all sources` |
| 3     | —          | `docs: include root CHANGELOG via snippets` |
| 4     | 1, 2, 3    | `docs: mkdocs build hygiene + --strict` |
| 5     | 0, 1, 2    | `docs: refresh llms*.txt and CIRPASS-2 framing` |
| 6     | 1, 5       | `docs: sync AGENTS.md / CLAUDE.md with 0.5.0 reality` |
| 7     | 4          | `ci: docs coherence guards` |

Total: ~10 small PRs. Each phase is independently revertible.

______________________________________________________________________

## Verification checklist (final)

After all phases land, this single command should be silent:

```bash
# Default-version drift
! rg -nq '(default|currently).{0,20}\b0\.6\.1\b' README.md docs/ llms.txt llms-ctx.txt AGENTS.md \
    --glob '!docs/plans/**'
# Layer-count drift
! rg -nq '\bfive[ -](validation )?layer' README.md docs/ llms.txt --glob '!docs/plans/**'
# Stale error-code prefix
! rg -nq '\bMOD0\d{2}\b' README.md docs/ --glob '!docs/plans/**'
# Strict mkdocs build
uv run mkdocs build --strict
# Pre-commit / CI guards
uv run pytest tests/unit/test_doc_error_code_coverage.py -v
```

When every line of that block exits 0, the documentation surface is
coherent with the codebase as of 0.5.0 and protected against the same
drift recurring at 0.6.0.
