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

            def check(self, passport):
                return []

        registry.register_validator("mock", MockValidator())
        assert "mock" in registry.validator_names
        assert registry.validator_count == 1

    def test_register_exporter(self):
        """Test manual exporter registration."""
        registry = PluginRegistry(auto_discover=False)

        class MockExporter:
            def export(self, passport):
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

            def check(self, p):
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

            def check(self, p):
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

            def check(self, p):
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

            def check(self, p):
                raise RuntimeError("Plugin error")

        registry.register_validator("broken", BrokenRule())
        errors = registry.run_all_validators(passport)
        assert len(errors) == 1
        assert errors[0].code == "PLG_ERROR"
        assert "Plugin error" in errors[0].message

    def test_run_all_validators_multiple_rules(self, passport):
        """Test running multiple validators."""
        registry = PluginRegistry(auto_discover=False)

        class Rule1:
            rule_id = "R1"
            severity = "error"

            def check(self, p):
                return [("$.r1", "Rule 1")]

        class Rule2:
            rule_id = "R2"
            severity = "warning"

            def check(self, p):
                return [("$.r2", "Rule 2")]

        registry.register_validator("r1", Rule1())
        registry.register_validator("r2", Rule2())
        errors = registry.run_all_validators(passport)
        assert len(errors) == 2


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
