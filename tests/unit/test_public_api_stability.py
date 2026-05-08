"""Public-API stability tests.

Phase 3 of docs/plans/UNTP_0.7.0_MIGRATION.md formalises the
public-import contract in §4.1.8 / §7.6:

> Within a minor (0.X.0 → 0.X.Y): no class is removed from
> ``dppvalidator.models.__all__``; no parameter on a documented
> constructor is removed or renamed.

These tests guard the import paths that third-party plugins depend on
(specifically ``examples/dppvalidator_example_plugin/``). They snapshot
the set of public names exported from ``dppvalidator.models`` and
``dppvalidator.models.passport`` and fail the build if any name
disappears within a minor.

If you legitimately rename or remove a class, update both the snapshot
**and** the tracking issue's CHANGELOG entry under "Removed".
"""

from __future__ import annotations

import dppvalidator
from dppvalidator import models as models_pkg
from dppvalidator.models import (
    passport as passport_module,
)

# Snapshot of the names guaranteed to be importable from
# ``dppvalidator.models`` through 0.4.x. Adding to this set is fine; removing
# from it requires bumping the validator's minor version (see plan §7.6).
EXPECTED_MODELS_EXPORTS = frozenset(
    {
        # Base & primitives
        "UNTPBaseModel",
        "UNTPStrictModel",
        "Classification",
        "FlexibleUri",
        "Link",
        "Measure",
        "SecureLink",
        "Characteristics",
        "Dimension",
        # Enums
        "ConformityTopic",
        "CriterionStatus",
        "EncryptionMethod",
        "GranularityLevel",
        "HashMethod",
        "OperationalScope",
        # Identifiers
        "Facility",
        "IdentifierScheme",
        "Party",
        # Materials
        "Material",
        # Product
        "Product",
        # Claims (v0.6 names, kept through 0.4.x)
        "Claim",
        "Criterion",
        "Metric",
        "Regulation",
        "Standard",
        # Performance scorecards (v0.6 only — gone in v0.7)
        "CircularityPerformance",
        "EmissionsPerformance",
        "TraceabilityPerformance",
        # Credential / envelope
        "CredentialIssuer",
        "CredentialStatus",
        "ProductPassport",
        "DigitalProductPassport",
    }
)


class TestModelsPackagePublicAPI:
    def test_top_level_dppvalidator_exports(self) -> None:
        """Names guaranteed at the package root."""
        for name in (
            "DigitalProductPassport",
            "ValidationEngine",
            "ValidationError",
            "ValidationResult",
            "DeepValidator",
            "DeepValidationResult",
        ):
            assert hasattr(dppvalidator, name), (
                f"dppvalidator.{name} disappeared — see plan §7.6 stability contract."
            )

    def test_models_package_keeps_v06_exports(self) -> None:
        """Every name in the snapshot must still be importable."""
        actual = set(models_pkg.__all__)
        missing = EXPECTED_MODELS_EXPORTS - actual
        assert not missing, (
            "\nThe following names were REMOVED from dppvalidator.models.__all__:\n  "
            + "\n  ".join(sorted(missing))
            + "\n\nIf this is intentional, you are breaking the public-API "
            "stability contract documented in §7.6 of the migration plan. "
            "Either restore the re-export or bump the validator's minor "
            "version and update CHANGELOG.md."
        )

    def test_models_package_actually_exposes_each_name(self) -> None:
        """``__all__`` and ``hasattr`` must agree."""
        for name in EXPECTED_MODELS_EXPORTS:
            assert hasattr(models_pkg, name), (
                f"dppvalidator.models lists {name!r} in __all__ but "
                "``hasattr`` says it isn't there. The re-export shim is broken."
            )


class TestSubmoduleImportPaths:
    """The example plugin imports `from dppvalidator.models.passport import …`.

    That submodule path must keep resolving to the v0.6 class through
    the 0.4.x line. Phase 9 will switch it to v0.7; that's a separate
    minor release.
    """

    def test_passport_module_re_exports_v0_6_class(self) -> None:
        from dppvalidator.models.v0_6 import (
            DigitalProductPassport as V06DigitalProductPassport,
        )

        assert passport_module.DigitalProductPassport is V06DigitalProductPassport, (
            "dppvalidator.models.passport must re-export the v0.6 "
            "DigitalProductPassport class through 0.4.x. Phase 9 (validator 0.5.0) "
            "switches the default — this test will be updated then."
        )

    def test_v0_6_namespace_is_accessible(self) -> None:
        from dppvalidator.models import v0_6

        assert hasattr(v0_6, "DigitalProductPassport")
        assert hasattr(v0_6, "Product")
        assert hasattr(v0_6, "Material")
        assert hasattr(v0_6, "ProductPassport")  # gone in v0.7

    def test_v0_7_namespace_is_accessible(self) -> None:
        from dppvalidator.models import v0_7

        assert hasattr(v0_7, "DigitalProductPassport")
        assert hasattr(v0_7, "Product")
        assert hasattr(v0_7, "Material")
        # v0.7-only classes
        assert hasattr(v0_7, "IssuingSoftware")
        assert hasattr(v0_7, "Country")
        assert hasattr(v0_7, "PartyRole")
        assert hasattr(v0_7, "Performance")

    def test_v0_7_drops_v0_6_only_classes(self) -> None:
        """Deliberate non-exports from v0_7."""
        from dppvalidator.models import v0_7

        assert not hasattr(v0_7, "ProductPassport"), (
            "v0.7 should not have ProductPassport — credentialSubject is Product directly."
        )
        assert not hasattr(v0_7, "EmissionsPerformance"), (
            "v0.7 should not have EmissionsPerformance — collapsed into Claim.claimedPerformance."
        )
        assert not hasattr(v0_7, "SecureLink"), (
            "v0.7 should not have SecureLink — absorbed into Link."
        )
        assert not hasattr(v0_7, "Metric"), (
            "v0.7 should not have Metric — split into Performance.metric/measure/score."
        )
