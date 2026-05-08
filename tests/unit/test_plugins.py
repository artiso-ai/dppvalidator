"""Tests for plugin architecture."""

import pytest

from dppvalidator.models import CredentialIssuer, DigitalProductPassport
from dppvalidator.plugins import (
    EXPORTER_ENTRY_POINT,
    VALIDATOR_ENTRY_POINT,
    PluginRegistry,
    discover_exporters,
    discover_validators,
    get_default_registry,
    list_available_plugins,
    reset_default_registry,
)


class TestPluginDiscovery:
    """Tests for plugin discovery functions."""

    def test_validator_entry_point_constant(self):
        """Test validator entry point constant."""
        assert VALIDATOR_ENTRY_POINT == "dppvalidator.validators"

    def test_exporter_entry_point_constant(self):
        """Test exporter entry point constant."""
        assert EXPORTER_ENTRY_POINT == "dppvalidator.exporters"

    def test_discover_validators_returns_iterator(self):
        """Test discover_validators returns an iterator."""
        result = discover_validators()
        assert hasattr(result, "__iter__")

    def test_discover_exporters_returns_iterator(self):
        """Test discover_exporters returns an iterator."""
        result = discover_exporters()
        assert hasattr(result, "__iter__")

    def test_list_available_plugins_returns_dict(self):
        """Test list_available_plugins returns dictionary."""
        result = list_available_plugins()
        assert isinstance(result, dict)
        assert "validators" in result
        assert "exporters" in result


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_registry_init_no_auto_discover(self):
        """Test registry initialization without auto-discovery."""
        registry = PluginRegistry(auto_discover=False)
        assert registry.validator_count == 0
        assert registry.exporter_count == 0

    def test_register_validator(self):
        """Test manual validator registration."""
        registry = PluginRegistry(auto_discover=False)

        class MockValidator:
            rule_id = "MOCK"
            description = "Mock validator"
            severity = "warning"

            def check(self, _passport):  # noqa: ARG002
                return []

        registry.register_validator("mock", MockValidator())
        assert "mock" in registry.validator_names
        assert registry.validator_count == 1

    def test_register_exporter(self):
        """Test manual exporter registration."""
        registry = PluginRegistry(auto_discover=False)

        class MockExporter:
            def export(self, _passport):  # noqa: ARG002
                return ""

        registry.register_exporter("mock", MockExporter())
        assert "mock" in registry.exporter_names
        assert registry.exporter_count == 1

    def test_get_validator(self):
        """Test getting a registered validator."""
        registry = PluginRegistry(auto_discover=False)

        class MockValidator:
            pass

        registry.register_validator("mock", MockValidator())
        result = registry.get_validator("mock")
        assert result is not None

    def test_get_validator_not_found(self):
        """Test getting a non-existent validator."""
        registry = PluginRegistry(auto_discover=False)
        result = registry.get_validator("nonexistent")
        assert result is None

    def test_get_exporter(self):
        """Test getting a registered exporter."""
        registry = PluginRegistry(auto_discover=False)

        class MockExporter:
            pass

        registry.register_exporter("mock", MockExporter())
        result = registry.get_exporter("mock")
        assert result is not None

    def test_get_exporter_not_found(self):
        """Test getting a non-existent exporter."""
        registry = PluginRegistry(auto_discover=False)
        result = registry.get_exporter("nonexistent")
        assert result is None

    def test_unregister_validator(self):
        """Test unregistering a validator."""
        registry = PluginRegistry(auto_discover=False)

        class MockValidator:
            pass

        registry.register_validator("mock", MockValidator())
        assert registry.unregister_validator("mock") is True
        assert registry.validator_count == 0

    def test_unregister_validator_not_found(self):
        """Test unregistering a non-existent validator."""
        registry = PluginRegistry(auto_discover=False)
        assert registry.unregister_validator("nonexistent") is False

    def test_unregister_exporter(self):
        """Test unregistering an exporter."""
        registry = PluginRegistry(auto_discover=False)

        class MockExporter:
            pass

        registry.register_exporter("mock", MockExporter())
        assert registry.unregister_exporter("mock") is True
        assert registry.exporter_count == 0

    def test_unregister_exporter_not_found(self):
        """Test unregistering a non-existent exporter."""
        registry = PluginRegistry(auto_discover=False)
        assert registry.unregister_exporter("nonexistent") is False


