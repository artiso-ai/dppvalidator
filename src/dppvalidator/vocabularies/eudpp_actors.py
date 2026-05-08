"""EU DPP Core Ontology actor and role definitions.

Provides dataclass representations of actors and roles from the EU DPP
Core Ontology, based on ESPR Art 2(37-48) economic operator definitions.

Source: EU DPP Core Ontology v1.5.1 (Actors and Roles module)
Namespace: http://dpp.taltech.ee/EUDPP#
DOI: 10.5281/zenodo.15270342
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    pass


# =============================================================================
# Actor Class Enums
# =============================================================================


class EUDPPActorClass(str, Enum):
    """EU DPP Core Ontology actor class URIs."""

    ACTOR = "eudpp:Actor"
    LEGAL_PERSON = "eudpp:LegalPerson"
    NATURAL_PERSON = "eudpp:NaturalPerson"
    FACILITY = "eudpp:Facility"


class EUDPPRoleClass(str, Enum):
    """EU DPP Core Ontology role class URIs.

    Role hierarchy per ESPR Art 2(37-55).
    """

    # Base role
    ROLE = "eudpp:Role"

    # Economic operators (ESPR Art 2(46))
    ECONOMIC_OPERATOR = "eudpp:EconomicOperatorRole"
    MANUFACTURER = "eudpp:ManufacturerRole"
    IMPORTER = "eudpp:ImporterRole"
    DISTRIBUTOR = "eudpp:DistributorRole"
    DEALER = "eudpp:DealerRole"
    FULFILMENT_PROVIDER = "eudpp:FulfilmentServiceProviderRole"
    AUTHORISED_REP = "eudpp:AuthorisedRepresentativeRole"

    # Authorities
    AUTHORITY = "eudpp:AuthorityRole"
    MARKET_SURVEILLANCE = "eudpp:MarketSurveillanceAuthorityRole"
    CUSTOMS = "eudpp:CustomsAuthorityRole"

    # Customers (ESPR Art 2(35))
    CUSTOMER = "eudpp:CustomerRole"
    CONSUMER = "eudpp:ConsumerRole"
    END_USER = "eudpp:EndUserRole"

    # Independent operators (ESPR Art 2(47))
    INDEPENDENT_OPERATOR = "eudpp:IndependentOperatorRole"
    PROFESSIONAL_REPAIRER = "eudpp:ProfessionalRepairerRole"

    # Circular economy roles
    RECYCLER = "eudpp:RecyclerRole"
    REFURBISHER = "eudpp:RefurbisherRole"
    REMANUFACTURER = "eudpp:RemanufacturerRole"

    # Service providers
    DPP_SERVICE_PROVIDER = "eudpp:DPPServiceProviderRole"
    CONFORMITY_BODY = "eudpp:ConformityAssessmentBodyRole"
    NOTIFIED_BODY = "eudpp:NotifiedBodyRole"
    CREDENTIAL_AGENCY = "eudpp:CredentialAgencyRole"
    ISSUING_AGENCY = "eudpp:IssuingAgencyRole"


# =============================================================================
# Role Hierarchy
# =============================================================================


ROLE_HIERARCHY: dict[str, list[str]] = {
    "eudpp:Role": [
        "eudpp:EconomicOperatorRole",
        "eudpp:AuthorityRole",
        "eudpp:CustomerRole",
        "eudpp:EndUserRole",
        "eudpp:IndependentOperatorRole",
        "eudpp:ProfessionalRepairerRole",
        "eudpp:RecyclerRole",
        "eudpp:RefurbisherRole",
        "eudpp:RemanufacturerRole",
        "eudpp:DPPServiceProviderRole",
        "eudpp:ConformityAssessmentBodyRole",
        "eudpp:CredentialAgencyRole",
        "eudpp:IssuingAgencyRole",
    ],
    "eudpp:EconomicOperatorRole": [
        "eudpp:ManufacturerRole",
        "eudpp:ImporterRole",
        "eudpp:DistributorRole",
        "eudpp:DealerRole",
        "eudpp:FulfilmentServiceProviderRole",
        "eudpp:AuthorisedRepresentativeRole",
    ],
    "eudpp:AuthorityRole": [
        "eudpp:MarketSurveillanceAuthorityRole",
        "eudpp:CustomsAuthorityRole",
    ],
    "eudpp:CustomerRole": [
        "eudpp:ConsumerRole",
    ],
    "eudpp:ConformityAssessmentBodyRole": [
        "eudpp:NotifiedBodyRole",
    ],
}


ACTOR_HIERARCHY: dict[str, list[str]] = {
    "eudpp:Actor": [
        "eudpp:LegalPerson",
        "eudpp:NaturalPerson",
    ],
}


# =============================================================================
# Actor Dataclasses
# =============================================================================


@dataclass(frozen=True, slots=True)
class Actor:
    """Actor per EU DPP Core Ontology.

    Actor means a legal or natural person. One actor can take on
    multiple roles.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPActorClass.ACTOR.value

    actor_name: str | None = None
    electronic_contact: str | None = None
    postal_address: str | None = None
    registered_trade_name: str | None = None
    registered_trademark: str | None = None


