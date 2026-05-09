"""TYR-coded rule implementations for the tyres pilot.

Each rule walks the UNTP DPP envelope, looking for the
``credentialSubject.extensions.tyreLifecycleHistory`` extension
slot. Passports without that extension are silently skipped (not
every DPP is a tyre DPP — the rule should be a no-op for textile
or generic DPPs).

The extension is read as raw dict / model attribute data — no
pyyaml-style schema enforcement. Type errors caused by malformed
extensions are caught defensively; the model layer is responsible
for catching shape problems before these rules run.
"""

from __future__ import annotations

from typing import Any, Literal

# ETRTO load-index range. The full table runs 0-279, but realistic
# passenger / light-truck tyres land in the 60-130 band; values
# outside this range are *technically valid* but warrant a check.
_ETRTO_LOAD_INDEX_PASSENGER = range(60, 131)
_ETRTO_SPEED_RATINGS = frozenset(
    ["L", "M", "N", "P", "Q", "R", "S", "T", "U", "H", "V", "W", "Y", "Z"]
)
_RECYCLING_METHODS = frozenset(
    ["mechanical", "pyrolysis", "devulcanisation", "energy_recovery", "other"]
)


# =============================================================================
# Helpers
# =============================================================================


def _extract_history(passport: Any) -> dict[str, Any] | None:
    """Pull the tyreLifecycleHistory dict from the passport's extension slot.

    Returns ``None`` when the extension isn't present (the passport
    isn't a tyre DPP). Tolerant of both dict-shaped extensions
    (Pydantic ``extra="allow"`` payload) and structured Pydantic
    sub-models. Returns the raw dict so the rule logic stays
    decoupled from the plugin's own model classes.
    """
    cs = getattr(passport, "credential_subject", None)
    if cs is None and isinstance(passport, dict):
        cs = passport.get("credentialSubject") or passport.get("credential_subject")
    if cs is None:
        return None

    extensions = getattr(cs, "extensions", None)
    if extensions is None and isinstance(cs, dict):
        extensions = cs.get("extensions")
    if extensions is None:
        return None

    history = (
        extensions.get("tyreLifecycleHistory")
        if isinstance(extensions, dict)
        else getattr(extensions, "tyreLifecycleHistory", None)
    )
    if isinstance(history, dict):
        return history
    if hasattr(history, "model_dump"):
        return history.model_dump(by_alias=True, mode="json")
    return None


def _birth(history: dict[str, Any]) -> dict[str, Any] | None:
    """Return the Birth sub-dict from a history payload."""
    birth = history.get("birth")
    if isinstance(birth, dict):
        return birth
    return None


