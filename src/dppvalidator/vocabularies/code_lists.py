"""Extended code list validation for materials, HS codes, and GTINs."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib.resources import files
from typing import Any

from dppvalidator.logging import get_logger

logger = get_logger(__name__)


def _get_data_files() -> Any:
    """Get the data directory using importlib.resources."""
    return files("dppvalidator.vocabularies").joinpath("data")


@lru_cache(maxsize=4)
def _load_code_list(name: str) -> frozenset[str]:
    """Load code list from bundled JSON data file.

    Args:
        name: Name of the code list file (without .json extension)

    Returns:
        Frozenset of valid codes
    """
    try:
        data_files = _get_data_files()
        data_file = data_files.joinpath(f"{name}.json")
        content = data_file.read_text(encoding="utf-8")
        data = json.loads(content)
        return frozenset(data.get("codes", []))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load code list %s: %s", name, e)
        return frozenset()


def get_material_codes() -> frozenset[str]:
    """Get UNECE Rec 46 material codes.

    Returns:
        Frozenset of valid material codes
    """
    return _load_code_list("materials")


def get_hs_codes() -> frozenset[str]:
    """Get HS (Harmonized System) codes for textiles.

    Returns:
        Frozenset of valid HS codes
    """
    return _load_code_list("hs_codes")


def is_valid_material_code(code: str) -> bool:
    """Check if a material code is valid per UNECE Rec 46.

    Args:
        code: Material code to validate

    Returns:
        True if valid, False otherwise
    """
    if not code:
        return False
    # Normalize: uppercase, strip whitespace
    normalized = code.upper().strip().replace(" ", "_").replace("-", "_")
    return normalized in get_material_codes()


def is_valid_hs_code(code: str) -> bool:
    """Check if an HS code is valid for textiles (Chapters 50-63).

    Args:
        code: HS code to validate (4-digit chapter heading)

    Returns:
        True if valid, False otherwise
    """
    if not code:
        return False
    # Normalize: remove dots, spaces, take first 4 digits
    normalized = re.sub(r"[.\s]", "", code)[:4]
    return normalized in get_hs_codes()


def is_textile_hs_code(code: str) -> bool:
    """Check if an HS code belongs to textile chapters (50-63).

    Args:
        code: HS code to check

    Returns:
        True if textile chapter, False otherwise
    """
    if not code:
        return False
    normalized = re.sub(r"[.\s]", "", code)
    if len(normalized) < 2:
        return False
    try:
        chapter = int(normalized[:2])
        return 50 <= chapter <= 63
    except ValueError:
        return False


def validate_gtin(gtin: str) -> bool:
    """Validate a GTIN (Global Trade Item Number) checksum.

    Supports GTIN-8, GTIN-12, GTIN-13, and GTIN-14.

    Args:
        gtin: GTIN string to validate

    Returns:
        True if checksum is valid, False otherwise
    """
    if not gtin:
        return False

    # Remove any non-digit characters
    digits = re.sub(r"\D", "", gtin)

    # Valid lengths: 8, 12, 13, 14
    if len(digits) not in (8, 12, 13, 14):
        return False

    # Calculate check digit using GS1 algorithm
    # Weights alternate 3, 1, 3, 1... from right to left (excluding check digit)
    total = 0
    for i, digit in enumerate(reversed(digits[:-1])):
        weight = 3 if i % 2 == 0 else 1
        total += int(digit) * weight

    # Check digit is (10 - (total mod 10)) mod 10
    expected_check = (10 - (total % 10)) % 10
    actual_check = int(digits[-1])

    return expected_check == actual_check


def extract_gtin_from_gs1_digital_link(url: str) -> str | None:
    """Extract GTIN from a GS1 Digital Link URL.

    Examples:
        - https://id.gs1.org/01/09506000134352
        - https://example.com/01/09506000134352/21/12345

    Args:
        url: GS1 Digital Link URL

    Returns:
        GTIN string or None if not found
    """
    # Pattern: /01/ followed by 8-14 digits
    match = re.search(r"/01/(\d{8,14})", url)
    if match:
        return match.group(1)
    return None


def is_valid_gs1_digital_link(url: str) -> bool:
    """Validate a GS1 Digital Link URL contains a valid GTIN.

    Args:
        url: URL to validate

    Returns:
        True if contains valid GTIN, False otherwise
    """
    gtin = extract_gtin_from_gs1_digital_link(url)
    if gtin is None:
        return False
    return validate_gtin(gtin)


def get_hs_chapter_description(code: str) -> str | None:
    """Get the description for an HS chapter.

    Args:
        code: HS code

    Returns:
        Chapter description or None
    """
    chapters = {
        "50": "Silk",
        "51": "Wool, fine or coarse animal hair",
        "52": "Cotton",
        "53": "Other vegetable textile fibres",
        "54": "Man-made filaments",
        "55": "Man-made staple fibres",
        "56": "Wadding, felt and nonwovens",
        "57": "Carpets and other textile floor coverings",
        "58": "Special woven fabrics",
        "59": "Impregnated, coated, covered or laminated textile fabrics",
        "60": "Knitted or crocheted fabrics",
        "61": "Articles of apparel, knitted or crocheted",
        "62": "Articles of apparel, not knitted or crocheted",
        "63": "Other made up textile articles",
    }
    if not code:
        return None
    normalized = re.sub(r"[.\s]", "", code)
    if len(normalized) >= 2:
        return chapters.get(normalized[:2])
    return None
