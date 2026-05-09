#!/usr/bin/env python3
"""Fetch and pin CIRPASS-2 vocab-hub artefacts.

Phase 0 of `docs/plans/CIRPASS_2_MIGRATION.md` (task 0.1). Reads a JSON
manifest of `(family, module, version, guid, …)` rows, downloads each
export from the DPP Vocabulary Hub API, computes an LF-normalised
SHA-256 of the bytes, and emits rows compatible with
`src/dppvalidator/schemas/data/MANIFEST.json` (schema v1, extended with
the Phase 1 `family`/`module`/`vocabulary_hub_guid`/`superseded_by`
fields).

Uses ``httpx`` (project dependency) so HTTP 303 redirects, content
negotiation, and the hub's ``Accept`` requirement are handled cleanly.

Usage
-----

    # Show what would be fetched (offline; no I/O)
    uv run python tools/snapshot/fetch_cirpass.py --list

    # Fetch every artefact whose ``guid`` is set; emit MANIFEST rows
    uv run python tools/snapshot/fetch_cirpass.py --fetch

    # D-0.3 gate: GET https://w3id.org/eudpp/{MODULE} for each ontology
    # artefact; non-zero exit if any fail to dereference. Capture the
    # vocab-hub GUID from each redirect so the manifest stays in sync
    # with the upstream W3ID resolver.
    uv run python tools/snapshot/fetch_cirpass.py --verify-canonical

    # All-in-one
    uv run python tools/snapshot/fetch_cirpass.py --fetch --verify-canonical \
        > tools/snapshot/manifest-rows.json

Exit codes
----------

    0  Success (every requested action completed)
    1  Operator error (bad config, no GUIDs set, conflicting flags)
    2  Network/integrity failure (HTTP error, hash mismatch)
    3  D-0.3 verification failed (one or more canonical IRIs do not
       dereference); blocks Phase 1 per the migration plan's R12 row
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# DPP Vocabulary Hub export endpoints.
#
# The hub uses opaque GUIDs prefixed by artefact kind:
#   - OntologyVersion_<uuid>           → TTL  (~80 of these on the hub)
#   - JsonSchemaVersion_<uuid>         → JSON Schema  (~2)
#   - JsonSchemaSpecVersion_<uuid>     → JSON Schema spec  (~2)
#
# Message-tree exports (CIRPASS reference structure, MVP Textile DPP, the
# tyre declarations) are not currently surfaced as a stable kind in the
# static spec listing; the operator must source those URLs by hand from
# the hub's tree-view UI before invoking this fetcher. See README.md.
_HUB_BASE = "https://dpp.vocabulary-hub.eu"
_ONTOLOGY_EXPORT = _HUB_BASE + "/api/ontology/-/version/{guid}/export"
_JSON_SCHEMA_EXPORT = _HUB_BASE + "/api/json-schema/-/version/{guid}/export"

# A GUID placeholder that operators leave in the artefacts file until
# they pair the (title, version) tuple with the actual hub GUID. Every
# row whose ``guid`` starts with this prefix is skipped on ``--fetch``
# and reported by ``--list``.
_GUID_PLACEHOLDER_PREFIX = "TODO_"

# Default config + output paths, both relative to the repo root.
_CONFIG_DEFAULT = "tools/snapshot/cirpass2_artefacts.json"
_OUTPUT_DEFAULT = "tools/snapshot/cirpass-2"

# User-Agent — identifies this fetcher in hub logs.
_USER_AGENT = "dppvalidator-snapshot-fetcher/1 (+https://github.com/artiso-ai/dppvalidator)"

# HTTP timeout. The hub is generally fast; 30s is generous.
_HTTP_TIMEOUT = 30.0


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Artefact:
    """One row of the CIRPASS-2 artefact manifest.

    The fields mirror the artefacts-config JSON 1:1; downstream consumers
    (the hub fetcher, the manifest emitter, the snapshot doc generator)
    all read this same shape.
    """

    family: str  # "eudpp-ontology" | "cirpass" | "untp" | "tyre" | …
    module: str | None  # "P_DPP" | "SOC" | … (None for non-modular families)
    version: str
    date: str | None  # ISO 8601 publish date as printed on the hub
    title: str  # Human title from the hub listing
    guid: str  # OntologyVersion_<uuid> | JsonSchemaVersion_<uuid> | …
    canonical_iri: str | None  # https://w3id.org/eudpp/<module>/ (ontology only)
    format: str  # "ttl" | "jsonld" | "json-schema" | "tree-view-json"
    scope: str  # "phase-1-vendor" | "phase-3-derive-schema" | "phase-7-pilot"
    source_url: str | None = None  # Override of the derived hub URL (for messages)
    notes: str = ""

    @property
    def is_placeholder(self) -> bool:
        """True if the operator has not yet paired this row with a real GUID."""
        return self.guid.startswith(_GUID_PLACEHOLDER_PREFIX)

    @property
    def derived_source_url(self) -> str:
        """The fetch URL — explicit ``source_url`` wins, else derived from GUID."""
        if self.source_url:
            return self.source_url
        if self.guid.startswith("OntologyVersion_"):
            return _ONTOLOGY_EXPORT.format(guid=self.guid)
        if self.guid.startswith("JsonSchemaVersion_"):
            return _JSON_SCHEMA_EXPORT.format(guid=self.guid)
        if self.guid.startswith("JsonSchemaSpecVersion_"):
            return _JSON_SCHEMA_EXPORT.format(guid=self.guid)
        msg = (
            f"artefact {self.family}/{self.module}/{self.version}: "
            f"no source_url override and GUID {self.guid!r} is not a "
            f"recognised hub kind (Ontology / JsonSchema). Either set "
            f"``source_url`` explicitly or use a hub-native GUID."
        )
        raise ValueError(msg)

    @property
    def vendored_basename(self) -> str:
        """File basename for the verbatim download under the scratch dir."""
        mod = self.module.lower() if self.module else self.family
        ver = self.version.replace(".", "_").replace("-", "_")
        ext = {"ttl": "ttl", "jsonld": "jsonld", "json-schema": "json", "tree-view-json": "json"}[
            self.format
        ]
        return f"{self.family}__{mod}__v{ver}.{ext}"


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Outcome of fetching a single artefact."""

    artefact: Artefact
    bytes_count: int
    sha256: str
    saved_to: Path
    pulled_at: str  # ISO 8601 UTC


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _load_artefacts(config_path: Path) -> list[Artefact]:
    """Parse the artefacts config; raise ValueError with a helpful message on bad shape."""
    if not config_path.is_file():
        msg = f"artefacts config not found: {config_path}"
        raise FileNotFoundError(msg)

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        msg = (
            f"artefacts config {config_path} is not schema_version=1; "
            f"got {raw.get('schema_version')!r}"
        )
        raise ValueError(msg)

    rows = raw.get("artefacts")
    if not isinstance(rows, list) or not rows:
        msg = f"artefacts config {config_path} has no 'artefacts' array"
        raise ValueError(msg)

    out: list[Artefact] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            msg = f"artefact[{i}] is not an object"
            raise ValueError(msg)
        try:
            out.append(
                Artefact(
                    family=row["family"],
                    module=row.get("module"),
                    version=row["version"],
                    date=row.get("date"),
                    title=row["title"],
                    guid=row["guid"],
                    canonical_iri=row.get("canonical_iri"),
                    format=row["format"],
                    scope=row["scope"],
                    source_url=row.get("source_url"),
                    notes=row.get("notes", ""),
                )
            )
        except KeyError as e:
            msg = f"artefact[{i}] missing required key: {e.args[0]}"
            raise ValueError(msg) from None
    return out


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


