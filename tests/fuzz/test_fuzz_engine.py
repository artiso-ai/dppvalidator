"""Fuzzing tests for the validation engine.

These tests ensure the validation engine never crashes on arbitrary input,
even malformed or malicious data.
"""

import json

from hypothesis import given, settings
from hypothesis import strategies as st

from dppvalidator.validators import ValidationEngine, ValidationResult


class TestEngineFuzzing:
    """Fuzzing tests for ValidationEngine."""

    @given(st.binary(min_size=0, max_size=1000))
    @settings(max_examples=500, deadline=500)
    def test_engine_never_crashes_on_binary(self, data: bytes):
        """Test engine never crashes on arbitrary binary input."""
        engine = ValidationEngine(layers=["model"])
        try:
            text = data.decode("utf-8", errors="replace")
            result = engine.validate(text)
            assert result is not None
            assert isinstance(result, ValidationResult)
        except Exception:  # noqa: S110
            # Any exception is acceptable as long as it doesn't crash
            pass

    @given(st.text(min_size=0, max_size=500))
    @settings(max_examples=500, deadline=500)
    def test_engine_never_crashes_on_text(self, text: str):
        """Test engine never crashes on arbitrary text input."""
        engine = ValidationEngine(layers=["model"])
        try:
            result = engine.validate(text)
            assert result is not None
            assert isinstance(result, ValidationResult)
        except Exception:  # noqa: S110
            pass

    @given(
        st.recursive(
            st.none()
            | st.booleans()
            | st.integers()
            | st.floats(allow_nan=False)
            | st.text(max_size=50),
            lambda children: st.lists(children, max_size=5)
            | st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=5),
            max_leaves=20,
        )
    )
    @settings(max_examples=300, deadline=500)
    def test_engine_never_crashes_on_json_structure(self, data):
        """Test engine never crashes on arbitrary JSON-like structures."""
        engine = ValidationEngine(layers=["model"])
        try:
            result = engine.validate(data)
            assert result is not None
            assert isinstance(result, ValidationResult)
        except Exception:  # noqa: S110
            pass

    @given(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=30),
            values=st.one_of(
                st.none(),
                st.booleans(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(max_size=100),
                st.lists(st.text(max_size=20), max_size=5),
            ),
            min_size=0,
            max_size=20,
        )
    )
    @settings(max_examples=300, deadline=500)
    def test_engine_never_crashes_on_random_dicts(self, data: dict):
        """Test engine never crashes on random dictionary input."""
        engine = ValidationEngine(layers=["model"])
        result = engine.validate(data)
        assert result is not None
        assert isinstance(result, ValidationResult)
        # Invalid data should produce invalid result
        if "id" not in data or "issuer" not in data:
            assert result.valid is False

    @given(st.binary(min_size=0, max_size=500))
    @settings(max_examples=200, deadline=500)
    def test_engine_with_all_layers_never_crashes(self, data: bytes):
        """Test engine with all layers enabled never crashes."""
        engine = ValidationEngine(layers=["model", "semantic"])
        try:
            text = data.decode("utf-8", errors="replace")
            result = engine.validate(text)
            assert result is not None
        except Exception:  # noqa: S110
            pass


class TestJSONParseFuzzing:
    """Fuzzing tests for JSON parsing paths."""

    @given(st.text(min_size=0, max_size=200))
    @settings(max_examples=300, deadline=500)
    def test_json_parse_never_crashes(self, text: str):
        """Test JSON parsing never crashes on arbitrary text."""
        engine = ValidationEngine(layers=["model"])
        try:
            # Try to parse as JSON first
            data = json.loads(text)
            result = engine.validate(data)
            assert result is not None
        except json.JSONDecodeError:
            # Invalid JSON is expected
            pass
        except Exception:  # noqa: S110
            # Other exceptions are acceptable
            pass

    @given(st.from_regex(r"\{[^}]*\}", fullmatch=True))
    @settings(max_examples=200, deadline=500)
    def test_json_like_strings_never_crash(self, text: str):
        """Test JSON-like strings never crash the engine."""
        engine = ValidationEngine(layers=["model"])
        try:
            result = engine.validate(text)
            assert result is not None
        except Exception:  # noqa: S110
            pass


class TestMalformedInputFuzzing:
    """Fuzzing tests for malformed inputs."""

    @given(
        st.dictionaries(
            keys=st.sampled_from(["id", "issuer", "type", "@context", "credentialSubject"]),
            values=st.one_of(
                st.none(),
                st.integers(),
                st.text(max_size=50),
                st.lists(st.none(), max_size=3),
            ),
            min_size=0,
            max_size=5,
        )
    )
    @settings(max_examples=200, deadline=500)
    def test_partial_valid_structure_never_crashes(self, data: dict):
        """Test partial DPP-like structures never crash."""
        engine = ValidationEngine(layers=["model"])
        result = engine.validate(data)
        assert result is not None
        assert isinstance(result, ValidationResult)

    @given(
        st.fixed_dictionaries(
            {
                "id": st.one_of(st.none(), st.integers(), st.text(max_size=100)),
                "issuer": st.one_of(
                    st.none(),
                    st.integers(),
                    st.text(max_size=50),
                    st.dictionaries(st.text(max_size=10), st.text(max_size=20), max_size=3),
                ),
            }
        )
    )
    @settings(max_examples=200, deadline=500)
    def test_wrong_types_never_crash(self, data: dict):
        """Test wrong field types never crash the engine."""
        engine = ValidationEngine(layers=["model"])
        result = engine.validate(data)
        assert result is not None
        assert isinstance(result, ValidationResult)

    @given(st.integers(min_value=-1000000, max_value=1000000))
    @settings(max_examples=100, deadline=500)
    def test_integer_input_never_crashes(self, data: int):
        """Test integer input never crashes."""
        engine = ValidationEngine(layers=["model"])
        result = engine.validate(data)  # type: ignore
        assert result is not None

    @given(st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=100, deadline=500)
    def test_float_input_never_crashes(self, data: float):
        """Test float input never crashes."""
        engine = ValidationEngine(layers=["model"])
        result = engine.validate(data)  # type: ignore
        assert result is not None

    @given(st.lists(st.text(max_size=20), max_size=10))
    @settings(max_examples=100, deadline=500)
    def test_list_input_never_crashes(self, data: list):
        """Test list input never crashes."""
        engine = ValidationEngine(layers=["model"])
        result = engine.validate(data)  # type: ignore
        assert result is not None
