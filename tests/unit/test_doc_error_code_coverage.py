"""Docs guard: every emitted error code has a docs page and nav entry.

Phase 7 of the [Docs Coherence Plan]
(../../docs/plans/DOCS_COHERENCE_PLAN.md). This test walks ``src/``
for error-code literals matching the prefixes pinned by
[ADR 0006](../../docs/adr/0006-validation-layer-taxonomy.md) and
asserts:

1. Every emitted code has a corresponding ``docs/errors/<CODE>.md`` page.
2. Every emitted code is listed in ``mkdocs.yml`` under ``nav.Errors``.
3. Every ``docs/errors/<CODE>.md`` page maps back to a code emitted by
   ``src/`` (no orphaned doc pages).

Together with ``tools/check_doc_default_version.py`` and the
``mkdocs build --strict`` gate added in Phase 4, this prevents the
``MOD`` → ``MDL`` style drift that motivated the plan.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Prefix allow-list — every prefix that ADR 0006 names as a valid
# error-code surface. Adding a new prefix means updating this set
# *and* documenting it in ADR 0006.
KNOWN_PREFIXES: frozenset[str] = frozenset(
    {
        # Layered prefixes (Layer 1..6 — Layer 0 detection has no codes
        # of its own; Layer 7 signature codes are reserved).
        "SCH",
        "MDL",
        "JLD",
        "SEM",
        "VOC",
        # Plugin packs.
        "TXT",  # Textile
        "CQ",  # CIRPASS Quality
        "TYR",  # Tyres
        # Non-layer / cross-cutting.
        "PRS",  # Parsing (pre-Layer 1)
        "DET",  # Detection routing
        "VER",  # Version routing
        "UPG",  # 0.6 → 0.7 upgrade shim
        "MAP",  # Cross-family migration shim
        "PRT",  # Advisory rules (Party-Role)
    }
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"
ERRORS_DIR = REPO_ROOT / "docs" / "errors"
MKDOCS_YML = REPO_ROOT / "mkdocs.yml"

# Prefixes we don't expect every code under to have its own docs page.
# Plugin-pack codes (TXT, CQ, TYR) are documented as a group in their
# plugin pages; per-code coverage is enforced by the plugin's own
# integration tests, not this guard. Plugin authors can opt in by
# dropping ``docs/errors/<CODE>.md`` files.
DOCS_OPTIONAL_PREFIXES: frozenset[str] = frozenset({"TXT", "CQ", "TYR"})

# Exclude directories from the source scan.
SKIP_DIR_PARTS = frozenset({"__pycache__", ".pytest_cache", ".ruff_cache", "site"})


# Match a 3-digit code preceded by a known prefix, with both prefix and
# digits as a single token. We require the prefix to be in
# KNOWN_PREFIXES so that random three-letter sequences in test data
# don't trip the scan (e.g. an unrelated "MAY001" identifier).
_CODE_PATTERN = re.compile(r"\b(?P<code>(?:" + "|".join(sorted(KNOWN_PREFIXES)) + r")\d{3})\b")


def _emitted_codes() -> set[str]:
    """Walk ``src/`` for code literals matching :data:`_CODE_PATTERN`."""
    codes: set[str] = set()
    for py in SRC.rglob("*.py"):
        if any(part in SKIP_DIR_PARTS for part in py.parts):
            continue
        text = py.read_text(encoding="utf-8")
        for hit in _CODE_PATTERN.finditer(text):
            codes.add(hit.group("code"))
    return codes


def _doc_codes() -> set[str]:
    """Codes that have a ``docs/errors/<CODE>.md`` page."""
    return {p.stem for p in ERRORS_DIR.glob("*.md") if p.stem != "index"}


def _nav_codes() -> set[str]:
    """Codes referenced by an ``errors/<CODE>.md`` entry in mkdocs nav.

    mkdocs.yml uses ``!!python/name:...`` tag literals that PyYAML's
    SafeLoader rejects. We don't need to evaluate the nav tree
    structurally — a regex over the file is sufficient and side-steps
    the YAML loader entirely.
    """
    text = MKDOCS_YML.read_text(encoding="utf-8")
    return set(re.findall(r"errors/([A-Z]+\d{3})\.md", text))


def _filter_required(codes: set[str]) -> set[str]:
    return {c for c in codes if not any(c.startswith(p) for p in DOCS_OPTIONAL_PREFIXES)}


def test_emitted_codes_have_doc_pages() -> None:
    """Every code emitted by src/ has a docs/errors/<CODE>.md page."""
    emitted = _emitted_codes()
    documented = _doc_codes()
    required = _filter_required(emitted)
    missing = sorted(required - documented)
    assert not missing, (
        f"Codes emitted by src/ but missing docs/errors/<CODE>.md: {missing}. "
        "Either add the page (template: docs/errors/MDL001.md) or, for "
        "plugin-pack prefixes, extend DOCS_OPTIONAL_PREFIXES in this test."
    )


def test_emitted_codes_are_in_mkdocs_nav() -> None:
    """Every code emitted by src/ is listed in mkdocs.yml nav.Errors."""
    emitted = _emitted_codes()
    in_nav = _nav_codes()
    required = _filter_required(emitted)
    missing = sorted(required - in_nav)
    assert not missing, (
        f"Codes emitted by src/ but missing from mkdocs.yml nav.Errors: "
        f"{missing}. Add an entry under the appropriate section "
        "(see Schema/Model/JSON-LD/... groupings)."
    )


def test_no_orphan_doc_pages() -> None:
    """Every docs/errors/<CODE>.md maps to a code emitted by src/."""
    emitted = _emitted_codes()
    documented = _doc_codes()
    orphans = sorted(documented - emitted)
    assert not orphans, (
        f"docs/errors/<CODE>.md pages with no matching emitter in src/: "
        f"{orphans}. Either delete the page or add the emitter."
    )


@pytest.mark.parametrize("code", sorted(KNOWN_PREFIXES))
def test_known_prefixes_match_adr(code: str) -> None:
    """Sanity: the allow-list and ADR 0006's prefix table agree."""
    adr = (REPO_ROOT / "docs" / "adr" / "0006-validation-layer-taxonomy.md").read_text(
        encoding="utf-8"
    )
    assert code in adr, (
        f"prefix {code!r} is in KNOWN_PREFIXES but not mentioned in "
        "docs/adr/0006-validation-layer-taxonomy.md — update either the "
        "ADR or this test's allow-list."
    )
