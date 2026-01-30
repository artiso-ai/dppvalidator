"""Tests for UNTP DPP models."""

import pytest
from pydantic import ValidationError

from dppvalidator.models import (
    CircularityPerformance,
    Claim,
    Classification,
    ConformityTopic,
    CredentialIssuer,
    CredentialStatus,
    Criterion,
    CriterionStatus,
    DigitalProductPassport,
    Dimension,
    EmissionsPerformance,
    EncryptionMethod,
    Facility,
    GranularityLevel,
    HashMethod,
    IdentifierScheme,
    Link,
    Material,
    Measure,
    Metric,
    OperationalScope,
    Party,
    Product,
    ProductPassport,
    Regulation,
    SecureLink,
    Standard,
    TraceabilityPerformance,
)


class TestMeasure:
    """Tests for Measure model."""

    def test_valid_measure(self):
        """Test creating a valid measure."""
        measure = Measure(value=100.0, unit="KGM")
        assert measure.value == 100.0
        assert measure.unit == "KGM"

    def test_measure_to_jsonld(self):
        """Test JSON-LD serialization."""
        measure = Measure(value=50.5, unit="LTR")
        jsonld = measure.to_jsonld()
        assert jsonld["type"] == ["Measure"]
        assert jsonld["value"] == 50.5


class TestMaterial:
    """Tests for Material model."""

    def test_valid_material(self):
        """Test creating a valid material."""
        material = Material(name="Lithium Iron Phosphate")
        assert material.name == "Lithium Iron Phosphate"

    def test_material_with_mass_fraction(self):
        """Test material with mass fraction."""
        material = Material(
            name="Steel",
            massFraction=0.6,
            originCountry="DE",
        )
        assert material.mass_fraction == 0.6
        assert material.origin_country == "DE"

    def test_hazardous_without_safety_info(self):
        """Test hazardous material requires safety info."""
        with pytest.raises(ValidationError, match="materialSafetyInformation"):
            Material(name="Hazardous Chemical", hazardous=True)

    def test_hazardous_with_safety_info(self):
        """Test hazardous material with safety info."""
        material = Material(
            name="Hazardous Chemical",
            hazardous=True,
            materialSafetyInformation={"linkURL": "https://example.com/msds"},
        )
        assert material.hazardous is True


class TestCredentialIssuer:
    """Tests for CredentialIssuer model."""

    def test_valid_issuer(self):
        """Test creating a valid issuer."""
        issuer = CredentialIssuer(
            id="https://example.com/issuers/001",
            name="Example Company Ltd",
        )
        assert issuer.name == "Example Company Ltd"

    def test_issuer_to_jsonld(self):
        """Test JSON-LD serialization."""
        issuer = CredentialIssuer(
            id="https://example.com/issuers/001",
            name="Test Corp",
        )
        jsonld = issuer.to_jsonld()
        assert "CredentialIssuer" in jsonld["type"]


class TestProduct:
    """Tests for Product model."""

    def test_valid_product(self):
        """Test creating a valid product."""
        product = Product(
            id="https://example.com/products/001",
            name="EV Battery",
        )
        assert product.name == "EV Battery"

    def test_product_with_serial_number(self):
        """Test product with serial number."""
        product = Product(
            id="https://example.com/products/002",
            name="Battery Pack",
            serialNumber="SN-2024-001",
            batchNumber="BATCH-Q1",
        )
        assert product.serial_number == "SN-2024-001"


