"""Rich progress bar factory — keeps progress on stderr so stdout stays pipeable."""

from __future__ import annotations

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from polytool.core.console import err_console


def make_progress(transient: bool = False) -> Progress:
    """Build a Rich Progress with sensible columns.

    Use as a context manager:

        with make_progress() as progress:
            task = progress.add_task("Working", total=100)
            for ...:
                progress.update(task, advance=1)
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=err_console,
        transient=transient,
    )


def make_spinner(description: str) -> Progress:
    """Build a Rich Progress without a bar — for indeterminate work."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=err_console,
        transient=False,
    )