class TestRunAllValidators:
    """Tests for running plugin validators."""

    @pytest.fixture
    def passport(self) -> DigitalProductPassport:
        """Create test passport."""
        return DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )

    def test_run_all_validators_empty_registry(self, passport):
        """Test running validators on empty registry."""
        registry = PluginRegistry(auto_discover=False)
        errors = registry.run_all_validators(passport)
        assert errors == []

    def test_run_all_validators_with_passing_rule(self, passport):
        """Test running validators that pass."""
        registry = PluginRegistry(auto_discover=False)

        class PassingRule:
            rule_id = "PASS"
            description = "Always passes"
            severity = "error"

            def check(self, _p):  # noqa: ARG002
                return []

        registry.register_validator("passing", PassingRule())
        errors = registry.run_all_validators(passport)
        assert len(errors) == 0

    def test_run_all_validators_with_failing_rule(self, passport):
        """Test running validators that produce violations."""
        registry = PluginRegistry(auto_discover=False)

        class FailingRule:
            rule_id = "FAIL"
            description = "Always fails"
            severity = "error"

            def check(self, _p):  # noqa: ARG002
                return [("$.path", "Error message")]

        registry.register_validator("failing", FailingRule())
        errors = registry.run_all_validators(passport)
        assert len(errors) == 1
        assert errors[0].code == "FAIL"
        assert errors[0].layer == "plugin"

    def test_run_all_validators_with_class(self, passport):
        """Test running validators registered as classes."""
        registry = PluginRegistry(auto_discover=False)

        class ClassRule:
            rule_id = "CLASS"
            description = "Class-based rule"
            severity = "warning"

            def check(self, _p):  # noqa: ARG002
                return [("$.test", "Class rule violation")]

        # Register class, not instance
        registry.register_validator("class_rule", ClassRule)
        errors = registry.run_all_validators(passport)
        assert len(errors) == 1
        assert errors[0].severity == "warning"

    def test_run_all_validators_handles_exceptions(self, passport):
        """Test that plugin exceptions are caught."""
        registry = PluginRegistry(auto_discover=False)

        class BrokenRule:
            rule_id = "BROKEN"
            description = "Throws exception"
            severity = "error"

            def check(self, _p):  # noqa: ARG002
                raise RuntimeError("Plugin error")

        registry.register_validator("broken", BrokenRule())
        errors = registry.run_all_validators(passport)
        assert len(errors) == 1
        assert errors[0].code == "PLG001"
        assert "Plugin error" in errors[0].message

    def test_run_all_validators_multiple_rules(self, passport):
        """Test running multiple validators."""
        registry = PluginRegistry(auto_discover=False)

        class Rule1:
            rule_id = "R1"
            severity = "error"

            def check(self, _p):  # noqa: ARG002
                return [("$.r1", "Rule 1")]

        class Rule2:
            rule_id = "R2"
            severity = "warning"

            def check(self, _p):  # noqa: ARG002
                return [("$.r2", "Rule 2")]

        registry.register_validator("r1", Rule1())
        registry.register_validator("r2", Rule2())
        errors = registry.run_all_validators(passport)
        assert len(errors) == 2


