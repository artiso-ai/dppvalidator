"""Tests for centralized logging module."""

from __future__ import annotations

import logging
from io import StringIO

from dppvalidator.logging import (
    DEFAULT_FORMAT,
    LOGGER_NAME,
    SIMPLE_FORMAT,
    configure_logging,
    get_logger,
    set_level,
)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_with_none_returns_root(self):
        """Getting logger with None returns root package logger."""
        logger = get_logger(None)
        assert logger.name == LOGGER_NAME

    def test_get_logger_with_package_name(self):
        """Getting logger with package name returns that logger."""
        logger = get_logger("dppvalidator.validators")
        assert logger.name == "dppvalidator.validators"

    def test_get_logger_with_external_name(self):
        """Getting logger with external name prefixes with package name."""
        logger = get_logger("mymodule")
        assert logger.name == f"{LOGGER_NAME}.mymodule"

    def test_get_logger_with_dppvalidator_prefix(self):
        """Getting logger starting with dppvalidator returns as-is."""
        logger = get_logger("dppvalidator.custom")
        assert logger.name == "dppvalidator.custom"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def teardown_method(self):
        """Clean up logger handlers after each test."""
        root_logger = logging.getLogger(LOGGER_NAME)
        root_logger.handlers.clear()
        root_logger.addHandler(logging.NullHandler())

    def test_configure_logging_default(self):
        """Configure logging with defaults."""
        configure_logging()
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.WARNING
        assert len(root_logger.handlers) == 1

    def test_configure_logging_verbose(self):
        """Configure logging with verbose mode."""
        configure_logging(verbose=True)
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.DEBUG

    def test_configure_logging_quiet(self):
        """Configure logging with quiet mode."""
        configure_logging(quiet=True)
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level > logging.CRITICAL

    def test_configure_logging_string_level(self):
        """Configure logging with string level."""
        configure_logging(level="INFO")
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.INFO

    def test_configure_logging_int_level(self):
        """Configure logging with integer level."""
        configure_logging(level=logging.ERROR)
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.ERROR

    def test_configure_logging_custom_stream(self):
        """Configure logging with custom stream."""
        stream = StringIO()
        configure_logging(level=logging.INFO, stream=stream)
        logger = get_logger("test")
        logger.info("test message")
        output = stream.getvalue()
        assert "test message" in output

    def test_configure_logging_custom_format(self):
        """Configure logging with custom format string."""
        stream = StringIO()
        configure_logging(
            level=logging.INFO,
            stream=stream,
            format_string="CUSTOM: %(message)s",
        )
        logger = get_logger("test")
        logger.info("hello")
        output = stream.getvalue()
        assert "CUSTOM: hello" in output

    def test_configure_logging_uses_simple_format_for_warning(self):
        """Warning level uses simple format by default."""
        configure_logging(level=logging.WARNING)
        root_logger = logging.getLogger(LOGGER_NAME)
        handler = root_logger.handlers[0]
        formatter = handler.formatter
        assert formatter is not None
        assert SIMPLE_FORMAT in formatter._fmt  # type: ignore[union-attr]

    def test_configure_logging_uses_default_format_for_debug(self):
        """Debug level uses detailed format by default."""
        configure_logging(level=logging.DEBUG)
        root_logger = logging.getLogger(LOGGER_NAME)
        handler = root_logger.handlers[0]
        formatter = handler.formatter
        assert formatter is not None
        assert DEFAULT_FORMAT in formatter._fmt  # type: ignore[union-attr]

    def test_configure_logging_clears_existing_handlers(self):
        """Configure logging clears existing handlers."""
        root_logger = logging.getLogger(LOGGER_NAME)
        root_logger.addHandler(logging.StreamHandler())
        root_logger.addHandler(logging.StreamHandler())
        assert len(root_logger.handlers) >= 2

        configure_logging()
        assert len(root_logger.handlers) == 1


class TestSetLevel:
    """Tests for set_level function."""

    def teardown_method(self):
        """Clean up logger handlers after each test."""
        root_logger = logging.getLogger(LOGGER_NAME)
        root_logger.handlers.clear()
        root_logger.addHandler(logging.NullHandler())

    def test_set_level_with_int(self):
        """Set level with integer value."""
        configure_logging()
        set_level(logging.DEBUG)
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.DEBUG

    def test_set_level_with_string(self):
        """Set level with string value."""
        configure_logging()
        set_level("ERROR")
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.ERROR

    def test_set_level_updates_handlers(self):
        """Set level also updates handler levels."""
        configure_logging()
        set_level(logging.DEBUG)
        root_logger = logging.getLogger(LOGGER_NAME)
        for handler in root_logger.handlers:
            assert handler.level == logging.DEBUG

    def test_set_level_invalid_string_defaults_to_warning(self):
        """Invalid string level defaults to WARNING."""
        configure_logging()
        set_level("INVALID")
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.WARNING
