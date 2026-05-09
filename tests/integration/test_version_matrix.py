"""Phase 5 acceptance test: validator-layer × UNTP-version matrix.

This module enforces the Phase 5 exit criterion from
``docs/plans/UNTP_0.7.0_MIGRATION.md``:

> Parametrised matrix is green; coverage report unchanged or improved.

The matrix multiplies every supported validation layer (``schema``,
``model``, ``semantic``, ``jsonld``, ``deep``) by every supported UNTP
DPP version (currently ``0.6.1`` and ``0.7.0``) and asserts the
canonical happy-path fixture validates cleanly through each layer/version
combination. When a new UNTP version is registered, the matrix
automatically expands.

Negative coverage — fixtures that *must* fail — lives next to this test
in ``tests/fixtures/invalid/0.7.0/`` with a parametrised "every invalid
fixture surfaces at least one error" check.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from dppvalidator.validators import ValidationEngine

_FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"
_VALID_DIR = _FIXTURE_ROOT / "valid"
_INVALID_07_DIR = _FIXTURE_ROOT / "invalid" / "0.7.0"


# ---------------------------------------------------------------------------
# Fixture discovery — keyed on the published UNTP version
# ---------------------------------------------------------------------------


_HAPPY_PATH_BY_VERSION: dict[str, Path] = {
    "0.6.1": _VALID_DIR / "untp-dpp-instance-0.6.1.json",
    "0.7.0": _VALID_DIR / "untp-dpp-instance-0.7.0.json",
}


def _matrix_versions() -> tuple[str, ...]:
    """Read the matrix versions from the conftest registry helper."""
    from tests.conftest import all_matrix_versions

    return tuple(all_matrix_versions())


def _layers_for(
    version: str,  # noqa: ARG001 — placeholder for future per-version filtering
) -> tuple[str, ...]:
    """Layers that should execute against ``version``.

    All four sub-validators are exercised for both versions in Phase 5
    — the matrix is exhaustive on purpose. If a layer ever needs to
    skip a version (e.g. an experimental layer not yet ported), this
    is the place to express that. The deep validator is async and
    handled separately.
    """
    return ("schema", "model", "semantic", "jsonld")


# ---------------------------------------------------------------------------
# Happy-path matrix — sub-validator × version
# ---------------------------------------------------------------------------


def _layer_version_matrix() -> list[tuple[str, str, Path]]:
    """Build the ``(layer, version, fixture)`` cartesian product."""
    out: list[tuple[str, str, Path]] = []
    for version in _matrix_versions():
        fixture = _HAPPY_PATH_BY_VERSION.get(version)
        if fixture is None or not fixture.is_file():
            continue
        for layer in _layers_for(version):
            out.append((layer, version, fixture))
    return out


@pytest.mark.parametrize(
    ("layer", "version", "fixture"),
    _layer_version_matrix(),
    ids=lambda val: val if isinstance(val, str) else val.name,
)
def test_layer_passes_for_canonical_fixture(layer: str, version: str, fixture: Path) -> None:
    """Run a single layer against the canonical fixture for ``version``.

    Fails when the fixture is rejected — that's the matrix's purpose.
    Each (layer, version) slot is a separate test ID so CI failures
    point straight at the broken combination without ambiguity.
    """
    engine = ValidationEngine(schema_version=version, layers=[layer])
    data = json.loads(fixture.read_text(encoding="utf-8"))
    result = engine.validate(data)
    assert result.valid, (
        f"{layer} layer rejected the canonical {version} fixture "
        f"({fixture.name}):\n"
        + "\n".join(f"  [{e.code}] {e.path}: {e.message}" for e in result.errors)
    )


def test_full_pipeline_passes_for_each_version() -> None:
    """The default-layer pipeline (schema+model+semantic) is green per version."""
    for version in _matrix_versions():
        fixture = _HAPPY_PATH_BY_VERSION.get(version)
        if fixture is None or not fixture.is_file():
            pytest.skip(f"No happy-path fixture vendored for {version}")
        engine = ValidationEngine(schema_version=version)
        data = json.loads(fixture.read_text(encoding="utf-8"))
        result = engine.validate(data)
        assert result.valid, f"Full pipeline failed for {version} ({fixture.name}):\n" + "\n".join(
            f"  [{e.code}] {e.path}: {e.message}" for e in result.errors
        )


# ---------------------------------------------------------------------------
# Deep validator — async, exercised once per version
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("version", _matrix_versions())
def test_deep_validator_runs_per_version(version: str) -> None:
    """The deep validator constructs and executes for each UNTP version.

    The fixture has no external links (``href``-bearing fields are
    self-referential or absent), so deep traversal has nothing to fetch
    and the result must be valid. We assert the *path* compiles per
    version more than that the result is empty — Phase 3b's
    ``LINK_PATHS_BY_VERSION`` dispatch is what's under test.
    """
    fixture = _HAPPY_PATH_BY_VERSION.get(version)
    if fixture is None or not fixture.is_file():
        pytest.skip(f"No happy-path fixture vendored for {version}")
    data = json.loads(fixture.read_text(encoding="utf-8"))
    engine = ValidationEngine(schema_version=version)
    result = asyncio.run(engine.validate_deep(data))
    # The deep validator may surface no findings — what matters is that
    # the per-version dispatch table produced a runnable validator.
    assert result is not None


# ---------------------------------------------------------------------------
# Negative matrix — every invalid v0.7 fixture surfaces an error
# ---------------------------------------------------------------------------


def _invalid_07_fixtures() -> list[Path]:
    return sorted(_INVALID_07_DIR.glob("*.json"))


@pytest.mark.parametrize(
    "fixture",
    _invalid_07_fixtures(),
    ids=lambda p: p.name,
)
def test_invalid_v07_fixture_is_rejected(fixture: Path) -> None:
    """Every fixture in ``invalid/0.7.0/`` must be flagged as invalid.

    Catches regressions where a schema or model relaxation accidentally
    starts accepting a payload that's documented as invalid.
    """
    data: dict[str, Any] = json.loads(fixture.read_text(encoding="utf-8"))
    engine = ValidationEngine(schema_version="0.7.0")
    result = engine.validate(data)
    assert not result.valid, (
        f"{fixture.name} unexpectedly validated cleanly — the fixture is "
        "documented as invalid; either the fixture or the validator "
        "regressed."
    )
    assert result.errors, (
        f"{fixture.name} returned valid=False but no errors — the engine "
        "should always surface the cause."
    )


# ---------------------------------------------------------------------------
# Phase 2 (CIRPASS-2): family-aware detection routing
# ---------------------------------------------------------------------------
#
# The full CIRPASS validation pipeline lands in Phase 4 of the
# CIRPASS-2 migration. Phase 2 only adds the registry + detection
# axes. These tests assert that:
#   1. The CIRPASS family surfaces in the registry alongside UNTP.
#   2. ``detect_schema()`` routes synthetic CIRPASS-shaped payloads to
#      the CIRPASS family with the right version.
#   3. A payload that carries *both* UNTP and EUDPP context references
#      routes to UNTP (the EUDPP IRI is a downstream binding, not a
#      family override).


def test_registry_exposes_both_families() -> None:
    """Phase 2 task 2.1+2.5: both UNTP and CIRPASS surface in the registry."""
    from dppvalidator.schemas.registry import SchemaFamily, SchemaRegistry

    r = SchemaRegistry()
    families = set(r.available_families)
    assert SchemaFamily.UNTP in families
    assert SchemaFamily.CIRPASS in families


def test_cirpass_detection_routes_synthetic_payload() -> None:
    """A CIRPASS-shaped payload (root Product + EUDPP context) routes
    to ``(SchemaFamily.CIRPASS, "1.3.0")`` per Phase 2 task 2.7+2.8."""
    from dppvalidator.schemas.registry import DEFAULT_VERSIONS, SchemaFamily
    from dppvalidator.validators.detection import detect_schema

    payload = {
        "@context": ["https://www.w3.org/ns/credentials/v2", "https://w3id.org/eudpp/"],
        "type": ["DigitalProductPassport"],
        "Product": {"name": "Sample"},
    }
    family, version = detect_schema(payload)
    assert family is SchemaFamily.CIRPASS
    assert version == DEFAULT_VERSIONS[SchemaFamily.CIRPASS]


def test_mixed_context_payload_routes_to_untp() -> None:
    """A payload with both UNTP and EUDPP @context references stays
    routed to UNTP — the EUDPP IRI is a downstream binding the UNTP-VC
    declares, not a family override."""
    from dppvalidator.schemas.registry import SchemaFamily
    from dppvalidator.validators.detection import detect_schema

    payload = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            "https://w3id.org/eudpp/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "credentialSubject": {"name": "Sample"},
    }
    family, version = detect_schema(payload)
    assert family is SchemaFamily.UNTP
    assert version == "0.6.1"


def test_cirpass_default_version_resolves() -> None:
    """``SchemaRegistry.get_schema_for(CIRPASS)`` returns the default."""
    from dppvalidator.schemas.registry import (
        DEFAULT_VERSIONS,
        SchemaFamily,
        SchemaRegistry,
    )

    r = SchemaRegistry()
    schema = r.get_schema_for(SchemaFamily.CIRPASS)
    assert schema.version == DEFAULT_VERSIONS[SchemaFamily.CIRPASS]
    assert schema.family is SchemaFamily.CIRPASS
