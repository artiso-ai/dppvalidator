"""Tests for EU DPP Core Ontology actors and roles (Phase 2)."""

import pytest

from dppvalidator.vocabularies.eudpp_actors import (
    ACTOR_HIERARCHY,
    ROLE_HIERARCHY,
    Actor,
    AuthorisedRepresentativeRole,
    AuthorityRole,
    ConformityAssessmentBodyRole,
    ConsumerRole,
    CustomerRole,
    CustomsAuthorityRole,
    DealerRole,
    DistributorRole,
    DPPServiceProviderRole,
    EndUserRole,
    EUDPPActorClass,
    EUDPPRoleClass,
    Facility,
    FulfilmentServiceProviderRole,
    ImporterRole,
    IndependentOperatorRole,
    LegalPerson,
    ManufacturerRole,
    MarketSurveillanceAuthorityRole,
    NaturalPerson,
    NotifiedBodyRole,
    ProfessionalRepairerRole,
    RecyclerRole,
    RefurbisherRole,
    RemanufacturerRole,
    Role,
    get_actor_hierarchy,
    get_all_circular_economy_roles,
    get_all_economic_operator_roles,
    get_role_hierarchy,
    is_economic_operator_role,
    is_role_subclass_of,
)


class TestEUDPPActorClass:
    """Tests for EUDPPActorClass enum."""

    def test_actor_classes_exist(self):
        """Test actor class URIs exist."""
        assert EUDPPActorClass.ACTOR.value == "eudpp:Actor"
        assert EUDPPActorClass.LEGAL_PERSON.value == "eudpp:LegalPerson"
        assert EUDPPActorClass.NATURAL_PERSON.value == "eudpp:NaturalPerson"
        assert EUDPPActorClass.FACILITY.value == "eudpp:Facility"


class TestEUDPPRoleClass:
    """Tests for EUDPPRoleClass enum."""

    def test_base_role_exists(self):
        """Test base role URI exists."""
        assert EUDPPRoleClass.ROLE.value == "eudpp:Role"

    def test_economic_operator_roles_exist(self):
        """Test economic operator role URIs exist."""
        assert EUDPPRoleClass.ECONOMIC_OPERATOR.value == "eudpp:EconomicOperatorRole"
        assert EUDPPRoleClass.MANUFACTURER.value == "eudpp:ManufacturerRole"
        assert EUDPPRoleClass.IMPORTER.value == "eudpp:ImporterRole"
        assert EUDPPRoleClass.DISTRIBUTOR.value == "eudpp:DistributorRole"
        assert EUDPPRoleClass.DEALER.value == "eudpp:DealerRole"
        assert EUDPPRoleClass.FULFILMENT_PROVIDER.value == "eudpp:FulfilmentServiceProviderRole"
        assert EUDPPRoleClass.AUTHORISED_REP.value == "eudpp:AuthorisedRepresentativeRole"

    def test_authority_roles_exist(self):
        """Test authority role URIs exist."""
        assert EUDPPRoleClass.AUTHORITY.value == "eudpp:AuthorityRole"
        assert EUDPPRoleClass.MARKET_SURVEILLANCE.value == "eudpp:MarketSurveillanceAuthorityRole"
        assert EUDPPRoleClass.CUSTOMS.value == "eudpp:CustomsAuthorityRole"

    def test_circular_economy_roles_exist(self):
        """Test circular economy role URIs exist."""
        assert EUDPPRoleClass.RECYCLER.value == "eudpp:RecyclerRole"
        assert EUDPPRoleClass.REFURBISHER.value == "eudpp:RefurbisherRole"
        assert EUDPPRoleClass.REMANUFACTURER.value == "eudpp:RemanufacturerRole"


class TestActor:
    """Tests for Actor dataclass."""

    def test_create_actor(self):
        """Test creating an actor."""
        actor = Actor(
            actor_name="ACME Corporation",
            electronic_contact="info@acme.com",
            postal_address="123 Main St, City, Country",
            registered_trade_name="ACME Corp",
            registered_trademark="ACME™",
        )
        assert actor._class_uri == "eudpp:Actor"
        assert actor.actor_name == "ACME Corporation"
        assert actor.electronic_contact == "info@acme.com"

    def test_create_actor_minimal(self):
        """Test creating actor with minimal fields."""
        actor = Actor()
        assert actor._class_uri == "eudpp:Actor"
        assert actor.actor_name is None

    def test_actor_immutable(self):
        """Test actor is immutable."""
        actor = Actor(actor_name="Test")
        with pytest.raises(AttributeError):
            actor.actor_name = "Modified"  # type: ignore[misc]


