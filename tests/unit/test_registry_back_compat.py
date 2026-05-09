"""Phase 2 task 2.3 — bare-string registry lookup keeps working in 0.4.z.

The migration plan promises (cardinal rule §5: coexist-before-cut) that
pre-Phase-2 callers using the bare-string ``SCHEMA_REGISTRY[version]``
form keep working unchanged in ``0.4.z``. The two-axis tuple-keyed
registry introduced in Phase 2 is the new source of truth; the
bare-string ``SCHEMA_REGISTRY`` and ``DEFAULT_SCHEMA_VERSION`` constants
are derived views that filter to the UNTP family.

Phase 9 task 9.4 will activate a ``DeprecationWarning`` on the
bare-string surface; Phase 10 removes it. This test pins the back-
compat contract for the ``0.4.z`` window.
"""

from __future__ import annotations

import warnings

from dppvalidator.schemas.registry import (
    DEFAULT_SCHEMA_VERSION,
    DEFAULT_VERSIONS,
    SCHEMA_REGISTRY,
    SCHEMA_REGISTRY_BY_FAMILY,
    SchemaFamily,
    SchemaRegistry,
    SchemaVersion,
)


def test_bare_string_registry_only_exposes_untp_rows() -> None:
    """The derived bare-string view filters to the UNTP family.

    CIRPASS rows are reachable only through the family-aware API
    (``SchemaRegistry.get_schema_for(SchemaFamily.CIRPASS, ...)`` or
    ``SCHEMA_REGISTRY_BY_FAMILY[(SchemaFamily.CIRPASS, ...)]``).
    """
    for version, schema in SCHEMA_REGISTRY.items():
        assert schema.family is SchemaFamily.UNTP, (
            f"Bare-string entry for version {version!r} unexpectedly "
            f"belongs to family {schema.family!r}; the bare-string view "
            f"must filter to UNTP only for back-compat."
        )


def test_bare_string_lookup_resolves_untp_versions() -> None:
    """The pre-Phase-2 ``SchemaRegistry.get_schema(version)`` API still
    works for every UNTP version registered."""
    r = SchemaRegistry()
    for version in r.available_versions:
        schema = r.get_schema(version)
        assert isinstance(schema, SchemaVersion)
        assert schema.version == version
        assert schema.family is SchemaFamily.UNTP


def test_bare_string_lookup_emits_deprecation_warning_in_0_5_0() -> None:
    """Phase 9 task 9.4 (dppvalidator 0.5.0): the bare-string
    ``SCHEMA_REGISTRY[version]`` lookup now emits a
    ``DeprecationWarning`` on every ``__getitem__`` access. The
    tuple-keyed ``SCHEMA_REGISTRY_BY_FAMILY`` is the source of truth.
    The warning will become a hard removal in Phase 10 (0.6.0).
    """
    from dppvalidator.schemas.registry import SCHEMA_REGISTRY

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        # Direct bare-string lookup — what the deprecation targets.
        _ = SCHEMA_REGISTRY["0.6.1"]
        _ = SCHEMA_REGISTRY["0.7.0"]
    deprecation_warnings = [w for w in captured if issubclass(w.category, DeprecationWarning)]
    assert len(deprecation_warnings) == 2
    # Each warning should reference the migration plan.
    for w in deprecation_warnings:
        assert "0.5.0" in str(w.message)
        assert "0.6.0" in str(w.message)


def test_default_schema_version_aliases_untp_default() -> None:
    """The legacy ``DEFAULT_SCHEMA_VERSION`` constant equals
    ``DEFAULT_VERSIONS[SchemaFamily.UNTP]``."""
    assert DEFAULT_VERSIONS[SchemaFamily.UNTP] == DEFAULT_SCHEMA_VERSION


def test_tuple_keyed_registry_is_source_of_truth() -> None:
    """Every bare-string entry has a corresponding tuple-keyed entry."""
    for version, schema in SCHEMA_REGISTRY.items():
        key = (SchemaFamily.UNTP, version)
        assert key in SCHEMA_REGISTRY_BY_FAMILY, (
            f"Bare-string entry {version!r} has no tuple-keyed counterpart"
        )
        assert SCHEMA_REGISTRY_BY_FAMILY[key] is schema, (
            f"Bare-string {version!r} and tuple-keyed {key!r} must point at "
            f"the *same* SchemaVersion instance (derived view)"
        )


def test_cirpass_row_only_reachable_via_family_aware_api() -> None:
    """CIRPASS 1.3.0 is registered in the tuple-keyed registry but absent
    from the bare-string view."""
    assert (SchemaFamily.CIRPASS, "1.3.0") in SCHEMA_REGISTRY_BY_FAMILY
    assert "1.3.0" not in SCHEMA_REGISTRY


def test_get_schema_for_resolves_cirpass_default() -> None:
    """``get_schema_for(CIRPASS)`` with no explicit version uses the
    family default."""
    r = SchemaRegistry()
    schema = r.get_schema_for(SchemaFamily.CIRPASS)
    assert schema.version == DEFAULT_VERSIONS[SchemaFamily.CIRPASS]
    assert schema.family is SchemaFamily.CIRPASS


def test_get_schema_for_unknown_version_raises() -> None:
    """Unknown ``(family, version)`` pairs raise a clear error."""
    r = SchemaRegistry()
    try:
        r.get_schema_for(SchemaFamily.CIRPASS, "999.0.0")
    except ValueError as e:
        assert "999.0.0" in str(e)
        assert "Available" in str(e)
    else:
        raise AssertionError("ValueError not raised for unknown CIRPASS version")


def test_available_for_returns_untp_versions() -> None:
    """Phase 2 ``available_for(family)`` lists per-family versions."""
    r = SchemaRegistry()
    untp_versions = r.available_for(SchemaFamily.UNTP)
    assert "0.6.0" in untp_versions
    assert "0.6.1" in untp_versions
    assert "0.7.0" in untp_versions
    assert "1.3.0" not in untp_versions
    cirpass_versions = r.available_for(SchemaFamily.CIRPASS)
    assert cirpass_versions == ["1.3.0"]


def test_available_families_returns_both() -> None:
    """Both families surface in the registry."""
    r = SchemaRegistry()
    families = sorted(f.value for f in r.available_families)
    assert families == ["cirpass", "untp"]


def test_active_version_back_compat_still_returns_untp_default() -> None:
    """The :func:`compat.active_version` helper with no argument returns
    the UNTP default (preserves pre-Phase-2 behaviour)."""
    from dppvalidator.compat import active_version

    assert active_version() == DEFAULT_VERSIONS[SchemaFamily.UNTP]


def test_active_version_with_family_kwarg_returns_per_family_default() -> None:
    """Phase 2 task 2.11 added the ``family`` keyword."""
    from dppvalidator.compat import active_version

    assert active_version(SchemaFamily.UNTP) == DEFAULT_VERSIONS[SchemaFamily.UNTP]
    assert active_version(SchemaFamily.CIRPASS) == DEFAULT_VERSIONS[SchemaFamily.CIRPASS]
