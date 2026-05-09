"""Tyres pilot exporters.

Phase 7 task 7.7 of [docs/plans/CIRPASS_2_MIGRATION.md]. Registers
a CSV exporter via the ``dppvalidator.exporters`` entry-point group.

The CSV exporter flattens a TyreLifecycleHistory into one row per
declaration, useful for fleet operators who want a tabular ledger
of their tyre population's lifecycle.
"""

from __future__ import annotations

import csv
import io
from typing import Any


class TyreLifecycleCSVExporter:
    """Flatten a TyreLifecycleHistory into CSV rows.

    Each row is one declaration: the Birth + every subsequent
    event becomes a separate line. Columns are:

    - ``tyreUuid``
    - ``eventType`` (birth | collection | retread | recycling)
    - ``timestamp`` (ISO 8601)
    - ``actorId``
    - ``actorName``
    - ``method`` (Recycling only) / ``process`` (Retread only) / empty

    Implements the minimal :class:`Exporter` protocol —
    ``export(passport) -> str``.
    """

    name: str = "tyres-lifecycle-csv"
    format_id: str = "tyres-lifecycle-csv"

    def export(self, passport: Any) -> str:
        """Return a CSV string flattening the tyreLifecycleHistory extension.

        When the passport carries no tyreLifecycleHistory, returns
        a CSV with just the header row.
        """
        from dppvalidator_tyres.validators.rules import _extract_history

        history = _extract_history(passport)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "tyreUuid",
                "eventType",
                "timestamp",
                "actorId",
                "actorName",
                "method",
            ]
        )
        if history is None:
            return buf.getvalue()
        birth = history.get("birth")
        if isinstance(birth, dict):
            manuf = birth.get("manufacturer") or {}
            writer.writerow(
                [
                    birth.get("tyreUuid", ""),
                    "birth",
                    birth.get("manufacturedAt", ""),
                    manuf.get("id", ""),
                    manuf.get("name", ""),
                    "",
                ]
            )
        events = history.get("events")
        if not isinstance(events, list):
            return buf.getvalue()
        for event in events:
            if not isinstance(event, dict):
                continue
            event_type = event.get("type") or ""
            decl = event.get("declaration") or {}
            if not isinstance(decl, dict):
                continue
            actor_key = {
                "collection": "collector",
                "retread": "retreader",
                "recycling": "recycler",
            }.get(event_type, "")
            actor = decl.get(actor_key) or {}
            ts_key = {
                "collection": "collectedAt",
                "retread": "retreadedAt",
                "recycling": "recycledAt",
            }.get(event_type, "")
            writer.writerow(
                [
                    decl.get("tyreUuid", ""),
                    event_type,
                    decl.get(ts_key, ""),
                    actor.get("id", ""),
                    actor.get("name", ""),
                    decl.get("method", "")
                    if event_type == "recycling"
                    else decl.get("process", "")
                    if event_type == "retread"
                    else "",
                ]
            )
        return buf.getvalue()


__all__ = ["TyreLifecycleCSVExporter"]
