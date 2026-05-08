"""Phase 3c acceptance tests: per-version ``TermMapping`` columns.

This module covers the ontology half of Phase 3c (see
``docs/plans/UNTP_0.7.0_MIGRATION.md``):

1. ``TermMapping.term_for(version)`` resolves the correct spelling per
   version. Renames (``serialNumber`` → ``itemNumber``, ``producedByParty``
   → ``relatedParty``, ``granularityLevel`` → ``idGranularity``,
   ``materialsProvenance`` → ``materialProvenance``,
   ``conformityClaim`` → ``performanceClaim``) round-trip.
2. The :data:`TERM_REMOVED` sentinel collapses to ``None`` when consulted
   per-version: ``gtin`` is gone in v0.7.
3. :class:`OntologyMapper` exposes the right per-version forward index via
   :meth:`mapped_terms_for` and :meth:`find_mapping_for_term`.
4. The default (no-version) API still returns the v0.6 canonical spelling
   so pre-Phase-3c callers and the existing test suite are unaffected.
"""

from __future__ import annotations

import pytest

from dppvalidator.vocabularies.ontology import (
    TERM_MAPPINGS,
    TERM_REMOVED,
    OntologyMapper,
    TermMapping,
)

# ---------------------------------------------------------------------------
# 1. TermMapping.term_for() resolution
# ---------------------------------------------------------------------------


class TestTermMappingPerVersion:
    """The new ``term_for()`` method resolves to the right spelling."""

    @pytest.mark.parametrize(
        ("v06", "v07"),
        [
            ("serialNumber", "itemNumber"),
            ("granularityLevel", "idGranularity"),
            ("producedByParty", "relatedParty"),
            ("materialsProvenance", "materialProvenance"),
            ("conformityClaim", "performanceClaim"),
        ],
    )
    def test_renames_round_trip(self, v06: str, v07: str) -> None:
        """Renamed fields resolve to the new spelling under v0.7."""
        mapper = OntologyMapper()
        # Forward look-up by the v0.6 canonical key still works.
        mapping = mapper.get_mapping(v06)
        assert mapping is not None, f"missing mapping for v0.6 term {v06!r}"
        assert mapping.term_for("0.6.1") == v06
        assert mapping.term_for("0.6.0") == v06
        assert mapping.term_for("0.7.0") == v07

    def test_unchanged_fields_resolve_to_canonical(self) -> None:
        """Fields with no version-specific rename use ``untp_term`` for both."""
        mapping = next(m for m in TERM_MAPPINGS if m.untp_term == "validFrom")
        assert mapping.term_for("0.6.1") == "validFrom"
        assert mapping.term_for("0.7.0") == "validFrom"

    def test_unknown_version_falls_back_to_canonical(self) -> None:
        """Forward-compat: an unrecognised version returns the canonical spelling."""
        mapping = next(m for m in TERM_MAPPINGS if m.untp_term == "name")
        assert mapping.term_for("9.9.9") == "name"


class TestTermRemovedSentinel:
    """``TERM_REMOVED`` collapses to ``None`` when resolving per-version."""

    def test_gtin_removed_in_v07(self) -> None:
        """``gtin`` exists in v0.6 but is removed in v0.7."""
        mapping = next(m for m in TERM_MAPPINGS if m.untp_term == "gtin")
        assert mapping.term_for("0.6.1") == "gtin"
        assert mapping.term_for("0.7.0") is None
        # Sentinel is exposed for explicit comparison.
        assert mapping.untp_v0_7 == TERM_REMOVED

    def test_term_removed_value_is_a_string_marker(self) -> None:
        """The sentinel is a string so ``slots=True`` types stay clean."""
        assert isinstance(TERM_REMOVED, str)
        assert TERM_REMOVED.startswith("<") and TERM_REMOVED.endswith(">")


# ---------------------------------------------------------------------------
# 2. OntologyMapper version-keyed lookup
# ---------------------------------------------------------------------------


