#!/usr/bin/env python3
"""Diff two UNTP DPP JSON Schema versions and emit a markdown table.

Usage:
    python3 diff_schema.py <old-schema.json> <new-schema.json>

Prints sections matching the format used in the migration plan:
  - Root field diff
  - Required-field diff
  - $defs class diff (added / removed / shared)
  - Per-shared-class property diff

No external dependencies; standard library only.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _props(spec: Mapping[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for name, body in (spec.get("$defs") or {}).items():
        out[name] = sorted((body.get("properties") or {}).keys())
    out["__root__"] = sorted((spec.get("properties") or {}).keys())
    return out


def _print_section(title: str) -> None:
    print()
    print(f"### {title}")
    print()


def main(old_path: str, new_path: str) -> int:
    old = json.loads(Path(old_path).read_text(encoding="utf-8"))
    new = json.loads(Path(new_path).read_text(encoding="utf-8"))

    old_props = _props(old)
    new_props = _props(new)

    print(f"# Schema diff: `{Path(old_path).name}` → `{Path(new_path).name}`")

    _print_section("Root field diff")
    ra, rb = set(old_props["__root__"]), set(new_props["__root__"])
    print(f"- removed: {sorted(ra - rb)}")
    print(f"- added:   {sorted(rb - ra)}")
    print(f"- shared:  {sorted(ra & rb)}")

    _print_section("Required-field diff")
    print(f"- old required: {old.get('required')}")
    print(f"- new required: {new.get('required')}")

    _print_section("$defs class diff")
    da = set(old_props) - {"__root__"}
    db = set(new_props) - {"__root__"}
    print(f"- removed defs: {sorted(da - db)}")
    print(f"- added defs:   {sorted(db - da)}")
    print(f"- shared defs:  {sorted(da & db)}")

    _print_section("Per-shared-class property diff")
    for cls in sorted(da & db):
        pa, pb = set(old_props[cls]), set(new_props[cls])
        if pa == pb:
            continue
        print(f"#### `{cls}`")
        print(f"- removed: {sorted(pa - pb)}")
        print(f"- added:   {sorted(pb - pa)}")
        print()

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
