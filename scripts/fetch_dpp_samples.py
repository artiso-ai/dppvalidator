#!/usr/bin/env python3
"""
Script to fetch and evaluate Digital Product Passport samples for testing.

Downloads DPP samples from various sources and evaluates their structure
to determine if they are valid candidates for testing the dppvalidator library.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

# Raw URLs provided by the user (with duplicates and fragments)
RAW_URLS = """
https://untp-verifiable-credentials.s3.amazonaws.com/bc075c5f-2304-4b3f-bb24-46d9fa9a8e60.json
https://spherity.github.io/schemas/testing/breathable-t-shirt.json
https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/io.catenax.battery.battery_pass/6.0.0/gen/BatteryPass.json
https://zenodo.org/records/15279026/preview/untp-dpp-instance-0.5.0-computer.json.txt
https://test.uncefact.org/vocabulary/untp/dia/DigitalIdentityAnchor-instance-0.6.1.json
https://opensource.unicc.org/phila/spec-untp/-/raw/main/website/samples/untp-digital-facility-record-v0.3.9.json
https://opensource.unicc.org/11dot2/spec-untp/-/raw/main/website/samples/untp-digital-product-passport-v0.3.10.json
https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-instance-0.6.0.json
https://batterypass.github.io/BatteryPassDataModel/BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/gen/GeneralProductInformation-payload.json
https://batterypass.github.io/BatteryPassDataModel//BatteryPass/io.BatteryPass.CarbonFootprint/1.2.0/gen/CarbonFootprintForBatteries-payload.json
https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/gen/GeneralProductInformation-ld.json
https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.CarbonFootprint/1.2.0/gen/CarbonFootprintForBatteries-ld.json
https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.Circularity/1.2.0/gen/Circularity-ld.json
https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.MaterialComposition/1.2.0/gen/MaterialComposition-ld.json
https://nfc-forum.org/ndpp/long-dpp-example.json
https://batterypass.github.io/BatteryPassDataModel//BatteryPass/io.BatteryPass.MaterialComposition/1.2.0/gen/MaterialComposition-payload.json
"""


@dataclass
class Evaluation:
    """Evaluation results for a DPP sample."""

    is_json_ld: bool = False
    has_context: bool = False
    has_type: bool = False
    detected_type: str | list[str] | None = None
    is_verifiable_credential: bool = False
    is_dpp_like: bool = False
    is_battery_pass: bool = False
    is_schema: bool = False
    has_product_info: bool = False
    top_level_keys: list[str] = field(default_factory=list)
    recommendation: str = "unknown"
    notes: list[str] = field(default_factory=list)


@dataclass
class DPPSample:
    """Represents a downloaded DPP sample with metadata."""

    url: str
    filename: str
    content: dict[str, Any] | None = None
    error: str | None = None
    content_hash: str | None = None
    evaluation: Evaluation = field(default_factory=Evaluation)

    @property
    def is_valid(self) -> bool:
        return self.content is not None and self.error is None


def clean_and_dedupe_urls(raw_urls: str) -> list[str]:
    """Parse, clean (remove fragments), and deduplicate URLs."""
    urls = []
    for line in raw_urls.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Handle malformed URLs (two URLs concatenated)
        if "https://" in line[8:]:
            parts = re.split(r"(?=https://)", line)
            for part in parts:
                if part:
                    urls.append(part)
        else:
            urls.append(line)

    # Remove fragments and deduplicate
    cleaned = []
    seen = set()
    for url in urls:
        parsed = urlparse(url)
        # Rebuild URL without fragment, normalize double slashes in path
        clean_path = re.sub(r"//+", "/", parsed.path)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{clean_path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"

        if clean_url not in seen:
            seen.add(clean_url)
            cleaned.append(clean_url)

    return cleaned


def derive_filename(url: str) -> str:
    """Derive a meaningful filename from the URL."""
    parsed = urlparse(url)
    path = parsed.path

    # Get the base filename
    basename = Path(path).name
    if not basename or basename == "":
        basename = "unknown"

    # Remove .txt extension if present (some JSON files have .json.txt)
    if basename.endswith(".json.txt"):
        basename = basename[:-4]
    elif not basename.endswith(".json"):
        basename += ".json"

    # Add source prefix for clarity
    domain = parsed.netloc.replace(".", "_")
    if "github" in domain or "githubusercontent" in domain:
        # Extract repo/org info
        parts = path.split("/")
        if len(parts) >= 2:
            org_repo = "_".join(p for p in parts[1:3] if p)
            return f"{org_repo}_{basename}"

    return f"{domain}_{basename}"


def evaluate_dpp_structure(data: dict[str, Any]) -> Evaluation:
    """Evaluate if the JSON structure appears to be a valid DPP candidate."""
    evaluation = Evaluation()

    if not isinstance(data, dict):
        evaluation.notes.append("Not a JSON object")
        evaluation.recommendation = "reject"
        return evaluation

    keys = list(data.keys())
    evaluation.top_level_keys = keys[:20]  # Limit for readability

    # Check for JSON-LD markers
    if "@context" in data:
        evaluation.has_context = True
        evaluation.is_json_ld = True

    if "@type" in data or "type" in data:
        evaluation.has_type = True
        type_val = data.get("@type") or data.get("type")
        if isinstance(type_val, list):
            evaluation.detected_type = type_val
        else:
            evaluation.detected_type = str(type_val) if type_val else None

    # Check for Verifiable Credential structure
    vc_indicators = ["credentialSubject", "issuer", "issuanceDate", "proof"]
    vc_count = sum(1 for k in vc_indicators if k in data)
    if vc_count >= 2:
        evaluation.is_verifiable_credential = True

    # Check for DPP-like structure
    dpp_indicators = [
        "product",
        "productIdentifier",
        "productName",
        "manufacturer",
        "manufacturerInformation",
        "circularity",
        "sustainability",
        "materials",
        "materialComposition",
        "carbonFootprint",
    ]
    dpp_count = sum(1 for k in dpp_indicators if k in data or k in str(data).lower())
    if dpp_count >= 2:
        evaluation.is_dpp_like = True

    # Check for Battery Pass specific fields
    battery_indicators = [
        "batteryId",
        "batteryModel",
        "batteryCategory",
        "batteryWeight",
        "ratedCapacity",
        "batteryStatus",
        "stateOfHealth",
        "stateOfCharge",
    ]
    battery_count = sum(1 for k in battery_indicators if k in str(data))
    if battery_count >= 2:
        evaluation.is_battery_pass = True

    # Check if it's a schema rather than an instance
    schema_indicators = ["$schema", "$id", "properties", "definitions", "required"]
    schema_count = sum(1 for k in schema_indicators if k in data)
    if schema_count >= 3:
        evaluation.is_schema = True
        evaluation.notes.append("Appears to be a JSON Schema, not a DPP instance")

    # Check for product information
    if "product" in data or "credentialSubject" in data:
        evaluation.has_product_info = True

    # Determine recommendation
    if evaluation.is_schema:
        evaluation.recommendation = "schema_only"
    elif evaluation.is_verifiable_credential and evaluation.is_dpp_like:
        evaluation.recommendation = "excellent"
        evaluation.notes.append("Verifiable Credential with DPP structure")
    elif evaluation.is_verifiable_credential:
        evaluation.recommendation = "good"
        evaluation.notes.append("Verifiable Credential structure")
    elif evaluation.is_battery_pass:
        evaluation.recommendation = "good"
        evaluation.notes.append("Battery Pass data")
    elif evaluation.is_dpp_like:
        evaluation.recommendation = "moderate"
        evaluation.notes.append("DPP-like structure without VC wrapper")
    elif evaluation.is_json_ld:
        evaluation.recommendation = "maybe"
        evaluation.notes.append("JSON-LD but structure unclear")
    else:
        evaluation.recommendation = "review"
        evaluation.notes.append("Structure needs manual review")

    return evaluation


def fetch_sample(client: httpx.Client, url: str) -> DPPSample:
    """Fetch a single DPP sample from URL."""
    filename = derive_filename(url)
    sample = DPPSample(url=url, filename=filename)

    try:
        response = client.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()

        content_text = response.text
        sample.content_hash = hashlib.sha256(content_text.encode()).hexdigest()[:16]

        # Try to parse as JSON
        sample.content = json.loads(content_text)
        sample.evaluation = evaluate_dpp_structure(sample.content)

    except httpx.HTTPStatusError as e:
        sample.error = f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
    except httpx.RequestError as e:
        sample.error = f"Request error: {e}"
    except json.JSONDecodeError as e:
        sample.error = f"Invalid JSON: {e}"
    except Exception as e:
        sample.error = f"Unexpected error: {e}"

    return sample


def fetch_all_samples(urls: list[str]) -> list[DPPSample]:
    """Fetch all DPP samples from the provided URLs."""
    samples = []

    with httpx.Client(
        headers={
            "User-Agent": "dppvalidator-sample-fetcher/1.0",
            "Accept": "application/json, application/ld+json, text/plain",
        }
    ) as client:
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Fetching: {url[:80]}...")
            sample = fetch_sample(client, url)
            samples.append(sample)

            if sample.error:
                print(f"  ❌ Error: {sample.error}")
            else:
                print(f"  ✓ {sample.filename} -> {sample.evaluation.recommendation}")

    return samples


def generate_report(samples: list[DPPSample]) -> str:
    """Generate a markdown report of the evaluation results."""
    lines = ["# DPP Sample Evaluation Report\n"]

    # Summary
    total = len(samples)
    success = sum(1 for s in samples if s.is_valid)
    failed = total - success

    lines.append("## Summary\n")
    lines.append(f"- **Total URLs**: {total}")
    lines.append(f"- **Successfully fetched**: {success}")
    lines.append(f"- **Failed**: {failed}\n")

    # Group by recommendation
    by_rec: dict[str, list[DPPSample]] = {}
    for s in samples:
        rec = s.evaluation.recommendation if s.is_valid else "failed"
        by_rec.setdefault(rec, []).append(s)

    lines.append("## By Recommendation\n")
    order = ["excellent", "good", "moderate", "maybe", "schema_only", "review", "failed"]
    for rec in order:
        if rec in by_rec:
            lines.append(f"### {rec.upper()} ({len(by_rec[rec])})\n")
            for s in by_rec[rec]:
                if s.is_valid:
                    notes = ", ".join(s.evaluation.notes)
                    lines.append(f"- `{s.filename}`: {notes}")
                else:
                    lines.append(f"- `{s.filename}`: {s.error}")
                lines.append(f"  - URL: {s.url}")
            lines.append("")

    # Detailed evaluation
    lines.append("## Detailed Evaluation\n")
    for s in samples:
        lines.append(f"### {s.filename}\n")
        lines.append(f"- **URL**: {s.url}")
        if s.error:
            lines.append(f"- **Error**: {s.error}")
        else:
            lines.append(f"- **Hash**: {s.content_hash}")
            lines.append(f"- **Recommendation**: {s.evaluation.recommendation}")
            lines.append(f"- **Is JSON-LD**: {s.evaluation.is_json_ld}")
            lines.append(f"- **Is VC**: {s.evaluation.is_verifiable_credential}")
            lines.append(f"- **Is DPP-like**: {s.evaluation.is_dpp_like}")
            lines.append(f"- **Is Battery Pass**: {s.evaluation.is_battery_pass}")
            lines.append(f"- **Is Schema**: {s.evaluation.is_schema}")
            lines.append(f"- **Type**: {s.evaluation.detected_type}")
            lines.append(f"- **Top keys**: {', '.join(s.evaluation.top_level_keys[:10])}")
            if s.evaluation.notes:
                lines.append(f"- **Notes**: {'; '.join(s.evaluation.notes)}")
        lines.append("")

    return "\n".join(lines)


def save_samples(samples: list[DPPSample], output_dir: Path) -> None:
    """Save valid samples to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by hash to avoid duplicates
    by_hash: dict[str, DPPSample] = {}
    for s in samples:
        if s.is_valid and s.content_hash and s.content_hash not in by_hash:
            by_hash[s.content_hash] = s

    for sample in by_hash.values():
        filepath = output_dir / sample.filename
        # Avoid overwriting - add hash suffix if exists
        if filepath.exists():
            stem = filepath.stem
            filepath = output_dir / f"{stem}_{sample.content_hash}.json"

        with open(filepath, "w") as f:
            json.dump(sample.content, f, indent=2)
        print(f"Saved: {filepath.name}")


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("DPP Sample Fetcher and Evaluator")
    print("=" * 60)

    # Parse and dedupe URLs
    urls = clean_and_dedupe_urls(RAW_URLS)
    print(f"\nFound {len(urls)} unique URLs to process.\n")

    # Fetch all samples
    samples = fetch_all_samples(urls)

    # Generate and save report
    report = generate_report(samples)
    report_path = Path(__file__).parent.parent / "tests" / "fixtures" / "samples_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    # Save samples to fixtures directory
    samples_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "samples"
    print(f"\nSaving samples to: {samples_dir}")
    save_samples(samples, samples_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    excellent = [s for s in samples if s.evaluation.recommendation == "excellent"]
    good = [s for s in samples if s.evaluation.recommendation == "good"]
    moderate = [s for s in samples if s.evaluation.recommendation == "moderate"]
    schema_only = [s for s in samples if s.evaluation.recommendation == "schema_only"]
    failed = [s for s in samples if not s.is_valid]

    print(f"  Excellent candidates: {len(excellent)}")
    print(f"  Good candidates:      {len(good)}")
    print(f"  Moderate candidates:  {len(moderate)}")
    print(f"  Schema only:          {len(schema_only)}")
    print(f"  Failed to fetch:      {len(failed)}")


if __name__ == "__main__":
    main()
