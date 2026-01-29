"""Centralized logging configuration for dppvalidator.

This module provides a unified logging interface for the entire package.
All modules should use `get_logger(__name__)` to obtain a logger instance.

Usage:
    from dppvalidator.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Processing passport...")
    logger.debug("Detailed info: %s", data)
    logger.warning("Something unexpected")
    logger.error("Failed to validate: %s", error)
"""

from __future__ import annotations

import logging
import sys
from typing import TextIO

# Package-level logger name
LOGGER_NAME = "dppvalidator"

# Default format for log messages
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(levelname)s: %(message)s"


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance for the given module name.

    Args:
        name: Module name (typically __name__). If None, returns the root
              package logger.

    Returns:
        A configured logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing...")
    """
    if name is None:
        return logging.getLogger(LOGGER_NAME)

    # Ensure all loggers are children of the package logger
    if not name.startswith(LOGGER_NAME):
        if name.startswith("dppvalidator"):
            return logging.getLogger(name)
        return logging.getLogger(f"{LOGGER_NAME}.{name}")

    return logging.getLogger(name)


def configure_logging(
    level: int | str = logging.WARNING,
    format_string: str | None = None,
    stream: TextIO | None = None,
    quiet: bool = False,
    verbose: bool = False,
) -> None:
    """Configure the package-level logger.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO, "DEBUG")
        format_string: Custom format string. If None, uses default format.
        stream: Output stream. If None, uses sys.stderr.
        quiet: If True, suppress all output (sets level to CRITICAL+1)
        verbose: If True, enable debug output (sets level to DEBUG)

    Example:
        >>> configure_logging(level=logging.DEBUG, verbose=True)
    """
    root_logger = logging.getLogger(LOGGER_NAME)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Determine level
    if quiet:
        effective_level = logging.CRITICAL + 1
    elif verbose:
        effective_level = logging.DEBUG
    elif isinstance(level, str):
        effective_level = getattr(logging, level.upper(), logging.WARNING)
    else:
        effective_level = level

    root_logger.setLevel(effective_level)

    # Create handler
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setLevel(effective_level)

    # Set format
    if format_string is None:
        format_string = SIMPLE_FORMAT if effective_level >= logging.WARNING else DEFAULT_FORMAT

    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)


def set_level(level: int | str) -> None:
    """Set the logging level for the package logger.

    Args:
        level: Logging level (e.g., logging.DEBUG, "INFO")
    """
    root_logger = logging.getLogger(LOGGER_NAME)

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.WARNING)

    root_logger.setLevel(level)

    for handler in root_logger.handlers:
        handler.setLevel(level)


# Initialize with default configuration (warnings only, no output by default)
# CLI will call configure_logging() to set up proper output
_root = logging.getLogger(LOGGER_NAME)
_root.addHandler(logging.NullHandler())