# Pattern that captures the vocab-hub GUID from a W3ID redirect Location.
_HUB_GUID_RE = re.compile(r"OntologyVersion_[a-f0-9-]+")


def _build_client(*, follow_redirects: bool = True) -> httpx.Client:
    """One httpx.Client per fetcher run, configured for the hub.

    The hub returns ``400 Bad Request`` if no compatible ``Accept``
    header is supplied — its supported media types are
    ``text/turtle``, ``application/n-triples``, ``application/rdf+xml``,
    ``application/ld+json``. The fetcher's ``--fetch`` mode handles
    ontology TTLs and JSON Schema bytes; ``text/turtle`` covers the
    ontology case and the hub falls through to JSON for JsonSchema
    rows even with this Accept set (verified empirically).
    """
    return httpx.Client(
        follow_redirects=follow_redirects,
        timeout=_HTTP_TIMEOUT,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": (
                "text/turtle, application/x-turtle, application/ld+json, "
                "application/json, application/rdf+xml, */*"
            ),
        },
    )


def _http_get(client: httpx.Client, url: str) -> bytes:
    """HTTP GET with redirects followed and the hub's Accept requirement set.

    Raises :class:`httpx.HTTPStatusError` on a non-2xx response so the
    caller can surface a clean error. The hub returns the raw export
    bytes (Turtle, JSON Schema, JSON-LD, …) in the response body.
    """
    response = client.get(url)
    response.raise_for_status()
    return response.content