@dataclass(frozen=True, slots=True)
class LegalPerson(Actor):
    """Legal person per EU DPP Core Ontology.

    A body of persons or an entity (as a corporation) considered as
    having many of the rights and responsibilities of a natural person.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPActorClass.LEGAL_PERSON.value

    unique_operator_id: str | None = None
    established_in: str | None = None


@dataclass(frozen=True, slots=True)
class NaturalPerson(Actor):
    """Natural person per EU DPP Core Ontology.

    A human being as distinguished from a person (as a corporation)
    created by operation of law.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPActorClass.NATURAL_PERSON.value

    residing_in: str | None = None


@dataclass(frozen=True, slots=True)
class Facility:
    """Facility per EU DPP Core Ontology.

    A facility may be a place where specific activities occur, such as
    a production/manufacturing facility (factory) or a place that
    generates electricity.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPActorClass.FACILITY.value

    unique_facility_id: str
    name: str | None = None
    location: str | None = None


# =============================================================================
# Role Dataclasses
# =============================================================================


@dataclass(frozen=True, slots=True)
class Role:
    """Role per EU DPP Core Ontology.

    Role means a set of tasks typically performed by one actor
    (e.g. Responsible Economic Operator, Independent operator).

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.ROLE.value

    role_name: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class EconomicOperatorRole(Role):
    """Economic operator role per ESPR Art 2(46).

    Economic operator means the manufacturer, the authorised
    representative, the importer, the distributor, the dealer
    and the fulfilment service provider.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.ECONOMIC_OPERATOR.value


@dataclass(frozen=True, slots=True)
class ManufacturerRole(EconomicOperatorRole):
    """Manufacturer role per ESPR Art 2(42).

    Manufacturer means any natural or legal person that manufactures
    a product or that has a product designed or manufactured and
    markets that product under their name or trademark.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.MANUFACTURER.value


@dataclass(frozen=True, slots=True)
class ImporterRole(EconomicOperatorRole):
    """Importer role per ESPR Art 2(44).

    Importer means any natural or legal person established in the
    Union that places a product from a third country on the Union
    market.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.IMPORTER.value


@dataclass(frozen=True, slots=True)
class DistributorRole(EconomicOperatorRole):
    """Distributor role per ESPR Art 2(45).

    Distributor means any natural or legal person in the supply chain,
    other than the manufacturer or the importer, that makes a product
    available on the market.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.DISTRIBUTOR.value


@dataclass(frozen=True, slots=True)
class DealerRole(EconomicOperatorRole):
    """Dealer role per ESPR Art 2(55).

    Dealer means a distributor or any other natural or legal person
    that offers products for sale, hire or hire purchase, or that
    displays products, to end users in the course of a commercial
    activity.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.DEALER.value


@dataclass(frozen=True, slots=True)
class FulfilmentServiceProviderRole(EconomicOperatorRole):
    """Fulfilment service provider role per Regulation (EU) 2019/1020 Art 3(11).

    Fulfilment service provider means any natural or legal person
    offering, in the course of commercial activity, at least two of
    the following services: warehousing, packaging, addressing and
    dispatching, without having ownership of the products involved.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.FULFILMENT_PROVIDER.value


