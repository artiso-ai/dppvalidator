#!/usr/bin/env python3
"""Regenerate EUDPP enum classes from a vendored TTL.

Phase 1 tasks 1.7–1.11 of [docs/plans/CIRPASS_2_MIGRATION.md] each call
for "regenerate ``X`` enum against the v1.9.1 TTL". This script is the
force-multiplier that turns those tasks from a hand-rewrite into a
single command per module.

Operator workflow (after Phase 0 / Phase 1.1 vendors a v1.9.1 TTL):

    uv run --extra rdf python tools/codegen/cirpass/regenerate_enums.py \\
        --ttl src/dppvalidator/vocabularies/data/ontologies/product_dpp_v1.9.1.ttl \\
        --target class \\
        --namespace https://w3id.org/eudpp/ \\
        --prefix eudpp \\
        --enum-name EUDPPClass \\
        --enum-doc "EU DPP Core Ontology class URIs."

Output: a complete Python `class Foo(str, Enum)` block on stdout, with
a `# generated-from: <ttl-path>@<sha256>` header. Paste-replace the
existing enum body in the corresponding `vocabularies/eudpp_*.py` file.

Targets:

    --target class               owl:Class instances
    --target object-property     owl:ObjectProperty instances
    --target datatype-property   owl:DatatypeProperty instances

Naming convention:

    Local IRI name (CamelCase or snake_case)  →  UPPER_SNAKE Python identifier
    e.g. EnvironmentalFootprint              →  ENVIRONMENTAL_FOOTPRINT
         Carbon_Footprint                    →  CARBON_FOOTPRINT
         linkToPreviousDPP                   →  LINK_TO_PREVIOUS_DPP

Enum value: compact form ``{prefix}:{local}``. Compact form expands to
the canonical IRI via :class:`dppvalidator.vocabularies.ontology.EUDPPNamespace`.

Drift gate: ``tools/codegen/check_drift.py`` re-runs this generator for
every (TTL, target, enum-name) tuple in its config and diffs against
the committed source. Non-zero exit on drift. See workstream X1 in the
migration plan.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# rdflib is in the [rdf] optional-extra; this tool requires it.
# Operators run via ``uv run --extra rdf python ...``.
try:
    from rdflib import Graph, URIRef
    from rdflib.namespace import OWL, RDFS
except ModuleNotFoundError as e:
    print(
        "error: rdflib not installed. Run with `uv run --extra rdf python ...`.",
        file=sys.stderr,
    )
    raise SystemExit(2) from e

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Target → RDF type mapping. Stable enum keyed off the CLI ``--target`` flag.
_TARGET_TO_RDF_TYPE: dict[str, URIRef] = {
    "class": OWL.Class,
    "object-property": OWL.ObjectProperty,
    "datatype-property": OWL.DatatypeProperty,
}


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EnumMember:
    """One row of the regenerated enum."""

    python_name: str  # UPPER_SNAKE Python identifier
    compact_iri: str  # ``prefix:LocalName``
    label: str | None  # rdfs:label (English), if present
    comment: str | None  # rdfs:comment (English), if present

    def render(self) -> str:
        """Render as a single-line enum-member declaration with optional comment."""
        line = f'    {self.python_name} = "{self.compact_iri}"'
        if self.label:
            line += f"  # {self.label}"
        return line


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------


_CAMEL_BOUNDARY_1 = re.compile(r"([a-z0-9])([A-Z])")
_CAMEL_BOUNDARY_2 = re.compile(r"([A-Z]+)([A-Z][a-z])")


def to_upper_snake(local_name: str) -> str:
    """Convert a local IRI name to ``UPPER_SNAKE_CASE``.

    Handles three input shapes:

    1. CamelCase (``EnvironmentalFootprint``)        →  ``ENVIRONMENTAL_FOOTPRINT``
    2. Underscored (``Carbon_Footprint``)            →  ``CARBON_FOOTPRINT``
    3. CamelCase with acronyms (``linkToPreviousDPP``) → ``LINK_TO_PREVIOUS_DPP``

    The two-pass regex inserts boundaries at ``aB`` and ``ABc`` runs,
    leaving consecutive caps intact. The result is uppercase-snake-cased.
    """
    # Pass 1: insert ``_`` between lowercase/digit and following uppercase
    s = _CAMEL_BOUNDARY_1.sub(r"\1_\2", local_name)
    # Pass 2: handle acronym → CamelCase boundary (e.g. HTTPRequest → HTTP_Request)
    s = _CAMEL_BOUNDARY_2.sub(r"\1_\2", s)
    return s.upper()


def local_name_of(iri: str, namespace: str) -> str | None:
    """Return the local name of ``iri`` if it lives under ``namespace``, else None."""
    if iri.startswith(namespace):
        return iri[len(namespace) :]
    # Some ontologies use ``#`` separator instead of ``/``; tolerate both.
    if namespace.endswith("/") and iri.startswith(namespace[:-1] + "#"):
        return iri[len(namespace[:-1] + "#") :]
    return None


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def _english_literal(graph: Graph, subject: URIRef, predicate: URIRef) -> str | None:
    """Return the first English (or untagged) literal for (subject, predicate), trimmed."""
    candidates = list(graph.objects(subject, predicate))
    en: str | None = None
    untagged: str | None = None
    for o in candidates:
        # rdflib literals carry a .language attribute; be defensive.
        lang = getattr(o, "language", None)
        text = str(o).strip()
        if lang == "en":
            en = text
            break
        if lang is None and untagged is None:
            untagged = text
    return en or untagged


def extract_members(
    graph: Graph,
    rdf_type: URIRef,
    namespace: str,
    *,
    prefix: str,
) -> list[EnumMember]:
    """Walk the graph for every ``?s a {rdf_type}`` whose IRI is in ``namespace``."""
    members: list[EnumMember] = []
    seen_python: set[str] = set()

    for subject in graph.subjects(
        predicate=URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), object=rdf_type
    ):
        if not isinstance(subject, URIRef):
            continue
        local = local_name_of(str(subject), namespace)
        if local is None or not local:
            continue

        python_name = to_upper_snake(local)
        if python_name in seen_python:
            # Two IRIs collapsing to the same Python identifier — surface
            # as an error so the operator disambiguates upstream.
            print(
                f"error: duplicate Python identifier {python_name!r} from "
                f"{subject} (already seen). Disambiguate the local name "
                f"in the source TTL.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        seen_python.add(python_name)

        members.append(
            EnumMember(
                python_name=python_name,
                compact_iri=f"{prefix}:{local}",
                label=_english_literal(graph, subject, RDFS.label),
                comment=_english_literal(graph, subject, RDFS.comment),
            )
        )

    members.sort(key=lambda m: m.python_name)
    return members


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _sha256_of_file(path: Path) -> str:
    """LF-normalised SHA-256 of a file (matches the project's manifest scheme)."""
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def render_enum(
    *,
    enum_name: str,
    enum_doc: str,
    members: list[EnumMember],
    ttl_path: Path,
    target: str,
) -> str:
    """Render the full ``class Foo(str, Enum)`` block, ready to paste-replace."""
    sha = _sha256_of_file(ttl_path)
    rel_ttl = ttl_path
    # Best-effort relative path; ``relative_to`` raises ValueError when
    # the TTL lives outside CWD (e.g. invoked from a different repo).
    with contextlib.suppress(ValueError):
        rel_ttl = ttl_path.resolve().relative_to(Path.cwd())

    body = "\n".join(m.render() for m in members) if members else "    pass"

    header = (
        f"# generated-from: {rel_ttl}@{sha} (target={target})\n"
        f"# Regenerated by tools/codegen/cirpass/regenerate_enums.py.\n"
        f"# Editing this block by hand is futile — the next codegen run\n"
        f"# overwrites the changes. Adjust the source TTL upstream instead.\n"
    )

    return f'{header}class {enum_name}(str, Enum):\n    """{enum_doc}"""\n\n{body}\n'


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="regenerate_enums.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--ttl", type=Path, required=True, help="vendored TTL path")
    p.add_argument(
        "--target",
        choices=sorted(_TARGET_TO_RDF_TYPE.keys()),
        required=True,
        help="OWL element kind to extract",
    )
    p.add_argument(
        "--namespace",
        required=True,
        help="IRI prefix to scope extraction to (e.g. https://w3id.org/eudpp/)",
    )
    p.add_argument(
        "--prefix",
        required=True,
        help="compact prefix for enum values (e.g. eudpp, lca, p_dpp)",
    )
    p.add_argument("--enum-name", required=True, help="Python class name for the generated enum")
    p.add_argument(
        "--enum-doc",
        default="Generated EU DPP Core Ontology enum.",
        help="docstring for the generated enum class",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.ttl.is_file():
        print(f"error: TTL not found: {args.ttl}", file=sys.stderr)
        return 1

    graph = Graph()
    graph.parse(args.ttl, format="turtle")

    rdf_type = _TARGET_TO_RDF_TYPE[args.target]
    members = extract_members(graph, rdf_type, args.namespace, prefix=args.prefix)
    if not members:
        print(
            f"warning: no {args.target} members found under namespace "
            f"{args.namespace!r} in {args.ttl}",
            file=sys.stderr,
        )

    sys.stdout.write(
        render_enum(
            enum_name=args.enum_name,
            enum_doc=args.enum_doc,
            members=members,
            ttl_path=args.ttl,
            target=args.target,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