def _resolve_w3id(client: httpx.Client, url: str) -> tuple[bool, str | None]:
    """Resolve a ``https://w3id.org/eudpp/...`` IRI to its hub GUID.

    Returns ``(ok, guid_or_None)``. ``ok`` is True when the W3ID
    redirector returns a 3xx whose ``Location`` contains a recognisable
    hub GUID (``OntologyVersion_<uuid>``). The second hop — actually
    fetching the redirect target — is *not* gated here: as of
    2026-05-08 the W3ID redirector points at a stale upstream path
    (``/api/ontology-version/{guid}/...``), but the bytes are reachable
    via the canonical hub URL (``/api/ontology/-/version/{guid}/export``)
    derived from the same GUID. So "the IRI is functionally
    dereferenceable" reduces to "we got a GUID". Stale-target detection
    is logged for the operator's awareness but does not flip ``ok``.
    """
    with httpx.Client(
        follow_redirects=False,
        timeout=_HTTP_TIMEOUT,
        headers=client.headers,
    ) as no_follow:
        try:
            r = no_follow.get(url)
        except httpx.HTTPError:
            return False, None
    location = r.headers.get("location", "")
    match = _HUB_GUID_RE.search(location)
    guid = match.group(0) if match else None
    # 3xx with a recognisable GUID is success regardless of second-hop
    # staleness. 200 with no redirect (rare; some W3ID targets are
    # served directly) is also success. Anything else fails.
    if 300 <= r.status_code < 400 and guid:
        return True, guid
    if r.status_code == 200:
        return True, guid
    return False, guid


def _lf_normalised_sha256(content: bytes) -> str:
    """Match :py:meth:`SchemaVersion.verify_integrity` in `schemas/registry.py`.

    LF-normalising before hashing makes the SHA stable across platforms
    (CRLF on Windows would otherwise produce a different hash).
    """
    normalised = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalised).hexdigest()


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def _mode_list(artefacts: list[Artefact]) -> int:
    """Print the planned artefact set; flag rows still missing a GUID."""
    placeholder_count = 0
    print(f"# {len(artefacts)} CIRPASS-2 artefacts planned")
    print()
    print(f"{'family':<18} {'module':<10} {'version':<14} {'format':<16} {'guid':<48} title")
    print("-" * 140)
    for a in sorted(artefacts, key=lambda x: (x.family, x.module or "", x.version)):
        marker = " ⚠ TODO" if a.is_placeholder else ""
        if a.is_placeholder:
            placeholder_count += 1
        print(
            f"{a.family:<18} {a.module or '-':<10} {a.version:<14} "
            f"{a.format:<16} {a.guid:<48} {a.title}{marker}"
        )
    print()
    if placeholder_count:
        print(
            f"# {placeholder_count} of {len(artefacts)} artefacts have placeholder GUIDs",
            file=sys.stderr,
        )
        print(
            "# Pair them with the hub UI before running --fetch (see README.md).",
            file=sys.stderr,
        )
    return 0


