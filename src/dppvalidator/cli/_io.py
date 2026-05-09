"""Shared CLI I/O helpers.

Phase 8.6 polish (2026-05-09). Centralises input loading across the
``validate``, ``export``, and ``migrate`` commands — three near-
identical ``_load_input`` helpers with subtly different error
phrasings and (for ``export``) missing stdin support.

Module-private — the underscore prefix marks it as internal to the
``cli`` package; subcommand modules import :func:`load_input`
directly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger

if TYPE_CHECKING:
    from dppvalidator.cli.console import Console

logger = get_logger(__name__)


def load_input(input_path: str, console: Console) -> dict[str, Any] | None:
    """Load a JSON DPP payload from a file path or stdin.

    Args:
        input_path: File path or the literal ``"-"`` to read stdin.
        console: CLI console for human-readable error reporting.

    Returns:
        The parsed JSON dict on success; ``None`` on any failure
        (file not found, JSON parse error, encoding error, etc.).
        Callers translate ``None`` into the ``EXIT_IO_ERROR`` (5)
        exit code per the Phase 6 §6.7 contract.
    """
    try:
        if input_path == "-":
            # Ensure UTF-8 encoding for stdin on every platform that
            # supports the reconfigure() hook (Python 3.7+ on most
            # OSes; PyPy / older 3.x may not).
            if hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
            content = sys.stdin.read()
        else:
            path = Path(input_path)
            if not path.exists():
                logger.error("File not found: %s", input_path)
                console.print_error(f"File not found: {input_path}")
                return None
            content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON: %s", exc)
        console.print_error(f"Invalid JSON: {exc}")
        return None
    except Exception as exc:  # noqa: BLE001 — boundary catch for CLI ergonomics
        logger.exception("Unexpected error loading input")
        console.print_error(str(exc))
        return None


__all__ = ["load_input"]
