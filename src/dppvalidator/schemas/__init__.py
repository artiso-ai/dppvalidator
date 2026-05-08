"""Schema management for UNTP DPP and CIRPASS versions."""

from dppvalidator.schemas.cirpass_loader import (
    CIRPASS_SCHEMA_FILE,
    CIRPASS_SCHEMA_TITLE,
    CIRPASS_SCHEMA_VERSION,
    CIRPASSSchemaLoader,
    CIRPASSSHACLLoader,
    get_cirpass_schema,
    get_cirpass_schema_version,
)
from dppvalidator.schemas.loader import SchemaLoader
from dppvalidator.schemas.registry import (
    DEFAULT_SCHEMA_VERSION,
    SCHEMA_REGISTRY,
    SchemaRegistry,
    SchemaVersion,
)

__all__ = [
    # UNTP schema loading
    "SchemaLoader",
    "SchemaRegistry",
    "SchemaVersion",
    "SCHEMA_REGISTRY",
    "DEFAULT_SCHEMA_VERSION",
    # CIRPASS schema loading (Phase 5)
    "CIRPASSSchemaLoader",
    "CIRPASSSHACLLoader",
    "CIRPASS_SCHEMA_VERSION",
    "CIRPASS_SCHEMA_TITLE",
    "CIRPASS_SCHEMA_FILE",
    "get_cirpass_schema",
    "get_cirpass_schema_version",
]
