"""Phase 5 multilingual round-trip integration test.

Asserts that going CIRPASS → UNTP → CIRPASS produces *exactly one*
``MAP001`` warning per dropped language. The reverse shim picks the
``default_language`` entry (or the first if no exact match) and
reports every other language as a separate ``MAP001`` so consumers
can count them deterministically.
"""

from __future__ import annotations

from dppvalidator.compat import (
    MAP_CODE_LOSSY,
    to_cirpass_1_3,
    to_untp_0_7,
)
from dppvalidator.models.cirpass.v1_3 import (
    Identifier,
    IssuedAt,
    LocalisedText,
    Product,
    ReferencePassport,
)
from dppvalidator.models.cirpass.v1_3.temporal import datetime as _dt_module  # noqa: F401


def _three_language_cirpass(*, languages: list[str]) -> dict:
    """Build a CIRPASS payload with one productName entry per language."""
    from datetime import datetime, timezone

    passport = ReferencePassport(
        dppIdentifier=Identifier(
            value="https://example.com/dpp/i18n",
            scheme="https://example.com/dpp-register/",
        ),
        product=Product(
            productIdentifier=Identifier(
                value="01234567890128",
                scheme="https://gs1.org/voc/",
            ),
            productName=[
                LocalisedText(value=f"Name in {lang}", language=lang) for lang in languages
            ],
        ),
        issuedAt=IssuedAt(timestamp=datetime(2026, 5, 8, tzinfo=timezone.utc)),
    )
    return passport.model_dump(by_alias=True, exclude_none=True, mode="json")


# =============================================================================
# Reverse drops every language but the default
# =============================================================================


def test_reverse_drops_each_extra_language_with_one_map001() -> None:
    """3 languages on input → 2 MAP001 warnings on the reverse."""
    cirpass = _three_language_cirpass(languages=["en", "de", "fr"])
    _, warns = to_untp_0_7(cirpass, default_language="en")
    productname_lossy = [
        w
        for w in warns
        if w.code == MAP_CODE_LOSSY
        and "productName" in w.path
        or "credentialSubject.name" in w.path
    ]
    # Exactly 2 dropped languages (de, fr).
    assert len(productname_lossy) == 2
    dropped_langs = {dict(w.details).get("language") for w in productname_lossy}
    assert dropped_langs == {"de", "fr"}


def test_reverse_picks_default_language_when_present() -> None:
    """The kept entry is the one whose language matches default_language."""
    cirpass = _three_language_cirpass(languages=["en", "de", "fr"])
    untp, _ = to_untp_0_7(cirpass, default_language="de")
    # The German entry was kept.
    assert untp["credentialSubject"]["name"] == "Name in de"


def test_reverse_falls_back_to_first_when_default_absent() -> None:
    """When default_language doesn't match any entry, pick the first."""
    cirpass = _three_language_cirpass(languages=["es", "it", "pt"])
    untp, warns = to_untp_0_7(cirpass, default_language="en")
    assert untp["credentialSubject"]["name"] == "Name in es"
    # Two languages were dropped (it, pt) — exactly two MAP001 entries.
    productname_lossy = [
        w
        for w in warns
        if w.code == MAP_CODE_LOSSY
        and "productName" in w.path
        or "credentialSubject.name" in w.path
    ]
    assert len(productname_lossy) == 2


# =============================================================================
# Forward synthesises a single language
# =============================================================================


def test_forward_synthesises_default_language() -> None:
    """Forward shim wraps a UNTP scalar in a single-entry LocalisedText."""
    untp = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/dpp/i18n-fwd",
        "name": "Test",
        "issuer": {"id": "did:web:x", "name": "X", "type": ["CredentialIssuer"]},
        "validFrom": "2026-01-01T00:00:00+00:00",
        "credentialSubject": {
            "type": ["Product"],
            "id": "01234567890128",
            "name": "T-shirt",
            "idScheme": {"id": "https://gs1.org/voc/", "name": "GS1 GTIN"},
            "idGranularity": "model",
            "productCategory": [
                {
                    "schemeId": "https://www.wcoomd.org/",
                    "schemeName": "WCO HS",
                    "code": "61091000",
                    "name": "T-shirts",
                }
            ],
            "producedAtFacility": {
                "id": "https://example.com/f",
                "name": "F",
                "type": ["Facility"],
            },
            "countryOfProduction": {"countryCode": "DE"},
            "materialProvenance": [],
        },
    }
    cirpass, _ = to_cirpass_1_3(untp, default_language="zh-Hant")
    # The forward shim created a single LocalisedText entry with the
    # caller's default_language tag.
    assert cirpass["product"]["productName"] == [{"value": "T-shirt", "language": "zh-Hant"}]


# =============================================================================
# Round-trip — CIRPASS → UNTP → CIRPASS preserves the picked language
# =============================================================================


def test_cirpass_to_untp_to_cirpass_preserves_picked_language() -> None:
    """The single language that survives the UNTP scalar bottleneck
    survives a forward re-projection back into CIRPASS."""
    cirpass = _three_language_cirpass(languages=["en", "de"])
    untp, _ = to_untp_0_7(cirpass, default_language="de")
    back, _ = to_cirpass_1_3(untp, default_language="de")
    # The German name is preserved.
    assert back["product"]["productName"] == [{"value": "Name in de", "language": "de"}]


def test_round_trip_drops_one_language_per_lost_entry() -> None:
    """Counting invariant: the round-trip emits exactly N-1 MAP001
    warnings on the reverse leg, where N is the number of CIRPASS
    multilingual entries."""
    languages = ["en", "de", "fr", "es", "it"]
    cirpass = _three_language_cirpass(languages=languages)
    _, warns = to_untp_0_7(cirpass, default_language="en")
    productname_lossy = [
        w
        for w in warns
        if w.code == MAP_CODE_LOSSY
        and ("productName" in w.path or "credentialSubject.name" in w.path)
    ]
    assert len(productname_lossy) == len(languages) - 1