class TestLegalPerson:
    """Tests for LegalPerson dataclass."""

    def test_create_legal_person(self):
        """Test creating a legal person."""
        lp = LegalPerson(
            actor_name="Tech Corp GmbH",
            unique_operator_id="urn:uuid:12345678-1234-1234-1234-123456789012",
            established_in="DE",
        )
        assert lp._class_uri == "eudpp:LegalPerson"
        assert lp.unique_operator_id == "urn:uuid:12345678-1234-1234-1234-123456789012"
        assert lp.established_in == "DE"

    def test_legal_person_inherits_actor(self):
        """Test LegalPerson inherits from Actor."""
        lp = LegalPerson(
            actor_name="Test Corp",
            electronic_contact="test@corp.com",
        )
        assert lp.actor_name == "Test Corp"
        assert lp.electronic_contact == "test@corp.com"


class TestNaturalPerson:
    """Tests for NaturalPerson dataclass."""

    def test_create_natural_person(self):
        """Test creating a natural person."""
        np = NaturalPerson(
            actor_name="John Doe",
            residing_in="FR",
        )
        assert np._class_uri == "eudpp:NaturalPerson"
        assert np.residing_in == "FR"

    def test_natural_person_inherits_actor(self):
        """Test NaturalPerson inherits from Actor."""
        np = NaturalPerson(actor_name="Jane Doe")
        assert np.actor_name == "Jane Doe"


class TestFacility:
    """Tests for Facility dataclass."""

    def test_create_facility(self):
        """Test creating a facility."""
        facility = Facility(
            unique_facility_id="urn:uuid:facility-12345",
            name="Main Manufacturing Plant",
            location="Berlin, Germany",
        )
        assert facility._class_uri == "eudpp:Facility"
        assert facility.unique_facility_id == "urn:uuid:facility-12345"
        assert facility.name == "Main Manufacturing Plant"

    def test_facility_immutable(self):
        """Test facility is immutable."""
        facility = Facility(unique_facility_id="test-id")
        with pytest.raises(AttributeError):
            facility.name = "Modified"  # type: ignore[misc]


class TestRole:
    """Tests for Role dataclass."""

    def test_create_role(self):
        """Test creating a role."""
        role = Role(
            role_name="Test Role",
            description="A test role",
        )
        assert role._class_uri == "eudpp:Role"
        assert role.role_name == "Test Role"


class TestEconomicOperatorRoles:
    """Tests for economic operator role classes."""

    def test_manufacturer_role(self):
        """Test ManufacturerRole class."""
        role = ManufacturerRole()
        assert role._class_uri == "eudpp:ManufacturerRole"

    def test_importer_role(self):
        """Test ImporterRole class."""
        role = ImporterRole()
        assert role._class_uri == "eudpp:ImporterRole"

    def test_distributor_role(self):
        """Test DistributorRole class."""
        role = DistributorRole()
        assert role._class_uri == "eudpp:DistributorRole"

    def test_dealer_role(self):
        """Test DealerRole class."""
        role = DealerRole()
        assert role._class_uri == "eudpp:DealerRole"

    def test_fulfilment_provider_role(self):
        """Test FulfilmentServiceProviderRole class."""
        role = FulfilmentServiceProviderRole()
        assert role._class_uri == "eudpp:FulfilmentServiceProviderRole"

    def test_authorised_rep_role(self):
        """Test AuthorisedRepresentativeRole class."""
        role = AuthorisedRepresentativeRole()
        assert role._class_uri == "eudpp:AuthorisedRepresentativeRole"


class TestAuthorityRoles:
    """Tests for authority role classes."""

    def test_authority_role(self):
        """Test AuthorityRole class."""
        role = AuthorityRole()
        assert role._class_uri == "eudpp:AuthorityRole"

    def test_market_surveillance_role(self):
        """Test MarketSurveillanceAuthorityRole class."""
        role = MarketSurveillanceAuthorityRole()
        assert role._class_uri == "eudpp:MarketSurveillanceAuthorityRole"

    def test_customs_authority_role(self):
        """Test CustomsAuthorityRole class."""
        role = CustomsAuthorityRole()
        assert role._class_uri == "eudpp:CustomsAuthorityRole"


class TestCustomerRoles:
    """Tests for customer role classes."""

    def test_customer_role(self):
        """Test CustomerRole class."""
        role = CustomerRole()
        assert role._class_uri == "eudpp:CustomerRole"

    def test_consumer_role(self):
        """Test ConsumerRole class."""
        role = ConsumerRole()
        assert role._class_uri == "eudpp:ConsumerRole"

    def test_end_user_role(self):
        """Test EndUserRole class."""
        role = EndUserRole()
        assert role._class_uri == "eudpp:EndUserRole"


