"""Performance scorecard models for UNTP DPP."""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import Field

from dppvalidator.models.base import UNTPBaseModel
from dppvalidator.models.claims import Standard
from dppvalidator.models.enums import OperationalScope
from dppvalidator.models.primitives import Link, SecureLink


class EmissionsPerformance(UNTPBaseModel):
    """Emissions performance scorecard."""

    _jsonld_type: ClassVar[list[str]] = ["EmissionsPerformance"]

    carbon_footprint: Annotated[
        float,
        Field(
            ...,
            alias="carbonFootprint",
            description="Carbon footprint in KgCO2e per declared unit",
        ),
    ]
    declared_unit: Annotated[
        str,
        Field(
            ...,
            alias="declaredUnit",
            description="Unit of product (EA, KGM, LTR) for carbon footprint basis",
        ),
    ]
    operational_scope: Annotated[
        OperationalScope | None,
        Field(
            default=None,
            alias="operationalScope",
            description="Emissions operational scope (GHG Protocol or lifecycle boundary)",
        ),
    ]
    primary_sourced_ratio: Annotated[
        float,
        Field(
            ...,
            ge=0,
            le=1,
            alias="primarySourcedRatio",
            description="Ratio of primary source emissions data (0-1)",
        ),
    ]
    reporting_standard: Annotated[
        Standard | None,
        Field(
            default=None,
            alias="reportingStandard",
            description="Reporting standard (GHG Protocol, IFRS S2, etc.)",
        ),
    ]


class TraceabilityPerformance(UNTPBaseModel):
    """Traceability performance for a value chain process."""

    _jsonld_type: ClassVar[list[str]] = ["TraceabilityPerformance"]

    value_chain_process: Annotated[
        str | None,
        Field(
            default=None,
            alias="valueChainProcess",
            description="Industry-specific value chain process name",
        ),
    ]
    verified_ratio: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            le=1,
            alias="verifiedRatio",
            description="Proportion of traced materials (0-1)",
        ),
    ]
    traceability_event: Annotated[
        list[SecureLink] | None,
        Field(
            default=None,
            alias="traceabilityEvent",
            description="Links to traceability events",
        ),
    ]


class CircularityPerformance(UNTPBaseModel):
    """Circularity performance scorecard."""

    _jsonld_type: ClassVar[list[str]] = ["CircularityPerformance"]

    recycling_information: Annotated[
        Link | None,
        Field(
            default=None,
            alias="recyclingInformation",
            description="Link to recycling information",
        ),
    ]
    repair_information: Annotated[
        Link | None,
        Field(
            default=None,
            alias="repairInformation",
            description="Link to repair instructions",
        ),
    ]
    recyclable_content: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            le=1,
            alias="recyclableContent",
            description="Fraction designed to be recyclable (0-1)",
        ),
    ]
    recycled_content: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            le=1,
            alias="recycledContent",
            description="Fraction of recycled content (0-1)",
        ),
    ]
    utility_factor: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            alias="utilityFactor",
            description="Durability indicator (lifetime / industry avg)",
        ),
    ]
    material_circularity_indicator: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            le=1,
            alias="materialCircularityIndicator",
            description="Overall circularity indicator (0-1)",
        ),
    ]
