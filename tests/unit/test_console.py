"""Tests for CLI console module."""

from __future__ import annotations

from io import StringIO

from dppvalidator.cli.console import Console


class TestConsole:
    """Tests for Console class."""

    def test_console_init_defaults(self):
        """Test Console initialization with defaults."""
        console = Console()
        assert console._quiet is False

    def test_console_init_quiet(self):
        """Test Console initialization in quiet mode."""
        console = Console(quiet=True)
        assert console._quiet is True

    def test_console_print_basic(self):
        """Test basic print."""
        stream = StringIO()
        console = Console(file=stream)
        console.print("Hello World")
        output = stream.getvalue()
        assert "Hello World" in output

    def test_console_print_quiet_suppresses(self):
        """Test print is suppressed in quiet mode."""
        stream = StringIO()
        console = Console(file=stream, quiet=True)
        console.print("Hello World")
        output = stream.getvalue()
        assert output == ""

    def test_console_print_error(self, capsys):
        """Test print_error outputs to stderr."""
        console = Console()
        console.print_error("Test error")
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()

    def test_console_print_error_quiet(self, capsys):
        """Test print_error is suppressed in quiet mode."""
        console = Console(quiet=True)
        console.print_error("Test error")
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_console_print_warning(self):
        """Test print_warning."""
        stream = StringIO()
        console = Console(file=stream)
        console.print_warning("Test warning")
        output = stream.getvalue()
        assert "warning" in output.lower()

    def test_console_print_warning_quiet(self):
        """Test print_warning is suppressed in quiet mode."""
        stream = StringIO()
        console = Console(file=stream, quiet=True)
        console.print_warning("Test warning")
        output = stream.getvalue()
        assert output == ""

    def test_console_print_success(self):
        """Test print_success."""
        stream = StringIO()
        console = Console(file=stream)
        console.print_success("Test success")
        output = stream.getvalue()
        assert "success" in output.lower()

    def test_console_print_success_quiet(self):
        """Test print_success is suppressed in quiet mode."""
        stream = StringIO()
        console = Console(file=stream, quiet=True)
        console.print_success("Test success")
        output = stream.getvalue()
        assert output == ""

    def test_console_is_rich_property(self):
        """Test is_rich property."""
        console = Console()
        # Property should return boolean
        assert isinstance(console.is_rich, bool)

    def test_console_create_table(self):
        """Test create_table returns table object."""
        console = Console()
        table = console.create_table(title="Test Table")
        assert table is not None

    def test_console_print_table(self):
        """Test print_table output."""
        stream = StringIO()
        console = Console(file=stream)
        table = console.create_table(title="Test Table")
        table.add_column("Name")
        table.add_column("Value")
        table.add_row("A", "1")
        table.add_row("B", "2")
        console.print_table(table)
        output = stream.getvalue()
        # Should have some output
        assert len(output) > 0

    def test_console_print_table_quiet(self):
        """Test print_table is suppressed in quiet mode."""
        stream = StringIO()
        console = Console(file=stream, quiet=True)
        table = console.create_table(title="Test Table")
        table.add_column("Name")
        table.add_row("A")
        console.print_table(table)
        output = stream.getvalue()
        assert output == ""

    def test_console_print_panel(self):
        """Test print_panel output."""
        stream = StringIO()
        console = Console(file=stream)
        console.print_panel("Panel content", title="Test Panel")
        output = stream.getvalue()
        assert "Panel" in output or "content" in output

    def test_console_print_panel_quiet(self):
        """Test print_panel is suppressed in quiet mode."""
        stream = StringIO()
        console = Console(file=stream, quiet=True)
        console.print_panel("Panel content", title="Test Panel")
        output = stream.getvalue()
        assert output == ""

    def test_console_print_panel_no_title(self):
        """Test print_panel without title."""
        stream = StringIO()
        console = Console(file=stream)
        console.print_panel("Panel content")
        output = stream.getvalue()
        assert "content" in output.lower() or len(output) > 0

    def test_console_print_with_style(self):
        """Test print with style parameter."""
        stream = StringIO()
        console = Console(file=stream)
        console.print("Styled text", style="bold")
        output = stream.getvalue()
        assert "Styled text" in output

    def test_console_print_multiple_args(self):
        """Test print with multiple arguments."""
        stream = StringIO()
        console = Console(file=stream)
        console.print("First", "Second", "Third")
        output = stream.getvalue()
        assert "First" in output


