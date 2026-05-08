"""Example plugin for dppvalidator demonstrating custom validators and exporters.

Phase 6 of ``docs/plans/UNTP_0.7.0_MIGRATION.md`` adds
:class:`BrandNameRuleV07` — a v0.7-shape companion to the v0.6
:class:`BrandNameRule` — so plugin authors see how to write a
version-aware rule that targets the new namespace without touching
the v0.6 surface.
"""

from dppvalidator_example_plugin.brand_name_v07 import BrandNameRuleV07
from dppvalidator_example_plugin.exporters import CSVExporter
from dppvalidator_example_plugin.validators import BrandNameRule, MinMaterialsRule

__version__ = "0.2.0"

__all__ = [
    "BrandNameRule",
    "BrandNameRuleV07",
    "MinMaterialsRule",
    "CSVExporter",
]
