#!/usr/bin/env python3
"""Generate missing error documentation files.

This script creates placeholder documentation for error codes that are
defined in the source code but don't have documentation files.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Add src to path for imports (resolve for CI/CD robustness)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

if TYPE_CHECKING:
    pass

# Late import after path setup - noqa needed for E402
from dppvalidator.validators.errors import ERROR_REGISTRY  # noqa: E402

DOCS_ERRORS_DIR = PROJECT_ROOT / "docs" / "errors"

# Error metadata for generating docs
ERROR_METADATA: dict[str, dict[str, str]] = {
    # Schema errors from SCHEMA_ERROR_CODES
    "SCH001": {"title": "Schema Not Loaded", "category": "Schema Errors"},
    "SCH002": {"title": "Type Mismatch", "category": "Schema Errors"},
    "SCH003": {"title": "Invalid Enum Value", "category": "Schema Errors"},
    "SCH004": {"title": "Invalid Format", "category": "Schema Errors"},
    "SCH005": {"title": "Pattern Mismatch", "category": "Schema Errors"},
    "SCH006": {"title": "String Too Short", "category": "Schema Errors"},
    "SCH007": {"title": "String Too Long", "category": "Schema Errors"},
    "SCH008": {"title": "Value Below Minimum", "category": "Schema Errors"},
    "SCH009": {"title": "Value Above Maximum", "category": "Schema Errors"},
    "SCH010": {"title": "Additional Properties", "category": "Schema Errors"},
    "SCH011": {"title": "Too Few Items", "category": "Schema Errors"},
    "SCH012": {"title": "Too Many Items", "category": "Schema Errors"},
    "SCH013": {"title": "Duplicate Items", "category": "Schema Errors"},
    "SCH014": {"title": "Const Mismatch", "category": "Schema Errors"},
    "SCH015": {"title": "AllOf Violation", "category": "Schema Errors"},
    "SCH016": {"title": "AnyOf Violation", "category": "Schema Errors"},
    "SCH017": {"title": "OneOf Violation", "category": "Schema Errors"},
    "SCH018": {"title": "Not Violation", "category": "Schema Errors"},
    "SCH019": {"title": "Contains Violation", "category": "Schema Errors"},
    "SCH020": {"title": "PrefixItems Violation", "category": "Schema Errors"},
    "SCH021": {"title": "Reference Resolution", "category": "Schema Errors"},
    "SCH099": {"title": "Unknown Schema Error", "category": "Schema Errors"},
    # Model errors
    "MDL001": {"title": "Model Validation Failed", "category": "Model Errors"},
    "MDL002": {"title": "Invalid URL Format", "category": "Model Errors"},
    "MDL003": {"title": "Invalid DateTime Format", "category": "Model Errors"},
    "MDL010": {"title": "Invalid Issuer", "category": "Model Errors"},
    "MDL011": {"title": "Invalid Issuer ID", "category": "Model Errors"},
    "MDL012": {"title": "Invalid Issuer Name", "category": "Model Errors"},
    "MDL013": {"title": "Invalid Issuer Type", "category": "Model Errors"},
    "MDL014": {"title": "Invalid Issuer Location", "category": "Model Errors"},
    "MDL015": {"title": "Invalid Issuer Identifier", "category": "Model Errors"},
    "MDL016": {"title": "Invalid Identifier Scheme", "category": "Model Errors"},
    "MDL020": {"title": "Invalid Credential Subject", "category": "Model Errors"},
    "MDL021": {"title": "Invalid Credential Subject ID", "category": "Model Errors"},
    "MDL022": {"title": "Invalid Credential Subject Type", "category": "Model Errors"},
    "MDL030": {"title": "Invalid Product", "category": "Model Errors"},
    "MDL031": {"title": "Invalid Product ID", "category": "Model Errors"},
    "MDL032": {"title": "Invalid Product Name", "category": "Model Errors"},
    "MDL033": {"title": "Invalid Product Category", "category": "Model Errors"},
    "MDL040": {"title": "Invalid Material", "category": "Model Errors"},
    "MDL041": {"title": "Invalid Material Name", "category": "Model Errors"},
    "MDL042": {"title": "Invalid Material Fraction", "category": "Model Errors"},
    "MDL050": {"title": "Invalid Claim", "category": "Model Errors"},
    "MDL051": {"title": "Invalid Claim Type", "category": "Model Errors"},
    "MDL052": {"title": "Invalid Claim Topic", "category": "Model Errors"},
    "MDL053": {"title": "Invalid Claim Assessment", "category": "Model Errors"},
    "MDL060": {"title": "Invalid Traceability", "category": "Model Errors"},
    "MDL061": {"title": "Invalid Traceability Event", "category": "Model Errors"},
    "MDL070": {"title": "Invalid Circularity", "category": "Model Errors"},
    "MDL071": {"title": "Invalid Circularity Content", "category": "Model Errors"},
    "MDL080": {"title": "Invalid Emission", "category": "Model Errors"},
    "MDL081": {"title": "Invalid Emission Value", "category": "Model Errors"},
    "MDL090": {"title": "Invalid Facility", "category": "Model Errors"},
    "MDL091": {"title": "Invalid Facility Location", "category": "Model Errors"},
    "MDL099": {"title": "Unknown Model Error", "category": "Model Errors"},
    # CIRPASS rules
    "CQ001": {"title": "Missing Mandatory Attributes", "category": "CIRPASS Errors"},
    "CQ004": {"title": "Missing CAS Number", "category": "CIRPASS Errors"},
    "CQ011": {"title": "Missing Operator ID", "category": "CIRPASS Errors"},
    "CQ016": {"title": "Missing Validity Period", "category": "CIRPASS Errors"},
    "CQ017": {"title": "Granularity Mismatch", "category": "CIRPASS Errors"},
    "CQ020": {"title": "Missing Weight/Volume", "category": "CIRPASS Errors"},
    # Textile rules
    "TXT001": {"title": "Invalid Textile HS Code", "category": "Textile Errors"},
    "TXT002": {"title": "Missing Material Composition", "category": "Textile Errors"},
    "TXT003": {"title": "Missing Microplastic Data", "category": "Textile Errors"},
    "TXT004": {"title": "Missing Durability Info", "category": "Textile Errors"},
    "TXT005": {"title": "Missing Care Instructions", "category": "Textile Errors"},
}

TEMPLATE = """# {code} - {title}

