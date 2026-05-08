______________________________________________________________________

paths:

- "plugins/\*\*/\*"
- "src/dppvalidator/\*\*/\*.py"

______________________________________________________________________

# Plugin License Rules

The `plugins/` directory contains separately-licensed packages. Follow these rules strictly.

## License isolation

- **Core package** (`src/dppvalidator/`): MIT licensed.
- **Plugin packages** (`plugins/*/`): may have different licenses (e.g. GPL-3.0).

## Critical rules

1. **No reverse imports**: core MUST NOT import from any plugin.

   - `src/dppvalidator/` cannot contain `from dppvalidator_textiles import ...`
   - Plugins depend on core, never the reverse.

1. **Separate `pyproject.toml`**: each plugin has its own with:

   - Its own `license` field.
   - Dependency on `dppvalidator>=X.Y.Z`.
   - Its own entry-points registration.

1. **LICENSE file per plugin**: each plugin directory must have its own LICENSE file.

1. **No code copying**: do not copy GPL-licensed code into MIT-licensed core.

   - Extend via inheritance, not duplication.
   - Use entry-points for plugin discovery.

## Current plugins

| Plugin   | Path                | License          | Upstream   |
| -------- | ------------------- | ---------------- | ---------- |
| textiles | `plugins/textiles/` | GPL-3.0-or-later | spec-unttp |

## When adding new plugins

1. Check upstream license compatibility.
1. Create `plugins/<name>/LICENSE` with appropriate license.
1. Set `license` in `plugins/<name>/pyproject.toml`.
1. Document in this file.
