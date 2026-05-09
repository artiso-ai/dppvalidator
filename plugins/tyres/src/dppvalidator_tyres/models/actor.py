"""Shared TyreActor model — used by every GDSO declaration.

Each declaration (Birth / Collection / Retread / Recycling) names
the actor that produced it. The actor is identified by a stable
URI plus a human-readable name and an optional GLEIF LEI (the
recommended GDSO identifier scheme).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# GLEIF Legal Entity Identifier — 20 alphanumeric characters per
# ISO 17442. The GDSO actor declaration recommends LEI as the
# canonical operator identifier.
_LEI_RE = re.compile(r"^[0-9A-Z]{20}$")


class TyreActor(BaseModel):
    """An actor in the tyre lifecycle (manufacturer, collector, retreader, recycler).

    Wire shape:
        ``{"id": "https://example.com/operator/X",
           "name": "ACME Tyre Manufacturing",
           "lei": "529900T8BM49AURSDO55"}``
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    id: str = Field(..., description="URI / DID identifying the actor.")
    name: str = Field(..., min_length=1, description="Human-readable actor name.")
    lei: str | None = Field(
        default=None,
        description=(
            "GLEIF Legal Entity Identifier (ISO 17442). 20 alphanumeric "
            "characters; recommended by GDSO for production declarations."
        ),
    )

    @field_validator("lei")
    @classmethod
    def _validate_lei(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not _LEI_RE.match(value):
            msg = (
                f"TyreActor.lei={value!r} is not a valid GLEIF LEI "
                "(20 alphanumeric characters per ISO 17442)."
            )
            raise ValueError(msg)
        return value
