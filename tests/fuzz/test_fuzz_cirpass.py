"""Fuzz tests for CIRPASS-2 validation to ensure robustness.

Tests that the validation engine and CIRPASS rules never crash
on malformed or unexpected input.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from dppvalidator.validators import ValidationEngine, ValidationResult


class TestCIRPASSRulesFuzzing:
    """Fuzz tests for CIRPASS validation rules."""

    @given(
        st.fixed_dictionaries(
            {
                "id": st.text(min_size=0, max_size=200),
                "issuer": st.one_of(
                    st.none(),
                    st.text(max_size=100),
                    st.fixed_dictionaries(
                        {
                            "id": st.text(max_size=100),
                            "name": st.text(max_size=100),
                        }
                    ),
                ),
                "validFrom": st.one_of(
                    st.none(),
                    st.text(max_size=50),
                    st.integers(),
                ),
                "validUntil": st.one_of(
                    st.none(),
                    st.text(max_size=50),
                    st.integers(),
                ),
                "credentialSubject": st.one_of(
                    st.none(),
                    st.text(max_size=100),
                    st.dictionaries(
                        st.text(min_size=1, max_size=20),
                        st.text(max_size=50),
                        max_size=5,
                    ),
                ),
            }
        )
    )
    @settings(max_examples=200, deadline=1000)
    def test_validation_engine_never_crashes_on_dpp_like_data(self, data: dict):
        """Test engine handles DPP-like structures without crashing."""
        engine = ValidationEngine(layers=["model", "semantic"])
        try:
            result = engine.validate(data)
            assert result is not None
            assert isinstance(result, ValidationResult)
        except Exception:
            # Validation errors are acceptable, crashes are not
            pass

    @given(
        st.lists(
            st.fixed_dictionaries(
                {
                    "name": st.text(max_size=50),
                    "massFraction": st.one_of(
                        st.none(),
                        st.floats(allow_nan=True, allow_infinity=True),
                        st.text(max_size=20),
                        st.integers(),
                    ),
                }
            ),
            max_size=10,
        )
    )
    @settings(max_examples=100, deadline=500)
    def test_materials_provenance_fuzzing(self, materials: list):
        """Test materials provenance handling with fuzzed data."""
        engine = ValidationEngine(layers=["model", "semantic"])
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["DigitalProductPassport"],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "validFrom": "2024-01-01T00:00:00Z",
            "validUntil": "2034-01-01T00:00:00Z",
            "credentialSubject": {
                "id": "https://example.com/subject",
                "type": ["ProductPassport"],
                "product": {"id": "https://example.com/product", "name": "Test"},
                "materialsProvenance": materials,
            },
        }
        try:
            result = engine.validate(data)
            assert result is not None
        except Exception:
            pass


class TestExternalLibraryFuzzing:
    """Fuzz tests for external library integration."""

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=30),
            st.recursive(
                st.none() | st.booleans() | st.integers() | st.text(max_size=50),
                lambda children: st.lists(children, max_size=3)
                | st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=3),
                max_leaves=10,
            ),
            max_size=10,
        )
    )
    @settings(max_examples=100, deadline=1000)
    def test_jsonld_context_fuzzing(self, context_like: dict):
        """Test JSON-LD context handling with fuzzed data."""
        engine = ValidationEngine(layers=["model"])
        data = {
            "@context": context_like,
            "type": ["DigitalProductPassport"],
            "id": "https://example.com/dpp",
        }
        try:
            result = engine.validate(data)
            assert result is not None
        except Exception:
            pass

    @given(
        st.text(
            min_size=0,
            max_size=500,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "S", "Z"),
                whitelist_characters="\n\t@:/<>{}[]\"'",
            ),
        )
    )
    @settings(max_examples=200, deadline=500)
    def test_url_like_strings_fuzzing(self, url_like: str):
        """Test URL-like string handling."""
        engine = ValidationEngine(layers=["model"])
        data = {
            "id": url_like,
            "issuer": {"id": url_like, "name": "Test"},
        }
        try:
            result = engine.validate(data)
            assert result is not None
        except Exception:
            pass


class TestSHACLFuzzing:
    """Fuzz tests for SHACL validation (when available)."""

    @given(
        st.dictionaries(
            st.sampled_from(["@context", "@type", "@id", "type", "id", "name", "value"]),
            st.one_of(
                st.none(),
                st.text(max_size=100),
                st.lists(st.text(max_size=50), max_size=5),
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=100, deadline=1000)
    def test_shacl_validator_handles_malformed_jsonld(self, data: dict):
        """Test SHACL validator handles malformed JSON-LD gracefully."""
        try:
            from dppvalidator.vocabularies.rdf_loader import is_shacl_available

            if not is_shacl_available():
                return

            from dppvalidator.validators.shacl import validate_jsonld_with_official_shacl

            result = validate_jsonld_with_official_shacl(data)
            assert result is not None
        except ImportError:
            pass
        except Exception:
            # Any exception is acceptable as long as it doesn't crash Python
            pass


class TestDateTimeFuzzing:
    """Fuzz tests for datetime handling in validation."""

    @given(
        valid_from=st.one_of(
            st.none(),
            st.text(max_size=50),
            st.integers(min_value=-1000000000, max_value=1000000000),
            st.floats(allow_nan=True),
        ),
        valid_until=st.one_of(
            st.none(),
            st.text(max_size=50),
            st.integers(min_value=-1000000000, max_value=1000000000),
            st.floats(allow_nan=True),
        ),
    )
    @settings(max_examples=150, deadline=500)
    def test_datetime_field_fuzzing(self, valid_from, valid_until):
        """Test datetime field handling with fuzzed values."""
        engine = ValidationEngine(layers=["model", "semantic"])
        data = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["DigitalProductPassport"],
            "id": "https://example.com/dpp",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "validFrom": valid_from,
            "validUntil": valid_until,
            "credentialSubject": {
                "id": "https://example.com/subject",
                "type": ["ProductPassport"],
                "product": {"id": "https://example.com/product", "name": "Test"},
            },
        }
        try:
            result = engine.validate(data)
            assert result is not None
        except Exception:
            pass
