"""Phase 5 — Hypothesis-driven round-trip invariants for the UNTP ↔ CIRPASS shims.

Per the Phase 5 exit criteria of [docs/plans/CIRPASS_2_MIGRATION.md]:

> Property test (200 examples, default profile) green both directions.

The invariants:

- ``to_cirpass_1_3(to_untp_0_7(c))[0]`` recovers the lossless-subset
  fields of ``c``.
- ``to_untp_0_7(to_cirpass_1_3(u))[0]`` recovers the lossless-subset
  fields of ``u``.

Strategies are constrained to the *documented* lossless subset
(see ``docs/concepts/untp-cirpass-mapping.md``). Inputs outside the
subset are excluded — those are explicitly lossy, not bugs.
"""

from __future__ import annotations

from datetime import datetime, timezone

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from dppvalidator.compat import to_cirpass_1_3, to_untp_0_7

# =============================================================================
# Strategies
# =============================================================================


# Pragmatic identifier characters — alphanumeric + dash + underscore +
# slash + colon. Avoids whitespace + control + characters that would
# break BCP-47 / URI parsing.
_id_chars = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"),
        whitelist_characters="-_/.:",
    ),
    min_size=1,
    max_size=20,
).filter(lambda s: s.strip() == s and not s.startswith("-"))


# Single-language BCP-47 tags drawn from a small set so the round-
# trip can pick the right one deterministically.
_languages = st.sampled_from(["en", "de", "fr", "es", "it", "zh"])


# ISO datetimes in UTC, deterministic format. Avoid microseconds so
# string parsing/round-tripping stays bit-stable.
def _iso_dt(dt: datetime) -> str:
    return dt.replace(microsecond=0, tzinfo=timezone.utc).isoformat()


# Naïve datetime range — 2010-01-01 .. 2050-01-01.
_datetimes = st.datetimes(
    min_value=datetime(2010, 1, 1),
    max_value=datetime(2050, 1, 1),
).map(_iso_dt)


# Two scheme URIs from the bundled lookup that round-trip cleanly.
_scheme_urls = st.sampled_from(
    [
        "https://gs1.org/voc/",
        "https://www.gleif.org/lei/",
        "https://www.iso.org/standard/82220.html",
    ]
)


@st.composite
def cirpass_lossless(draw: st.DrawFn, language: str = "en") -> dict:
    """Strategy: minimal CIRPASS payload from the lossless subset.

    Includes only fields that round-trip identity-preserving:

    - ``dppIdentifier.value`` (string)
    - ``product.productIdentifier.value`` + ``scheme`` (registered)
    - ``product.productName[0]`` (single language)
    - ``issuedAt.timestamp`` (ISO 8601)
    - ``effectivePeriod.start`` + ``end`` (both populated)
    - one related-actor with ManufacturerRole
    """
    # Draw two distinct datetimes so start < end.
    start_str = draw(_datetimes)
    end_str = draw(_datetimes)
    if start_str == end_str:
        # Force ordering — use start as-is and bump end to year 2050.
        end_str = "2050-01-01T00:00:00+00:00"
    if start_str > end_str:
        start_str, end_str = end_str, start_str
    issued_str = start_str  # M07: issuedAt = validFrom
    payload: dict = {
        "dppIdentifier": {
            "value": "https://example.com/dpp/" + draw(_id_chars),
            "scheme": "https://example.com/dpp-register/",
            "schemeName": "DPP register",
        },
        "product": {
            "productIdentifier": {
                "value": draw(_id_chars),
                "scheme": draw(_scheme_urls),
            },
            "productName": [
                {"value": draw(_id_chars), "language": language},
            ],
        },
        "issuedAt": {"timestamp": issued_str},
        "effectivePeriod": {"start": start_str, "end": end_str},
    }
    # Optional: a single related-actor with ManufacturerRole. We
    # always include one so the M12 round-trip path is exercised.
    payload["relatedActors"] = [
        {
            "actor": {
                "actorIdentifier": {
                    "value": draw(_id_chars),
                    "scheme": "https://www.gleif.org/lei/",
                    "schemeName": "GLEIF LEI",
                },
                "actorName": [{"value": draw(_id_chars), "language": language}],
            },
            "role": "eudpp:ManufacturerRole",
        }
    ]
    return payload


# =============================================================================
# Properties
# =============================================================================


