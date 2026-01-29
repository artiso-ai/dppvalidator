# DPP Validator GitHub Action

Validate Digital Product Passports against the UNTP schema in your CI/CD pipeline.

## Usage

```yaml
- uses: artiso-ai/dppvalidator/.github/actions/validate-dpp@v1
  with:
    files: 'data/passports/*.json'
    strict: false
    fail-on-warning: false
```

## Inputs

| Input             | Description                           | Required | Default |
| ----------------- | ------------------------------------- | -------- | ------- |
| `files`           | File path or glob pattern to validate | Yes      | -       |
| `strict`          | Enable strict JSON Schema validation  | No       | `false` |
| `fail-on-warning` | Fail if warnings are found            | No       | `false` |
| `schema-version`  | UNTP DPP schema version               | No       | `0.6.1` |
| `python-version`  | Python version to use                 | No       | `3.11`  |

## Outputs

| Output          | Description                         |
| --------------- | ----------------------------------- |
| `valid`         | Whether all files passed validation |
| `error-count`   | Total number of errors found        |
| `warning-count` | Total number of warnings found      |

## Examples

### Basic Validation

```yaml
name: Validate DPP
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: artiso-ai/dppvalidator/.github/actions/validate-dpp@v1
        with:
          files: 'data/*.json'
```

### Strict Mode with Warning Failure

```yaml
- uses: artiso-ai/dppvalidator/.github/actions/validate-dpp@v1
  with:
    files: 'passports/**/*.json'
    strict: true
    fail-on-warning: true
```

### Using Outputs

```yaml
- uses: artiso-ai/dppvalidator/.github/actions/validate-dpp@v1
  id: validate
  with:
    files: 'data/*.json'

- name: Check results
  if: always()
  run: |
    echo "Valid: ${{ steps.validate.outputs.valid }}"
    echo "Errors: ${{ steps.validate.outputs.error-count }}"
    echo "Warnings: ${{ steps.validate.outputs.warning-count }}"
```

## Badge

Add a validation badge to your README:

```markdown
![DPP Validated](https://img.shields.io/badge/DPP-Validated-green)
```
