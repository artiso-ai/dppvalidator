"""Example custom validators for dppvalidator.

These validators implement the SemanticRule protocol and are automatically
discovered via Python entry points when the plugin is installed.

Both rules below target the **v0.6.x** wire shape — `credentialSubject`
is a `ProductPassport` envelope wrapping `Product`, and material
provenance lives at `credentialSubject.materialsProvenance` (plural,
v0.6 spelling). They declare ``applies_to_versions`` so the engine's
per-version plugin dispatch (Phase 6 of
``docs/plans/UNTP_0.7.0_MIGRATION.md``) skips them when a v0.7 payload
flows through. As a defensive belt-and-braces, ``check()`` also ducks
on attribute presence so the rules no-op cleanly even if dispatch
ever misroutes a v0.7 passport into them.

For the v0.7 sibling, see ``brand_name_v07.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport

# Both rules target v0.6.x. The engine's per-version dispatch reads
# this tuple to skip non-matching payloads; the duck-typing in
# ``check()`` is a second line of defence in case dispatch is bypassed
# (e.g. by a caller invoking ``PluginRegistry.run_all_validators``
# directly without ``schema_version=``).
_V06_VERSIONS: tuple[str, ...] = ("0.6.0", "0.6.1")


def _is_v06_shape(passport: Any) -> bool:
    """True when ``passport`` is a v0.6-shaped envelope.

    v0.6 wraps the product under ``credential_subject.product``; v0.7
    has the Product directly as ``credential_subject``. Presence of
    the inner ``.product`` attribute is the cleanest discriminator.
    """
    cs = getattr(passport, "credential_subject", None)
    if cs is None:
        return False
    return hasattr(cs, "product")


class BrandNameRule:
    """SEM_BRAND: v0.6 products should have a brand name for traceability.

    This example validator checks if products have a brand name
    specified — important for consumer identification and traceability.
    Targets the v0.6.x wire shape (`credentialSubject.product.name`).
    For v0.7, see :class:`BrandNameRuleV07` in ``brand_name_v07.py``.
    """

    rule_id: str = "SEM_BRAND"
    description: str = "Products should have a brand name"
    severity: Literal["error", "warning", "info"] = "warning"

    # Engine's per-version dispatch consults this; v0.7 payloads are
    # routed past us to ``BrandNameRuleV07`` instead.
    applies_to_versions: tuple[str, ...] = _V06_VERSIONS

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check if product has a brand name.

        Args:
            passport: The Digital Product Passport to validate

        Returns:
            List of (path, message) tuples for each violation
        """
        violations: list[tuple[str, str]] = []

        if not _is_v06_shape(passport):
            # Not a v0.6 passport — defensive no-op (the engine's
            # per-version dispatch should already have skipped us).
            return violations

        if passport.credential_subject is None:
            return violations

        product = passport.credential_subject.product
        if product and not product.name:
            violations.append(
                (
                    "$.credentialSubject.product.name",
                    "Product should have a name for better traceability",
                )
            )

        return violations


class MinMaterialsRule:
    """SEM_MINMAT: v0.6 products should declare at least 2 materials.

    This example validator encourages comprehensive material disclosure
    by checking if at least 2 materials are declared. Targets the v0.6.x
    `credentialSubject.materialsProvenance` array (plural, v0.6 spelling).
    A v0.7 sibling would read `credentialSubject.materialProvenance`
    (singular) — see ``brand_name_v07.py`` for the version-aware-rule
    pattern.
    """

    rule_id: str = "SEM_MINMAT"
    description: str = "Products should declare at least 2 materials"
    severity: Literal["error", "warning", "info"] = "info"

    applies_to_versions: tuple[str, ...] = _V06_VERSIONS

    def check(self, passport: DigitalProductPassport) -> list[tuple[str, str]]:
        """Check if product has minimum materials declared.

        Args:
            passport: The Digital Product Passport to validate

        Returns:
            List of (path, message) tuples for each violation
        """
        violations: list[tuple[str, str]] = []

        if not _is_v06_shape(passport):
            return violations

        if passport.credential_subject is None:
            return violations

        materials = passport.credential_subject.materials_provenance
        if materials is not None and len(materials) < 2:
            violations.append(
                (
                    "$.credentialSubject.materialsProvenance",
                    f"Only {len(materials)} material(s) declared. "
                    "Consider adding more for comprehensive disclosure.",
                )
            )

        return violations
