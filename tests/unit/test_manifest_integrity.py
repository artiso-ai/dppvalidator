"""Phase 5 acceptance test: every bundled artefact matches MANIFEST.json.

Cardinal rule 4 from ``.claude/rules/untp-versioning.md``:

> Bundled artefacts have a manifest. Every JSON Schema and JSON-LD
> context vendored under ``src/dppvalidator/schemas/data/`` or
> ``src/dppvalidator/vocabularies/data/`` MUST appear in
> ``src/dppvalidator/schemas/data/MANIFEST.json`` with version, source
> URL, SHA-256, and pull date. CI verifies the hashes.

This module is the CI verification end of that contract:

1. Every entry in MANIFEST.json points at a file that exists.
2. Each file's SHA-256 matches the manifest pin.
3. The manifest is well-formed (every entry has the required fields).
4. (Drift catch) Every bundled JSON Schema / JSON-LD artefact is
   *covered* by the manifest — adding a vendored file without a
   manifest entry fails the suite.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_PATH = _REPO_ROOT / "src" / "dppvalidator" / "schemas" / "data" / "MANIFEST.json"

# Required keys every artefact entry must have.
_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {"version", "kind", "path", "source_url", "sha256", "pulled_at"}
)

# Vendored-data directories scanned by the drift-catch test.
_VENDORED_DIRS: tuple[Path, ...] = (
    _REPO_ROOT / "src" / "dppvalidator" / "schemas" / "data",
    _REPO_ROOT / "src" / "dppvalidator" / "vocabularies" / "data",
)

# File extensions that count as "vendored" for the drift-catch test.
# README.md and __init__.py are infrastructure, not data, and don't need
# manifest entries.
_TRACKED_EXTENSIONS: frozenset[str] = frozenset({".json", ".jsonld"})

# Known files that intentionally aren't tracked by MANIFEST.json. These
# fall into two buckets:
#
# 1. Project-curated lists that don't have a single upstream-pinned
#    source (countries, units, materials, HS codes).
# 2. CIRPASS-schema files: the CIRPASS axis has its own version pin
#    (``CIRPASS_SCHEMA_VERSION`` in ``schemas/cirpass_loader.py``);
#    folding them into MANIFEST.json would conflate two version axes.
_UNTRACKED_FILES: frozenset[str] = frozenset(
    {
        "MANIFEST.json",  # the manifest itself
        # Project-curated vocab data.
        "countries.json",
        "units.json",
        "materials.json",
        "hs_codes.json",
        # CIRPASS schemas — separate version axis (cirpass_loader.py).
        "cirpass_dpp_schema.json",
        "cirpass_dpp_openapi.json",
    }
)


def _load_manifest() -> dict[str, Any]:
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def _normalise_for_hash(content: bytes) -> bytes:
    """Match the SHA-256 normalisation used by the registry's verifier.

    ``SchemaVersion.verify_integrity`` normalises ``\\r\\n`` to ``\\n``
    before hashing so cross-platform line-ending differences don't
    invalidate the pins. The manifest hashes are computed against the
    same normalised bytes.
    """
    return content.replace(b"\r\n", b"\n")


# ---------------------------------------------------------------------------
# Manifest is well-formed
# ---------------------------------------------------------------------------


class TestManifestStructure:
    """Sanity checks on MANIFEST.json itself."""

    def test_manifest_file_exists(self) -> None:
        assert _MANIFEST_PATH.is_file(), f"missing manifest at {_MANIFEST_PATH}"

    def test_manifest_is_valid_json(self) -> None:
        # Will raise if the manifest is malformed.
        _load_manifest()

    def test_manifest_has_artefacts_array(self) -> None:
        manifest = _load_manifest()
        assert isinstance(manifest.get("artefacts"), list)
        assert manifest["artefacts"], "artefacts array is empty"

    def test_every_entry_has_required_fields(self) -> None:
        manifest = _load_manifest()
        for entry in manifest["artefacts"]:
            missing = _REQUIRED_FIELDS - set(entry.keys())
            assert not missing, (
                f"manifest entry for {entry.get('path')!r} missing fields: {sorted(missing)}"
            )

    def test_paths_are_repo_relative(self) -> None:
        """Every ``path`` field is a relative path under ``src/``."""
        manifest = _load_manifest()
        for entry in manifest["artefacts"]:
            path = entry["path"]
            assert not path.startswith("/"), f"path is absolute: {path!r}"
            assert path.startswith("src/dppvalidator/"), (
                f"path is not under src/dppvalidator/: {path!r}"
            )

    def test_optional_phase1_fields_have_known_shapes(self) -> None:
        """Phase 1 task 1.2 added optional fields; validate when present.

        New optional fields:
        - ``family``: ``"untp" | "cirpass" | "eudpp-ontology"``.
        - ``module``: short module name (uppercase letters / underscores
          only, e.g. ``P_DPP``, ``SOC``, ``LCA``, ``ACTOR``, ``CON``).
        - ``vocabulary_hub_guid``: ``OntologyVersion_<uuid>`` /
          ``JsonSchemaVersion_<uuid>`` / ``JsonSchemaSpecVersion_<uuid>``,
          or a ``TODO_*`` placeholder during the Phase 0 transition.
        - ``superseded_by``: a manifest key ``<kind>@<version>`` matching
          another row in the same manifest.
        """
        import re

        manifest = _load_manifest()
        legal_families = {"untp", "cirpass", "eudpp-ontology"}
        guid_pattern = re.compile(
            r"^(OntologyVersion|JsonSchemaVersion|JsonSchemaSpecVersion|TODO)_[A-Za-z0-9_-]+$"
        )
        module_pattern = re.compile(r"^[A-Z][A-Z0-9_]*$")
        all_keys = {f"{entry['kind']}@{entry['version']}" for entry in manifest["artefacts"]}

        for entry in manifest["artefacts"]:
            label = f"{entry.get('kind')}@{entry.get('version')}"

            family = entry.get("family")
            if family is not None:
                assert family in legal_families, (
                    f"manifest row {label!r} has unknown family {family!r}; "
                    f"expected one of {sorted(legal_families)}"
                )

            module = entry.get("module")
            if module is not None:
                assert module_pattern.match(module), (
                    f"manifest row {label!r} has malformed module {module!r}; "
                    f"expected uppercase letters / digits / underscores"
                )

            guid = entry.get("vocabulary_hub_guid")
            if guid is not None:
                assert guid_pattern.match(guid), (
                    f"manifest row {label!r} has malformed "
                    f"vocabulary_hub_guid {guid!r}; expected one of "
                    f"OntologyVersion_/JsonSchemaVersion_/"
                    f"JsonSchemaSpecVersion_/TODO_ prefix + UUID"
                )

            superseded_by = entry.get("superseded_by")
            if superseded_by is not None:
                assert superseded_by in all_keys, (
                    f"manifest row {label!r} declares superseded_by="
                    f"{superseded_by!r}, which is not a key in the same "
                    f"manifest (expected ``<kind>@<version>``)"
                )


# ---------------------------------------------------------------------------
# Each manifest entry resolves to an existing file with matching hash
# ---------------------------------------------------------------------------


def _manifest_entries_with_files() -> list[tuple[str, Path, str]]:
    """Materialise ``(label, file_path, expected_sha256)`` triples."""
    manifest = _load_manifest()
    out: list[tuple[str, Path, str]] = []
    for entry in manifest["artefacts"]:
        label = f"{entry['kind']}@{entry['version']}"
        out.append(
            (label, _REPO_ROOT / entry["path"], entry["sha256"]),
        )
    return out


@pytest.mark.parametrize(
    ("label", "file_path", "expected_sha256"),
    _manifest_entries_with_files(),
    ids=lambda v: v if isinstance(v, str) else getattr(v, "name", str(v)),
)
def test_manifest_entry_file_exists_and_hash_matches(
    label: str, file_path: Path, expected_sha256: str
) -> None:
    """The bundled file exists and its SHA-256 matches the manifest pin.

    Failure here means either:
    - the file was edited without re-running the manifest update; or
    - the manifest pin is stale.

    Either way: re-pull the upstream artefact, refresh the SHA in
    MANIFEST.json, and re-run the suite.
    """
    assert file_path.is_file(), f"manifest entry {label!r} points at missing file {file_path}"
    raw = file_path.read_bytes()
    actual = hashlib.sha256(_normalise_for_hash(raw)).hexdigest()
    assert actual == expected_sha256, (
        f"SHA-256 mismatch for {label} ({file_path.name}):\n"
        f"  manifest: {expected_sha256}\n"
        f"  on disk:  {actual}\n"
        "Either the file was modified or the manifest is stale."
    )


# ---------------------------------------------------------------------------
# Drift catch: every vendored .json/.jsonld is in the manifest
# ---------------------------------------------------------------------------


def _all_vendored_files() -> list[Path]:
    """Return every vendored file under the tracked data directories.

    Skips directory infrastructure (``__init__.py``, ``__pycache__``,
    ``README.md``) and files in the explicit allow-list of
    project-curated vocabularies (``countries.json`` etc.).
    """
    out: list[Path] = []
    for root in _VENDORED_DIRS:
        if not root.is_dir():  # pragma: no cover — repo layout is stable
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in _TRACKED_EXTENSIONS:
                continue
            if path.name in _UNTRACKED_FILES:
                continue
            out.append(path)
    return sorted(out)


def test_every_vendored_file_is_manifested() -> None:
    """Every ``.json``/``.jsonld`` under data dirs has a manifest entry.

    Adding a new vendored upstream artefact without a manifest entry
    silently bypasses CI hash verification — this guard catches that
    drift.
    """
    manifest = _load_manifest()
    manifested_paths = {(_REPO_ROOT / e["path"]).resolve() for e in manifest["artefacts"]}
    untracked: list[Path] = []
    for vendored in _all_vendored_files():
        if vendored.resolve() not in manifested_paths:
            untracked.append(vendored.relative_to(_REPO_ROOT))
    assert not untracked, (
        f"{len(untracked)} vendored file(s) lack manifest entries:\n"
        + "\n".join(f"  - {p}" for p in untracked)
        + "\nAdd them to src/dppvalidator/schemas/data/MANIFEST.json or "
        "extend tests/unit/test_manifest_integrity.py:_UNTRACKED_FILES if "
        "they're project-curated (not vendored)."
    )
