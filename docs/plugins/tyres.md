# Tyres pilot plugin (`dppvalidator-tyres`)

> **Status: Pre-1.0 / Experimental.** The GDSO Birth v0.9 and
> Recycling v0.1 declarations are still moving — the rule contract
> may shift before the 1.0 cut. Production users should pin a specific
> version of `dppvalidator-tyres` and review the [`CHANGELOG`](https://github.com/artiso-ai/dppvalidator/blob/main/plugins/tyres/CHANGELOG.md)
> on every minor bump.

Phase 7 of [`docs/plans/CIRPASS_2_MIGRATION.md`] introduces this
plugin, scaffolded against the GDSO public declaration specs.

## Installation

```sh
uv add dppvalidator-tyres
# or
pip install dppvalidator-tyres
```

The plugin auto-registers via Python entry-points under the
`dppvalidator.validators` and `dppvalidator.exporters` groups; no
glue code is required at the call site. After install, verify
discovery:

```sh
$ uv run python -c "from dppvalidator.plugins.discovery import list_available_plugins; print(list_available_plugins())"
{'validators': [..., 'tyr001_dot_marking', 'tyr002_birth_chain', ...], 'exporters': [..., 'tyres_lifecycle_csv']}
```

## Wire shape

Tyre lifecycle data is carried in the UNTP DPP envelope's extension
slot:

```json
{
  "credentialSubject": {
    "extensions": {
      "tyreLifecycleHistory": {
        "birth": { /* GDSO Birth v0.9 */ },
        "events": [
          {"type": "collection", "declaration": { /* GDSO Collection v0.1 */ }},
          {"type": "retread",    "declaration": { /* GDSO Retread v0.1 */ }},
          {"type": "recycling",  "declaration": { /* GDSO Recycling v0.1 */ }}
        ]
      }
    }
  }
}
```

The plugin's rules walk this extension slot. Passports without the
extension are silently skipped — non-tyre DPPs are not affected.

## Rule reference

| Code     | Severity | Topic                    | Notes                                                                           |
| -------- | -------- | ------------------------ | ------------------------------------------------------------------------------- |
| `TYR001` | error    | DOT marking              | Required: `plantCode`, `sizeCode`, `weekOfYear`, `year`.                        |
| `TYR002` | error    | Birth chain completeness | Required: `tyreUuid`, `manufacturer.id`, `manufacturer.name`.                   |
| `TYR003` | warning  | Load index               | ETRTO range 60–130 (passenger / light-truck).                                   |
| `TYR004` | warning  | Speed rating             | ETRTO letter set: L, M, N, P, Q, R, S, T, U, H, V, W, Y, Z.                     |
| `TYR005` | warning  | Tyre dimensions          | Section width 125–445 mm; aspect ratio 20–95; rim 10–24 in.                     |
| `TYR006` | error    | Retread provenance       | Every Retread event names `previousBirthUuid`.                                  |
| `TYR007` | warning  | Collection actor         | Every Collection event identifies `collector.id` + `name`.                      |
| `TYR008` | warning  | Recycling method         | Closed set: mechanical / pyrolysis / devulcanisation / energy_recovery / other. |

## Models

| Model                  | Source spec          | Description                                   |
| ---------------------- | -------------------- | --------------------------------------------- |
| `Birth`                | GDSO Birth v0.9      | Manufacturer's at-mould declaration.          |
| `Collection`           | GDSO Collection v0.1 | Collector's at-end-of-first-life declaration. |
| `Retread`              | GDSO Retread v0.1    | Retreader's renewal declaration.              |
| `Recycling`            | GDSO Recycling v0.1  | Recycler's at-end-of-life declaration.        |
| `TyreLifecycleHistory` | (aggregate)          | Birth + chronologically-ordered events.       |

The aggregate enforces three cross-event invariants:

1. Every event's `tyreUuid` matches the Birth's.
1. Events are chronologically ordered.
1. At most one Recycling event (lifecycle terminator).

## Exporter

The plugin registers a CSV exporter under
`dppvalidator.exporters` group as `tyres-lifecycle-csv`. It
flattens a TyreLifecycleHistory into one row per declaration:

```sh
$ uv run dppvalidator export passport.json --format tyres-lifecycle-csv
tyreUuid,eventType,timestamp,actorId,actorName,method
550e8400-e29b-41d4-a716-446655440000,birth,2026-04-15T10:30:00+00:00,https://example.com/operator/acme,ACME Tyres,
550e8400-e29b-41d4-a716-446655440000,collection,2030-08-01T09:00:00+00:00,https://example.com/op/collector-eu,EU Tyre Collection,
550e8400-e29b-41d4-a716-446655440000,recycling,2031-02-15T11:00:00+00:00,https://example.com/op/recycler-de,Recycle Co.,mechanical
```

## License

GPL-3.0-or-later. See
[`plugins/tyres/LICENSE`](https://github.com/artiso-ai/dppvalidator/blob/main/plugins/tyres/LICENSE)
for the rationale; the canonical text is at
<https://www.gnu.org/licenses/gpl-3.0.html>.

The dppvalidator core is MIT-licensed; per the
[plugin-license isolation rule](https://github.com/artiso-ai/dppvalidator/blob/main/.claude/rules/plugin-licenses.md),
the core never imports from this plugin (one-way dependency only).

## Status note

Phase 7 of the migration plan (2026-05) explicitly marks this
plugin **Pre-1.0 / Experimental**. The GDSO Birth v0.9 spec was
last updated in 2025; the Recycling v0.1 declaration is still in
draft. Expect breaking changes in:

- Field names on the four declaration models.
- Rule IDs (the `TYR0NN` numerals are stable; the *severity* of
  individual rules may shift between minor releases).
- Exporter column ordering.

The plugin will move to 1.0 when the GDSO declarations stabilise
(planned for 2026-Q4).

## Sample fixture

A minimal Birth-only fixture lives at
[`plugins/tyres/samples/birth.json`](https://github.com/artiso-ai/dppvalidator/blob/main/plugins/tyres/samples/birth.json).
The Phase 7 exit criterion requires this fixture to validate
cleanly:

```sh
uv run dppvalidator validate plugins/tyres/samples/birth.json
# → ✓ VALID
```

[`docs/plans/cirpass_2_migration.md`]: ../plans/CIRPASS_2_MIGRATION.md
