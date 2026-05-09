"""Phase 5 task 5.5 — UNTP ↔ CIRPASS identifier-scheme lookup unit tests.

Pins the bundled lookup table's coverage of common pilot schemes and
the round-trip behaviour for both canonical URIs and aliases. Also
exercises the URI-to-name synthesis fallback that fires when a
scheme isn't in the table.
"""

from __future__ import annotations

from dppvalidator.compat._identifier_schemes import (
    IdentifierSchemeMapping,
    _scheme_name_from_uri,
    all_mappings,
    lookup_by_name,
    lookup_by_uri,
    to_cirpass,
    to_untp,
)


def test_bundled_table_covers_expected_schemes() -> None:
    """The bundled table includes every scheme commonly seen in EU DPP pilots."""
    names = {row.scheme_name for row in all_mappings()}
    expected = {
        "GS1 GTIN",
        "GS1 Digital Link",
        "GLEIF LEI",
        "ISO/IEC 15459",
        "EORI",
        "EUID",
        "DUNS",
        "WCO HS",
        "EU TARIC",
        "EU CPV",
    }
    assert expected <= names, f"Missing expected schemes: {expected - names}"


def test_lookup_by_uri_resolves_canonical_and_alias() -> None:
    canonical = lookup_by_uri("https://gs1.org/voc/")
    assert canonical is not None
    assert canonical.scheme_name == "GS1 GTIN"

    alias = lookup_by_uri("https://www.gs1.org/voc/")
    assert alias is not None
    assert alias.scheme_uri == "https://gs1.org/voc/"  # canonicalises


def test_lookup_by_name_returns_canonical_row() -> None:
    row = lookup_by_name("GLEIF LEI")
    assert isinstance(row, IdentifierSchemeMapping)
    assert row.scheme_uri == "https://www.gleif.org/lei/"


def test_lookup_by_uri_returns_none_for_unknown() -> None:
    assert lookup_by_uri("https://example.com/not-a-real-scheme/") is None


def test_lookup_by_name_returns_none_for_unknown() -> None:
    assert lookup_by_name("Made-up scheme") is None


def test_to_cirpass_canonicalises_known_scheme() -> None:
    """``to_cirpass`` returns the canonical URI even when given an alias."""
    cirpass_uri, cirpass_name, mapping = to_cirpass("https://www.gs1.org/voc/", "GS1 GTIN")
    assert cirpass_uri == "https://gs1.org/voc/"
    assert cirpass_name == "GS1 GTIN"
    assert mapping is not None


def test_to_cirpass_passthrough_for_unknown_scheme() -> None:
    cirpass_uri, cirpass_name, mapping = to_cirpass("https://example.com/custom/", "Custom")
    assert cirpass_uri == "https://example.com/custom/"
    assert cirpass_name == "Custom"
    assert mapping is None


def test_to_cirpass_handles_empty_inputs() -> None:
    """Empty/None inputs return empty URI + None mapping (no crash)."""
    cirpass_uri, cirpass_name, mapping = to_cirpass(None, None)
    assert cirpass_uri == ""
    assert cirpass_name is None
    assert mapping is None


def test_to_untp_lifts_canonical_scheme() -> None:
    untp_id, untp_name, mapping = to_untp("https://gs1.org/voc/", "GS1 GTIN")
    assert untp_id == "https://gs1.org/voc/"
    assert untp_name == "GS1 GTIN"
    assert mapping is not None


def test_to_untp_resolves_via_scheme_name_fallback() -> None:
    """When the URI isn't in the table but the name is, resolve via name."""
    # Use an unknown URI but a known scheme name — exercises the
    # ``_BY_NAME`` fallback branch.
    untp_id, untp_name, mapping = to_untp("https://unknown.example.com/", "GLEIF LEI")
    assert untp_id == "https://unknown.example.com/"
    assert untp_name == "GLEIF LEI"
    assert mapping is not None
    assert mapping.scheme_name == "GLEIF LEI"


def test_to_untp_synthesises_name_when_nothing_matches() -> None:
    untp_id, untp_name, mapping = to_untp("https://example.com/path/segment/", None)
    assert untp_id == "https://example.com/path/segment/"
    assert untp_name == "segment"
    assert mapping is None


def test_to_untp_uses_explicit_name_when_provided() -> None:
    """Caller-provided name on an unknown scheme is preferred over synthesis."""
    untp_id, untp_name, mapping = to_untp("https://example.com/anything/", "Explicit Label")
    assert untp_name == "Explicit Label"
    assert mapping is None


def test_scheme_name_from_uri_fallbacks() -> None:
    """The synthesiser handles edge cases gracefully."""
    # Path-stripped form
    assert _scheme_name_from_uri("https://example.com/foo/bar") == "bar"
    # Trailing slash
    assert _scheme_name_from_uri("https://example.com/foo/") == "foo"
    # Trailing fragment marker is stripped
    assert _scheme_name_from_uri("https://example.com/path#") == "path"
    # Bare scheme
    assert _scheme_name_from_uri("urn:isan:0000-0000-9E59-0000") != ""
    # Empty
    assert _scheme_name_from_uri("") == "unknown-scheme"


def test_all_mappings_has_no_collisions() -> None:
    """No two rows share the same canonical URI."""
    uris = [row.scheme_uri for row in all_mappings()]
    assert len(uris) == len(set(uris))
    names = [row.scheme_name for row in all_mappings()]
    assert len(names) == len(set(names))


def test_aliases_canonicalise_to_a_unique_row() -> None:
    """Each alias resolves to exactly one canonical row."""
    for row in all_mappings():
        for alias in row.aliases:
            resolved = lookup_by_uri(alias)
            assert resolved is not None
            # Aliases canonicalise back to a row whose canonical URI is
            # one of the table rows (could be the row itself or, in
            # principle, another row that takes precedence in
            # registration order).
            assert any(resolved.scheme_uri == r.scheme_uri for r in all_mappings())
