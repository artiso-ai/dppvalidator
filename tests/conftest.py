"""Shared pytest fixtures for dppvalidator tests.

Phase 5 of ``docs/plans/UNTP_0.7.0_MIGRATION.md`` parametrises the
:func:`valid_dpp_data` fixture over both supported UNTP DPP versions
(0.6.1 and 0.7.0). Tests that need to pin a specific version use the
``@pytest.mark.dpp_version("X.Y.Z")`` marker; tests without a marker
run against both shapes.

The version list is read from the schema registry — adding a new
UNTP version automatically expands the matrix.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from dppvalidator.schemas.registry import SCHEMA_REGISTRY

if TYPE_CHECKING:
    from collections.abc import Iterable

# The matrix used by parametrised fixtures. We surface "0.6.1" + "0.7.0"
# as canonical entries; "0.6.0" stays in the registry but isn't matrix-tested
# because it shares the v0.6 wire shape with 0.6.1 — adding it would
# duplicate every test slot for no extra coverage.
_MATRIX_DPP_VERSIONS: tuple[str, ...] = ("0.6.1", "0.7.0")


def pytest_configure(config: pytest.Config) -> None:
    """Register dppvalidator-specific markers."""
    config.addinivalue_line(
        "markers",
        "dpp_version(version): pin a parametrised dpp fixture to a single "
        "UNTP DPP version. Use to keep a test class scoped to one wire shape "
        "when its assertions are version-specific (Phase 5).",
    )


def _matrix_versions() -> tuple[str, ...]:
    """Return the parametrisation matrix, intersected with the registry.

    Defensive: if a matrix version somehow drops out of the registry
    we'd silently parametrise over a missing schema. This guards against
    that by filtering to the current registry's version set.
    """
    return tuple(v for v in _MATRIX_DPP_VERSIONS if v in SCHEMA_REGISTRY)


@pytest.fixture(params=_matrix_versions(), ids=lambda v: f"v{v}")
def dpp_version(request: pytest.FixtureRequest) -> str:
    """The UNTP DPP version for the current parametrisation slot.

    Tests can pin to a single version with
    ``@pytest.mark.dpp_version("0.6.1")``; non-matching params are
    skipped so the surviving run is single-version. Tests that don't
    apply the marker run twice (once per matrix version).
    """
    marker = request.node.get_closest_marker("dpp_version")
    if marker is not None:
        wanted = marker.args[0] if marker.args else None
        if wanted is not None and wanted != request.param:
            pytest.skip(f"dpp_version({wanted!r}) marker filters out {request.param!r}")
    return request.param


def _v06_payload() -> dict[str, Any]:
    """Minimal valid 0.6.x DPP payload."""
    return {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/credentials/dpp-001",
        "issuer": {
            "id": "https://example.com/issuers/001",
            "name": "Example Company Ltd",
        },
        "validFrom": "2024-01-01T00:00:00Z",
        "validUntil": "2034-01-01T00:00:00Z",
        "credentialSubject": {
            "id": "https://example.com/subject/001",
            "type": ["ProductPassport"],
            "product": {
                "id": "https://example.com/products/001",
                "name": "Example Product",
            },
        },
    }


def _v07_payload() -> dict[str, Any]:
    """Minimal valid 0.7.0 DPP payload.

    Includes every v0.7-required field on Product so the engine's
    model-layer validation passes without modification.
    """
    return {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/credentials/dpp-001",
        "name": "Minimal v0.7 DPP",
        "issuer": {
            "type": ["CredentialIssuer"],
            "id": "did:example:issuer-001",
            "name": "Example Company Ltd",
        },
        "validFrom": "2024-01-01T00:00:00Z",
        "validUntil": "2034-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["Product"],
            "id": "https://example.com/products/001",
            "name": "Example Product",
            "idScheme": {
                "type": ["IdentifierScheme"],
                "id": "https://example.com/schemes/internal",
                "name": "Internal product scheme",
            },
            "idGranularity": "model",
            "productCategory": [
                {
                    "type": ["Classification"],
                    "schemeId": "https://unstats.un.org/unsd/classifications/Econ/cpc/",
                    "schemeName": "UN Central Product Classification",
                    "code": "12345",
                    "name": "Example category",
                }
            ],
            "producedAtFacility": {
                "type": ["Facility"],
                "id": "https://example.com/facilities/001",
                "name": "Example facility",
            },
            "countryOfProduction": {"countryCode": "DE", "countryName": "Germany"},
        },
    }


_PAYLOAD_BY_VERSION: dict[str, Any] = {
    "0.6.1": _v06_payload,
    "0.7.0": _v07_payload,
}


@pytest.fixture
def valid_dpp_data(dpp_version: str) -> dict[str, Any]:
    """Return a minimal valid DPP for the active parametrisation slot.

    Phase 5: this fixture is now parametrised over both supported UNTP
    versions via :func:`dpp_version`. Tests that hardcode a specific
    UNTP version on the engine should pin themselves with
    ``@pytest.mark.dpp_version("X.Y.Z")``.

    The returned payload satisfies:
    - CQ001: Mandatory ESPR attributes (issuer, validFrom, credentialSubject.product[/Product]).
    - CQ016: Validity period (validFrom, validUntil).
    - All v0.7-required Product fields when the version slot is 0.7.0.
    """
    factory = _PAYLOAD_BY_VERSION.get(dpp_version)
    if factory is None:  # pragma: no cover — defensive
        raise RuntimeError(f"No fixture payload registered for {dpp_version!r}")
    return factory()


@pytest.fixture
def valid_dpp_json(valid_dpp_data: dict[str, Any]) -> str:
    """Return :func:`valid_dpp_data` serialised as a JSON string."""
    return json.dumps(valid_dpp_data)


@pytest.fixture
def minimal_dpp_data() -> dict[str, Any]:
    """Return minimal v0.6.x DPP data (may not pass all CIRPASS rules).

    Use this for tests that specifically test partial/incomplete DPPs.
    Pinned to v0.6.x because tests using it typically construct a
    :class:`dppvalidator.models.passport.DigitalProductPassport`
    directly — the top-level alias resolves to the v0.6 model.
    """
    return {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ],
        "id": "https://example.com/credentials/dpp-001",
        "issuer": {
            "id": "https://example.com/issuers/001",
            "name": "Example Company Ltd",
        },
    }


def all_matrix_versions() -> Iterable[str]:
    """Public helper for tests that need to know the matrix versions."""
    return _matrix_versions()