class TestDigitalProductPassport:
    """Tests for DigitalProductPassport model."""

    @pytest.fixture
    def minimal_dpp_data(self) -> dict:
        """Minimal valid DPP data fixture."""
        return {
            "id": "https://example.com/credentials/dpp-001",
            "issuer": {
                "id": "https://example.com/issuers/001",
                "name": "Example Company Ltd",
            },
        }

    def test_minimal_dpp(self, minimal_dpp_data: dict):
        """Test creating a minimal valid DPP."""
        dpp = DigitalProductPassport(**minimal_dpp_data)
        assert dpp.issuer.name == "Example Company Ltd"

    def test_dpp_default_context(self, minimal_dpp_data: dict):
        """Test DPP has default context."""
        dpp = DigitalProductPassport(**minimal_dpp_data)
        assert "https://www.w3.org/ns/credentials/v2" in dpp.context

    def test_dpp_with_dates(self, minimal_dpp_data: dict):
        """Test DPP with validity dates."""
        minimal_dpp_data["validFrom"] = "2024-01-01T00:00:00Z"
        minimal_dpp_data["validUntil"] = "2034-01-01T00:00:00Z"
        dpp = DigitalProductPassport(**minimal_dpp_data)
        assert dpp.valid_from is not None
        assert dpp.valid_until is not None

    def test_dpp_invalid_date_order(self, minimal_dpp_data: dict):
        """Test DPP rejects validFrom >= validUntil."""
        minimal_dpp_data["validFrom"] = "2034-01-01T00:00:00Z"
        minimal_dpp_data["validUntil"] = "2024-01-01T00:00:00Z"
        with pytest.raises(ValidationError, match="validFrom"):
            DigitalProductPassport(**minimal_dpp_data)

    def test_dpp_to_jsonld(self, minimal_dpp_data: dict):
        """Test JSON-LD serialization."""
        dpp = DigitalProductPassport(**minimal_dpp_data)
        jsonld = dpp.to_jsonld(include_context=True)
        assert "@context" in jsonld
        assert "DigitalProductPassport" in jsonld["type"]


class TestEnums:
    """Tests for enumeration types."""

    def test_conformity_topic_values(self):
        """Test ConformityTopic enum values."""
        assert ConformityTopic.ENVIRONMENT_EMISSIONS.value == "environment.emissions"
        assert ConformityTopic.SOCIAL_LABOUR.value == "social.labour"

    def test_granularity_level_values(self):
        """Test GranularityLevel enum values."""
        assert GranularityLevel.ITEM.value == "item"
        assert GranularityLevel.BATCH.value == "batch"
        assert GranularityLevel.MODEL.value == "model"

    def test_operational_scope_values(self):
        """Test OperationalScope enum values."""
        assert OperationalScope.CRADLE_TO_GATE.value == "CradleToGate"

    def test_hash_method_values(self):
        """Test HashMethod enum values."""
        assert HashMethod.SHA_256.value == "SHA-256"

    def test_encryption_method_values(self):
        """Test EncryptionMethod enum values."""
        assert EncryptionMethod.AES.value == "AES"

    def test_criterion_status_values(self):
        """Test CriterionStatus enum values."""
        assert CriterionStatus.ACTIVE.value == "active"


class TestLink:
    """Tests for Link model."""

    def test_link_with_url(self):
        """Test creating a link with URL."""
        link = Link(linkURL="https://example.com/doc")
        assert str(link.link_url) == "https://example.com/doc"

    def test_link_with_name(self):
        """Test link with display name."""
        link = Link(linkURL="https://example.com/doc", linkName="Documentation")
        assert link.link_name == "Documentation"

    def test_link_to_jsonld(self):
        """Test JSON-LD serialization."""
        link = Link(linkURL="https://example.com/doc")
        jsonld = link.to_jsonld()
        assert jsonld["type"] == ["Link"]


class TestSecureLink:
    """Tests for SecureLink model."""

    def test_secure_link_with_hash(self):
        """Test secure link with hash."""
        link = SecureLink(
            linkURL="https://example.com/file.pdf",
            hashDigest="abc123",
            hashMethod=HashMethod.SHA_256,
        )
        assert link.hash_digest == "abc123"
        assert link.hash_method == HashMethod.SHA_256

    def test_secure_link_to_jsonld(self):
        """Test JSON-LD serialization."""
        link = SecureLink(linkURL="https://example.com/file.pdf")
        jsonld = link.to_jsonld()
        assert "SecureLink" in jsonld["type"]
        assert "Link" in jsonld["type"]


class TestClassification:
    """Tests for Classification model."""

    def test_valid_classification(self):
        """Test creating a valid classification."""
        classification = Classification(
            id="https://vocabulary.example.com/class/001",
            name="Electronics",
            code="ELEC",
        )
        assert classification.name == "Electronics"
        assert classification.code == "ELEC"

    def test_classification_to_jsonld(self):
        """Test JSON-LD serialization."""
        classification = Classification(
            id="https://vocabulary.example.com/class/001",
            name="Electronics",
        )
        jsonld = classification.to_jsonld()
        assert jsonld["type"] == ["Classification"]


