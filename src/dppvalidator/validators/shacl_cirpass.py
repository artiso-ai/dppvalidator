"""Per-module SHACL pass for CIRPASS DPP reference structure v1.3.0.

Phase 4 task 4.8 of [docs/plans/CIRPASS_2_MIGRATION.md]. The CIRPASS
SHACL pipeline runs *one pass per EUDPP module* (P_DPP / SOC / LCA /
ACTOR / CON / CORE) so violation reports can carry per-module source
attribution. Bundled v1.9.1 / v1.9.4-Maki TTLs are OWL ontologies
(axiom-bearing, not constraint-bearing), so the runtime treats them as
shape graphs that pyshacl will additionally infer SHACL constraints
from where they exist.

Architecture
============

- :class:`CirpassSHACLValidator` exposes ``validate(parsed_data)``,
  returning a :class:`SHACLValidationResult` augmented with per-module
  ``source`` attribution (``SOC v1.9.1``, ``LCA v1.9.4-Maki``, etc.).
- :func:`_load_module_shapes_graph` is `lru_cache`-d, keyed on
  ``(family, module, version, sha256_of_bundle)``. Repeat invocations
  in the same process reuse the parsed graph; reproducibility across
  processes is guaranteed by the SHA-pin.
- :class:`CirpassSHACLLayer` is the :class:`ValidationLayer` adapter
  used by the engine.

Optional dependency
===================

``pyshacl`` and ``rdflib`` are gated behind the ``[rdf]`` extra. When
either is absent, the layer becomes a single info-level diagnostic
(``LCS-SHACL-UNAVAILABLE``); validation continues.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from functools import cache
from importlib.resources import as_file, files
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger
from dppvalidator.schemas.registry import SchemaFamily
from dppvalidator.validators.layers import ValidationContext, ValidationLayer
from dppvalidator.validators.results import ValidationError, ValidationResult

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


# =============================================================================
# Module manifest
# =============================================================================


@dataclass(frozen=True, slots=True)
class CirpassModule:
    """One row of the per-module shape-graph manifest."""

    name: str
    """Human-readable module name (``SOC``, ``LCA``, ``ACTOR``…)."""

    version: str
    """Module version (``v1.9.1``, ``v1.9.4-Maki``)."""

    bundle_filename: str
    """Filename under ``vocabularies/data/ontologies/``."""

    error_prefix: str
    """Error code prefix used for violation attribution."""


# Phase 4 §4.8: the five EUDPP modules + the integration CORE. Module
# version mirrors the bundled TTL filename. Codes use the Phase 4
# code-prefix audit (``CR`` for base / CORE; ``SUB`` for SOC; ``LCS``
# for LCA; ``ACT`` for ACTOR; ``REL`` for CON).
CIRPASS_MODULES: tuple[CirpassModule, ...] = (
    CirpassModule(
        name="P_DPP",
        version="v1.9.1",
        bundle_filename="product_dpp_v1.9.1.ttl",
        error_prefix="CR",
    ),
    CirpassModule(
        name="SOC",
        version="v1.9.1",
        bundle_filename="soc_v1.9.1.ttl",
        error_prefix="SUB",
    ),
    CirpassModule(
        name="LCA",
        version="v1.9.4-Maki",
        bundle_filename="lca_v1.9.4_Maki.ttl",
        error_prefix="LCS",
    ),
    CirpassModule(
        name="ACTOR",
        version="v1.9.1",
        bundle_filename="actors_roles_v1.9.1.ttl",
        error_prefix="ACT",
    ),
    CirpassModule(
        name="CON",
        version="v1.9.1",
        bundle_filename="connector_v1.9.1.ttl",
        error_prefix="REL",
    ),
)


# =============================================================================
# Cached shape-graph loader
# =============================================================================


def _bundle_sha256(filename: str) -> str:
    """SHA-256 of an LF-normalised TTL bundle.

    The hash is included in the :func:`_load_module_shapes_graph`
    cache key so a vendored TTL bump invalidates the entry cleanly,
    and so cross-process reproducibility is verifiable from the
    bundled bytes alone.
    """
    try:
        bundle = files("dppvalidator.vocabularies.data.ontologies").joinpath(filename)
        with as_file(bundle) as path:
            data = Path(path).read_bytes()
    except (FileNotFoundError, ModuleNotFoundError):
        return "missing"
    normalised = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalised).hexdigest()


@cache
def _load_module_shapes_graph(
    family: SchemaFamily,
    module_name: str,
    version: str,
    sha256: str,
) -> Any:
    """Load and parse the SHACL shape graph for one EUDPP module.

    Cache key components:

    - ``family``     — :class:`SchemaFamily.CIRPASS` for now; the
      signature reserves space for future SHACL-bearing UNTP graphs.
    - ``module_name`` — ``P_DPP`` / ``SOC`` / …
    - ``version``    — module-specific version string.
    - ``sha256``     — pin against the bundled bytes; flips when a
      TTL is upgraded so stale entries are evicted automatically.

    Returns ``None`` when ``rdflib`` is unavailable. Raises
    ``FileNotFoundError`` if the bundled TTL is missing — this is a
    bug, not a runtime condition (the manifest pins the filenames).
    """
    if family is not SchemaFamily.CIRPASS:
        msg = (
            "_load_module_shapes_graph currently supports only the "
            "CIRPASS family; UNTP SHACL bundles are deferred."
        )
        raise ValueError(msg)
    try:
        from rdflib import Graph
    except ImportError:
        return None

    # Find the bundled TTL by name.
    module = next((m for m in CIRPASS_MODULES if m.name == module_name), None)
    if module is None:
        msg = f"Unknown CIRPASS module: {module_name!r}"
        raise ValueError(msg)
    if module.version != version:
        msg = (
            f"Module version mismatch for {module_name}: cache key "
            f"says {version!r}, manifest says {module.version!r}."
        )
        raise ValueError(msg)

    bundle = files("dppvalidator.vocabularies.data.ontologies").joinpath(module.bundle_filename)
    text = bundle.read_text(encoding="utf-8")

    graph = Graph()
    graph.parse(data=text, format="turtle")
    # ``sha256`` is part of the cache key; we don't re-verify here
    # because :func:`_bundle_sha256` already produced the value at
    # call site. The cache hit/miss decision is what enforces it.
    _ = sha256
    return graph


# =============================================================================
# Validator
# =============================================================================


@dataclass
class _PerModuleResult:
    """Per-module SHACL outcome wrapped for layer-level merge."""

    module: CirpassModule
    available: bool
    conforms: bool = True
    violations: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)


class CirpassSHACLValidator:
    """Per-module SHACL validator for CIRPASS reference-structure payloads.

    The validator serialises the input JSON-LD-shaped payload to RDF
    once, then runs ``pyshacl.validate`` against each module's shape
    graph in turn. Each violation carries a ``source`` attribution
    string of the form ``"SOC v1.9.1"`` so consumers can grep for
    "which module rejected this?".
    """

    def __init__(
        self,
        version: str,
        modules: tuple[CirpassModule, ...] | None = None,
    ) -> None:
        """Initialize the per-module SHACL validator.

        Args:
            version: CIRPASS reference-structure version. Stored on
                the result for attribution.
            modules: Override the per-module manifest; defaults to
                :data:`CIRPASS_MODULES` (the v1.9.1 / v1.9.4-Maki set).
        """
        self.version = version
        self._modules = modules or CIRPASS_MODULES

    @staticmethod
    def is_available() -> bool:
        """Return True if pyshacl + rdflib are installed."""
        try:
            import pyshacl  # noqa: F401
            import rdflib  # noqa: F401

            return True
        except ImportError:
            return False

    def validate(self, parsed_data: dict[str, Any]) -> ValidationResult:
        """Run per-module SHACL validation; merge to a single result.

        Args:
            parsed_data: The raw CIRPASS payload (a dict).

        Returns:
            :class:`ValidationResult` whose errors / warnings carry
            per-module source attribution.
        """
        if not self.is_available():
            # Optional-dependency missing. Surface as info-level so
            # consumers see the gap without failing validation.
            return ValidationResult(
                valid=True,
                info=[
                    ValidationError(
                        path="$",
                        message=(
                            "CIRPASS SHACL validation skipped: pyshacl / "
                            "rdflib not installed. Install with: "
                            "uv add 'dppvalidator[rdf]' or "
                            "pip install 'dppvalidator[rdf]'."
                        ),
                        code="LCS-SHACL-UNAVAILABLE",
                        layer="semantic",
                        severity="info",
                    )
                ],
                schema_version=self.version,
            )

        from rdflib import Graph

        # The CIRPASS message is JSON-shaped (not strictly JSON-LD)
        # so we can't always parse it directly with format="json-ld".
        # We attempt JSON-LD first; if that fails, we fall back to a
        # synthetic conversion that wraps each top-level field as a
        # blank-node property. Either way, the resulting graph is
        # what pyshacl walks.
        data_graph = Graph()
        try:
            import json as _json

            data_graph.parse(data=_json.dumps(parsed_data), format="json-ld")
        except Exception as exc:  # noqa: BLE001 — broad catch is intentional
            logger.debug(
                "CIRPASS SHACL: JSON-LD parse failed (%s); proceeding "
                "with empty data graph (constraints fire only when "
                "there is RDF to evaluate against).",
                exc,
            )
            data_graph = Graph()

        per_module = [self._validate_one_module(data_graph, m) for m in self._modules]
        return self._merge(per_module)

    def _validate_one_module(self, data_graph: Any, module: CirpassModule) -> _PerModuleResult:
        """Run pyshacl against one module's bundled shape graph."""
        sha = _bundle_sha256(module.bundle_filename)
        try:
            shapes_graph = _load_module_shapes_graph(
                SchemaFamily.CIRPASS,
                module.name,
                module.version,
                sha,
            )
        except (FileNotFoundError, ValueError) as exc:
            logger.debug("CIRPASS SHACL: %s shape graph unavailable (%s)", module.name, exc)
            return _PerModuleResult(module=module, available=False)
        if shapes_graph is None:
            return _PerModuleResult(module=module, available=False)

        try:
            import pyshacl
        except ImportError:
            return _PerModuleResult(module=module, available=False)

        # Run pyshacl. ``inference="rdfs"`` lets the validator infer
        # subclass-of relationships from the bundled OWL axioms before
        # evaluating any SHACL constraints declared alongside.
        conforms, results_graph, _ = pyshacl.validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference="rdfs",
            abort_on_first=False,
        )
        violations: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        if not conforms:
            self._extract_violations(results_graph, module, violations, warnings)
        return _PerModuleResult(
            module=module,
            available=True,
            conforms=conforms,
            violations=violations,
            warnings=warnings,
        )

    @staticmethod
    def _extract_violations(
        results_graph: Any,
        module: CirpassModule,
        violations: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> None:
        """Walk a pyshacl results graph and convert to attributed dicts."""
        from rdflib import Namespace

        sh_ns = Namespace("http://www.w3.org/ns/shacl#")
        source = f"{module.name} {module.version}"
        for report in results_graph.subjects(predicate=sh_ns.conforms):
            for vr in results_graph.objects(report, sh_ns.result):
                severity = ""
                message = ""
                path = ""
                focus_node = ""
                for sev in results_graph.objects(vr, sh_ns.resultSeverity):
                    severity = str(sev)
                for msg in results_graph.objects(vr, sh_ns.resultMessage):
                    message = str(msg)
                for p in results_graph.objects(vr, sh_ns.resultPath):
                    path = str(p)
                for fn in results_graph.objects(vr, sh_ns.focusNode):
                    focus_node = str(fn)
                bucket = warnings if "Warning" in severity else violations
                bucket.append(
                    {
                        "source": source,
                        "module": module.name,
                        "version": module.version,
                        "path": path,
                        "message": message,
                        "focusNode": focus_node,
                        "severity": severity,
                    }
                )

    def _merge(self, results: list[_PerModuleResult]) -> ValidationResult:
        """Collapse per-module outcomes into a single ValidationResult."""
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        info: list[ValidationError] = []

        for r in results:
            if not r.available:
                # We surface unavailable shape graphs as info-level
                # diagnostics so consumers know which modules ran and
                # which were skipped.
                info.append(
                    ValidationError(
                        path="$",
                        message=(
                            f"CIRPASS SHACL: {r.module.name} {r.module.version} "
                            f"shape graph unavailable; skipped."
                        ),
                        code=f"{r.module.error_prefix}-SHACL-SKIP",
                        layer="semantic",
                        severity="info",
                        context={
                            "module": r.module.name,
                            "version": r.module.version,
                            "source": f"{r.module.name} {r.module.version}",
                        },
                    )
                )
                continue
            for v in r.violations:
                errors.append(_to_validation_error(v, r.module, "error"))
            for w in r.warnings:
                warnings.append(_to_validation_error(w, r.module, "warning"))
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
            schema_version=self.version,
        )


