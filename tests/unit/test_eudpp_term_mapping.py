"""Phase 1 deliverable: every TERM_MAPPINGS row resolves to a real ontology IRI.

Per [docs/plans/CIRPASS_2_MIGRATION.md] §Phase 1 Tests, this guard
loads every bundled v1.9.1 EUDPP TTL into a single rdflib graph and
asserts that each row of
:data:`dppvalidator.vocabularies.ontology.TERM_MAPPINGS` (whose
``cirpass_uri`` expands under :class:`EUDPPNamespace`) corresponds to a
real ontology resource (``owl:Class``, ``owl:ObjectProperty``,
``owl:DatatypeProperty``, ``rdfs:Class``, or ``rdf:Property``) in the
graph.

Behaviour during the Phase 1 transition window:

- *Strict path* — runs only when at least one v1.9.1 TTL is in the
  bundled ontology directory. Missing rows produce a clear pytest
  failure with the unmapped IRIs listed.
- *Legacy fallback* — when only pre-1.9 TTLs are present (the current
  state until Phase 1.1 vendors v1.9.1), the test calls
  ``pytest.skip`` with a message pointing at the migration plan. This
  prevents the test from blocking the bytes-independent half of
  Phase 1 while still failing loudly the moment v1.9.1 TTLs land
  without matching mapping coverage.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dppvalidator.vocabularies.ontology import (
    TERM_MAPPINGS,
    TRANSITIONAL_EUDPP_REMOVED_IN_V1_9,
    EUDPPNamespace,
    expand_eudpp_uri,
)

pytest.importorskip("rdflib")

# ruff: noqa: E402 — imports below the pytest skip-import are intentional.
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ONTOLOGY_DIR = _REPO_ROOT / "src" / "dppvalidator" / "vocabularies" / "data" / "ontologies"

# Filename pattern the v1.9.x EUDPP TTLs are vendored as. The presence of
# *any* matching file flips the test from "skip during transition" to
# "strict, fail-loud".
_V19_FILENAME_GLOB = "*_v1.9*.ttl"

# RDF types accepted as a successful resolution for a mapping row.
_TYPES_OK: frozenset[URIRef] = frozenset(
    {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, RDFS.Class, RDF.Property}
)


def _bundled_v19_ttls() -> list[Path]:
    """Return any v1.9-versioned TTL bundled under the ontology dir."""
    if not _ONTOLOGY_DIR.is_dir():
        return []
    return sorted(_ONTOLOGY_DIR.glob(_V19_FILENAME_GLOB))


def _load_graph(paths: list[Path]) -> Graph:
    """Merge every TTL into a single rdflib graph for cross-module lookups."""
    graph = Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def _is_eudpp_compact(uri: str) -> bool:
    """Return True for compact URIs whose prefix maps to an EUDPP module."""
    if ":" not in uri:
        return False
    prefix = uri.split(":", 1)[0].lower()
    eudpp_prefixes = {ns.name.lower() for ns in EUDPPNamespace} & {
        "eudpp",
        "p_dpp",
        "soc",
        "lca",
        "actor",
        "con",
    }
    return prefix in eudpp_prefixes


def test_every_eudpp_term_mapping_resolves_in_bundled_ttl() -> None:
    """Strict gate (post-Phase 1.1): every EUDPP-prefixed mapping resolves."""
    ttl_files = _bundled_v19_ttls()
    if not ttl_files:
        pytest.skip(
            "Phase 1 transition window: no v1.9.x EUDPP TTLs bundled yet "
            "(see docs/plans/CIRPASS_2_MIGRATION.md task 1.1). "
            "This test flips to strict once v1.9.1 TTLs land."
        )

    graph = _load_graph(ttl_files)

    eudpp_rows = [m for m in TERM_MAPPINGS if _is_eudpp_compact(m.cirpass_uri)]
    assert eudpp_rows, "TERM_MAPPINGS has no EUDPP-prefixed rows — registry unwired?"

    unresolved: list[tuple[str, str]] = []
    for mapping in eudpp_rows:
        # Phase 1 task 1.6 audit: a small allow-list of v1.7.1-era
        # predicates retained in TERM_MAPPINGS for v0.6↔v0.7 UNTP
        # rename round-trip but with no v1.9.1 EUDPP equivalent.
        if mapping.cirpass_uri in TRANSITIONAL_EUDPP_REMOVED_IN_V1_9:
            continue
        full_iri = expand_eudpp_uri(mapping.cirpass_uri)
        # Accept both fragment (``#``) and path (``/``) continuations:
        # term IRIs use the former, document IRIs the latter. A bare
        # ``https://w3id.org/eudpp`` prefix without separator means the
        # compact prefix wasn't in :class:`EUDPPNamespace` and
        # ``expand_eudpp_uri`` returned the input unchanged.
        if not full_iri.startswith("https://w3id.org/eudpp"):
            unresolved.append((mapping.cirpass_uri, "compact prefix has no namespace"))
            continue

        ref = URIRef(full_iri)
        types = {t for t in graph.objects(ref, RDF.type) if isinstance(t, URIRef)}
        if not types & _TYPES_OK:
            unresolved.append((mapping.cirpass_uri, full_iri))

    if unresolved:
        rendered = "\n".join(f"  {compact} → {target}" for compact, target in unresolved)
        pytest.fail(
            f"\n{len(unresolved)} EUDPP TERM_MAPPINGS row(s) do not resolve to a "
            f"class or property in the bundled v1.9 TTLs:\n{rendered}\n\n"
            f"Either the TERM_MAPPINGS row references a renamed/removed class "
            f"(update or remove the row), or the bundle is missing the module "
            f"that defines it (Phase 1 task 1.1)."
        )


def test_term_mappings_table_uses_canonical_compact_prefixes() -> None:
    """Every EUDPP-namespaced row in TERM_MAPPINGS uses a known compact prefix.

    This guard runs unconditionally — it doesn't need a v1.9 TTL on disk;
    it only needs the ``EUDPPNamespace`` registry to know the legal
    prefixes. Catches typos like ``eupdd:Foo`` or hand-edited rows that
    skip the canonical W3ID prefix per ADR 0002.
    """
    legal_prefixes = {
        ns.name.lower()
        for ns in EUDPPNamespace
        # Only EUDPP-module prefixes; SI / QUDT / etc. are tracked
        # separately and TERM_MAPPINGS rows shouldn't carry their compact
        # forms.
        if ns.name.lower() in {"eudpp", "p_dpp", "soc", "lca", "actor", "con"}
    }
    bad: list[str] = []
    for mapping in TERM_MAPPINGS:
        if ":" not in mapping.cirpass_uri:
            bad.append(f"{mapping.untp_term} → {mapping.cirpass_uri} (no prefix)")
            continue
        prefix = mapping.cirpass_uri.split(":", 1)[0].lower()
        if prefix not in legal_prefixes and prefix not in {"si", "qudt", "schema", "gs1", "untp"}:
            bad.append(f"{mapping.untp_term} → {mapping.cirpass_uri} (unknown prefix {prefix!r})")
    assert not bad, "TERM_MAPPINGS rows with unrecognised compact prefixes:\n  " + "\n  ".join(bad)
