"""Shared Rich console (stderr for status, stdout reserved for piped output)."""

from __future__ import annotations

from rich.console import Console

console = Console()
err_console = Console(stderr=True)