class TestIdentifierScheme:
    """Tests for IdentifierScheme model."""

    def test_valid_identifier_scheme(self):
        """Test creating a valid identifier scheme."""
        scheme = IdentifierScheme(
            id="https://id.gs1.org/",
            name="GS1 Global Trade Item Number",
        )
        assert scheme.name == "GS1 Global Trade Item Number"

    def test_identifier_scheme_to_jsonld(self):
        """Test JSON-LD serialization."""
        scheme = IdentifierScheme(name="DUNS")
        jsonld = scheme.to_jsonld()
        assert jsonld["type"] == ["IdentifierScheme"]


class TestParty:
    """Tests for Party model."""

    def test_valid_party(self):
        """Test creating a valid party."""
        party = Party(
            id="https://example.com/parties/001",
            name="Example Corporation",
        )
        assert party.name == "Example Corporation"

    def test_party_with_registered_id(self):
        """Test party with registered ID."""
        party = Party(
            id="https://example.com/parties/001",
            name="Example Corp",
            registeredId="REG-12345",
        )
        assert party.registered_id == "REG-12345"

    def test_party_to_jsonld(self):
        """Test JSON-LD serialization."""
        party = Party(id="https://example.com/parties/001", name="Corp")
        jsonld = party.to_jsonld()
        assert jsonld["type"] == ["Party"]


class TestFacility:
    """Tests for Facility model."""

    def test_valid_facility(self):
        """Test creating a valid facility."""
        facility = Facility(
            id="https://example.com/facilities/001",
            name="Manufacturing Plant A",
        )
        assert facility.name == "Manufacturing Plant A"

    def test_facility_to_jsonld(self):
        """Test JSON-LD serialization."""
        facility = Facility(id="https://example.com/facilities/001", name="Plant A")
        jsonld = facility.to_jsonld()
        assert jsonld["type"] == ["Facility"]


class TestMetric:
    """Tests for Metric model."""

    def test_valid_metric(self):
        """Test creating a valid metric."""
        metric = Metric(
            metricName="Carbon Footprint",
            metricValue={"value": 25.5, "unit": "KGM"},
        )
        assert metric.metric_name == "Carbon Footprint"
        assert metric.metric_value.value == 25.5

    def test_metric_with_accuracy(self):
        """Test metric with accuracy."""
        metric = Metric(
            metricName="Energy Usage",
            metricValue={"value": 100, "unit": "KWH"},
            accuracy=0.95,
        )
        assert metric.accuracy == 0.95

    def test_metric_accuracy_bounds(self):
        """Test metric accuracy must be 0-1."""
        with pytest.raises(ValidationError):
            Metric(
                metricName="Test",
                metricValue={"value": 1, "unit": "EA"},
                accuracy=1.5,
            )


class TestEmissionsPerformance:
    """Tests for EmissionsPerformance model."""

    def test_valid_emissions(self):
        """Test creating valid emissions performance."""
        emissions = EmissionsPerformance(
            carbonFootprint=25.5,
            declaredUnit="KGM",
            operationalScope=OperationalScope.CRADLE_TO_GATE,
            primarySourcedRatio=0.8,
        )
        assert emissions.carbon_footprint == 25.5
        assert emissions.operational_scope == OperationalScope.CRADLE_TO_GATE

    def test_emissions_ratio_bounds(self):
        """Test primary sourced ratio must be 0-1."""
        with pytest.raises(ValidationError):
            EmissionsPerformance(
                carbonFootprint=25.5,
                declaredUnit="KGM",
                operationalScope=OperationalScope.CRADLE_TO_GATE,
                primarySourcedRatio=1.5,
            )

    def test_emissions_to_jsonld(self):
        """Test JSON-LD serialization."""
        emissions = EmissionsPerformance(
            carbonFootprint=25.5,
            declaredUnit="KGM",
            operationalScope=OperationalScope.CRADLE_TO_GATE,
            primarySourcedRatio=0.8,
        )
        jsonld = emissions.to_jsonld()
        assert jsonld["type"] == ["EmissionsPerformance"]