## Description

{description}

## Category

{category}

## Severity

`{severity}`

## Common Causes

{causes}

## How to Fix

{fix}

## Example

```json
{example}
```

## See Also

- [Error Overview](index.md)
"""


def get_error_info(code: str) -> dict[str, str]:
    """Get error info from registry or metadata."""
    meta = ERROR_METADATA.get(code, {})
    registry = ERROR_REGISTRY.get(code, {})

    prefix = "".join(c for c in code if c.isalpha())

    # Determine severity based on prefix
    severity_map = {
        "SCH": "error",
        "MDL": "error",
        "SEM": "error",
        "JLD": "warning",
        "VOC": "warning",
        "CQ": "error",
        "TXT": "warning",
    }

    return {
        "title": meta.get("title", registry.get("title", f"Error {code}")),
        "category": meta.get("category", f"{prefix} Errors"),
        "severity": severity_map.get(prefix, "error"),
        "description": registry.get("suggestion", f"Validation error {code}."),
        "causes": "- Input data does not meet validation requirements",
        "fix": registry.get("suggestion", "Review the error message and correct the input data."),
        "example": registry.get("example", "// Example will vary based on error"),
    }


def generate_doc(code: str) -> str:
    """Generate documentation content for an error code."""
    info = get_error_info(code)
    return TEMPLATE.format(code=code, **info)


def main() -> int:
    """Generate missing error documentation files."""
    DOCS_ERRORS_DIR.mkdir(parents=True, exist_ok=True)

    # Find missing codes
    from check_error_docs import find_documented_error_codes, find_error_codes_in_source

    source_codes = find_error_codes_in_source()
    documented = find_documented_error_codes()
    missing = source_codes - documented

    if not missing:
        print("All error codes are documented!")
        return 0

    print(f"Generating {len(missing)} error documentation files...")

    for code in sorted(missing):
        doc_path = DOCS_ERRORS_DIR / f"{code}.md"
        content = generate_doc(code)
        doc_path.write_text(content, encoding="utf-8")
        print(f"  Created: {doc_path.name}")

    print(f"\n✅ Generated {len(missing)} documentation files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