def _events(history: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the events list (may be empty)."""
    events = history.get("events")
    if isinstance(events, list):
        return [e for e in events if isinstance(e, dict)]
    return []


# =============================================================================
# TYR001 — DOT marking
# =============================================================================


class DOTMarkingRule:
    """TYR001: Birth declaration carries a well-formed DOT marking."""

    rule_id: str = "TYR001"
    description: str = "Tyre Birth declaration must carry a DOT marking (US DOT 49 CFR 574)"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Add a ``dotMarking`` object to the Birth declaration with "
        "plantCode, sizeCode, weekOfYear (1-53), and year (4-digit)."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TYR001"

    def check(self, passport: Any) -> list[tuple[str, str]]:
        history = _extract_history(passport)
        if history is None:
            return []
        birth = _birth(history)
        if birth is None:
            return []
        path = "$.credentialSubject.extensions.tyreLifecycleHistory.birth.dotMarking"
        dot = birth.get("dotMarking")
        if not isinstance(dot, dict):
            return [(path, "Tyre Birth declaration is missing dotMarking.")]
        violations: list[tuple[str, str]] = []
        for required in ("plantCode", "sizeCode", "weekOfYear", "year"):
            if dot.get(required) in (None, ""):
                violations.append(
                    (
                        f"{path}.{required}",
                        f"DOT marking is missing required field {required!r}.",
                    )
                )
        return violations


# =============================================================================
# TYR002 — Birth chain completeness
# =============================================================================


class BirthChainCompletenessRule:
    """TYR002: Birth declaration carries the manufacturer actor + tyre UUID."""

    rule_id: str = "TYR002"
    description: str = "Tyre Birth declaration must carry tyreUuid and manufacturer actor"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Populate ``tyreUuid`` (UUID v4) and ``manufacturer`` "
        "(an actor object with id + name) on the Birth declaration."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TYR002"

    def check(self, passport: Any) -> list[tuple[str, str]]:
        history = _extract_history(passport)
        if history is None:
            return []
        birth = _birth(history)
        if birth is None:
            return [
                (
                    "$.credentialSubject.extensions.tyreLifecycleHistory.birth",
                    "TyreLifecycleHistory has no Birth declaration.",
                )
            ]
        violations: list[tuple[str, str]] = []
        path = "$.credentialSubject.extensions.tyreLifecycleHistory.birth"
        if not birth.get("tyreUuid"):
            violations.append((f"{path}.tyreUuid", "Birth declaration is missing tyreUuid."))
        manuf = birth.get("manufacturer")
        if not isinstance(manuf, dict):
            violations.append(
                (
                    f"{path}.manufacturer",
                    "Birth declaration is missing the manufacturer actor.",
                )
            )
        else:
            if not manuf.get("id"):
                violations.append(
                    (f"{path}.manufacturer.id", "Manufacturer actor is missing id (URI / DID).")
                )
            if not manuf.get("name"):
                violations.append(
                    (f"{path}.manufacturer.name", "Manufacturer actor is missing name.")
                )
        return violations


# =============================================================================
# TYR003 — Load index
# =============================================================================


class LoadIndexRule:
    """TYR003: Load index lies in the ETRTO passenger/light-truck band (60-130)."""

    rule_id: str = "TYR003"
    description: str = "Load index should be in the ETRTO passenger / light-truck range (60-130)"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Verify the load index value against the ETRTO standard "
        "manual; values outside 60-130 are unusual for passenger / "
        "light-truck applications."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TYR003"

    def check(self, passport: Any) -> list[tuple[str, str]]:
        history = _extract_history(passport)
        if history is None:
            return []
        birth = _birth(history)
        if birth is None:
            return []
        size = birth.get("size")
        if not isinstance(size, dict):
            return []
        load_index = size.get("loadIndex")
        if not isinstance(load_index, int):
            return []
        path = "$.credentialSubject.extensions.tyreLifecycleHistory.birth.size.loadIndex"
        if load_index not in _ETRTO_LOAD_INDEX_PASSENGER:
            return [
                (
                    path,
                    f"Load index {load_index} is outside the ETRTO passenger / "
                    f"light-truck range (60-130).",
                )
            ]
        return []


# =============================================================================
# TYR004 — Speed rating
# =============================================================================


class SpeedRatingRule:
    """TYR004: Speed rating is a recognised ETRTO letter code."""

    rule_id: str = "TYR004"
    description: str = "Speed rating should be a recognised ETRTO letter code"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Use one of L, M, N, P, Q, R, S, T, U, H, V, W, Y, Z."
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TYR004"

    def check(self, passport: Any) -> list[tuple[str, str]]:
        history = _extract_history(passport)
        if history is None:
            return []
        birth = _birth(history)
        if birth is None:
            return []
        size = birth.get("size")
        if not isinstance(size, dict):
            return []
        speed = size.get("speedRating")
        if not isinstance(speed, str):
            return []
        path = "$.credentialSubject.extensions.tyreLifecycleHistory.birth.size.speedRating"
        if speed.upper() not in _ETRTO_SPEED_RATINGS:
            return [
                (
                    path,
                    f"Speed rating {speed!r} is not in the ETRTO standard set "
                    f"({sorted(_ETRTO_SPEED_RATINGS)}).",
                )
            ]
        return []


# =============================================================================
# TYR005 — Section width / aspect ratio / rim diameter sanity
# =============================================================================


class SectionWidthRule:
    """TYR005: Tyre size dimensions look sane for passenger / light-truck."""

    rule_id: str = "TYR005"
    description: str = "Tyre dimensions should be in the passenger / light-truck range"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "ETRTO ranges: section width 125-445 mm, aspect ratio 20-95, rim diameter 10-24 inches."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TYR005"

    def check(self, passport: Any) -> list[tuple[str, str]]:
        history = _extract_history(passport)
        if history is None:
            return []
        birth = _birth(history)
        if birth is None:
            return []
        size = birth.get("size")
        if not isinstance(size, dict):
            return []
        violations: list[tuple[str, str]] = []
        path = "$.credentialSubject.extensions.tyreLifecycleHistory.birth.size"
        sw = size.get("sectionWidth")
        if isinstance(sw, int) and not (125 <= sw <= 445):
            violations.append(
                (f"{path}.sectionWidth", f"Section width {sw} mm is outside ETRTO 125-445.")
            )
        ar = size.get("aspectRatio")
        if isinstance(ar, int) and not (20 <= ar <= 95):
            violations.append((f"{path}.aspectRatio", f"Aspect ratio {ar} is outside ETRTO 20-95."))
        rd = size.get("rimDiameter")
        if isinstance(rd, int) and not (10 <= rd <= 24):
            violations.append(
                (f"{path}.rimDiameter", f"Rim diameter {rd} in is outside the 10-24 range.")
            )
        return violations


# =============================================================================
# TYR006 — Retread provenance
# =============================================================================


class RetreadProvenanceRule:
    """TYR006: Retread events name the upstream Birth via previousBirthUuid."""

    rule_id: str = "TYR006"
    description: str = "Retread declaration must reference the upstream Birth (previousBirthUuid)"
    severity: Literal["error", "warning", "info"] = "error"
    suggestion: str = (
        "Populate ``previousBirthUuid`` on every Retread event so the "
        "casing chain can be reconstructed."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TYR006"

    def check(self, passport: Any) -> list[tuple[str, str]]:
        history = _extract_history(passport)
        if history is None:
            return []
        violations: list[tuple[str, str]] = []
        for i, event in enumerate(_events(history)):
            if event.get("type") != "retread":
                continue
            decl = event.get("declaration")
            if not isinstance(decl, dict):
                continue
            if not decl.get("previousBirthUuid"):
                violations.append(
                    (
                        f"$.credentialSubject.extensions.tyreLifecycleHistory.events[{i}].declaration.previousBirthUuid",
                        "Retread declaration is missing previousBirthUuid.",
                    )
                )
        return violations


# =============================================================================
# TYR007 — Collection actor
# =============================================================================


class CollectionActorRule:
    """TYR007: Collection events identify the collecting actor."""

    rule_id: str = "TYR007"
    description: str = "Collection declaration must identify the collecting actor"
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = "Populate ``collector.id`` and ``collector.name`` on every Collection event."
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TYR007"

    def check(self, passport: Any) -> list[tuple[str, str]]:
        history = _extract_history(passport)
        if history is None:
            return []
        violations: list[tuple[str, str]] = []
        for i, event in enumerate(_events(history)):
            if event.get("type") != "collection":
                continue
            decl = event.get("declaration")
            if not isinstance(decl, dict):
                continue
            collector = decl.get("collector")
            base = f"$.credentialSubject.extensions.tyreLifecycleHistory.events[{i}].declaration.collector"
            if not isinstance(collector, dict):
                violations.append((base, "Collection declaration is missing the collector actor."))
                continue
            if not collector.get("id"):
                violations.append((f"{base}.id", "Collection.collector is missing id."))
            if not collector.get("name"):
                violations.append((f"{base}.name", "Collection.collector is missing name."))
        return violations


# =============================================================================
# TYR008 — Recycling method
# =============================================================================


class RecyclingMethodRule:
    """TYR008: Recycling events declare the recycling method."""

    rule_id: str = "TYR008"
    description: str = (
        "Recycling declaration must name the method (mechanical / "
        "pyrolysis / devulcanisation / energy_recovery / other)"
    )
    severity: Literal["error", "warning", "info"] = "warning"
    suggestion: str = (
        "Populate ``method`` on every Recycling event with a value "
        "from the GDSO Recycling v0.1 enumeration."
    )
    docs_url: str = "https://artiso-ai.github.io/dppvalidator/errors/TYR008"

    def check(self, passport: Any) -> list[tuple[str, str]]:
        history = _extract_history(passport)
        if history is None:
            return []
        violations: list[tuple[str, str]] = []
        for i, event in enumerate(_events(history)):
            if event.get("type") != "recycling":
                continue
            decl = event.get("declaration")
            if not isinstance(decl, dict):
                continue
            method = decl.get("method")
            base = f"$.credentialSubject.extensions.tyreLifecycleHistory.events[{i}].declaration.method"
            if not isinstance(method, str) or not method:
                violations.append((base, "Recycling declaration is missing method."))
                continue
            if method not in _RECYCLING_METHODS:
                violations.append(
                    (
                        base,
                        f"Recycling method {method!r} is not in the GDSO v0.1 "
                        f"closed set ({sorted(_RECYCLING_METHODS)}).",
                    )
                )
        return violations