@given(cirpass_lossless(language="en"))
@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_cirpass_round_trip_preserves_lossless_subset(payload: dict) -> None:
    """CIRPASS → UNTP → CIRPASS preserves the lossless-subset fields."""
    untp, _ = to_untp_0_7(payload, default_language="en")
    back, _ = to_cirpass_1_3(untp, default_language="en")
    # Lossless invariants:
    assert back["dppIdentifier"]["value"] == payload["dppIdentifier"]["value"]
    assert (
        back["product"]["productIdentifier"]["value"]
        == payload["product"]["productIdentifier"]["value"]
    )
    assert (
        back["product"]["productIdentifier"]["scheme"]
        == payload["product"]["productIdentifier"]["scheme"]
    )
    assert (
        back["product"]["productName"][0]["value"] == payload["product"]["productName"][0]["value"]
    )
    assert (
        back["product"]["productName"][0]["language"]
        == payload["product"]["productName"][0]["language"]
    )
    # M07: issuedAt timestamp round-trips.
    assert back["issuedAt"]["timestamp"] == payload["issuedAt"]["timestamp"]
    # M08: effectivePeriod round-trips.
    assert back["effectivePeriod"]["start"] == payload["effectivePeriod"]["start"]
    assert back["effectivePeriod"]["end"] == payload["effectivePeriod"]["end"]


@st.composite
def untp_lossless(draw: st.DrawFn, language: str = "en") -> dict:
    """Strategy: minimal UNTP DPP payload from the lossless subset."""
    valid_from_str = draw(_datetimes)
    valid_until_str = draw(_datetimes)
    if valid_from_str == valid_until_str:
        valid_until_str = "2050-01-01T00:00:00+00:00"
    if valid_from_str > valid_until_str:
        valid_from_str, valid_until_str = valid_until_str, valid_from_str
    untp = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/dpp/" + draw(_id_chars),
        "name": draw(_id_chars),
        "issuer": {
            "id": "did:web:" + draw(_id_chars) + ".example.com",
            "name": draw(_id_chars),
            "type": ["CredentialIssuer"],
        },
        "validFrom": valid_from_str,
        "validUntil": valid_until_str,
        "credentialSubject": {
            "type": ["Product"],
            "id": draw(_id_chars),
            "name": draw(_id_chars),
            "idScheme": {
                "id": draw(_scheme_urls),
                "name": "Scheme",
            },
            "idGranularity": "model",
            "productCategory": [
                {
                    "schemeId": "https://www.wcoomd.org/",
                    "schemeName": "WCO HS",
                    "code": draw(_id_chars),
                    "name": "Category",
                }
            ],
            "producedAtFacility": {
                "id": "https://example.com/f/" + draw(_id_chars),
                "name": draw(_id_chars),
                "type": ["Facility"],
            },
            "countryOfProduction": {"countryCode": "DE"},
            "materialProvenance": [],
            "relatedParty": [
                {
                    "role": "manufacturer",
                    "party": {
                        "id": "https://example.com/lei/" + draw(_id_chars),
                        "name": draw(_id_chars),
                        "type": ["Party"],
                        "idScheme": {
                            "id": "https://www.gleif.org/lei/",
                            "name": "GLEIF LEI",
                        },
                    },
                }
            ],
        },
    }
    _ = language  # accepted for API symmetry; used below
    return untp


@given(untp_lossless(language="en"))
@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_untp_round_trip_preserves_lossless_subset(payload: dict) -> None:
    """UNTP → CIRPASS → UNTP preserves the lossless-subset fields."""
    cirpass, _ = to_cirpass_1_3(payload, default_language="en")
    back, _ = to_untp_0_7(cirpass, default_language="en")
    assert back["id"] == payload["id"]
    assert back["validFrom"] == payload["validFrom"]
    assert back["validUntil"] == payload["validUntil"]
    assert back["credentialSubject"]["id"] == payload["credentialSubject"]["id"]
    assert (
        back["credentialSubject"]["idScheme"]["id"]
        == payload["credentialSubject"]["idScheme"]["id"]
    )
    # The first manufacturer party's id round-trips through M12.
    assert back["issuer"]["id"] == payload["credentialSubject"]["relatedParty"][0]["party"]["id"]


# =============================================================================
# Determinism property — same input always produces same output
# =============================================================================


@given(cirpass_lossless(language="en"))
@settings(max_examples=50, deadline=None)
def test_reverse_is_pure(payload: dict) -> None:
    """Two consecutive reverse-shim calls produce byte-identical output."""
    a, _ = to_untp_0_7(payload, default_language="en")
    b, _ = to_untp_0_7(payload, default_language="en")
    assert a == b


@given(untp_lossless(language="en"))
@settings(max_examples=50, deadline=None)
def test_forward_is_pure(payload: dict) -> None:
    """Two consecutive forward-shim calls produce byte-identical output."""
    a, _ = to_cirpass_1_3(payload, default_language="en")
    b, _ = to_cirpass_1_3(payload, default_language="en")
    assert a == b
