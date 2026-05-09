"""Phase 7 task 7.5 — tyres pilot model unit tests.

Pins the four GDSO declaration shapes + the TyreLifecycleHistory
aggregate. These tests run only when ``dppvalidator-tyres`` is
installed (the plugin is editable-installed in the dev environment
via ``uv pip install -e plugins/tyres/``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

pytest.importorskip("dppvalidator_tyres")

from dppvalidator_tyres.models import (
    Birth,
    Collection,
    DOTMarking,
    Recycling,
    RecyclingMethod,
    Retread,
    TyreActor,
    TyreLifecycleHistory,
    TyreSize,
)
from dppvalidator_tyres.models.collection import CollectionDisposition
from dppvalidator_tyres.models.retread import RetreadProcess

# =============================================================================
# Shared fixtures
# =============================================================================


_TYRE_UUID = UUID("550e8400-e29b-41d4-a716-446655440000")


def _manufacturer() -> TyreActor:
    return TyreActor(
        id="https://example.com/operator/acme",
        name="ACME Tyres",
        lei="529900T8BM49AURSDO55",
    )


def _birth() -> Birth:
    return Birth(
        tyreUuid=_TYRE_UUID,
        manufacturer=_manufacturer(),
        manufacturedAt=datetime(2026, 4, 15, 10, 30, tzinfo=timezone.utc),
        dotMarking=DOTMarking(plantCode="B7", sizeCode="5K", weekOfYear=16, year=2026),
        size=TyreSize(
            sectionWidth=205,
            aspectRatio=55,
            rimDiameter=16,
            loadIndex=91,
            speedRating="V",
        ),
    )


# =============================================================================
# TyreActor
# =============================================================================


def test_tyre_actor_minimal() -> None:
    actor = TyreActor(id="https://example.com/op/x", name="X")
    assert actor.id == "https://example.com/op/x"
    assert actor.name == "X"
    assert actor.lei is None


def test_tyre_actor_lei_validation_rejects_short_string() -> None:
    with pytest.raises(ValueError, match="not a valid GLEIF LEI"):
        TyreActor(id="https://example.com/op/x", name="X", lei="TOO-SHORT")


def test_tyre_actor_lei_validation_accepts_canonical() -> None:
    actor = TyreActor(
        id="https://example.com/op/x",
        name="X",
        lei="529900T8BM49AURSDO55",
    )
    assert actor.lei == "529900T8BM49AURSDO55"


# =============================================================================
# DOTMarking
# =============================================================================


def test_dot_marking_well_formed() -> None:
    dot = DOTMarking(plantCode="B7", sizeCode="5K", weekOfYear=16, year=2026)
    assert dot.plant_code == "B7"
    assert dot.week_of_year == 16


def test_dot_marking_rejects_lowercase_plant_code() -> None:
    with pytest.raises(ValueError, match="DOT plant code"):
        DOTMarking(plantCode="b7", sizeCode="5K", weekOfYear=16, year=2026)


def test_dot_marking_week_bounds() -> None:
    with pytest.raises(ValueError):
        DOTMarking(plantCode="B7", sizeCode="5K", weekOfYear=54, year=2026)
    with pytest.raises(ValueError):
        DOTMarking(plantCode="B7", sizeCode="5K", weekOfYear=0, year=2026)


# =============================================================================
# TyreSize
# =============================================================================


def test_tyre_size_passenger_range() -> None:
    size = TyreSize(
        sectionWidth=205,
        aspectRatio=55,
        rimDiameter=16,
        loadIndex=91,
        speedRating="V",
    )
    assert size.speed_rating == "V"


def test_tyre_size_speed_rating_normalised_to_uppercase() -> None:
    size = TyreSize(
        sectionWidth=205,
        aspectRatio=55,
        rimDiameter=16,
        loadIndex=91,
        speedRating="v",
    )
    assert size.speed_rating == "V"


def test_tyre_size_rejects_unknown_speed_rating() -> None:
    with pytest.raises(ValueError, match="ETRTO"):
        TyreSize(
            sectionWidth=205,
            aspectRatio=55,
            rimDiameter=16,
            loadIndex=91,
            speedRating="A",
        )


# =============================================================================
# Birth
# =============================================================================


def test_birth_constructible_from_minimal_payload() -> None:
    birth = _birth()
    assert birth.tyre_uuid == _TYRE_UUID
    assert birth.manufacturer.name == "ACME Tyres"


def test_birth_requires_tz_aware_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Birth(
            tyreUuid=_TYRE_UUID,
            manufacturer=_manufacturer(),
            manufacturedAt=datetime(2026, 4, 15, 10, 30),  # naive!
            dotMarking=DOTMarking(plantCode="B7", sizeCode="5K", weekOfYear=16, year=2026),
            size=TyreSize(
                sectionWidth=205,
                aspectRatio=55,
                rimDiameter=16,
                loadIndex=91,
                speedRating="V",
            ),
        )


# =============================================================================
# Collection / Retread / Recycling
# =============================================================================


def test_collection_minimal() -> None:
    collection = Collection(
        tyreUuid=_TYRE_UUID,
        collector=_manufacturer(),
        collectedAt=datetime(2030, 1, 1, tzinfo=timezone.utc),
        disposition=CollectionDisposition.RETREAD,
    )
    assert collection.disposition == CollectionDisposition.RETREAD.value


def test_retread_requires_previous_birth_uuid() -> None:
    with pytest.raises(ValueError):
        Retread(  # type: ignore[call-arg]
            tyreUuid=_TYRE_UUID,
            retreader=_manufacturer(),
            retreadedAt=datetime(2030, 6, 1, tzinfo=timezone.utc),
            process=RetreadProcess.COLD_CURE,
            # previousBirthUuid intentionally omitted
        )


def test_retread_full_shape() -> None:
    retread = Retread(
        tyreUuid=_TYRE_UUID,
        retreader=_manufacturer(),
        retreadedAt=datetime(2030, 6, 1, tzinfo=timezone.utc),
        process=RetreadProcess.COLD_CURE,
        previousBirthUuid=_TYRE_UUID,
        cycleNumber=1,
    )
    assert retread.process == RetreadProcess.COLD_CURE.value


def test_recycling_recovery_fractions_sum_invariant() -> None:
    """Recovery-fraction sum > 1.0 raises."""
    from dppvalidator_tyres.models.recycling import RecoveryFraction

    with pytest.raises(ValueError, match="exceeds 1.0"):
        Recycling(
            tyreUuid=_TYRE_UUID,
            recycler=_manufacturer(),
            recycledAt=datetime(2031, 1, 1, tzinfo=timezone.utc),
            method=RecyclingMethod.MECHANICAL,
            recoveryFractions=[
                RecoveryFraction(materialName="Crumb rubber", massFractionRecovered=Decimal("0.7")),
                RecoveryFraction(materialName="Steel wire", massFractionRecovered=Decimal("0.5")),
            ],
        )


def test_recycling_recovery_fractions_sum_within_one_ok() -> None:
    from dppvalidator_tyres.models.recycling import RecoveryFraction

    recycling = Recycling(
        tyreUuid=_TYRE_UUID,
        recycler=_manufacturer(),
        recycledAt=datetime(2031, 1, 1, tzinfo=timezone.utc),
        method=RecyclingMethod.MECHANICAL,
        recoveryFractions=[
            RecoveryFraction(materialName="Crumb rubber", massFractionRecovered=Decimal("0.7")),
            RecoveryFraction(materialName="Steel wire", massFractionRecovered=Decimal("0.12")),
        ],
    )
    assert recycling.recovery_fractions is not None
    assert len(recycling.recovery_fractions) == 2


# =============================================================================
# TyreLifecycleHistory aggregate
# =============================================================================


def test_history_with_no_events_is_valid() -> None:
    history = TyreLifecycleHistory(birth=_birth())
    assert history.events == []


def test_history_chronological_events_ok() -> None:
    history = TyreLifecycleHistory(
        birth=_birth(),
        events=[
            {
                "type": "collection",
                "declaration": Collection(
                    tyreUuid=_TYRE_UUID,
                    collector=_manufacturer(),
                    collectedAt=datetime(2030, 1, 1, tzinfo=timezone.utc),
                    disposition=CollectionDisposition.RECYCLE,
                ),
            },
            {
                "type": "recycling",
                "declaration": Recycling(
                    tyreUuid=_TYRE_UUID,
                    recycler=_manufacturer(),
                    recycledAt=datetime(2031, 1, 1, tzinfo=timezone.utc),
                    method=RecyclingMethod.MECHANICAL,
                ),
            },
        ],
    )
    assert len(history.events) == 2


def test_history_rejects_uuid_mismatch() -> None:
    other_uuid = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    with pytest.raises(ValueError, match="does not match the Birth"):
        TyreLifecycleHistory(
            birth=_birth(),
            events=[
                {
                    "type": "collection",
                    "declaration": Collection(
                        tyreUuid=other_uuid,
                        collector=_manufacturer(),
                        collectedAt=datetime(2030, 1, 1, tzinfo=timezone.utc),
                        disposition=CollectionDisposition.RECYCLE,
                    ),
                },
            ],
        )


def test_history_rejects_out_of_order_events() -> None:
    with pytest.raises(ValueError, match="chronological"):
        TyreLifecycleHistory(
            birth=_birth(),
            events=[
                {
                    "type": "collection",
                    "declaration": Collection(
                        tyreUuid=_TYRE_UUID,
                        collector=_manufacturer(),
                        collectedAt=datetime(2025, 1, 1, tzinfo=timezone.utc),
                        disposition=CollectionDisposition.RECYCLE,
                    ),
                },
            ],
        )


def test_history_rejects_event_after_recycling() -> None:
    with pytest.raises(ValueError, match="follows a Recycling event"):
        TyreLifecycleHistory(
            birth=_birth(),
            events=[
                {
                    "type": "recycling",
                    "declaration": Recycling(
                        tyreUuid=_TYRE_UUID,
                        recycler=_manufacturer(),
                        recycledAt=datetime(2030, 1, 1, tzinfo=timezone.utc),
                        method=RecyclingMethod.MECHANICAL,
                    ),
                },
                {
                    "type": "collection",
                    "declaration": Collection(
                        tyreUuid=_TYRE_UUID,
                        collector=_manufacturer(),
                        collectedAt=datetime(2031, 1, 1, tzinfo=timezone.utc),
                        disposition=CollectionDisposition.RECYCLE,
                    ),
                },
            ],
        )


def test_history_rejects_two_recycling_events() -> None:
    with pytest.raises(ValueError, match="only one Recycling event"):
        TyreLifecycleHistory(
            birth=_birth(),
            events=[
                {
                    "type": "recycling",
                    "declaration": Recycling(
                        tyreUuid=_TYRE_UUID,
                        recycler=_manufacturer(),
                        recycledAt=datetime(2030, 1, 1, tzinfo=timezone.utc),
                        method=RecyclingMethod.MECHANICAL,
                    ),
                },
                {
                    "type": "recycling",
                    "declaration": Recycling(
                        tyreUuid=_TYRE_UUID,
                        recycler=_manufacturer(),
                        recycledAt=datetime(2031, 1, 1, tzinfo=timezone.utc),
                        method=RecyclingMethod.PYROLYSIS,
                    ),
                },
            ],
        )