class TestRunAllValidatorsVersionFilter:
    """Per-version plugin dispatch — Phase 6 of UNTP 0.7.0 migration.

    Plugins that declare ``applies_to_versions`` are skipped when the
    payload's resolved version doesn't match. Plugins without that
    attribute keep running for every version (back-compat).
    """

    @pytest.fixture
    def passport(self) -> DigitalProductPassport:
        """Minimal passport — the rules below don't introspect it."""
        return DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )

    def test_plugin_with_matching_applies_to_versions_runs(self, passport):
        """Plugin runs when ``schema_version`` is in ``applies_to_versions``."""
        registry = PluginRegistry(auto_discover=False)

        class V07OnlyRule:
            rule_id = "V07_ONLY"
            severity = "warning"
            applies_to_versions = ("0.7.0",)

            def check(self, _p):  # noqa: ARG002
                return [("$", "v0.7-only violation")]

        registry.register_validator("v07_only", V07OnlyRule())
        errors = registry.run_all_validators(passport, schema_version="0.7.0")
        assert len(errors) == 1
        assert errors[0].code == "V07_ONLY"

    def test_plugin_with_non_matching_applies_to_versions_is_skipped(self, passport):
        """Plugin is silently skipped when ``schema_version`` doesn't match.

        Critically: the skipped plugin must NOT raise and must NOT
        produce a PLG001 entry — it's filtered before ``check()``
        is called.
        """
        registry = PluginRegistry(auto_discover=False)

        class V07OnlyRuleThatWouldCrashOnV06:
            rule_id = "V07_ONLY"
            severity = "warning"
            applies_to_versions = ("0.7.0",)

            def check(self, passport):
                # Reach for a v0.7 attribute. If the engine routed a
                # v0.6 passport here this would AttributeError.
                return [(passport.credential_subject.does_not_exist, "x")]

        registry.register_validator("v07_only", V07OnlyRuleThatWouldCrashOnV06())
        errors = registry.run_all_validators(passport, schema_version="0.6.1")
        # Filter applied, ``check()`` never called — zero errors.
        assert errors == []

    def test_plugin_without_applies_to_versions_runs_for_every_version(self, passport):
        """Plugins predating Phase 6 still run for every version."""
        registry = PluginRegistry(auto_discover=False)

        class LegacyRule:
            rule_id = "LEGACY"
            severity = "info"
            # No ``applies_to_versions``.

            def check(self, _p):  # noqa: ARG002
                return [("$", "legacy violation")]

        registry.register_validator("legacy", LegacyRule())
        for version in ("0.6.0", "0.6.1", "0.7.0", "9.9.9"):
            errors = registry.run_all_validators(passport, schema_version=version)
            assert len(errors) == 1, f"legacy plugin should run for {version}"

    def test_no_schema_version_arg_runs_every_plugin(self, passport):
        """Calling without ``schema_version`` ignores the filter entirely.

        Pre-Phase-6 callers (e.g. anyone invoking
        ``PluginRegistry.run_all_validators(passport)``) get the same
        behaviour they always had.
        """
        registry = PluginRegistry(auto_discover=False)

        class V07OnlyRule:
            rule_id = "V07_ONLY"
            severity = "warning"
            applies_to_versions = ("0.7.0",)

            def check(self, _p):  # noqa: ARG002
                return [("$", "v0.7-only violation")]

        registry.register_validator("v07", V07OnlyRule())
        errors = registry.run_all_validators(passport)  # no schema_version=
        assert len(errors) == 1, "back-compat path: no version → no filter"

    def test_filter_works_on_class_registration_too(self, passport):
        """``applies_to_versions`` on a class is honoured (not just on instances)."""
        registry = PluginRegistry(auto_discover=False)

        class V07ClassRule:
            rule_id = "V07_CLASS"
            severity = "warning"
            applies_to_versions = ("0.7.0",)

            def check(self, _p):  # noqa: ARG002
                return [("$", "x")]

        # Register the class, not an instance — the filter must still see it.
        registry.register_validator("v07_class", V07ClassRule)
        errors_06 = registry.run_all_validators(passport, schema_version="0.6.1")
        errors_07 = registry.run_all_validators(passport, schema_version="0.7.0")
        assert errors_06 == []
        assert len(errors_07) == 1


class TestDefaultRegistry:
    """Tests for default registry singleton."""

    def teardown_method(self):
        """Reset registry after each test."""
        reset_default_registry()

    def test_get_default_registry_returns_registry(self):
        """Test getting default registry."""
        registry = get_default_registry()
        assert isinstance(registry, PluginRegistry)

    def test_get_default_registry_is_singleton(self):
        """Test that default registry is a singleton."""
        registry1 = get_default_registry()
        registry2 = get_default_registry()
        assert registry1 is registry2

    def test_reset_default_registry(self):
        """Test resetting the default registry."""
        registry1 = get_default_registry()
        reset_default_registry()
        registry2 = get_default_registry()
        assert registry1 is not registry2


class TestRegistryProperties:
    """Tests for registry properties."""

    def test_validator_names(self):
        """Test validator_names property."""
        registry = PluginRegistry(auto_discover=False)

        class MockValidator:
            pass

        registry.register_validator("v1", MockValidator())
        registry.register_validator("v2", MockValidator())
        names = registry.validator_names
        assert "v1" in names
        assert "v2" in names

    def test_exporter_names(self):
        """Test exporter_names property."""
        registry = PluginRegistry(auto_discover=False)

        class MockExporter:
            pass

        registry.register_exporter("e1", MockExporter())
        registry.register_exporter("e2", MockExporter())
        names = registry.exporter_names
        assert "e1" in names
        assert "e2" in names

    def test_validator_count(self):
        """Test validator_count property."""
        registry = PluginRegistry(auto_discover=False)
        assert registry.validator_count == 0

        class MockValidator:
            pass

        registry.register_validator("v1", MockValidator())
        assert registry.validator_count == 1

    def test_exporter_count(self):
        """Test exporter_count property."""
        registry = PluginRegistry(auto_discover=False)
        assert registry.exporter_count == 0

        class MockExporter:
            pass

        registry.register_exporter("e1", MockExporter())
        assert registry.exporter_count == 1


