"""Phase 3b acceptance tests: version-keyed deep-validation paths.

This module covers the ``LINK_PATHS_BY_VERSION`` half of Phase 3b
(``docs/plans/UNTP_0.7.0_MIGRATION.md``):

1. The dispatch table covers every key in :data:`SCHEMA_REGISTRY`.
2. :class:`DeepValidator` selects the correct path list when
   ``follow_links`` is left at the default ``None``.
3. The ``[*]`` list-iteration token in v0.7 paths is normalised correctly
   by ``_get_urls_at_path`` — paths like
   ``credentialSubject.performanceClaim[*].evidence`` extract URLs from
   every element of the list.
4. Backward-compat: the legacy ``DEFAULT_LINK_PATHS`` constant still
   imports and matches the v0.6.1 list byte-for-byte.

The crawl integration test (full async traversal) lives elsewhere — this
module exercises the *path table* without touching the network.
"""

from __future__ import annotations

import pytest

from dppvalidator.schemas.registry import SCHEMA_REGISTRY
from dppvalidator.validators.deep import (
    DEFAULT_LINK_PATHS,
    LINK_PATHS_BY_VERSION,
    DeepValidator,
)

# ---------------------------------------------------------------------------
# 1. Dispatch-table consistency
# ---------------------------------------------------------------------------


class TestLinkPathDispatchConsistency:
    """``LINK_PATHS_BY_VERSION`` must cover every registered version."""

    def test_every_registered_version_has_paths(self) -> None:
        missing = sorted(set(SCHEMA_REGISTRY) - set(LINK_PATHS_BY_VERSION))
        assert not missing, (
            f"LINK_PATHS_BY_VERSION is missing {missing}. "
            "Add entries in src/dppvalidator/validators/deep.py."
        )

    def test_no_orphan_path_lists(self) -> None:
        extra = sorted(set(LINK_PATHS_BY_VERSION) - set(SCHEMA_REGISTRY))
        assert not extra, f"LINK_PATHS_BY_VERSION has entries {extra} not in SCHEMA_REGISTRY."

    def test_v07_paths_use_new_envelope_shape(self) -> None:
        """v0.7 paths target the new envelope (no ``credentialSubject.product`` traversal)."""
        v07_paths = LINK_PATHS_BY_VERSION["0.7.0"]
        # Every path roots at credentialSubject directly (not credentialSubject.product).
        for p in v07_paths:
            assert "credentialSubject.product." not in p, (
                f"v0.7 path uses the v0.6 envelope shape: {p!r}"
            )

    def test_v06_paths_unchanged(self) -> None:
        """v0.6 paths must not have drifted — they're a backward-compat surface."""
        assert LINK_PATHS_BY_VERSION["0.6.1"] == [
            "credentialSubject.traceabilityEvents",
            "credentialSubject.conformityClaim",
            "credentialSubject.product.traceabilityInfo",
            "credentialSubject.materialsProvenance",
        ]


# ---------------------------------------------------------------------------
# 2. DEFAULT_LINK_PATHS backward-compat
# ---------------------------------------------------------------------------


def test_default_link_paths_matches_v0_6_1() -> None:
    """The old ``DEFAULT_LINK_PATHS`` constant still resolves to the v0.6.1 list.

    Anyone who imported it pre-Phase-3b sees the same value, just sourced
    from the dispatch table now.
    """
    assert LINK_PATHS_BY_VERSION["0.6.1"] == DEFAULT_LINK_PATHS


# ---------------------------------------------------------------------------
# 3. DeepValidator picks the right paths per version
# ---------------------------------------------------------------------------


