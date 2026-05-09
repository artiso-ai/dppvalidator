"""Per-rule unit tests for the CIRPASS v1.3.0 rule tree.

Phase 4 of [docs/plans/CIRPASS_2_MIGRATION.md]. Each rule has a
positive (rule does not fire on a clean fixture) and negative
(rule fires with a stable error code + JSON path) test. The
fixtures are constructed via :func:`_clean_passport` so each test
exercises *exactly* the field its rule covers — that keeps the
attribution stable when an unrelated change to a sibling rule
shifts the failing-fixture's blast radius.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from dppvalidator.models.cirpass.v1_3 import (
    Actor,
    ActorRole,
    ActorRoleAssignment,
    ClassificationCode,
    Composition,
    Concentration,
    ConnectorRelation,
    EffectivePeriod,
    Facility,
    HazardClassification,
    Identifier,
    ImpactCategoryReference,
    ImpactResult,
    IssuedAt,
    LifeCycleAssessment,
    LocalisedText,
    Material,
    Product,
    ReferencePassport,
    SubstanceOfConcern,
)
from dppvalidator.validators.rules.cirpass_v1_3 import (
    ALL_ACTOR_RULES,
    ALL_BASE_RULES,
    ALL_CONNECTOR_RULES,
    ALL_LCA_RULES,
    ALL_RULES_CIRPASS_V1_3,
    ALL_SUBSTANCE_RULES,
    ActorIdentificationRule,
    ActorRoleAssignmentTemporalRule,
    ActorRoleClosureRule,
    BCP47LanguageTagRule,
    ConnectorRelationTemporalRule,
    ConnectorRelationTypeClosureRule,
    ConnectorSubjectObjectDistinctRule,
    DPPIdentifierUniqueRule,
    EffectivePeriodMonotonicRule,
    HazardCategoryClosureRule,
    ImpactCategoryClosureRule,
    IssuedAtBeforeEffectiveRule,
    LCAResultsPresentRule,
    LCAUnitNormalisationRule,
    LifeCycleStageClosureRule,
    MandatoryEconomicOperatorRule,
    MassFractionConcentrationBoundRule,
    PreviousDPPDistinctRule,
    ProductIdentifierShapeRule,
    ReferencePeriodMonotonicRule,
    SubstanceIdentificationRule,
)
from dppvalidator.vocabularies.eudpp_actors import EUDPPRoleClass
from dppvalidator.vocabularies.eudpp_lca import LCIAImpactCategory
from dppvalidator.vocabularies.eudpp_substances import HazardCategory, LifeCycleStage

# =============================================================================
# Shared fixtures
# =============================================================================


def _clean_passport(**overrides: object) -> ReferencePassport:
    """Construct a minimal-but-valid :class:`ReferencePassport`.

    Per-rule tests pass overrides for the fields they exercise.
    Defaults pass every rule in :data:`ALL_RULES_CIRPASS_V1_3`. The
    parent is constructed with :meth:`model_construct` so tests can
    inject invariant-violating sub-objects (built with
    :meth:`model_construct` on the child) without Pydantic
    re-running the inner validators.
    """
    dpp_identifier = Identifier(
        value="https://example.com/dpp/CR-CLEAN",
        scheme="https://example.com/dpp-register/",
    )
    product = Product(
        productIdentifier=Identifier(
            value="01234567890128",
            scheme="https://gs1.org/voc/",
        ),
        productName=[LocalisedText(value="Clean Product", language="en")],
    )
    issued_at = IssuedAt(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))

    # Map alias -> snake_case for ``model_construct`` (which uses the
    # canonical field name, not the wire alias).
    _ALIAS_TO_FIELD = {
        "dppIdentifier": "dpp_identifier",
        "issuedAt": "issued_at",
        "effectivePeriod": "effective_period",
        "relatedActors": "related_actors",
        "actorRoleAssignments": "actor_role_assignments",
        "substancesOfConcern": "substances_of_concern",
        "connectorRelations": "connector_relations",
        "previousDpp": "previous_dpp",
    }

    fields: dict[str, object] = {
        "dpp_identifier": dpp_identifier,
        "product": product,
        "issued_at": issued_at,
        "effective_period": None,
        "related_actors": None,
        "actor_role_assignments": None,
        "composition": None,
        "substances_of_concern": None,
        "lca": None,
        "connector_relations": None,
        "previous_dpp": None,
    }
    for key, value in overrides.items():
        canonical = _ALIAS_TO_FIELD.get(key, key)
        fields[canonical] = value

    return ReferencePassport.model_construct(**fields)


# =============================================================================
# Dispatch sanity (Phase 4.1)
# =============================================================================


class TestRuleSetDispatch:
    """The rule sets are aggregated correctly from per-module imports."""

    def test_all_rules_set_covers_every_module(self) -> None:
        assert len(ALL_BASE_RULES) == 6
        assert len(ALL_SUBSTANCE_RULES) == 4
        assert len(ALL_LCA_RULES) == 4
        assert len(ALL_ACTOR_RULES) == 4
        assert len(ALL_CONNECTOR_RULES) == 3
        # Top-level set is the concatenation of the module sets.
        expected_total = (
            len(ALL_BASE_RULES)
            + len(ALL_SUBSTANCE_RULES)
            + len(ALL_LCA_RULES)
            + len(ALL_ACTOR_RULES)
            + len(ALL_CONNECTOR_RULES)
        )
        assert len(ALL_RULES_CIRPASS_V1_3) == expected_total

    def test_rule_id_codes_use_correct_prefixes(self) -> None:
        """Each module's rules use its reserved code prefix."""
        for r in ALL_BASE_RULES:
            assert r.rule_id.startswith("CR")  # type: ignore[attr-defined]
        for r in ALL_SUBSTANCE_RULES:
            assert r.rule_id.startswith("SUB")  # type: ignore[attr-defined]
        for r in ALL_LCA_RULES:
            assert r.rule_id.startswith("LCS")  # type: ignore[attr-defined]
        for r in ALL_ACTOR_RULES:
            assert r.rule_id.startswith("ACT")  # type: ignore[attr-defined]
        for r in ALL_CONNECTOR_RULES:
            assert r.rule_id.startswith("REL")  # type: ignore[attr-defined]

    def test_rule_ids_are_unique(self) -> None:
        ids = [r.rule_id for r in ALL_RULES_CIRPASS_V1_3]  # type: ignore[attr-defined]
        assert len(ids) == len(set(ids)), f"Duplicate rule IDs: {ids}"


