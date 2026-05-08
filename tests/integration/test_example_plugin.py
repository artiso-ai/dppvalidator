"""Phase 6 acceptance test: example plugin integration coverage.

The exit criterion from §Phase 6 of
``docs/plans/UNTP_0.7.0_MIGRATION.md``:

> ``pip install -e examples/dppvalidator_example_plugin && pytest
>   tests/integration/test_example_plugin.py`` is green.

This module makes the example plugin a CI-tested target so any
public-API regression in the core (renaming a model attribute, moving
a module, breaking the ``SemanticRule`` protocol) is caught
immediately.

The plugin is treated as an editable optional dependency: if it isn't
installed when the suite runs, the tests skip with a clear pointer to
the install command rather than failing. This keeps the plugin
opt-in while still wiring it into nightly CI.
"""

from __future__ import annotations

import importlib
import importlib.util
from typing import Any

import pytest


def _plugin_installed() -> bool:
    """Return True when ``dppvalidator_example_plugin`` is importable."""
    return importlib.util.find_spec("dppvalidator_example_plugin") is not None


pytestmark = pytest.mark.skipif(
    not _plugin_installed(),
    reason=(
        "example plugin not installed; run "
        "`uv pip install -e examples/dppvalidator_example_plugin` first"
    ),
)


# ---------------------------------------------------------------------------
# Fixtures: build v0.6 / v0.7 passports for the rules to chew on
# ---------------------------------------------------------------------------


@pytest.fixture
def v06_passport() -> Any:
    """Construct a minimal v0.6 ``DigitalProductPassport`` instance.

    Uses the top-level alias ``dppvalidator.models.passport`` —
    that's the import the plugin's v0.6 rule expects to see, and the
    public-API stability rule in §4.1.8 of the migration plan
    promises this entry point keeps working in 0.4.0.
    """
    from dppvalidator.models.passport import DigitalProductPassport

    payload: dict[str, Any] = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/credentials/test-v06",
        "issuer": {"id": "did:example:1", "name": "Example"},
        "validFrom": "2024-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["ProductPassport"],
            "id": "https://example.com/subject/1",
            "product": {
                "type": ["Product"],
                "id": "https://example.com/products/1",
                "name": "v0.6 sample product",
            },
            "materialsProvenance": [
                {"name": "Cotton", "originCountry": "EG", "massFraction": 0.6},
                {"name": "Polyester", "originCountry": "DE", "massFraction": 0.4},
            ],
        },
    }
    return DigitalProductPassport.model_validate(payload)


@pytest.fixture
def v07_passport() -> Any:
    """Construct a minimal v0.7 ``DigitalProductPassport`` instance."""
    from dppvalidator.models.v0_7.envelope import DigitalProductPassport

    payload: dict[str, Any] = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "id": "https://example.com/credentials/test-v07",
        "name": "Sample DPP",
        "issuer": {
            "type": ["CredentialIssuer"],
            "id": "did:example:1",
            "name": "Example",
        },
        "validFrom": "2024-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["Product"],
            "id": "https://example.com/products/1",
            "name": "v0.7 sample product",
            "idScheme": {
                "type": ["IdentifierScheme"],
                "id": "https://example.com/schemes/internal",
                "name": "Internal scheme",
            },
            "idGranularity": "model",
            "productCategory": [
                {
                    "type": ["Classification"],
                    "schemeId": "https://unstats.un.org/cpc/",
                    "schemeName": "UN CPC",
                    "code": "12345",
                    "name": "Example category",
                }
            ],
            "producedAtFacility": {
                "type": ["Facility"],
                "id": "https://example.com/facilities/1",
                "name": "Example facility",
            },
            "countryOfProduction": {"countryCode": "DE", "countryName": "Germany"},
            "relatedParty": [
                {
                    "role": "brandOwner",
                    "party": {
                        "type": ["Party"],
                        "id": "did:example:brand",
                        "name": "Sample Brand Inc",
                    },
                }
            ],
        },
    }
    return DigitalProductPassport.model_validate(payload)


# ---------------------------------------------------------------------------
# Public-API stability — the imports the plugin relies on still work
# ---------------------------------------------------------------------------


class TestPluginPublicApi:
    """The imports baked into the plugin must remain stable."""

    def test_top_level_passport_alias_imports(self) -> None:
        """``dppvalidator.models.passport.DigitalProductPassport`` resolves."""
        from dppvalidator.models.passport import DigitalProductPassport

        assert DigitalProductPassport is not None

    def test_credential_subject_dot_product_dot_name_path_works(self, v06_passport: Any) -> None:
        """The plugin reads ``passport.credential_subject.product.name``.

        Phase 3 moved the v0.6 models under ``models/v0_6/`` with a
        thin shim at the top level. The shim must continue to expose
        the original attribute path; otherwise the example plugin
        breaks at attribute-access time, not import time.
        """
        assert v06_passport.credential_subject is not None
        assert v06_passport.credential_subject.product is not None
        assert v06_passport.credential_subject.product.name == "v0.6 sample product"

    def test_v07_credential_subject_is_product_directly(self, v07_passport: Any) -> None:
        """v0.7 credentialSubject *is* the Product (no envelope)."""
        cs = v07_passport.credential_subject
        assert cs is not None
        # The v0.7 shape must NOT carry an outer ``.product`` attribute —
        # plugin authors targeting v0.7 read the Product fields directly.
        assert not hasattr(cs, "product")
        assert cs.name == "v0.7 sample product"


# ---------------------------------------------------------------------------
# Entry-point discovery
# ---------------------------------------------------------------------------


