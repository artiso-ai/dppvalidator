"""CIRPASS reference-structure Pydantic models.

Phase 3 of [docs/plans/CIRPASS_2_MIGRATION.md] introduced this package
for the CIRPASS DPP reference structure (a hierarchical message model
distinct from UNTP's Verifiable-Credential envelope). The single
versioned namespace ``v1_3`` mirrors the UNTP convention
(``models/v0_6/``, ``models/v0_7/``).

Importing this package is intentionally lazy: ``import dppvalidator``
must not pull the CIRPASS surface eagerly (per the migration plan's
cross-cutting workstream X3 — cold-start budget). Use:

    from dppvalidator.models.cirpass.v1_3 import ReferencePassport

…and the package loads on first reference.
"""