# =============================================================================
# CR — base structural rules
# =============================================================================


class TestDPPIdentifierUniqueRule:
    rule = DPPIdentifierUniqueRule()

    def test_clean_payload_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_dpp_identical_to_product_identifier(self) -> None:
        passport = _clean_passport(
            dppIdentifier=Identifier(
                value="01234567890128",  # same as product.productIdentifier.value
                scheme="https://example.com/dpp-register/",
            )
        )
        violations = self.rule.check(passport)
        assert len(violations) == 1
        assert violations[0][0] == "$.dppIdentifier.value"
        assert "identical" in violations[0][1].lower()


class TestProductIdentifierShapeRule:
    rule = ProductIdentifierShapeRule()

    def test_clean_payload_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_invalid_scheme_uri(self) -> None:
        # Use model_construct to bypass field-validator and exercise the rule.
        passport = _clean_passport()
        passport.product.product_identifier = Identifier.model_construct(
            value="01234567890128",
            scheme="not-a-uri",
        )
        violations = self.rule.check(passport)
        assert len(violations) == 1
        assert violations[0][0] == "$.product.productIdentifier.scheme"


class TestEffectivePeriodMonotonicRule:
    rule = EffectivePeriodMonotonicRule()

    def test_no_period_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_well_ordered_period_no_violation(self) -> None:
        period = EffectivePeriod(
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2031, 12, 31, tzinfo=timezone.utc),
        )
        assert self.rule.check(_clean_passport(effectivePeriod=period)) == []

    def test_inverted_period_fires(self) -> None:
        period = EffectivePeriod.model_construct(
            start=datetime(2031, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        violations = self.rule.check(_clean_passport(effectivePeriod=period))
        assert len(violations) == 1
        assert violations[0][0] == "$.effectivePeriod"


class TestIssuedAtBeforeEffectiveRule:
    rule = IssuedAtBeforeEffectiveRule()

    def test_no_period_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_issued_inside_window(self) -> None:
        period = EffectivePeriod(
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2031, 12, 31, tzinfo=timezone.utc),
        )
        assert self.rule.check(_clean_passport(effectivePeriod=period)) == []

    def test_issued_after_window_end_fires(self) -> None:
        period = EffectivePeriod(
            start=datetime(2020, 1, 1, tzinfo=timezone.utc),
            end=datetime(2024, 12, 31, tzinfo=timezone.utc),
        )
        passport = _clean_passport(
            issuedAt=IssuedAt(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc)),
            effectivePeriod=period,
        )
        violations = self.rule.check(passport)
        assert len(violations) == 1
        assert violations[0][0] == "$.issuedAt.timestamp"


