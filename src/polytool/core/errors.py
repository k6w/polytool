"""Error types with friendly hints for the CLI."""

from __future__ import annotations

from typing import NoReturn

import typer
from rich.panel import Panel

from polytool.core.console import err_console


def render_panel(message: str, hint: str | None) -> None:
    """Render the standard red error panel to stderr."""
    body = f"[red bold]{message}[/red bold]"
    if hint:
        body += f"\n\n[dim]Hint:[/dim] {hint}"
    err_console.print(Panel(body, border_style="red", title="Error"))


class PolytoolError(Exception):
    """A user-facing error with an optional fix hint.

    The CLI entry point (``polytool.cli.main``) catches this and renders
    ``render_panel`` instead of letting Python or Typer print a stack trace.
    """

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class MissingExtraError(PolytoolError):
    """Raised when an optional dependency group isn't installed."""

    def __init__(self, module: str, extra: str) -> None:
        from rich.markup import escape

        message = f"Missing optional dependency: '{module}' (from the '{extra}' extra)."
        # rich.markup.escape only escapes `[` — `]` is left literal because
        # Rich only treats `[` as the markup-tag opener.
        spec = escape(f"polytool[{extra}]")
        full = escape("polytool[full]")
        hint = (
            f"Install with: [cyan]uv tool install '{spec}'[/cyan]\n"
            f"Or for everything: [cyan]uv tool install '{full}'[/cyan]"
        )
        super().__init__(message, hint)
        self.module = module
        self.extra = extra


def fail(message: str, hint: str | None = None) -> NoReturn:
    """Print a red error panel and exit with code 1."""
    render_panel(message, hint)
    raise typer.Exit(code=1)


def install_excepthook() -> None:
    """No-op kept for backwards compatibility.

    Earlier versions installed a ``sys.excepthook``. The CLI entry-point now
    handles ``PolytoolError`` directly via a try/except wrapper.
    """
    return
