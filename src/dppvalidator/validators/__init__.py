"""Multi-layer DPP validation module."""

from dppvalidator.validators.deep import (
    DeepValidationResult,
    DeepValidator,
    validate_deep,
)
from dppvalidator.validators.detection import detect_schema_version, is_dpp_document
from dppvalidator.validators.engine import ValidationEngine
from dppvalidator.validators.jsonld_semantic import (
    JSONLDValidator,
    validate_jsonld,
)
from dppvalidator.validators.model import ModelValidator
from dppvalidator.validators.protocols import AsyncValidator, SemanticRule, Validator
from dppvalidator.validators.results import (
    ValidationError,
    ValidationException,
    ValidationResult,
)
from dppvalidator.validators.schema import SchemaType, SchemaValidator
from dppvalidator.validators.semantic import SemanticValidator
from dppvalidator.validators.shacl import (
    CIRPASS_SHAPES,
    OfficialSHACLLoader,
    RDFSHACLValidator,
    SHACLNodeShape,
    SHACLPropertyShape,
    SHACLSeverity,
    SHACLValidationResult,
    SHACLValidator,
    get_cirpass_shapes,
    is_shacl_validation_available,
    load_official_shacl_shapes,
    validate_jsonld_with_official_shacl,
    validate_with_shacl,
)

__all__ = [
    # Detection
    "detect_schema_version",
    "is_dpp_document",
    # Engine
    "ValidationEngine",
    # Results
    "ValidationResult",
    "ValidationError",
    "ValidationException",
    # Validators
    "SchemaType",
    "SchemaValidator",
    "ModelValidator",
    "SemanticValidator",
    "JSONLDValidator",
    "validate_jsonld",
    # Deep validation
    "DeepValidator",
    "DeepValidationResult",
    "validate_deep",
    # Protocols
    "Validator",
    "AsyncValidator",
    "SemanticRule",
    # SHACL validation
    "SHACLValidator",
    "SHACLValidationResult",
    "SHACLNodeShape",
    "SHACLPropertyShape",
    "SHACLSeverity",
    "CIRPASS_SHAPES",
    "get_cirpass_shapes",
    "validate_with_shacl",
    # Official SHACL (Phase 8)
    "OfficialSHACLLoader",
    "RDFSHACLValidator",
    "is_shacl_validation_available",
    "load_official_shacl_shapes",
    "validate_jsonld_with_official_shacl",
]
