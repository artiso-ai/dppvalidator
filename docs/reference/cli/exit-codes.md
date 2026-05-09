# CLI exit codes

Phase 6 task 6.7 of [docs/plans/CIRPASS_2_MIGRATION.md] formalises
the CLI exit-code surface. Every `dppvalidator` subcommand exits
with one of the codes below; values are stable across releases so
shell wrappers / CI pipelines / plugins may pattern-match on the
integer.

The same constants are exported from
[`dppvalidator.cli.main`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/cli/main.py)
(`EXIT_VALID`, `EXIT_INVALID`, `EXIT_ERROR`,
`EXIT_FAMILY_MISMATCH`, `EXIT_BLOCKING_WARNINGS`, `EXIT_IO_ERROR`).

| Code | Constant                 | Meaning                                                                                                                                                                                                       |
| ---- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0`  | `EXIT_VALID`             | Operation completed successfully. For `validate`, the input passed every layer with zero errors. For `export` / `migrate`, the output was written.                                                            |
| `1`  | `EXIT_INVALID`           | Validation produced one or more errors. The input parsed cleanly but failed one or more validation layers.                                                                                                    |
| `2`  | `EXIT_ERROR`             | Unrecoverable engine / shim failure (uncaught exception, dependency missing, invalid arguments not caught by argparse). The CLI prints a stack trace under `--verbose`.                                       |
| `3`  | `EXIT_FAMILY_MISMATCH`   | A `--target` (or `--to`) flag explicitly contradicts the payload's detected family. Surfaces `DET001`. New in Phase 6.                                                                                        |
| `4`  | `EXIT_BLOCKING_WARNINGS` | A migration / upgrade emitted at least one `warning`-or-higher diagnostic and the user did not pass `--accept-warnings`. The output is *not* written; a sidecar JSON file lists the warnings. New in Phase 6. |
| `5`  | `EXIT_IO_ERROR`          | IO failure: file not found, encoding error, glob pattern matched nothing, output path not writable. New in Phase 6 — distinguishes IO from logical failures.                                                  |

## Per-command code matrix

| Command    | `0`                                                  | `1`                                       | `2`                                    | `3`                                   | `4`                                           | `5`                                   |
| ---------- | ---------------------------------------------------- | ----------------------------------------- | -------------------------------------- | ------------------------------------- | --------------------------------------------- | ------------------------------------- |
| `validate` | All inputs valid                                     | One or more validation errors             | Engine crash                           | `--target` mismatches detected family | (n/a)                                         | File-not-found / glob match nothing   |
| `export`   | Output written                                       | Validation failed (input not a valid DPP) | Exporter crash                         | (n/a)                                 | (n/a)                                         | File-not-found / output write failure |
| `migrate`  | Output written, no warnings (or `--accept-warnings`) | (n/a)                                     | Shim crash                             | `--from` / `--to` family mismatch     | Blocking warnings without `--accept-warnings` | File-not-found / output write failure |
| `schema`   | Listing / download / info succeeded                  | (n/a)                                     | Unknown subcommand or download failure | (n/a)                                 | (n/a)                                         | Output directory not writable         |

## Examples

### Family-mismatch (code 3)

```sh
$ dppvalidator validate cirpass-payload.json --target untp
DET001: cirpass-payload.json — payload looks like 'cirpass'
        but --target='untp' pins the other family.
$ echo $?
3
```

### Blocking-warnings during migrate (code 4)

```sh
$ dppvalidator migrate untp-fixture.json --to cirpass-1.3 -o out.json
Migration to CIRPASS reference structure v1.3.0 emitted 5 blocking
warning(s); refusing to write. Re-run with --accept-warnings to
override, or fix the issues listed in the sidecar warnings file.
  [MAP002] (warning) $.dppIdentifier.scheme: …
  [MAP002] (warning) $.product.productName[0].language: …
  …
$ echo $?
4
$ ls out.json out.json.warnings.json
out.json.warnings.json   # only the sidecar exists; no main output
```

### IO error (code 5)

```sh
$ dppvalidator validate /no/such/file.json
File not found: /no/such/file.json
$ echo $?
5
```

## Rationale

Pre-Phase-6, the CLI used `0`/`1`/`2` for `valid`/`invalid`/`error`.
Wrappers couldn't distinguish "the file didn't exist" from "the
engine crashed", or "you passed `--target=untp` on a CIRPASS
payload" from "the payload had validation errors". Phase 6 adds
three orthogonal codes (`3` family-mismatch, `4` blocking-warnings,
`5` IO) so CI pipelines can branch precisely on the failure shape
without parsing the human-readable output.

The legacy codes remain unchanged so existing scripts and
golden-snapshot tests keep passing.