class TestFallbackTable:
    """Tests for _FallbackTable class."""

    def test_fallback_table_creation(self):
        """Test _FallbackTable creation."""
        from dppvalidator.cli.console import _FallbackTable

        table = _FallbackTable(title="Test")
        assert table.title == "Test"

    def test_fallback_table_add_column(self):
        """Test _FallbackTable add_column."""
        from dppvalidator.cli.console import _FallbackTable

        table = _FallbackTable()
        table.add_column("Name")
        table.add_column("Value")
        assert len(table.columns) == 2

    def test_fallback_table_add_row(self):
        """Test _FallbackTable add_row."""
        from dppvalidator.cli.console import _FallbackTable

        table = _FallbackTable()
        table.add_column("Name")
        table.add_row("Test")
        assert len(table.rows) == 1

    def test_fallback_table_render(self):
        """Test _FallbackTable render."""
        from dppvalidator.cli.console import _FallbackTable

        table = _FallbackTable(title="Test Table")
        table.add_column("Name")
        table.add_column("Value")
        table.add_row("A", "1")
        table.add_row("B", "2")
        stream = StringIO()
        table.render(stream)
        output = stream.getvalue()
        assert "Test Table" in output
        assert "Name" in output

    def test_fallback_table_render_empty(self):
        """Test _FallbackTable render with no columns."""
        from dppvalidator.cli.console import _FallbackTable

        table = _FallbackTable()
        stream = StringIO()
        table.render(stream)
        output = stream.getvalue()
        # Empty table should produce minimal output
        assert output == "" or len(output) < 5


class TestConsoleNoRich:
    """Tests for Console when Rich is not available."""

    def test_console_print_without_rich(self, monkeypatch):
        """Test print without Rich."""
        from dppvalidator.cli import console as console_module

        monkeypatch.setattr(console_module, "HAS_RICH", False)

        stream = StringIO()
        c = Console(file=stream)
        c._rich = None  # Force no Rich
        c.print("Plain text")
        output = stream.getvalue()
        assert "Plain text" in output

    def test_console_print_error_without_rich(self, monkeypatch, capsys):
        """Test print_error without Rich."""
        from dppvalidator.cli import console as console_module

        monkeypatch.setattr(console_module, "HAS_RICH", False)

        c = Console()
        c._rich = None
        c.print_error("Test error")
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_console_print_warning_without_rich(self, monkeypatch):
        """Test print_warning without Rich."""
        from dppvalidator.cli import console as console_module

        monkeypatch.setattr(console_module, "HAS_RICH", False)

        stream = StringIO()
        c = Console(file=stream)
        c._rich = None
        c.print_warning("Test warning")
        output = stream.getvalue()
        assert "Warning:" in output

    def test_console_print_success_without_rich(self, monkeypatch):
        """Test print_success without Rich."""
        from dppvalidator.cli import console as console_module

        monkeypatch.setattr(console_module, "HAS_RICH", False)

        stream = StringIO()
        c = Console(file=stream)
        c._rich = None
        c.print_success("Test success")
        output = stream.getvalue()
        assert "✓" in output

    def test_console_print_panel_without_rich(self, monkeypatch, capsys):
        """Test print_panel without Rich."""
        from dppvalidator.cli import console as console_module

        monkeypatch.setattr(console_module, "HAS_RICH", False)

        c = Console()
        c._rich = None
        c.print_panel("Content", title="Title")
        captured = capsys.readouterr()
        assert "Title" in captured.out or "Content" in captured.out

    def test_console_create_table_without_rich(self, monkeypatch):
        """Test create_table without Rich returns fallback."""
        from dppvalidator.cli import console as console_module
        from dppvalidator.cli.console import _FallbackTable

        monkeypatch.setattr(console_module, "HAS_RICH", False)

        c = Console()
        c._rich = None
        table = c.create_table(title="Test")
        assert isinstance(table, _FallbackTable)

    def test_console_print_table_without_rich(self, monkeypatch):
        """Test print_table without Rich."""
        from dppvalidator.cli import console as console_module
        from dppvalidator.cli.console import _FallbackTable

        monkeypatch.setattr(console_module, "HAS_RICH", False)

        stream = StringIO()
        c = Console(file=stream)
        c._rich = None
        table = _FallbackTable(title="Test")
        table.add_column("Col1")
        table.add_row("Val1")
        c.print_table(table)
        output = stream.getvalue()
        assert "Test" in output or "Col1" in output
