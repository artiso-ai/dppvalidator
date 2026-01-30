______________________________________________________________________

## description: CLI reference for validating and exporting DPPs.

# CLI Usage

The dppvalidator CLI provides commands for validating DPPs, exporting to different formats, and inspecting schemas.

## Commands

### validate

Validate a Digital Product Passport JSON file.

```
dppvalidator validate <input> [options]
```

**Arguments:**

- `input` — Path to JSON file or `-` for stdin

**Options:**

- `-s, --strict` — Enable strict JSON Schema validation
- `-f, --format` — Output format: `text`, `json`, `table` (default: text)
- `--schema-version` — Schema version (default: 0.6.1)
- `--fail-fast` — Stop on first error
- `--max-errors` — Maximum errors to report (default: 100)

**Examples:**

```
# Validate a file
dppvalidator validate passport.json

# Validate from stdin
cat passport.json | dppvalidator validate -

# JSON output for CI/CD
dppvalidator validate passport.json --format json

# Strict mode with custom schema version
dppvalidator validate passport.json --strict --schema-version 0.6.1
```

### export

Export a DPP to different formats.

```
dppvalidator export <input> [options]
```

**Options:**

- `-f, --format` — Output format: `json`, `jsonld` (default: json)
- `-o, --output` — Output file path (default: stdout)

**Examples:**

```
# Export to JSON-LD
dppvalidator export passport.json --format jsonld

# Save to file
dppvalidator export passport.json --format jsonld -o output.jsonld
```

### schema

Display schema information.

```
dppvalidator schema [options]
```

**Options:**

- `--version` — Schema version to display
- `--list` — List available schema versions

**Examples:**

```
# Show current schema
dppvalidator schema

# List available versions
dppvalidator schema --list
```

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