class TestCircularityPerformance:
    """Tests for CircularityPerformance model."""

    def test_valid_circularity(self):
        """Test creating valid circularity performance."""
        circularity = CircularityPerformance(
            recyclableContent=0.85,
            recycledContent=0.3,
            utilityFactor=1.2,
        )
        assert circularity.recyclable_content == 0.85
        assert circularity.recycled_content == 0.3

    def test_circularity_content_bounds(self):
        """Test recyclable content must be 0-1."""
        with pytest.raises(ValidationError):
            CircularityPerformance(recyclableContent=1.5)

    def test_circularity_to_jsonld(self):
        """Test JSON-LD serialization."""
        circularity = CircularityPerformance(recycledContent=0.3)
        jsonld = circularity.to_jsonld()
        assert jsonld["type"] == ["CircularityPerformance"]


class TestTraceabilityPerformance:
    """Tests for TraceabilityPerformance model."""

    def test_valid_traceability(self):
        """Test creating valid traceability performance."""
        traceability = TraceabilityPerformance(
            valueChainProcess="Manufacturing",
            verifiedRatio=0.9,
        )
        assert traceability.value_chain_process == "Manufacturing"
        assert traceability.verified_ratio == 0.9

    def test_traceability_to_jsonld(self):
        """Test JSON-LD serialization."""
        traceability = TraceabilityPerformance(verifiedRatio=0.8)
        jsonld = traceability.to_jsonld()
        assert jsonld["type"] == ["TraceabilityPerformance"]


class TestCriterion:
    """Tests for Criterion model."""

    def test_valid_criterion(self):
        """Test creating a valid criterion."""
        criterion = Criterion(
            id="https://example.com/criteria/001",
            name="Energy Efficiency",
            description="Minimum energy efficiency requirements",
            conformityTopic=ConformityTopic.ENVIRONMENT_ENERGY,
            status=CriterionStatus.ACTIVE,
        )
        assert criterion.name == "Energy Efficiency"
        assert criterion.conformity_topic == ConformityTopic.ENVIRONMENT_ENERGY

    def test_criterion_to_jsonld(self):
        """Test JSON-LD serialization."""
        criterion = Criterion(
            id="https://example.com/criteria/001",
            name="Test",
            description="Test criterion",
            conformityTopic=ConformityTopic.ENVIRONMENT_ENERGY,
            status=CriterionStatus.ACTIVE,
        )
        jsonld = criterion.to_jsonld()
        assert jsonld["type"] == ["Criterion"]


class TestStandard:
    """Tests for Standard model."""

    def test_valid_standard(self):
        """Test creating a valid standard."""
        standard = Standard(
            id="https://iso.org/14001",
            name="ISO 14001",
            issuingParty={
                "id": "https://iso.org",
                "name": "ISO",
            },
        )
        assert standard.name == "ISO 14001"

    def test_standard_to_jsonld(self):
        """Test JSON-LD serialization."""
        standard = Standard(
            name="ISO 14001",
            issuingParty={"id": "https://iso.org", "name": "ISO"},
        )
        jsonld = standard.to_jsonld()
        assert jsonld["type"] == ["Standard"]


class TestRegulation:
    """Tests for Regulation model."""

    def test_valid_regulation(self):
        """Test creating a valid regulation."""
        regulation = Regulation(
            id="https://ec.europa.eu/espr",
            name="EU ESPR",
            administeredBy={
                "id": "https://ec.europa.eu",
                "name": "European Commission",
            },
            jurisdictionCountry="EU",
        )
        assert regulation.name == "EU ESPR"
        assert regulation.jurisdiction_country == "EU"

    def test_regulation_to_jsonld(self):
        """Test JSON-LD serialization."""
        regulation = Regulation(
            name="ESPR",
            administeredBy={"id": "https://ec.europa.eu", "name": "EC"},
        )
        jsonld = regulation.to_jsonld()
        assert jsonld["type"] == ["Regulation"]


class TestClaim:
    """Tests for Claim model."""

    def test_valid_claim(self):
        """Test creating a valid claim."""
        claim = Claim(
            id="https://example.com/claims/001",
            conformance=True,
            conformityTopic=ConformityTopic.ENVIRONMENT_EMISSIONS,
        )
        assert claim.conformance is True
        assert claim.conformity_topic == ConformityTopic.ENVIRONMENT_EMISSIONS

    def test_claim_to_jsonld(self):
        """Test JSON-LD serialization has both types."""
        claim = Claim(
            id="https://example.com/claims/001",
            conformance=True,
            conformityTopic=ConformityTopic.ENVIRONMENT_EMISSIONS,
        )
        jsonld = claim.to_jsonld()
        assert "Claim" in jsonld["type"]
        assert "Declaration" in jsonld["type"]


