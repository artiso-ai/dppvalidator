#!/usr/bin/env python3
"""Fetch vocabulary data from UNCEFACT and update bundled JSON files.

This script is intended to be run periodically (e.g., monthly via GitHub Actions)
to keep vocabulary data up-to-date.

Usage:
    python scripts/fetch_vocabularies.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent.parent / "src" / "dppvalidator" / "vocabularies" / "data"

VOCABULARIES = {
    "countries": {
        "url": "https://vocabulary.uncefact.org/CountryId",
        "description": "ISO 3166-1 country codes",
        "fallback_url": "https://restcountries.com/v3.1/all?fields=cca2",
    },
    "units": {
        "url": "https://vocabulary.uncefact.org/UnitMeasureCode",
        "description": "UNECE Rec20 unit of measure codes",
    },
}

# Fallback unit codes from UNECE Rec20 - common units used in DPP
# Source: https://unece.org/trade/uncefact/cl-recommendations
FALLBACK_UNIT_CODES = {
    # Mass
    "KGM",
    "GRM",
    "MGM",
    "TNE",
    "LBR",
    "ONZ",
    "DTN",
    "CTM",
    "MC",
    # Length
    "MTR",
    "CMT",
    "MMT",
    "KMT",
    "INH",
    "FOT",
    "YRD",
    "SMI",
    "NMI",
    # Volume
    "LTR",
    "MLT",
    "MTQ",
    "CMQ",
    "DMQ",
    "GLI",
    "GLL",
    "PT",
    "QT",
    # Area
    "MTK",
    "CMK",
    "DMK",
    "KMK",
    "INK",
    "FTK",
    "YDK",
    "HAR",
    "ACR",
    # Time
    "SEC",
    "MIN",
    "HUR",
    "DAY",
    "WEE",
    "MON",
    "ANN",
    # Temperature
    "CEL",
    "FAH",
    "KEL",
    # Electrical
    "AMP",
    "VLT",
    "OHM",
    "WTT",
    "KWT",
    "MAW",
    # Energy
    "KWH",
    "MWH",
    "JOU",
    "KJO",
    "MJO",
    "GJO",
    "WHR",
    # Pressure
    "BAR",
    "PAL",
    "KPA",
    "MPA",
    "ATM",
    "PSI",
    # Count/quantity
    "EA",
    "PR",
    "SET",
    "DZN",
    "GRO",
    "PCE",
    "NAR",
    "NPR",
    # Percentage/ratio
    "PCT",
    "P1",
    # Flow rates
    "MQH",
    "MQS",
    "LTH",
    "LTM",
    # Power
    "KWN",
    "C62",
    # Frequency
    "HTZ",
    "KHZ",
    "MHZ",
    "GHZ",
    # Data
    "E34",
    "E35",
    "E36",
    "4L",  # byte, kilobyte, megabyte, gigabyte
}

TIMEOUT = 30.0


def fetch_uncefact_vocabulary(url: str) -> set[str] | None:
    """Fetch vocabulary codes from UNCEFACT endpoint."""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(
                url,
                headers={"Accept": "application/json"},
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()

            codes: set[str] = set()
            if isinstance(data, dict):
                if "@graph" in data:
                    for item in data["@graph"]:
                        if isinstance(item, dict):
                            code = item.get("@id", "").split("#")[-1]
                            if code and not code.startswith("_"):
                                codes.add(code)
                elif "member" in data:
                    for member in data.get("member", []):
                        if isinstance(member, dict):
                            code = member.get("notation") or member.get("@id", "").split("#")[-1]
                            if code:
                                codes.add(code)

            if codes:
                return codes

    except Exception as e:
        print(f"Failed to fetch from {url}: {e}")

    return None


def fetch_countries_fallback() -> set[str] | None:
    """Fetch country codes from restcountries.com as fallback."""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(
                VOCABULARIES["countries"]["fallback_url"],
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()

            codes = {country["cca2"] for country in data if "cca2" in country}
            if codes:
                return codes

    except Exception as e:
        print(f"Failed to fetch from fallback: {e}")

    return None


def save_vocabulary(name: str, codes: set[str], description: str) -> None:
    """Save vocabulary codes to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "description": description,
        "source": VOCABULARIES[name]["url"],
        "count": len(codes),
        "codes": sorted(codes),
    }

    output_path = DATA_DIR / f"{name}.json"
    output_path.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Saved {len(codes)} {name} codes to {output_path}")


def main() -> int:
    """Fetch and save all vocabularies."""
    success = True

    # Fetch country codes
    print("Fetching country codes...")
    countries = fetch_uncefact_vocabulary(VOCABULARIES["countries"]["url"])
    if not countries:
        print("Trying fallback source for countries...")
        countries = fetch_countries_fallback()

    if countries:
        save_vocabulary("countries", countries, VOCABULARIES["countries"]["description"])
    else:
        print("ERROR: Failed to fetch country codes from any source")
        success = False

    # Fetch unit codes
    print("Fetching unit codes...")
    units = fetch_uncefact_vocabulary(VOCABULARIES["units"]["url"])

    if not units:
        print("Using fallback unit codes...")
        units = FALLBACK_UNIT_CODES

    save_vocabulary("units", units, VOCABULARIES["units"]["description"])

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
