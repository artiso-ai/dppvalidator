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

Validate a Digital Product Passport.

```
dppvalidator validate INPUT [OPTIONS]
```

**Arguments:**

| Argument | Description                        |
| -------- | ---------------------------------- |
| INPUT    | Path to JSON file or `-` for stdin |

**Options:**

| Option             | Default | Description                       |
| ------------------ | ------- | --------------------------------- |
| `-s, --strict`     | false   | Enable strict validation          |
| `-f, --format`     | text    | Output format (text, json, table) |
| `--schema-version` | 0.6.1   | Schema version                    |
| `--fail-fast`      | false   | Stop on first error               |
| `--max-errors`     | 100     | Maximum errors to report          |

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

```
dppvalidator schema [OPTIONS]
```

**Options:**

| Option      | Description               |
| ----------- | ------------------------- |
| `--version` | Schema version to display |
| `--list`    | List available versions   |

## Exit Codes

| Code | Meaning           |
| ---- | ----------------- |
| 0    | Success / Valid   |
| 1    | Validation failed |
| 2    | Error             |

## Examples

```
# Validate a file
dppvalidator validate passport.json

# Validate with JSON output
dppvalidator validate passport.json -f json

# Export to JSON-LD
dppvalidator export passport.json -f jsonld -o output.jsonld

# List schema versions
dppvalidator schema --list
```