class TestProductPassport:
    """Tests for ProductPassport model."""

    def test_valid_product_passport(self):
        """Test creating a valid product passport."""
        passport = ProductPassport(
            id="https://example.com/passports/001",
            granularityLevel=GranularityLevel.ITEM,
        )
        assert passport.granularity_level == GranularityLevel.ITEM

    def test_product_passport_to_jsonld(self):
        """Test JSON-LD serialization."""
        passport = ProductPassport()
        jsonld = passport.to_jsonld()
        assert jsonld["type"] == ["ProductPassport"]


class TestDimension:
    """Tests for Dimension model."""

    def test_valid_dimension(self):
        """Test creating a valid dimension."""
        dimension = Dimension(
            length={"value": 100, "unit": "CMT"},
            width={"value": 50, "unit": "CMT"},
            height={"value": 25, "unit": "CMT"},
        )
        assert dimension.length.value == 100

    def test_dimension_to_jsonld(self):
        """Test JSON-LD serialization."""
        dimension = Dimension()
        jsonld = dimension.to_jsonld()
        assert jsonld["type"] == ["Dimension"]


class TestCredentialStatus:
    """Tests for CredentialStatus model (W3C VC v2 revocation)."""

    def test_valid_credential_status(self):
        """Test creating a valid credential status."""
        status = CredentialStatus(
            id="https://example.com/status/1#42",
            type="BitstringStatusListEntry",
            statusPurpose="revocation",
            statusListIndex="42",
            statusListCredential="https://example.com/status/1",
        )
        assert status.id == "https://example.com/status/1#42"
        assert status.type == "BitstringStatusListEntry"
        assert status.status_purpose == "revocation"
        assert status.status_list_index == "42"

    def test_credential_status_minimal(self):
        """Test minimal credential status with only required fields."""
        status = CredentialStatus(
            id="https://example.com/status/1",
            type="StatusList2021Entry",
        )
        assert status.id == "https://example.com/status/1"
        assert status.type == "StatusList2021Entry"
        assert status.status_purpose is None
        assert status.status_list_index is None
        assert status.status_list_credential is None

    def test_credential_status_to_jsonld(self):
        """Test JSON-LD serialization."""
        status = CredentialStatus(
            id="https://example.com/status/1#42",
            type="BitstringStatusListEntry",
            statusPurpose="revocation",
        )
        jsonld = status.to_jsonld()
        assert jsonld["type"] == ["CredentialStatus"]
        assert jsonld["id"] == "https://example.com/status/1#42"
        assert jsonld["statusPurpose"] == "revocation"

    def test_credential_status_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            CredentialStatus(id="https://example.com/status")  # missing type


class TestDigitalProductPassportCredentialStatus:
    """Tests for credentialStatus field on DigitalProductPassport."""

    def test_passport_with_single_credential_status(self):
        """Test passport with single credential status."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp/001",
            issuer={"id": "did:web:example.com", "name": "Issuer"},
            credentialStatus={
                "id": "https://example.com/status/1#42",
                "type": "BitstringStatusListEntry",
                "statusPurpose": "revocation",
            },
        )
        assert passport.credential_status is not None
        assert passport.credential_status.type == "BitstringStatusListEntry"

    def test_passport_with_multiple_credential_statuses(self):
        """Test passport with list of credential statuses."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp/001",
            issuer={"id": "did:web:example.com", "name": "Issuer"},
            credentialStatus=[
                {
                    "id": "https://example.com/status/revocation#42",
                    "type": "BitstringStatusListEntry",
                    "statusPurpose": "revocation",
                },
                {
                    "id": "https://example.com/status/suspension#42",
                    "type": "BitstringStatusListEntry",
                    "statusPurpose": "suspension",
                },
            ],
        )
        assert isinstance(passport.credential_status, list)
        assert len(passport.credential_status) == 2
        assert passport.credential_status[0].status_purpose == "revocation"
        assert passport.credential_status[1].status_purpose == "suspension"

    def test_passport_without_credential_status(self):
        """Test passport without credential status (optional field)."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp/001",
            issuer={"id": "did:web:example.com", "name": "Issuer"},
        )
        assert passport.credential_status is None
