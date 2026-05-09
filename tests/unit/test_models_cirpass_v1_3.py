"""Phase 3 task — per-class happy path + edge cases for CIRPASS v1.3.0 models.

Coverage targets per the migration plan's Phase 3 exit criteria:

- Coverage on `models/cirpass/v1_3/` ≥ 95%.
- Round-trip parse/dump of every Phase 0 fixture is bit-stable
  modulo `json.dumps(sort_keys=True)`.
- All 3 valid fixtures parse cleanly; all 6 invalid fixtures fail
  with a descriptive error.

Each test name surfaces the exact invariant it pins so a future
regression points back here without spelunking.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from dppvalidator.models.cirpass.v1_3 import (
    Actor,
    ActorRole,
    ActorRoleAssignment,
    ClassificationCode,
    Composition,
    Concentration,
    ConnectorRelation,
    EffectivePeriod,
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
    RelationType,
    SubstanceOfConcern,
    is_valid_bcp47,
    looks_like_gtin,
)
from dppvalidator.vocabularies.eudpp_actors import EUDPPRoleClass
from dppvalidator.vocabularies.eudpp_lca import LCIAImpactCategory
from dppvalidator.vocabularies.eudpp_substances import HazardCategory, LifeCycleStage

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VALID_DIR = _REPO_ROOT / "tests" / "fixtures" / "valid" / "cirpass-1.3.0"
_INVALID_DIR = _REPO_ROOT / "tests" / "fixtures" / "invalid" / "cirpass-1.3.0"


# =============================================================================
# i18n: LocalisedText
# =============================================================================


class TestLocalisedText:
    def test_minimal_en(self) -> None:
        t = LocalisedText(value="Hello", language="en")
        assert t.value == "Hello"
        assert t.language == "en"

    def test_strips_whitespace(self) -> None:
        # Base model has str_strip_whitespace=True
        t = LocalisedText(value="  Hello  ", language="en")
        assert t.value == "Hello"

    @pytest.mark.parametrize(
        "tag",
        ["en", "de", "fr", "zh-Hant", "zh-Hans", "en-GB", "en-US", "en-029"],
    )
    def test_accepts_recognised_bcp47(self, tag: str) -> None:
        LocalisedText(value="x", language=tag)
        assert is_valid_bcp47(tag)

    @pytest.mark.parametrize(
        "tag",
        ["ENGLISH", "en_US", "english-USA", "x", "1en", ""],
    )
    def test_rejects_malformed_bcp47(self, tag: str) -> None:
        with pytest.raises(ValidationError):
            LocalisedText(value="x", language=tag)
        assert not is_valid_bcp47(tag)

    def test_empty_value_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LocalisedText(value="", language="en")


# =============================================================================
# Temporal: EffectivePeriod, IssuedAt
# =============================================================================


class TestEffectivePeriod:
    def test_start_only(self) -> None:
        ep = EffectivePeriod(start=datetime(2026, 1, 1, tzinfo=timezone.utc))
        assert ep.end is None

    def test_start_before_end(self) -> None:
        ep = EffectivePeriod(
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2031, 1, 1, tzinfo=timezone.utc),
        )
        assert ep.start < ep.end  # type: ignore[operator]

    def test_inverted_period_rejected(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            EffectivePeriod(
                start=datetime(2031, 1, 1, tzinfo=timezone.utc),
                end=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )


class TestIssuedAt:
    def test_utc_accepted(self) -> None:
        IssuedAt(timestamp=datetime(2026, 5, 8, tzinfo=timezone.utc))

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError, match="timezone-aware"):
            IssuedAt(timestamp=datetime(2026, 5, 8))


# =============================================================================
# Product / Identifier / ClassificationCode
# =============================================================================


class TestIdentifier:
    def test_minimal(self) -> None:
        i = Identifier(value="01234567890128", scheme="https://gs1.org/voc/")
        assert i.value == "01234567890128"

    def test_scheme_must_be_uri(self) -> None:
        with pytest.raises(ValidationError, match="http"):
            Identifier(value="x", scheme="GTIN")

    def test_alias_scheme_name(self) -> None:
        i = Identifier(value="x", scheme="https://example.com/", schemeName="GS1")
        assert i.scheme_name == "GS1"


class TestProduct:
    def test_round_trip_minimal(self) -> None:
        p = Product(
            productIdentifier=Identifier(value="01234567890128", scheme="https://gs1.org/voc/"),
            productName=[LocalisedText(value="Test", language="en")],
        )
        # by_alias keeps the JSON-LD-flavoured field names
        dumped = p.model_dump(mode="json", by_alias=True, exclude_none=True)
        restored = Product.model_validate(dumped)
        assert restored == p

    def test_empty_product_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Product(
                productIdentifier=Identifier(value="x", scheme="https://example.com/"),
                productName=[],
            )

    def test_classification_code_with_localised_name(self) -> None:
        c = ClassificationCode(
            code="61091000",
            scheme="https://www.wcoomd.org/...",
            name=[LocalisedText(value="T-shirts", language="en")],
        )
        assert c.code == "61091000"


def test_looks_like_gtin_helper() -> None:
    assert looks_like_gtin("01234567890128")  # GTIN-14
    assert looks_like_gtin("12345678")  # GTIN-8
    assert not looks_like_gtin("abc")
    assert not looks_like_gtin("123")


# =============================================================================
# Actor / ActorRole / ActorRoleAssignment
# =============================================================================


class TestActor:
    def test_role_enum_resolves(self) -> None:
        actor = Actor(
            actorIdentifier=Identifier(value="529900", scheme="https://gleif.org/"),
            actorName=[LocalisedText(value="Foo Ltd", language="en")],
        )
        role = ActorRole(actor=actor, role=EUDPPRoleClass.MANUFACTURER.value)
        assert role.role_enum is EUDPPRoleClass.MANUFACTURER

    def test_role_enum_returns_none_for_unknown_role(self) -> None:
        actor = Actor(
            actorIdentifier=Identifier(value="x", scheme="https://example.com/"),
            actorName=[LocalisedText(value="X", language="en")],
        )
        role = ActorRole(actor=actor, role="eudpp:DownstreamCustomRole")
        assert role.role_enum is None

    def test_role_assignment_with_temporal_bounds(self) -> None:
        actor = Actor(
            actorIdentifier=Identifier(value="x", scheme="https://example.com/"),
            actorName=[LocalisedText(value="X", language="en")],
        )
        a = ActorRoleAssignment(
            actor=actor,
            role=EUDPPRoleClass.RECYCLER.value,
            validFrom="2026-01-01T00:00:00Z",
            validTo="2031-12-31T23:59:59Z",
        )
        assert a.valid_from == "2026-01-01T00:00:00Z"


# =============================================================================
# Material / Composition
# =============================================================================


class TestMaterial:
    def test_iso_2076_ok(self) -> None:
        Material(
            materialName=[LocalisedText(value="Cotton", language="en")],
            materialType="CO",
        )

    def test_bad_iso_2076_rejected(self) -> None:
        with pytest.raises(ValidationError, match="ISO"):
            Material(
                materialName=[LocalisedText(value="X", language="en")],
                materialType="cotton",
            )

    def test_bad_country_code_rejected(self) -> None:
        with pytest.raises(ValidationError, match="ISO"):
            Material(
                materialName=[LocalisedText(value="X", language="en")],
                originCountry="Germany",
            )

    def test_mass_fraction_bounds(self) -> None:
        Material(
            materialName=[LocalisedText(value="X", language="en")],
            massFraction=Decimal("0.5"),
        )
        with pytest.raises(ValidationError):
            Material(
                materialName=[LocalisedText(value="X", language="en")],
                massFraction=Decimal("1.5"),
            )


class TestComposition:
    def test_sum_within_one_ok(self) -> None:
        Composition(
            materials=[
                Material(
                    materialName=[LocalisedText(value="A", language="en")],
                    massFraction=Decimal("0.6"),
                ),
                Material(
                    materialName=[LocalisedText(value="B", language="en")],
                    massFraction=Decimal("0.4"),
                ),
            ]
        )

    def test_sum_overflow_rejected(self) -> None:
        with pytest.raises(ValidationError, match="sum"):
            Composition(
                materials=[
                    Material(
                        materialName=[LocalisedText(value="A", language="en")],
                        massFraction=Decimal("0.7"),
                    ),
                    Material(
                        materialName=[LocalisedText(value="B", language="en")],
                        massFraction=Decimal("0.8"),
                    ),
                ]
            )


# =============================================================================
# SubstanceOfConcern
# =============================================================================


class TestSubstanceOfConcern:
    def test_minimal(self) -> None:
        s = SubstanceOfConcern(
            nameIUPAC="Bisphenol A",
            numberCAS="80-05-7",
            concentrations=[Concentration(value=Decimal("0.001"), unit="mass_fraction")],
        )
        assert s.is_identified()

    def test_cas_format_enforced(self) -> None:
        with pytest.raises(ValidationError, match="CAS"):
            SubstanceOfConcern(
                nameIUPAC="X",
                numberCAS="abc-12-3",
                concentrations=[Concentration(value=Decimal("0.1"), unit="mass_fraction")],
            )

    def test_ec_format_enforced(self) -> None:
        with pytest.raises(ValidationError, match="EC"):
            SubstanceOfConcern(
                nameIUPAC="X",
                numberEC="20A-753-7",
                concentrations=[Concentration(value=Decimal("0.1"), unit="mass_fraction")],
            )

    def test_hazard_classification_with_enum(self) -> None:
        h = HazardClassification(
            category=HazardCategory.CARCINOGENICITY_1,
            statement=[LocalisedText(value="May cause cancer", language="en")],
        )
        # use_enum_values=True coerces to .value at validation time
        assert h.category == HazardCategory.CARCINOGENICITY_1.value


class TestConcentration:
    def test_lifecycle_stage_enum(self) -> None:
        c = Concentration(
            value=Decimal("0.001"),
            unit="mass_fraction",
            lifecycleStage=LifeCycleStage.IN_PRODUCT,
        )
        assert c.lifecycle_stage == LifeCycleStage.IN_PRODUCT.value


# =============================================================================
# LCA
# =============================================================================


class TestLifeCycleAssessment:
    def test_v19_impact_category_resolves(self) -> None:
        ref = ImpactCategoryReference(category=LCIAImpactCategory.CLIMATE_CHANGE.value)
        assert ref.category_enum is LCIAImpactCategory.CLIMATE_CHANGE

    def test_legacy_lca_iri_returns_none_enum(self) -> None:
        # v2.0-style ``lca:Climate_change_total`` is not in the v1.9.4-Maki
        # canonical set; .category_enum returns None.
        ref = ImpactCategoryReference(category="lca:Climate_change_total")
        assert ref.category_enum is None

    def test_minimal_with_one_result(self) -> None:
        lca = LifeCycleAssessment(
            results=[
                ImpactResult(
                    impactCategory=ImpactCategoryReference(
                        category=LCIAImpactCategory.WATER_USE_DEPRIVATION.value
                    ),
                    value=Decimal("123.45"),
                    unit="m3_water_eq_deprived",
                )
            ]
        )
        assert len(lca.results) == 1


# =============================================================================
# Connector
# =============================================================================


class TestConnectorRelation:
    def test_v19_relation_type_resolves(self) -> None:
        cr = ConnectorRelation(
            relation=RelationType.HAS_MANUFACTURER.value,
            subject="https://example.com/dpp/1",
            object="https://example.com/actor/abc",
        )
        assert cr.relation_type is RelationType.HAS_MANUFACTURER

    def test_unknown_relation_returns_none_enum(self) -> None:
        cr = ConnectorRelation(
            relation="eudpp:downstreamCustomRelation",
            subject="https://example.com/a",
            object="https://example.com/b",
        )
        assert cr.relation_type is None

    def test_empty_subject_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ConnectorRelation(
                relation="eudpp:hasManufacturer",
                subject="   ",
                object="https://example.com/b",
            )


# =============================================================================
# ReferencePassport (root) — round-trip every fixture
# =============================================================================


class TestReferencePassportRoundTrip:
    @pytest.mark.parametrize(
        "fixture_name",
        ["minimal.json", "multilingual.json", "full.json"],
    )
    def test_valid_fixture_parses_and_round_trips(self, fixture_name: str) -> None:
        fixture = _VALID_DIR / fixture_name
        raw = json.loads(fixture.read_text(encoding="utf-8"))
        p = ReferencePassport.model_validate(raw)
        # Round-trip: dump-then-reparse yields an equal instance
        dumped = p.model_dump(mode="json", by_alias=True, exclude_none=True)
        restored = ReferencePassport.model_validate(dumped)
        assert restored == p

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "missing_dpp_identifier.json",
            "empty_product_name.json",
            "bad_bcp47_language_tag.json",
            "mass_fraction_overflow.json",
            "bad_cas_number.json",
            "effective_period_inverted.json",
        ],
    )
    def test_invalid_fixture_rejected(self, fixture_name: str) -> None:
        fixture = _INVALID_DIR / fixture_name
        raw = json.loads(fixture.read_text(encoding="utf-8"))
        # Strip the diagnostic ``_failure`` field that documents the
        # expected failure for human reviewers.
        raw.pop("_failure", None)
        with pytest.raises(ValidationError):
            ReferencePassport.model_validate(raw)
