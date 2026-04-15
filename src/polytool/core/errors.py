"""Error types with friendly hints for the CLI."""

from __future__ import annotations

import sys
from typing import NoReturn

import typer
from rich.panel import Panel

from polytool.core.console import err_console


class PolytoolError(Exception):
    """A user-facing error with an optional fix hint."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class MissingExtraError(PolytoolError):
    """Raised when an optional dependency group isn't installed."""

    def __init__(self, module: str, extra: str) -> None:
        message = f"Missing optional dependency: '{module}' (from the '{extra}' extra)."
        hint = (
            f"Install with: [cyan]uv tool install 'polytool[{extra}]'[/cyan]\n"
            f"Or for everything: [cyan]uv tool install 'polytool[full]'[/cyan]"
        )
        super().__init__(message, hint)
        self.module = module
        self.extra = extra


def fail(message: str, hint: str | None = None) -> NoReturn:
    """Print a red error panel and exit with code 1."""
    body = f"[red bold]{message}[/red bold]"
    if hint:
        body += f"\n\n[dim]Hint:[/dim] {hint}"
    err_console.print(Panel(body, border_style="red", title="Error"))
    raise typer.Exit(code=1)


def install_excepthook() -> None:
    """Install a sys.excepthook that renders PolytoolError nicely."""
    original = sys.excepthook

    def hook(exc_type, exc_value, tb):
        if isinstance(exc_value, PolytoolError):
            fail(exc_value.message, exc_value.hint)
            return
        original(exc_type, exc_value, tb)

    sys.excepthook = hook