@dataclass(frozen=True, slots=True)
class AuthorisedRepresentativeRole(EconomicOperatorRole):
    """Authorised representative role per ESPR Art 2(43).

    Authorised representative means any natural or legal person
    established in the Union that has received a written mandate
    from the manufacturer to act on the manufacturer's behalf.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.AUTHORISED_REP.value


@dataclass(frozen=True, slots=True)
class AuthorityRole(Role):
    """Authority role per EU DPP Core Ontology.

    A role of an actor who exercises authority.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.AUTHORITY.value


@dataclass(frozen=True, slots=True)
class MarketSurveillanceAuthorityRole(AuthorityRole):
    """Market surveillance authority role per Regulation (EU) 2019/1020 Art 3(4).

    Market surveillance authority means an authority designated by a
    Member State under Article 10 as responsible for carrying out
    market surveillance in the territory of that Member State.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.MARKET_SURVEILLANCE.value


@dataclass(frozen=True, slots=True)
class CustomsAuthorityRole(AuthorityRole):
    """Customs authority role per Regulation (EU) No 952/2013 Art 5(1).

    Customs authorities means the customs administrations of the Member
    States responsible for applying the customs legislation.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.CUSTOMS.value


@dataclass(frozen=True, slots=True)
class CustomerRole(Role):
    """Customer role per ESPR Art 2(35).

    Customer means a natural or legal person that purchases, hires or
    receives a product for their own use whether or not acting for
    purposes which are outside their trade, business, craft or profession.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.CUSTOMER.value


@dataclass(frozen=True, slots=True)
class ConsumerRole(CustomerRole):
    """Consumer role per Directive (EU) 2019/771 Art 2(2).

    Consumer means any natural person who, in relation to contracts
    covered by Directive (EU) 2019/771, is acting for purposes which
    are outside that person's trade, business, craft or profession.

    Note: ConsumerRole can only be held by NaturalPerson.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.CONSUMER.value


@dataclass(frozen=True, slots=True)
class EndUserRole(Role):
    """End user role per Regulation (EU) 2019/1020 Art 3(21).

    End user means any natural or legal person residing or established
    in the Union, to whom a product has been made available either as
    a consumer outside of any trade, business, craft or profession or
    as a professional end user in the course of its industrial or
    professional activities.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.END_USER.value


@dataclass(frozen=True, slots=True)
class IndependentOperatorRole(Role):
    """Independent operator role per ESPR Art 2(47).

    Independent operator means natural or legal person that is
    independent of the manufacturer and is directly or indirectly
    involved in the refurbishment, repair, maintenance or repurposing
    of a product.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.INDEPENDENT_OPERATOR.value


@dataclass(frozen=True, slots=True)
class ProfessionalRepairerRole(Role):
    """Professional repairer role per ESPR Art 2(48).

    Professional repairer means a natural or legal person that provides
    professional repair or maintenance services for a product,
    irrespective of whether that person acts within the manufacturer's
    distribution system or independently.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.PROFESSIONAL_REPAIRER.value


@dataclass(frozen=True, slots=True)
class RecyclerRole(Role):
    """Recycler role per EU DPP Core Ontology.

    Role that can be held by actor performing "recycling".

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.RECYCLER.value


@dataclass(frozen=True, slots=True)
class RefurbisherRole(Role):
    """Refurbisher role per EU DPP Core Ontology.

    Role that can be held by actor performing "refurbishment".

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.REFURBISHER.value


@dataclass(frozen=True, slots=True)
class RemanufacturerRole(Role):
    """Remanufacturer role per EU DPP Core Ontology.

    Role that can be held by actor performing "remanufacturing".

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.REMANUFACTURER.value


