"""Guard test: every emitted EUDPP IRI uses the canonical ``w3id.org/eudpp/`` prefix.

Phase 1 of [docs/plans/CIRPASS_2_MIGRATION.md](../../docs/plans/CIRPASS_2_MIGRATION.md)
rebased the EUDPP namespace onto the canonical W3ID prefix
(``https://w3id.org/eudpp/``), per ADR 0002 — replacing the per-publisher
hosts ``http://dpp.taltech.ee/EUDPP#`` and ``http://dpp.cea.fr/EUDPP/LCA#``
that earlier releases shipped.

This test enforces the rebase by failing whenever a Python source file
under ``src/dppvalidator/`` re-introduces the legacy hosts as bare
strings. The schema-data files (``vocabularies/data/schemas/cirpass_dpp_*``)
are vendored spec exports from the v1.7.1-era hub release and are
exempt — they will be replaced when Phase 1 task 1.1 vendors the
v1.9.1 TTLs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from dppvalidator.vocabularies.ontology import EUDPPNamespace, get_eudpp_context

# Legacy host substrings that must not appear in committed Python source.
_LEGACY_HOSTS = (
    "dpp.taltech.ee",
    "dpp.cea.fr",
)

# Canonical EUDPP root. Term IRIs use the fragment form
# ``https://w3id.org/eudpp#<term>``; document IRIs (used in
# ``MANIFEST.json::canonical_iri``) use the path form
# ``https://w3id.org/eudpp/<MODULE>``. Both share the prefix below
# (no trailing separator) so a single ``startswith`` check covers both.
_CANONICAL_PREFIX = "https://w3id.org/eudpp"
# Specifically the term namespace — what ``EUDPPNamespace.EUDPP`` binds.
_CANONICAL_TERM_NAMESPACE = "https://w3id.org/eudpp#"

# Files exempted from the legacy-host scan because their docstrings
# legitimately *explain* the rebase. Adding a file here is rarely the
# right answer — prefer rephrasing prose to drop the literal — but the
# rebase-source files (where the migration is documented) are stable
# exemptions.
_DOC_EXEMPT_FILES: frozenset[Path] = frozenset(
    {
        Path("src/dppvalidator/vocabularies/ontology.py"),
        Path("src/dppvalidator/vocabularies/eudpp_lca.py"),
    }
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_namespace_enum_uses_canonical_term_namespace() -> None:
    """``EUDPPNamespace.EUDPP`` binds the canonical fragment term namespace.

    Phase 1 vendored TTLs confirmed every EUDPP class/property IRI lives
    in the single namespace ``https://w3id.org/eudpp#``. The previous
    Phase 1 design exposed per-module enum members
    (P_DPP/SOC/ACTOR/CON/LCA) as alleged module-scoped namespaces;
    that was incorrect — the modules are separate ontology *documents*
    that share this one term namespace, not independent class-IRI
    prefixes. The enum carries one canonical EUDPP entry only.
    """
    assert EUDPPNamespace.EUDPP.value == _CANONICAL_TERM_NAMESPACE


def test_eudpp_context_emits_canonical_term_namespace() -> None:
    """``get_eudpp_context()`` emits the canonical fragment IRI for every EUDPP-aliased prefix."""
    ctx = get_eudpp_context()
    # ``eudpp:`` is the primary compact prefix; ``lca:`` is registered
    # as a human-readability alias for the same namespace (the LCA TTL
    # itself binds ``ns1: <https://w3id.org/eudpp#>``).
    for prefix in ("eudpp", "lca"):
        assert prefix in ctx, f"missing prefix {prefix!r} in EUDPP context"
        assert ctx[prefix] == _CANONICAL_TERM_NAMESPACE, (
            f"{prefix} → {ctx[prefix]!r} should equal {_CANONICAL_TERM_NAMESPACE!r}"
        )


def test_no_legacy_hosts_in_python_source() -> None:
    """No Python source file under ``src/dppvalidator/`` references legacy EUDPP hosts.

    Vendored spec data (TTL/JSON Schema under ``vocabularies/data/``) is
    exempt — those are upstream artefacts frozen at the v1.7.1-era
    release and get replaced by Phase 1 task 1.1.
    """
    root = _project_root()
    src = root / "src" / "dppvalidator"
    pattern = re.compile("|".join(re.escape(h) for h in _LEGACY_HOSTS))
    violations: list[tuple[Path, int, str]] = []
    for path in sorted(src.rglob("*.py")):
        rel = path.relative_to(root)
        if rel in _DOC_EXEMPT_FILES:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern.search(line):
                violations.append((rel, lineno, line.strip()))
    if violations:
        pretty = "\n".join(f"  {p}:{n}: {line[:100]}" for p, n, line in violations)
        pytest.fail(
            f"\n{len(violations)} legacy EUDPP-host reference(s) found in src/.\n"
            f"Phase 1 of the CIRPASS-2 migration rebased these onto the "
            f"canonical {_CANONICAL_PREFIX!r} prefix (ADR 0002).\n"
            f"\nViolations:\n{pretty}\n"
        )


# Names that Phase 1 task 1.5 deleted. Re-introducing them would
# silently re-conflate CIRPASS messages with EUDPP axioms (G6 fix).
# Detection is line-anchored — definitions are caught while string
# mentions in docstrings are not.
_DELETED_ALIAS_DEFINITIONS = (
    # ``CIRPASSNamespace = ...`` re-aliasing
    re.compile(r"^\s*CIRPASSNamespace\s*=", re.MULTILINE),
    # ``def get_cirpass_context(`` / ``def expand_cirpass_uri(`` /
    # ``def compact_cirpass_uri(``
    re.compile(
        r"^\s*def\s+(get_cirpass_context|expand_cirpass_uri|compact_cirpass_uri)\s*\(", re.MULTILINE
    ),
)


def test_deleted_aliases_not_reintroduced() -> None:
    """Phase 1 task 1.5 deleted four CIRPASS/EUDPP aliases. Guard against re-add.

    The deleted symbols were ``CIRPASSNamespace``, ``get_cirpass_context``,
    ``expand_cirpass_uri``, and ``compact_cirpass_uri``. Their removal is
    a deliberate consequence of ADR 0002 (canonical W3ID rebase) and the
    G6 message/axiom disambiguation. This guard fails if any source
    module re-defines them — the right move is to use the canonical
    ``_eudpp_`` surface and let downstream consumers call that.
    """
    root = _project_root()
    src = root / "src" / "dppvalidator"
    violations: list[tuple[Path, int, str]] = []
    for path in sorted(src.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for pattern in _DELETED_ALIAS_DEFINITIONS:
            for match in pattern.finditer(text):
                # Locate the line number of the match.
                lineno = text.count("\n", 0, match.start()) + 1
                line = text.splitlines()[lineno - 1] if lineno - 1 < len(text.splitlines()) else ""
                violations.append((path.relative_to(root), lineno, line.strip()))
    if violations:
        pretty = "\n".join(f"  {p}:{n}: {line[:100]}" for p, n, line in violations)
        pytest.fail(
            f"\n{len(violations)} re-introduction(s) of a deleted CIRPASS alias.\n"
            f"Phase 1 task 1.5 removed CIRPASSNamespace and three "
            f"_cirpass_ functions in favour of the canonical _eudpp_ "
            f"surface. Don't add them back — call the EUDPP-named "
            f"alternative.\n\nViolations:\n{pretty}\n"
        )
