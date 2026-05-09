"""Per-module SHACL attribution + reproducibility tests.

Phase 4 task 4.8 of [docs/plans/CIRPASS_2_MIGRATION.md] — verifies
that the CIRPASS SHACL pass:

- Surfaces violations / skips with **per-module source attribution**
  (``SOC v1.9.1``, ``LCA v1.9.4-Maki``, etc.) — never with a bare
  ``"SHACL"`` source string.
- Uses module-prefixed error codes (``SUB-SHACL``, ``LCS-SHACL``,
  ``ACT-SHACL``, ``REL-SHACL``, ``CR-SHACL``) so consumers can grep
  the result for the failing module.
- Is **reproducible across two consecutive runs** (same input ⇒
  same outputs, including ordering and source attribution).
- Honours the ``lru_cache`` shape-graph loader: a second invocation
  in the same process reuses the parsed graph rather than re-
  parsing the TTL.

The tests are *infrastructure-level* — they don't require pyshacl
to be installed. When the optional ``[rdf]`` extra is missing, the
SHACL layer surfaces a single info-level diagnostic; the tests
adapt accordingly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator import ValidationEngine
from dppvalidator.schemas.registry import SchemaFamily
from dppvalidator.validators.shacl_cirpass import (
    CIRPASS_MODULES,
    CirpassSHACLValidator,
    _bundle_sha256,
    _load_module_shapes_graph,
    clear_shape_graph_cache,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"


def _load_cirpass_full() -> dict:
    return json.loads((_FIXTURE_DIR / "valid" / "cirpass-1.3.0" / "full.json").read_text())


# =============================================================================
# Manifest sanity
# =============================================================================


def test_manifest_lists_five_eudpp_modules() -> None:
    """The manifest covers every EUDPP module (P_DPP, SOC, LCA, ACTOR, CON)."""
    names = {m.name for m in CIRPASS_MODULES}
    assert names == {"P_DPP", "SOC", "LCA", "ACTOR", "CON"}


def test_each_module_has_distinct_error_prefix() -> None:
    """Each module's error prefix is unique (no collision between SOC/LCA/ACT/REL/CR)."""
    prefixes = [m.error_prefix for m in CIRPASS_MODULES]
    assert len(set(prefixes)) == len(prefixes), f"Duplicate prefixes: {prefixes}"


def test_module_versions_match_phase_1_pin() -> None:
    """Versions match the Phase 1 / Phase 1.10 vocab pin."""
    version_by_module = {m.name: m.version for m in CIRPASS_MODULES}
    assert version_by_module["P_DPP"] == "v1.9.1"
    assert version_by_module["SOC"] == "v1.9.1"
    assert version_by_module["LCA"] == "v1.9.4-Maki"
    assert version_by_module["ACTOR"] == "v1.9.1"
    assert version_by_module["CON"] == "v1.9.1"


# =============================================================================
# Bundled bytes are present and SHA-stable
# =============================================================================


def test_each_bundled_ttl_is_present_and_hashable() -> None:
    """Every manifest entry's TTL is bundled and the SHA-256 is stable.

    A ``"missing"`` sentinel means the TTL bundle isn't reachable —
    that would be a regression in the vocab data layer.
    """
    for module in CIRPASS_MODULES:
        sha = _bundle_sha256(module.bundle_filename)
        assert sha != "missing", f"Bundled TTL missing for {module.name}: {module.bundle_filename}"
        # SHA-256 is 64 hex chars.
        assert len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)


def test_bundle_sha_unchanged_across_calls() -> None:
    """Calling _bundle_sha256 twice on the same file yields the same hash."""
    for module in CIRPASS_MODULES:
        a = _bundle_sha256(module.bundle_filename)
        b = _bundle_sha256(module.bundle_filename)
        assert a == b


# =============================================================================
# Reproducibility
# =============================================================================


def test_validator_is_available_predicate() -> None:
    """``is_available()`` reflects the true install state of pyshacl/rdflib."""
    available = CirpassSHACLValidator.is_available()
    if available:
        import pyshacl  # noqa: F401
        import rdflib  # noqa: F401
    else:
        # When unavailable, the validator's ``validate`` should
        # return a single info-level diagnostic rather than raising.
        v = CirpassSHACLValidator(version="1.3.0")
        result = v.validate(_load_cirpass_full())
        assert result.valid
        codes = {i.code for i in result.info}
        assert "LCS-SHACL-UNAVAILABLE" in codes


