"""Shared helpers for the UNTP ↔ CIRPASS compat shims.

Phase 8.5 polish (2026-05-09). Lifted from the two shim modules
(``untp_0_7_to_cirpass_1_3.py`` and ``cirpass_1_3_to_untp_0_7.py``)
where the helpers had drifted into near-duplicates. Centralising
them keeps the two shims symmetric and makes future maintenance
(e.g. tightening the ISO 8601 parser) a single-site edit.

Module-private — the underscore prefix on the filename makes it a
private member of the ``compat`` package; consumers should reach
for the public surface (``to_cirpass_1_3``, ``to_untp_0_7``,
``MappingWarning``, etc.) rather than these helpers directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def normalise_iso8601(value: Any) -> str:
    """Normalise a datetime-shaped scalar to an ISO 8601 string.

    Accepts:

    - :class:`datetime.datetime` instances → ``.isoformat()``.
    - Pre-formatted strings → returned unchanged.
    - Anything else → ``str(value)``.

    The function does *not* validate the timestamp shape — the
    model layer is responsible for catching malformed inputs at
    validate time, and surfacing them as ``MDL050``-coded errors.
    Both shims previously rolled their own (slightly divergent)
    versions of this helper; lifting it here keeps the
    forward / reverse shim symmetric.
    """
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return str(value)


def pick_localised(items: Any, default_language: str) -> tuple[str | None, list[str]]:
    """Pick a single string from a list of LocalisedText dicts.

    Returns ``(picked_value, dropped_languages)``:

    - ``picked_value`` is the ``value`` field of the entry whose
      ``language`` matches ``default_language`` exactly. When no
      entry matches, falls back to the first list entry. ``None``
      when the list is empty / not a list.
    - ``dropped_languages`` lists every *other* language present so
      callers can emit one ``MAP001`` per dropped entry.

    Used by the reverse shim (CIRPASS LocalisedText[] → UNTP scalar
    string) — the forward shim wraps UNTP scalars in a single-entry
    list directly without needing this helper.
    """
    if not isinstance(items, list) or not items:
        return None, []
    picked: dict[str, Any] | None = None
    for item in items:
        if isinstance(item, dict) and item.get("language") == default_language:
            picked = item
            break
    if picked is None:
        for item in items:
            if isinstance(item, dict):
                picked = item
                break
    picked_value = picked.get("value") if isinstance(picked, dict) else None
    dropped_languages = [
        item.get("language") or ""
        for item in items
        if isinstance(item, dict) and item is not picked
    ]
    return (str(picked_value) if picked_value is not None else None), dropped_languages


__all__ = ["normalise_iso8601", "pick_localised"]
