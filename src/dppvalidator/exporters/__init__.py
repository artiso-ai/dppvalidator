"""Exporter utilities for Digital Product Passports."""

from typing import Any

from dppvalidator.exporters.cirpass_jsonld import (
    CIRPASSJsonLDExporter,
    export_cirpass_jsonld,
    export_cirpass_jsonld_dict,
)
from dppvalidator.exporters.contexts import (
    CONTEXTS,
    DEFAULT_VERSION,
    ContextDefinition,
    ContextManager,
)
from dppvalidator.exporters.eudpp_jsonld import (
    EUDPP_CANONICAL_CONTEXT_URL,
    EUDPPJsonLDExporter,
    EUDPPTermMapper,
    export_eudpp_jsonld,
    export_eudpp_jsonld_dict,
    get_eudpp_jsonld_context,
    get_term_mapping_summary,
    validate_eudpp_export,
)
from dppvalidator.exporters.json import JSONExporter, export_json
from dppvalidator.exporters.jsonld import JSONLDExporter, export_jsonld
from dppvalidator.exporters.protocols import Exporter


def __getattr__(name: str) -> Any:
    """PEP 562 hook so the deprecated ``EUDPP_CONTEXT_URL`` re-export
    triggers the same :class:`DeprecationWarning` as the underlying
    module-level attribute.

    Without this, importing the package eagerly resolves the constant
    at module-load time and the warning fires at import rather than
    use site. With it, the warning fires only when consumers actually
    reach for the deprecated name.
    """
    if name == "EUDPP_CONTEXT_URL":
        # Defer to the underlying module's __getattr__, which emits
        # the deprecation warning with the right ``stacklevel``.
        from dppvalidator.exporters import eudpp_jsonld

        return eudpp_jsonld.EUDPP_CONTEXT_URL
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "Exporter",
    "JSONLDExporter",
    "export_jsonld",
    "JSONExporter",
    "export_json",
    "ContextManager",
    "ContextDefinition",
    "CONTEXTS",
    "DEFAULT_VERSION",
    # EU DPP Export
    "EUDPPJsonLDExporter",
    "EUDPPTermMapper",
    "EUDPP_CANONICAL_CONTEXT_URL",
    "EUDPP_CONTEXT_URL",  # deprecated alias resolved via __getattr__
    "export_eudpp_jsonld",
    "export_eudpp_jsonld_dict",
    "get_eudpp_jsonld_context",
    "get_term_mapping_summary",
    "validate_eudpp_export",
    # CIRPASS-LD Export (Phase 6)
    "CIRPASSJsonLDExporter",
    "export_cirpass_jsonld",
    "export_cirpass_jsonld_dict",
]
