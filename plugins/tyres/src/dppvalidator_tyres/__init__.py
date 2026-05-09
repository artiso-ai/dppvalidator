"""dppvalidator-tyres — GDSO-aligned tyres pilot plugin.

Phase 7 of [docs/plans/CIRPASS_2_MIGRATION.md] in the
``dppvalidator`` core. The plugin lives at ``plugins/tyres/`` of the
core repo and is published to PyPI as ``dppvalidator-tyres``.

Status: **Pre-1.0 / Experimental.** The GDSO Birth v0.9 and
Recycling v0.1 declarations are still moving; rule IDs and message
wording may change before the 1.0 cut.

Public surface
==============

- :mod:`dppvalidator_tyres.models` — Pydantic models for the four
  GDSO declarations (Birth, Collection, Retread, Recycling) plus
  the :class:`TyreLifecycleHistory` aggregate.
- :mod:`dppvalidator_tyres.validators` — eight ``TYR0NN`` rules
  registered via entry-points.
- :mod:`dppvalidator_tyres.exporters` — CSV exporter that flattens
  a Tyre Lifecycle History into one row per declaration.

Cardinal rule
=============

Per ``.claude/rules/plugin-licenses.md`` (rule §1, "No reverse
imports"): the dppvalidator core MUST NOT import from this package.
Phase 7 task 7.9 of the migration plan adds a CI gate
(``tools/check_imports.py``) that fails the build when the rule
is violated.
"""

from __future__ import annotations

__version__ = "0.1.0"
__experimental__ = True

# Stable identifier the migration plan + CLI use to mark this
# plugin as Pre-1.0 in help text. Phase 9 of the migration plan
# uses it to gate the deprecation-warning ramp.
PLUGIN_STATUS = "Pre-1.0 / Experimental"

__all__ = [
    "PLUGIN_STATUS",
    "__experimental__",
    "__version__",
]
