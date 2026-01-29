"""Claim and conformity-related models for UNTP DPP."""

from __future__ import annotations

from datetime import date
from typing import Annotated, ClassVar

from pydantic import Field

from dppvalidator.models.base import UNTPBaseModel, UNTPStrictModel
from dppvalidator.models.enums import ConformityTopic, CriterionStatus
from dppvalidator.models.identifiers import Party
from dppvalidator.models.primitives import Classification, FlexibleUri, Measure, SecureLink


class Metric(UNTPStrictModel):
    """Performance metric with value and optional score."""

    _jsonld_type: ClassVar[list[str]] = ["Metric"]

    metric_name: Annotated[
        str,
        Field(..., alias="metricName", description="Human readable metric name"),
    ]
    metric_value: Annotated[
        Measure,
        Field(..., alias="metricValue", description="Numeric value and unit"),
    ]
    score: str | None = Field(default=None, description="Score or rank for this metric")
    accuracy: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Accuracy as percentage (0-1)",
    )


class Criterion(UNTPBaseModel):
    """Specific rule or criterion within a standard or regulation."""

    _jsonld_type: ClassVar[list[str]] = ["Criterion"]

    id: Annotated[
        FlexibleUri,
        Field(..., description="Unique identifier for the criterion"),
    ]
    name: str = Field(..., description="Criterion name")
    description: str = Field(..., description="Full text description of the criterion")
    conformity_topic: Annotated[
        ConformityTopic,
        Field(..., alias="conformityTopic", description="Conformity topic category"),
    ]
    status: CriterionStatus = Field(..., description="Lifecycle status")
    sub_criterion: Annotated[
        list[Criterion] | None,
        Field(default=None, alias="subCriterion", description="Subordinate criteria"),
    ]
    threshold_value: Annotated[
        Metric | None,
        Field(default=None, alias="thresholdValue", description="Minimum compliance threshold"),
    ]
    performance_level: Annotated[
        str | None,
        Field(default=None, alias="performanceLevel", description="Performance category code"),
    ]
    category: Annotated[
        list[Classification] | None,
        Field(default=None, description="Product categories the criterion applies to"),
    ]
    tag: Annotated[
        list[str] | None,
        Field(default=None, description="Tags for stakeholder/commodity types"),
    ]


class Standard(UNTPStrictModel):
    """Standard that specifies conformance criteria (e.g., ISO 14000)."""

    _jsonld_type: ClassVar[list[str]] = ["Standard"]

    id: Annotated[
        FlexibleUri | None,
        Field(default=None, description="Unique identifier for the standard"),
    ]
    name: str | None = Field(default=None, description="Name of the standard")
    issuing_party: Annotated[
        Party,
        Field(..., alias="issuingParty", description="Party that issued the standard"),
    ]
    issue_date: Annotated[
        date | None,
        Field(default=None, alias="issueDate", description="Date the standard was issued"),
    ]


class Regulation(UNTPStrictModel):
    """Regulation that defines assessment criteria."""

    _jsonld_type: ClassVar[list[str]] = ["Regulation"]

    id: Annotated[
        FlexibleUri | None,
        Field(default=None, description="Globally unique identifier of the regulation"),
    ]
    name: str | None = Field(default=None, description="Name of the regulation or act")
    jurisdiction_country: Annotated[
        str | None,
        Field(
            default=None,
            alias="jurisdictionCountry",
            description="ISO 3166-1 jurisdiction country code",
        ),
    ]
    administered_by: Annotated[
        Party,
        Field(..., alias="administeredBy", description="Issuing body of the regulation"),
    ]
    effective_date: Annotated[
        date | None,
        Field(default=None, alias="effectiveDate", description="Date regulation came into effect"),
    ]


class Claim(UNTPBaseModel):
    """Declaration of conformance with standard or regulation criteria."""

    _jsonld_type: ClassVar[list[str]] = ["Claim", "Declaration"]

    id: Annotated[
        FlexibleUri,
        Field(..., description="Unique identifier for the declaration"),
    ]
    description: str | None = Field(default=None, description="Textual description of the claim")
    reference_standard: Annotated[
        Standard | None,
        Field(default=None, alias="referenceStandard", description="Reference standard"),
    ]
    reference_regulation: Annotated[
        Regulation | None,
        Field(default=None, alias="referenceRegulation", description="Reference regulation"),
    ]
    assessment_criteria: Annotated[
        list[Criterion] | None,
        Field(default=None, alias="assessmentCriteria", description="Assessment specifications"),
    ]
    assessment_date: Annotated[
        date | None,
        Field(default=None, alias="assessmentDate", description="Date of assessment"),
    ]
    declared_value: Annotated[
        list[Metric] | None,
        Field(default=None, alias="declaredValue", description="Measured values"),
    ]
    conformance: bool = Field(..., description="Whether the claim conforms to criteria")
    conformity_topic: Annotated[
        ConformityTopic,
        Field(..., alias="conformityTopic", description="Conformity topic category"),
    ]
    conformity_evidence: Annotated[
        SecureLink | None,
        Field(
            default=None, alias="conformityEvidence", description="Evidence supporting the claim"
        ),
    ]