class TestBCP47LanguageTagRule:
    rule = BCP47LanguageTagRule()

    def test_clean_payload_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_malformed_tag_fires(self) -> None:
        passport = _clean_passport()
        passport.product.product_name[0] = LocalisedText.model_construct(
            value="Bad", language="ENGLISH-NOT-A-TAG"
        )
        violations = self.rule.check(passport)
        assert len(violations) == 1
        assert violations[0][0] == "$.product.productName[0].language"


class TestPreviousDPPDistinctRule:
    rule = PreviousDPPDistinctRule()

    def test_clean_payload_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_self_referential_fires(self) -> None:
        passport = _clean_passport(previousDpp="https://example.com/dpp/CR-CLEAN")
        violations = self.rule.check(passport)
        assert len(violations) == 1
        assert violations[0][0] == "$.previousDpp"


# =============================================================================
# SUB — substance rules
# =============================================================================


def _soc_concentration() -> Concentration:
    return Concentration(value=Decimal("0.0008"), unit="mass_fraction")


class TestSubstanceIdentificationRule:
    rule = SubstanceIdentificationRule()

    def test_no_substances_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_identified_substance(self) -> None:
        soc = SubstanceOfConcern(
            nameIUPAC="Bisphenol A",
            concentrations=[_soc_concentration()],
        )
        assert self.rule.check(_clean_passport(substancesOfConcern=[soc])) == []

    def test_unidentified_fires(self) -> None:
        soc = SubstanceOfConcern.model_construct(concentrations=[_soc_concentration()])
        violations = self.rule.check(_clean_passport(substancesOfConcern=[soc]))
        assert len(violations) == 1
        assert violations[0][0] == "$.substancesOfConcern[0]"


class TestHazardCategoryClosureRule:
    rule = HazardCategoryClosureRule()

    def test_clean_payload_no_violation(self) -> None:
        soc = SubstanceOfConcern(
            nameIUPAC="X",
            concentrations=[_soc_concentration()],
            hazards=[HazardClassification(category=HazardCategory.SVHC)],
        )
        assert self.rule.check(_clean_passport(substancesOfConcern=[soc])) == []

    def test_off_enum_category_fires(self) -> None:
        bad = HazardClassification.model_construct(category="not_a_real_category")
        soc = SubstanceOfConcern(
            nameIUPAC="X",
            concentrations=[_soc_concentration()],
            hazards=[bad],
        )
        violations = self.rule.check(_clean_passport(substancesOfConcern=[soc]))
        assert len(violations) == 1
        assert "category" in violations[0][0]


