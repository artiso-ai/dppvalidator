"""dppvalidator - Digital Product Passport validation library."""

from importlib.metadata import version

from dppvalidator.logging import configure_logging, get_logger
from dppvalidator.models.passport import DigitalProductPassport
from dppvalidator.validators.deep import DeepValidationResult, DeepValidator
from dppvalidator.validators.engine import ValidationEngine
from dppvalidator.validators.results import ValidationError, ValidationResult

__version__ = version("dppvalidator")

__all__ = [
    "__version__",
    # Logging
    "configure_logging",
    "get_logger",
    # Models
    "DigitalProductPassport",
    # Validation
    "ValidationEngine",
    "ValidationError",
    "ValidationResult",
    # Deep validation
    "DeepValidator",
    "DeepValidationResult",
]
