# CLI Reference

Complete reference for the dppvalidator command line interface.

## Synopsis

```
dppvalidator [OPTIONS] COMMAND [ARGS]...
```

## Global Options

```text
--version    Show version and exit
--help       Show help message and exit
-v           Verbose output
-q           Quiet mode (suppress output)
```

## Commands

### validate

Validate one or more Digital Product Passports.

```
dppvalidator validate INPUT... [OPTIONS]
```

**Arguments:**

| Argument | Description                                                |
| -------- | ---------------------------------------------------------- |
| INPUT... | Path(s) to JSON file(s), glob pattern(s), or `-` for stdin |

Supports multiple files and glob patterns for batch validation.

**Options:**

<!-- markdownlint-disable MD013 MD060 -->

| Option             | Default | Description                                                                  |
| ------------------ | ------- | ---------------------------------------------------------------------------- |
| `-s, --strict`     | false   | Enable strict validation                                                     |
| `-f, --format`     | text    | Output format (text, json, table)                                            |
| `--schema-version` | 0.6.1   | Schema version (one of `0.6.0`, `0.6.1`, `0.7.0`)                            |
| `--upgrade-from`   | none    | Run the v0.6 → v0.7 compat shim before validating; accepts `0.6.0` / `0.6.1` |
| `--fail-fast`      | false   | Stop on first error                                                          |
| `--max-errors`     | 100     | Maximum errors to report                                                     |

<!-- markdownlint-enable MD013 MD060 -->

### export

Export a DPP to different formats.

```
dppvalidator export INPUT [OPTIONS]
```

**Options:**

| Option         | Default | Description                  |
| -------------- | ------- | ---------------------------- |
| `-f, --format` | json    | Output format (json, jsonld) |
| `-o, --output` | stdout  | Output file path             |

### schema

Display schema information.

```text
dppvalidator schema [OPTIONS]
```

**Options:**

| Option      | Description               |
| ----------- | ------------------------- |
| `--version` | Schema version to display |
| `--list`    | List available versions   |

### migrate

Upgrade a v0.6.x DPP payload to v0.7.0 shape via the compat shim.

```text
dppvalidator migrate INPUT [OPTIONS]
```

**Arguments:**

<!-- markdownlint-disable MD060 -->

| Argument | Description                                |
| -------- | ------------------------------------------ |
| INPUT    | Path to v0.6.x JSON file, or `-` for stdin |

<!-- markdownlint-enable MD060 -->

**Options:**

<!-- markdownlint-disable MD013 MD060 -->

| Option              | Default | Description                                                                                                           |
| ------------------- | ------- | --------------------------------------------------------------------------------------------------------------------- |
| `-o, --output`      | stdout  | Output file path                                                                                                      |
| `--in-place`        | false   | Write the upgraded JSON back to the input path. Mutually exclusive with `-o`.                                         |
| `--accept-warnings` | false   | Write the upgraded JSON even when the shim emits warning- or error-severity events. INFO-severity events never block. |
| `--from`            | 0.6.x   | Source UNTP version family. Pass `0.6.0` / `0.6.1` to pin.                                                            |

<!-- markdownlint-enable MD013 MD060 -->

A sidecar `<output>.warnings.json` is always written alongside the
upgraded payload when blocking warnings fire (whether the main
output is written or not), so callers always have a
machine-readable record of every transformation.

## Exit Codes

<!-- markdownlint-disable MD013 MD060 -->

| Code | Meaning                                                                 |
| ---- | ----------------------------------------------------------------------- |
| 0    | Success / Valid (validate); upgrade with no blocking warnings (migrate) |
| 1    | Validation failed (validate); blocking warnings (migrate)               |
| 2    | Error (file not found, invalid JSON, unknown version)                   |

<!-- markdownlint-enable MD013 MD060 -->

## Examples

```bash
# Validate a single file (auto-detects the UNTP version)
dppvalidator validate passport.json

# Validate multiple files
dppvalidator validate passport1.json passport2.json passport3.json

# Validate with glob pattern
dppvalidator validate "data/passports/*.json"

# Batch validate with strict mode and JSON output
dppvalidator validate "data/*.json" --strict --format json

# Pin to v0.7.0 (fail-fast on payloads that declare a different version)
dppvalidator validate passport.json --schema-version 0.7.0

# Run the v0.6 → v0.7 shim, then validate as v0.7.0
dppvalidator validate passport-v06.json \
    --upgrade-from 0.6.1 \
    --schema-version 0.7.0

# Export to JSON-LD
dppvalidator export passport.json -f jsonld -o output.jsonld

# List schema versions (currently 0.6.0, 0.6.1, 0.7.0)
dppvalidator schema --list

# Upgrade a v0.6.x payload to v0.7.0 shape
dppvalidator migrate passport.json -o passport-v07.json

# Upgrade in place, accepting warnings
dppvalidator migrate passport.json --in-place --accept-warnings
```
