"""Phase 3b acceptance tests: v0.7 semantic rules + version-keyed dispatch.

This module covers the Phase 3b deliverables in
``docs/plans/UNTP_0.7.0_MIGRATION.md``:

1. The :data:`ALL_RULES_BY_VERSION` dispatch is in lock-step with
   :data:`SCHEMA_REGISTRY` — every registered version has a rule list.
2. The :class:`SemanticValidator` selects the right rule list when
   ``rules`` is left at the default ``None``.
3. Each ported v0.7 rule fires on the new envelope shape (no false
   positives from v0.6-shaped checks) — see the per-class smoke tests.
4. The dropped rule (``OperationalScopeRule`` / SEM007) is documented
   in :data:`DROPPED_RULES_V0_6_TO_V0_7` but is **not** in
   :data:`ALL_RULES_V0_7`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from dppvalidator.models import v0_7
from dppvalidator.schemas.registry import SCHEMA_REGISTRY
from dppvalidator.validators.rules import ALL_RULES_BY_VERSION
from dppvalidator.validators.rules.v0_7 import (
    ALL_RULES_V0_7,
    DROPPED_RULES_V0_6_TO_V0_7,
    CircularityContentRule,
    CIRPASSMandatoryAttributesRule,
    ConformityClaimRule,
    GranularitySerialNumberRule,
    HazardousMaterialRule,
    MassFractionSumRule,
    ValidityDateRule,
)
from dppvalidator.validators.semantic import SemanticValidator

_UPSTREAM_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "upstream" / "v0.7.0"


def _load_canonical() -> dict:
    p = _UPSTREAM_DIR / "samples" / "DigitalProductPassport_instance.json"
    if not p.is_file():  # pragma: no cover — vendored in Phase 0
        pytest.skip(f"Upstream sample missing: {p}")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def canonical_v07() -> v0_7.DigitalProductPassport:
    return v0_7.DigitalProductPassport.model_validate(_load_canonical())


# ---------------------------------------------------------------------------
# 1. Dispatch-table consistency
# ---------------------------------------------------------------------------


class TestRuleDispatchConsistency:
    """``ALL_RULES_BY_VERSION`` must cover every key in ``SCHEMA_REGISTRY``."""

    def test_every_registered_version_has_a_rule_set(self) -> None:
        missing = sorted(set(SCHEMA_REGISTRY) - set(ALL_RULES_BY_VERSION))
        assert not missing, (
            f"ALL_RULES_BY_VERSION is missing entries for {missing}. "
            "Add them in src/dppvalidator/validators/rules/__init__.py."
        )

    def test_no_orphan_rule_sets(self) -> None:
        extra = sorted(set(ALL_RULES_BY_VERSION) - set(SCHEMA_REGISTRY))
        assert not extra, f"ALL_RULES_BY_VERSION has entries {extra} not in SCHEMA_REGISTRY."

    def test_v07_drops_operational_scope_rule(self) -> None:
        """SEM007 is the canonical dropped rule — must be advertised in DROPPED_RULES."""
        assert "SEM007" in DROPPED_RULES_V0_6_TO_V0_7
        # And it must NOT appear in the v0.7 rule list.
        rule_ids = {getattr(r, "rule_id", None) for r in ALL_RULES_V0_7}
        assert "SEM007" not in rule_ids


# ---------------------------------------------------------------------------
# 2. SemanticValidator dispatch
# ---------------------------------------------------------------------------


class TestSemanticValidatorDispatch:
    """The validator picks the right rule list when ``rules`` is None."""

    def test_v06_uses_v06_rules(self) -> None:
        v = SemanticValidator(schema_version="0.6.1")
        ids = {getattr(r, "rule_id", None) for r in v.rules}
        assert "SEM007" in ids, (
            "Expected the v0.6 rule set to include OperationalScopeRule (SEM007)."
        )

    def test_v07_uses_v07_rules(self) -> None:
        v = SemanticValidator(schema_version="0.7.0")
        ids = {getattr(r, "rule_id", None) for r in v.rules}
        assert "SEM007" not in ids, (
            "v0.7 rule set must NOT include OperationalScopeRule — see DROPPED_RULES_V0_6_TO_V0_7."
        )
        # Sanity: it should still include the ported rules.
        assert {"SEM001", "SEM003", "CQ001"}.issubset(ids)

    def test_unknown_version_falls_back_to_default(self) -> None:
        v = SemanticValidator(schema_version="9.9.9")
        # Should fall back to ALL_RULES (v0.6.x default).
        assert len(v.rules) > 0

    def test_explicit_rules_override(self) -> None:
        custom = [MassFractionSumRule()]
        v = SemanticValidator(schema_version="0.7.0", rules=custom)
        assert v.rules is custom


# ---------------------------------------------------------------------------
# 3. v0.7 rule semantics (no false positives, fires when expected)
# ---------------------------------------------------------------------------


class TestV07RulesNoFalsePositives:
    """Ported rules walking the v0.7 shape produce zero violations on the
    canonical sample (which is well-formed)."""

    @pytest.mark.parametrize(
        "rule_cls",
        [
            # NOTE: ``MassFractionSumRule`` is intentionally NOT in this set —
            # the canonical 0.7.0 sample carries a partial-declaration material
            # provenance (one material at 30 %), so SEM001 *should* fire as a
            # warning. That's a "rule fires correctly", not a "false positive".
            # See ``test_mass_fraction_rule_fires_on_partial_declaration`` below.
            ValidityDateRule,
            HazardousMaterialRule,
            CircularityContentRule,
            ConformityClaimRule,
            GranularitySerialNumberRule,
            CIRPASSMandatoryAttributesRule,
        ],
    )
    def test_rule_clean_on_canonical_sample(
        self,
        canonical_v07: v0_7.DigitalProductPassport,
        rule_cls: type,
    ) -> None:
        rule = rule_cls()
        violations = rule.check(canonical_v07)
        assert violations == [], (
            f"{rule_cls.__name__} produced {len(violations)} violation(s) on "
            f"a canonical 0.7.0 sample: {violations}"
        )

    def test_mass_fraction_rule_fires_on_partial_declaration(
        self, canonical_v07: v0_7.DigitalProductPassport
    ) -> None:
        """SEM001 fires (as a warning) when material provenance sums to < 1.0.

        The canonical 0.7.0 sample declares one material at mass fraction
        0.3 — that's a documented partial declaration and SEM001 must
        flag it so the user knows the material list is incomplete.
        """
        rule = MassFractionSumRule()
        violations = rule.check(canonical_v07)
        assert len(violations) == 1
        path, message = violations[0]
        assert path == "$.credentialSubject.materialProvenance"
        assert "partial declaration" in message
        # Severity is "warning" — not an error.
        assert rule.severity == "warning"


class TestV07RulesFire:
    """The ported rules still fire on the conditions they're meant to flag."""

    def _envelope(self, **overrides):
        sample = _load_canonical()
        sample.update(overrides)
        return v0_7.DigitalProductPassport.model_validate(sample)

    def test_validity_date_rule_fires_on_inverted_dates(self) -> None:
        # Constructing the model directly bypasses the model-level invariant,
        # but we can simulate the rule's view by building a stub object.
        class _Stub:
            valid_from = datetime(2030, 1, 1, tzinfo=timezone.utc)
            valid_until = datetime(2025, 1, 1, tzinfo=timezone.utc)

        rule = ValidityDateRule()
        violations = rule.check(_Stub())
        assert any("validFrom" in msg for _, msg in violations)

    def test_hazardous_material_rule_fires_when_no_safety_info(self) -> None:
        # Build a stand-alone Material so we don't trip the model-level
        # invariant — the rule walks the dotted path via getattr.
        class _Mat:
            name = "Lithium"
            hazardous = True
            material_safety_information = None

        class _Product:
            material_provenance = [_Mat()]

        class _DPP:
            credential_subject = _Product()

        rule = HazardousMaterialRule()
        violations = rule.check(_DPP())
        assert violations and "Lithium" in violations[0][1]

    def test_conformity_claim_rule_warns_when_no_claims(self) -> None:
        class _Product:
            performance_claim = []

        class _DPP:
            credential_subject = _Product()

        rule = ConformityClaimRule()
        violations = rule.check(_DPP())
        assert violations and "performance" in violations[0][1].lower()
