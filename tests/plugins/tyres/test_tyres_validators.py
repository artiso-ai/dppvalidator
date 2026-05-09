"""Phase 7 task 7.6 — TYR-coded validator unit tests.

Each rule has a positive (clean fixture → no violations) and
negative (broken fixture → violation with the right code) test.
The fixtures use a synthetic ``Passport`` shim that mimics the
UNTP DPP wire shape — rules walk the
``credentialSubject.extensions.tyreLifecycleHistory`` slot, so a
plain dict-shaped passport is sufficient to exercise the rule
logic without booting the full ValidationEngine.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

pytest.importorskip("dppvalidator_tyres")

from dppvalidator_tyres.validators import (
    TYR_RULES,
    BirthChainCompletenessRule,
    CollectionActorRule,
    DOTMarkingRule,
    LoadIndexRule,
    RecyclingMethodRule,
    RetreadProvenanceRule,
    SectionWidthRule,
    SpeedRatingRule,
)

# =============================================================================
# Test passport shim
# =============================================================================
#
# The plugin's rules walk ``passport.credential_subject.extensions.tyreLifecycleHistory``.
# A SimpleNamespace-shaped object with the right attributes is
# sufficient — no need to construct a real Pydantic DPP envelope.


class _SubjectStub:
    """Attribute-shim for the ``credential_subject`` slot.

    The rule helper (:func:`_extract_history`) reads
    ``passport.credential_subject.extensions`` as either an attribute
    *or* a dict member. The stub keeps ``extensions`` as a *dict* so
    rules find ``tyreLifecycleHistory`` via dict lookup (same path
    a real Pydantic model would expose with ``model_dump``).
    """

    def __init__(self, extensions: dict[str, Any]) -> None:
        self.extensions = extensions


class _PassportStub:
    """Top-level passport stub with a ``credential_subject`` attr."""

    def __init__(self, credential_subject: _SubjectStub) -> None:
        self.credential_subject = credential_subject


def _passport(history: dict[str, Any] | None) -> object:
    """Build a minimal passport-shaped object carrying the given history."""
    extensions: dict[str, Any] = {}
    if history is not None:
        extensions["tyreLifecycleHistory"] = history
    return _PassportStub(_SubjectStub(extensions))


def _well_formed_history() -> dict[str, Any]:
    """A clean tyreLifecycleHistory that passes every TYR rule."""
    return {
        "birth": {
            "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
            "manufacturer": {
                "id": "https://example.com/operator/acme",
                "name": "ACME Tyres",
                "lei": "529900T8BM49AURSDO55",
            },
            "manufacturedAt": "2026-04-15T10:30:00+00:00",
            "dotMarking": {
                "plantCode": "B7",
                "sizeCode": "5K",
                "weekOfYear": 16,
                "year": 2026,
            },
            "size": {
                "sectionWidth": 205,
                "aspectRatio": 55,
                "rimDiameter": 16,
                "loadIndex": 91,
                "speedRating": "V",
            },
        },
        "events": [],
    }


# =============================================================================
# Dispatch sanity
# =============================================================================


def test_tyr_rules_tuple_lists_all_eight() -> None:
    assert len(TYR_RULES) == 8
    rule_ids = [r.rule_id for r in TYR_RULES]
    assert rule_ids == [
        "TYR001",
        "TYR002",
        "TYR003",
        "TYR004",
        "TYR005",
        "TYR006",
        "TYR007",
        "TYR008",
    ]


def test_every_rule_carries_attribution() -> None:
    for rule in TYR_RULES:
        assert rule.rule_id.startswith("TYR")
        assert rule.description
        assert rule.severity in {"error", "warning", "info"}
        assert rule.suggestion
        assert rule.docs_url


# =============================================================================
# Non-tyre passports are silently skipped
# =============================================================================


def test_rules_skip_passport_without_extension() -> None:
    """A non-tyre passport must produce zero violations from any TYR rule."""
    passport = _passport(history=None)
    for rule in TYR_RULES:
        assert rule.check(passport) == [], f"{rule.rule_id} fired on non-tyre passport"


# =============================================================================
# TYR001 — DOT marking
# =============================================================================


def test_tyr001_clean_payload_no_violation() -> None:
    rule = DOTMarkingRule()
    assert rule.check(_passport(_well_formed_history())) == []


def test_tyr001_missing_dot_marking_fires() -> None:
    rule = DOTMarkingRule()
    history = _well_formed_history()
    del history["birth"]["dotMarking"]
    violations = rule.check(_passport(history))
    assert len(violations) == 1
    assert "dotMarking" in violations[0][0]


def test_tyr001_missing_field_fires() -> None:
    rule = DOTMarkingRule()
    history = _well_formed_history()
    history["birth"]["dotMarking"]["plantCode"] = ""
    violations = rule.check(_passport(history))
    assert len(violations) == 1
    assert "plantCode" in violations[0][0]


# =============================================================================
# TYR002 — Birth chain completeness
# =============================================================================


def test_tyr002_clean_payload_no_violation() -> None:
    rule = BirthChainCompletenessRule()
    assert rule.check(_passport(_well_formed_history())) == []


def test_tyr002_missing_manufacturer_fires() -> None:
    rule = BirthChainCompletenessRule()
    history = _well_formed_history()
    del history["birth"]["manufacturer"]
    violations = rule.check(_passport(history))
    assert any("manufacturer" in v[0] for v in violations)


def test_tyr002_missing_manufacturer_id_fires() -> None:
    rule = BirthChainCompletenessRule()
    history = _well_formed_history()
    history["birth"]["manufacturer"]["id"] = ""
    violations = rule.check(_passport(history))
    assert any("manufacturer.id" in v[0] for v in violations)


def test_tyr002_missing_birth_fires() -> None:
    rule = BirthChainCompletenessRule()
    history = _well_formed_history()
    del history["birth"]
    violations = rule.check(_passport(history))
    assert violations
    assert "no Birth declaration" in violations[0][1]


# =============================================================================
# TYR003 — Load index
# =============================================================================


def test_tyr003_in_range_no_violation() -> None:
    rule = LoadIndexRule()
    assert rule.check(_passport(_well_formed_history())) == []


def test_tyr003_below_range_fires() -> None:
    rule = LoadIndexRule()
    history = _well_formed_history()
    history["birth"]["size"]["loadIndex"] = 30
    violations = rule.check(_passport(history))
    assert len(violations) == 1
    assert "loadIndex" in violations[0][0]


def test_tyr003_above_range_fires() -> None:
    rule = LoadIndexRule()
    history = _well_formed_history()
    history["birth"]["size"]["loadIndex"] = 200
    violations = rule.check(_passport(history))
    assert len(violations) == 1


# =============================================================================
# TYR004 — Speed rating
# =============================================================================


def test_tyr004_known_letter_no_violation() -> None:
    rule = SpeedRatingRule()
    history = _well_formed_history()
    history["birth"]["size"]["speedRating"] = "H"
    assert rule.check(_passport(history)) == []


def test_tyr004_unknown_letter_fires() -> None:
    rule = SpeedRatingRule()
    history = _well_formed_history()
    history["birth"]["size"]["speedRating"] = "A"
    violations = rule.check(_passport(history))
    assert len(violations) == 1


def test_tyr004_lowercase_normalised() -> None:
    """Lowercase letters are normalised to uppercase before comparison."""
    rule = SpeedRatingRule()
    history = _well_formed_history()
    history["birth"]["size"]["speedRating"] = "v"
    assert rule.check(_passport(history)) == []


# =============================================================================
# TYR005 — Section width / aspect ratio / rim diameter
# =============================================================================


def test_tyr005_in_range_no_violation() -> None:
    rule = SectionWidthRule()
    assert rule.check(_passport(_well_formed_history())) == []


def test_tyr005_oversize_section_width_fires() -> None:
    rule = SectionWidthRule()
    history = _well_formed_history()
    history["birth"]["size"]["sectionWidth"] = 600
    violations = rule.check(_passport(history))
    assert len(violations) == 1
    assert "sectionWidth" in violations[0][0]


def test_tyr005_multiple_dim_violations() -> None:
    rule = SectionWidthRule()
    history = _well_formed_history()
    history["birth"]["size"]["aspectRatio"] = 5
    history["birth"]["size"]["rimDiameter"] = 30
    violations = rule.check(_passport(history))
    assert len(violations) == 2


# =============================================================================
# TYR006 — Retread provenance
# =============================================================================


def _retread_event(*, missing_previous: bool = False) -> dict[str, Any]:
    declaration = {
        "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
        "retreader": {"id": "https://example.com/retreader/x", "name": "Retreader"},
        "retreadedAt": "2030-06-01T00:00:00+00:00",
        "process": "cold_cure",
        "previousBirthUuid": "550e8400-e29b-41d4-a716-446655440000",
    }
    if missing_previous:
        del declaration["previousBirthUuid"]
    return {"type": "retread", "declaration": declaration}


def test_tyr006_clean_retread_no_violation() -> None:
    rule = RetreadProvenanceRule()
    history = _well_formed_history()
    history["events"].append(_retread_event())
    assert rule.check(_passport(history)) == []


def test_tyr006_missing_previous_birth_uuid_fires() -> None:
    rule = RetreadProvenanceRule()
    history = _well_formed_history()
    history["events"].append(_retread_event(missing_previous=True))
    violations = rule.check(_passport(history))
    assert len(violations) == 1
    assert "previousBirthUuid" in violations[0][0]


def test_tyr006_skips_non_retread_events() -> None:
    """TYR006 only fires on Retread events; collection / recycling untouched."""
    rule = RetreadProvenanceRule()
    history = _well_formed_history()
    history["events"].append(
        {
            "type": "collection",
            "declaration": {
                "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
                "collector": {"id": "x", "name": "X"},
                "collectedAt": "2030-01-01T00:00:00+00:00",
                "disposition": "retread",
            },
        }
    )
    assert rule.check(_passport(history)) == []


# =============================================================================
# TYR007 — Collection actor
# =============================================================================


def test_tyr007_clean_collection_no_violation() -> None:
    rule = CollectionActorRule()
    history = _well_formed_history()
    history["events"].append(
        {
            "type": "collection",
            "declaration": {
                "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
                "collector": {"id": "https://example.com/collector/eu", "name": "EU Collection"},
                "collectedAt": "2030-01-01T00:00:00+00:00",
                "disposition": "recycle",
            },
        }
    )
    assert rule.check(_passport(history)) == []


def test_tyr007_missing_collector_fires() -> None:
    rule = CollectionActorRule()
    history = _well_formed_history()
    history["events"].append(
        {
            "type": "collection",
            "declaration": {
                "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
                "collectedAt": "2030-01-01T00:00:00+00:00",
                "disposition": "recycle",
            },
        }
    )
    violations = rule.check(_passport(history))
    assert len(violations) == 1
    assert "collector" in violations[0][0]


def test_tyr007_collector_missing_id_fires() -> None:
    rule = CollectionActorRule()
    history = _well_formed_history()
    history["events"].append(
        {
            "type": "collection",
            "declaration": {
                "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
                "collector": {"name": "Anonymous"},
                "collectedAt": "2030-01-01T00:00:00+00:00",
                "disposition": "recycle",
            },
        }
    )
    violations = rule.check(_passport(history))
    assert any("collector.id" in v[0] for v in violations)


# =============================================================================
# TYR008 — Recycling method
# =============================================================================


def test_tyr008_known_method_no_violation() -> None:
    rule = RecyclingMethodRule()
    history = _well_formed_history()
    history["events"].append(
        {
            "type": "recycling",
            "declaration": {
                "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
                "recycler": {"id": "x", "name": "X"},
                "recycledAt": "2031-01-01T00:00:00+00:00",
                "method": "mechanical",
            },
        }
    )
    assert rule.check(_passport(history)) == []


def test_tyr008_unknown_method_fires() -> None:
    rule = RecyclingMethodRule()
    history = _well_formed_history()
    history["events"].append(
        {
            "type": "recycling",
            "declaration": {
                "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
                "recycler": {"id": "x", "name": "X"},
                "recycledAt": "2031-01-01T00:00:00+00:00",
                "method": "alchemy",
            },
        }
    )
    violations = rule.check(_passport(history))
    assert len(violations) == 1


def test_tyr008_missing_method_fires() -> None:
    rule = RecyclingMethodRule()
    history = _well_formed_history()
    history["events"].append(
        {
            "type": "recycling",
            "declaration": {
                "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
                "recycler": {"id": "x", "name": "X"},
                "recycledAt": "2031-01-01T00:00:00+00:00",
            },
        }
    )
    violations = rule.check(_passport(history))
    assert len(violations) == 1


# =============================================================================
# Determinism: rule.check() is pure
# =============================================================================


def test_rule_check_does_not_mutate_input() -> None:
    """Each rule call must leave the passport untouched."""
    history = _well_formed_history()
    snapshot = deepcopy(history)
    passport = _passport(history)
    for rule in TYR_RULES:
        rule.check(passport)
    assert history == snapshot
