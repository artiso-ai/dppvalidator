#!/usr/bin/env python3
"""Check that all error codes in the codebase have documentation.

This script scans the source code for error codes and verifies that each
has a corresponding documentation file in docs/errors/.

Exit codes:
    0 - All error codes are documented
    1 - Missing documentation found
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Project root (resolve to absolute path for robustness in CI/CD)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src" / "dppvalidator"
DOCS_ERRORS_DIR = PROJECT_ROOT / "docs" / "errors"
MKDOCS_FILE = PROJECT_ROOT / "mkdocs.yml"

# Error code pattern: 2-3 uppercase letters followed by 3 digits
ERROR_CODE_PATTERN = re.compile(r"\b([A-Z]{2,3}\d{3})\b")

# Error code prefixes to check
KNOWN_PREFIXES = {"SCH", "PRS", "MDL", "SEM", "JLD", "VOC", "SIG", "CQ", "TXT"}


def find_error_codes_in_source() -> set[str]:
    """Find all error codes defined in source code."""
    error_codes: set[str] = set()

    # Scan Python files in src
    for py_file in SRC_DIR.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")

        # Find all error code matches
        for match in ERROR_CODE_PATTERN.finditer(content):
            code = match.group(1)
            prefix = "".join(c for c in code if c.isalpha())
            if prefix in KNOWN_PREFIXES:
                error_codes.add(code)

    return error_codes


def find_documented_error_codes() -> set[str]:
    """Find all error codes that have documentation files."""
    documented: set[str] = set()

    if not DOCS_ERRORS_DIR.exists():
        return documented

    for md_file in DOCS_ERRORS_DIR.glob("*.md"):
        if md_file.stem != "index":
            # Filename is the error code (e.g., SCH001.md)
            documented.add(md_file.stem)

    return documented


def find_error_codes_in_mkdocs() -> set[str]:
    """Find error codes referenced in mkdocs.yml navigation."""
    referenced: set[str] = set()

    if not MKDOCS_FILE.exists():
        return referenced

    content = MKDOCS_FILE.read_text(encoding="utf-8")
    for match in ERROR_CODE_PATTERN.finditer(content):
        referenced.add(match.group(1))

    return referenced


def main() -> int:
    """Check error documentation coverage."""
    print("Checking error code documentation...")
    print()

    # Find codes
    source_codes = find_error_codes_in_source()
    documented_codes = find_documented_error_codes()
    mkdocs_codes = find_error_codes_in_mkdocs()

    # Calculate differences
    missing_docs = source_codes - documented_codes
    missing_nav = documented_codes - mkdocs_codes
    orphan_docs = documented_codes - source_codes

    # Report
    print(f"Error codes in source: {len(source_codes)}")
    print(f"Documented error codes: {len(documented_codes)}")
    print(f"Error codes in mkdocs nav: {len(mkdocs_codes)}")
    print()

    has_errors = False

    if missing_docs:
        has_errors = True
        print("❌ Missing documentation for error codes:")
        for code in sorted(missing_docs):
            print(f"   - {code}")
        print()
        print(f"   Create files in docs/errors/: {', '.join(sorted(missing_docs))}")
        print()

    if missing_nav:
        has_errors = True
        print("❌ Documented but missing from mkdocs.yml nav:")
        for code in sorted(missing_nav):
            print(f"   - {code}")
        print()

    if orphan_docs:
        print("⚠️  Documentation exists but code not found in source:")
        for code in sorted(orphan_docs):
            print(f"   - {code}")
        print()

    if not has_errors:
        print("✅ All error codes are documented and in mkdocs nav!")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
