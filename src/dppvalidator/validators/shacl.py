"""SHACL validation layer for EU DPP Core Ontology alignment.

Provides SHACL-based validation using official CIRPASS-2 SHACL shapes
from the DPP Vocabulary Hub. Supports both placeholder shapes (for
structural validation) and official RDF-based validation with pyshacl.

Note: Full SHACL validation requires the [rdf] extra:
    pip install dppvalidator[rdf]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from importlib.resources import files
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport

logger = get_logger(__name__)


class SHACLSeverity(str, Enum):
    """SHACL constraint severity levels."""

    VIOLATION = "sh:Violation"
    WARNING = "sh:Warning"
    INFO = "sh:Info"


class SHACLConstraintType(str, Enum):
    """Common SHACL constraint types."""

    MIN_COUNT = "sh:minCount"
    MAX_COUNT = "sh:maxCount"
    DATATYPE = "sh:datatype"
    PATTERN = "sh:pattern"
    MIN_INCLUSIVE = "sh:minInclusive"
    MAX_INCLUSIVE = "sh:maxInclusive"
    CLASS = "sh:class"
    NODE = "sh:node"
    HAS_VALUE = "sh:hasValue"
    IN = "sh:in"


@dataclass(frozen=True, slots=True)
class SHACLPropertyShape:
    """SHACL property shape definition."""

    path: str
    name: str
    description: str
    min_count: int | None = None
    max_count: int | None = None
    datatype: str | None = None
    pattern: str | None = None
    node_kind: str | None = None
    severity: SHACLSeverity = SHACLSeverity.VIOLATION


@dataclass(frozen=True, slots=True)
class SHACLNodeShape:
    """SHACL node shape definition."""

    target_class: str
    name: str
    description: str
    properties: tuple[SHACLPropertyShape, ...] = field(default_factory=tuple)


@dataclass
class SHACLValidationResult:
    """Result of SHACL validation."""

    conforms: bool
    violations: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    info: list[dict[str, Any]] = field(default_factory=list)


# CIRPASS DPP Core shapes (placeholder definitions based on ESPR requirements)
# These will be replaced with official shapes when published
CIRPASS_DPP_SHAPE = SHACLNodeShape(
    target_class="cirpass:DigitalProductPassport",
    name="CIRPASSDPPShape",
    description="CIRPASS-2 Digital Product Passport shape",
    properties=(
        SHACLPropertyShape(
            path="cirpass:uniqueProductIdentifier",
            name="UniqueProductIdentifier",
            description="Unique product identifier per ESPR Art 9(1)",
            min_count=1,
            datatype="xsd:string",
        ),
        SHACLPropertyShape(
            path="cirpass:economicOperator",
            name="EconomicOperator",
            description="Economic operator per ESPR Annex III (g)",
            min_count=1,
            node_kind="sh:IRI",
        ),
        SHACLPropertyShape(
            path="cirpass:marketPlacementDate",
            name="MarketPlacementDate",
            description="Market placement date per ESPR Art 9(2i)",
            min_count=1,
            datatype="xsd:dateTime",
        ),
        SHACLPropertyShape(
            path="cirpass:granularityLevel",
            name="GranularityLevel",
            description="DPP granularity level per SR5423",
            min_count=1,
            datatype="xsd:string",
            severity=SHACLSeverity.WARNING,
        ),
    ),
)

CIRPASS_PRODUCT_SHAPE = SHACLNodeShape(
    target_class="cirpass:Product",
    name="CIRPASSProductShape",
    description="CIRPASS-2 Product shape",
    properties=(
        SHACLPropertyShape(
            path="cirpass:productName",
            name="ProductName",
            description="Product name per ESPR Annex III",
            min_count=1,
            datatype="xsd:string",
        ),
        SHACLPropertyShape(
            path="cirpass:materialComposition",
            name="MaterialComposition",
            description="Material composition per ESPR Annex I (a)",
            min_count=0,
            severity=SHACLSeverity.WARNING,
        ),
    ),
)

CIRPASS_MATERIAL_SHAPE = SHACLNodeShape(
    target_class="cirpass:MaterialComposition",
    name="CIRPASSMaterialShape",
    description="CIRPASS-2 Material composition shape",
    properties=(
        SHACLPropertyShape(
            path="cirpass:materialName",
            name="MaterialName",
            description="Material name",
            min_count=1,
            datatype="xsd:string",
        ),
        SHACLPropertyShape(
            path="cirpass:massPercentage",
            name="MassPercentage",
            description="Mass percentage per ESPR Annex I (a)",
            datatype="xsd:decimal",
            severity=SHACLSeverity.WARNING,
        ),
        SHACLPropertyShape(
            path="cirpass:substanceOfConcern",
            name="SubstanceOfConcern",
            description="Substance of concern flag per ESPR Art 7(5a)",
            datatype="xsd:boolean",
        ),
    ),
)

# All CIRPASS shapes
CIRPASS_SHAPES: tuple[SHACLNodeShape, ...] = (
    CIRPASS_DPP_SHAPE,
    CIRPASS_PRODUCT_SHAPE,
    CIRPASS_MATERIAL_SHAPE,
)


class SHACLValidator:
    """SHACL validation foundation.

    Provides infrastructure for SHACL-based validation. Full validation
    requires pyshacl library and RDF graph conversion.
    """

    def __init__(self, shapes: tuple[SHACLNodeShape, ...] | None = None) -> None:
        """Initialize SHACL validator.

        Args:
            shapes: SHACL shapes to use. Defaults to CIRPASS shapes.
        """
        self._shapes = shapes or CIRPASS_SHAPES

    def validate_structure(self, passport: DigitalProductPassport) -> SHACLValidationResult:
        """Validate passport structure against SHACL shapes.

        This performs structural validation without full RDF/SHACL processing.
        For full SHACL validation, use validate_rdf with pyshacl.

        Args:
            passport: Digital Product Passport to validate

        Returns:
            SHACLValidationResult with conformance status
        """
        result = SHACLValidationResult(conforms=True)

        # Check DPP shape constraints
        self._check_dpp_constraints(passport, result)

        # Check product constraints if present
        if passport.credential_subject and passport.credential_subject.product:
            self._check_product_constraints(passport, result)

        # Check material constraints if present
        if passport.credential_subject and passport.credential_subject.materials_provenance:
            self._check_material_constraints(passport, result)

        result.conforms = len(result.violations) == 0
        return result

    def _check_dpp_constraints(
        self, passport: DigitalProductPassport, result: SHACLValidationResult
    ) -> None:
        """Check DPP-level SHACL constraints."""
        # Check issuer (economicOperator)
        if not passport.issuer or not passport.issuer.id:
            result.violations.append(
                {
                    "path": "cirpass:economicOperator",
                    "message": "Missing economic operator identifier",
                    "shape": "CIRPASSDPPShape",
                    "constraint": SHACLConstraintType.MIN_COUNT.value,
                }
            )

        # Check validFrom (marketPlacementDate)
        if not passport.valid_from:
            result.violations.append(
                {
                    "path": "cirpass:marketPlacementDate",
                    "message": "Missing market placement date",
                    "shape": "CIRPASSDPPShape",
                    "constraint": SHACLConstraintType.MIN_COUNT.value,
                }
            )

        # Check granularity level (warning)
        if passport.credential_subject and not passport.credential_subject.granularity_level:
            result.warnings.append(
                {
                    "path": "cirpass:granularityLevel",
                    "message": "Missing granularity level (model/batch/item)",
                    "shape": "CIRPASSDPPShape",
                    "constraint": SHACLConstraintType.MIN_COUNT.value,
                }
            )

    def _check_product_constraints(
        self, passport: DigitalProductPassport, result: SHACLValidationResult
    ) -> None:
        """Check product-level SHACL constraints."""
        product = passport.credential_subject.product  # type: ignore[union-attr]
        if product is None:
            return

        # Check product name
        if not getattr(product, "name", None):
            result.violations.append(
                {
                    "path": "cirpass:productName",
                    "message": "Missing product name",
                    "shape": "CIRPASSProductShape",
                    "constraint": SHACLConstraintType.MIN_COUNT.value,
                }
            )

    def _check_material_constraints(
        self, passport: DigitalProductPassport, result: SHACLValidationResult
    ) -> None:
        """Check material-level SHACL constraints."""
        materials = passport.credential_subject.materials_provenance  # type: ignore[union-attr]
        if materials is None:
            return

        for i, material in enumerate(materials):
            # Check material name
            if not material.name:
                result.violations.append(
                    {
                        "path": f"cirpass:materialComposition[{i}]/cirpass:materialName",
                        "message": f"Material {i} missing name",
                        "shape": "CIRPASSMaterialShape",
                        "constraint": SHACLConstraintType.MIN_COUNT.value,
                    }
                )

            # Check mass percentage (warning)
            if material.mass_fraction is None:
                result.warnings.append(
                    {
                        "path": f"cirpass:materialComposition[{i}]/cirpass:massPercentage",
                        "message": f"Material '{material.name}' missing mass percentage",
                        "shape": "CIRPASSMaterialShape",
                        "constraint": SHACLConstraintType.MIN_COUNT.value,
                    }
                )

    @property
    def shape_count(self) -> int:
        """Number of registered SHACL shapes."""
        return len(self._shapes)

    @property
    def shape_names(self) -> list[str]:
        """List of registered shape names."""
        return [s.name for s in self._shapes]

    def get_shape(self, name: str) -> SHACLNodeShape | None:
        """Get shape by name."""
        for shape in self._shapes:
            if shape.name == name:
                return shape
        return None


def get_cirpass_shapes() -> tuple[SHACLNodeShape, ...]:
    """Get all CIRPASS SHACL shapes.

    Returns:
        Tuple of CIRPASS node shapes
    """
    return CIRPASS_SHAPES


def validate_with_shacl(passport: DigitalProductPassport) -> SHACLValidationResult:
    """Validate passport against CIRPASS SHACL shapes.

    Convenience function for SHACL validation.

    Args:
        passport: Digital Product Passport to validate

    Returns:
        SHACLValidationResult with conformance status
    """
    validator = SHACLValidator()
    return validator.validate_structure(passport)


# =============================================================================
# Official SHACL Loading (Phase 8)
# =============================================================================


class OfficialSHACLLoader:
    """Load official CIRPASS SHACL shapes from bundled TTL files.

    Provides loading of the official CIRPASS-2 SHACL constraint shapes
    for RDF-based validation. Requires the [rdf] extra.

    Example:
        >>> loader = OfficialSHACLLoader()
        >>> if loader.is_available():
        ...     graph = loader.load_shapes_graph()
        ...     print(f"Loaded {len(graph)} triples")
    """

    SHACL_FILE = "cirpass_dpp_shacl.ttl"

    def __init__(self) -> None:
        """Initialize official SHACL loader."""
        self._shapes_graph: Any | None = None
        self._shapes_text: str | None = None

    def is_available(self) -> bool:
        """Check if RDF/SHACL dependencies are available.

        Returns:
            True if rdflib and pyshacl are installed
        """
        try:
            import pyshacl  # noqa: F401
            import rdflib  # noqa: F401

            return True
        except ImportError:
            return False

    def load_shapes_text(self) -> str:
        """Load SHACL shapes as text.

        Returns:
            SHACL shapes file content as string

        Raises:
            FileNotFoundError: If SHACL file not found
        """
        if self._shapes_text is not None:
            return self._shapes_text

        try:
            data_dir = files("dppvalidator.vocabularies.data.schemas")
            shacl_path = data_dir.joinpath(self.SHACL_FILE)
            self._shapes_text = shacl_path.read_text(encoding="utf-8")
            logger.debug("Loaded CIRPASS SHACL shapes text")
            return self._shapes_text
        except FileNotFoundError as e:
            raise FileNotFoundError(f"CIRPASS SHACL file not found: {self.SHACL_FILE}") from e

    def load_shapes_graph(self) -> Any:
        """Load SHACL shapes as RDF graph.

        Returns:
            rdflib.Graph with SHACL shapes

        Raises:
            ImportError: If rdflib not installed
            FileNotFoundError: If SHACL file not found
        """
        if self._shapes_graph is not None:
            return self._shapes_graph

        try:
            from rdflib import Graph
        except ImportError as e:
            raise ImportError(
                "rdflib required for RDF SHACL validation. "
                "Install with: pip install dppvalidator[rdf]"
            ) from e

        content = self.load_shapes_text()
        self._shapes_graph = Graph()
        self._shapes_graph.parse(data=content, format="turtle")
        logger.debug("Parsed CIRPASS SHACL shapes graph (%d triples)", len(self._shapes_graph))
        return self._shapes_graph

    def clear_cache(self) -> None:
        """Clear cached shapes."""
        self._shapes_graph = None
        self._shapes_text = None


class RDFSHACLValidator:
    """Full RDF-based SHACL validator using official CIRPASS shapes.

    Provides complete SHACL validation using pyshacl and the official
    CIRPASS-2 SHACL constraint shapes. Requires the [rdf] extra.

    Example:
        >>> validator = RDFSHACLValidator()
        >>> if validator.is_available():
        ...     result = validator.validate_graph(data_graph)
        ...     print(f"Conforms: {result.conforms}")
    """

    def __init__(self, use_official_shapes: bool = True) -> None:
        """Initialize RDF SHACL validator.

        Args:
            use_official_shapes: Use official CIRPASS shapes (default: True)
        """
        self._use_official = use_official_shapes
        self._loader = OfficialSHACLLoader()

    def is_available(self) -> bool:
        """Check if SHACL validation is available.

        Returns:
            True if pyshacl is installed
        """
        return self._loader.is_available()

    def load_shapes(self) -> Any:
        """Load SHACL shapes graph.

        Returns:
            rdflib.Graph with shapes

        Raises:
            ImportError: If rdflib not installed
        """
        if self._use_official:
            return self._loader.load_shapes_graph()
        return self._load_placeholder_shapes()

    def _load_placeholder_shapes(self) -> Any:
        """Load placeholder shapes as RDF graph for backward compatibility."""
        try:
            from rdflib import Graph
        except ImportError as e:
            raise ImportError("rdflib required. Install with: pip install dppvalidator[rdf]") from e

        # Create minimal placeholder shapes
        g = Graph()
        # Placeholder - just return empty graph for now
        return g

    def validate_graph(self, data_graph: Any) -> SHACLValidationResult:
        """Validate RDF data graph against SHACL shapes.

        Args:
            data_graph: rdflib.Graph with data to validate

        Returns:
            SHACLValidationResult with conformance status

        Raises:
            ImportError: If pyshacl not installed
        """
        try:
            import pyshacl
        except ImportError as e:
            raise ImportError(
                "pyshacl required for SHACL validation. Install with: pip install dppvalidator[rdf]"
            ) from e

        shapes_graph = self.load_shapes()

        conforms, results_graph, results_text = pyshacl.validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference="rdfs",
            abort_on_first=False,
        )

        result = SHACLValidationResult(conforms=conforms)

        # Parse results from results_graph
        if not conforms:
            result = self._parse_validation_results(results_graph, result)

        logger.debug(
            "SHACL validation: conforms=%s, violations=%d", conforms, len(result.violations)
        )
        return result

    def _parse_validation_results(
        self, results_graph: Any, result: SHACLValidationResult
    ) -> SHACLValidationResult:
        """Parse SHACL validation results from results graph."""
        from rdflib import Namespace

        SH_NS = Namespace("http://www.w3.org/ns/shacl#")

        for report in results_graph.subjects(predicate=SH_NS.conforms):
            for validation_result in results_graph.objects(report, SH_NS.result):
                severity = None
                message = ""
                path = ""
                focus_node = ""

                for sev in results_graph.objects(validation_result, SH_NS.resultSeverity):
                    severity = str(sev)
                for msg in results_graph.objects(validation_result, SH_NS.resultMessage):
                    message = str(msg)
                for p in results_graph.objects(validation_result, SH_NS.resultPath):
                    path = str(p)
                for fn in results_graph.objects(validation_result, SH_NS.focusNode):
                    focus_node = str(fn)

                violation_info = {
                    "path": path,
                    "message": message,
                    "focusNode": focus_node,
                    "severity": severity,
                }

                if severity and "Violation" in severity:
                    result.violations.append(violation_info)
                elif severity and "Warning" in severity:
                    result.warnings.append(violation_info)
                else:
                    result.info.append(violation_info)

        return result

    def validate_jsonld(self, jsonld_data: dict[str, Any]) -> SHACLValidationResult:
        """Validate JSON-LD data against SHACL shapes.

        Args:
            jsonld_data: JSON-LD dictionary to validate

        Returns:
            SHACLValidationResult with conformance status

        Raises:
            ImportError: If rdflib/pyshacl not installed
        """
        try:
            from rdflib import Graph
        except ImportError as e:
            raise ImportError("rdflib required. Install with: pip install dppvalidator[rdf]") from e

        import json

        data_graph = Graph()
        data_graph.parse(data=json.dumps(jsonld_data), format="json-ld")

        return self.validate_graph(data_graph)


def is_shacl_validation_available() -> bool:
    """Check if full SHACL validation is available.

    Returns:
        True if pyshacl and rdflib are installed
    """
    loader = OfficialSHACLLoader()
    return loader.is_available()


def load_official_shacl_shapes() -> Any:
    """Load official CIRPASS SHACL shapes as RDF graph.

    Convenience function to load the official SHACL shapes.

    Returns:
        rdflib.Graph with CIRPASS SHACL shapes

    Raises:
        ImportError: If rdflib not installed
    """
    loader = OfficialSHACLLoader()
    return loader.load_shapes_graph()


def validate_jsonld_with_official_shacl(jsonld_data: dict[str, Any]) -> SHACLValidationResult:
    """Validate JSON-LD against official CIRPASS SHACL shapes.

    Convenience function for full SHACL validation.

    Args:
        jsonld_data: JSON-LD dictionary to validate

    Returns:
        SHACLValidationResult with conformance status

    Raises:
        ImportError: If rdflib/pyshacl not installed
    """
    validator = RDFSHACLValidator(use_official_shapes=True)
    return validator.validate_jsonld(jsonld_data)