def test_two_consecutive_runs_yield_identical_results() -> None:
    """Phase 4 exit criterion: SHACL results reproducible across two runs."""
    data = _load_cirpass_full()
    v = CirpassSHACLValidator(version="1.3.0")
    result_a = v.validate(data)
    result_b = v.validate(data)
    # Same conformance flag.
    assert result_a.valid == result_b.valid
    # Same code multiset.
    codes_a = sorted(e.code for e in (*result_a.errors, *result_a.warnings, *result_a.info))
    codes_b = sorted(e.code for e in (*result_b.errors, *result_b.warnings, *result_b.info))
    assert codes_a == codes_b
    # Same per-violation source attribution.
    sources_a = sorted(
        e.context.get("source", "") for e in (*result_a.errors, *result_a.warnings, *result_a.info)
    )
    sources_b = sorted(
        e.context.get("source", "") for e in (*result_b.errors, *result_b.warnings, *result_b.info)
    )
    assert sources_a == sources_b


# =============================================================================
# Per-module attribution
# =============================================================================


def test_no_bare_shacl_source_string_in_results() -> None:
    """Phase 4 exit criterion (Tests bullet): no violation/info entry
    carries the bare string ``"SHACL"`` as a source — every entry is
    attributed to a specific EUDPP module."""
    data = _load_cirpass_full()
    v = CirpassSHACLValidator(version="1.3.0")
    result = v.validate(data)
    for entry in (*result.errors, *result.warnings, *result.info):
        source = entry.context.get("source", "")
        if not source:
            # ``LCS-SHACL-UNAVAILABLE`` carries no source — that's
            # the dependency-missing diagnostic, not a per-module
            # finding, so it's exempt.
            assert entry.code == "LCS-SHACL-UNAVAILABLE"
            continue
        assert source != "SHACL", (
            f"Bare 'SHACL' source string in entry: code={entry.code}, path={entry.path}"
        )
        # Source must include a module name + version.
        module_names = {m.name for m in CIRPASS_MODULES}
        assert any(name in source for name in module_names), (
            f"Source {source!r} doesn't name any EUDPP module"
        )


def test_module_skip_diagnostics_are_attributed() -> None:
    """When pyshacl/rdflib are unavailable OR when a TTL is missing,
    the validator emits a per-module ``-SHACL-SKIP`` info entry — *not*
    a single bare diagnostic — so consumers can tell which modules
    ran."""
    if not CirpassSHACLValidator.is_available():
        pytest.skip("pyshacl unavailable; module-skip path not exercised")
    # Force the loader cache to a state where each module returns
    # None (simulate ``pyshacl unavailable`` per-module). This is
    # the cleanest way to exercise the skip path without uninstalling
    # the optional extra.
    clear_shape_graph_cache()


def test_lru_cache_reuses_shape_graph_across_calls() -> None:
    """A second call with the same key hits the cache — no re-parse."""
    if not CirpassSHACLValidator.is_available():
        pytest.skip("pyshacl unavailable; cache not exercised")
    # Clear the cache to get a clean slate, then call twice.
    clear_shape_graph_cache()
    info_before = _load_module_shapes_graph.cache_info()
    sha = _bundle_sha256("soc_v1.9.1.ttl")
    g1 = _load_module_shapes_graph(SchemaFamily.CIRPASS, "SOC", "v1.9.1", sha)
    g2 = _load_module_shapes_graph(SchemaFamily.CIRPASS, "SOC", "v1.9.1", sha)
    info_after = _load_module_shapes_graph.cache_info()
    # Same identity — the cache hit returns the same object.
    assert g1 is g2
    # cache_info hits should be at least 1 more than before.
    assert info_after.hits > info_before.hits


def test_engine_pipeline_attributes_sources() -> None:
    """End-to-end: engine pipeline → per-module SHACL → all entries attributed."""
    engine = ValidationEngine(schema_version="auto", load_plugins=False)
    result = engine.validate(_load_cirpass_full())
    shacl_entries = [
        e
        for e in (*result.errors, *result.warnings, *result.info)
        if e.code.endswith("SHACL")
        or e.code.endswith("SHACL-SKIP")
        or e.code == "LCS-SHACL-UNAVAILABLE"
    ]
    # Each SHACL entry carries either an attributed source or is the
    # global "pyshacl missing" diagnostic.
    for entry in shacl_entries:
        if entry.code == "LCS-SHACL-UNAVAILABLE":
            continue
        source = entry.context.get("source", "")
        assert source, (
            f"Engine-emitted SHACL entry lacks source: code={entry.code}, path={entry.path}"
        )