@dataclass(frozen=True, slots=True)
class DPPServiceProviderRole(Role):
    """DPP service provider role per ESPR Art 2(32).

    Digital product passport service provider means a natural or legal
    person that is an independent third-party authorised by the economic
    operator which places the product on the market or puts it into
    service and that processes the digital product passport data for
    that product.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.DPP_SERVICE_PROVIDER.value


@dataclass(frozen=True, slots=True)
class ConformityAssessmentBodyRole(Role):
    """Conformity assessment body role per ESPR Art 2(52).

    Conformity assessment body means a body that performs conformity
    assessment activities including calibration, testing, certification
    and inspection.

    Note: ConformityAssessmentBodyRole can only be held by LegalPerson.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.CONFORMITY_BODY.value


@dataclass(frozen=True, slots=True)
class NotifiedBodyRole(ConformityAssessmentBodyRole):
    """Notified body role per ESPR Chapter IX.

    Notified body means a conformity assessment body notified in
    accordance with Chapter IX.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.NOTIFIED_BODY.value


@dataclass(frozen=True, slots=True)
class CredentialAgencyRole(Role):
    """Credential agency role per ESPR Art 11.

    Credential agency means a legal person that provides (professional)
    credentials to parties, which may be used to make and verify a
    variety of claims in the DPP.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.CREDENTIAL_AGENCY.value


@dataclass(frozen=True, slots=True)
class IssuingAgencyRole(Role):
    """Issuing agency role per ESPR Art 12(4a).

    Issuing agency is a legal person that provides unique identifiers
    and data carriers. Under specific conditions, economic operators
    may perform the functions associated with an Issuing Agency.

    Source: actors_roles_v1.5.1.ttl
    """

    _class_uri: ClassVar[str] = EUDPPRoleClass.ISSUING_AGENCY.value


# =============================================================================
# Helper Functions
# =============================================================================


def get_role_hierarchy(role_uri: str) -> list[str]:
    """Get all sub-roles of a given role.

    Args:
        role_uri: EU DPP role URI (e.g., "eudpp:EconomicOperatorRole")

    Returns:
        List of sub-role URIs
    """
    return ROLE_HIERARCHY.get(role_uri, [])


def get_actor_hierarchy(actor_uri: str) -> list[str]:
    """Get all sub-types of a given actor class.

    Args:
        actor_uri: EU DPP actor URI (e.g., "eudpp:Actor")

    Returns:
        List of actor subclass URIs
    """
    return ACTOR_HIERARCHY.get(actor_uri, [])


def is_role_subclass_of(child_uri: str, parent_uri: str) -> bool:
    """Check if a role is a subclass of another.

    Args:
        child_uri: Potential child role URI
        parent_uri: Potential parent role URI

    Returns:
        True if child is a subclass of parent
    """
    if child_uri == parent_uri:
        return True

    for parent, children in ROLE_HIERARCHY.items():
        if child_uri in children:
            if parent == parent_uri:
                return True
            return is_role_subclass_of(parent, parent_uri)

    return False


def is_economic_operator_role(role_uri: str) -> bool:
    """Check if a role is an economic operator role per ESPR Art 2(46).

    Args:
        role_uri: Role URI to check

    Returns:
        True if role is EconomicOperatorRole or a subclass
    """
    return is_role_subclass_of(role_uri, EUDPPRoleClass.ECONOMIC_OPERATOR.value)


def get_all_economic_operator_roles() -> list[str]:
    """Get all economic operator role URIs.

    Returns:
        List of economic operator role URIs
    """
    return [
        EUDPPRoleClass.ECONOMIC_OPERATOR.value,
        EUDPPRoleClass.MANUFACTURER.value,
        EUDPPRoleClass.IMPORTER.value,
        EUDPPRoleClass.DISTRIBUTOR.value,
        EUDPPRoleClass.DEALER.value,
        EUDPPRoleClass.FULFILMENT_PROVIDER.value,
        EUDPPRoleClass.AUTHORISED_REP.value,
    ]


def get_all_circular_economy_roles() -> list[str]:
    """Get all circular economy related role URIs.

    Returns:
        List of circular economy role URIs
    """
    return [
        EUDPPRoleClass.RECYCLER.value,
        EUDPPRoleClass.REFURBISHER.value,
        EUDPPRoleClass.REMANUFACTURER.value,
        EUDPPRoleClass.PROFESSIONAL_REPAIRER.value,
    ]