class TestDeepValidatorVersionDispatch:
    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("0.6.0", LINK_PATHS_BY_VERSION["0.6.0"]),
            ("0.6.1", LINK_PATHS_BY_VERSION["0.6.1"]),
            ("0.7.0", LINK_PATHS_BY_VERSION["0.7.0"]),
        ],
    )
    def test_default_follow_links_per_version(self, version: str, expected: list[str]) -> None:
        validator = DeepValidator(schema_version=version, max_depth=0)
        assert validator.follow_links == expected
        assert validator.schema_version == version

    def test_explicit_follow_links_override(self) -> None:
        custom = ["credentialSubject.id"]
        validator = DeepValidator(
            schema_version="0.7.0",
            follow_links=custom,
            max_depth=0,
        )
        assert validator.follow_links is custom

    def test_unknown_version_falls_back_to_default(self) -> None:
        validator = DeepValidator(schema_version="9.9.9", max_depth=0)
        assert validator.follow_links == DEFAULT_LINK_PATHS


# ---------------------------------------------------------------------------
# 4. ``[*]`` list-iteration token handling
# ---------------------------------------------------------------------------


class TestStarTokenHandling:
    """The ``[*]`` token in v0.7 paths must not break path traversal."""

    @pytest.fixture
    def validator(self) -> DeepValidator:
        return DeepValidator(schema_version="0.7.0", max_depth=0)

    def test_star_in_path_extracts_from_every_list_element(self, validator: DeepValidator) -> None:
        """``performanceClaim[*].evidence[*].linkURL`` extracts URLs from each row."""
        data = {
            "credentialSubject": {
                "performanceClaim": [
                    {
                        "evidence": [
                            {"linkURL": "https://example.com/evidence/a.pdf"},
                            {"linkURL": "https://example.com/evidence/b.pdf"},
                        ],
                    },
                    {
                        "evidence": [
                            {"linkURL": "https://example.com/evidence/c.pdf"},
                        ],
                    },
                ],
            },
        }
        urls = validator._get_urls_at_path(data, "credentialSubject.performanceClaim[*].evidence")
        assert sorted(urls) == [
            "https://example.com/evidence/a.pdf",
            "https://example.com/evidence/b.pdf",
            "https://example.com/evidence/c.pdf",
        ]

    def test_star_normalises_to_implicit_iteration(self, validator: DeepValidator) -> None:
        """``foo[*].bar`` and ``foo.bar`` produce the same result.

        The ``[*]`` token is purely a readability aid; the underlying
        resolver iterates lists implicitly.
        """
        data = {
            "credentialSubject": {
                "relatedParty": [
                    {"party": {"id": "https://example.com/party/1"}},
                    {"party": {"id": "https://example.com/party/2"}},
                ],
            },
        }
        with_star = validator._get_urls_at_path(data, "credentialSubject.relatedParty[*].party.id")
        without_star = validator._get_urls_at_path(data, "credentialSubject.relatedParty.party.id")
        assert with_star == without_star
        assert sorted(with_star) == [
            "https://example.com/party/1",
            "https://example.com/party/2",
        ]

    def test_v07_relatedDocument_extraction(self, validator: DeepValidator) -> None:
        """The simple ``credentialSubject.relatedDocument`` v0.7 path works."""
        data = {
            "credentialSubject": {
                "relatedDocument": [
                    {"linkURL": "https://example.com/spec.pdf", "name": "Spec"},
                    {"linkURL": "https://example.com/care.pdf", "name": "Care"},
                ],
            },
        }
        urls = validator._get_urls_at_path(data, "credentialSubject.relatedDocument")
        assert sorted(urls) == [
            "https://example.com/care.pdf",
            "https://example.com/spec.pdf",
        ]


# ---------------------------------------------------------------------------
# 5. Empty-data robustness
# ---------------------------------------------------------------------------


def test_extract_links_handles_empty_payload() -> None:
    """The crawler returns no links for an empty document."""
    validator = DeepValidator(schema_version="0.7.0", max_depth=0)
    links = validator._extract_links({}, depth=0)
    assert links == []


def test_extract_links_skips_missing_paths() -> None:
    """Paths that don't resolve in the payload don't error — just yield no links."""
    validator = DeepValidator(schema_version="0.7.0", max_depth=0)
    data = {"credentialSubject": {"id": "https://example.com/p/1"}}
    # Only ``credentialSubject`` is populated; the v0.7 paths target deeper
    # fields that aren't in this minimal doc. Should yield no links, no errors.
    links = validator._extract_links(data, depth=0)
    assert links == []