class TestMassFractionConcentrationBoundRule:
    rule = MassFractionConcentrationBoundRule()

    def test_well_bounded_no_violation(self) -> None:
        soc = SubstanceOfConcern(
            nameIUPAC="X",
            concentrations=[Concentration(value=Decimal("0.5"), unit="mass_fraction")],
        )
        assert self.rule.check(_clean_passport(substancesOfConcern=[soc])) == []

    def test_non_mass_fraction_unit_skipped(self) -> None:
        soc = SubstanceOfConcern(
            nameIUPAC="X",
            concentrations=[Concentration(value=Decimal("5000"), unit="mg_per_kg")],
        )
        assert self.rule.check(_clean_passport(substancesOfConcern=[soc])) == []

    def test_overbound_mass_fraction_fires(self) -> None:
        soc = SubstanceOfConcern(
            nameIUPAC="X",
            concentrations=[
                Concentration.model_construct(value=Decimal("1.5"), unit="mass_fraction")
            ],
        )
        violations = self.rule.check(_clean_passport(substancesOfConcern=[soc]))
        assert len(violations) == 1


class TestLifeCycleStageClosureRule:
    rule = LifeCycleStageClosureRule()

    def test_known_stage_no_violation(self) -> None:
        soc = SubstanceOfConcern(
            nameIUPAC="X",
            concentrations=[
                Concentration(
                    value=Decimal("0.001"),
                    unit="mass_fraction",
                    lifecycleStage=LifeCycleStage.IN_PRODUCT,
                )
            ],
        )
        assert self.rule.check(_clean_passport(substancesOfConcern=[soc])) == []

    def test_unknown_stage_fires(self) -> None:
        c = Concentration.model_construct(
            value=Decimal("0.001"),
            unit="mass_fraction",
            lifecycle_stage="bogus_stage",
        )
        soc = SubstanceOfConcern(nameIUPAC="X", concentrations=[c])
        violations = self.rule.check(_clean_passport(substancesOfConcern=[soc]))
        assert len(violations) == 1


# =============================================================================
# LCS — LCA rules
# =============================================================================


def _impact(category: str = "eudpp:climateChange", value: float = 12.34) -> ImpactResult:
    return ImpactResult(
        impactCategory=ImpactCategoryReference(category=category),
        value=Decimal(str(value)),
        unit="kg_CO2_eq",
    )


class TestLCAResultsPresentRule:
    rule = LCAResultsPresentRule()

    def test_no_lca_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_results_present_no_violation(self) -> None:
        lca = LifeCycleAssessment(results=[_impact()])
        assert self.rule.check(_clean_passport(lca=lca)) == []

    def test_empty_results_fires(self) -> None:
        lca = LifeCycleAssessment.model_construct(results=[])
        violations = self.rule.check(_clean_passport(lca=lca))
        assert len(violations) == 1
        assert violations[0][0] == "$.lca.results"


class TestImpactCategoryClosureRule:
    rule = ImpactCategoryClosureRule()

    def test_canonical_eudpp_iri_no_violation(self) -> None:
        lca = LifeCycleAssessment(results=[_impact(LCIAImpactCategory.CLIMATE_CHANGE.value)])
        assert self.rule.check(_clean_passport(lca=lca)) == []

    def test_legacy_lca_iri_tolerated(self) -> None:
        lca = LifeCycleAssessment(results=[_impact("lca:Climate_change_total")])
        assert self.rule.check(_clean_passport(lca=lca)) == []

    def test_off_canonical_iri_fires(self) -> None:
        lca = LifeCycleAssessment(results=[_impact("eudpp:notARealCategory")])
        violations = self.rule.check(_clean_passport(lca=lca))
        assert len(violations) == 1


class TestLCAUnitNormalisationRule:
    rule = LCAUnitNormalisationRule()

    def test_canonical_unit_no_violation(self) -> None:
        lca = LifeCycleAssessment(results=[_impact()])
        assert self.rule.check(_clean_passport(lca=lca)) == []

    def test_off_canonical_unit_fires(self) -> None:
        result = ImpactResult(
            impactCategory=ImpactCategoryReference(category="eudpp:climateChange"),
            value=Decimal("12.34"),
            unit="not-a-canonical-unit",
        )
        lca = LifeCycleAssessment(results=[result])
        violations = self.rule.check(_clean_passport(lca=lca))
        assert len(violations) == 1


