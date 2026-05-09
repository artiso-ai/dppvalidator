"""Multilingual labels for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.11 of [docs/plans/CIRPASS_2_MIGRATION.md] (resolves G16).
ESPR Annex requires DPP labels in the official languages of every
member state where the product is sold; the CIRPASS message expresses
this through fielded multilingual values rather than UNTP's default-
language strings. :class:`LocalisedText` is the wrapper.
"""

from __future__ import annotations

import re
from typing import ClassVar

from pydantic import Field, field_validator

from dppvalidator.models.base import UNTPBaseModel

# BCP-47 language tag — pragmatic regex that matches the real-world
# subset (RFC 5646's full grammar accepts more shapes; this covers
# everything ESPR actually emits).
#
#   primary subtag   2-3 ASCII letters     en, de, fra, zh
#   region subtag    optional 2-letter or 3-digit territory  en-US, en-029
#   script subtag    optional 4-letter ISO-15924             zh-Hant
#   variant subtag   optional 5-8 alphanum                   en-GB-oxendict
_BCP47_RE = re.compile(
    r"^(?P<primary>[a-z]{2,3})"
    r"(?:-(?P<script>[A-Z][a-z]{3}))?"
    r"(?:-(?P<region>[A-Z]{2}|[0-9]{3}))?"
    r"(?:-(?P<variant>[a-zA-Z0-9]{5,8}))?$"
)


class LocalisedText(UNTPBaseModel):
    """A text value tagged with a BCP-47 language identifier.

    Wire shape: ``{"value": "Cotton t-shirt", "language": "en"}``.

    Used wherever the CIRPASS reference structure expects a
    user-facing label that must surface in multiple official
    languages — product name, description, classification labels,
    etc. The set of fields requiring this wrapper is dictated by the
    v1.9.1 SHACL shape audit (Phase 1 task 1.6); fields without the
    multilingual requirement use plain :class:`str`.

    Attributes:
        value: The text content. Whitespace is trimmed by the base
            model's ``str_strip_whitespace`` config.
        language: BCP-47 tag (``en``, ``de``, ``zh-Hant``,
            ``en-US``, etc.). Validated against the pragmatic-subset
            grammar in :data:`_BCP47_RE`. Lower-case primary subtag,
            initial-case script subtag, upper-case region subtag.
    """

    _jsonld_type: ClassVar[list[str]] = ["LocalisedText"]

    value: str = Field(
        ...,
        description="The text value in the language identified by ``language``.",
        min_length=1,
    )
    language: str = Field(
        ...,
        description="BCP-47 language tag (e.g. ``en``, ``de``, ``zh-Hant``).",
    )

    @field_validator("language")
    @classmethod
    def _validate_bcp47(cls, value: str) -> str:
        if not _BCP47_RE.match(value):
            msg = (
                f"language tag {value!r} is not a recognised BCP-47 form. "
                f"Expected ``primary[-Script][-REGION][-variant]``, e.g. "
                f"``en``, ``de``, ``zh-Hant``, ``en-GB``."
            )
            raise ValueError(msg)
        return value


def is_valid_bcp47(value: str) -> bool:
    """Return True if ``value`` is a recognised BCP-47 tag.

    Used as a public helper for callers that need to validate a
    language string outside the :class:`LocalisedText` constructor
    (e.g. mapping shims that pre-flight-check before wrapping).
    """
    return bool(_BCP47_RE.match(value))