class TestPluginDiscoveryCoverage:
    """Coverage tests for plugin discovery module."""

    def test_discover_plugins_fallback_path(self, monkeypatch):
        """Test discovery fallback for older Python entry_points API."""
        from dppvalidator.plugins import discovery

        # Mock entry_points to raise TypeError (simulating old API)
        def mock_entry_points_old(*_args, **kwargs):
            if kwargs:  # New API with group= keyword
                raise TypeError("group keyword not supported")
            # Return empty dict for old API
            return {}

        monkeypatch.setattr(discovery, "entry_points", mock_entry_points_old)

        # Should not raise, returns empty list
        result = list(discovery._discover_plugins("dppvalidator.validators"))
        assert result == []

    def test_discover_plugins_load_error(self, monkeypatch):
        """Test discovery handles plugin load errors gracefully."""
        from dppvalidator.plugins import discovery

        class MockEntryPoint:
            name = "broken_plugin"
            value = "broken.module:Plugin"

            def load(self):
                raise ImportError("Module not found")

        def mock_entry_points(group=None):  # noqa: ARG001
            return [MockEntryPoint()]

        monkeypatch.setattr(discovery, "entry_points", mock_entry_points)

        # Should not raise, returns empty list (load failed)
        result = list(discovery._discover_plugins("test.group"))
        assert result == []

    def test_discover_plugins_successful_load(self, monkeypatch):
        """Test discovery successfully loads plugin."""
        from dppvalidator.plugins import discovery

        class MockPlugin:
            pass

        class MockEntryPoint:
            name = "good_plugin"
            value = "good.module:Plugin"

            def load(self):
                return MockPlugin

        def mock_entry_points(group=None):  # noqa: ARG001
            return [MockEntryPoint()]

        monkeypatch.setattr(discovery, "entry_points", mock_entry_points)

        result = list(discovery._discover_plugins("test.group"))
        assert len(result) == 1
        assert result[0][0] == "good_plugin"
        assert result[0][1] is MockPlugin


class TestPluginRegistryAutoDiscover:
    """Tests for PluginRegistry auto-discovery."""

    def test_registry_auto_discover_runs_discovery(self, monkeypatch):
        """Test registry auto-discovers validators and exporters."""
        from dppvalidator.plugins import registry as registry_module

        validators_discovered = []
        exporters_discovered = []

        def mock_discover_validators():
            validators_discovered.append(True)
            return iter([])

        def mock_discover_exporters():
            exporters_discovered.append(True)
            return iter([])

        # Patch at the registry module level where they're imported
        monkeypatch.setattr(registry_module, "discover_validators", mock_discover_validators)
        monkeypatch.setattr(registry_module, "discover_exporters", mock_discover_exporters)

        # Reset and create new registry with auto_discover
        reset_default_registry()
        _registry = PluginRegistry(auto_discover=True)

        # Verify both discovery methods were called
        assert len(validators_discovered) > 0
        assert len(exporters_discovered) > 0
        assert _registry is not None


class TestPluginRegistryStrictMode:
    """Tests for PluginRegistry strict mode error handling."""

    def test_run_all_validators_strict_raises_plugin_error(self):
        """Test strict mode raises PluginError on validator failure."""
        from dppvalidator.plugins.registry import PluginError

        registry = PluginRegistry(auto_discover=False)

        class FailingValidator:
            rule_id = "FAIL001"
            description = "Always fails"
            severity = "error"

            def check(self, _passport):  # noqa: ARG002
                raise RuntimeError("Intentional failure")

        registry.register_validator("failing", FailingValidator())

        passport = DigitalProductPassport(
            id="https://example.com/dpp/test",
            issuer=CredentialIssuer(
                id="https://example.com/issuer",
                name="Test Issuer",
            ),
        )

        with pytest.raises(PluginError) as exc_info:
            registry.run_all_validators(passport, strict=True)

        assert "failing" in str(exc_info.value).lower() or "fail" in str(exc_info.value).lower()
