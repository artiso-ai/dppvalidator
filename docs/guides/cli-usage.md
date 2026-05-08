______________________________________________________________________

## description: CLI reference for validating and exporting DPPs.

# CLI Usage

The dppvalidator CLI provides commands for validating DPPs, exporting to different formats, and inspecting schemas.

## Commands

### validate

Validate one or more Digital Product Passport JSON files.

```
dppvalidator validate <input>... [options]
```

**Arguments:**

- `input...` — Path(s) to JSON file(s), glob pattern(s), or `-` for stdin

**Options:**

- `-s, --strict` — Enable strict JSON Schema validation
- `-f, --format` — Output format: `text`, `json`, `table` (default: text)
- `--schema-version` — Schema version (default: `0.6.1`; one of
  `0.6.0`, `0.6.1`, `0.7.0`)
- `--upgrade-from` — Run the v0.6 → v0.7 compat shim before validating
  (Phase 4); accepts `0.6.0` / `0.6.1`
- `--fail-fast` — Stop on first error
- `--max-errors` — Maximum errors to report (default: 100)

**v0.6.x examples:**

```bash
# Validate a single file (default schema-version is 0.6.1)
dppvalidator validate passport.json

# Pin v0.6.1 explicitly. A v0.7.0 payload through this command fails
# fast with VER001 (version mismatch).
dppvalidator validate passport.json --schema-version 0.6.1

# Validate multiple files
dppvalidator validate passport1.json passport2.json passport3.json

# Validate with glob pattern (quote to prevent shell expansion)
dppvalidator validate "data/passports/*.json"

# Batch validate entire directory
dppvalidator validate "data/**/*.json" --strict

# Validate from stdin
cat passport.json | dppvalidator validate -

# JSON output for CI/CD (includes summary for batch)
dppvalidator validate "*.json" --format json

# Table output for quick overview
dppvalidator validate "*.json" --format table
```

**v0.7.0 examples:**

```bash
# Pin v0.7.0 explicitly. The detection layer otherwise auto-detects
# from the payload's @context URL.
dppvalidator validate passport-v07.json --schema-version 0.7.0

# Run the compat shim, then validate as v0.7.0. Upgrade warnings are
# inlined in the validation output.
dppvalidator validate passport-v06.json \
    --upgrade-from 0.6.1 \
    --schema-version 0.7.0
```

**Batch Output:**

When validating multiple files, the output includes a summary:

- **Text format**: Individual results + summary counts
- **JSON format**: `{"files": [...], "summary": {"total": N, "valid": N, "invalid": N}}`
- **Table format**: Status table with error/warning counts per file

### export

Export a DPP to different formats.

```
dppvalidator export <input> [options]
```

**Options:**

- `-f, --format` — Output format: `json`, `jsonld` (default: jsonld)
- `-o, --output` — Output file path (default: stdout)

**Examples:**

```
# Export to JSON-LD
dppvalidator export passport.json --format jsonld

# Save to file
dppvalidator export passport.json --format jsonld -o output.jsonld
```

### schema

Manage DPP schemas.

```
dppvalidator schema <subcommand> [options]
```

**Subcommands:**

- `list` — List available schema versions
- `info` — Show schema information
- `download` — Download a schema version

**Options (for info/download):**

- `-v, --version` — Schema version (default: 0.6.1)
- `-o, --output` — Output directory for download

**Examples:**

```bash
# List every registered version (currently 0.6.0, 0.6.1, 0.7.0).
dppvalidator schema list

# Show schema info for v0.6.1.
dppvalidator schema info -v 0.6.1

# Show schema info for v0.7.0.
dppvalidator schema info -v 0.7.0

# Download schema to local directory.
dppvalidator schema download -v 0.7.0 -o ./schemas/
```

### migrate

Upgrade a v0.6.x DPP payload to v0.7.0 shape via the compat shim
(Phase 4). The full reference for the warning codes and field
renames is the [migration guide](migration-0-6-to-0-7.md).

```text
dppvalidator migrate <input> [options]
```

**Arguments:**

- `input` — Path to v0.6.x JSON file, or `-` for stdin.

**Options:**

- `-o, --output` — Output file path (default: stdout)
- `--in-place` — Write the upgraded JSON back to the input path
  (overwrites). Mutually exclusive with `-o`.
- `--accept-warnings` — Write the upgraded JSON even when the shim
  emits warning- or error-severity events. Without this, the command
  exits with code 1 on any non-info warning.
- `--from` — Source UNTP version family (default: `0.6.x`). Pass an
  explicit `X.Y.Z` to pin.

**Examples:**

```bash
# Default — upgrade to stdout, refuse if warnings fire.
dppvalidator migrate passport.json

# Write to an explicit output path.
dppvalidator migrate passport.json -o passport-v07.json

# Overwrite the input.
dppvalidator migrate passport.json --in-place

# Accept warnings; sidecar passport-v07.json.warnings.json is written
# alongside the upgraded payload.
dppvalidator migrate passport.json -o passport-v07.json --accept-warnings
```

**Exit codes:**

- `0` — Upgrade succeeded with no blocking warnings (or
  `--accept-warnings` was given).
- `1` — Blocking warnings fired and `--accept-warnings` was not given;
  the sidecar warnings file is still written.
- `2` — Error (file not found, invalid JSON, unknown source version).

## Exit Codes

| Code | Meaning                                    |
| ---- | ------------------------------------------ |
| 0    | Validation passed                          |
| 1    | Validation failed                          |
| 2    | Error (file not found, invalid JSON, etc.) |

## Environment Variables

| Variable                      | Description                                 |
| ----------------------------- | ------------------------------------------- |
| `DPPVALIDATOR_SCHEMA_VERSION` | Default schema version                      |
| `DPPVALIDATOR_LOG_LEVEL`      | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Next Steps

- [Validation Guide](validation.md) — Understanding validation layers
- [JSON-LD Export](jsonld.md) — Working with JSON-LD output