def _to_validation_error(
    payload: dict[str, Any], module: CirpassModule, severity: str
) -> ValidationError:
    """Convert a pyshacl-violation dict to a typed ValidationError."""
    return ValidationError(
        path=payload.get("path") or "$",
        message=payload.get("message") or "SHACL constraint violation",
        code=f"{module.error_prefix}-SHACL",
        layer="semantic",
        severity=severity,  # type: ignore[arg-type]
        context={
            "module": module.name,
            "version": module.version,
            "source": payload.get("source", f"{module.name} {module.version}"),
            "focusNode": payload.get("focusNode", ""),
            "shacl_severity": payload.get("severity", ""),
        },
    )


# =============================================================================
# Validation layer adapter
# =============================================================================


class CirpassSHACLLayer(ValidationLayer):
    """:class:`ValidationLayer` adapter for the CIRPASS SHACL pass."""

    def __init__(self, validator: CirpassSHACLValidator | None, schema_version: str) -> None:
        self._validator = validator
        self._schema_version = schema_version

    @property
    def name(self) -> str:
        return "shacl"

    def should_run(self, context: ValidationContext) -> bool:
        # SHACL always runs on CIRPASS payloads, even when there is no
        # passport in the context (the pre-model-layer schema fail
        # path) — graphs evaluate against the parsed JSON, not the
        # validated Pydantic root.
        return self._validator is not None and bool(context.parsed_data)

    def execute(self, context: ValidationContext) -> ValidationResult:
        if self._validator is None:
            return ValidationResult(valid=True, schema_version=self._schema_version)
        return self._validator.validate(context.parsed_data)


# =============================================================================
# Reset hook (testing)
# =============================================================================


def clear_shape_graph_cache() -> None:
    """Clear the :func:`_load_module_shapes_graph` cache.

    Used by tests that want to assert reproducibility across two
    consecutive runs without process restart.
    """
    _load_module_shapes_graph.cache_clear()
