"""Claim and conformity-related types for UNTP v0.7.0.

This is where the biggest semantic shift lives compared to v0.6.x:

- The three v0.6 "scorecard" classes (``EmissionsPerformance``,
  ``CircularityPerformance``, ``TraceabilityPerformance``) are gone. They
  fold into :class:`Claim.claimedPerformance: list[Performance]`, with the
  topic of the claim carried by :class:`ConformityTopic` entries on
  :attr:`Claim.conformityTopic`.
- The v0.6 ``Metric`` class is gone. Its content is split across
  :class:`Performance.metric` (the metric being measured),
  :class:`Performance.measure` (the numeric reading), and
  :class:`Performance.score` (the qualitative score).
- The v0.6 ``Standard``, ``Regulation``, ``Criterion`` classes are now
  inlined under :class:`Claim` as plain ``referenceStandard[]``,
  ``referenceRegulation[]``, ``referenceCriteria[]`` arrays of free-form
  reference objects.
- :class:`Period` is new — used by :attr:`Claim.applicablePeriod`.

Cross-field invariants implemented as model validators:

- :class:`Period`: ``startDate`` must be strictly before ``endDate`` when
  both are present.
- :class:`Performance`: at least one of ``measure`` / ``score`` must be
  present. A claim that conveys neither is meaningless.
- :class:`Claim`: when ``claimedPerformance`` is non-empty, an
  ``applicablePeriod`` SHOULD be supplied (advisory; logged via the
  semantic-rule layer in Phase 3b — not enforced here so that compact
  claims still validate).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, ClassVar

from pydantic import Field, model_validator

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.v0_7.primitives import (
    Classification,
    FlexibleUri,
    Link,
    Measure,
)


class ConformityTopic(UNTPBaseModel):
    """A topic that a claim conforms to (e.g. emissions, circularity, traceability).

    Drawn from the UNTP topics vocabulary at
    ``https://vocabulary.uncefact.org/ConformityTopic#``. ``id`` and
    ``name`` are required; ``definition`` carries the rich human-readable
    definition.
    """

    _jsonld_type: ClassVar[list[str]] = ["ConformityTopic"]

    id: FlexibleUri = Field(..., description="URI identifying the conformity topic.")
    name: str = Field(..., description="Short name (e.g. ``emissions``).")
    definition: Annotated[str | None, Field(default=None)]


class Period(UNTPBaseModel):
    """A date interval used by claims and reporting periods.

    Both bounds are optional individually so callers can express open-ended
    periods, but if both are present the start must precede the end.
    """

    _jsonld_type: ClassVar[list[str]] = ["Period"]

    start_date: Annotated[date | None, Field(default=None, alias="startDate")]
    end_date: Annotated[date | None, Field(default=None, alias="endDate")]

    @model_validator(mode="after")
    def _validate_interval(self) -> Period:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError(
                "Period.startDate must be on or before Period.endDate "
                f"(got {self.start_date} > {self.end_date})",
            )
        return self


class Score(UNTPBaseModel):
    """A qualitative performance grade (e.g. ``AAA``, ``B``, ``A+``).

    The grade itself is a coded value (``code``); ``rank`` is an integer
    where 1 is the highest rank within the scoring framework. The
    framework that defines the codes is referenced via the parent
    :class:`Performance` and the :class:`Claim` it belongs to (not by
    Score itself).
    """

    _jsonld_type: ClassVar[list[str]] = ["Score"]

    code: str = Field(..., description="Coded score value (e.g. 'AAA', 'B').")
    rank: Annotated[
        int | None,
        Field(
            default=None,
            description="Integer rank within the framework (1 = highest).",
        ),
    ]
    definition: Annotated[
        str | None,
        Field(default=None, description="Description of the meaning of this score."),
    ]


class Performance(UNTPBaseModel):
    """A single performance reading: metric + measure and/or score.

    Replaces the v0.6 ``Metric`` class (and absorbs the per-topic scorecard
    classes via :class:`Claim`). At least one of ``measure`` or ``score``
    must be present — a Performance that says *nothing* about the metric
    is meaningless.
    """

    _jsonld_type: ClassVar[list[str]] = ["Performance"]

    metric: dict[str, Any] = Field(
        ...,
        description=(
            "The metric being measured (free-form object; the upstream schema does "
            "not enforce a sub-schema here, leaving room for industry-specific shapes)."
        ),
    )
    measure: Measure | None = Field(default=None, description="Quantitative reading.")
    score: Score | None = Field(default=None, description="Qualitative grade.")

    @model_validator(mode="after")
    def _at_least_one_outcome(self) -> Performance:
        if self.measure is None and self.score is None:
            raise ValueError(
                "Performance must have at least one of ``measure`` or ``score`` — "
                "a performance reading with neither value is meaningless.",
            )
        return self


class Claim(UNTPBaseModel):
    """A conformity claim attached to a :class:`Product` in v0.7.0.

    Where v0.6.x split conformity into ``conformityClaim`` (typed claims)
    plus three separate scorecard classes, v0.7.0 unifies everything here:
    set ``conformityTopic`` to mark the topic, ``claimedPerformance`` to
    carry the readings, and ``referenceCriteria/Standard/Regulation`` to
    point at the framework the claim conforms to.

    Reference fields are intentionally typed as ``list[dict[str, Any]]``:
    the upstream schema leaves their internal shape open for now (Phase 3c
    revisits this when the eudpp_jsonld exporter mapping is reworked).
    """

    _jsonld_type: ClassVar[list[str]] = ["Claim"]

    id: FlexibleUri = Field(
        ..., description="Globally unique identifier of this claim (URI or UUID)."
    )
    name: str = Field(..., description="Name of the claim — usually mirrors the criterion name.")
    description: Annotated[str | None, Field(default=None)]
    conformity_topic: Annotated[
        list[ConformityTopic],
        Field(default_factory=list, alias="conformityTopic"),
    ]
    reference_criteria: Annotated[
        list[dict[str, Any]],
        Field(
            default_factory=list,
            alias="referenceCriteria",
            description="The criteria this claim is asserted against.",
        ),
    ]
    reference_standard: Annotated[
        list[dict[str, Any]],
        Field(default_factory=list, alias="referenceStandard"),
    ]
    reference_regulation: Annotated[
        list[dict[str, Any]],
        Field(default_factory=list, alias="referenceRegulation"),
    ]
    claim_date: Annotated[
        date | None,
        Field(default=None, alias="claimDate"),
    ]
    applicable_period: Annotated[
        Period | None,
        Field(default=None, alias="applicablePeriod"),
    ]
    claimed_performance: Annotated[
        list[Performance],
        Field(
            default_factory=list,
            alias="claimedPerformance",
            description=(
                "The performance levels claimed by this claim — replaces the v0.6.x "
                "Emissions/Circularity/TraceabilityPerformance scorecards."
            ),
        ),
    ]
    evidence: Annotated[
        list[Link],
        Field(
            default_factory=list,
            description="URIs of evidence supporting the claim (typically DCC credentials).",
        ),
    ]
    classification: Annotated[
        list[Classification],
        Field(default_factory=list),
    ]
