# ADR 0004 — Textile v2 ships as a built-in profile

**Status:** Accepted (Phase 7, 2026-05-08).

## Context

The Phase 7 task list asked for two pilot refreshes:

1. The textile pilot — add MVP Textile DPP v2 (2025-12-04) rules.
1. The tyres pilot — scaffold a brand-new GDSO-aligned plugin.

The plan was originally framed in terms of *plugins* for both
(`plugins/textiles/` for v2 textile rules; `plugins/tyres/` for
GDSO declarations). During implementation it became clear that
the two pilots have different licensing and packaging
requirements:

- **Tyres** tracks GDSO declarations whose interpretation we want
  to publish under a copyleft licence (GPL-3.0-or-later) so
  derived rule packs stay in the open-source commons. The plugin
  is a separate distribution package because its license boundary
  must be explicit.
- **Textiles** has no equivalent upstream-licensing constraint —
  the rules are interpretations of EU ESPR Annex requirements and
  the JRC preparatory study. The textile pilot already had
  built-in rules at
  `src/dppvalidator/validators/rules/v0_X/textile.py`; the v2
  rules are an *additive* upgrade to the same interpretation.

## Decision

Ship Textile v2 as a **built-in profile**, not an out-of-tree
plugin:

- New module
  [`src/dppvalidator/validators/rules/v0_7/textile_v2.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/rules/v0_7/textile_v2.py)
  carries the v2 rule pack alongside the existing v1 module.
- A profile registry
  (`dppvalidator.validators.rules.TEXTILE_PROFILES`) keys both
  packs (`textile-v1` / `textile-v2`).
- The CLI exposes `validate --profile {textile-v1,textile-v2}` to
  toggle between them.
- The two packs are *alternatives* — only one runs against any
  given payload. The validator's profile dispatch *replaces* the
  v1 textile rules with the chosen pack rather than running both.

The tyres pilot stays as a plugin package
([`plugins/tyres/`](https://github.com/artiso-ai/dppvalidator/tree/main/plugins/tyres))
with GPL-3.0-or-later licensing, per
[ADR 0003](0003-tyre-license.md).

## Consequences

**Pros**

- Single dependency: textile v2 ships with the core, no
  additional install step.
- Profile dispatch is uniform: any future built-in pilot pack
  (e.g. `electronics-v1`) can join the same registry without a
  separate plugin scaffold.
- The rule code lives next to the existing v1 textile module —
  shared helpers (`TEXTILE_HS_CHAPTERS`, fibre code lookups)
  don't have to cross a package boundary.

**Cons**

- License-clarity advantage of out-of-tree plugins is lost.
  Mitigation: the textile rules don't carry a copyleft upstream
  constraint, so this isn't a real concern.
- Adds 7 rule classes to the core code-size footprint. Mitigation:
  the rule classes are stateless and lazy-loaded only when the
  profile is set (no import-time cost when no profile is in use).

## Reversal cost

Low. If a future textile-rule licensing concern emerges, the v2
pack can be lifted into a `plugins/textiles/` plugin without
breaking the public API: the registry entries become
entry-points, and the `--profile textile-v2` flag continues to
resolve through the same dispatch hook.

## See also

- [Phase 7 task 7.1 in the migration plan](../plans/CIRPASS_2_MIGRATION.md)
  (engineering-side log).
- [ADR 0003 — Tyres plugin license](0003-tyre-license.md).
- [`textile_v2.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/validators/rules/v0_7/textile_v2.py).
