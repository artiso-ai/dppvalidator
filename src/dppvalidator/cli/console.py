"""CLI console output utilities with Rich support and fallback.

This module provides a unified interface for CLI output that uses Rich
when available and falls back to plain print otherwise.
"""

from __future__ import annotations

import sys
from typing import Any, TextIO

try:
    from rich.console import Console as RichConsole
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    RichConsole = None  # type: ignore[misc, assignment]
    Panel = None  # type: ignore[misc, assignment]
    Table = None  # type: ignore[misc, assignment]
    Text = None  # type: ignore[misc, assignment]


class Console:
    """Console wrapper that uses Rich when available, falls back to print."""

    def __init__(self, file: TextIO | None = None, quiet: bool = False) -> None:
        """Initialize console.

        Args:
            file: Output stream (default: stdout)
            quiet: If True, suppress all output
        """
        self._file = file or sys.stdout
        self._quiet = quiet
        self._rich: RichConsole | None = None

        if HAS_RICH:
            self._rich = RichConsole(file=self._file)

    @property
    def is_rich(self) -> bool:
        """Check if Rich is available."""
        return self._rich is not None

    def print(self, *args: Any, style: str | None = None, **kwargs: Any) -> None:
        """Print to console.

        Args:
            *args: Items to print
            style: Rich style (ignored if Rich not available)
            **kwargs: Additional arguments passed to print/rich.print
        """
        if self._quiet:
            return

        if self._rich and style:
            self._rich.print(*args, style=style, **kwargs)
        elif self._rich:
            self._rich.print(*args, **kwargs)
        else:
            print(*args, file=self._file, **kwargs)

    def print_error(self, message: str) -> None:
        """Print an error message to stderr.

        Args:
            message: Error message
        """
        if self._quiet:
            return

        if HAS_RICH:
            err_console = RichConsole(file=sys.stderr)
            err_console.print(f"[bold red]Error:[/bold red] {message}")
        else:
            print(f"Error: {message}", file=sys.stderr)

    def print_warning(self, message: str) -> None:
        """Print a warning message.

        Args:
            message: Warning message
        """
        if self._quiet:
            return

        if self._rich:
            self._rich.print(f"[yellow]Warning:[/yellow] {message}")
        else:
            print(f"Warning: {message}", file=self._file)

    def print_success(self, message: str) -> None:
        """Print a success message.

        Args:
            message: Success message
        """
        if self._quiet:
            return

        if self._rich:
            self._rich.print(f"[bold green]✓[/bold green] {message}")
        else:
            print(f"✓ {message}", file=self._file)

    def print_panel(self, content: str, title: str | None = None, style: str = "blue") -> None:
        """Print content in a panel.

        Args:
            content: Panel content
            title: Optional panel title
            style: Panel border style
        """
        if self._quiet:
            return

        if self._rich and Panel:
            self._rich.print(Panel(content, title=title, border_style=style))
        else:
            if title:
                print(f"\n{title}")
                print("-" * 40)
            print(content)

    def create_table(self, title: str | None = None) -> Table | _FallbackTable:
        """Create a table for output.

        Args:
            title: Optional table title

        Returns:
            Rich Table or fallback table object
        """
        if self._rich and Table:
            return Table(title=title)
        return _FallbackTable(title=title)

    def print_table(self, table: Table | _FallbackTable) -> None:
        """Print a table.

        Args:
            table: Table to print
        """
        if self._quiet:
            return

        if self._rich and isinstance(table, Table):
            self._rich.print(table)
        elif isinstance(table, _FallbackTable):
            table.render(self._file)


class _FallbackTable:
    """Simple table fallback when Rich is not available."""

    def __init__(self, title: str | None = None) -> None:
        self.title = title
        self.columns: list[str] = []
        self.rows: list[list[str]] = []

    def add_column(self, header: str, **kwargs: Any) -> None:  # noqa: ARG002
        """Add a column to the table."""
        self.columns.append(header)

    def add_row(self, *values: str) -> None:
        """Add a row to the table."""
        self.rows.append(list(values))

    def render(self, file: TextIO) -> None:
        """Render the table to a file."""
        if self.title:
            print(f"\n{self.title}", file=file)

        if not self.columns:
            return

        widths = [len(col) for col in self.columns]
        for row in self.rows:
            for i, val in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(val)))

        header = "  ".join(col.ljust(widths[i]) for i, col in enumerate(self.columns))
        print(header, file=file)
        print("-" * len(header), file=file)

        for row in self.rows:
            line = "  ".join(
                str(val).ljust(widths[i]) if i < len(widths) else str(val)
                for i, val in enumerate(row)
            )
            print(line, file=file)


console = Console()
err_console = Console(file=sys.stderr)
