"""Example plugin for dppvalidator demonstrating custom validators and exporters."""

from dppvalidator_example_plugin.exporters import CSVExporter
from dppvalidator_example_plugin.validators import BrandNameRule, MinMaterialsRule

__version__ = "0.1.0"

__all__ = [
    "BrandNameRule",
    "MinMaterialsRule",
    "CSVExporter",
]