class TestOntologyMapperVersionDispatch:
    """``OntologyMapper`` per-version forward index."""

    def test_mapped_terms_for_v06_includes_gtin(self) -> None:
        mapper = OntologyMapper()
        terms = mapper.mapped_terms_for("0.6.1")
        assert "gtin" in terms
        assert "serialNumber" in terms

    def test_mapped_terms_for_v07_excludes_gtin_renames_serialNumber(self) -> None:
        mapper = OntologyMapper()
        terms = mapper.mapped_terms_for("0.7.0")
        assert "gtin" not in terms, "gtin must be excluded from the v0.7 index"
        assert "serialNumber" not in terms, "serialNumber → itemNumber rename"
        assert "itemNumber" in terms
        assert "materialProvenance" in terms
        assert "performanceClaim" in terms

    def test_find_mapping_for_term_with_v07_spelling(self) -> None:
        """Looking up ``itemNumber`` (v0.7 spelling) returns the same row as ``serialNumber`` (v0.6)."""
        mapper = OntologyMapper()
        v06 = mapper.find_mapping_for_term("serialNumber", version="0.6.1")
        v07 = mapper.find_mapping_for_term("itemNumber", version="0.7.0")
        assert v06 is not None and v07 is not None
        assert v06 is v07, "both version-spellings must resolve to the same TermMapping row"

    def test_find_mapping_default_falls_back_to_v07(self) -> None:
        """Without an explicit ``version``, v0.7-only spellings still resolve.

        This keeps ``find_mapping_for_term('itemNumber')`` working for callers
        who don't yet pass a version argument.
        """
        mapper = OntologyMapper()
        result = mapper.find_mapping_for_term("itemNumber")
        assert result is not None
        assert result.cirpass_uri == "eudpp:uniqueProductID"

    def test_to_untp_with_version_returns_correct_spelling(self) -> None:
        """``to_untp(uri, version)`` returns the spelling for the given version."""
        mapper = OntologyMapper()
        uri = "eudpp:uniqueProductID"
        assert mapper.to_untp(uri, version="0.6.1") == "serialNumber"
        assert mapper.to_untp(uri, version="0.7.0") == "itemNumber"

    def test_to_untp_with_version_returns_none_for_removed_terms(self) -> None:
        """``to_untp`` returns ``None`` when the term is removed in that version."""
        mapper = OntologyMapper()
        # ``eudpp:GTIN`` was the v0.6 ``gtin`` field; gone in v0.7.
        assert mapper.to_untp("eudpp:GTIN", version="0.6.1") == "gtin"
        assert mapper.to_untp("eudpp:GTIN", version="0.7.0") is None

    def test_to_untp_without_version_preserves_legacy_behaviour(self) -> None:
        """No-version call returns the canonical (v0.6) spelling."""
        mapper = OntologyMapper()
        # Legacy callers (pre-Phase-3c) get the same result they always did.
        assert mapper.to_untp("eudpp:uniqueProductID") == "serialNumber"
        assert mapper.to_untp("eudpp:GTIN") == "gtin"


# ---------------------------------------------------------------------------
# 3. Backward compatibility: pre-Phase-3c API surface
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Pre-Phase-3c callers and tests must keep working."""

    def test_to_cirpass_unchanged(self) -> None:
        mapper = OntologyMapper()
        assert mapper.to_cirpass("Product") == "eudpp:Product"
        assert mapper.to_cirpass("serialNumber") == "eudpp:uniqueProductID"
        assert mapper.to_cirpass("nope") is None

    def test_mapping_count_includes_v07_only_rows(self) -> None:
        """The mapping count reflects the table size — including new rows added in Phase 3c."""
        mapper = OntologyMapper()
        # Phase 3c added 2 new rows (materialsProvenance, conformityClaim).
        assert mapper.mapping_count == len(TERM_MAPPINGS)

    def test_mapped_terms_default_returns_canonical_spellings(self) -> None:
        mapper = OntologyMapper()
        # Default ``mapped_terms`` is keyed on the canonical (v0.6) spelling.
        assert "serialNumber" in mapper.mapped_terms
        assert "itemNumber" not in mapper.mapped_terms

    def test_termmapping_dataclass_is_frozen_and_slotted(self) -> None:
        """The dataclass shape is part of the public contract."""
        from dataclasses import FrozenInstanceError

        m = TermMapping(untp_term="x", cirpass_uri="eudpp:y", description="z")
        with pytest.raises(FrozenInstanceError):
            m.untp_term = "mutated"  # type: ignore[misc]