class TestPluginDiscovery:
    """The installed plugin's entry points are discoverable."""

    def test_validator_entry_points_register(self) -> None:
        from dppvalidator.plugins.discovery import discover_validators

        names = {name for name, _ in discover_validators()}
        assert "brand_name" in names
        assert "brand_name_v07" in names
        assert "min_materials" in names

    def test_exporter_entry_points_register(self) -> None:
        from dppvalidator.plugins.discovery import discover_exporters

        names = {name for name, _ in discover_exporters()}
        assert "csv" in names

    def test_validator_classes_are_instantiable(self) -> None:
        """Each discovered validator class can be constructed.

        ``discover_validators`` returns the class object (not an
        instance). The engine instantiates them; a constructor that
        requires arguments would break the registry without surfacing
        a clear error.
        """
        from dppvalidator.plugins.discovery import discover_validators

        for name, cls in discover_validators():
            instance = cls()
            assert instance is not None, f"failed to construct {name}"
            assert hasattr(instance, "rule_id")
            assert hasattr(instance, "check")


# ---------------------------------------------------------------------------
# v0.6 rule behaviour — keep working
# ---------------------------------------------------------------------------


class TestV06BrandNameRule:
    """The v0.6 ``BrandNameRule`` keeps its pre-Phase-3 behaviour."""

    def test_no_violation_when_product_has_name(self, v06_passport: Any) -> None:
        from dppvalidator_example_plugin.validators import BrandNameRule

        rule = BrandNameRule()
        assert rule.check(v06_passport) == []

    def test_violation_when_product_name_missing(self, v06_passport: Any) -> None:
        from dppvalidator_example_plugin.validators import BrandNameRule

        # Pydantic v2 frozen=False on this model — we reach in directly.
        v06_passport.credential_subject.product.name = ""
        rule = BrandNameRule()
        violations = rule.check(v06_passport)
        assert len(violations) == 1
        path, _ = violations[0]
        assert path == "$.credentialSubject.product.name"


class TestV06MinMaterialsRule:
    """The v0.6 ``MinMaterialsRule`` keeps its pre-Phase-3 behaviour."""

    def test_no_violation_with_two_materials(self, v06_passport: Any) -> None:
        from dppvalidator_example_plugin.validators import MinMaterialsRule

        rule = MinMaterialsRule()
        assert rule.check(v06_passport) == []

    def test_warning_with_one_material(self, v06_passport: Any) -> None:
        from dppvalidator_example_plugin.validators import MinMaterialsRule

        # Trim materials down to 1 to trigger the rule.
        v06_passport.credential_subject.materials_provenance = (
            v06_passport.credential_subject.materials_provenance[:1]
        )
        rule = MinMaterialsRule()
        violations = rule.check(v06_passport)
        assert len(violations) == 1


# ---------------------------------------------------------------------------
# v0.7 rule behaviour — new in Phase 6
# ---------------------------------------------------------------------------


class TestV07BrandNameRule:
    """The new ``BrandNameRuleV07`` ships v0.7-aware semantics."""

    def test_rule_id_advertised(self) -> None:
        from dppvalidator_example_plugin.brand_name_v07 import BrandNameRuleV07

        rule = BrandNameRuleV07()
        assert rule.rule_id == "SEM_BRAND_V07"

    def test_applies_to_versions_pins_v07(self) -> None:
        from dppvalidator_example_plugin.brand_name_v07 import BrandNameRuleV07

        assert BrandNameRuleV07.applies_to_versions == ("0.7.0",)

    def test_no_violation_when_product_has_name(self, v07_passport: Any) -> None:
        from dppvalidator_example_plugin.brand_name_v07 import BrandNameRuleV07

        rule = BrandNameRuleV07()
        assert rule.check(v07_passport) == []

    def test_no_violation_when_brand_owner_present_even_without_name(
        self, v07_passport: Any
    ) -> None:
        from dppvalidator_example_plugin.brand_name_v07 import BrandNameRuleV07

        # Drop the name; the brandOwner relatedParty alone should satisfy.
        v07_passport.credential_subject.name = ""
        rule = BrandNameRuleV07()
        assert rule.check(v07_passport) == []

    def test_violation_when_neither_name_nor_brand_owner(self, v07_passport: Any) -> None:
        from dppvalidator_example_plugin.brand_name_v07 import BrandNameRuleV07

        v07_passport.credential_subject.name = ""
        v07_passport.credential_subject.related_party = []
        rule = BrandNameRuleV07()
        violations = rule.check(v07_passport)
        assert len(violations) == 1
        path, message = violations[0]
        assert path == "$.credentialSubject"
        assert "brandOwner" in message

    def test_silently_skips_v06_passports(self, v06_passport: Any) -> None:
        """Handed a v0.6 passport, the v0.7 rule no-ops cleanly.

        This is the version-aware-rule pattern: rules co-exist in the
        registry and self-filter on shape rather than crashing when the
        wrong version flows through.
        """
        from dppvalidator_example_plugin.brand_name_v07 import BrandNameRuleV07

        rule = BrandNameRuleV07()
        # Even though the v0.6 product.name is set, the v0.7 rule should
        # not look at the wrapped product — it returns no violations
        # because the shape didn't match.
        assert rule.check(v06_passport) == []


# ---------------------------------------------------------------------------
# CSV exporter — public-API smoke
# ---------------------------------------------------------------------------


class TestCSVExporterSmoke:
    """The CSV exporter still exports a non-empty payload."""

    def test_export_returns_string(self, v06_passport: Any) -> None:
        from dppvalidator_example_plugin.exporters import CSVExporter

        exporter = CSVExporter()
        out = exporter.export(v06_passport)
        assert isinstance(out, str)
        assert out
