"""Property-based tests for dppvalidator models using Hypothesis."""

from hypothesis import given, settings
from hypothesis import strategies as st

from dppvalidator.models import (
    CredentialIssuer,
    DigitalProductPassport,
    Measure,
    Product,
    ProductPassport,
)


# Custom strategies for DPP domain types
def printable_text(min_size: int = 1, max_size: int = 100) -> st.SearchStrategy[str]:
    """Strategy for generating printable text without control/whitespace characters."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P"),
            blacklist_characters="\r\n\t\x00\xa0",
        ),
        min_size=min_size,
        max_size=max_size,
    ).filter(lambda x: len(x.strip()) > 0 and x == x.strip())


class TestMeasureProperty:
    """Property-based tests for Measure model."""

    @given(
        value=st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
        unit=st.sampled_from(["KGM", "LTR", "MTR", "GRM", "CMT"]),
    )
    @settings(max_examples=100)
    def test_measure_roundtrip(self, value, unit):
        """Test Measure model round-trip: create → dump → validate."""
        measure = Measure(value=value, unit=unit)
        dumped = measure.model_dump()
        restored = Measure.model_validate(dumped)

        assert restored.value == measure.value
        assert restored.unit == measure.unit

    @given(value=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False))
    @settings(max_examples=50)
    def test_measure_value_preserved(self, value):
        """Test that measure value is preserved through serialization."""
        measure = Measure(value=value, unit="KGM")
        assert measure.model_dump()["value"] == value


class TestCredentialIssuerProperty:
    """Property-based tests for CredentialIssuer model."""

    @given(name=printable_text(1, 50))
    @settings(max_examples=50)
    def test_issuer_name_roundtrip(self, name):
        """Test issuer name round-trip."""
        issuer = CredentialIssuer(
            id="https://example.com/issuer",
            name=name,
        )
        dumped = issuer.model_dump(by_alias=True)
        restored = CredentialIssuer.model_validate(dumped)

        assert restored.name == name

    @given(
        name=printable_text(1, 50),
    )
    @settings(max_examples=30)
    def test_issuer_json_serialization(self, name):
        """Test issuer JSON serialization is valid."""
        issuer = CredentialIssuer(
            id="https://example.com/issuer",
            name=name,
        )
        json_str = issuer.model_dump_json()
        assert len(json_str) > 0
        assert "id" in json_str or "name" in json_str


class TestProductProperty:
    """Property-based tests for Product model."""

    @given(
        name=printable_text(1, 100),
        description=st.text(min_size=0, max_size=500),
    )
    @settings(max_examples=50)
    def test_product_text_fields_preserved(self, name, description):
        """Test product text fields are preserved."""
        product = Product(
            id="https://example.com/product",
            name=name,
            description=description if description.strip() else None,
        )
        dumped = product.model_dump(exclude_none=True)
        restored = Product.model_validate(dumped)

        assert restored.name == name


class TestDigitalProductPassportProperty:
    """Property-based tests for DigitalProductPassport."""

    @given(
        issuer_name=printable_text(1, 50),
    )
    @settings(max_examples=30)
    def test_passport_issuer_roundtrip(self, issuer_name):
        """Test passport with issuer round-trip."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(
                id="https://example.com/issuer",
                name=issuer_name,
            ),
        )
        dumped = passport.model_dump(by_alias=True, exclude_none=True)
        restored = DigitalProductPassport.model_validate(dumped)

        assert restored.issuer.name == issuer_name

    @given(st.data())
    @settings(max_examples=20)
    def test_passport_always_has_required_fields(self, data):
        """Test that passport always has required fields after creation."""
        issuer_name = data.draw(printable_text(1, 30))

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(
                id="https://example.com/issuer",
                name=issuer_name,
            ),
        )

        # Required fields must exist
        assert passport.id is not None
        assert passport.issuer is not None
        assert passport.issuer.id is not None


class TestProductPassportProperty:
    """Property-based tests for ProductPassport (credential subject)."""

    @given(
        product_name=printable_text(1, 50),
    )
    @settings(max_examples=30)
    def test_product_passport_with_product(self, product_name):
        """Test ProductPassport with product."""
        pp = ProductPassport(
            id="https://example.com/pp",
            product=Product(
                id="https://example.com/product",
                name=product_name,
            ),
        )
        dumped = pp.model_dump(by_alias=True, exclude_none=True)
        restored = ProductPassport.model_validate(dumped)

        assert restored.product is not None
        assert restored.product.name == product_name


class TestModelInvariants:
    """Tests for model invariants that should always hold."""

    @given(
        values=st.lists(
            st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=30)
    def test_measure_list_all_valid(self, values):
        """Test that a list of measures can all be created."""
        measures = [Measure(value=v, unit="KGM") for v in values]
        assert len(measures) == len(values)
        assert all(m.value >= 0 for m in measures)

    @given(
        count=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=10)
    def test_multiple_passports_independent(self, count):
        """Test that multiple passports are independent."""
        passports = [
            DigitalProductPassport(
                id=f"https://example.com/dpp-{i}",
                issuer=CredentialIssuer(
                    id=f"https://example.com/issuer-{i}",
                    name=f"Issuer {i}",
                ),
            )
            for i in range(count)
        ]

        # Each passport should have unique id
        ids = [str(p.id) for p in passports]
        assert len(set(ids)) == count
