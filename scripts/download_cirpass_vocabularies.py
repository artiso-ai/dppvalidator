#!/usr/bin/env python3
"""Download CIRPASS-2 vocabularies from the DPP Vocabulary Hub.

This script fetches the latest ontologies, JSON schemas, and API specs
from the CIRPASS-2 project for use in dppvalidator.
"""

import asyncio
import logging
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://dpp.vocabulary-hub.eu"

# Target directories (resolve for CI/CD robustness)
DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "dppvalidator" / "vocabularies" / "data"
ONTOLOGIES_DIR = DATA_DIR / "ontologies"
SCHEMAS_DIR = DATA_DIR / "schemas"

# Priority 1: Core Ontology Modules (TTL format) - Latest versions only
PRIORITY_1_ONTOLOGIES = {
    "eudpp_core_v1.3.1.ttl": (
        f"{BASE_URL}/api/ontology-version/OntologyVersion_b9d20c7a-a6d2-43b4-96f1-467e66911f3b/export?format=turtle"
    ),
    "product_dpp_v1.7.1.ttl": (
        f"{BASE_URL}/api/ontology-version/OntologyVersion_d8046709-cc88-453f-a374-8e964101a3db/export?format=turtle"
    ),
    "actors_roles_v1.5.1.ttl": (
        f"{BASE_URL}/api/ontology-version/OntologyVersion_40443b4b-c2eb-4a14-a0f8-5b653d441a5e/export?format=turtle"
    ),
    "soc_v1.4.7.ttl": (
        f"{BASE_URL}/api/ontology-version/OntologyVersion_0ed82e77-a4ac-4baa-908f-ae36ce0692c0/export?format=turtle"
    ),
    "lca_v2.0.ttl": (
        f"{BASE_URL}/api/ontology-version/OntologyVersion_08381633-1ffe-4fd8-bc38-88d47062aab5/export?format=turtle"
    ),
}

# Priority 2: JSON Schema (for validation)
PRIORITY_2_SCHEMAS = {
    "cirpass_dpp_schema.json": (
        f"{BASE_URL}/api/wizard/export/Message_5cbe085e-4445-4daa-b3db-82fd162ef73d/json/schema?format=json"
    ),
    "cirpass_dpp_schema.yaml": (
        f"{BASE_URL}/api/wizard/export/Message_5cbe085e-4445-4daa-b3db-82fd162ef73d/json/schema?format=yaml"
    ),
    "cirpass_dpp_shacl.ttl": (
        f"{BASE_URL}/api/wizard/export/Message_5cbe085e-4445-4daa-b3db-82fd162ef73d/rdf/shacl?format=ttl"
    ),
}

# Priority 3: API Specs (optional)
PRIORITY_3_API_SPECS = {
    "cirpass_dpp_openapi.json": (
        f"{BASE_URL}/api/wizard/export/Message_5cbe085e-4445-4daa-b3db-82fd162ef73d/openapi?format=json"
    ),
    "cirpass_dpp_schema.xsd": (
        f"{BASE_URL}/api/wizard/export/Message_5cbe085e-4445-4daa-b3db-82fd162ef73d/xml/schema?style=doll"
    ),
}


async def download_file(
    client: httpx.AsyncClient,
    url: str,
    target_path: Path,
    *,
    timeout: float = 60.0,
) -> bool:
    """Download a file from URL to target path."""
    try:
        logger.info(f"Downloading: {target_path.name}")
        response = await client.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(response.content)

        size_kb = len(response.content) / 1024
        logger.info(f"  ✓ {target_path.name} ({size_kb:.1f} KB)")
        return True

    except httpx.HTTPStatusError as e:
        logger.error(f"  ✗ {target_path.name}: HTTP {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        logger.error(f"  ✗ {target_path.name}: {e}")
        return False


async def download_resources(
    resources: dict[str, str],
    target_dir: Path,
    category: str,
) -> tuple[int, int]:
    """Download a category of resources."""
    logger.info(f"\n{'=' * 60}")
    logger.info(f"{category}")
    logger.info(f"{'=' * 60}")

    success = 0
    failed = 0

    async with httpx.AsyncClient() as client:
        tasks = [
            download_file(client, url, target_dir / filename) for filename, url in resources.items()
        ]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result:
                success += 1
            else:
                failed += 1

    return success, failed


async def main() -> None:
    """Download all CIRPASS-2 vocabulary resources."""
    logger.info("CIRPASS-2 Vocabulary Downloader")
    logger.info("================================\n")

    total_success = 0
    total_failed = 0

    # Priority 1: Ontologies
    s, f = await download_resources(
        PRIORITY_1_ONTOLOGIES,
        ONTOLOGIES_DIR,
        "Priority 1: Core Ontology Modules",
    )
    total_success += s
    total_failed += f

    # Priority 2: Schemas
    s, f = await download_resources(
        PRIORITY_2_SCHEMAS,
        SCHEMAS_DIR,
        "Priority 2: JSON Schema & SHACL",
    )
    total_success += s
    total_failed += f

    # Priority 3: API Specs
    s, f = await download_resources(
        PRIORITY_3_API_SPECS,
        SCHEMAS_DIR,
        "Priority 3: API Specifications",
    )
    total_success += s
    total_failed += f

    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("SUMMARY")
    logger.info(f"{'=' * 60}")
    logger.info(f"Successfully downloaded: {total_success}")
    logger.info(f"Failed: {total_failed}")

    if total_failed > 0:
        logger.warning("\nSome downloads failed. Check the logs above for details.")
    else:
        logger.info("\n✓ All downloads completed successfully!")

    # Show target directories
    logger.info("\nFiles saved to:")
    logger.info(f"  Ontologies: {ONTOLOGIES_DIR}")
    logger.info(f"  Schemas:    {SCHEMAS_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
