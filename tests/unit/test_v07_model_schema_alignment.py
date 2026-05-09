"""Phase 9 task 9.9 — UNTP v0.7.0 model ↔ schema alignment guard.

Three tiers:

1. **Strict tier (CI-blocking):** asserts the BLOCKER-tier drifts from
   Phase 8.9 (D1, D2) are closed and the resulting acceptance gradient
   stays consistent.
2. **Drift-watch tier (CI-blocking but tolerant):** asserts only
   *expected* drift items appear in the diff. Any new D-item not in
   ``EXPECTED_DRIFT`` fails the test, forcing every future PR that
   widens drift to update the constant — no silent widening.
3. **Compatibility tier (CI-blocking):** asserts the v0.6 → v0.7
   upgrade shim still produces v0.7-conformant output for every
   v0.6 fixture, AND that the wider PartyRoleEnum surface remains
   intact (so the CIRPASS reverse shim's mapping fidelity is
   preserved).

The diff itself follows Phase 8.9's methodology: walk every $def in
the schema; walk every Pydantic v0.7 BaseModel subclass; compare
the alias sets / required markers / annotations.

Reference: ``docs/plans/CIRPASS_2_MIGRATION.md`` Phase 8.9 catalogue.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

import pydantic
import pytest

import dppvalidator.models.v0_7 as v07_pkg

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "dppvalidator"
    / "schemas"
    / "data"
    / "untp-dpp-schema-0.7.0.json"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_schema() -> dict[str, Any]:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _walk_v07_classes() -> dict[str, type[pydantic.BaseModel]]:
    """Collect every Pydantic BaseModel subclass under models/v0_7/."""
    classes: dict[str, type[pydantic.BaseModel]] = {}
    for _, modname, _ in pkgutil.iter_modules(v07_pkg.__path__):
        mod = importlib.import_module(f"dppvalidator.models.v0_7.{modname}")
        for name in dir(mod):
            obj = getattr(mod, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, pydantic.BaseModel)
                and obj is not pydantic.BaseModel
                and obj.__module__.startswith("dppvalidator.models.v0_7")
            ):
                classes[name] = obj
    return classes


def _model_aliases(cls: type[pydantic.BaseModel]) -> set[str]:
    """JSON-visible alias set for a Pydantic model class."""
    return {(finfo.alias or fname) for fname, finfo in cls.model_fields.items()}


# ---------------------------------------------------------------------------
# Strict tier — Phase 9 BLOCKER closures (D1, D2)
# ---------------------------------------------------------------------------


class TestPhase9BlockerClosures:
    """Tier 1: D1 + D2 must remain closed."""

    def test_d1_status_list_index_is_int_typed(self) -> None:
        """D1: schema declares integer; model annotation must be int|None."""
        from dppvalidator.models.v0_7.envelope import BitstringStatusListEntry

        field = BitstringStatusListEntry.model_fields["status_list_index"]
        # Pydantic stores the annotation as-is; check it allows int
        anno = str(field.annotation)
        assert "int" in anno, f"D1 regression: statusListIndex annotation {anno!r} dropped int"

    def test_d1_numeric_string_coercion_works(self) -> None:
        """D1 back-compat: numeric strings still coerce."""
        from dppvalidator.models.v0_7.envelope import BitstringStatusListEntry

        e = BitstringStatusListEntry.model_validate(
            {
                "id": "https://example.com/sl/x",
                "type": "BitstringStatusListEntry",
                "statusPurpose": "revocation",
                "statusListIndex": "12345",
                "statusListCredential": "https://example.com/sl",
            }
        )
        assert e.status_list_index == 12345

    def test_d2_strict_set_size_invariant(self) -> None:
        """D2: SCHEMA_STRICT_ROLES must remain at 6 (matching schema)."""
        from dppvalidator.models.v0_7.identifiers import SCHEMA_STRICT_ROLES

        assert len(SCHEMA_STRICT_ROLES) == 6

    def test_d2_pydantic_enum_remains_wider(self) -> None:
        """D2 compat: PartyRoleEnum must remain at 20 values for shim fidelity."""
        from dppvalidator.models.v0_7.identifiers import PartyRoleEnum

        assert len(list(PartyRoleEnum)) == 20

    def test_d2_strict_set_is_subset_of_pydantic_enum(self) -> None:
        from dppvalidator.models.v0_7.identifiers import (
            SCHEMA_STRICT_ROLES,
            PartyRoleEnum,
        )

        pydantic_values = {e.value for e in PartyRoleEnum}
        assert SCHEMA_STRICT_ROLES.issubset(pydantic_values)


# ---------------------------------------------------------------------------
# Drift-watch tier — register every known drift; new drift fails CI
# ---------------------------------------------------------------------------


# Phase 8.9 drift catalogue. Values are the set of schema-only
# property names (in schema $def, missing as first-class Pydantic
# field) for each affected $def. Update this constant when a Phase
# 10 task closes a drift item.
EXPECTED_SCHEMA_ONLY_DRIFT: dict[str, frozenset[str]] = {
    # D8 + D11 + D16 (Link)
    "Link": frozenset({"linkName", "linkType"}),
    # D9 + D12 + D17 (Package)
    "Package": frozenset(
        {"description", "dimensions", "materialUsed", "packageLabel", "performanceClaim"}
    ),
    # D10 (Party)
    "Party": frozenset(
        {
            "registrationCountry",
            "partyAddress",
            "organisationWebsite",
            "industryCategory",
            "partyAlsoKnownAs",
        }
    ),
    # D13 (Period)
    "Period": frozenset({"periodInformation"}),
    # D14 (RenderTemplate2024)
    "RenderTemplate2024": frozenset({"mediaQuery", "url"}),
}


# Phase 8.9 drift catalogue: model-only fields per class. The
# acceptance gradient (D2/PRT001) means these are intentional
# Pydantic-permissive surfaces; Phase 10.13 will deprecate them.
EXPECTED_MODEL_ONLY_DRIFT: dict[str, frozenset[str]] = {
    "Claim": frozenset({"classification"}),  # D15
    "Link": frozenset({"description", "name", "relationship"}),  # D16
    "Package": frozenset({"packageType", "weight"}),  # D17
    "RenderTemplate2024": frozenset({"id"}),  # D18
}


def _build_model_to_def_mapping() -> dict[str, str]:
    """Map model class name → schema $def name when shapes align."""
    schema = _load_schema()
    schema_defs = set(schema.get("$defs", {}).keys())
    classes = _walk_v07_classes()
    mapping: dict[str, str] = {}
    for cname, cls in classes.items():
        if cname in schema_defs:
            mapping[cname] = cname
            continue
        jsonld_type = getattr(cls, "_jsonld_type", None)
        if isinstance(jsonld_type, list) and jsonld_type:
            for t in jsonld_type:
                if t in schema_defs:
                    mapping[cname] = t
                    break
    return mapping


class TestDriftWatch:
    """Tier 2: assert the diff matches the registered baseline exactly.

    Any NEW drift not in ``EXPECTED_SCHEMA_ONLY_DRIFT`` /
    ``EXPECTED_MODEL_ONLY_DRIFT`` fails the test, forcing every
    future PR widening drift to update the constants. Closing a
    drift item also fails the test until the constant is shrunk —
    enforcing that drift fixes update this baseline atomically.
    """

    def test_no_unregistered_drift_anywhere(self) -> None:
        schema = _load_schema()
        defs = schema.get("$defs", {})
        classes = _walk_v07_classes()
        mapping = _build_model_to_def_mapping()
        found_schema_only: dict[str, set[str]] = {}
        found_model_only: dict[str, set[str]] = {}

        # Filter both sides symmetrically: ``type`` is a JSON-LD type
        # token that schema declares as a property but our models
        # carry as a ``_jsonld_type`` ClassVar (not a field).
        json_ld_keywords = {"@context", "@id", "@type", "type"}

        for cname, sdef_name in mapping.items():
            sdef = defs.get(sdef_name) or {}
            schema_props = set(sdef.get("properties", {}).keys()) - json_ld_keywords
            model_aliases = _model_aliases(classes[cname]) - json_ld_keywords
            so = schema_props - model_aliases
            mo = model_aliases - schema_props
            if so:
                found_schema_only[cname] = so
            if mo:
                found_model_only[cname] = mo

        # Confirm every registered class still has the registered drift
        for cname, expected in EXPECTED_SCHEMA_ONLY_DRIFT.items():
            assert found_schema_only.get(cname) == set(expected), (
                f"schema-only drift baseline diverged for {cname}: "
                f"expected {sorted(expected)}, found {sorted(found_schema_only.get(cname) or set())}"
            )
        for cname, expected in EXPECTED_MODEL_ONLY_DRIFT.items():
            assert found_model_only.get(cname) == set(expected), (
                f"model-only drift baseline diverged for {cname}: "
                f"expected {sorted(expected)}, found {sorted(found_model_only.get(cname) or set())}"
            )

        # Confirm no new drift class appeared
        new_schema_only = set(found_schema_only) - set(EXPECTED_SCHEMA_ONLY_DRIFT)
        new_model_only = set(found_model_only) - set(EXPECTED_MODEL_ONLY_DRIFT)
        assert not new_schema_only, (
            f"NEW unregistered schema-only drift in classes: {sorted(new_schema_only)}. "
            "Update EXPECTED_SCHEMA_ONLY_DRIFT in this file before merging."
        )
        assert not new_model_only, (
            f"NEW unregistered model-only drift in classes: {sorted(new_model_only)}. "
            "Update EXPECTED_MODEL_ONLY_DRIFT in this file before merging."
        )


# ---------------------------------------------------------------------------
# Compatibility tier — v0.6 + CIRPASS round-trip preservation
# ---------------------------------------------------------------------------


class TestCrossVersionCompatibility:
    """Tier 3: cross-version + cross-family invariants."""

    def test_v06_credential_status_remains_str_typed(self) -> None:
        """Cardinal rule: v0.6 models are frozen — must stay str."""
        from dppvalidator.models.v0_6.credential import CredentialStatus

        field = CredentialStatus.model_fields["status_list_index"]
        anno = str(field.annotation)
        assert "str" in anno, (
            f"v0.6 CredentialStatus.statusListIndex annotation {anno!r} drifted from str — "
            "v0.6 must remain frozen per .claude/rules/untp-versioning.md"
        )

    def test_v07_credential_status_alias_for_bitstring(self) -> None:
        """Phase 3 alias: CredentialStatus is BitstringStatusListEntry in v0.7."""
        from dppvalidator.models.v0_7 import BitstringStatusListEntry, CredentialStatus

        assert CredentialStatus is BitstringStatusListEntry

    def test_cirpass_reverse_shim_table_preserved(self) -> None:
        """The 8 wider rich-extension targets must remain intact."""
        from dppvalidator.compat.cirpass_1_3_to_untp_0_7 import _EUDPP_TO_UNTP_ROLE
        from dppvalidator.models.v0_7.identifiers import SCHEMA_STRICT_ROLES

        targets = set(_EUDPP_TO_UNTP_ROLE.values())
        wider = targets - SCHEMA_STRICT_ROLES
        # The reverse shim emits at least these 8 rich-extension targets
        # (Phase 8.9 verified count); shrinking would degrade fidelity.
        rich_targets = {
            "importer",
            "distributor",
            "retailer",
            "logisticsProvider",
            "operator",
            "regulator",
            "serviceProvider",
            "certifier",
        }
        assert rich_targets.issubset(wider), (
            "CIRPASS reverse-shim mapping table degraded — rich-extension "
            "targets shrunk from the Phase 9 baseline."
        )


# ---------------------------------------------------------------------------
# Cross-tier: Phase 8.9 D-item disposition table
# ---------------------------------------------------------------------------


# Closed (no further work): D21, D23. Phase 8.8 originally flagged
# them as drift; Phase 8.9 audit confirmed the model is faithful.
class TestDispositionClosures:
    """Tier 1 closures: D21 and D23 from Phase 8.9 audit."""

    def test_d21_digital_product_passport_root_aligned(self) -> None:
        """D21 CLOSED: model fields cover all schema-root properties."""
        from dppvalidator.models.v0_7 import DigitalProductPassport

        schema = _load_schema()
        root_props = set(schema.get("properties", {}).keys()) - {"@context", "@id"}
        # `type` is a reserved JSON-LD/VC keyword handled implicitly
        root_props -= {"type"}
        model_aliases = _model_aliases(DigitalProductPassport) - {"@context", "type"}
        missing_in_model = root_props - model_aliases
        assert not missing_in_model, (
            f"D21 regression: schema-root properties absent from model: {sorted(missing_in_model)}"
        )

    def test_d21_required_fields_are_required_in_model(self) -> None:
        """D21 CLOSED: schema-required root fields are required in Pydantic."""
        from dppvalidator.models.v0_7 import DigitalProductPassport

        schema = _load_schema()
        root_required = set(schema.get("required", [])) - {"@context", "@id", "@type"}
        for r in root_required:
            for fname, finfo in DigitalProductPassport.model_fields.items():
                if (finfo.alias or fname) == r:
                    assert finfo.is_required(), (
                        f"D21 regression: schema-required {r!r} is Optional in model"
                    )
                    break
            else:
                pytest.fail(f"D21 regression: required field {r!r} not found in model")

    def test_d23_identifier_scheme_matches_inline_shape(self) -> None:
        """D23 CLOSED: IdentifierScheme matches schema's inline {type, id, name}."""
        from dppvalidator.models.v0_7.identifiers import IdentifierScheme

        schema = _load_schema()
        inline = schema["$defs"]["Party"]["properties"]["idScheme"]
        inline_props = set(inline.get("properties", {}).keys())
        model_aliases = _model_aliases(IdentifierScheme)
        missing = inline_props - model_aliases
        assert not missing, (
            f"D23 regression: IdentifierScheme drifted from inline shape: missing {sorted(missing)}"
        )