class TestReferencePeriodMonotonicRule:
    rule = ReferencePeriodMonotonicRule()

    def test_no_reference_period_no_violation(self) -> None:
        lca = LifeCycleAssessment(results=[_impact()])
        assert self.rule.check(_clean_passport(lca=lca)) == []

    def test_well_ordered_reference_period(self) -> None:
        period = EffectivePeriod(
            start=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )
        lca = LifeCycleAssessment(results=[_impact()], referencePeriod=period)
        assert self.rule.check(_clean_passport(lca=lca)) == []

    def test_inverted_reference_period_fires(self) -> None:
        period = EffectivePeriod.model_construct(
            start=datetime(2025, 12, 31, tzinfo=timezone.utc),
            end=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        lca = LifeCycleAssessment.model_construct(results=[_impact()], reference_period=period)
        violations = self.rule.check(_clean_passport(lca=lca))
        assert len(violations) == 1


# =============================================================================
# ACT — actor rules
# =============================================================================


def _actor(
    value: str = "529900T8BM49AURSDO55", scheme: str = "https://www.gleif.org/lei/"
) -> Actor:
    return Actor(
        actorIdentifier=Identifier(value=value, scheme=scheme),
        actorName=[LocalisedText(value="Example Actor", language="en")],
    )


class TestActorIdentificationRule:
    rule = ActorIdentificationRule()

    def test_clean_payload_no_violation(self) -> None:
        passport = _clean_passport(
            relatedActors=[ActorRole(actor=_actor(), role=EUDPPRoleClass.MANUFACTURER.value)]
        )
        assert self.rule.check(passport) == []

    def test_empty_value_fires(self) -> None:
        bad_actor = Actor.model_construct(
            actor_identifier=Identifier.model_construct(value="", scheme="https://example.com/"),
            actor_name=[LocalisedText(value="X", language="en")],
        )
        passport = _clean_passport(
            relatedActors=[ActorRole(actor=bad_actor, role=EUDPPRoleClass.MANUFACTURER.value)]
        )
        violations = self.rule.check(passport)
        assert len(violations) == 1
        assert "actorIdentifier.value" in violations[0][0]

    def test_non_uri_scheme_fires(self) -> None:
        bad_actor = Actor.model_construct(
            actor_identifier=Identifier.model_construct(
                value="LEI-001",
                scheme="GLEIF",
            ),
            actor_name=[LocalisedText(value="X", language="en")],
        )
        passport = _clean_passport(
            relatedActors=[ActorRole(actor=bad_actor, role=EUDPPRoleClass.MANUFACTURER.value)]
        )
        violations = self.rule.check(passport)
        assert len(violations) == 1
        assert "actorIdentifier.scheme" in violations[0][0]


class TestActorRoleClosureRule:
    rule = ActorRoleClosureRule()

    def test_known_role_no_violation(self) -> None:
        passport = _clean_passport(
            relatedActors=[ActorRole(actor=_actor(), role=EUDPPRoleClass.MANUFACTURER.value)]
        )
        assert self.rule.check(passport) == []

    def test_off_enum_role_fires(self) -> None:
        passport = _clean_passport(
            relatedActors=[ActorRole(actor=_actor(), role="eudpp:NotARealRole")]
        )
        violations = self.rule.check(passport)
        assert len(violations) == 1


class TestMandatoryEconomicOperatorRule:
    rule = MandatoryEconomicOperatorRule()

    def test_no_actors_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_economic_operator_present_no_violation(self) -> None:
        passport = _clean_passport(
            relatedActors=[ActorRole(actor=_actor(), role=EUDPPRoleClass.MANUFACTURER.value)]
        )
        assert self.rule.check(passport) == []

    def test_only_authority_role_fires(self) -> None:
        passport = _clean_passport(
            relatedActors=[ActorRole(actor=_actor(), role=EUDPPRoleClass.AUTHORITY.value)]
        )
        violations = self.rule.check(passport)
        assert len(violations) == 1


class TestActorRoleAssignmentTemporalRule:
    rule = ActorRoleAssignmentTemporalRule()

    def test_no_assignments_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_well_ordered_assignment(self) -> None:
        ara = ActorRoleAssignment(
            actor=_actor(),
            role=EUDPPRoleClass.MANUFACTURER.value,
            validFrom="2026-01-01T00:00:00+00:00",
            validTo="2031-01-01T00:00:00+00:00",
        )
        assert self.rule.check(_clean_passport(actorRoleAssignments=[ara])) == []

    def test_inverted_assignment_fires(self) -> None:
        ara = ActorRoleAssignment(
            actor=_actor(),
            role=EUDPPRoleClass.MANUFACTURER.value,
            validFrom="2031-01-01T00:00:00+00:00",
            validTo="2026-01-01T00:00:00+00:00",
        )
        violations = self.rule.check(_clean_passport(actorRoleAssignments=[ara]))
        assert len(violations) == 1


# =============================================================================
# REL — connector rules
# =============================================================================


class TestConnectorRelationTypeClosureRule:
    rule = ConnectorRelationTypeClosureRule()

    def test_no_relations_no_violation(self) -> None:
        assert self.rule.check(_clean_passport()) == []

    def test_known_predicate_no_violation(self) -> None:
        rel = ConnectorRelation(
            relation="eudpp:hasManufacturer",
            subject="https://example.com/dpp/CR-CLEAN",
            object="https://example.com/actor/abc",
        )
        assert self.rule.check(_clean_passport(connectorRelations=[rel])) == []

    def test_off_enum_predicate_fires(self) -> None:
        rel = ConnectorRelation(
            relation="eudpp:notARealPredicate",
            subject="https://example.com/dpp/CR-CLEAN",
            object="https://example.com/actor/abc",
        )
        violations = self.rule.check(_clean_passport(connectorRelations=[rel]))
        assert len(violations) == 1


class TestConnectorSubjectObjectDistinctRule:
    rule = ConnectorSubjectObjectDistinctRule()

    def test_distinct_endpoints_no_violation(self) -> None:
        rel = ConnectorRelation(
            relation="eudpp:hasManufacturer",
            subject="https://example.com/dpp/A",
            object="https://example.com/actor/B",
        )
        assert self.rule.check(_clean_passport(connectorRelations=[rel])) == []

    def test_self_referential_fires(self) -> None:
        rel = ConnectorRelation(
            relation="eudpp:hasManufacturer",
            subject="https://example.com/X",
            object="https://example.com/X",
        )
        violations = self.rule.check(_clean_passport(connectorRelations=[rel]))
        assert len(violations) == 1


class TestConnectorRelationTemporalRule:
    rule = ConnectorRelationTemporalRule()

    def test_well_ordered_no_violation(self) -> None:
        rel = ConnectorRelation(
            relation="eudpp:hasManufacturer",
            subject="https://example.com/A",
            object="https://example.com/B",
            validFrom="2026-01-01T00:00:00+00:00",
            validTo="2031-01-01T00:00:00+00:00",
        )
        assert self.rule.check(_clean_passport(connectorRelations=[rel])) == []

    def test_inverted_fires(self) -> None:
        rel = ConnectorRelation(
            relation="eudpp:hasManufacturer",
            subject="https://example.com/A",
            object="https://example.com/B",
            validFrom="2031-01-01T00:00:00+00:00",
            validTo="2026-01-01T00:00:00+00:00",
        )
        violations = self.rule.check(_clean_passport(connectorRelations=[rel]))
        assert len(violations) == 1


# =============================================================================
# Coverage of helpers
# =============================================================================


def test_facility_module_present() -> None:
    """Smoke test the Facility model still exposes expected attributes."""
    f = Facility(
        facilityIdentifier=Identifier(value="F-001", scheme="https://example.com/permits/"),
        facilityName=[LocalisedText(value="Plant A", language="en")],
    )
    assert f.facility_name[0].value == "Plant A"


def test_classification_code_smoke() -> None:
    cc = ClassificationCode(code="61102090", scheme="https://www.wcoomd.org/")
    assert cc.code == "61102090"


def test_composition_smoke() -> None:
    c = Composition(
        materials=[
            Material(
                materialName=[LocalisedText(value="Cotton", language="en")],
                materialType="CO",
            )
        ]
    )
    assert len(c.materials) == 1


@pytest.mark.parametrize(
    "rule_cls,attribute",
    [
        (DPPIdentifierUniqueRule, "rule_id"),
        (HazardCategoryClosureRule, "severity"),
        (LCAUnitNormalisationRule, "suggestion"),
        (ActorRoleClosureRule, "docs_url"),
        (ConnectorSubjectObjectDistinctRule, "description"),
    ],
)
def test_each_rule_carries_attribution(rule_cls: type, attribute: str) -> None:
    """Every rule must expose the standard attribution attributes."""
    instance = rule_cls()
    value = getattr(instance, attribute, None)
    assert value, f"{rule_cls.__name__} missing {attribute!r}"


# =============================================================================
# Extra coverage cases — exercise paths the per-rule happy-path tests
# above don't otherwise cover.
# =============================================================================


def test_actor_role_closure_rule_fires_on_assignments_too() -> None:
    """ACT002 walks ``actorRoleAssignments`` in addition to ``relatedActors``."""
    rule = ActorRoleClosureRule()
    bad_role = "eudpp:NotARealRole"
    ara = ActorRoleAssignment(actor=_actor(), role=bad_role)
    passport = _clean_passport(actorRoleAssignments=[ara])
    violations = rule.check(passport)
    assert len(violations) == 1
    assert "$.actorRoleAssignments[0].role" in violations[0][0]


def test_actor_role_closure_rule_clean_assignments() -> None:
    """ACT002 ignores well-formed assignments."""
    rule = ActorRoleClosureRule()
    ara = ActorRoleAssignment(actor=_actor(), role=EUDPPRoleClass.MANUFACTURER.value)
    assert rule.check(_clean_passport(actorRoleAssignments=[ara])) == []


def test_act004_skips_assignment_with_missing_endpoint() -> None:
    """ACT004 is no-op when one of validFrom/validTo is missing."""
    rule = ActorRoleAssignmentTemporalRule()
    ara = ActorRoleAssignment(
        actor=_actor(),
        role=EUDPPRoleClass.MANUFACTURER.value,
        validFrom="2026-01-01T00:00:00+00:00",
        # validTo intentionally omitted
    )
    assert rule.check(_clean_passport(actorRoleAssignments=[ara])) == []


def test_act004_skips_unparseable_timestamp() -> None:
    """ACT004 silently skips when a timestamp can't be parsed.

    Model-layer validation is responsible for catching malformed
    ISO 8601; the semantic rule uses :func:`_parse_iso_datetime`
    defensively and returns no violation when parsing fails.
    """
    rule = ActorRoleAssignmentTemporalRule()
    ara = ActorRoleAssignment.model_construct(
        actor=_actor(),
        role=EUDPPRoleClass.MANUFACTURER.value,
        valid_from="not-a-timestamp",
        valid_to="2031-01-01T00:00:00+00:00",
    )
    assert rule.check(_clean_passport(actorRoleAssignments=[ara])) == []


def test_rel003_skips_relation_with_missing_endpoint() -> None:
    """REL003 is no-op when one of validFrom/validTo is missing."""
    rule = ConnectorRelationTemporalRule()
    rel = ConnectorRelation(
        relation="eudpp:hasManufacturer",
        subject="https://example.com/A",
        object="https://example.com/B",
        validFrom="2026-01-01T00:00:00+00:00",
    )
    assert rule.check(_clean_passport(connectorRelations=[rel])) == []


def test_rel003_skips_unparseable_timestamp() -> None:
    """REL003 silently skips on parse failure (model layer's job)."""
    rule = ConnectorRelationTemporalRule()
    rel = ConnectorRelation.model_construct(
        relation="eudpp:hasManufacturer",
        subject="https://example.com/A",
        object="https://example.com/B",
        valid_from="not-a-timestamp",
        valid_to="2031-01-01T00:00:00+00:00",
    )
    assert rule.check(_clean_passport(connectorRelations=[rel])) == []


def test_bcp47_walks_every_attached_localised_text() -> None:
    """CR005 walks the entire reachable LocalisedText tree.

    Combine an actor name + commodity-code label + LCA impact
    name in a single passport, then inject one bad tag deep in the
    tree to confirm the rule still finds it.
    """
    rule = BCP47LanguageTagRule()
    actor = _actor()
    actor.actor_name.append(LocalisedText.model_construct(value="X", language="bad-tag-99"))
    cc = ClassificationCode(
        code="61102090",
        scheme="https://www.wcoomd.org/",
        name=[LocalisedText(value="T-shirt", language="en")],
    )
    passport = _clean_passport(
        relatedActors=[ActorRole(actor=actor, role=EUDPPRoleClass.MANUFACTURER.value)],
    )
    passport.product.commodity_code = [cc]
    violations = rule.check(passport)
    assert len(violations) == 1
    assert "$.relatedActors[0].actor.actorName[1].language" in violations[0][0]


def test_walk_localised_text_includes_lca_impact_names() -> None:
    """Stress :func:`_walk_localised_text`: every nested label is reached."""
    rule = BCP47LanguageTagRule()
    impact = ImpactResult(
        impactCategory=ImpactCategoryReference(
            category="eudpp:climateChange",
            name=[
                LocalisedText(value="OK", language="en"),
                LocalisedText.model_construct(value="Bad", language="not-a-tag"),
            ],
        ),
        value=Decimal("1"),
        unit="kg_CO2_eq",
    )
    lca = LifeCycleAssessment(results=[impact])
    violations = rule.check(_clean_passport(lca=lca))
    assert len(violations) == 1
    assert "$.lca.results[0].impactCategory.name[1].language" in violations[0][0]


def test_walk_localised_text_includes_substance_hazard_statements() -> None:
    rule = BCP47LanguageTagRule()
    hazard = HazardClassification(
        category=HazardCategory.SVHC,
        statement=[LocalisedText.model_construct(value="X", language="bad-tag")],
    )
    soc = SubstanceOfConcern(
        nameIUPAC="X",
        concentrations=[_soc_concentration()],
        hazards=[hazard],
    )
    violations = rule.check(_clean_passport(substancesOfConcern=[soc]))
    assert len(violations) == 1
    assert "$.substancesOfConcern[0].hazards[0].statement[0].language" in violations[0][0]


def test_walk_localised_text_includes_composition_material_names() -> None:
    rule = BCP47LanguageTagRule()
    material = Material.model_construct(
        material_name=[LocalisedText.model_construct(value="X", language="bad-tag")],
    )
    composition = Composition.model_construct(materials=[material])
    violations = rule.check(_clean_passport(composition=composition))
    assert len(violations) == 1
    assert "$.composition.materials[0].materialName[0].language" in violations[0][0]


def test_walk_actors_includes_assignment_targets() -> None:
    """Coverage for the actor walker's assignment branch."""
    rule = ActorIdentificationRule()
    bad_actor = Actor.model_construct(
        actor_identifier=Identifier.model_construct(value="", scheme="https://example.com/"),
        actor_name=[LocalisedText(value="X", language="en")],
    )
    ara = ActorRoleAssignment(actor=bad_actor, role=EUDPPRoleClass.MANUFACTURER.value)
    passport = _clean_passport(actorRoleAssignments=[ara])
    violations = rule.check(passport)
    assert len(violations) == 1
    assert "$.actorRoleAssignments[0].actor.actorIdentifier.value" in violations[0][0]


def test_mandatory_economic_operator_rule_recognises_assignment_role() -> None:
    """ACT003 reads roles from both ``relatedActors`` and ``actorRoleAssignments``."""
    rule = MandatoryEconomicOperatorRule()
    ara = ActorRoleAssignment(actor=_actor(), role=EUDPPRoleClass.MANUFACTURER.value)
    passport = _clean_passport(actorRoleAssignments=[ara])
    assert rule.check(passport) == []