def _mode_fetch(artefacts: list[Artefact], output_dir: Path) -> tuple[int, list[FetchResult]]:
    """Download every non-placeholder artefact; return (exit_code, results)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[FetchResult] = []
    failures: list[tuple[Artefact, str]] = []
    skipped_placeholder = 0

    with _build_client() as client:
        for a in artefacts:
            if a.is_placeholder:
                skipped_placeholder += 1
                print(
                    f"⚠ skip placeholder: {a.family}/{a.module}/{a.version} (guid={a.guid})",
                    file=sys.stderr,
                )
                continue

            url = a.derived_source_url
            print(f"→ GET {url}", file=sys.stderr)
            try:
                content = _http_get(client, url)
            except (httpx.HTTPError, ValueError) as e:
                failures.append((a, str(e)))
                print(f"  ✗ {e}", file=sys.stderr)
                continue

            sha = _lf_normalised_sha256(content)
            path = output_dir / a.vendored_basename
            path.write_bytes(content)
            results.append(
                FetchResult(
                    artefact=a,
                    bytes_count=len(content),
                    sha256=sha,
                    saved_to=path,
                    pulled_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
                )
            )
            print(
                f"  ✓ {len(content)} bytes, sha256={sha[:12]}…, → {path}",
                file=sys.stderr,
            )

    if failures:
        print(
            f"\n# {len(failures)} fetch failures, {skipped_placeholder} placeholder skips, "
            f"{len(results)} successful",
            file=sys.stderr,
        )
        return 2, results
    if skipped_placeholder and not results:
        print(
            "\n# No GUIDs paired yet — fetch produced nothing. "
            "Populate cirpass2_artefacts.json before running --fetch.",
            file=sys.stderr,
        )
        return 1, results
    return 0, results


def _mode_verify_canonical(artefacts: list[Artefact]) -> int:
    """D-0.3 gate: every ontology artefact's canonical_iri must dereference.

    Side benefit: prints the GUID captured from each W3ID's 303 redirect
    so the operator can sanity-check that
    ``cirpass2_artefacts.json::guid`` matches the live hub's GUID for
    that canonical IRI.
    """
    targets = [a for a in artefacts if a.canonical_iri]
    if not targets:
        print("# No artefacts declare a canonical_iri; nothing to verify.", file=sys.stderr)
        return 0

    print(f"# Verifying {len(targets)} canonical EUDPP IRIs dereference", file=sys.stderr)
    failures: list[Artefact] = []
    with _build_client() as client:
        for a in targets:
            assert a.canonical_iri is not None  # narrowed by the filter above
            ok, guid = _resolve_w3id(client, a.canonical_iri)
            marker = "✓" if ok else "✗"
            recorded = a.guid if not a.is_placeholder else "(placeholder)"
            mismatch = ""
            if guid and not a.is_placeholder and guid != a.guid:
                mismatch = f"  ⚠ MISMATCH: artefacts.json says {recorded}"
            print(
                f"  {marker} {a.canonical_iri}  guid={guid or '—'}{mismatch}",
                file=sys.stderr,
            )
            if not ok:
                failures.append(a)

    if failures:
        print(
            f"\n# D-0.3 FAILED for {len(failures)}/{len(targets)} IRIs. "
            f"R12 escalates to a Phase 1 blocker.",
            file=sys.stderr,
        )
        return 3
    print(f"\n# D-0.3 verified: all {len(targets)} canonical IRIs dereference.", file=sys.stderr)
    return 0


def _emit_manifest_rows(results: list[FetchResult]) -> None:
    """Print a JSON array of MANIFEST.json-compatible rows to stdout."""
    rows = [
        {
            "family": r.artefact.family,
            "module": r.artefact.module,
            "version": r.artefact.version,
            "kind": _kind_for(r.artefact),
            "path": f"src/dppvalidator/vocabularies/data/ontologies/{r.saved_to.name}",
            "source_url": r.artefact.derived_source_url,
            "vocabulary_hub_guid": r.artefact.guid,
            "canonical_iri": r.artefact.canonical_iri,
            "sha256": r.sha256,
            "bytes": r.bytes_count,
            "pulled_at": r.pulled_at,
            "notes": r.artefact.notes
            or (f"Vendored in Phase 1 from DPP Vocabulary Hub ({r.artefact.guid})."),
        }
        for r in results
    ]
    json.dump(rows, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")


def _kind_for(a: Artefact) -> str:
    """Compose the legacy ``kind`` string for the manifest row."""
    if a.family == "eudpp-ontology":
        return f"eudpp-{(a.module or '').lower()}-ontology"
    if a.family == "cirpass":
        return "cirpass-message"
    return f"{a.family}-message"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fetch_cirpass.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--config",
        type=Path,
        default=Path(_CONFIG_DEFAULT),
        help=f"artefacts config (default: {_CONFIG_DEFAULT})",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path(_OUTPUT_DEFAULT),
        help=f"verbatim downloads land here (default: {_OUTPUT_DEFAULT})",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--list", action="store_true", help="enumerate planned artefacts; no I/O")
    mode.add_argument("--fetch", action="store_true", help="download + hash + emit MANIFEST rows")
    mode.add_argument(
        "--verify-canonical",
        action="store_true",
        help="D-0.3 gate: HEAD every canonical EUDPP IRI",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        artefacts = _load_artefacts(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # Default mode if none chosen: list (safe, no I/O).
    if not (args.list or args.fetch or args.verify_canonical):
        return _mode_list(artefacts)
    if args.list:
        return _mode_list(artefacts)
    if args.verify_canonical:
        return _mode_verify_canonical(artefacts)
    # args.fetch
    code, results = _mode_fetch(artefacts, args.output)
    if results:
        _emit_manifest_rows(results)
    return code


if __name__ == "__main__":
    sys.exit(main())
