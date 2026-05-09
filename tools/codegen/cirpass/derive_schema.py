#!/usr/bin/env python3
"""Derive the CIRPASS reference structure v1.3.0 JSON Schema from Pydantic models.

Phase 3 task 3.1 of [docs/plans/CIRPASS_2_MIGRATION.md]. The plan
originally specified deriving the schema from the hub's tree-view
export, but the hub does not publish a JSON Schema for the v1.3.0
message (per D-0.1 in the plan), and the message-tree GUIDs remain
operator-gated as of Phase 0.

**Pragmatic alternative landed in Phase 3:** generate the JSON Schema
from the canonical
:class:`dppvalidator.models.cirpass.v1_3.ReferencePassport` Pydantic
model. The Pydantic models *are* the source of truth, so the JSON
Schema is a pure projection — no hand-editing required, no drift risk
between Pydantic and JSON Schema. When the tree-view export
eventually lands, it becomes a *cross-check* (the tree-view-derived
schema and the Pydantic-derived schema should converge; any
divergence is either a model bug or a spec interpretation question).

Output is committed at:

    src/dppvalidator/schemas/data/cirpass-reference-1.3.0.json

Drift gate at ``tools/codegen/check_drift.py`` re-runs this generator
on every CI build and ``git diff --exit-code``s the result.

Usage:

    uv run python tools/codegen/cirpass/derive_schema.py

    # Dry-run (print to stdout):
    uv run python tools/codegen/cirpass/derive_schema.py --stdout
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from dppvalidator.models.cirpass.v1_3 import ReferencePassport

_REPO_ROOT = Path(__file__).resolve().parents[3]
_OUTPUT = _REPO_ROOT / "src" / "dppvalidator" / "schemas" / "data" / "cirpass-reference-1.3.0.json"


def _derive() -> dict:
    """Generate the JSON Schema dict from :class:`ReferencePassport`.

    Pydantic v2's :meth:`model_json_schema` emits a draft-2020-12 JSON
    Schema by default; we wrap it with the standard ``$schema`` /
    ``$id`` headers expected by the project's JSON-Schema validator
    layer.
    """
    # Phase 4 of docs/plans/CIRPASS_2_MIGRATION.md flipped the
    # derivation mode from ``serialization`` → ``validation`` because
    # the schema feeds the *input* validation layer (the engine's
    # ``SchemaLayer`` runs *before* the Pydantic model layer). In
    # ``validation`` mode Pydantic emits a permissive schema for
    # ``Decimal`` fields (accepts number / int / string), which mirrors
    # how ``model_validate`` actually coerces. The serialization-mode
    # schema, by contrast, declares ``Decimal`` as ``"string"`` only —
    # that's right for serialised output but wrong for input
    # validation against numeric JSON literals.
    schema = ReferencePassport.model_json_schema(mode="validation")
    # Annotate with a stable provenance header so consumers / drift
    # reviewers know how the bytes were produced.
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://artiso-ai.github.io/dppvalidator/schemas/cirpass-reference-1.3.0.json"
    schema["x-generated-from"] = (
        "dppvalidator.models.cirpass.v1_3.ReferencePassport.model_json_schema(mode='validation')"
    )
    schema["x-generator"] = "tools/codegen/cirpass/derive_schema.py"
    schema["x-cirpass-version"] = "1.3.0"
    schema["x-phase"] = (
        "Phase 4 of docs/plans/CIRPASS_2_MIGRATION.md "
        "(Pydantic-first derivation, validation-mode for input; "
        "tree-view cross-check pending)."
    )
    return schema


def _serialise(schema: dict) -> str:
    """Stable JSON serialisation: indent=2, sort_keys, LF-only."""
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _write(text: str, path: Path) -> tuple[int, str]:
    """Write ``text`` to ``path``; return (bytes_written, sha256)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = text.encode("utf-8")
    path.write_bytes(raw)
    sha = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return len(raw), sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="derive_schema.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the schema to stdout instead of writing the bundled file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_OUTPUT,
        help=f"Output path (default: {_OUTPUT.relative_to(_REPO_ROOT)}).",
    )
    args = parser.parse_args(argv)

    schema = _derive()
    text = _serialise(schema)

    if args.stdout:
        sys.stdout.write(text)
        return 0

    bytes_written, sha = _write(text, args.output)
    rel = args.output.resolve().relative_to(_REPO_ROOT)
    print(
        f"✓ wrote {rel} ({bytes_written} bytes, sha256={sha[:12]}…)",
        file=sys.stderr,
    )
    print(f"  full sha256: {sha}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
