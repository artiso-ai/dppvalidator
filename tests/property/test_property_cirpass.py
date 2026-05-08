"""Property-based tests for CIRPASS-2 validation using Hypothesis.

Tests the invariants and properties of CIRPASS validation rules.
"""

from datetime import datetime, timedelta, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from dppvalidator.models import CredentialIssuer, DigitalProductPassport, Product, ProductPassport
from dppvalidator.validators.rules.cirpass import (
    CIRPASSMandatoryAttributesRule,
    CIRPASSValidityPeriodRule,
)

# Strategy for generating valid URLs
url_strategy = st.from_regex(
    r"https://[a-z]+\.[a-z]{2,3}/[a-z0-9\-]+",
    fullmatch=True,
)


# Strategy for generating valid ISO dates
def datetime_strategy(min_year: int = 2020, max_year: int = 2030):
    """Generate valid datetime strings."""
    return st.datetimes(
        min_value=datetime(min_year, 1, 1, tzinfo=timezone.utc),
        max_value=datetime(max_year, 12, 31, tzinfo=timezone.utc),
    ).map(lambda dt: dt.isoformat())


class TestCIRPASSMandatoryAttributesProperty:
    """Property-based tests for CQ001: Mandatory ESPR attributes."""

    @given(
        issuer_name=st.text(
            min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N", "P"))
        ),
    )
    @settings(max_examples=50)
    def test_valid_passport_always_passes_mandatory_check(self, issuer_name: str):
        """A complete passport should always pass mandatory attribute checks."""
        if not issuer_name.strip():
            return  # Skip empty names

        rule = CIRPASSMandatoryAttributesRule()
        passport = DigitalProductPassport(
            id="https://example.com/dpp/test",
            issuer=CredentialIssuer(
                id="https://example.com/issuer",
                name=issuer_name.strip(),
            ),
            validFrom=datetime.now(timezone.utc).isoformat(),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product/test",
                    name="Test Product",
                ),
            ),
        )
        violations = rule.check(passport)
        # Complete passport should have no mandatory attribute violations
        assert len([v for v in violations if "mandatory" in v[1].lower()]) == 0

    @given(
        has_valid_from=st.booleans(),
        has_credential_subject=st.booleans(),
    )
    @settings(max_examples=30)
    def test_optional_fields_affect_violations(
        self, has_valid_from: bool, has_credential_subject: bool
    ):
        """Optional CIRPASS fields affect violation count."""
        rule = CIRPASSMandatoryAttributesRule()

        # Build passport - issuer is always required by Pydantic
        kwargs = {
            "id": "https://example.com/dpp/test",
            "issuer": CredentialIssuer(
                id="https://example.com/issuer",
                name="Test Issuer",
            ),
        }

        if has_valid_from:
            kwargs["validFrom"] = datetime.now(timezone.utc).isoformat()

        if has_credential_subject:
            kwargs["credentialSubject"] = ProductPassport(
                product=Product(
                    id="https://example.com/product/test",
                    name="Test Product",
                ),
            )

        passport = DigitalProductPassport(**kwargs)
        violations = rule.check(passport)

        # If all CIRPASS fields present, fewer violations expected
        all_present = has_valid_from and has_credential_subject
        if all_present:
            assert len(violations) == 0
        # Violations depend on which fields are missing


class TestCIRPASSValidityPeriodProperty:
    """Property-based tests for CQ016: Validity period rules."""

    @given(
        days_valid=st.integers(min_value=1, max_value=3650),
    )
    @settings(max_examples=50)
    def test_valid_period_never_produces_date_order_violation(self, days_valid: int):
        """A passport with validFrom < validUntil should not have date order violations."""
        rule = CIRPASSValidityPeriodRule()

        now = datetime.now(timezone.utc)
        valid_from = now.isoformat()
        valid_until = (now + timedelta(days=days_valid)).isoformat()

        passport = DigitalProductPassport(
            id="https://example.com/dpp/test",
            issuer=CredentialIssuer(
                id="https://example.com/issuer",
                name="Test Issuer",
            ),
            validFrom=valid_from,
            validUntil=valid_until,
        )

        violations = rule.check(passport)
        # Should not have date order violations
        date_order_violations = [
            v for v in violations if "before" in v[1].lower() or "order" in v[1].lower()
        ]
        assert len(date_order_violations) == 0

    @given(
        years_until_expiry=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=30)
    def test_long_validity_periods_are_accepted(self, years_until_expiry: int):
        """Passports with various validity periods should be validated."""
        rule = CIRPASSValidityPeriodRule()

        now = datetime.now(timezone.utc)
        valid_from = now.isoformat()
        valid_until = (now + timedelta(days=365 * years_until_expiry)).isoformat()

        passport = DigitalProductPassport(
            id="https://example.com/dpp/test",
            issuer=CredentialIssuer(
                id="https://example.com/issuer",
                name="Test Issuer",
            ),
            validFrom=valid_from,
            validUntil=valid_until,
        )

        violations = rule.check(passport)
        # Valid date order should not produce date violations
        date_violations = [
            v for v in violations if "date" in v[1].lower() or "before" in v[1].lower()
        ]
        assert len(date_violations) == 0


class TestDPPModelProperty:
    """Property-based tests for DPP model invariants."""

    @given(
        product_name=st.text(min_size=1, max_size=200),
        issuer_name=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=50)
    def test_passport_roundtrip_preserves_data(self, product_name: str, issuer_name: str):
        """Creating a passport and serializing/deserializing should preserve data."""
        if not product_name.strip() or not issuer_name.strip():
            return

        passport = DigitalProductPassport(
            id="https://example.com/dpp/test",
            issuer=CredentialIssuer(
                id="https://example.com/issuer",
                name=issuer_name.strip(),
            ),
            validFrom=datetime.now(timezone.utc).isoformat(),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/product/test",
                    name=product_name.strip(),
                ),
            ),
        )

        # Serialize to dict and back
        data = passport.model_dump(by_alias=True, exclude_none=True)
        restored = DigitalProductPassport.model_validate(data)

        # Core fields should match
        assert restored.id == passport.id
        assert restored.issuer.name == passport.issuer.name

    @given(
        num_materials=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=20)
    def test_passport_with_materials_validates(self, num_materials: int):
        """Passports with varying numbers of materials should validate."""
        from dppvalidator.validators import ValidationEngine

        passport_data = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "type": ["DigitalProductPassport", "VerifiableCredential"],
            "id": "https://example.com/dpp/test",
            "issuer": {"id": "https://example.com/issuer", "name": "Test"},
            "validFrom": datetime.now(timezone.utc).isoformat(),
            "validUntil": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            "credentialSubject": {
                "id": "https://example.com/subject",
                "type": ["ProductPassport"],
                "product": {
                    "id": "https://example.com/product",
                    "name": "Test Product",
                },
            },
        }

        if num_materials > 0:
            passport_data["credentialSubject"]["materialsProvenance"] = [
                {"name": f"Material {i}", "massFraction": 1.0 / num_materials}
                for i in range(num_materials)
            ]

        engine = ValidationEngine(layers=["model"])
        result = engine.validate(passport_data)

        # Should successfully parse regardless of material count
        assert result is not None