class TestCircularEconomyRoles:
    """Tests for circular economy role classes."""

    def test_recycler_role(self):
        """Test RecyclerRole class."""
        role = RecyclerRole()
        assert role._class_uri == "eudpp:RecyclerRole"

    def test_refurbisher_role(self):
        """Test RefurbisherRole class."""
        role = RefurbisherRole()
        assert role._class_uri == "eudpp:RefurbisherRole"

    def test_remanufacturer_role(self):
        """Test RemanufacturerRole class."""
        role = RemanufacturerRole()
        assert role._class_uri == "eudpp:RemanufacturerRole"

    def test_professional_repairer_role(self):
        """Test ProfessionalRepairerRole class."""
        role = ProfessionalRepairerRole()
        assert role._class_uri == "eudpp:ProfessionalRepairerRole"

    def test_independent_operator_role(self):
        """Test IndependentOperatorRole class."""
        role = IndependentOperatorRole()
        assert role._class_uri == "eudpp:IndependentOperatorRole"


class TestServiceProviderRoles:
    """Tests for service provider role classes."""

    def test_dpp_service_provider_role(self):
        """Test DPPServiceProviderRole class."""
        role = DPPServiceProviderRole()
        assert role._class_uri == "eudpp:DPPServiceProviderRole"

    def test_conformity_body_role(self):
        """Test ConformityAssessmentBodyRole class."""
        role = ConformityAssessmentBodyRole()
        assert role._class_uri == "eudpp:ConformityAssessmentBodyRole"

    def test_notified_body_role(self):
        """Test NotifiedBodyRole class."""
        role = NotifiedBodyRole()
        assert role._class_uri == "eudpp:NotifiedBodyRole"


class TestRoleHierarchy:
    """Tests for role hierarchy functions."""

    def test_role_hierarchy_not_empty(self):
        """Test role hierarchy is not empty."""
        assert len(ROLE_HIERARCHY) > 0

    def test_get_economic_operator_subroles(self):
        """Test getting economic operator subroles."""
        subroles = get_role_hierarchy("eudpp:EconomicOperatorRole")
        assert "eudpp:ManufacturerRole" in subroles
        assert "eudpp:ImporterRole" in subroles
        assert "eudpp:DistributorRole" in subroles

    def test_get_authority_subroles(self):
        """Test getting authority subroles."""
        subroles = get_role_hierarchy("eudpp:AuthorityRole")
        assert "eudpp:MarketSurveillanceAuthorityRole" in subroles
        assert "eudpp:CustomsAuthorityRole" in subroles

    def test_is_role_subclass_direct(self):
        """Test direct role subclass relationship."""
        assert is_role_subclass_of("eudpp:ManufacturerRole", "eudpp:EconomicOperatorRole")
        assert is_role_subclass_of("eudpp:CustomsAuthorityRole", "eudpp:AuthorityRole")

    def test_is_role_subclass_transitive(self):
        """Test transitive role subclass relationship."""
        assert is_role_subclass_of("eudpp:ManufacturerRole", "eudpp:Role")
        assert is_role_subclass_of("eudpp:NotifiedBodyRole", "eudpp:Role")

    def test_is_role_subclass_same(self):
        """Test role is subclass of itself."""
        assert is_role_subclass_of("eudpp:ManufacturerRole", "eudpp:ManufacturerRole")

    def test_is_not_role_subclass(self):
        """Test non-subclass relationship."""
        assert not is_role_subclass_of("eudpp:ManufacturerRole", "eudpp:AuthorityRole")


class TestActorHierarchy:
    """Tests for actor hierarchy functions."""

    def test_actor_hierarchy_not_empty(self):
        """Test actor hierarchy is not empty."""
        assert len(ACTOR_HIERARCHY) > 0

    def test_get_actor_subtypes(self):
        """Test getting actor subtypes."""
        subtypes = get_actor_hierarchy("eudpp:Actor")
        assert "eudpp:LegalPerson" in subtypes
        assert "eudpp:NaturalPerson" in subtypes


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_is_economic_operator_role(self):
        """Test is_economic_operator_role function."""
        assert is_economic_operator_role("eudpp:ManufacturerRole")
        assert is_economic_operator_role("eudpp:ImporterRole")
        assert is_economic_operator_role("eudpp:EconomicOperatorRole")
        assert not is_economic_operator_role("eudpp:ConsumerRole")
        assert not is_economic_operator_role("eudpp:RecyclerRole")

    def test_get_all_economic_operator_roles(self):
        """Test get_all_economic_operator_roles function."""
        roles = get_all_economic_operator_roles()
        assert "eudpp:EconomicOperatorRole" in roles
        assert "eudpp:ManufacturerRole" in roles
        assert "eudpp:ImporterRole" in roles
        assert len(roles) == 7

    def test_get_all_circular_economy_roles(self):
        """Test get_all_circular_economy_roles function."""
        roles = get_all_circular_economy_roles()
        assert "eudpp:RecyclerRole" in roles
        assert "eudpp:RefurbisherRole" in roles
        assert "eudpp:RemanufacturerRole" in roles
        assert "eudpp:ProfessionalRepairerRole" in roles
        assert len(roles) == 4
