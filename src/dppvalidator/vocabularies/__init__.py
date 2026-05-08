"""External vocabulary loading and validation.

This module provides the public API for vocabulary operations.
For advanced usage, import directly from submodules:

    from dppvalidator.vocabularies.code_lists import is_valid_material_code
    from dppvalidator.vocabularies.ontology import OntologyMapper
    from dppvalidator.vocabularies.rdf_loader import load_ontology
    from dppvalidator.vocabularies.eudpp_classes import EUDPPClass
    from dppvalidator.vocabularies.eudpp_actors import Actor
    from dppvalidator.vocabularies.eudpp_substances import Substance
    from dppvalidator.vocabularies.eudpp_lca import ImpactCategory
    from dppvalidator.vocabularies.eudpp_relations import ProductRelationMapper
    from dppvalidator.vocabularies.cirpass_terms import CIRPASSTerm
"""

from dppvalidator.vocabularies.cache import VocabularyCache
from dppvalidator.vocabularies.code_lists import (
    is_valid_gs1_digital_link,
    is_valid_hs_code,
    is_valid_material_code,
    validate_gtin,
)
from dppvalidator.vocabularies.loader import VocabularyLoader
from dppvalidator.vocabularies.ontology import OntologyMapper
from dppvalidator.vocabularies.rdf_loader import (
    RDFNotAvailableError,
    is_rdf_available,
    is_shacl_available,
)

__all__ = [
    # Core loader
    "VocabularyLoader",
    "VocabularyCache",
    # Code validation (most common use cases)
    "is_valid_gs1_digital_link",
    "is_valid_hs_code",
    "is_valid_material_code",
    "validate_gtin",
    # Ontology mapping
    "OntologyMapper",
    # RDF availability checks
    "RDFNotAvailableError",
    "is_rdf_available",
    "is_shacl_available",
]
