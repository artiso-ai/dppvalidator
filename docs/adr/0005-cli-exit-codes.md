# ADR 0005 — CLI exit-code surface (six codes)

**Status:** Accepted (Phase 6, 2026-05-08).

## Context

Pre-Phase-6, dppvalidator's CLI used three exit codes:

| Code | Meaning                                              |
| ---- | ---------------------------------------------------- |
| `0`  | Validation passed.                                   |
| `1`  | Validation produced errors.                          |
| `2`  | Engine error (uncaught exception, IO failure, etc.). |

Phase 6 of the CIRPASS-2 migration introduced two new failure
shapes that the legacy three-code surface couldn't express
distinctly:

- `--target {untp,cirpass}` mismatching the detected family —
  conceptually a different problem from "validation found errors"
  (the payload is fine; the user's flag is wrong).
- `migrate --to {...}` blocking on `MAP00X` warnings under
  `--strict` — also conceptually different from "validation
  errors".

CI consumers wanted to branch on the failure shape without
parsing human-readable error messages.

## Decision

Adopt a six-code exit surface, exposed as module-level constants
in
[`src/dppvalidator/cli/main.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/cli/main.py)
and documented at
[`docs/reference/cli/exit-codes.md`](../reference/cli/exit-codes.md):

| Code | Constant                 | Meaning                                                                                         |
| ---- | ------------------------ | ----------------------------------------------------------------------------------------------- |
| `0`  | `EXIT_VALID`             | Operation completed successfully.                                                               |
| `1`  | `EXIT_INVALID`           | Validation produced one or more errors.                                                         |
| `2`  | `EXIT_ERROR`             | Unrecoverable engine / shim failure (uncaught exception, dependency missing).                   |
| `3`  | `EXIT_FAMILY_MISMATCH`   | `--target` (or `--to`) explicitly contradicts the payload's detected family. Surfaces `DET001`. |
| `4`  | `EXIT_BLOCKING_WARNINGS` | A migration / upgrade emitted blocking warnings without `--accept-warnings`.                    |
| `5`  | `EXIT_IO_ERROR`          | IO failure: file not found, encoding error, glob match nothing, output write failure.           |

## Migration

The old `EXIT_ERROR=2` semantics partly overlapped with the new
`EXIT_IO_ERROR=5` (file-not-found returned `2` pre-Phase-6).
Phase 6 splits IO failures off into `5`; existing CI scripts that
treat any non-zero code as "something went wrong" continue to
work; scripts that branch specifically on `2` for engine errors
get the cleaner semantics.

Each pre-existing test that pinned the legacy `EXIT_ERROR` for
file-not-found was updated in Phase 6 to use `EXIT_IO_ERROR`.

## Consequences

**Pros**

- CI pipelines branch precisely on failure shape.
- Wrapper scripts (e.g. pre-commit hooks) can decide whether to
  retry (`5` IO transient) vs surface immediately (`1`/`3`/`4`).
- The exit table is a stable public contract — pinned by
  `tests/integration/test_cli_cirpass.py::test_phase6_exit_codes_stable`.

**Cons**

- Six codes is more than three. Mitigation: the table is short
  and the constants are self-documenting; the
  [`exit-codes.md`](../reference/cli/exit-codes.md) reference
  fits on one page.
- `EXIT_ERROR=2` is now a rarer case; consumers that conflated
  it with IO errors see a behaviour change. Mitigation: that
  conflation was a documentation gap, not a real contract;
  Phase 6 makes the boundary explicit.

## Reversal cost

Medium. Removing codes 3-5 would break wrapper scripts that
adopted them. The constants are public; removal would be a SemVer
major bump. Phase 10 of the migration plan does *not* plan to
revisit; the table is intended as the long-term contract.

## See also

- [`docs/reference/cli/exit-codes.md`](../reference/cli/exit-codes.md) —
  the documented contract.
- [Phase 6 task 6.7 in the migration plan](../plans/CIRPASS_2_MIGRATION.md)
  (engineering-side log).
- [`src/dppvalidator/cli/main.py`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/cli/main.py)
  — constant definitions.
