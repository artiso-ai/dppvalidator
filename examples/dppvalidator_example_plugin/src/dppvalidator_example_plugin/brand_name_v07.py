"""v0.7-shape variant of BrandNameRule for the example plugin.

Phase 6 of ``docs/plans/UNTP_0.7.0_MIGRATION.md``: ships a sibling of
:class:`dppvalidator_example_plugin.validators.BrandNameRule` written
against the **v0.7 wire shape**, so plugin authors browsing the
example see how to author a version-aware rule that targets the new
namespace.

Key differences from the v0.6 rule:

- v0.7 ``credentialSubject`` *is* the Product directly — there is no
  ``ProductPassport`` envelope, so the brand-name check reads
  ``passport.credential_subject.name`` rather than
  ``passport.credential_subject.product.name``.
- v0.7 introduces a ``relatedParty: list[PartyRole]`` field that
  carries typed (role, party) pairs. A "brandOwner" entry on
  ``relatedParty`` is the canonical way to attribute brand identity
  in v0.7; this rule promotes that pattern by *upgrading* the
  violation when neither a name nor a brandOwner party is present.

The rule duck-types on the passport's module path so it can co-exist
with the v0.6 ``BrandNameRule`` in the same registry — the engine
runs both, and each silently no-ops when handed a passport from the
"wrong" version.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from dppvalidator.models.v0_7.envelope import DigitalProductPassport


class BrandNameRuleV07:
    """SEM_BRAND_V07: v0.7 variant of the brand-name semantic check.

    Targets the v0.7 ``credentialSubject`` (now a ``Product`` directly).
    Emits a *warning* when ``Product.name`` is empty AND no
    ``relatedParty`` carries the ``brandOwner`` role — both of those
    are reasonable ways to attribute brand identity in v0.7.

    Example:
        >>> rule = BrandNameRuleV07()
        >>> violations = rule.check(passport)  # passport: v0.7 DPP
        >>> for path, message in violations:
        ...     print(f"{path}: {message}")
    """

    rule_id: str = "SEM_BRAND_V07"
    description: str = (
        "Products should attribute brand identity via Product.name or a "
        "relatedParty with role 'brandOwner' (UNTP v0.7 shape)"
    )
    severity: Literal["error", "warning", "info"] = "warning"

    # The set of UNTP versions this rule targets. The engine's per-version
    # rule dispatch (``ALL_RULES_BY_VERSION``) reads this attribute to
    # decide whether to run the rule for a given payload version.
    applies_to_versions: tuple[str, ...] = ("0.7.0",)

    def check(
        self,
        passport: DigitalProductPassport,
    ) -> list[tuple[str, str]]:
        """Check that brand identity is attributable.

        Args:
            passport: A v0.7 ``DigitalProductPassport`` instance.

        Returns:
            List of ``(path, message)`` tuples — empty when the passport
            attributes brand identity through any supported channel.

        Notes:
            Ducks on attribute presence rather than ``isinstance``: v0.6
            passports lack ``credential_subject.related_party`` and
            ``credential_subject.name`` lives one level deeper, so the
            rule no-ops cleanly when given a v0.6 passport.
        """
        violations: list[tuple[str, str]] = []

        product = self._extract_v07_product(passport)
        if product is None:
            # Wrong version shape — silently skip.
            return violations

        has_name = bool(getattr(product, "name", None))
        has_brand_owner = self._has_brand_owner_party(product)

        if not has_name and not has_brand_owner:
            violations.append(
                (
                    "$.credentialSubject",
                    "Product should attribute brand identity via Product.name "
                    "or a relatedParty with role 'brandOwner'.",
                )
            )

        return violations

    @staticmethod
    def _extract_v07_product(passport: Any) -> Any | None:
        """Return the v0.7 Product, or ``None`` if the shape doesn't match.

        v0.7's credentialSubject *is* a Product (no envelope). v0.6
        wraps it: ``credentialSubject.product`` — the presence of an
        outer ``.product`` attribute is the cleanest discriminator.
        """
        cs = getattr(passport, "credential_subject", None)
        if cs is None:
            return None
        # v0.6 wraps the Product under credential_subject.product;
        # v0.7 has the Product directly.
        if hasattr(cs, "product"):
            return None
        return cs

    @staticmethod
    def _has_brand_owner_party(product: Any) -> bool:
        """True when a ``relatedParty`` carries the ``brandOwner`` role."""
        related = getattr(product, "related_party", None) or []
        for entry in related:
            role = getattr(entry, "role", None)
            # ``role`` is an Enum on the model but its value is a string;
            # the engine's ``use_enum_values=True`` config means we may
            # see either form depending on how the passport was loaded.
            value = getattr(role, "value", role)
            if value == "brandOwner":
                return True
        return False
