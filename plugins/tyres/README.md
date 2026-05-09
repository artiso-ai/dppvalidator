# dppvalidator-tyres

> **Status: Pre-1.0 / Experimental.** The GDSO Birth v0.9 and Recycling
> v0.1 specifications are still moving — this plugin tracks them but
> does *not* claim production stability. The rule contract may shift
> without a SemVer bump until 1.0.

GDSO-aligned tyres pilot plugin for [dppvalidator]. Adds Pydantic
models for the tyre lifecycle declarations (Birth, Collection,
Retread, Recycling) plus an aggregate Tyre Lifecycle History
wrapper, and registers `TYR001…TYR008` validation rules.

## Installation

```sh
uv add dppvalidator-tyres
# or
pip install dppvalidator-tyres
```

The plugin auto-registers via Python entry-points (group
`dppvalidator.validators`); no glue code required at the call site.

## Rule codes

| Code     | Severity | Topic                                                                                       |
| -------- | -------- | ------------------------------------------------------------------------------------------- |
| `TYR001` | error    | DOT marking present and well-formed                                                         |
| `TYR002` | error    | Birth declaration carries the manufacturer-actor chain                                      |
| `TYR003` | warning  | Load index is in the standard ETRTO range                                                   |
| `TYR004` | warning  | Speed rating is a recognised letter code                                                    |
| `TYR005` | warning  | Section width / aspect ratio / rim diameter look sane                                       |
| `TYR006` | error    | Retread declarations name the upstream Birth UUID                                           |
| `TYR007` | warning  | Collection declarations identify the collecting actor                                       |
| `TYR008` | warning  | Recycling declarations name the recycling method (mechanical / pyrolysis / devulcanisation) |

## Models

Models live under `dppvalidator_tyres.models`. The aggregate
`TyreLifecycleHistory` wraps the four declaration types with a
single tyre-identifying Birth and a chronologically-ordered list
of subsequent events.

## License

GPL-3.0-or-later. See [`LICENSE`](LICENSE) for the rationale; the
canonical license text is at <https://www.gnu.org/licenses/gpl-3.0.html>.

## Status note

The GDSO Birth v0.9 spec was last updated in 2025. The Recycling v0.1
declaration is still in draft. The plugin's rule-pack interpretation
follows what's in the GDSO public docs; expect breaking changes in
the rule IDs / message wording until 1.0.

[dppvalidator]: https://github.com/artiso-ai/dppvalidator
