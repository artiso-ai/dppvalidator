# ADR 0003 — GDSO Tyre data-model license — provisional GPL-3.0

**Status:** Proposed (pending OA-1 closure)
**Date:** 2026-05-08
**Deciders:** dppvalidator maintainers (drafted during CIRPASS-2 migration planning)
**Migration-plan label:** OA-1
**Related phases:** Phase 0 (license confirmation), Phase 7 (tyres plugin scaffolding)

## Context

Phase 7 of the CIRPASS-2 migration plan scaffolds a new `plugins/tyres/`
package mirroring the GDSO Ambassador Data Models v1 and the four tyre
declarations (Birth v0.9, Collection v0.1, Retread v0.1, Recycling v0.1)
plus the Tyre Lifecycle History v1 wrapper, all hosted on the DPP
Vocabulary Hub under the *CIRPASS-2 Pilot: Tyre Digital Product
Passport* group.

The license under which GDSO publishes these artefacts is *not stated
on the spec listing page* as of 2026-05-08. The CIRPASS-2 Pilot group
is in a separate hub project, possibly with restricted access policy.
Phase 7 cannot ship without a known license:

- The plugin's own `pyproject.toml` declares a `license` field.
- The plugin's `LICENSE` file must be present.
- The license must be compatible with the plugin sitting alongside
  `plugins/textiles/` (GPL-3.0-or-later) and the MIT-licensed core,
  per [`.claude/rules/plugin-licenses.md`](https://github.com/artiso-ai/dppvalidator/blob/main/.claude/rules/plugin-licenses.md).

## Decision

Until the license is explicitly confirmed, scaffold the plugin under
**GPL-3.0-or-later**, mirroring `plugins/textiles/`. Promote this ADR
from `Proposed` to `Accepted` once OA-1 closes and the actual license
is recorded.

If OA-1 confirms a *different* license (e.g. the GDSO data is more
permissively licensed, or restricted to project members), this ADR is
*Superseded* by a new ADR carrying the correct license; the plugin's
`pyproject.toml`, `LICENSE`, and any module headers update in lockstep.

## Consequences

**Positive**

- Phase 7 can scaffold against a concrete default without waiting on
  the human-review gate. Code structure (entry-points, `pyproject.toml`
  shape, `LICENSE` placement) is fully workable.
- The default is the most-restrictive realistic choice, so no
  permissive-license expectations leak into either core or downstream
  consumers prematurely.
- Plugin license isolation is enforced by the Phase 7 task 7.9 import
  graph gate (`tools/check_imports.py`); a license correction requires
  no import changes.

**Negative**

- A subsequent license correction means a `git mv` of the plugin's
  `LICENSE` file and a `pyproject.toml` field update — still cheap, but
  not free.
- If GDSO publishes under a *less* permissive license than GPL-3.0
  (e.g. CC-BY-NC, with field-of-use restrictions), the entire
  scaffolding would need to be reconsidered: a non-OSI-approved license
  excludes the plugin from PyPI under the standard Trove classifiers.
  This case is the explicit blocker that OA-1 must resolve before
  Phase 7 ships.

## Alternatives considered

- **Block Phase 7 until OA-1 closes.** Rejected: stalls the work for
  a license-confirmation step that is independent of the engineering.
  The default-and-correct-later path keeps both moving.
- **Default to MIT** (matching core). Rejected: GDSO data is more
  likely upstream-restricted than upstream-permissive given the
  pilot-project context. MIT default gives consumers a wrong impression
  of permissiveness.
- **Default to "license: TBD" placeholder.** Rejected: PyPI rejects
  packages with no license; CI license-classifier checks fail.

## Validation hooks

- OA-1 (open action item, Phase 0 close) — owner: human reviewer.
- Phase 7 task 7.4 — `plugins/tyres/LICENSE` materialises the chosen
  license.
- Phase 7 task 7.9 — `tools/check_imports.py` gate enforces license
  isolation regardless of the chosen license.

## References

- [Migration plan §1.4 OA-1](../plans/CIRPASS_2_MIGRATION.md)
- [`.claude/rules/plugin-licenses.md`](https://github.com/artiso-ai/dppvalidator/blob/main/.claude/rules/plugin-licenses.md)
- DPP Vocabulary Hub — Tyre DPP Playground group: <https://dpp.vocabulary-hub.eu/specifications>
- GDSO project: confirm via vocab-hub Pilot project metadata.
