"""RDF/TTL ontology loader with optional dependency support.

Provides utilities for loading and parsing Turtle (TTL) ontology files
from the EU DPP Core Ontology and CIRPASS-2 vocabularies.

Requires the [rdf] optional extra:
    uv add "dppvalidator[rdf]"  # or: pip install "dppvalidator[rdf]"

This module is designed to gracefully handle missing dependencies,
raising informative ImportError messages when rdflib is not installed.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from rdflib import Graph

logger = get_logger(__name__)


# =============================================================================
# RDF Import Checking
# =============================================================================


class RDFNotAvailableError(ImportError):
    """Raised when RDF functionality is used without [rdf] extra installed."""

    def __init__(self, feature: str = "RDF functionality") -> None:
        super().__init__(
            f"{feature} requires the [rdf] extra. "
            "Install with: uv add dppvalidator[rdf] or pip install dppvalidator[rdf]"
        )


def _check_rdflib_available() -> None:
    """Check if rdflib is available, raise informative error if not."""
    try:
        import rdflib  # noqa: F401
    except ImportError as e:
        raise RDFNotAvailableError("rdflib") from e


def is_rdf_available() -> bool:
    """Check if RDF dependencies are available.

    Returns:
        True if rdflib is installed
    """
    try:
        import rdflib  # noqa: F401

        return True
    except ImportError:
        return False


def is_shacl_available() -> bool:
    """Check if SHACL validation dependencies are available.

    Returns:
        True if pyshacl is installed
    """
    try:
        import pyshacl  # noqa: F401

        return True
    except ImportError:
        return False


# =============================================================================
# Ontology Loading
# =============================================================================


def load_ontology(path: Path, format: str = "turtle") -> Graph:
    """Load an ontology file into an RDF graph.

    Args:
        path: Path to the ontology file
        format: RDF format (default: "turtle" for .ttl files)

    Returns:
        Parsed RDF Graph

    Raises:
        RDFNotAvailableError: If rdflib is not installed
        FileNotFoundError: If the ontology file doesn't exist
        RuntimeError: If parsing fails
    """
    _check_rdflib_available()

    from rdflib import Graph

    if not path.exists():
        raise FileNotFoundError(f"Ontology file not found: {path}")

    try:
        g = Graph()
        g.parse(path, format=format)
        logger.debug("Loaded ontology from %s (%d triples)", path, len(g))
        return g
    except Exception as e:
        raise RuntimeError(f"Failed to parse ontology {path}: {e}") from e


def load_ontology_text(content: str, format: str = "turtle") -> Graph:
    """Load an ontology from text content into an RDF graph.

    Args:
        content: Ontology content as string
        format: RDF format (default: "turtle")

    Returns:
        Parsed RDF Graph

    Raises:
        RDFNotAvailableError: If rdflib is not installed
        RuntimeError: If parsing fails
    """
    _check_rdflib_available()

    from rdflib import Graph

    try:
        g = Graph()
        g.parse(data=content, format=format)
        logger.debug("Loaded ontology from text (%d triples)", len(g))
        return g
    except Exception as e:
        raise RuntimeError(f"Failed to parse ontology text: {e}") from e


# =============================================================================
# Bundled Ontology Loading
# =============================================================================


def _get_ontology_data_dir() -> Any:
    """Get the ontology data directory using importlib.resources."""
    return files("dppvalidator.vocabularies.data.ontologies")


def load_bundled_ontology(filename: str) -> Graph:
    """Load a bundled ontology file from the package data.

    Args:
        filename: Name of the ontology file (e.g., "soc_v1.4.7.ttl")

    Returns:
        Parsed RDF Graph

    Raises:
        RDFNotAvailableError: If rdflib is not installed
        FileNotFoundError: If the ontology file doesn't exist
        RuntimeError: If parsing fails
    """
    _check_rdflib_available()

    from rdflib import Graph

    try:
        data_dir = _get_ontology_data_dir()
        ontology_path = data_dir.joinpath(filename)
        content = ontology_path.read_text(encoding="utf-8")

        g = Graph()
        g.parse(data=content, format="turtle")
        logger.debug("Loaded bundled ontology %s (%d triples)", filename, len(g))
        return g
    except FileNotFoundError:
        raise FileNotFoundError(f"Bundled ontology not found: {filename}") from None
    except Exception as e:
        raise RuntimeError(f"Failed to load bundled ontology {filename}: {e}") from e


def load_eudpp_core_ontology() -> Graph:
    """Load the EU DPP Core Ontology (product_dpp).

    Returns:
        Parsed RDF Graph with EU DPP Core Ontology

    Raises:
        RDFNotAvailableError: If rdflib is not installed
    """
    return load_bundled_ontology("product_dpp_v1.7.1.ttl")


def load_soc_ontology() -> Graph:
    """Load the Substances of Concern (SOC) ontology.

    Returns:
        Parsed RDF Graph with SOC ontology

    Raises:
        RDFNotAvailableError: If rdflib is not installed
    """
    return load_bundled_ontology("soc_v1.4.7.ttl")


def load_lca_ontology() -> Graph:
    """Load the LCA/Environmental Footprint ontology.

    Returns:
        Parsed RDF Graph with LCA ontology

    Raises:
        RDFNotAvailableError: If rdflib is not installed
    """
    return load_bundled_ontology("lca_v2.0.ttl")


def load_actor_ontology() -> Graph:
    """Load the Actor/Role ontology.

    Returns:
        Parsed RDF Graph with Actor ontology

    Raises:
        RDFNotAvailableError: If rdflib is not installed
    """
    return load_bundled_ontology("actors_roles_v1.5.1.ttl")


def load_all_eudpp_ontologies() -> Graph:
    """Load and merge all EU DPP ontologies into a single graph.

    Returns:
        Merged RDF Graph with all EU DPP ontologies

    Raises:
        RDFNotAvailableError: If rdflib is not installed
    """
    _check_rdflib_available()

    from rdflib import Graph

    merged = Graph()

    ontologies = [
        "eudpp_core_v1.3.1.ttl",
        "product_dpp_v1.7.1.ttl",
        "actors_roles_v1.5.1.ttl",
        "soc_v1.4.7.ttl",
        "lca_v2.0.ttl",
    ]

    for filename in ontologies:
        try:
            g = load_bundled_ontology(filename)
            merged += g
            logger.debug("Merged %s into combined graph", filename)
        except FileNotFoundError:
            logger.warning("Ontology %s not found, skipping", filename)

    logger.info("Loaded %d ontologies with %d total triples", len(ontologies), len(merged))
    return merged


# =============================================================================
# SHACL Loading
# =============================================================================


def _get_schema_data_dir() -> Any:
    """Get the schema data directory using importlib.resources."""
    return files("dppvalidator.vocabularies.data.schemas")


def load_cirpass_shacl_shapes() -> Graph:
    """Load CIRPASS SHACL shapes for validation.

    Returns:
        Parsed RDF Graph with SHACL shapes

    Raises:
        RDFNotAvailableError: If rdflib is not installed
        FileNotFoundError: If SHACL file doesn't exist
    """
    _check_rdflib_available()

    from rdflib import Graph

    try:
        data_dir = _get_schema_data_dir()
        shacl_path = data_dir.joinpath("cirpass_dpp_shacl.ttl")
        content = shacl_path.read_text(encoding="utf-8")

        g = Graph()
        g.parse(data=content, format="turtle")
        logger.debug("Loaded CIRPASS SHACL shapes (%d triples)", len(g))
        return g
    except FileNotFoundError:
        raise FileNotFoundError("CIRPASS SHACL shapes not found") from None
    except Exception as e:
        raise RuntimeError(f"Failed to load CIRPASS SHACL shapes: {e}") from e


# =============================================================================
# Query Utilities
# =============================================================================


def query_ontology(graph: Graph, sparql_query: str) -> list[dict[str, Any]]:
    """Execute a SPARQL query on an RDF graph.

    Args:
        graph: RDF Graph to query
        sparql_query: SPARQL query string

    Returns:
        List of result dictionaries

    Raises:
        RDFNotAvailableError: If rdflib is not installed
    """
    _check_rdflib_available()

    results = []
    for row in graph.query(sparql_query):
        result = {}
        for i, var in enumerate(row):
            result[f"var{i}"] = str(var) if var else None
        results.append(result)

    return results


def get_ontology_classes(graph: Graph) -> list[str]:
    """Get all class URIs from an ontology.

    Args:
        graph: RDF Graph to query

    Returns:
        List of class URIs
    """
    _check_rdflib_available()

    query = """
    SELECT DISTINCT ?class WHERE {
        ?class a owl:Class .
    }
    """

    try:
        results = []
        for row in graph.query(query):
            if row[0]:
                results.append(str(row[0]))
        return results
    except Exception:
        # Fallback if query fails
        return []


def get_ontology_properties(graph: Graph) -> list[str]:
    """Get all property URIs from an ontology.

    Args:
        graph: RDF Graph to query

    Returns:
        List of property URIs (both object and datatype properties)
    """
    _check_rdflib_available()

    query = """
    SELECT DISTINCT ?prop WHERE {
        { ?prop a owl:ObjectProperty . }
        UNION
        { ?prop a owl:DatatypeProperty . }
    }
    """

    try:
        results = []
        for row in graph.query(query):
            if row[0]:
                results.append(str(row[0]))
        return results
    except Exception:
        # Fallback if query fails
        return []
